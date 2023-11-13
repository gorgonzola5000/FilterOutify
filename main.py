
import requests

# Set up authorization headers
client_id = 'ffb1d8d326f248fb9e5ebce160bb77b7'
client_secret = '9ad69e31226141348c25d56ad4d25aa5'
auth_url = 'https://accounts.spotify.com/api/token'
headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
}

data = {
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret,
}

auth_response = requests.post(auth_url, headers=headers, data=data)

auth_response_data = auth_response.json()
access_token = auth_response_data['access_token']
headers = {
    'Authorization': f'Bearer {access_token}'
}

# Replace 'artist_id' with the Spotify ID of the artist
artist_id = '0k17h0D3J5VfsdmQ1iZtE9'
response = requests.get(f'https://api.spotify.com/v1/artists/{artist_id}', headers=headers)
print(response.json())
