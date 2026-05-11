#!/usr/bin/env python
"""Check Mattermost database schema for token/session tables"""
import psycopg2

conn = psycopg2.connect(
    host='dpg-d7i893f7f7vs7390o3j0-a.singapore-postgres.render.com',
    port=5432,
    database='mattermost_btg0',
    user='mattermost',
    password='D3ttPexvU0qXGzLZb4BotF681xdbZRyp',
    sslmode='require'
)
cur = conn.cursor()

print("=== TABLES WITH 'token' OR 'session' ===")
cur.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND (table_name LIKE '%token%' OR table_name LIKE '%session%')
    ORDER BY table_name
""")
for row in cur.fetchall():
    print(f"  - {row[0]}")

print("\n=== ALL TABLES (sample) ===")
cur.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name
    LIMIT 30
""")
for row in cur.fetchall():
    print(f"  - {row[0]}")

conn.close()
