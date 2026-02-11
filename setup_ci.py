"""
CI Setup Helper
Run this script to generate the secret values needed for GitHub Actions.
"""
import json
import os
from pathlib import Path

def get_file_content(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            # Load and dump to minify JSON
            try:
                data = json.load(f)
                return json.dumps(data, separators=(',', ':'))
            except json.JSONDecodeError:
                return f.read().strip()
    return None

def main():
    print("\n=== GitHub Actions Secrets Setup ===\n")
    
    # 1. YOUTUBE_CLIENT_SECRETS
    client_secrets = get_file_content("client_secrets.json")
    if client_secrets:
        print("✅ Found client_secrets.json")
        print("\nCREATE SECRET: YOUTUBE_CLIENT_SECRETS")
        print("VALUE:")
        print(client_secrets)
    else:
        print("❌ client_secrets.json not found!")

    print("\n" + "-"*50 + "\n")

    # 2. YOUTUBE_TOKEN_JSON
    token_json = get_file_content("token.json")
    if token_json:
        print("✅ Found token.json")
        print("\nCREATE SECRET: YOUTUBE_TOKEN_JSON")
        print("VALUE:")
        print(token_json)
    else:
        print("❌ token.json not found!")
        print("Run 'python main.py setup-youtube' first to authenticate.")

    print("\n" + "-"*50 + "\n")

    # 3. Other Secrets
    print("Don't forget to add these other secrets from your .env file:")
    print("- ELEVENLABS_API_KEY")
    print("- PEXELS_API_KEY")
    print("- TELEGRAM_BOT_TOKEN")
    print("- TELEGRAM_CHAT_ID")
    
    print("\nTo run this manually: python setup_ci.py")

if __name__ == "__main__":
    main()
