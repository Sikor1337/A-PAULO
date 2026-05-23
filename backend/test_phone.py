import urllib.request, json
data = json.dumps({'full_name': 'Test', 'email': 'test@test.pl', 'phone': '123123123123123', 'join_date': '2024-01-01'}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/api/v1/volunteers/', data=data, headers={'Content-Type': 'application/json'}, method='POST')
try:
    with urllib.request.urlopen(req) as response:
        print('SUKCES:', response.status)
except urllib.error.HTTPError as e:
    print('ODRZUCENIE:', e.code, e.read().decode('utf-8'))
