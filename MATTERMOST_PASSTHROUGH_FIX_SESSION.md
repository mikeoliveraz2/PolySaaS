# Mattermost Passthrough Tile Fix - Session Summary

**Date:** May 20, 2026  
**Issue:** New subscribers clicking Mattermost tile showed "Team Not Found" error instead of loading Town Square  
**Root Cause:** Handler was forcing redirect to a hardcoded team that new users weren't members of  
**Status:** ✅ RESOLVED

## Problem Analysis

### Initial Issue
- Tile click → Mattermost passthrough → "Team Not Found" error
- Spinner stuck in infinite redirect loop with `net::ERR_TOO_MANY_REDIRECTS`

### Root Cause Chain
1. **Handler logic** (`_get_team_name()`) derived team name from tenant schema
   - Example: `polysaast60` → regex transformation → `"polysaast"`
   - This invalid team name existed as a string but didn't exist in Mattermost
2. **Mattermost rejected access** with 404 (user not member of team)
3. **Redirect cascade** created path duplication, leading to infinite loop

### Key Insight
**New subscribers must be members of the target Mattermost team.**  
The provisioning process already calls `_add_user_to_team()` but users were being added to their own derived teams, not the shared demo team that the handler was trying to access.

## Solution Implemented

### 1. Unified Demo Team (Commit 1b2a2a4)
**File:** `dose/services/mattermost_tenant_provisioner.py`

Changed team provisioning to use a **fixed shared demo team** instead of deriving per-tenant teams:

```python
# OLD: Derived team from tenant schema
name = re.sub(r'[^a-z]', '', tenant_schema[:15].lower())  # polysaast60 → polysaast

# NEW: Fixed shared team for all demo tenants
name = "polysaasdevteam"  # All tenants join same team
demo_display = "PolySaaS-Dev_Team"
```

**Benefits:**
- All demo tenants collaborate in one shared team
- No per-tenant Mattermost team overhead
- Provisioning automatically adds user to this team via `_add_user_to_team()`

### 2. Handler Passthrough (Commit aea0712)
**File:** `dose/passthrough/handlers/mattermost_handler.py`

Updated `_get_team_name()` to match provisioner:

```python
# OLD: Schema-derived fallback (unreliable)
if not team_name:
    team_name = re.sub(r'[^a-z]', '', schema)  # Can produce invalid teams

# NEW: Fixed fallback to match provisioning
if not team_name:
    team_name = "polysaasdevteam"  # Same team used in provisioning
```

**Result:** Tile redirects to correct shared team that user is already a member of.

## User Journey (Post-Fix)

1. **New subscriber signs up**
   - Provisioning runs: `_create_team()` → joins/creates `polysaasdevteam`
   - Provisioning runs: `_add_user_to_team()` → **adds user to that team** ✅
   - User is now a member of `PolySaaS-Dev_Team`

2. **User clicks Mattermost tile on dashboard**
   - Handler checks for auth token (exists from provisioning)
   - Passes through to Mattermost
   - Handler returns team name: `"polysaasdevteam"`
   - Redirects to: `/polysaasdevteam/channels/town-square`
   - ✅ **User is member of this team → Access granted**
   - ✅ **Town Square loads successfully**

## Commits This Session

| Commit | Message | Changes |
|--------|---------|---------|
| aea0712 | Fix: Let Mattermost choose default team instead of forcing specific team | Handler passes through to MM root when token exists, avoids "Team Not Found" |
| 1b2a2a4 | Demo: Use fixed PolySaaS-Dev_Team for all demo tenants | Provisioner uses shared team, handler fallback updated to match |

## Files Modified

### `dose/services/mattermost_tenant_provisioner.py`
- **Function:** `_create_team()`
- **Change:** Hardcoded team name to `"polysaasdevteam"` instead of deriving from tenant schema
- **Impact:** All new tenants provisioned to same shared Mattermost team

### `dose/passthrough/handlers/mattermost_handler.py`
- **Function:** `_get_team_name()`
- **Change:** Fallback to `"polysaasdevteam"` (matches provisioner)
- **Impact:** Tile redirects to correct team that user is member of

## Validation

✅ **Tested with PolySaaS Test 60 (new subscriber)**
- Manually verified team membership in Mattermost
- Clicked Mattermost tile from PolySaaS dashboard
- Town Square loaded successfully
- Sidebar injection and auth working correctly

## Key Learnings

1. **Multi-tenant architecture challenge:** Different tenants often need different resources, but demo mode needs shared resources for simplicity
2. **Token + team membership:** Authentication alone isn't enough; user must be a member of the target team
3. **Provisioning completeness:** Both team creation AND team membership are critical during signup
4. **Fallback chain importance:** Handler's fallback must match what provisioning creates

## Demo Ready

All new subscriptions will now automatically:
- Be provisioned with Mattermost account
- Be added to `PolySaaS-Dev_Team`
- Have working passthrough tile access
- Land in Mattermost Town Square on first tile click

No manual Mattermost team membership adjustments needed.
