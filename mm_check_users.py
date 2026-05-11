#!/usr/bin/env python
"""Check Mattermost database for existing users"""
import psycopg2
import sys

try:
    # Try external hostname format for Mattermost DB
    conn = psycopg2.connect(
        host='dpg-d7i893f7f7vs7390o3j0-a.singapore-postgres.render.com',
        port=5432,
        database='mattermost_btg0',
        user='mattermost',
        password='D3ttPexvU0qXGzLZb4BotF681xdbZRyp',
        sslmode='require'
    )
    cur = conn.cursor()
    
    # Check existing users
    print("=== EXISTING USERS ===")
    cur.execute("SELECT id, username, email, roles, createat FROM users ORDER BY createat DESC LIMIT 10")
    users = cur.fetchall()
    if users:
        for row in users:
            print(f"ID: {row[0][:8]}... | User: {row[1]} | Email: {row[2]} | Roles: {row[3]} | Created: {row[4]}")
    else:
        print("No users found - database is empty")
    
    # Check teams
    print("\n=== EXISTING TEAMS ===")
    cur.execute("SELECT id, name, displayname, type FROM teams ORDER BY createat DESC LIMIT 10")
    teams = cur.fetchall()
    if teams:
        for row in teams:
            print(f"ID: {row[0][:8]}... | Name: {row[1]} | Display: {row[2]} | Type: {row[3]}")
    else:
        print("No teams found")
    
    conn.close()
    
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
