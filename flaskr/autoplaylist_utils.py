import requests
from flask import session
import time
import json

def get_playlists():
    headers = {
                'Authorization': f'Bearer {session["authorization_token"]}'
            }
    try:
        response = requests.get('https://api.spotify.com/v1/me/playlists', headers=headers)
        response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx
    except requests.exceptions.HTTPError as err:
        print(f'HTTP error occurred: {err}')  # or handle the error in a way that's appropriate for your application
    else:
        response_json = response.json()  # get the first page of playlists of the user
    playlists_dict = {}
    for item in response_json['items']:
        if item['images']:
            temp_dict = {
                "name": item['name'],
                "ap_id": None,
                "public": item['public'],
                "image": item['images'][0]['url'],
                "tracks_total": item['tracks']['total']
                }
        else:
            temp_dict = {
                "name": item['name'],
                "ap_id": None,
                "public": item['public'],
                "image": None,
                "tracks_total": item['tracks']['total']
                }
        playlists_dict[item['id']] = temp_dict

    while response_json['next'] != None: # get the rest of the pages of playlists of the user
        time.sleep(2)
        response = requests.get(response_json['next'], headers=headers)
        response_json = response.json()
        for item in response_json['items']:
            temp_dict = {
                "name": item['name'],
                "ap_id": None,
                "public": item['public'],
                "image": item['images'][0]['url'],
                "tracks_total": item['tracks']['total']
            }
            playlists_dict[item['id']] = temp_dict

    session['user_playlists'] = playlists_dict

    for key in playlists_dict:
        item = playlists_dict[key]
        if item['name'].endswith(' AP'):
            name_without_ap = item['name'].replace(' AP', '')
            for key2 in playlists_dict:
                item2 = playlists_dict[key2]
                if item2['name'] == name_without_ap:
                    session['user_playlists'][key2]["ap_id"] = key

def get_tracks(playlist_id):
    headers = {
        'Authorization': f'Bearer {session["authorization_token"]}'
        # add limit 50
    }
    tracks_dict = {}
    while True: # do
        tracks_temp = requests.get(f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks', headers=headers)
        tracks_temp_json = tracks_temp.json()
        for item in tracks_temp_json['items']:
            temp_dict = {
                "name": item['track']['name'],
                "artist": item['track']['artists'][0]['name'],
                "album": item['track']['album']['name'],
                "image": item['track']['album']['images'][0]['url']
                # "genres": item['track']['artists'][0]['genres']
            }
            tracks_dict[item['track']['id']] = temp_dict
        time.sleep(2)
        if tracks_temp_json['next'] == None: # while tracks_temp['next'] != None, so while there are more pages of tracks
            break
    return tracks_dict

def create_playlist(playlist_id):
    headers = {
    'Authorization': f'Bearer {session["authorization_token"]}',
    'Content-Type': 'application/json'
    }
    data = {
        'name': f"{session['user_playlists'][playlist_id]['name']} AP",
        'public': False
    }
    response = requests.post(f'https://api.spotify.com/v1/users/{session["user_id"]}/playlists', headers=headers, data=json.dumps(data))
    if response.status_code == 201:
        response_json = response.json()

        session['user_playlists'][playlist_id]['ap_id'] = response_json['id']
        session.modified = True

def get_user_id():
    if 'authorization_token' in session:
        headers = {
            'Authorization': f'Bearer {session["authorization_token"]}'
        }
        response = requests.get('https://api.spotify.com/v1/me', headers=headers)
        if response.status_code == 200:
            response_json = response.json()
            session['user_id'] = response_json['id']
            return {'profile': response_json}
        else:
            return {}
    return {}