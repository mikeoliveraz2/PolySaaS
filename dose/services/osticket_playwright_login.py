"""
OSTicket Playwright-based login service
Bypasses 422 errors by using a real browser to handle CSRF, cookies, and hidden fields automatically.
"""
import asyncio
import logging
from typing import Dict, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. Install with: pip install playwright && playwright install chromium")


async def osticket_login_with_playwright(
    login_url: str,
    username: str,
    password: str,
    cookies: Optional[Dict] = None
) -> Dict:
    """
    Login to OSTicket using Playwright (real browser automation).
    This bypasses 422 errors by handling CSRF tokens, cookies, and hidden fields automatically.

    Args:
        login_url: Full URL to OSTicket login page (e.g., https://domain.com/scp/login.php)
        username: OSTicket username
        password: OSTicket password
        cookies: Optional dict of cookies to set before login

    Returns:
        Dict with:
            - success: bool
            - cookies: list of cookie dicts (can be saved to session)
            - redirect_url: str (where OSTicket redirected after login)
            - error: str (if failed)
    """
    if not PLAYWRIGHT_AVAILABLE:
        return {
            'success': False,
            'error': 'Playwright not installed. Run: pip install playwright && playwright install chromium'
        }

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()

            # Set cookies if provided
            if cookies:
                await context.add_cookies([
                    {
                        'name': k,
                        'value': v,
                        'url': login_url.split('/scp/')[0] + '/scp/'
                    }
                    for k, v in cookies.items()
                ])

            page = await context.new_page()

            # Navigate to login page
            logger.info(f"[OSTICKET PLAYWRIGHT] Navigating to: {login_url}")
            await page.goto(login_url, wait_until='networkidle')

            # Fill in credentials
            logger.info(f"[OSTICKET PLAYWRIGHT] Filling credentials for user: {username}")
            await page.fill('input[name="userid"]', username)
            await page.fill('input[name="passwd"]', password)

            # Submit form - Playwright handles CSRF token, hidden fields, cookies automatically
            logger.info(f"[OSTICKET PLAYWRIGHT] Submitting login form")
            await page.click('button[type="submit"], input[type="submit"]')

            # Wait for navigation/redirect
            try:
                await page.wait_for_load_state('networkidle', timeout=10000)
            except:
                # If timeout, check if we're on a different page
                pass

            # Get final URL (redirect destination)
            final_url = page.url
            logger.info(f"[OSTICKET PLAYWRIGHT] Final URL after login: {final_url}")

            # Extract all cookies from the browser context
            browser_cookies = await context.cookies()
            logger.info(f"[OSTICKET PLAYWRIGHT] Captured {len(browser_cookies)} cookies")

            # Check if login was successful (redirected away from login page)
            success = 'login.php' not in final_url.lower()

            await browser.close()

            return {
                'success': success,
                'cookies': browser_cookies,
                'redirect_url': final_url,
                'error': None if success else 'Login failed - still on login page'
            }

    except Exception as e:
        logger.error(f"[OSTICKET PLAYWRIGHT] Error during login: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def osticket_login_sync(login_url: str, username: str, password: str, cookies: Optional[Dict] = None) -> Dict:
    """
    Synchronous wrapper for osticket_login_with_playwright.
    Use this from Django views (which are synchronous).
    """
    if not PLAYWRIGHT_AVAILABLE:
        return {
            'success': False,
            'error': 'Playwright not installed'
        }

    # Run async function in event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        osticket_login_with_playwright(login_url, username, password, cookies)
    )

