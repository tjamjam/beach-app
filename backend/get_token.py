#!/usr/bin/env python3
"""
Helper script to retrieve the CF_API_TOKEN from Cloudflare Worker secrets.
This requires you to have wrangler CLI installed and be logged in.
"""

import subprocess
import json
import sys

def get_secret_value(secret_name):
    """Get a secret value from Cloudflare Worker using wrangler"""
    try:
        # Use wrangler to get the secret value
        result = subprocess.run(
            ['wrangler', 'secret', 'list'],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the JSON output
        secrets = json.loads(result.stdout)
        
        # Find the secret by name
        for secret in secrets:
            if secret['name'] == secret_name:
                print(f"Found {secret_name} in your Cloudflare Worker secrets.")
                print("To use this token, you can:")
                print(f"1. Export it: export CF_API_TOKEN='your_token_value'")
                print(f"2. Or create a .env file with: CF_API_TOKEN=your_token_value")
                print(f"3. Or run your script with: CF_API_TOKEN=your_token_value python check_status.py")
                return True
        
        print(f"Secret '{secret_name}' not found in your Cloudflare Worker.")
        return False
        
    except subprocess.CalledProcessError as e:
        print(f"Error running wrangler: {e}")
        print("Make sure you have wrangler CLI installed and are logged in.")
        return False
    except json.JSONDecodeError as e:
        print(f"Error parsing wrangler output: {e}")
        return False

def main():
    print("Checking for CF_API_TOKEN in your Cloudflare Worker secrets...")
    
    if get_secret_value('CF_API_TOKEN'):
        print("\n✅ CF_API_TOKEN is configured in your Cloudflare Worker.")
        print("You just need to set it as an environment variable when running your script.")
    else:
        print("\n❌ CF_API_TOKEN not found in your Cloudflare Worker secrets.")
        print("You need to set it up first:")
        print("1. Go to your Cloudflare Worker dashboard")
        print("2. Navigate to Settings > Variables")
        print("3. Add a new secret with name 'CF_API_TOKEN'")
        print("4. Set a secure token value")

if __name__ == "__main__":
    main() 