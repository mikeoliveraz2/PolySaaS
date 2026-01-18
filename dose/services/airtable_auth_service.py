"""
Airtable Authentication Service
Uses headless browser to authenticate and capture session cookies
"""
import logging
import time
from django.conf import settings
from allauth.socialaccount.models import SocialToken, SocialAccount

logger = logging.getLogger(__name__)


class AirtableAuthService:
    """
    Service to authenticate with Airtable using headless browser
    and capture session cookies for proxy use
    """

    def __init__(self):
        self.browser = None
        self.cookies = None

    def authenticate_with_headless_browser(self, user):
        """
        Authenticate with Airtable using headless browser and Google OAuth

        Args:
            user: Django User object

        Returns:
            dict: Session cookies if successful, None otherwise
        """
        try:
            # Try Playwright first (more modern, faster)
            try:
                return self._authenticate_with_playwright(user)
            except ImportError:
                logger.info("[AIRTABLE AUTH] Playwright not available, trying Selenium...")
                return self._authenticate_with_selenium(user)
        except Exception as e:
            logger.error(f"[AIRTABLE AUTH] Error in headless browser authentication: {e}")
            import traceback
            logger.debug(f"[AIRTABLE AUTH] Traceback: {traceback.format_exc()}")
            return None

    def _authenticate_with_playwright(self, user):
        """Authenticate using Playwright (preferred)"""
        from playwright.sync_api import sync_playwright

        logger.info(f"[AIRTABLE AUTH] Starting Playwright authentication for user {user.username}")

        with sync_playwright() as p:
            # Launch headless browser
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()

            try:
                # Step 1: Navigate to Airtable
                logger.info("[AIRTABLE AUTH] Navigating to Airtable...")
                page.goto('https://airtable.com/', wait_until='networkidle', timeout=30000)

                # Step 2: Look for "Sign in with Google" button
                logger.info("[AIRTABLE AUTH] Looking for Google sign-in button...")

                # Wait for and click "Sign in with Google"
                try:
                    # Try multiple selectors for the Google sign-in button
                    selectors = [
                        'button:has-text("Sign in with Google")',
                        'a:has-text("Sign in with Google")',
                        '[data-testid*="google"]',
                        'button[aria-label*="Google"]',
                        'a[href*="google"]',
                        'button:has-text("Continue with Google")',
                    ]

                    button_found = False
                    for selector in selectors:
                        try:
                            page.wait_for_selector(selector, timeout=5000)
                            page.click(selector)
                            button_found = True
                            logger.info(f"[AIRTABLE AUTH] Clicked Google sign-in button: {selector}")
                            break
                        except:
                            continue

                    if not button_found:
                        # Try to find any sign-in link
                        sign_in_links = page.query_selector_all('a[href*="login"], a[href*="sign"], button:has-text("Sign")')
                        if sign_in_links:
                            sign_in_links[0].click()
                            logger.info("[AIRTABLE AUTH] Clicked generic sign-in link")
                            time.sleep(2)
                            # Now look for Google button on login page
                            for selector in selectors:
                                try:
                                    page.wait_for_selector(selector, timeout=5000)
                                    page.click(selector)
                                    button_found = True
                                    logger.info(f"[AIRTABLE AUTH] Clicked Google sign-in button on login page: {selector}")
                                    break
                                except:
                                    continue

                except Exception as e:
                    logger.warning(f"[AIRTABLE AUTH] Could not find/click Google sign-in button: {e}")
                    # Maybe already on Google OAuth page?

                # Step 3: Wait for Google OAuth page and handle it
                logger.info("[AIRTABLE AUTH] Waiting for Google OAuth...")
                time.sleep(3)

                # Check if we're on Google OAuth page
                current_url = page.url
                if 'accounts.google.com' in current_url:
                    logger.info("[AIRTABLE AUTH] On Google OAuth page")

                    # Get Google account email
                    google_account = SocialAccount.objects.filter(
                        user=user,
                        provider='google'
                    ).first()

                    email = None
                    if google_account:
                        email = google_account.extra_data.get('email') or user.email

                    if email:
                        # Try to auto-fill email if possible
                        try:
                            email_input = page.wait_for_selector('input[type="email"]', timeout=5000)
                            email_input.fill(email)
                            logger.info(f"[AIRTABLE AUTH] Filled email: {email}")

                            # Click Next button
                            next_button = page.wait_for_selector('button:has-text("Next"), button[id="identifierNext"]', timeout=5000)
                            next_button.click()
                            logger.info("[AIRTABLE AUTH] Clicked Next on email page")
                            time.sleep(2)
                        except Exception as e:
                            logger.warning(f"[AIRTABLE AUTH] Could not auto-fill email: {e}")

                    # At this point, user would need to manually authenticate
                    # OR we could use the OAuth token to make an API call
                    # For now, we'll wait and see if we get redirected back
                    logger.info("[AIRTABLE AUTH] Waiting for OAuth completion (may require manual intervention)...")
                    page.wait_for_url('**/airtable.com/**', timeout=60000)

                # Step 4: Check if we're authenticated
                final_url = page.url
                logger.info(f"[AIRTABLE AUTH] Final URL: {final_url}")

                if 'login' in final_url.lower() or 'sign' in final_url.lower():
                    logger.warning("[AIRTABLE AUTH] Still on login page - authentication may have failed")
                    return None

                # Step 5: Get cookies
                cookies = context.cookies()
                logger.info(f"[AIRTABLE AUTH] Captured {len(cookies)} cookies")

                # Convert to dict format
                cookie_dict = {}
                for cookie in cookies:
                    cookie_dict[cookie['name']] = cookie['value']
                    logger.debug(f"[AIRTABLE AUTH] Cookie: {cookie['name']} (domain={cookie.get('domain')})")

                return cookie_dict

            finally:
                browser.close()

    def _authenticate_with_selenium(self, user):
        """Authenticate using Selenium (fallback)"""
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options

        logger.info(f"[AIRTABLE AUTH] Starting Selenium authentication for user {user.username}")

        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        driver = webdriver.Chrome(options=chrome_options)

        try:
            # Navigate to Airtable
            logger.info("[AIRTABLE AUTH] Navigating to Airtable...")
            driver.get('https://airtable.com/')

            # Look for Google sign-in button
            logger.info("[AIRTABLE AUTH] Looking for Google sign-in button...")
            try:
                wait = WebDriverWait(driver, 10)
                google_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign in with Google')] | //a[contains(text(), 'Sign in with Google')]"))
                )
                google_button.click()
                logger.info("[AIRTABLE AUTH] Clicked Google sign-in button")
            except:
                logger.warning("[AIRTABLE AUTH] Could not find Google sign-in button")

            # Wait for redirect
            time.sleep(5)

            # Get cookies
            cookies = driver.get_cookies()
            logger.info(f"[AIRTABLE AUTH] Captured {len(cookies)} cookies")

            # Convert to dict format
            cookie_dict = {}
            for cookie in cookies:
                cookie_dict[cookie['name']] = cookie['value']

            return cookie_dict

        finally:
            driver.quit()

    def get_authenticated_cookies(self, user, request_session):
        """
        Get authenticated Airtable cookies, using cached ones if available

        Args:
            user: Django User object
            request_session: Django session object

        Returns:
            dict: Cookies to use for Airtable requests
        """
        # Check if we have cached cookies in session
        cached_cookies = request_session.get('_airtable_authenticated_cookies')
        if cached_cookies:
            logger.info("[AIRTABLE AUTH] Using cached authenticated cookies")
            return cached_cookies

        # No cached cookies - authenticate with headless browser
        logger.info("[AIRTABLE AUTH] No cached cookies, authenticating with headless browser...")
        cookies = self.authenticate_with_headless_browser(user)

        if cookies:
            # Cache in session
            request_session['_airtable_authenticated_cookies'] = cookies
            request_session.save()
            logger.info("[AIRTABLE AUTH] Saved authenticated cookies to session")
            return cookies

        return None

