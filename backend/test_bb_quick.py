#!/usr/bin/env python3
"""Quick test for buzzer beater functionality"""
import requests
import json

# Test the API endpoint
url = "http://localhost:8000/api/v1/search"
headers = {"Content-Type": "application/json"}

# Test query
data = {
    "query": "lebron james buzzer beaters 2023-24",
    "limit": 10
}

print("Testing buzzer beater search...")
print(f"Query: {data['query']}")
print("-" * 50)

try:
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Status: Success")
        print(f"Total results: {result.get('total', 0)}")
        
        if result.get('results'):
            print("\nFound buzzer beaters:")
            for i, clip in enumerate(result['results'][:5]):
                desc = clip.get('description', 'No description')
                print(f"{i+1}. {desc}")
        else:
            print("\nNo results found")
            
        # Show AI response
        if result.get('aiResponse'):
            print(f"\nAI Summary: {result['aiResponse']['summary']}")
            
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Connection error: {e}")
    print("Make sure the backend server is running on port 8000")