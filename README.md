# WPRDC - Pittsburgh Regional Data Center

Query 363+ datasets from the [Western PA Regional Data Center](https://data.wprdc.org). Property assessments, air quality, 311 requests, jail census, overdose data, parking, permits, violations — all queryable via SQL without downloading.

An [Agent Skill](https://skills.sh) — works with Claude Code, Clawdbot, Cursor, Windsurf, Cline, and any agent that supports the open skills format.

## Installation

```bash
npx skills add ianpcook/wprdc
```

## Features

- **Search** datasets by keyword, organization, or topic
- **SQL queries** against live tables (no download required!)
- **Property lookups** by parcel ID or address
- **Download** resources as CSV, JSON, or GeoJSON
- **363+ datasets** from Allegheny County, City of Pittsburgh, PRT, and more

## Quick Examples

```bash
# Search for datasets
wprdc.py search "property sales"
wprdc.py search "air quality" --org allegheny-county

# Property lookup by parcel ID
wprdc.py parcel 0028F00194000000

# SQL query (the killer feature!)
wprdc.py query 'SELECT "PROPERTYADDRESS", "FAIRMARKETTOTAL" FROM @assessments WHERE "PROPERTYCITY"='"'"'PITTSBURGH'"'"' LIMIT 5'

# Overdose trends
wprdc.py query 'SELECT case_year, COUNT(*) as deaths FROM @overdoses GROUP BY case_year ORDER BY case_year'

# Dataset info
wprdc.py info property-assessments
```

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

## Commands

| Command | Description |
|---------|-------------|
| `search <query>` | Search datasets by keyword |
| `info <dataset>` | Get dataset details |
| `resources <dataset>` | List tables/files in a dataset |
| `fields <resource>` | Show column schema |
| `query <sql>` | Execute SQL against live data |
| `parcel <pin>` | Quick property lookup |
| `download <dataset>` | Export to CSV/JSON/GeoJSON |
| `orgs` | List publishing organizations |
| `groups` | List topic categories |
| `shortcuts` | Show query shortcuts |

## Data Highlights

**Property & Housing**
- 584K property assessments with values, sales, building details
- Real estate transactions since 2013
- Code violations and permits

**Public Safety**
- Jail daily census (demographics, trends)
- Fatal overdoses by year, drug type, location
- 911 EMS/Fire dispatches (2015-present)

**Transportation**
- Parking transactions
- Transit routes and ridership

**Health & Environment**
- Air quality monitor readings
- Temperature inversion forecasts

## SQL Tips

1. **Quote UPPERCASE columns**: `"PROPERTYADDRESS"` (lowercase works without: `case_year`)
2. **Use LIMIT**: Large tables timeout without limits
3. **Check fields first**: `wprdc.py fields @assessments`

## License

MIT

## Links

- [WPRDC Portal](https://data.wprdc.org)
- [skills.sh](https://skills.sh) — The open agent skills ecosystem
