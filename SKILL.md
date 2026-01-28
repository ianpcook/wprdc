---
name: wprdc
description: Query Pittsburgh's Western PA Regional Data Center (WPRDC) — 363+ datasets covering property assessments, air quality, 311 requests, jail census, overdose data, permits, violations, and more. Run SQL queries against live tables without downloading. Use when user asks about Pittsburgh/Allegheny County public data, property lookups, civic data, or regional statistics.
version: 1.0.0
homepage: https://data.wprdc.org
metadata:
  clawdbot:
    emoji: 📊
  tags:
    - pittsburgh
    - civic-data
    - wprdc
    - ckan
    - property
    - public-data
    - allegheny-county
---

# WPRDC - Pittsburgh Regional Data Center

Query 363+ datasets from the Western PA Regional Data Center. Property assessments, air quality, 311 requests, jail census, overdose data, parking, permits, violations — all queryable via SQL without downloading.

## Quick Start

```bash
# Search for datasets
<skill>/wprdc.py search "property sales"
<skill>/wprdc.py search "air quality" --org allegheny-county

# Get dataset info
<skill>/wprdc.py info property-assessments

# List resources (tables) in a dataset
<skill>/wprdc.py resources property-assessments

# See field schema
<skill>/wprdc.py fields assessments

# SQL query (the killer feature!)
<skill>/wprdc.py query 'SELECT "PARID", "PROPERTYADDRESS" FROM @assessments WHERE "PROPERTYCITY"='"'"'PITTSBURGH'"'"' LIMIT 5'

# Quick parcel lookup
<skill>/wprdc.py parcel 0028F00194000000

# Download a dataset
<skill>/wprdc.py download property-assessments --format csv
```

## Commands

### `search <query>`
Search for datasets by keyword.

Options:
- `--org <name>` — Filter by organization (e.g., `allegheny-county`, `city-of-pittsburgh`)
- `--group <name>` — Filter by topic group (e.g., `health`, `housing-properties`)
- `--limit <n>` — Max results (default: 10)
- `--json` — Raw JSON output

### `info <dataset>`
Get detailed information about a dataset, including description, resources, and metadata.

### `resources <dataset>`
List all resources (tables/files) in a dataset with their IDs and queryability status.

### `fields <resource>`
Show the field schema for a resource. Use shortcut names or resource IDs.

### `query <sql>`
Execute SQL queries against live data. **This is the power feature!**

**Important:** Column names must be double-quoted because PostgreSQL is case-sensitive:
```sql
SELECT "PARID", "PROPERTYADDRESS" FROM @assessments WHERE "PROPERTYCITY"='PITTSBURGH' LIMIT 5
```

Use `@shortcut` notation for common tables (see Shortcuts below).

Options:
- `--json` — Raw JSON output
- `--table` — Format as ASCII table

### `parcel <pin>`
Quick property lookup by parcel ID. Returns address, assessments, building info, and last sale.

```bash
<skill>/wprdc.py parcel 0028F00194000000
```

### `download <dataset>`
Download a resource to a file.

Options:
- `--resource <id|name>` — Specific resource
- `--format <csv|json|geojson>` — Preferred format
- `--output <path>` — Output filename

### `orgs`
List all organizations publishing data.

### `groups`
List all topic groups (categories).

### `shortcuts`
Show available query shortcuts.

## Query Shortcuts

Use `@shortcut` in SQL queries instead of long resource IDs:

| Shortcut | Dataset |
|----------|---------|
| `@assessments` | Property Assessments (584K parcels) |
| `@sales` | Property Sales |
| `@311` | 311 Service Requests |
| `@permits` | PLI Permits |
| `@violations` | PLI Violations |
| `@overdoses` | Fatal Accidental Overdoses |
| `@jail` | Jail Daily Census |
| `@air-quality` | Air Quality |
| `@fishfry` | Fish Fry Map |

Example:
```bash
<skill>/wprdc.py query 'SELECT * FROM @overdoses WHERE "death_year"=2024 LIMIT 10'
```

## SQL Query Tips

1. **Quote UPPERCASE column names** — PostgreSQL is case-sensitive:
   ```sql
   SELECT "PROPERTYADDRESS" FROM @assessments  -- ✓ uppercase needs quotes
   SELECT case_year FROM @overdoses            -- ✓ lowercase works without quotes
   ```

2. **Use `LIMIT`** — Large tables can timeout without limits

3. **Check fields first** — Use `fields <resource>` to see available columns

4. **Aggregate queries work**:
   ```sql
   SELECT "PROPERTYCITY", COUNT(*) as cnt 
   FROM @assessments 
   GROUP BY "PROPERTYCITY" 
   ORDER BY cnt DESC 
   LIMIT 10
   ```

## Organizations

Major data publishers:
- **allegheny-county** — 143 datasets (assessments, health, jail, elections)
- **city-of-pittsburgh** — 126 datasets (311, permits, violations, budget)
- **pittsburgh-regional-transit** — 9 datasets (bus routes, ridership)
- **ppa** — 5 datasets (parking transactions)
- **pwsa** — 4 datasets (water/sewer)

## Topic Groups

- **housing-properties** — Property data, assessments, sales
- **health** — Overdoses, air quality, COVID, health indicators
- **public-safety-justice** — 911 calls, jail census, police data
- **transportation** — Transit, parking, bike infrastructure
- **environment** — Air quality, land use, green spaces
- **civic-vitality-governance** — 311, budgets, elections

## Example Queries

**"What's the assessed value of this property?"**
```bash
<skill>/wprdc.py parcel 0001A00001000000
```

**"Show recent 311 requests about potholes"**
```bash
<skill>/wprdc.py query 'SELECT "CREATED_ON", "REQUEST_TYPE", "ADDRESS" FROM @311 WHERE "REQUEST_TYPE" LIKE '"'"'%Pothole%'"'"' ORDER BY "CREATED_ON" DESC LIMIT 10'
```

**"How many overdose deaths per year?"**
```bash
<skill>/wprdc.py query 'SELECT case_year, COUNT(*) as deaths FROM @overdoses GROUP BY case_year ORDER BY case_year'
```

**"Find datasets about transit"**
```bash
<skill>/wprdc.py search "transit" --org pittsburgh-regional-transit
```

**"Download air quality data"**
```bash
<skill>/wprdc.py download allegheny-county-air-quality --format csv
```

## Data Source

All data from [Western PA Regional Data Center](https://data.wprdc.org), powered by CKAN.

Data is maintained by various regional organizations including Allegheny County, City of Pittsburgh, PWSA, PRT, and community groups. Update frequencies vary by dataset — check `info <dataset>` for details.

## Combining with Other Skills

This skill pairs well with:
- **fishfry** — Fish fry data is also on WPRDC
- **plow-tracker** — Cross-reference with 311 snow complaints
- **goplaces** — Geocode addresses for location-based queries
