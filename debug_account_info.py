import requests
import json

# Test the account info issue
base_url = "https://outlook-connector.preview.emergentagent.com/api"

# Login first
login_response = requests.post(f"{base_url}/auth/login", json={
    "email": "demo@postadepo.com",
    "password": "demo123"
})

if login_response.status_code == 200:
    token = login_response.json()['token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get connected accounts
    accounts_response = requests.get(f"{base_url}/connected-accounts", headers=headers)
    print("Connected Accounts:")
    print(json.dumps(accounts_response.json(), indent=2))
    
    # Get emails
    emails_response = requests.get(f"{base_url}/emails?folder=inbox", headers=headers)
    emails_data = emails_response.json()
    
    print(f"\nFirst 3 emails account info:")
    for i, email in enumerate(emails_data['emails'][:3]):
        print(f"Email {i+1}:")
        print(f"  Subject: {email.get('subject', 'No subject')}")
        print(f"  Sender: {email.get('sender', 'No sender')}")
        print(f"  Account ID: {email.get('account_id', 'No account_id')}")
        print(f"  Account Info: {email.get('account_info', 'No account_info')}")
        print()
else:
    print(f"Login failed: {login_response.status_code}")