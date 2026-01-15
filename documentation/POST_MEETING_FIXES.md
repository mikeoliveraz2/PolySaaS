# Post-Meeting Fixes - Multi-Tenant Schema Issue

## Problem
**CRITICAL:** All tenant-specific data is in `public` schema instead of tenant schemas (`olient`, etc.)

### Affected Models:
- ✅ PassThroughEndpoint - All in `public`, `olient` has 0 rows
- ✅ MonitorLogger - All in `public`, should be in `olient`
- ⚠️ Other models likely affected too (check all tenant-specific models)

### Current State:
- Endpoint ID 2 is in `public` schema pointing to old URL (oliverenterprises.app.saasify.cloud)
- `olient` schema has 0 rows for most tenant-specific models
- Data isolation is broken - all tenants see the same data

## For Demo Tomorrow
- Using endpoint ID 2 in `public` schema (works for now)
- Endpoint points to: `https://oliverenterprises.app.saasify.cloud/scp/`
- Auto-Login and passthrough work with this endpoint

## After Meeting - Fixes Needed

### 1. Audit All Models
Identify which models should be tenant-specific:
- PassThroughEndpoint ✅ (known)
- MonitorLogger ✅ (known)
- CallbackData? (check)
- Other models? (audit needed)

### 2. Create Migration Script
Create script to migrate all tenant-specific data from `public` to `olient`:
- PassThroughEndpoint
- MonitorLogger
- Any other tenant-specific models

### 3. Fix Schema Switching
Ensure middleware properly switches to tenant schema:
- `SessionTenantMiddleware` should set search_path correctly
- All queries should use tenant schema, not public
- Verify `get_current_tenant(request)` works correctly

### 4. Create OS Ticket Endpoint in `olient` Schema
Run: `python create_osticket_endpoint_olient.py`
- Creates endpoint in `olient` schema
- Points to: `https://polysaas.supportsystem.com/scp/`

### 5. Migrate All Data
- Move all tenant-specific data from `public` to `olient`
- Ensure each tenant has their own isolated data
- Update middleware/routing to use correct schema

### 6. Test Multi-Tenant Isolation
- Verify data in `olient` doesn't show up for other tenants
- Verify cookies are saved to correct schema
- Verify passthrough uses correct schema
- Verify MonitorLogger entries are in correct schema

## Files Modified (for schema fix)
- `dose/polysniffer/views.py` - Added tenant schema switching (commented out for demo)
- `create_osticket_endpoint_olient.py` - Script to create endpoint in olient

## Why Data Appears/Disappears - The Schema Issue

**The Problem You Experienced:**
- You see data in admin interface (because you're looking at `public` schema)
- Copilot says data isn't there (because it's querying `olient` schema or vice versa)
- This is why there was confusion about what data exists

**Root Cause:**
- All data is in `public` schema (PassThroughEndpoint, MonitorLogger, etc.)
- But the system is supposed to use tenant schemas (`olient`, etc.)
- When queries run in different schemas, data appears/disappears
- This is why you and Copilot saw different things!

## Root Cause - CRITICAL BUG FOUND

**The Problem:**
- `SessionTenantMiddleware` sets `search_path` using `connection.cursor()` in a `with` block
- `SET search_path` in a cursor context **only affects that cursor**, not Django ORM queries
- Django ORM uses a **different connection/cursor** from the connection pool
- So ORM queries still use `public` schema even though middleware "set" the search_path

**The Fix:**
Need to set `search_path` directly on the connection, not in a cursor context. Options:
1. Use `connection.cursor().execute()` without `with` block (but this is bad practice)
2. Use a database router to route queries to correct schema
3. Use `connection.set_schema()` if available (django-tenants pattern)
4. Set search_path at connection initialization time
5. Use `@transaction.atomic()` with schema switching inside

**Current Code (BROKEN):**
```python
with connection.cursor() as cursor:
    cursor.execute(f"SET search_path TO {schema_name},public;")
```

**Needs to be:**
```python
# Set on connection directly, not cursor
connection.cursor().execute(f"SET search_path TO {schema_name},public;")
# OR use a connection wrapper/router
```

## Current Status
✅ Works for demo (using public schema endpoint ID 2)
⏳ Schema fix deferred until after meeting

