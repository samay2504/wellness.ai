import requests

headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo0LCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJleHAiOjE3NTQ2OTExNzB9.ID4hbc21n003GCn7x1KTPrd9pxU0AKtF_X9yCMbRSkM'
}

try:
    r = requests.get('http://localhost:5000/api/blink-events', headers=headers)
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f'Events count: {len(data["events"])}')
        if data["events"]:
            print(f'First event: {data["events"][0]}')
    else:
        print(f'Error: {r.text}')
except Exception as e:
    print(f'Error: {e}')
