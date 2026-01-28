#!/usr/bin/env python3
"""
WPRDC CLI - Query Pittsburgh's Regional Data Center

Uses CKAN API to search datasets, run SQL queries, and download data.
https://data.wprdc.org
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional

BASE_URL = "https://data.wprdc.org/api/3/action"

# Common resource IDs for shortcuts
SHORTCUTS = {
    "assessments": "65855e14-549e-4992-b5be-d629afc676fa",  # Property Assessments (API version)
    "sales": "2c13021f-74a9-4289-a1e5-fe0472c89881",  # Property Sales
    "311": "76fda9d0-69be-4dd5-8108-0de7907fc5a4",  # 311 Data
    "permits": "f8ab32f7-44c7-43ca-98bf-c1b444724598",  # PLI Permits
    "violations": "4e5374be-1a88-47f7-afee-6a79317019b4",  # PLI Violations  
    "overdoses": "1c59b26a-1684-4bfb-92f7-205b947530cf",  # Fatal Overdoses
    "jail": "25fb2d57-dbef-4e4c-83c8-3d1f39f6ab85",  # Jail Daily Census
    "air-quality": "4aaa6785-f178-4cfe-a7e5-9a08e96a24dc",  # Air Quality
    "fishfry": "3703e134-cfe0-4660-8a2e-f61458ebcbb1",  # Fish Fry Map
}


def api_call(action: str, params: Optional[dict] = None) -> dict:
    """Make a CKAN API call."""
    url = f"{BASE_URL}/{action}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode())
            if not data.get("success"):
                print(f"API error: {data.get('error', 'Unknown error')}", file=sys.stderr)
                sys.exit(1)
            return data["result"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        try:
            error_data = json.loads(error_body)
            print(f"API error: {error_data.get('error', {}).get('message', str(e))}", file=sys.stderr)
        except:
            print(f"HTTP error {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)
        sys.exit(1)


def sql_query(sql: str) -> dict:
    """Execute a SQL query against the datastore."""
    # The SQL endpoint needs special handling
    url = f"{BASE_URL}/datastore_search_sql"
    params = {"sql": sql}
    url += "?" + urllib.parse.urlencode(params)
    
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            data = json.loads(response.read().decode())
            if not data.get("success"):
                error = data.get("error", {})
                if isinstance(error, dict):
                    print(f"SQL error: {error.get('message', error)}", file=sys.stderr)
                else:
                    print(f"SQL error: {error}", file=sys.stderr)
                sys.exit(1)
            return data["result"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        try:
            error_data = json.loads(error_body)
            err = error_data.get("error", {})
            if isinstance(err, dict):
                print(f"SQL error: {err.get('message', str(e))}", file=sys.stderr)
            else:
                print(f"SQL error: {err}", file=sys.stderr)
        except:
            print(f"HTTP error {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(1)


def cmd_search(args):
    """Search for datasets."""
    params = {"q": args.query, "rows": args.limit}
    
    if args.org:
        params["fq"] = f"organization:{args.org}"
    if args.group:
        fq = params.get("fq", "")
        params["fq"] = f"{fq} groups:{args.group}".strip()
    
    result = api_call("package_search", params)
    
    if args.json:
        print(json.dumps(result, indent=2))
        return
    
    count = result.get("count", 0)
    datasets = result.get("results", [])
    
    print(f"Found {count} datasets (showing {len(datasets)}):\n")
    
    for ds in datasets:
        name = ds.get("name", "unknown")
        title = ds.get("title", name)
        org = ds.get("organization", {}).get("title", "Unknown")
        notes = ds.get("notes", "")[:150].replace("\n", " ").replace("\r", "")
        if len(ds.get("notes", "")) > 150:
            notes += "..."
        num_resources = ds.get("num_resources", 0)
        
        print(f"📊 {title}")
        print(f"   ID: {name}")
        print(f"   Org: {org} | Resources: {num_resources}")
        if notes:
            print(f"   {notes}")
        print()


def cmd_info(args):
    """Get detailed info about a dataset."""
    result = api_call("package_show", {"id": args.dataset})
    
    if args.json:
        print(json.dumps(result, indent=2))
        return
    
    title = result.get("title", result.get("name"))
    org = result.get("organization", {}).get("title", "Unknown")
    notes = result.get("notes", "No description")
    license_title = result.get("license_title", "Unknown")
    steward = result.get("data_steward_name", "Unknown")
    steward_email = result.get("data_steward_email", "")
    freq_change = result.get("frequency_data_change", "Unknown")
    freq_publish = result.get("frequency_publishing", "Unknown")
    modified = result.get("metadata_modified", "")[:10]
    
    print(f"📊 {title}")
    print(f"   Organization: {org}")
    print(f"   License: {license_title}")
    print(f"   Data Steward: {steward}" + (f" ({steward_email})" if steward_email else ""))
    print(f"   Updates: {freq_change} changes, {freq_publish} publishing")
    print(f"   Last Modified: {modified}")
    print()
    
    # Clean up notes for display
    notes_clean = notes.replace("\r\n", "\n").replace("\r", "\n")
    # Take first paragraph or first 500 chars
    first_para = notes_clean.split("\n\n")[0][:500]
    if len(first_para) < len(notes_clean.split("\n\n")[0]):
        first_para += "..."
    print("Description:")
    print(first_para)
    print()
    
    # List resources
    resources = result.get("resources", [])
    if resources:
        print(f"Resources ({len(resources)}):")
        for r in resources:
            r_name = r.get("name", "Unnamed")
            r_format = r.get("format", "?")
            r_id = r.get("id", "")
            datastore = "✓ queryable" if r.get("datastore_active") else ""
            print(f"   • {r_name} [{r_format}] {datastore}")
            print(f"     ID: {r_id}")


def cmd_resources(args):
    """List resources in a dataset."""
    result = api_call("package_show", {"id": args.dataset})
    resources = result.get("resources", [])
    
    if args.json:
        print(json.dumps(resources, indent=2))
        return
    
    print(f"Resources in '{result.get('title', args.dataset)}':\n")
    
    for r in resources:
        name = r.get("name", "Unnamed")
        fmt = r.get("format", "?")
        rid = r.get("id", "")
        size = r.get("size")
        datastore = r.get("datastore_active", False)
        modified = r.get("last_modified", "")[:10] if r.get("last_modified") else ""
        
        size_str = ""
        if size:
            if size > 1_000_000_000:
                size_str = f" ({size / 1_000_000_000:.1f} GB)"
            elif size > 1_000_000:
                size_str = f" ({size / 1_000_000:.1f} MB)"
            elif size > 1_000:
                size_str = f" ({size / 1_000:.1f} KB)"
        
        status = "✓ SQL-queryable" if datastore else "download only"
        
        print(f"📄 {name}")
        print(f"   Format: {fmt}{size_str} | {status}")
        print(f"   ID: {rid}")
        if modified:
            print(f"   Modified: {modified}")
        print()


def cmd_fields(args):
    """Show field schema for a resource."""
    # Resolve shortcuts
    resource_id = SHORTCUTS.get(args.resource, args.resource)
    
    result = api_call("datastore_search", {"resource_id": resource_id, "limit": 0})
    fields = result.get("fields", [])
    
    if args.json:
        print(json.dumps(fields, indent=2))
        return
    
    print(f"Fields in resource:\n")
    
    for f in fields:
        fid = f.get("id", "")
        ftype = f.get("type", "?")
        if fid.startswith("_"):
            continue  # Skip internal fields
        print(f"   {fid}: {ftype}")


def cmd_query(args):
    """Execute a SQL query."""
    sql = args.sql
    
    # Handle shortcut table names
    for shortcut, resource_id in SHORTCUTS.items():
        sql = sql.replace(f"@{shortcut}", f'"{resource_id}"')
    
    result = sql_query(sql)
    records = result.get("records", [])
    
    if args.json:
        print(json.dumps(records, indent=2))
        return
    
    if not records:
        print("No results.")
        return
    
    # Get field order from first record
    fields = [k for k in records[0].keys() if not k.startswith("_")]
    
    # Print as table (simple format)
    if args.table:
        # Calculate column widths
        widths = {}
        for f in fields:
            widths[f] = max(len(f), max(len(str(r.get(f, ""))[:50]) for r in records))
            widths[f] = min(widths[f], 50)  # Cap at 50 chars
        
        # Header
        header = " | ".join(f.ljust(widths[f])[:widths[f]] for f in fields)
        print(header)
        print("-" * len(header))
        
        # Rows
        for r in records:
            row = " | ".join(str(r.get(f, "")).ljust(widths[f])[:widths[f]] for f in fields)
            print(row)
    else:
        # Print as list of records
        for i, r in enumerate(records):
            if i > 0:
                print("---")
            for f in fields:
                val = r.get(f, "")
                if val is not None and val != "":
                    print(f"{f}: {val}")


def cmd_download(args):
    """Download a resource."""
    # Get dataset info
    result = api_call("package_show", {"id": args.dataset})
    resources = result.get("resources", [])
    
    # Find the requested resource
    target = None
    for r in resources:
        if args.resource:
            if r.get("id") == args.resource or r.get("name", "").lower() == args.resource.lower():
                target = r
                break
        elif args.format:
            if r.get("format", "").upper() == args.format.upper():
                target = r
                break
    
    if not target and not args.resource and not args.format:
        # Default to first resource
        target = resources[0] if resources else None
    
    if not target:
        print(f"Resource not found. Available resources:", file=sys.stderr)
        for r in resources:
            print(f"  - {r.get('name')} [{r.get('format')}] ID: {r.get('id')}", file=sys.stderr)
        sys.exit(1)
    
    url = target.get("url")
    if not url:
        print("No download URL for this resource.", file=sys.stderr)
        sys.exit(1)
    
    # Determine output filename
    if args.output:
        output = Path(args.output)
    else:
        ext = target.get("format", "csv").lower()
        output = Path(f"{args.dataset}.{ext}")
    
    print(f"Downloading {target.get('name')} to {output}...")
    
    try:
        urllib.request.urlretrieve(url, output)
        size = output.stat().st_size
        if size > 1_000_000:
            print(f"Downloaded {size / 1_000_000:.1f} MB")
        else:
            print(f"Downloaded {size / 1_000:.1f} KB")
    except Exception as e:
        print(f"Download failed: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_orgs(args):
    """List organizations."""
    result = api_call("organization_list", {"all_fields": True})
    
    if args.json:
        print(json.dumps(result, indent=2))
        return
    
    print("Organizations:\n")
    for org in result:
        if isinstance(org, dict):
            name = org.get("name", "")
            title = org.get("title", name)
            count = org.get("package_count", 0)
            print(f"   {name}: {title} ({count} datasets)")
        else:
            print(f"   {org}")


def cmd_groups(args):
    """List topic groups."""
    result = api_call("group_list", {"all_fields": True})
    
    if args.json:
        print(json.dumps(result, indent=2))
        return
    
    print("Topic Groups:\n")
    for grp in result:
        if isinstance(grp, dict):
            name = grp.get("name", "")
            title = grp.get("title", name)
            count = grp.get("package_count", 0)
            print(f"   {name}: {title} ({count} datasets)")
        else:
            print(f"   {grp}")


def cmd_parcel(args):
    """Quick parcel lookup by PIN."""
    pin = args.pin.upper().replace("-", "").replace(" ", "")
    
    # Pad to 16 chars if needed
    if len(pin) < 16:
        pin = pin.ljust(16, "0")
    
    sql = f'''
        SELECT "PARID", "PROPERTYHOUSENUM", "PROPERTYADDRESS", "PROPERTYCITY", "PROPERTYZIP",
               "MUNIDESC", "SCHOOLDESC", "CLASSDESC", "USEDESC", "LOTAREA",
               "FAIRMARKETTOTAL", "COUNTYTOTAL", "LOCALTOTAL",
               "YEARBLT", "STORIES", "BEDROOMS", "FULLBATHS", "FINISHEDLIVINGAREA",
               "SALEDATE", "SALEPRICE"
        FROM "{SHORTCUTS['assessments']}"
        WHERE "PARID" = '{pin}'
    '''
    
    result = sql_query(sql)
    records = result.get("records", [])
    
    if args.json:
        print(json.dumps(records, indent=2))
        return
    
    if not records:
        print(f"No parcel found for PIN: {pin}")
        return
    
    r = records[0]
    
    addr_parts = [r.get("PROPERTYHOUSENUM", ""), r.get("PROPERTYADDRESS", "")]
    addr = " ".join(p for p in addr_parts if p and p.strip()).strip()
    city = r.get("PROPERTYCITY", "")
    zip_code = r.get("PROPERTYZIP", "")
    
    print(f"🏠 Parcel: {r.get('PARID', pin)}")
    print(f"   Address: {addr}, {city} {zip_code}")
    print(f"   Municipality: {r.get('MUNIDESC', 'Unknown')}")
    print(f"   School District: {r.get('SCHOOLDESC', 'Unknown')}")
    print(f"   Class: {r.get('CLASSDESC', 'Unknown')} - {r.get('USEDESC', 'Unknown')}")
    print()
    
    lot = r.get("LOTAREA")
    if lot:
        print(f"   Lot Area: {lot:,.0f} sq ft")
    
    fmv = r.get("FAIRMARKETTOTAL")
    county = r.get("COUNTYTOTAL")
    local = r.get("LOCALTOTAL")
    if fmv:
        print(f"   Fair Market Value: ${fmv:,.0f}")
    if county:
        print(f"   County Assessment: ${county:,.0f}")
    if local:
        print(f"   Local Assessment: ${local:,.0f}")
    print()
    
    year = r.get("YEARBLT")
    stories = r.get("STORIES")
    beds = r.get("BEDROOMS")
    baths = r.get("FULLBATHS")
    sqft = r.get("FINISHEDLIVINGAREA")
    
    if any([year, stories, beds, baths, sqft]):
        print("   Building:")
        if year:
            print(f"      Year Built: {int(year)}")
        if stories:
            print(f"      Stories: {stories}")
        if beds:
            print(f"      Bedrooms: {int(beds)}")
        if baths:
            print(f"      Bathrooms: {int(baths)}")
        if sqft:
            print(f"      Living Area: {sqft:,.0f} sq ft")
        print()
    
    sale_date = r.get("SALEDATE")
    sale_price = r.get("SALEPRICE")
    if sale_date or sale_price:
        print("   Last Sale:")
        if sale_date:
            print(f"      Date: {sale_date}")
        if sale_price:
            print(f"      Price: ${sale_price:,.0f}")


def cmd_shortcuts(args):
    """Show available query shortcuts."""
    print("Query shortcuts (use @name in SQL):\n")
    for name, rid in SHORTCUTS.items():
        print(f"   @{name}")
        print(f"      {rid}")
        print()
    print("Example: wprdc query \"SELECT * FROM @assessments WHERE PROPERTYCITY='PITTSBURGH' LIMIT 5\"")


def main():
    parser = argparse.ArgumentParser(
        description="Query Pittsburgh's Western PA Regional Data Center (WPRDC)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  wprdc search "property sales"
  wprdc search "air quality" --org allegheny-county
  wprdc info property-assessments
  wprdc resources property-assessments
  wprdc fields assessments
  wprdc query "SELECT * FROM @assessments WHERE PROPERTYCITY='PITTSBURGH' LIMIT 5"
  wprdc parcel 0001A00001000000
  wprdc download property-assessments --format csv
  wprdc shortcuts
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # search
    p_search = subparsers.add_parser("search", help="Search for datasets")
    p_search.add_argument("query", help="Search terms")
    p_search.add_argument("--org", help="Filter by organization")
    p_search.add_argument("--group", help="Filter by topic group")
    p_search.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")
    p_search.add_argument("--json", action="store_true", help="Output raw JSON")
    p_search.set_defaults(func=cmd_search)
    
    # info
    p_info = subparsers.add_parser("info", help="Get dataset details")
    p_info.add_argument("dataset", help="Dataset ID or name")
    p_info.add_argument("--json", action="store_true", help="Output raw JSON")
    p_info.set_defaults(func=cmd_info)
    
    # resources
    p_res = subparsers.add_parser("resources", help="List dataset resources")
    p_res.add_argument("dataset", help="Dataset ID or name")
    p_res.add_argument("--json", action="store_true", help="Output raw JSON")
    p_res.set_defaults(func=cmd_resources)
    
    # fields
    p_fields = subparsers.add_parser("fields", help="Show resource field schema")
    p_fields.add_argument("resource", help="Resource ID or shortcut name")
    p_fields.add_argument("--json", action="store_true", help="Output raw JSON")
    p_fields.set_defaults(func=cmd_fields)
    
    # query
    p_query = subparsers.add_parser("query", help="Execute SQL query")
    p_query.add_argument("sql", help="SQL query (use @shortcut for common tables)")
    p_query.add_argument("--json", action="store_true", help="Output raw JSON")
    p_query.add_argument("--table", action="store_true", help="Format as table")
    p_query.set_defaults(func=cmd_query)
    
    # download
    p_dl = subparsers.add_parser("download", help="Download a resource")
    p_dl.add_argument("dataset", help="Dataset ID or name")
    p_dl.add_argument("--resource", help="Resource ID or name")
    p_dl.add_argument("--format", help="Preferred format (csv, json, geojson)")
    p_dl.add_argument("--output", "-o", help="Output filename")
    p_dl.set_defaults(func=cmd_download)
    
    # orgs
    p_orgs = subparsers.add_parser("orgs", help="List organizations")
    p_orgs.add_argument("--json", action="store_true", help="Output raw JSON")
    p_orgs.set_defaults(func=cmd_orgs)
    
    # groups
    p_grps = subparsers.add_parser("groups", help="List topic groups")
    p_grps.add_argument("--json", action="store_true", help="Output raw JSON")
    p_grps.set_defaults(func=cmd_groups)
    
    # parcel (shortcut)
    p_parcel = subparsers.add_parser("parcel", help="Quick parcel lookup by PIN")
    p_parcel.add_argument("pin", help="Parcel ID (e.g., 0001A00001000000)")
    p_parcel.add_argument("--json", action="store_true", help="Output raw JSON")
    p_parcel.set_defaults(func=cmd_parcel)
    
    # shortcuts
    p_shortcuts = subparsers.add_parser("shortcuts", help="Show query shortcuts")
    p_shortcuts.set_defaults(func=cmd_shortcuts)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
