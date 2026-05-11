#!/usr/bin/env python
"""Create Personal Access Token for mikeoliveraz"""
import psycopg2
import secrets
import string
import sys
import re

def create_token():
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
    print(f"Found user mikeoliveraz: {user_id[:20]}...")
    
    # Generate Mattermost-style token (26 chars alphanumeric)
    # Mattermost tokens are exactly 26 characters
    alphabet = string.ascii_lowercase + string.digits
    token = ''.join(secrets.choice(alphabet) for _ in range(26))
    
    # Generate Mattermost-style ID (26 chars lowercase alphanumeric)
    mm_id = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(26))
    
    # Insert token
    try:
        cur.execute("""
            INSERT INTO useraccesstokens (id, token, userid, description, isactive)
            VALUES (%s, %s, %s, 'PolySaaS provisioner', true)
        """, (mm_id, token, user_id))
        
        conn.commit()
        print(f"SUCCESS: Token created")
        print(f"\n=== ADD THIS TO D:\\PolySaaS\\.env ===")
        print(f"MATTERMOST_ADMIN_TOKEN={token}")
        
        # Update .env file
        update_env_file(token)
        
    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
        return None
    
    conn.close()
    return token

def update_env_file(token):
    env_path = r"D:\PolySaaS\.env"
    try:
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Remove empty or placeholder MATTERMOST_ADMIN_TOKEN lines
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if line.strip().startswith('MATTERMOST_ADMIN_TOKEN='):
                val = line.split('=', 1)[1].strip()
                if val and val not in ['your_copied_token', 'your_token_here', 'your_mm_admin_token_here']:
                    new_lines.append(line)  # Keep existing valid token
                else:
                    continue  # Skip empty/placeholder
            else:
                new_lines.append(line)
        
        # Add new token if not already present
        if f"MATTERMOST_ADMIN_TOKEN={token}" not in content:
            new_lines.append(f"MATTERMOST_ADMIN_TOKEN={token}")
        
        with open(env_path, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print(f"\n✓ Updated {env_path}")
        
    except Exception as e:
        print(f"Could not auto-update .env: {e}")
        print("Please manually add the line above to your .env file")

if __name__ == "__main__":
    token = create_token()
    sys.exit(0 if token else 1)
