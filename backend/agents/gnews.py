import requests

# Test your new key directly
def test_gnews_key(api_key):
    url = f"https://gnews.io/api/v4/top-headlines?token={api_key}&lang=en"
    
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    return response.json() if response.status_code == 200 else None

# Test your new API key
NEW_API_KEY = "846ff100d69e0312a9fabfa4e39e13b6"
test_gnews_key(NEW_API_KEY)