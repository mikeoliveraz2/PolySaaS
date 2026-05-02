---
description: Fix blank Django admin user edit page and DoesNotExist errors
---

# BINGO: Blank Admin User Edit Page Fix

**Date:** May 1, 2026  
**Status:** ✅ COMPLETE  
**Branch:** main

## Summary

Fixed the blank Django admin user edit page on production (Render). The issue was caused by a multi-tenancy schema mismatch where:
1. `User` objects were stored in `public` schema (correct)
2. `UserProfile` objects were stored in tenant schemas (incorrect)
3. When the inline form tried to render UserProfiles, it couldn't find the related User in the tenant schema context

## Root Causes Identified

1. **Template inheritance issue** - `base_site.html` was using wrong block name (`page_content` vs `content`)
2. **Schema mismatch** - `UserProfile` objects in tenant schemas trying to reference `User` in `public` schema
3. **DoesNotExist on get_object** - `CustomUserAdmin` wasn't forcing `public` schema before queries
4. **UserProfile.__str__ crash** - accessing `self.user.username` when user not in current schema

## Files Changed

- `dose/templates/admin/base_site.html` - Fixed block inheritance from Jazzmin
- `dose/admin.py` - Added `get_queryset`, `get_object`, `change_view` overrides to force `public` schema for User queries; added `get_queryset` to `UserProfileInline` to handle cross-schema references
- `dose/models/user_profile.py` - Fixed `__str__` to handle missing user gracefully
- `dose/tenant_utils.py` - Added logging for tenant debugging
- `dose/management/commands/migrate_users_to_public.py` - Created for migrating users from tenant schemas to public
- `dose/management/commands/check_template_loading.py` - Created for template diagnostics

## Solution

The fix involved:
1. Forcing `search_path TO public` in `CustomUserAdmin.get_object()` before querying users
2. Adding `get_queryset` to `UserProfileInline` to query from `public` schema and filter out inaccessible profiles
3. Making `UserProfile.__str__` handle `User.DoesNotExist` gracefully

## Verification

- User list page loads correctly
- User edit form now displays with all fields (username, email, password, etc.)
- Can save changes to users
- No more `DoesNotExist` errors

## Follow-ups

- Consider moving `UserProfile` table entirely to `public` schema for consistency
- Ensure future user creation always happens in `public` schema
- Add tests to prevent regression of this multi-tenancy issue
