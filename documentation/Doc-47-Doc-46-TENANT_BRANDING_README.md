# Dose Tenant Branding System

## Overview
This Django application provides a multi-tenant system with customizable branding features including tenant logos, names, and taglines in the admin interface.

## Features
- **Multi-tenant Architecture**: Using django-tenants for schema isolation
- **Tenant Branding**: Logo upload, custom names, and taglines
- **Admin Interface**: Custom admin with tenant-specific branding
- **Popup-free Interface**: No popup windows for better user experience
- **User Management**: Tenant-specific user administration

## Models

### Tenant
- `name`: Organization name
- `tagline`: Custom tagline/slogan  
- `logo`: Image upload for tenant logo
- `schema_name`: Database schema identifier
- `created_on`: Creation timestamp

### TenantUser
- Extends Django's AbstractUser
- `tenant`: Foreign key to Tenant
- `is_tenant_admin`: Boolean for tenant administration rights

### Domain
- `domain`: Domain name for tenant access
- `tenant`: Foreign key to Tenant
- `is_primary`: Primary domain flag

## Setup Instructions

### 1. Database Configuration
The system supports both PostgreSQL (recommended) and SQLite (development).

**PostgreSQL (Production):**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': 'dose_development',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

**SQLite (Development):**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### 2. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate_schemas --shared
python manage.py migrate_schemas
```

### 3. Create Demo Tenant
```bash
python manage.py setup_tenant_branding --tenant-name "Your Company" --domain "yourcompany.localhost"
```

### 4. Access Admin Interface
- Navigate to: `http://yourcompany.localhost:8000/admin/`
- Login with: `admin` / `admin123`

## Admin Interface Features

### Tenant Branding Management
The admin interface provides comprehensive logo and tagline management:

#### **Logo Management**
- **Upload Interface**: Drag-and-drop or click to upload logo files
- **File Support**: PNG, JPG, SVG, and other image formats
- **Live Preview**: See how your logo will appear before saving
- **Size Recommendations**: Optimal size guidance (200x200px or larger)
- **Automatic Optimization**: Images are automatically optimized for web display

#### **Tagline Management**
- **Text Field**: Simple text input for your company tagline/slogan
- **Character Guidance**: Visual indicators for optimal length
- **Live Preview**: See tagline in context with your logo
- **Rich Display**: Taglines appear throughout the admin interface

#### **Branding Preview**
- **Real-time Preview**: See exactly how branding appears in admin header
- **Interactive Display**: Preview updates as you make changes
- **Mobile Preview**: See how branding appears on different screen sizes

### **Admin Interface Navigation**

1. **Access Tenant Admin**:
   - Go to: `http://yourcompany.localhost:8000/admin/`
   - Navigate to: `Dose` → `Tenants`
   - Click on your tenant name

2. **Update Logo**:
   - Scroll to "Visual Branding" section
   - Click "Choose File" next to Logo field
   - Upload your image file
   - See immediate preview below
   - Click "Save" to apply changes

3. **Update Tagline**:
   - In "Visual Branding" section
   - Enter text in "Tagline" field
   - See preview in "Branding Preview" section
   - Click "Save" to apply changes

4. **View Results**:
   - Logo and tagline appear in admin header immediately
   - Refresh any admin page to see updated branding
   - Changes are visible across all admin interfaces

### **Command Line Management**
For advanced users, manage branding via command line:

```bash
# List all tenants and their branding status
python manage.py manage_branding --list

# Update tagline for tenant ID 1
python manage.py manage_branding --tenant-id 1 --set-tagline "Your Company Slogan"

# Update logo for tenant ID 1
python manage.py manage_branding --tenant-id 1 --logo-path "/path/to/logo.png"
```

## File Structure
```
dose/
├── models.py              # Tenant, Domain, TenantUser models
├── admin.py               # Custom admin with branding
├── management/
│   └── commands/
│       └── setup_tenant_branding.py
static/
└── admin/
    └── css/
        └── tenant_admin.css    # Custom admin styles
templates/
└── admin/
    └── base_site.html         # Custom admin template
```

## Customization

### Adding New Branding Fields
To add additional branding options:

1. Add fields to Tenant model:
```python
class Tenant(TenantMixin):
    primary_color = models.CharField(max_length=7, default='#007bff')
    secondary_color = models.CharField(max_length=7, default='#6c757d')
```

2. Update admin fieldsets:
```python
fieldsets = (
    ('Branding', {
        'fields': ('logo', 'tagline', 'primary_color', 'secondary_color'),
    }),
)
```

### Custom Admin Templates
The system uses custom templates in `templates/admin/` that can be modified to change the appearance and behavior of the admin interface.

## Development Tips

1. **Media Files**: Ensure MEDIA_ROOT and MEDIA_URL are configured for logo uploads
2. **Static Files**: Run `collectstatic` to gather admin CSS files
3. **Database**: Use PostgreSQL for production multi-tenant setup
4. **Domains**: Add domains to your hosts file for local development

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running and credentials are correct
- For development, switch to SQLite in settings.py

### Migration Issues
- Use `migrate_schemas --shared` for shared apps
- Use `migrate_schemas` for tenant-specific migrations

### Logo Upload Issues
- Check MEDIA_ROOT permissions
- Verify MEDIA_URL is correctly configured
- Ensure directory exists: `mkdir -p media/tenant_logos/`

## Security Notes
- Change default admin password in production
- Use strong SECRET_KEY in settings
- Configure proper database permissions
- Set DEBUG=False in production
