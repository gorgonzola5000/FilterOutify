import base64
from flask import Flask, url_for, render_template, request, redirect, session, jsonify
import urllib.parse
import secrets
import requests
import dotenv
import regex as re
import json
from flaskr.autoplaylist_utils import get_playlists, get_tracks, create_playlist, get_user_id

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
    scope = 'user-read-private user-read-email playlist-modify-public playlist-modify-private playlist-read-private'
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
    get_playlists()
    user_playlists = session['user_playlists']
    return render_template('playlists.html', playlists=user_playlists)

@app.route('/playlists/<playlist_id>', methods=['GET', 'POST'])
def playlist(playlist_id):
    playlist_info = session['user_playlists'][playlist_id]

    if request.method == 'POST':
        create_playlist(playlist_id)
        return redirect(url_for('playlist', playlist_id=playlist_id))
    else:
        if playlist_info['ap_id'] == None:
            return render_template('playlist_no_ap_found.html', playlist_id=playlist_id)
        else:
            tracks = get_tracks(playlist_id)
            return render_template('playlist.html', tracks=tracks)