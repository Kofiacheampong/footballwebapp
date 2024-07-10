import requests


def fetch_stats(api_key):
    headers = {'X-Auth-Token': api_key}
    url = 'https://api.football-data.org/v4/competitions/PD/standings'
    
    print(f"Making request to URL: {url} with headers: {headers}")
    
    response = requests.get(url, headers=headers)
    
    print(f"Fetching data for standings - Status code: {response.status_code}")
    print(f"Response content: {response.content}")

    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code}")
        return []

    data = response.json()
    
    if 'standings' not in data:
        print(f"'standings' key not found in the response")
        return []
    
    standings = []
    for standing in data['standings']:
        for team in standing['table']:
            team_data = {
                'position': team['position'],
                'team': team['team']['name'],
                'points': team['points'],
                'emblem': team['team']['crest'] 
            }
            standings.append(team_data)
    
    print(f"Processed standings data: {standings}")
    return standings