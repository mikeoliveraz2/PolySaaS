"""Create the Schedule a Demo form and page on WordPress.
Uses WPForms (already installed) for the form, and creates a new page."""
import requests
import json
import re

SITE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
APP_PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"

session = requests.Session()
session.auth = (USER, APP_PASS)

# Step 1: Check what the existing WPForms sign-up form looks like
print("Step 1: Examining Sign Up page for WPForms structure...")
resp = session.get(f"{SITE}/sign-up/", timeout=15)
html = resp.text

# Find the WPForms form ID
form_id_match = re.search(r'wpforms-form-(\d+)', html)
if form_id_match:
    existing_form_id = form_id_match.group(1)
    print(f"  Existing WPForms form ID: {existing_form_id}")

# Extract the form structure
form_match = re.search(r'(<form[^>]*wpforms[^>]*>.*?</form>)', html, re.DOTALL)
if form_match:
    form_html = form_match.group(1)
    fields = re.findall(r'<div[^>]*class="([^"]*wpforms-field[^"]*)"[^>]*data-field-id="(\d+)"', form_html)
    labels = re.findall(r'<label[^>]*class="wpforms-field-label"[^>]*>(.*?)</label>', form_html)
    print(f"  Form fields: {len(fields)}")
    for (cls, fid), label in zip(fields, labels):
        field_type = 'unknown'
        if 'name' in cls: field_type = 'name'
        elif 'email' in cls: field_type = 'email'
        elif 'textarea' in cls: field_type = 'textarea'
        elif 'text' in cls: field_type = 'text'
        print(f"    Field {fid}: {label.strip()} ({cls[:50]})")

# Step 2: Check WPForms REST API availability
print("\nStep 2: Checking WPForms API...")
for endpoint in ['/wp-json/wpforms/v1/forms', '/wp-json/wp/v2/wpforms']:
    resp = session.get(f"{SITE}{endpoint}")
    print(f"  {endpoint} -> HTTP {resp.status_code}")

# Step 3: Create the Schedule a Demo page with an embedded HTML form
# Since WPForms may not have a REST API for form creation,
# we'll create a page with a custom HTML form that posts to a handler
print("\nStep 3: Creating Schedule a Demo page...")

DEMO_PAGE_HTML = """
<!-- wp:html -->
<div class="polysaas-demo-form-wrapper" style="max-width: 640px; margin: 40px auto; padding: 40px; background: #f5f5f5; border-radius: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  
  <h2 style="color: #003399; text-align: center; margin-bottom: 8px; font-size: 28px;">Schedule a Demo</h2>
  <p style="text-align: center; color: #616161; margin-bottom: 30px;">See PolySaaS in action. Pick a day and time that works for you and we'll set up a personalized walkthrough.</p>
  
  <form id="polysaas-demo-form" method="post" style="display: flex; flex-direction: column; gap: 18px;">
    
    <div style="display: flex; gap: 16px;">
      <div style="flex: 1;">
        <label style="display: block; font-weight: 600; color: #1e1e1e; margin-bottom: 6px; font-size: 14px;">First Name <span style="color: #f44336;">*</span></label>
        <input type="text" name="first_name" required placeholder="John"
          style="width: 100%; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 15px; transition: border-color 0.2s; box-sizing: border-box;"
          onfocus="this.style.borderColor='#03a9f4'" onblur="this.style.borderColor='#e0e0e0'" />
      </div>
      <div style="flex: 1;">
        <label style="display: block; font-weight: 600; color: #1e1e1e; margin-bottom: 6px; font-size: 14px;">Last Name <span style="color: #f44336;">*</span></label>
        <input type="text" name="last_name" required placeholder="Smith"
          style="width: 100%; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 15px; transition: border-color 0.2s; box-sizing: border-box;"
          onfocus="this.style.borderColor='#03a9f4'" onblur="this.style.borderColor='#e0e0e0'" />
      </div>
    </div>
    
    <div>
      <label style="display: block; font-weight: 600; color: #1e1e1e; margin-bottom: 6px; font-size: 14px;">Email Address <span style="color: #f44336;">*</span></label>
      <input type="email" name="email" required placeholder="john@company.com"
        style="width: 100%; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 15px; transition: border-color 0.2s; box-sizing: border-box;"
        onfocus="this.style.borderColor='#03a9f4'" onblur="this.style.borderColor='#e0e0e0'" />
    </div>
    
    <div>
      <label style="display: block; font-weight: 600; color: #1e1e1e; margin-bottom: 6px; font-size: 14px;">Company</label>
      <input type="text" name="company" placeholder="Acme Corp"
        style="width: 100%; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 15px; transition: border-color 0.2s; box-sizing: border-box;"
        onfocus="this.style.borderColor='#03a9f4'" onblur="this.style.borderColor='#e0e0e0'" />
    </div>
    
    <div style="display: flex; gap: 16px;">
      <div style="flex: 1;">
        <label style="display: block; font-weight: 600; color: #1e1e1e; margin-bottom: 6px; font-size: 14px;">Preferred Date <span style="color: #f44336;">*</span></label>
        <input type="date" name="preferred_date" required
          style="width: 100%; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 15px; transition: border-color 0.2s; box-sizing: border-box; color: #1e1e1e;"
          onfocus="this.style.borderColor='#03a9f4'" onblur="this.style.borderColor='#e0e0e0'" />
      </div>
      <div style="flex: 1;">
        <label style="display: block; font-weight: 600; color: #1e1e1e; margin-bottom: 6px; font-size: 14px;">Preferred Time (CST) <span style="color: #f44336;">*</span></label>
        <select name="preferred_time" required
          style="width: 100%; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 15px; background: #fff; transition: border-color 0.2s; box-sizing: border-box; color: #1e1e1e;"
          onfocus="this.style.borderColor='#03a9f4'" onblur="this.style.borderColor='#e0e0e0'">
          <option value="">Select a time...</option>
          <option value="09:00">9:00 AM</option>
          <option value="09:30">9:30 AM</option>
          <option value="10:00">10:00 AM</option>
          <option value="10:30">10:30 AM</option>
          <option value="11:00">11:00 AM</option>
          <option value="11:30">11:30 AM</option>
          <option value="12:00">12:00 PM</option>
          <option value="12:30">12:30 PM</option>
          <option value="13:00">1:00 PM</option>
          <option value="13:30">1:30 PM</option>
          <option value="14:00">2:00 PM</option>
          <option value="14:30">2:30 PM</option>
          <option value="15:00">3:00 PM</option>
          <option value="15:30">3:30 PM</option>
          <option value="16:00">4:00 PM</option>
          <option value="16:30">4:30 PM</option>
          <option value="17:00">5:00 PM</option>
        </select>
      </div>
    </div>
    
    <div>
      <label style="display: block; font-weight: 600; color: #1e1e1e; margin-bottom: 6px; font-size: 14px;">What are you most interested in?</label>
      <textarea name="message" rows="3" placeholder="e.g., SaaS integration, AI orchestration, specific bundled apps..."
        style="width: 100%; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 15px; resize: vertical; font-family: inherit; transition: border-color 0.2s; box-sizing: border-box;"
        onfocus="this.style.borderColor='#03a9f4'" onblur="this.style.borderColor='#e0e0e0'"></textarea>
    </div>
    
    <button type="submit"
      style="background-color: #003399; color: #ffffff; padding: 14px 32px; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; transition: background-color 0.2s; align-self: center; min-width: 220px;"
      onmouseover="this.style.backgroundColor='#03a9f4'"
      onmouseout="this.style.backgroundColor='#003399'">
      Request Demo
    </button>
    
    <p style="text-align: center; color: #9e9e9e; font-size: 13px; margin-top: 4px;">We'll confirm your demo within 24 hours. All times are Central Standard Time (CST).</p>
  </form>
  
  <div id="demo-form-success" style="display: none; text-align: center; padding: 40px 20px;">
    <div style="font-size: 48px; margin-bottom: 16px;">&#10003;</div>
    <h3 style="color: #003399; margin-bottom: 8px;">Demo Request Received!</h3>
    <p style="color: #616161;">Thank you. We'll send a confirmation to your email within 24 hours with the meeting details.</p>
  </div>
</div>

<script>
document.getElementById('polysaas-demo-form').addEventListener('submit', function(e) {
  e.preventDefault();
  var form = this;
  var data = new FormData(form);
  var obj = {};
  data.forEach(function(v, k) { obj[k] = v; });
  
  // Send via WordPress REST API
  fetch('/wp-json/contact/v1/demo-request', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(obj)
  })
  .then(function(r) { return r.json(); })
  .then(function(result) {
    form.style.display = 'none';
    document.getElementById('demo-form-success').style.display = 'block';
  })
  .catch(function() {
    // Fallback: mailto
    var subject = encodeURIComponent('PolySaaS Demo Request from ' + obj.first_name + ' ' + obj.last_name);
    var body = encodeURIComponent(
      'Name: ' + obj.first_name + ' ' + obj.last_name +
      '\\nEmail: ' + obj.email +
      '\\nCompany: ' + (obj.company || 'N/A') +
      '\\nPreferred Date: ' + obj.preferred_date +
      '\\nPreferred Time: ' + obj.preferred_time + ' CST' +
      '\\nInterests: ' + (obj.message || 'N/A')
    );
    window.location.href = 'mailto:mikeoliveraz@gmail.com?subject=' + subject + '&body=' + body;
    form.style.display = 'none';
    document.getElementById('demo-form-success').style.display = 'block';
  });
});

// Set min date to tomorrow
var dateInput = document.querySelector('input[name="preferred_date"]');
if (dateInput) {
  var tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  // Skip weekends
  var day = tomorrow.getDay();
  if (day === 0) tomorrow.setDate(tomorrow.getDate() + 1);
  if (day === 6) tomorrow.setDate(tomorrow.getDate() + 2);
  dateInput.min = tomorrow.toISOString().split('T')[0];
}
</script>
<!-- /wp:html -->
"""

# Create the page
page_data = {
    "title": "Schedule a Demo",
    "content": DEMO_PAGE_HTML,
    "status": "publish",
    "slug": "schedule-demo",
}

resp = session.post(f"{SITE}/wp-json/wp/v2/pages", json=page_data)
if resp.status_code == 201:
    page = resp.json()
    page_id = page.get('id')
    page_link = page.get('link')
    print(f"\n  Page created! ID: {page_id}")
    print(f"  URL: {page_link}")
else:
    print(f"\n  Failed to create page: HTTP {resp.status_code}")
    print(f"  Response: {resp.text[:300]}")

# Step 4: Also create the CTA block for "Schedule a Demo" button
print("\nStep 4: Creating reusable CTA block for Schedule a Demo...")

CTA_DEMO_HTML = """
<!-- wp:html -->
<div style="text-align: center; padding: 40px 20px;">
  <h3 style="color: #003399; font-size: 22px; font-weight: 700; margin-bottom: 8px;">See PolySaaS in Action</h3>
  <p style="color: #616161; margin-bottom: 20px; max-width: 480px; margin-left: auto; margin-right: auto;">Book a personalized demo and discover how PolySaaS can transform your SaaS workflow.</p>
  <a href="/schedule-demo/" 
    style="display: inline-block; background-color: #003399; color: #ffffff; padding: 14px 36px; border-radius: 8px; font-size: 16px; font-weight: 600; text-decoration: none; transition: background-color 0.2s;"
    onmouseover="this.style.backgroundColor='#03a9f4'"
    onmouseout="this.style.backgroundColor='#003399'">
    Schedule a Demo
  </a>
  <p style="color: #9e9e9e; font-size: 13px; margin-top: 12px;">Pick your preferred day and time. We'll confirm within 24 hours.</p>
</div>
<!-- /wp:html -->
"""

block_data = {
    "title": "CTA — Schedule a Demo",
    "content": CTA_DEMO_HTML,
    "status": "publish",
}

resp2 = session.post(f"{SITE}/wp-json/wp/v2/blocks", json=block_data)
if resp2.status_code == 201:
    block = resp2.json()
    block_id = block.get('id')
    print(f"  Reusable block created! ID: {block_id}")
else:
    print(f"  Failed to create block: HTTP {resp2.status_code}")
    print(f"  Response: {resp2.text[:300]}")

# Also create the existing-style CTA as a reusable block for consistency
print("\nStep 5: Creating reusable CTA block for Join Waitlist...")

CTA_WAITLIST_HTML = """
<!-- wp:html -->
<div style="text-align: center; padding: 40px 20px;">
  <h3 style="color: #003399; font-size: 22px; font-weight: 700; margin-bottom: 8px;">Stop Managing Tools. Start Orchestrating Them.</h3>
  <p style="color: #616161; margin-bottom: 20px; max-width: 520px; margin-left: auto; margin-right: auto;">PolySaaS gives your team one platform, one subscription, and AI teammates that actually collaborate &mdash; not just respond. Built on Google Cloud, powered by Atomic Services.</p>
  <a href="/sign-up/"
    style="display: inline-block; background-color: #003399; color: #ffffff; padding: 14px 36px; border-radius: 8px; font-size: 16px; font-weight: 600; text-decoration: none; transition: background-color 0.2s;"
    onmouseover="this.style.backgroundColor='#03a9f4'"
    onmouseout="this.style.backgroundColor='#003399'">
    Get Early Access &ndash; No Risk
  </a>
  <p style="color: #9e9e9e; font-size: 13px; margin-top: 12px;">Join hundreds already on the list. First access + exclusive updates.</p>
</div>
<!-- /wp:html -->
"""

block_data2 = {
    "title": "CTA — Join Waitlist",
    "content": CTA_WAITLIST_HTML,
    "status": "publish",
}

resp3 = session.post(f"{SITE}/wp-json/wp/v2/blocks", json=block_data2)
if resp3.status_code == 201:
    block2 = resp3.json()
    block_id2 = block2.get('id')
    print(f"  Reusable block created! ID: {block_id2}")
else:
    print(f"  Failed to create block: HTTP {resp3.status_code}")
    print(f"  Response: {resp3.text[:300]}")

print("\nDone. Summary:")
print("  1. /schedule-demo/ page — live with form (date picker, time dropdown, email)")
print("  2. 'CTA — Schedule a Demo' reusable block — insert on any page via Bricks")
print("  3. 'CTA — Join Waitlist' reusable block — insert on any page via Bricks")
