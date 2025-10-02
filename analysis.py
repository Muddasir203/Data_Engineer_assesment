"""
NYC 311 Service Requests Analysis

This script answers 5 meaningful questions about the NYC 311 dataset:
- 2 questions using pure SQL (Q1, Q2)
- 3 questions using Python data tooling with pandas and matplotlib (Q3, Q4, Q5)

Each question includes rationale, SQL/code, and well-formatted output.
"""

import os
import sqlite3
from contextlib import closing
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import Tuple

from src.db import get_db_path

OUTPUT_DIR = os.path.join(os.getcwd(), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Terminal formatting constants
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKCYAN = '\033[96m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'


def print_section_header(title: str, question: str, rationale: str):
    """Print formatted section header."""
    print(f"\n{'=' * 100}")
    print(f"{BOLD}{HEADER}{title}{ENDC}")
    print(f"{'=' * 100}")
    print(f"{OKCYAN}QUESTION: {question}{ENDC}")
    print(f"{OKGREEN}RATIONALE: {rationale}{ENDC}")
    print(f"{'=' * 100}\n")


def print_sql(sql: str):
    """Print formatted SQL query."""
    print(f"{OKBLUE}SQL QUERY:{ENDC}")
    print(f"{'-' * 100}")
    print(sql.strip())
    print(f"{'-' * 100}\n")


def print_results_table(df: pd.DataFrame, title: str = "RESULTS", max_rows: int = 20):
    """Print formatted results table."""
    print(f"{WARNING}{title}:{ENDC}")
    print(f"{'-' * 100}")
    if len(df) > max_rows:
        print(df.head(max_rows).to_string(index=False))
        print(f"\n... showing {max_rows} of {len(df)} rows ...")
    else:
        print(df.to_string(index=False))
    print(f"{'-' * 100}\n")


def query_to_df(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> pd.DataFrame:
    """Execute SQL query and return results as DataFrame."""
    return pd.read_sql_query(sql, conn, params=params)


def q1_busiest_agencies_by_workload(conn: sqlite3.Connection) -> Tuple[str, pd.DataFrame]:
    """
    Q1 (SQL): Which agencies handle the most service requests, and what is their resolution rate?
    
    This helps identify which city departments are most burdened and how effectively they resolve issues.
    It's important for resource allocation and understanding agency performance.
    """
    sql = """
    SELECT
      a.name AS agency,
      COUNT(*) AS total_requests,
      SUM(CASE WHEN sr.closed_date IS NOT NULL THEN 1 ELSE 0 END) AS closed_requests,
      ROUND(100.0 * SUM(CASE WHEN sr.closed_date IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS resolution_rate_pct,
      ROUND(AVG(
        CASE
          WHEN sr.closed_date IS NOT NULL AND sr.created_date IS NOT NULL
          THEN (julianday(sr.closed_date) - julianday(sr.created_date)) * 24.0
        END
      ), 2) AS avg_resolution_hours
    FROM service_requests sr
    LEFT JOIN agency a ON a.id = sr.agency_id
    WHERE a.name IS NOT NULL
    GROUP BY a.name
    ORDER BY total_requests DESC
    LIMIT 15;
    """
    
    print_section_header(
        "QUESTION 1 (SQL)",
        "Which agencies handle the most service requests, and what is their resolution rate?",
        "Understanding agency workload and performance helps identify resource needs and efficiency gaps."
    )
    print_sql(sql)
    
    df = query_to_df(conn, sql)
    print_results_table(df)
    
    df.to_csv(os.path.join(OUTPUT_DIR, "q1_busiest_agencies.csv"), index=False)
    return sql, df


def q2_complaint_types_by_resolution_difficulty(conn: sqlite3.Connection) -> Tuple[str, pd.DataFrame]:
    """
    Q2 (SQL): What are the most difficult complaint types to resolve (longest resolution time)?
    
    This reveals which issues take the longest to resolve, helping prioritize process improvements
    and set realistic expectations for citizens.
    """
    sql = """
    SELECT
      ct.name AS complaint_type,
      COUNT(*) AS total_requests,
      ROUND(AVG(
        CASE
          WHEN sr.closed_date IS NOT NULL AND sr.created_date IS NOT NULL
          THEN (julianday(sr.closed_date) - julianday(sr.created_date))
        END
      ), 2) AS avg_resolution_days,
      ROUND(MIN(
        CASE
          WHEN sr.closed_date IS NOT NULL AND sr.created_date IS NOT NULL
          THEN (julianday(sr.closed_date) - julianday(sr.created_date))
        END
      ), 2) AS min_resolution_days,
      ROUND(MAX(
        CASE
          WHEN sr.closed_date IS NOT NULL AND sr.created_date IS NOT NULL
          THEN (julianday(sr.closed_date) - julianday(sr.created_date))
        END
      ), 2) AS max_resolution_days
    FROM service_requests sr
    LEFT JOIN complaint_type ct ON ct.id = sr.complaint_type_id
    WHERE ct.name IS NOT NULL
      AND sr.closed_date IS NOT NULL
      AND sr.created_date IS NOT NULL
    GROUP BY ct.name
    HAVING COUNT(*) >= 100
    ORDER BY avg_resolution_days DESC
    LIMIT 15;
    """
    
    print_section_header(
        "QUESTION 2 (SQL)",
        "What are the most difficult complaint types to resolve (longest resolution time)?",
        "Identifying slow-to-resolve issues helps target process improvements and manage citizen expectations."
    )
    print_sql(sql)
    
    df = query_to_df(conn, sql)
    print_results_table(df)
    
    df.to_csv(os.path.join(OUTPUT_DIR, "q2_resolution_difficulty.csv"), index=False)
    return sql, df


def q3_temporal_patterns_analysis(conn: sqlite3.Connection) -> Tuple[str, pd.DataFrame]:
    """
    Q3 (Python): How do service request volumes vary by day of week and hour?
    
    Understanding temporal patterns helps optimize staffing schedules and identify peak demand periods.
    This uses pandas for date manipulation and matplotlib for visualization.
    """
    sql = """
    SELECT
      created_date,
      CASE CAST(strftime('%w', created_date) AS INTEGER)
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
      END AS day_of_week,
      CAST(strftime('%H', created_date) AS INTEGER) AS hour_of_day
    FROM service_requests
    WHERE created_date IS NOT NULL;
    """
    
    print_section_header(
        "QUESTION 3 (Python + Matplotlib)",
        "How do service request volumes vary by day of week and hour?",
        "Temporal patterns reveal peak demand times for optimal resource allocation and staffing."
    )
    
    df = query_to_df(conn, sql)
    
    # Analysis using pandas
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    by_day = df.groupby('day_of_week').size().reindex(day_order)
    by_hour = df.groupby('hour_of_day').size()
    
    # Print summary statistics
    summary_df = pd.DataFrame({
        'Day': day_order,
        'Requests': by_day.values,
        'Percentage': (by_day.values / by_day.sum() * 100).round(2)
    })
    print_results_table(summary_df, "REQUESTS BY DAY OF WEEK")
    
    # Create visualizations
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Day of week plot
    ax1.bar(range(7), by_day.values, color='steelblue', edgecolor='black')
    ax1.set_xlabel('Day of Week', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Number of Requests', fontsize=12, fontweight='bold')
    ax1.set_title('Service Requests by Day of Week', fontsize=14, fontweight='bold')
    ax1.set_xticks(range(7))
    ax1.set_xticklabels(day_order, rotation=45, ha='right')
    ax1.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for i, v in enumerate(by_day.values):
        ax1.text(i, v, f'{v:,}', ha='center', va='bottom')
    
    # Hour of day plot
    ax2.plot(by_hour.index, by_hour.values, marker='o', linewidth=2, markersize=6, color='darkgreen')
    ax2.fill_between(by_hour.index, by_hour.values, alpha=0.3, color='lightgreen')
    ax2.set_xlabel('Hour of Day', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Number of Requests', fontsize=12, fontweight='bold')
    ax2.set_title('Service Requests by Hour of Day', fontsize=14, fontweight='bold')
    ax2.set_xticks(range(0, 24, 2))
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    out_png = os.path.join(OUTPUT_DIR, "q3_temporal_patterns.png")
    plt.savefig(out_png, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"{OKGREEN}✓ Visualization saved to: {out_png}{ENDC}\n")
    
    return sql, summary_df


def q4_borough_comparison_analysis(conn: sqlite3.Connection) -> Tuple[str, pd.DataFrame]:
    """
    Q4 (Python): How do boroughs compare in terms of request volume, types, and resolution efficiency?
    
    Borough-level analysis reveals geographic disparities in service delivery and community needs,
    informing equitable resource distribution.
    """
    sql = """
    SELECT
      b.name AS borough,
      ct.name AS complaint_type,
      COUNT(*) AS request_count,
      AVG(
        CASE
          WHEN sr.closed_date IS NOT NULL AND sr.created_date IS NOT NULL
          THEN (julianday(sr.closed_date) - julianday(sr.created_date)) * 24.0
        END
      ) AS avg_resolution_hours
    FROM service_requests sr
    LEFT JOIN borough b ON b.id = sr.borough_id
    LEFT JOIN complaint_type ct ON ct.id = sr.complaint_type_id
    WHERE b.name IS NOT NULL
      AND b.name != 'Unspecified'
      AND ct.name IS NOT NULL
    GROUP BY b.name, ct.name;
    """
    
    print_section_header(
        "QUESTION 4 (Python + Matplotlib)",
        "How do boroughs compare in terms of request volume, types, and resolution efficiency?",
        "Geographic analysis identifies disparities in service delivery and helps ensure equitable resource allocation."
    )
    
    df = query_to_df(conn, sql)
    
    # Top complaints by borough
    top_by_borough = (df.sort_values('request_count', ascending=False)
                      .groupby('borough')
                      .head(3))
    
    print_results_table(top_by_borough, "TOP 3 COMPLAINT TYPES BY BOROUGH", max_rows=15)
    
    # Overall borough statistics
    borough_stats = df.groupby('borough').agg({
        'request_count': 'sum',
        'avg_resolution_hours': 'mean'
    }).round(2)
    borough_stats = borough_stats.sort_values('request_count', ascending=False)
    borough_stats.columns = ['Total Requests', 'Avg Resolution Hours']
    
    print_results_table(borough_stats.reset_index(), "OVERALL BOROUGH STATISTICS")
    
    # Create visualizations
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Request volume by borough
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    ax1.barh(borough_stats.index, borough_stats['Total Requests'], color=colors, edgecolor='black')
    ax1.set_xlabel('Total Requests', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Borough', fontsize=12, fontweight='bold')
    ax1.set_title('Service Request Volume by Borough', fontsize=14, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3)
    
    # Add value labels
    for i, v in enumerate(borough_stats['Total Requests']):
        ax1.text(v, i, f'  {v:,.0f}', va='center')
    
    # Average resolution time by borough
    ax2.barh(borough_stats.index, borough_stats['Avg Resolution Hours'], color=colors, edgecolor='black')
    ax2.set_xlabel('Average Resolution Time (Hours)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Borough', fontsize=12, fontweight='bold')
    ax2.set_title('Average Resolution Time by Borough', fontsize=14, fontweight='bold')
    ax2.grid(axis='x', alpha=0.3)
    
    # Add value labels
    for i, v in enumerate(borough_stats['Avg Resolution Hours']):
        ax2.text(v, i, f'  {v:.1f}h', va='center')
    
    plt.tight_layout()
    out_png = os.path.join(OUTPUT_DIR, "q4_borough_comparison.png")
    plt.savefig(out_png, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"{OKGREEN}✓ Visualization saved to: {out_png}{ENDC}\n")
    
    borough_stats.to_csv(os.path.join(OUTPUT_DIR, "q4_borough_stats.csv"))
    return sql, borough_stats.reset_index()


def q5_time_series_trend_analysis(conn: sqlite3.Connection) -> Tuple[str, pd.DataFrame]:
    """
    Q5 (Python): What are the overall trends in service requests over time, and are there seasonal patterns?
    
    Time series analysis reveals growth trends and seasonal variations, helping forecast future demand
    and plan capacity.
    """
    sql = """
    SELECT
      date(substr(created_date, 1, 10)) AS request_date,
      COUNT(*) AS daily_count,
      substr(created_date, 1, 7) AS year_month
    FROM service_requests
    WHERE created_date IS NOT NULL
    GROUP BY request_date
    ORDER BY request_date;
    """
    
    print_section_header(
        "QUESTION 5 (Python + Matplotlib)",
        "What are the overall trends in service requests over time, and are there seasonal patterns?",
        "Time series analysis helps forecast demand, identify seasonal patterns, and plan resources accordingly."
    )
    
    df = query_to_df(conn, sql)
    df['request_date'] = pd.to_datetime(df['request_date'])
    
    # Calculate rolling averages
    df_sorted = df.sort_values('request_date').set_index('request_date')
    df_sorted['7_day_ma'] = df_sorted['daily_count'].rolling(window=7, min_periods=1).mean()
    df_sorted['30_day_ma'] = df_sorted['daily_count'].rolling(window=30, min_periods=1).mean()
    
    # Monthly aggregation
    monthly = df.groupby('year_month')['daily_count'].sum().reset_index()
    monthly.columns = ['Month', 'Total Requests']
    
    print_results_table(monthly.tail(12), "MONTHLY REQUEST VOLUMES (Last 12 Months)")
    
    # Create comprehensive time series plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))
    
    # Daily trend with moving averages
    ax1.plot(df_sorted.index, df_sorted['daily_count'], alpha=0.3, color='gray', label='Daily', linewidth=0.5)
    ax1.plot(df_sorted.index, df_sorted['7_day_ma'], color='blue', label='7-Day Moving Avg', linewidth=2)
    ax1.plot(df_sorted.index, df_sorted['30_day_ma'], color='red', label='30-Day Moving Avg', linewidth=2)
    ax1.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Number of Requests', fontsize=12, fontweight='bold')
    ax1.set_title('NYC 311 Service Requests: Daily Trend with Moving Averages', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Monthly bars
    monthly['month_date'] = pd.to_datetime(monthly['Month'] + '-01')
    ax2.bar(monthly['month_date'], monthly['Total Requests'], width=20, color='steelblue', edgecolor='black')
    ax2.set_xlabel('Month', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Total Requests', fontsize=12, fontweight='bold')
    ax2.set_title('Monthly Service Request Volume', fontsize=14, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Add value labels on bars
    for i, row in monthly.iterrows():
        ax2.text(row['month_date'], row['Total Requests'], f"{row['Total Requests']:,.0f}",
                ha='center', va='bottom', fontsize=8, rotation=90)
    
    plt.tight_layout()
    out_png = os.path.join(OUTPUT_DIR, "q5_time_series_trends.png")
    plt.savefig(out_png, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"{OKGREEN}✓ Visualization saved to: {out_png}{ENDC}\n")
    
    monthly.to_csv(os.path.join(OUTPUT_DIR, "q5_monthly_trends.csv"), index=False)
    return sql, monthly


def main():
    """Run all analysis questions."""
    print(f"\n{BOLD}{HEADER}{'=' * 100}{ENDC}")
    print(f"{BOLD}{HEADER}NYC 311 SERVICE REQUESTS - DATA ANALYSIS{ENDC}")
    print(f"{BOLD}{HEADER}{'=' * 100}{ENDC}\n")
    print(f"{OKCYAN}This analysis answers 5 meaningful questions about NYC 311 service request data:{ENDC}")
    print(f"{OKCYAN}  • 2 questions using pure SQL (Q1, Q2){ENDC}")
    print(f"{OKCYAN}  • 3 questions using Python data tooling - pandas & matplotlib (Q3, Q4, Q5){ENDC}\n")
    print(f"{WARNING}All visualizations and CSV exports are saved to: {OUTPUT_DIR}{ENDC}\n")
    
    db_path = get_db_path()
    
    with closing(sqlite3.connect(db_path)) as conn:
        # Run all analysis questions
        q1_busiest_agencies_by_workload(conn)
        q2_complaint_types_by_resolution_difficulty(conn)
        q3_temporal_patterns_analysis(conn)
        q4_borough_comparison_analysis(conn)
        q5_time_series_trend_analysis(conn)
    
    print(f"\n{BOLD}{OKGREEN}{'=' * 100}{ENDC}")
    print(f"{BOLD}{OKGREEN}✓ ANALYSIS COMPLETE! All results saved to {OUTPUT_DIR}{ENDC}")
    print(f"{BOLD}{OKGREEN}{'=' * 100}{ENDC}\n")


if __name__ == "__main__":
    main()
