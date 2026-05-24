import requests

url = 'http://127.0.0.1:3000/query'

payload = {
    "sql": "SELECT Name FROM dndstats WHERE Size = ?",
    "parameters": ["Medium"]  # Rust expects a Vec<String>, so an empty list works perfectly
}

while True:
    sql = input("Enter sql query (q to exit):")
    if sql == "q":
        break
    parameters = [input("Enter parameter: ")]
    payload = {
        "sql": sql,
        "parameters": parameters
    }
    response = requests.put(url, json=payload)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")


