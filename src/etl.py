import os
import math
import time
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .db import db_conn, apply_schema

SOCRATA_URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"

ISO_FORMATS = (
    "%Y-%m-%dT%H:%M:%S.%f",  # e.g., 2023-01-01T12:34:56.789
    "%Y-%m-%dT%H:%M:%S",     # e.g., 2023-01-01T12:34:56
)


def parse_iso(dt: Optional[str]) -> Optional[str]:
    if not dt:
        return None
    for fmt in ISO_FORMATS:
        try:
            # Standardize to UTC ISO string without timezone info
            return datetime.strptime(dt, fmt).replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            continue
    # Fallback: return as-is
    return dt


def get_date_range() -> Tuple[str, str]:
    end = os.getenv("END_DATE")
    start = os.getenv("START_DATE")
    if not end:
        end_dt = datetime.now(timezone.utc)
    else:
        end_dt = datetime.fromisoformat(end)
    if not start:
        # Reduced from 90 days to 7 days to keep database under 10MB
        # This still provides enough data for meaningful analysis
        start_dt = end_dt - timedelta(days=7)
    else:
        start_dt = datetime.fromisoformat(start)
    return start_dt.date().isoformat(), end_dt.date().isoformat()


class SocrataError(Exception):
    pass


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=16), reraise=True,
       retry=retry_if_exception_type(SocrataError))
def fetch_page(params: Dict[str, str]) -> list:
    headers = {}
    token = os.getenv("SOCRATA_APP_TOKEN")
    if token:
        headers["X-App-Token"] = token
    resp = requests.get(SOCRATA_URL, params=params, headers=headers, timeout=60)
    if not resp.ok:
        raise SocrataError(f"HTTP {resp.status_code}: {resp.text[:200]}")
    try:
        return resp.json()
    except json.JSONDecodeError as e:
        raise SocrataError("Invalid JSON response") from e


def ensure_dimensions(conn, value: Optional[str], table: str, cache: Dict[str, int]) -> Optional[int]:
    if value is None:
        return None
    if value in cache:
        return cache[value]
    cur = conn.execute(f"INSERT OR IGNORE INTO {table}(name) VALUES (?)", (value,))
    # Fetch id
    row = conn.execute(f"SELECT id FROM {table} WHERE name = ?", (value,)).fetchone()
    dim_id = row[0] if row else None
    cache[value] = dim_id
    return dim_id


def upsert_service_request(conn, row: dict, caches: Dict[str, Dict[str, int]]):
    unique_key = row.get("unique_key")
    if unique_key is None:
        return
    try:
        unique_key = int(unique_key)
    except (TypeError, ValueError):
        return

    created_date = parse_iso(row.get("created_date"))
    closed_date = parse_iso(row.get("closed_date"))
    resolution_description = row.get("resolution_description")
    incident_zip = row.get("incident_zip")
    latitude = float(row.get("latitude")) if row.get("latitude") else None
    longitude = float(row.get("longitude")) if row.get("longitude") else None

    agency_id = ensure_dimensions(conn, row.get("agency"), "agency", caches["agency"]) 
    complaint_type_id = ensure_dimensions(conn, row.get("complaint_type"), "complaint_type", caches["complaint_type"]) 
    descriptor_id = ensure_dimensions(conn, row.get("descriptor"), "descriptor", caches["descriptor"]) 
    borough_id = ensure_dimensions(conn, row.get("borough"), "borough", caches["borough"]) 

    conn.execute(
        """
        INSERT INTO service_requests (
            unique_key, created_date, closed_date, resolution_description, incident_zip,
            latitude, longitude, agency_id, complaint_type_id, descriptor_id, borough_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(unique_key) DO UPDATE SET
            created_date=excluded.created_date,
            closed_date=excluded.closed_date,
            resolution_description=excluded.resolution_description,
            incident_zip=excluded.incident_zip,
            latitude=excluded.latitude,
            longitude=excluded.longitude,
            agency_id=excluded.agency_id,
            complaint_type_id=excluded.complaint_type_id,
            descriptor_id=excluded.descriptor_id,
            borough_id=excluded.borough_id
        """,
        (
            unique_key, created_date, closed_date, resolution_description, incident_zip,
            latitude, longitude, agency_id, complaint_type_id, descriptor_id, borough_id
        ),
    )


def run_etl() -> None:
    start_date, end_date = get_date_range()
    page_size = int(os.getenv("PAGE_SIZE", "5000"))

    print(f"ETL: Fetching NYC 311 data from {start_date} to {end_date}")
    print(f"ETL: Using page size {page_size}")

    with db_conn() as conn:
        apply_schema(conn)
        caches = {"agency": {}, "complaint_type": {}, "descriptor": {}, "borough": {}}

        # Get count for progress (optional; may be rate-limited). Use approximate via $select=count(*)
        count_params = {
            "$select": "count(1)",
            "$where": f"created_date between '{start_date}T00:00:00' and '{end_date}T23:59:59'"
        }
        try:
            cnt_json = fetch_page(count_params)
            total = int(cnt_json[0]["count_1"]) if cnt_json and "count_1" in cnt_json[0] else 0
            print(f"ETL: Estimated {total:,} records to fetch")
        except Exception as e:
            print(f"ETL: Could not get count estimate: {e}")
            total = 0

        offset = 0
        fetched = 0
        while True:
            params = {
                "$limit": page_size,
                "$offset": offset,
                "$order": "created_date",
                "$where": f"created_date between '{start_date}T00:00:00' and '{end_date}T23:59:59'"
            }
            data = fetch_page(params)
            if not data:
                break
            with conn:
                for r in data:
                    upsert_service_request(conn, r, caches)
            fetched += len(data)
            offset += page_size
            
            # Progress indicator
            if total > 0:
                progress = (fetched / total) * 100
                print(f"ETL: Progress {fetched:,}/{total:,} ({progress:.1f}%)")
            else:
                print(f"ETL: Fetched {fetched:,} records so far...")
            
            if total and fetched >= total:
                break
                
    print(f"ETL completed. Total records processed: {fetched:,}")


if __name__ == "__main__":
    run_etl()
