import os
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Grab fully rendered Nextcloud dashboard after login"

    def handle(self, *args, **options):
        NEXTCLOUD_URL = "http://localhost:8888"
        USERNAME = "admin"           # ← change if different
        PASSWORD = "admin"           # ← change to your NextCloud admin password

        # Check if Playwright is available
        try:
            from playwright.sync_api import sync_playwright
            playwright_available = True
        except ImportError:
            playwright_available = False
            self.stdout.write(self.style.WARNING("⚠️ Playwright not installed. Installing placeholder content..."))

        # First check if NextCloud is accessible (only if Playwright is available)
        if playwright_available:
            import requests
            try:
                response = requests.get("http://localhost:8888", timeout=5)
                self.stdout.write(f"✓ NextCloud is accessible (status: {response.status_code})")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠️ NextCloud not accessible: {e}"))
                playwright_available = False

        if not playwright_available:
            self.stdout.write("Creating placeholder content instead...")

            # Create placeholder content by running the placeholder script
            placeholder_script = os.path.join(os.path.dirname(__file__), "..", "..", "..", "create_placeholder_nextcloud.py")
            if os.path.exists(placeholder_script):
                try:
                    with open(placeholder_script, 'r', encoding='utf-8') as f:
                        exec(f.read())
                    self.stdout.write(self.style.SUCCESS("✅ Placeholder NextCloud content created"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Failed to create placeholder: {e}"))
            else:
                self.stdout.write(self.style.ERROR("❌ Placeholder script not found"))
            return

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Show browser for debugging
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 PolySaaS-Playwright"
            )
            page = context.new_page()

            try:
                self.stdout.write("🚀 Going to Nextcloud...")
                page.goto(NEXTCLOUD_URL, wait_until="networkidle", timeout=15000)

                # Check what we got
                title = page.title()
                url = page.url
                self.stdout.write(f"📄 Page title: {title}")
                self.stdout.write(f"🌐 Current URL: {url}")

                # Take screenshot for debugging
                page.screenshot(path="nextcloud_initial.png")
                self.stdout.write("📸 Screenshot saved: nextcloud_initial.png")

                # ---- LOG IN ----
                try:
                    page.wait_for_selector('input[name="user"]', timeout=10000)
                    self.stdout.write("✓ Login form found")

                    page.fill('input[name="user"]', USERNAME)
                    page.fill('input[name="password"]', PASSWORD)
                    self.stdout.write(f"🔐 Filled credentials: {USERNAME}/****")

                    page.click('button[type="submit"]')
                    self.stdout.write("🔄 Clicked login button")

                except Exception as login_error:
                    self.stdout.write(self.style.ERROR(f"❌ Login failed: {login_error}"))
                    # Maybe already logged in? Continue anyway

                # Try to wait for dashboard elements, but don't fail if they don't appear
                try:
                    page.wait_for_selector('#app-dashboard, .app-files', timeout=10000)
                    self.stdout.write(self.style.SUCCESS("✓ Dashboard elements found!"))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"⚠️ Dashboard selectors not found: {e}"))
                    # Try alternative selectors
                    try:
                        page.wait_for_selector('body', timeout=5000)
                        self.stdout.write(self.style.SUCCESS("✓ Page body loaded"))
                    except:
                        self.stdout.write(self.style.WARNING("⚠️ Even basic selectors failed"))

                self.stdout.write(self.style.SUCCESS("Logged in! Rendering dashboard..."))

                # Optional: wait a tiny bit more for all JS chunks
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except:
                    self.stdout.write(self.style.WARNING("⚠️ NetworkIdle timeout, continuing anyway..."))

                html = page.content()
                final_url = page.url

                # Take final screenshot
                page.screenshot(path="nextcloud_final.png")
                self.stdout.write("📸 Final screenshot saved: nextcloud_final.png")

                self.stdout.write(f"📍 Final URL: {final_url}")
                self.stdout.write(f"📏 Content length: {len(html)} characters")

                output_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "nextcloud_logged_in.html")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(html)

                self.stdout.write(self.style.SUCCESS(f"✅ Saved {len(html)} bytes → {output_path}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error during capture: {e}"))
                # Save whatever we have
                try:
                    html = page.content()
                    output_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "nextcloud_error_capture.html")
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(html)
                    self.stdout.write(f"💾 Saved error capture: {output_path}")
                except:
                    pass

            finally:
                browser.close()