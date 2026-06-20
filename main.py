import requests

def fetch_data(endpoint, filters={}):
    url = f"" #colocar o url da api
    response = requests.get(url, params=filters)
    
    return response.json() if response.status_code == 200 else None

# requisão
characters = fetch_data("characters", ) #filtro do que usar : ,{name: 'Daniel'}

if characters:
    print(characters)
else:
    print("Failed to fetch data")

    