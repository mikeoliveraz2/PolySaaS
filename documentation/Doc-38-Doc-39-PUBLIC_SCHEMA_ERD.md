# Entity Relationship Diagram (ERD) - Public Schema

## dose/models.py

### Tenant
- name: CharField
- slug: SlugField
- schema_name: CharField
- description: TextField
- tagline: CharField
- logo: ImageField
- created_at: DateTimeField
- is_active: BooleanField
- admin_theme: CharField

### UserProfile
- user: OneToOneField(User)
- tenant: ForeignKey(Tenant)
- created_at: DateTimeField

### TenantAwareModel (abstract)
- tenant: ForeignKey(Tenant)

### MLEngine (TenantAwareModel)
- engineName: CharField
- engineEndPoint: CharField
- matchingEventKey: CharField
- description: CharField
- parameters_json: JSONField
- pub_date: DateTimeField

### MLTaxonomy (TenantAwareModel)
- matchingEventKey: CharField
- description: CharField
- content_json: JSONField
- pub_date: DateTimeField

### MLDataset (TenantAwareModel)
- matchingEventKey: CharField
- isTraining: BooleanField
- description: CharField
- content_json: JSONField
- pub_date: DateTimeField

### CallBackData (TenantAwareModel)
- matchingEventKey: CharField
- description: CharField
- parameters_json: JSONField
- pub_date: DateTimeField

### Instruction (TenantAwareModel)
- eventKey: CharField
- requestpath: CharField
- requestmethod: CharField
- direction: CharField
- urllist: CharField
- appusername: CharField
- executescript: CharField
- description: CharField
- parameters_json: JSONField
- pub_date: DateTimeField

### Task (TenantAwareModel)
- title: CharField
- matchingEventKey: CharField
- description: TextField
- parameters_json: JSONField
- completed: BooleanField
- created_at: DateTimeField
- completed_at: DateTimeField

### NavigationPanel (TenantAwareModel)
- title: CharField
- panel_type: CharField
- description: TextField
- is_active: BooleanField
- sort_order: PositiveIntegerField
- panel_css_class: CharField
- panel_background_color: CharField
- created_at: DateTimeField
- updated_at: DateTimeField

### NavigationItem
- panel: ForeignKey(NavigationPanel)
- title: CharField
- item_type: CharField

## parameters/models.py

### Parameter
- id: BigAutoField
- matchingKey: CharField
- sequence: IntegerField
- param_kwargs_json: JSONField
- param1-10: CharField
- description: CharField
- created_at: DateTimeField
- updated_at: DateTimeField
- created_by: ForeignKey(User)

## Relationships
- UserProfile.user → User
- UserProfile.tenant → Tenant
- All models inheriting TenantAwareModel have tenant → Tenant
- Parameter.created_by → User
- NavigationItem.panel → NavigationPanel (which has tenant)
