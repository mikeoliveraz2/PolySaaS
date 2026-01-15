# Multi-Tenant Google Social Login UID Verification Summary

**Date:** 2025-09-28

## Overview
- Verified that Google social login UIDs are unique per Google account and enforced by Allauth.
- Confirmed that both tenants (olient and pilot) and both users (olientAdmin and pilotAdmin) exist, with user profiles present.
- Used Google OAuth Playground and a Python script to fetch and compare UIDs for:
  - mikeoliveraz@gmail.com (UID: 117986726904510989322)
  - xraycommon@gmail.com (UID: 118261961028963376601)
- Confirmed that these are truly separate Google accounts (different UIDs).
- Cleaned up the `socialaccount_socialaccount` table to remove any old or conflicting records.
- Successfully linked each Google account to the correct user in the correct tenant, with no UID conflicts.

## Steps Taken
1. Used OAuth Playground to obtain access tokens and fetch UIDs for both Google accounts.
2. Verified that both UIDs are unique and not aliases.
3. Emptied the `socialaccount_socialaccount` table to ensure a clean state.
4. Logged in as each user and connected the correct Google account.
5. Confirmed in Django admin that each user is linked to the correct Google UID.

## Result
- Both users can now log in with their respective Google accounts.
- Allauth enforces one-to-one mapping between Google UID and user.
- Multi-tenant social login is working as intended.

---

**Commit message suggestion:**
Enable unique Google social login for multi-tenant users; verified UID mapping and cleaned up socialaccount records.
