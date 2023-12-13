import base64
from flask import Flask, url_for, render_template, request, redirect, session, jsonify
import urllib.parse
import secrets
import requests
import dotenv
import regex as re
import json

app = Flask(__name__)
app.debug = True
app.secret_key = dotenv.get_key(dotenv.find_dotenv(), 'SECRET_KEY')

client_id = dotenv.get_key(dotenv.find_dotenv(), 'CLIENT_ID')
client_secret = dotenv.get_key(dotenv.find_dotenv(), 'CLIENT_SECRET')
redirect_uri = dotenv.get_key(dotenv.find_dotenv(), 'REDIRECT_URI')

@app.context_processor
def inject_user_profile():
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

@app.route('/login')
def login():
    state = secrets.token_hex(16)
    # scope = 'user-read-private user-read-email playlist-read-collaborative playlist-modify-public playlist-modify-private'
    scope = 'user-read-private user-read-email playlist-modify-public playlist-modify-private'
    params = urllib.parse.urlencode({
        'response_type': 'code',
        'client_id': client_id,
        'scope': scope,
        'redirect_uri': redirect_uri,
        'state': state
    })
    return redirect(f'https://accounts.spotify.com/authorize?{params}')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/callback')
def callback():
    code = request.args.get('code', default=None)
    state = request.args.get('state', default=None)

    if state is None:
        error = urllib.parse.urlencode({'error': 'state_mismatch'})
        return redirect(f'/?{error}')

    else:
        client_credentials = f"{client_id}:{client_secret}"
        client_credentials_b64 = base64.b64encode(client_credentials.encode()).decode()

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {client_credentials_b64}'
        }

        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri
        }

        response = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data)
        response_json = response.json()

        if response.status_code == 200:
            # Save the authorization token in the session
            session['authorization_token'] = response_json['access_token']
            get_user_id()
            return redirect(url_for('index'))
        else:
            error = urllib.parse.urlencode({'error': f'response.status_code'})
            return redirect(f'/?{error}')

@app.route('/')
def index():
    if 'authorization_token' in session:
        return redirect(url_for('playlists'))
    else:
        return render_template('about.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/playlists')
def playlists():
    # Check if the authorization token is present in the session
    if 'authorization_token' not in session:
        return redirect(url_for('login'))
    else:
        headers = {
            'Authorization': f'Bearer {session["authorization_token"]}'
        }

        response = requests.get('https://api.spotify.com/v1/me/playlists', headers=headers)
        response_json = response.json() # get the playlists of the user

        if response.status_code == 200:
            session.setdefault('user_playlist_and_ap_playlist_ids', {})
            for item in response_json['items']:
                if item['name'].endswith(' AP'):
                    name_without_ap = item['name'].replace(' AP', '')
                    for item2 in response_json['items']:
                        if item2['name'] == name_without_ap:
                            session['user_playlist_and_ap_playlist_ids'][item2['id']] = {
                            'user_playlist_name': item2['name'],
                            'ap_playlist_id': item['id'],
                            'ap_playlist_name': item['name']
                            }
        items = response_json['items']
        for item in items: # replace playlists with AP playlists
            if item['id'] in session['user_playlist_and_ap_playlist_ids']:
                item['id'] = session['user_playlist_and_ap_playlist_ids'][item['id']]['ap_playlist_id']
        return render_template('playlists.html', playlists=response_json['items'])

        # if response.status_code == 200:
        #     response_json = response.json()
        #     session.setdefault('user_playlist_and_ap_playlist_ids', {})
        #     for item in response_json['items']:
        #         if item['public'] == True:
        #             pattern = re.compile(re.escape(item['name']) + 'AP$')
        #             found = False
        #             for second_item in response_json['items']:
        #                 if pattern.match(second_item['name']):
        #                     session['user_playlist_and_ap_playlist_ids'][item['id']] = {
        #                         'ap_playlist_id': second_item['id'],
        #                         'playlist_name': item['name']
        #                     }
        #                     found = True
        #             if not found:
        #                 # Create a new playlist
        #                 data = {
        #                     'name': f'{item["name"]} AP',
        #                     'public': False
        #                 }
        #                 response = requests.post(f'https://api.spotify.com/v1/users/{session["user_id"]}/playlists', headers=headers, data=json.dumps(data))
        #                 if response.status_code == 201:
        #                     response_json = response.json()
        #                     session['user_playlist_and_ap_playlist_ids'][item['id']] = {
        #                         'ap_playlist_id': response_json['id'],
        #                         'playlist_name': item['name']
        #                     }
        # else:
        #     pass # if the token is expired, redirect to login

@app.route('/playlists/<playlist_id>')
def playlist(playlist_id):
    if playlist_id in session['user_playlist_and_ap_playlist_ids']:
        ap_playlist_id = session['user_playlist_and_ap_playlist_ids'][playlist_id]['ap_playlist_id']
        headers = {
            'Authorization': f'Bearer {session["authorization_token"]}'
        }
        tracks_ap = requests.get(f'https://api.spotify.com/v1/playlists/{ap_playlist_id}/tracks', headers=headers)
        if tracks_ap.status_code == 200:
            tracks_ap_json = tracks_ap.json()
        tracks_user = requests.get(f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks', headers=headers)
        if tracks_user.status_code == 200:
            tracks_user_json = tracks_user.json()
        return render_template('playlist.html', tracks_ap=tracks_ap_json['items'], tracks_user=tracks_user_json['items'])
    else:
        return render_template('playlist_no_ap_found.html', user_playlist_id=playlist_id)

@app.route('/create_playlist/<user_playlist_id>', methods=['POST'])
def create_playlist(user_playlist_id):
    headers = {
    'Authorization': f'Bearer {session["authorization_token"]}',
    'Content-Type': 'application/json'
    }
    # get user playlist info
    response = requests.get(f'https://api.spotify.com/v1/users/{session["user_id"]}/playlists/{user_playlist_id}', headers=headers)
    response_json = response.json()
    user_playlist_name = response_json['name'] # extract name of user playlist

    headers = {
    'Authorization': f'Bearer {session["authorization_token"]}',
    'Content-Type': 'application/json'
    }
    data = {
        'name': f'{user_playlist_name} AP',
        'public': False
    }

    response = requests.post(f'https://api.spotify.com/v1/users/{session["user_id"]}/playlists', headers=headers, data=json.dumps(data))
    if response.status_code == 201:
        response_json = response.json()
        session['user_playlist_and_ap_playlist_ids'][user_playlist_id] = {
            'ap_playlist_id': response_json['id'],
            'playlist_name': user_playlist_name
        }
    session.modified = True
    return redirect(url_for('playlist', playlist_id=user_playlist_id))
    

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