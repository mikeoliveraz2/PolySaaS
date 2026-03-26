"""Fix Sign Up page dark mode styling - heading, description, form fields, labels."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/1399",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

# Find last </style> to inject dark mode form CSS
dark_form_css = """
/* Dark mode: Sign Up form fixes */
body.dark-mode .wpforms-container,
body.dark-mode .wpforms-form {
    color: #F1F5F9 !important;
}
body.dark-mode .wpforms-form label,
body.dark-mode .wpforms-form .wpforms-field-label,
body.dark-mode .wpforms-form .wpforms-field-sublabel {
    color: #F1F5F9 !important;
}
body.dark-mode .wpforms-form input[type="text"],
body.dark-mode .wpforms-form input[type="email"],
body.dark-mode .wpforms-form input[type="tel"],
body.dark-mode .wpforms-form input[type="url"],
body.dark-mode .wpforms-form input[type="number"],
body.dark-mode .wpforms-form input[type="password"],
body.dark-mode .wpforms-form textarea,
body.dark-mode .wpforms-form select {
    background-color: #1E293B !important;
    color: #F1F5F9 !important;
    border-color: #334155 !important;
}
body.dark-mode .wpforms-form input::placeholder,
body.dark-mode .wpforms-form textarea::placeholder {
    color: #94A3B8 !important;
}
body.dark-mode .wpforms-form .wpforms-required-label {
    color: #F87171 !important;
}
body.dark-mode .wpforms-form button[type="submit"],
body.dark-mode .wpforms-form .wpforms-submit {
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    border: none !important;
}
"""

# Also fix the page heading and description text
# Find the heading - "Schedule/Sign Up for a Demo" type text
heading_pos = content.find('Schedule')
if heading_pos < 0:
    heading_pos = content.find('Sign Up')
if heading_pos > 0:
    start = max(0, heading_pos - 300)
    end = min(len(content), heading_pos + 500)
    print(f"Heading context:\n{content[start:end]}\n")

last_style = content.rfind('</style>')
if last_style > 0:
    content = content[:last_style] + dark_form_css + content[last_style:]
    print("Injected dark mode form CSS")
else:
    print("No </style> found!")
    sys.exit(1)

# Fix the page heading color - make it work in both modes
# The heading is likely using a color that's invisible in dark mode
# Search for the h2/h1 heading on the page
h_pat = r'<h[12][^>]*>.*?(?:Schedule|Sign Up|Demo).*?</h[12]>'
h_match = re.search(h_pat, content, re.DOTALL | re.IGNORECASE)
if h_match:
    old_h = h_match.group(0)
    print(f"Found heading: {old_h[:200]}")
    # If it has a hardcoded color, change to use CSS var
    if 'color:' in old_h:
        new_h = re.sub(r'color:[^;"]*', 'color:var(--ps-primary,#2563EB)', old_h)
        content = content.replace(old_h, new_h)
        print("Fixed heading color")

# Fix description paragraph
desc_pat = r'<p[^>]*>.*?(?:full PolySaaS|form below|personalized demo).*?</p>'
desc_match = re.search(desc_pat, content, re.DOTALL | re.IGNORECASE)
if desc_match:
    old_desc = desc_match.group(0)
    print(f"Found description: {old_desc[:200]}")
    if 'color:' in old_desc:
        new_desc = re.sub(r'color:[^;"]*', 'color:var(--ps-text-muted,#6B7280)', old_desc)
        content = content.replace(old_desc, new_desc)
        print("Fixed description color")

r2 = requests.post(BASE + "/wp-json/wp/v2/pages/1399",
                   auth=AUTH,
                   json={"content": content},
                   timeout=45)
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("SUCCESS - Sign Up page dark mode fixed")
else:
    print(f"Error: {r2.text[:300]}")
