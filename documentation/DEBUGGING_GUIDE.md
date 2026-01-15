# Passthrough Debugging Guide

## The Problem

When passthrough integrations fail with "access denied" or similar errors, we need to know:
- What is the real browser sending?
- What is our proxy sending?
- What's different?

## The Solution: Three-Layer Testing

### Layer 1: TDD Tests (Isolated Logic)

**File:** `test_osticket_rewriting.py`

Tests the rewriting logic in isolation:
- CSRF token preservation
- Form action rewriting
- Link rewriting
- No double rewriting

**Run:** `python test_osticket_rewriting.py`

**When to use:** After changing rewriting logic, before deploying.

### Layer 2: Full Cycle Test (Session Persistence)

**File:** `test_osticket_full_cycle.py`

Tests the complete GET → POST cycle with persistent session:
- GET login page
- Extract CSRF token
- POST login credentials
- Verify success/redirect

**Run:** `python test_osticket_full_cycle.py`

**When to use:** To verify session cookies are maintained between GET and POST.

### Layer 3: PolySniffer (Real Browser Capture)

**Tool:** PolySniffer MITM Logger

Captures what a REAL browser does:
- All request headers
- All cookies
- All POST data
- All responses
- WebSocket connections

**When to use:** When TDD tests pass but real browser still fails.

## Debugging Workflow

### Step 1: Run TDD Tests

```bash
python test_osticket_rewriting.py
```

**Expected:** All tests pass (rewriting logic is correct)

### Step 2: Run Full Cycle Test

```bash
python test_osticket_full_cycle.py
```

**Expected:** Login succeeds (session persistence works)

### Step 3: If Still Failing, Use PolySniffer

1. Open PolySniffer: https://polysniffer.up.railway.app
2. Enter OSTicket URL
3. Paste cookies
4. Complete login flow
5. Export HAR file
6. Compare with our proxy output

**Look for:**
- Missing headers
- Different cookie values
- Different POST data format
- Different request timing

### Step 4: Fix and Re-test

1. Update proxy code to match real browser
2. Re-run tests
3. Verify in real browser

## Common Issues and Solutions

### Issue: "Access Denied"

**Possible Causes:**
1. CSRF token mismatch
2. Session cookie mismatch
3. Missing headers
4. Wrong POST data format

**Debug:**
1. Run `test_osticket_full_cycle.py` - check CSRF token and session cookie
2. Use PolySniffer - compare headers and POST data
3. Check if `OSTSESSID` from GET matches POST

### Issue: Form Action Wrong

**Possible Causes:**
1. Rewriting logic bug
2. Post-processing not catching it

**Debug:**
1. Run `test_osticket_rewriting.py` - should catch this
2. Check terminal logs for `[REWRITE_URLS]` messages

### Issue: Cookies Not Persisting

**Possible Causes:**
1. Session not being saved to browser
2. Cookie domain/path mismatch
3. Cookie being overwritten

**Debug:**
1. Check browser DevTools → Application → Cookies
2. Compare with `test_osticket_full_cycle.py` output
3. Verify Set-Cookie headers are being copied

## Quick Reference

| Test | Command | What It Tests |
|------|---------|---------------|
| TDD Tests | `python test_osticket_rewriting.py` | Rewriting logic |
| Full Cycle | `python test_osticket_full_cycle.py` | Session persistence |
| Real Browser | PolySniffer | Actual browser behavior |

## Files

- `test_osticket_rewriting.py` - TDD tests for rewriting
- `test_osticket_full_cycle.py` - Full GET → POST cycle test
- `documentation/POLYSNIFFER_SETUP.md` - PolySniffer setup guide
- `documentation/DEBUGGING_GUIDE.md` - This file

## Next Steps

After demo video:
1. Set up PolySniffer
2. Capture OSTicket login flow
3. Compare with our proxy
4. Fix differences
5. Verify login works

