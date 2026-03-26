"""Quick test of endpoint catalog matching and normalization."""
from dose.services.app_endpoint_catalog import match_endpoint, normalize_data

# Test Dolibarr customer create
app, entity, action, config = match_endpoint('/admin/dolibarr/api/index.php/thirdparties', 'POST')
print(f"Match: {app}.{entity}.{action}")
print(f"Topic: {config['topic']}")

test_data = {
    'name': 'Acme Corp',
    'email': 'info@acme.com',
    'phone': '555-1234',
    'address': '123 Main St',
    'town': 'Springfield',
    'zip': '62701',
    'country_code': 'US',
    'client': '1',
}
norm = normalize_data(test_data, config['field_map'])
print(f"Normalized: {norm}")

# Test Odoo partner create
app2, entity2, action2, config2 = match_endpoint('/web/dataset/call_kw/res.partner/create', 'POST')
print(f"\nMatch: {app2}.{entity2}.{action2}")
print(f"Topic: {config2['topic']}")

# Test no match
app3, _, _, _ = match_endpoint('/some/random/path', 'GET')
print(f"\nNo match test: {app3}")
