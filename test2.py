import requests

url = "https://api-football-v1.p.rapidapi.com/v3/leagues"

querystring = {"id":"39"}

headers = {
	"x-rapidapi-key": "3f1b9299famsh4b3faa45d4246b1p12e413jsn9a109f61fc76",
	"x-rapidapi-host": "api-football-v1.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())