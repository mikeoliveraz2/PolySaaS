# Swagger/OpenAPI Documentation for Navigation Items API

## Overview
The Navigation Items API endpoints have been fully documented using `drf_yasg` (Django REST Framework - Yet Another Swagger Generator). This provides interactive API documentation accessible via the Swagger UI.

## Accessing Swagger Documentation

### Swagger UI (Interactive)
- **URL**: `http://localhost:8000/dose/swagger/`
- **Features**:
  - Browse all API endpoints
  - Try out endpoints directly from the browser
  - View request/response schemas
  - See example requests and responses

### Swagger JSON (OpenAPI Spec)
- **URL**: `http://localhost:8000/dose/swagger.json`
- **Use Cases**:
  - Import into Postman
  - Generate client SDKs
  - API testing tools

## Navigation Items Endpoints in Swagger

All 5 navigation items endpoints are documented under the **"Navigation Items"** tag:

### 1. GET /dose/api/nav-panels/
**Operation**: Get Navigation Panels
**Summary**: Retrieve all active navigation panels for the current tenant
**Authentication**: Required
**Response Example**:
```json
{
  "panels": [
    {"id": 1, "title": "Quick Actions", "sort_order": 1},
    {"id": 2, "title": "Integrations", "sort_order": 2}
  ]
}
```

### 2. GET /dose/api/my-nav-items/
**Operation**: Get My Personal Navigation Items
**Summary**: Retrieve all personal navigation items created by the authenticated user
**Authentication**: Required
**Filtering**: Automatic - returns only items where `is_personal=True` and `created_by_user=current_user`
**Response Example**:
```json
{
  "items": [
    {
      "id": 42,
      "title": "My GitHub",
      "url": "https://github.com/username",
      "icon_value": "🔗",
      "description": "My GitHub profile",
      "panel": "Quick Actions",
      "sort_order": 1,
      "clicks": 15
    }
  ]
}
```

### 3. POST /dose/api/nav-items/create/
**Operation**: Create Personal Navigation Item
**Summary**: Create a new personal navigation item (bookmark)
**Authentication**: Required
**Request Body**:
```json
{
  "title": "My GitHub",              // Required
  "url": "https://github.com/username", // Required
  "icon_value": "🔗",                // Optional (default: 🔗)
  "description": "Quick link",       // Optional
  "panel_id": 1                      // Optional
}
```
**Response Example**:
```json
{
  "success": true,
  "message": "Navigation item created successfully",
  "item": {
    "id": 42,
    "title": "My GitHub",
    "url": "https://github.com/username"
  }
}
```
**Error Responses**:
- `400`: Missing required fields (title or url)
- `500`: Server error

### 4. DELETE /dose/api/nav-items/{item_id}/delete/
**Operation**: Delete Personal Navigation Item
**Summary**: Delete a personal navigation item (owner only)
**Authentication**: Required
**Path Parameter**: `item_id` (integer) - ID of the item to delete
**Security**: Validates ownership (`is_personal=True` and `created_by_user=current_user`)
**Response Example**:
```json
{
  "success": true,
  "message": "Navigation item deleted successfully"
}
```
**Error Responses**:
- `404`: Item not found or permission denied
- `500`: Server error

### 5. PUT/PATCH /dose/api/nav-items/{item_id}/update/
**Operation**: Update Personal Navigation Item
**Summary**: Update a personal navigation item (owner only)
**Authentication**: Required
**Path Parameter**: `item_id` (integer) - ID of the item to update
**Request Body** (all fields optional):
```json
{
  "title": "My Updated GitHub",
  "url": "https://github.com/newusername",
  "icon_value": "📚",
  "description": "My new GitHub profile",
  "panel_id": 2
}
```
**Response Example**:
```json
{
  "success": true,
  "message": "Navigation item updated successfully",
  "item": {
    "id": 42,
    "title": "My Updated GitHub",
    "url": "https://github.com/newusername"
  }
}
```
**Error Responses**:
- `404`: Item not found or permission denied
- `500`: Server error

## Swagger Decorators Used

### @swagger_auto_schema
Each endpoint uses the `@swagger_auto_schema` decorator from `drf_yasg` to provide:

1. **operation_summary**: Short description shown in endpoint list
2. **operation_description**: Detailed explanation of what the endpoint does
3. **request_body**: Schema for POST/PUT/PATCH request bodies
4. **manual_parameters**: Path/query parameters (e.g., `item_id`)
5. **responses**: Response schemas for different status codes
6. **tags**: Grouping endpoints into categories (all use `['Navigation Items']`)
7. **examples**: Sample request/response JSON

### Example Decorator Structure
```python
@swagger_auto_schema(
    method='post',
    operation_summary="Create Personal Navigation Item",
    operation_description="Detailed description here...",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['title', 'url'],
        properties={
            'title': openapi.Schema(type=openapi.TYPE_STRING, example='My GitHub'),
            'url': openapi.Schema(type=openapi.TYPE_STRING, format='uri', example='https://github.com/username'),
        }
    ),
    responses={
        200: openapi.Response(
            description="Success response",
            examples={"application/json": {...}}
        ),
        400: openapi.Response(
            description="Error response",
            examples={"application/json": {...}}
        )
    },
    tags=['Navigation Items']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_create_nav_item(request):
    # Implementation here
    pass
```

## API Documentation Structure

### Schema Information (Updated)
The Swagger schema has been enhanced with:

```python
openapi.Info(
    title="Dose API",
    default_version='v1',
    description="""
    # Dose Multi-Tenant System API

    Complete API documentation for the DOSE platform.

    ## Key Features
    - Multi-Tenant Architecture
    - Session-Based Authentication
    - Personal & Shared Resources

    ## API Categories

    ### Navigation Items
    Manage personal and tenant-wide navigation items...

    ### Atomic Services
    Upload and manage differential equations...

    [etc.]
    """,
    terms_of_service="https://www.dose.com/terms/",
    contact=openapi.Contact(email="support@dose.com"),
    license=openapi.License(name="Proprietary - DOSE LLC 2025"),
)
```

## Using Swagger UI

### 1. Navigate to Swagger
Visit `http://localhost:8000/dose/swagger/` in your browser

### 2. Authenticate
- Click "Authorize" button (top right)
- Login using Django session (may redirect to `/admin/` or `/dose/login/`)
- Return to Swagger UI

### 3. Browse Endpoints
- Scroll to **"Navigation Items"** section
- Click on any endpoint to expand details
- View request/response schemas

### 4. Try It Out
1. Click "Try it out" button
2. Fill in request parameters/body
3. Click "Execute"
4. View response below (status code, headers, body)

### 5. Example: Create Navigation Item
1. Expand `POST /dose/api/nav-items/create/`
2. Click "Try it out"
3. Edit request body:
   ```json
   {
     "title": "Test Link",
     "url": "https://example.com",
     "icon_value": "🔗"
   }
   ```
4. Click "Execute"
5. Check response - should see `"success": true` and item ID

## Integration with Existing Endpoints

The Navigation Items endpoints complement existing Swagger-documented endpoints:

### Existing Endpoint Categories
- **Tenants**: Tenant management, switching, settings
- **UserProfiles**: User profile CRUD
- **ML Engines**: Machine learning components
- **ML Taxonomies**: AI taxonomy management
- **ML Datasets**: Dataset management
- **Atomic Services**: Parameter set uploads
- **Dashboard Buttons**: User dashboard customization

### New Category
- **Navigation Items**: Personal bookmark management (NEW)

All categories are visible in the Swagger UI sidebar, organized by tags.

## Postman Integration

### Import OpenAPI Spec
1. Open Postman
2. Click "Import" → "Link"
3. Enter: `http://localhost:8000/dose/swagger.json`
4. Postman auto-generates collection with all endpoints

### Collection Features
- All endpoints with correct HTTP methods
- Path parameters pre-configured
- Request body schemas
- Example requests
- Environment variables for `baseUrl`

## Client SDK Generation

### Using Swagger Codegen
```bash
# Install swagger-codegen
npm install -g @openapitools/openapi-generator-cli

# Generate Python client
openapi-generator-cli generate \
  -i http://localhost:8000/dose/swagger.json \
  -g python \
  -o ./dose-python-client

# Generate JavaScript/TypeScript client
openapi-generator-cli generate \
  -i http://localhost:8000/dose/swagger.json \
  -g typescript-axios \
  -o ./dose-ts-client
```

### Using Generated Client
```python
# Python example
from dose_client import ApiClient, NavigationItemsApi

client = ApiClient(configuration=config)
nav_api = NavigationItemsApi(client)

# Create item
response = nav_api.api_create_nav_item({
    "title": "My Link",
    "url": "https://example.com"
})
print(response.item.id)

# Get my items
items = nav_api.api_get_my_nav_items()
for item in items.items:
    print(f"{item.title}: {item.url}")
```

## Response Schema Validation

All endpoints use consistent response schemas:

### Success Response (200)
```json
{
  "success": true,
  "message": "Operation successful",
  "item": {
    "id": 42,
    "title": "...",
    "url": "..."
  }
}
```

### Error Response (400/404/500)
```json
{
  "success": false,
  "message": "Error description"
}
```

### List Response
```json
{
  "items": [
    {...},
    {...}
  ]
}
```

## Testing with Swagger UI

### Manual Test Workflow
1. **Create Panel** (if needed):
   - Use admin interface to create NavigationPanel
   - Note the panel ID

2. **Create Item**:
   - POST to `/dose/api/nav-items/create/`
   - Provide title, URL, optional panel_id
   - Note the returned item ID

3. **List Items**:
   - GET `/dose/api/my-nav-items/`
   - Verify newly created item appears

4. **Update Item**:
   - PATCH `/dose/api/nav-items/{item_id}/update/`
   - Change title or URL
   - Verify changes in response

5. **Delete Item**:
   - DELETE `/dose/api/nav-items/{item_id}/delete/`
   - Verify success response

6. **Verify Deletion**:
   - GET `/dose/api/my-nav-items/`
   - Confirm item is gone

## Security Notes

### Authentication Required
All endpoints require `IsAuthenticated` permission:
- User must be logged in
- Session must be active
- Swagger UI handles cookies automatically

### Ownership Validation
For create/update/delete operations:
- Item marked as `is_personal=True`
- Item associated with `created_by_user=request.user`
- Other users cannot see/modify personal items
- Admins can create tenant-wide items (`is_personal=False`)

### CSRF Protection
- All mutation endpoints (POST/PUT/PATCH/DELETE) require CSRF token
- Swagger UI auto-handles CSRF via cookies
- External clients must include `X-CSRFToken` header

## Troubleshooting

### Issue: Endpoints not showing in Swagger
**Solution**:
- Ensure `@api_view` decorator is used
- Check that view is imported in `urls.py`
- Verify URL route is registered

### Issue: "Authentication credentials not provided"
**Solution**:
- Click "Authorize" in Swagger UI
- Login via Django admin
- Return to Swagger and try again

### Issue: Examples not rendering
**Solution**:
- Check JSON syntax in `examples` parameter
- Ensure `application/json` content type specified
- Clear browser cache

### Issue: Request body validation failing
**Solution**:
- Check `required` fields in schema
- Verify field types match schema
- Review `openapi.Schema` properties

## Future Enhancements

### Additional Documentation
- [ ] Add detailed field descriptions
- [ ] Include more response examples (edge cases)
- [ ] Document rate limiting (if implemented)
- [ ] Add webhook documentation

### Schema Improvements
- [ ] Add request/response header documentation
- [ ] Document authentication flows in detail
- [ ] Include deprecation notices for old endpoints
- [ ] Add API versioning examples

### Testing Integration
- [ ] Integrate with pytest using Swagger spec
- [ ] Auto-generate API tests from schemas
- [ ] Add contract testing
- [ ] Performance benchmarks per endpoint

## Related Files

### Modified
- `dose/views/main.py`: Added `@swagger_auto_schema` decorators to all 5 endpoints
- `dose/urls.py`: Enhanced `schema_view` with detailed API description

### Dependencies
- `drf-yasg`: Swagger/OpenAPI generator for Django REST Framework
- `djangorestframework`: Required for `@api_view` and `@permission_classes`

### Configuration
- `mysite/settings.py`: `drf_yasg` in `INSTALLED_APPS`
- `dose/urls.py`: Swagger routes (`/dose/swagger/`, `/dose/swagger.json`)

## References

- **drf-yasg Documentation**: https://drf-yasg.readthedocs.io/
- **OpenAPI Specification**: https://swagger.io/specification/
- **Swagger UI**: https://swagger.io/tools/swagger-ui/
- **Postman Integration**: https://learning.postman.com/docs/integrations/available-integrations/working-with-openAPI/

## Conclusion

The Navigation Items API is now fully documented in Swagger with:
- ✅ 5 endpoints with complete schemas
- ✅ Request/response examples
- ✅ Authentication requirements
- ✅ Error response documentation
- ✅ Interactive testing via Swagger UI
- ✅ Postman import support
- ✅ SDK generation capability

Users can now discover, test, and integrate with the Navigation Items API using industry-standard OpenAPI tooling!
