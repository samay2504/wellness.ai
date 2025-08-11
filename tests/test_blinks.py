import requests
import json

# Test blink data submission with the JWT token from our existing user
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo0LCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJleHAiOjE3NTQ2OTExNzB9.ID4hbc21n003GCn7x1KTPrd9pxU0AKtF_X9yCMbRSkM"

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Test blink data submission
blink_data = {
    'blinks': [
        {
            'timestamp': 1754604600.0,
            'count': 1,
            'session_id': 'test_session_123',
            'device_id': 'test_device',
            'open_closed': 'closed',
            'direction': 'both',
            'confidence': 0.95
        }
    ]
}

try:
    r = requests.post('http://localhost:5000/api/blink-data', json=blink_data, headers=headers)
    print(f'Blink submission test: {r.status_code}')
    if r.headers.get('content-type', '').startswith('application/json'):
        print(f'Response: {r.json()}')
    else:
        print(f'Response: {r.text}')
except Exception as e:
    print(f'Error: {e}')
