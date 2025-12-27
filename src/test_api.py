import sys
import traceback

# Ensure the src directory is importable when running from project root
sys.path.append(r"c:\Users\Soham\OneDrive\Documents\python\app.1\src")

from fastapi.testclient import TestClient
from app import app

def run_test():
    client = TestClient(app)
    try:
        resp = client.post('/check-url', json={'url': 'https://google.com'})
        print('STATUS', resp.status_code)
        print(resp.text)
    except Exception:
        print('EXCEPTION during in-process request:')
        traceback.print_exc()

if __name__ == '__main__':
    run_test()
