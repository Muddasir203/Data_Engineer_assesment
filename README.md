# NYC 311 Service Requests Data Pipeline

A complete data engineering pipeline that ingests NYC 311 service request data, models it in SQLite, and provides comprehensive analysis with SQL and Python visualizations.

## 🎯 Project Overview

This project demonstrates a full data pipeline from ingestion to insights:
- **Data Ingestion**: Fetches NYC 311 data via Socrata API with pagination and error handling
- **Data Modeling**: Normalized SQLite schema with proper foreign keys and indexes
- **Analysis**: 5 meaningful questions answered with SQL and Python (pandas + matplotlib)
- **Visualization**: Professional charts and tables for decision-making insights

## 📋 Prerequisites

- **Python 3.10+**
- **SQLite 3.35+**


## 🚀 Quick Start

### 1. Setup Environment
```bash
# Clone the repository
git clone https://github.com/Muddasir203/Data_Engineer_assesment.git
cd Data_Engineer_assesment

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Complete Pipeline
```bash
# Build database and run analysis (one command)
make run
```

This will:
1. Download NYC 311 data (last 1 day by default - optimized for <20MB database)
2. Create SQLite database with normalized schema
3. Run comprehensive analysis with 5 questions
4. Generate visualizations and CSV outputs

### 3. View Results
- **Terminal**: Color-coded analysis results with insights
- **Files**: Check `outputs/` directory for:
  - CSV files with analysis data
  - PNG visualizations (300 DPI, publication-ready)

## 📊 Analysis Questions

The pipeline answers 5 meaningful questions about NYC 311 data:

### Q1: Agency Performance (SQL)
**Question**: Which agencies handle the most service requests, and what is their resolution rate?
**Insight**: Identifies agency workload and performance metrics for resource allocation

### Q2: Resolution Difficulty (SQL)  
**Question**: What are the most difficult complaint types to resolve?
**Insight**: Reveals process improvement opportunities and citizen expectation management

### Q3: Temporal Patterns (Python + Matplotlib)
**Question**: How do service request volumes vary by day of week and hour?
**Insight**: Optimizes staffing schedules and identifies peak demand periods

### Q4: Borough Comparison (Python + Matplotlib)
**Question**: How do boroughs compare in request volume and resolution efficiency?
**Insight**: Ensures equitable resource distribution and identifies geographic disparities

### Q5: Time Series Trends (Python + Matplotlib)
**Question**: What are the overall trends and seasonal patterns?
**Insight**: Enables demand forecasting and capacity planning with moving averages

## 🗂️ Project Structure

```
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── Makefile                 # Build automation
├── schema.sql              # Database schema
├── analysis.py             # Main analysis script
├── src/
│   ├── __init__.py
│   ├── db.py              # Database utilities
│   └── etl.py             # Data ingestion pipeline
├── tests/
│   ├── conftest.py        # Test configuration
│   └── test_etl_smoke.py  # ETL tests
├── tools/
│   └── gen_er_diagram.py  # Schema visualization
└── outputs/               # Analysis results
    ├── *.csv             # Data tables
    └── *.png             # Visualizations
```

## 🛠️ Available Commands

```bash
# Complete pipeline (ETL + Analysis)
make run

# Individual steps
make etl        # Download data and build database
make analysis   # Run analysis and generate outputs
make test       # Run test suite
make clean      # Remove database and outputs

# Direct execution
python -m src.etl      # ETL only
python analysis.py     # Analysis only
```

## 🗄️ Database Schema

The pipeline creates a normalized SQLite schema:

```sql
-- Dimensions
agency(id PK, name UNIQUE)
complaint_type(id PK, name UNIQUE)  
descriptor(id PK, name UNIQUE)
borough(id PK, name UNIQUE)

-- Fact table
service_requests(
  unique_key PK,
  created_date, closed_date, resolution_description,
  incident_zip, latitude, longitude,
  agency_id FK, complaint_type_id FK, descriptor_id FK, borough_id FK
)
```

**Key Features**:
- Proper foreign key relationships
- Indexes on analytical columns (date, complaint_type, borough)
- Normalized design for efficient queries
- Optimized for <10MB database size

## 📈 Sample Insights

### Agency Performance
- **NYPD**: Handles majority of requests with high resolution rates
- **DOB**: Perfect resolution rate for building-related complaints
- **TLC**: Lower resolution rates indicating process improvement opportunities

### Temporal Patterns
- **Peak days**: Monday typically busiest
- **Peak hours**: Business hours (8 AM - 5 PM)
- **Seasonal trends**: Clear patterns with moving averages for forecasting

### Geographic Distribution
- **Volume variations**: Brooklyn typically highest volume
- **Top complaints**: "Illegal Parking" across all boroughs
- **Resolution times**: Similar patterns across boroughs

## 🧪 Testing

```bash
# Run all tests
make test

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_etl_smoke.py -v
```

**Test Coverage**:
- ETL pipeline smoke tests
- Database connectivity
- Data quality checks
- Analysis script execution

## 📦 Dependencies

Core dependencies in `requirements.txt`:
- `pandas>=2.2.2` - Data manipulation and analysis
- `matplotlib>=3.9.0` - Visualization
- `requests>=2.32.3` - API communication
- `tenacity>=9.0.0` - Retry logic
- `pytest>=8.3.2` - Testing framework

## 🔧 Technical Features

### Data Pipeline
- **Idempotent ETL**: Safe to re-run, uses UPSERTs
- **Pagination**: Handles large datasets efficiently
- **Error Handling**: Retry logic with exponential backoff
- **Rate Limiting**: Respects API limits
- **Optimized Size**: <10MB database for fast cloning

### Analysis
- **SQL Queries**: Window functions, aggregations, date calculations
- **Python Tooling**: pandas groupby, rolling averages, time series
- **Visualizations**: Professional charts with 300 DPI resolution
- **Terminal Output**: Color-coded, formatted results

### Code Quality
- **Type Hints**: Full type annotations
- **Documentation**: Comprehensive docstrings
- **Modular Design**: Separated concerns (ETL vs Analysis)
- **Testing**: Automated test suite


## 📊 Output Files

After running analysis, check `outputs/` directory:

### CSV Files (Data)
- `q1_busiest_agencies.csv` - Agency performance metrics
- `q2_resolution_difficulty.csv` - Complaint resolution times  
- `q4_borough_stats.csv` - Borough-level statistics
- `q5_monthly_trends.csv` - Monthly request volumes

### PNG Files (Visualizations)
- `q3_temporal_patterns.png` - Day/hour patterns (dual chart)
- `q4_borough_comparison.png` - Borough comparison (dual chart)
- `q5_time_series_trends.png` - Time series trends (dual chart)

**Ready to run**: `make run` 🚀
