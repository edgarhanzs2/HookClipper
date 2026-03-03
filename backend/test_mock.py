from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

with open('backend/.env', 'wb') as f:
    f.write(b'dummy')

try:
    with open('backend/.env', 'rb') as f:
        res = client.post("/api/upload", files={"file": ("dummy.mp4", f, "video/mp4")}, data={"mock_ai": "true"})
        print(f"Status: {res.status_code}")
        print(f"Response: {res.json()}")
        
        job_id = res.json()["job_id"]
        status_res = client.get(f"/api/status/{job_id}")
        print(f"Job Initial State - mock_ai: {app.router.routes}") 
except Exception as e:
    print(f"Error: {e}")
