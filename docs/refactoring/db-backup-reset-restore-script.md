# PolySaaS Django DB Backup, Reset, and Restore Script

# 1. Dump your data (excluding auth and contenttypes)
python manage.py dumpdata --natural-foreign --natural-primary --exclude auth.permission --exclude contenttypes > local-backup.json

# 2. Drop and recreate your local database
# (You must do this in your DB tool or with psql/Adminer/pgAdmin)
# Example for psql:
#   DROP DATABASE polysaas_dev;
#   CREATE DATABASE polysaas_dev OWNER youruser;

# 3. Run migrations to create a fresh schema
python manage.py migrate

# 4. (Optional) Edit local-backup.json to update any tenant_id to tenant_slug if needed
#    (Search/replace "tenant_id": to "tenant": and ensure the value is the slug, not the old id)

# 5. Load your data back in
python manage.py loaddata local-backup.json

# 6. Start your server and test
python manage.py runserver

# If you get errors on loaddata, you may need to fix up the JSON to match the new schema.
# Always keep a copy of your original backup!
