#!/usr/bin/env python
"""Create Personal Access Token for mikeoliveraz"""
import psycopg2
import secrets
import sys

def create_token():
    # Connect to Mattermost DB
    conn = psycopg2.connect(
        host='dpg-d7i893f7f7vs7390o3j0-a.singapore-postgres.render.com',
        port=5432,
        database='mattermost_btg0',
        user='mattermost',
        password='D3ttPexvU0qXGzLZb4BotF681xdbZRyp',
        sslmode='require'
    )
    cur = conn.cursor()
    
    # Get mikeoliveraz user ID
    cur.execute("SELECT id FROM users WHERE username = 'mikeoliveraz'")
    result = cur.fetchone()
    if not result:
        print("ERROR: User mikeoliveraz not found")
        return None
    
    user_id = result[0]
    print(f"Found user mikeoliveraz: {user_id}")
    
    # Generate token
    token = secrets.token_urlsafe(32)
    print(f"Generated token: {token[:20]}...")
    
    # Check if tokens table exists and create token
    try:
        # Insert into user_access_tokens table
        cur.execute("""
            INSERT INTO user_access_tokens (id, token, user_id, description, is_active, 
                created_at, updated_at, last_used_at)
            VALUES (
                gen_random_uuid()::text, 
                %s, 
                %s, 
                'PolySaaS provisioner token', 
                true,
                EXTRACT(EPOCH FROM NOW())::bigint * 1000,
                EXTRACT(EPOCH FROM NOW())::bigint * 1000,
                0
            )
            ON CONFLICT (token) DO NOTHING
        """, (token, user_id))
        
        conn.commit()
        print(f"SUCCESS: Token created for mikeoliveraz")
        print(f"\n=== ADD THIS TO YOUR .env FILE ===")
        print(f"MATTERMOST_ADMIN_TOKEN={token}")
        
    except Exception as e:
        print(f"ERROR creating token: {e}")
        # Try alternative - maybe table schema is different
        try:
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'user_access_tokens'")
            cols = cur.fetchall()
            print(f"Available columns: {[c[0] for c in cols]}")
        except Exception as e2:
            print(f"Could not check schema: {e2}")
        conn.rollback()
        return None
    
    conn.close()
    return token

if __name__ == "__main__":
    token = create_token()
    if token:
        sys.exit(0)
    else:
        sys.exit(1)
