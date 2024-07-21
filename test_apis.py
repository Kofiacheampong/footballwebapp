import pandas as pd
import requests
import time
import json
import pprint


API_KEY = 'AIzaSyC5lldmh0NhxuoVRfGsJ8U0zg_fkBC5974'
channel_id  = 'UCOA4jOc0POjzaK2WYOWvmCw'

url = 'https://www.googleapis.com/youtube/v3/search?key='+API_KEY+'&part=snippet,id&order=date&maxResults=5'
response = requests.get(url).json()

pprint.pprint (response)