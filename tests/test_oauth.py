import requests
import json

# Test Google OAuth endpoint
data = {
    'access_token': 'test_token', 
    'email': 'test@example.com', 
    'name': 'Test User'
}

try:
    r = requests.post('http://localhost:5000/api/auth/google', json=data)
    print(f'Google OAuth test: {r.status_code}')
    if r.headers.get('content-type', '').startswith('application/json'):
        print(f'Response: {r.json()}')
    else:
        print(f'Response: {r.text}')
except Exception as e:
    print(f'Error: {e}')
