PRAGMA foreign_keys = ON;

-- Dimensions
CREATE TABLE IF NOT EXISTS agency (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS complaint_type (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS descriptor (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS borough (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

-- Fact table
CREATE TABLE IF NOT EXISTS service_requests (
  unique_key INTEGER PRIMARY KEY,
  created_date TEXT NOT NULL,
  closed_date TEXT,
  resolution_description TEXT,
  incident_zip TEXT,
  latitude REAL,
  longitude REAL,
  agency_id INTEGER,
  complaint_type_id INTEGER,
  descriptor_id INTEGER,
  borough_id INTEGER,
  CONSTRAINT fk_agency FOREIGN KEY (agency_id) REFERENCES agency(id),
  CONSTRAINT fk_complaint_type FOREIGN KEY (complaint_type_id) REFERENCES complaint_type(id),
  CONSTRAINT fk_descriptor FOREIGN KEY (descriptor_id) REFERENCES descriptor(id),
  CONSTRAINT fk_borough FOREIGN KEY (borough_id) REFERENCES borough(id)
);

-- Indexes for analytics
CREATE INDEX IF NOT EXISTS idx_sr_created_date ON service_requests(created_date);
CREATE INDEX IF NOT EXISTS idx_sr_closed_date ON service_requests(closed_date);
CREATE INDEX IF NOT EXISTS idx_sr_complaint_type ON service_requests(complaint_type_id);
CREATE INDEX IF NOT EXISTS idx_sr_borough ON service_requests(borough_id); 