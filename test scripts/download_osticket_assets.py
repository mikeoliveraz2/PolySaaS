import requests
import os

# Base URL for OSTicket assets
base_url = "https://polysaas.supportsystem.com"

# List of missing assets (relative paths)
assets = [
    "css/osticket.css",
    "css/typeahead.css",
    "css/ui-lightness/jquery-ui-1.13.2.custom.min.css",
    "css/jquery-ui-timepicker-addon.css",
    "css/thread.css",
    "css/redactor.css",
    "css/flags.css",
    "css/rtl.css",
    "css/select2.min.css",
    "assets/default/css/theme.css",
    "assets/default/css/print.css",
    "js/jquery-3.7.0.min.js",
    "js/jquery-ui-1.13.2.custom.min.js",
    "js/jquery-ui-timepicker-addon.js",
    "js/osticket.js",
    "js/filedrop.field.js",
    "js/bootstrap-typeahead.js",
    "js/redactor.min.js",
    "js/redactor-plugins.js",
    "js/redactor-osticket.js",
    "js/select2.min.js",
]

# Local directory
local_base = "static/osticket"

os.makedirs(local_base, exist_ok=True)

for asset in assets:
    url = f"{base_url}/{asset}"
    local_path = os.path.join(local_base, asset)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    print(f"Downloading {url} to {local_path}")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded {asset}")
        else:
            print(f"Failed to download {asset}: {response.status_code}")
    except Exception as e:
        print(f"Error downloading {asset}: {e}")

print("Download complete.")