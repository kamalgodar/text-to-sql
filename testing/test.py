import pandas as pd
import requests
import uuid

# Load data and remove unnecessary column
df = pd.read_csv('testing/query.csv')
df.drop(columns='id', inplace=True, errors='ignore')

url = "http://127.0.0.1:9000/test_chat"

# Iterate over each question and send a POST request
for query in df['question'].values:
    print("User Question: ", query)
    response = requests.post(
        url,
        json={
            "user_query": query,
            "session_id": str(uuid.uuid4())
        }
    )
    print(f"Status Code: {response.status_code}")
    print("Response JSON:", response.json())
    print("\n\n")