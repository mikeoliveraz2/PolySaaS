# Tenant Data Isolation Discussion

## Multi-Tenant Logic Confirmation
- Each tenant is assigned a separate database schema.
- Instructions and all tenant-specific records are stored in their respective schemas.
- Example: If user in tenant A sets an instruction for path `ABC`, it is stored in schema A. If user in tenant B sets an instruction for path `ght`, it is stored in schema B.
- When matching instructions, queries are always scoped to the current tenant's schema:
  - `Instruction.objects.filter(tenant=current_tenant, path=matched_path)`
- Only instructions for the current tenant are matched and returned; instructions for other tenants are isolated and not visible or matched.

## Safety Confirmation
- Because each tenant's data is stored in a separate schema, there is strict data isolation at the database level.
- Users in tenant A cannot access or match instructions from tenant B, and vice versa.
- The multi-tenant setup enforces robust data separation and security.

---
Discussion saved: September 7, 2025
