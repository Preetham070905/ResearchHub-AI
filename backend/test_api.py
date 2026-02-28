import httpx
import sys

BASE_URL = "http://localhost:8000"

def test_api():
    print("Testing API...")
    with httpx.Client() as client:
        # 1. Login
        print("1. Logging in...")
        resp = client.post(f"{BASE_URL}/auth/login", data={"username": "test@test.com", "password": "test123"})
        if resp.status_code != 200:
            print(f"Login failed: {resp.status_code} {resp.text}")
            return
        
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Test search
        print("\n2. Testing /agents/search-papers...")
        resp = client.post(f"{BASE_URL}/agents/search-papers", json={"query": "federated learning", "max_results": 2}, headers=headers)
        print(f"Search Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Search Error: {resp.text}")
        else:
            data = resp.json()
            papers = data.get('papers', [])
            print(f"Search Success. Papers found: {len(papers)}")
            if papers:
                print(f"First paper authors type: {type(papers[0].get('authors'))}")
            
        # 3. Test summarize
        print("\n3. Testing /agents/summarize...")
        resp = client.post(f"{BASE_URL}/agents/summarize", json={"query": "federated learning"}, headers=headers, timeout=60.0)
        print(f"Summarize Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Summarize Error: {resp.text}")
        else:
            res = resp.json()
            print(f"Summarize Success. Agent: {res.get('agent')}")
            
test_api()
