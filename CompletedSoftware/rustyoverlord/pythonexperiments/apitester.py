# Simple API tester to poke the settlement sim
import requests
import json
import time

BASE_URL = "http://localhost:3000"  # change if needed

def get_root():
    r = requests.get(f"{BASE_URL}/")
    print("GET / ->", r.status_code, r.text)


def get_state():
    r = requests.get(f"{BASE_URL}/state")
    print("GET /state ->", r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except:
        print(r.text)


def get_meta():
    r = requests.get(f"{BASE_URL}/meta")
    print("GET /meta ->", r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except:
        print(r.text)


def post_order(payload):
    r = requests.post(f"{BASE_URL}/order", json=payload)
    print("POST /order ->", r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except:
        print(r.text)


def post_commit(payload=None):
    r = requests.post(f"{BASE_URL}/commit", json=payload or {})
    print("POST /commit ->", r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except:
        print(r.text)


# --- Test workflow ---
def run_test_sequence():
    print("\n--- Root Check ---")
    get_root()

    print("\n--- Initial State ---")
    get_state()

    print("\n--- Meta Info ---")
    get_meta()

    print("\n--- Submit Order ---")
    sample_order = {
        "item": "widget",
        "quantity": 3
    }
    post_order(sample_order)

    time.sleep(0.5)

    print("\n--- Commit ---")
    post_commit()

    time.sleep(0.5)

    print("\n--- State After Commit ---")
    get_state()


if __name__ == "__main__":
    run_test_sequence()