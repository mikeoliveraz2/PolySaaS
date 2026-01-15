# D.O.S.E. Database State Check - Summary

**Date:** August 11, 2025

---

## Purpose
This script (`check_db.py`) is used to inspect the current state of the PostgreSQL database for the D.O.S.E. platform. It checks for:
- All tables in the `public` schema
- Foreign key constraints on the `django_admin_log` table
- Existence of the `dose_tenantuser` table
- Existence of the `auth_user` table

---

## What the Script Does
1. **Lists all tables** in the `public` schema (should include all Django and D.O.S.E. app tables)
2. **Checks foreign key constraints** on the `django_admin_log` table (verifies admin log integrity)
3. **Verifies existence of `dose_tenantuser` table** (checks for legacy or custom user-tenant mapping)
4. **Verifies existence of `auth_user` table** (checks for Django's default user table)

---

## Usage
Run the script from your project root:
```sh
python check_db.py
```

---

## Example Output
```
Current database tables:
  auth_user
  dose_tenant
  dose_userprofile
  django_admin_log
  ...

Checking for django_admin_log constraints:
  Constraint: ... -> ...

Checking if dose_tenantuser table exists:
  dose_tenantuser exists: False

Checking if auth_user table exists:
  auth_user exists: True
```

---

## Why This Is Useful
- **Debugs migration issues** (e.g., missing or extra tables)
- **Verifies schema after migrations**
- **Checks for legacy/obsolete tables**
- **Ensures admin log integrity**

---

## Next Steps
- If you see missing tables, check your migrations and run `python manage.py migrate`.
- If you see unexpected tables (like `dose_tenantuser`), consider cleaning up legacy schema.
- Use this script after major migrations or schema changes to verify database health.

---

*Script: `check_db.py` - D.O.S.E. Platform Database Inspector*
