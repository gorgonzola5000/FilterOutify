import base64
from flask import Flask, url_for, render_template, request, redirect, session
import urllib.parse
import secrets
import requests
import dotenv
from . import autoplaylist_utils
from .TokenExpiredError import TokenExpiredError

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
            autoplaylist_utils.get_user_id()
            return redirect(url_for('index'))
        else:
            error = urllib.parse.urlencode({'error': f'response.status_code'})
            return redirect(f'/?{error}')

@app.route('/')
def index():
    if 'authorization_token' in session:
        return redirect(url_for('playlists'))
    else:
        return redirect(url_for('about'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/playlists')
def playlists():
    try:
        autoplaylist_utils.get_playlists()
    except TokenExpiredError:
        session.clear()
        return redirect(url_for('login'))
    user_playlists = session['user_playlists']
    return render_template('playlists.html', playlists=user_playlists)

@app.route('/playlists/<playlist_id>', methods=['GET', 'POST'])
def playlist(playlist_id):
    if request.method == 'POST':
        try:
            autoplaylist_utils.create_playlist(playlist_id)
        except TokenExpiredError:
            session.clear()
            return redirect(url_for('login'))
        return redirect(url_for('playlist', playlist_id=playlist_id))
    else:
        playlist_info = session['user_playlists'][playlist_id]
        ap_playlist_id = playlist_info['ap_id']
        if playlist_info['ap_id'] == None:
            return render_template('playlist_no_ap_found.html', playlist_id=playlist_id)
        else:
            try:
                tracks = autoplaylist_utils.get_tracks(ap_playlist_id)
            except TokenExpiredError:
                session.clear()
                return redirect(url_for('login'))
            artist_set = list(set(track['artist'] for track in tracks.values()))
            artist_set.sort()
            return render_template('playlist.html', playlist_info=playlist_info, tracks=tracks, playlist_id=playlist_id, ap_playlist_id=ap_playlist_id, artists=artist_set)
        
@app.route('/playlists/<playlist_id>/filter_artist', methods=['POST'])
def filter_artist(playlist_id):
    try:
        criteria = request.form.get('artist')
        tracks_to_be_filtered_out = autoplaylist_utils.filter_tracks(playlist_id, criteria)
        autoplaylist_utils.remove_tracks_from_ap_playlist(playlist_id, tracks_to_be_filtered_out)
    except TokenExpiredError:
        session.clear()
        return redirect(url_for('login'))
    return redirect(url_for('playlist', playlist_id=playlist_id))

@app.route('/playlists/<playlist_id>/filter_track/<track_uri>', methods=['POST'])
def filter_track(playlist_id, track_uri):
    try:
        autoplaylist_utils.remove_tracks_from_ap_playlist(playlist_id, tracks_to_be_filtered_out=[track_uri])
    except TokenExpiredError:
        session.clear()
        return redirect(url_for('login'))
    return redirect(url_for('playlist', playlist_id=playlist_id))

@app.route('/playlists/<playlist_id>/reset', methods=['POST'])
def reset(playlist_id):
    try:
        autoplaylist_utils.reset_playlist(playlist_id)
    except TokenExpiredError:
        session.clear()
        return redirect(url_for('login'))
    return redirect(url_for('playlist', playlist_id=playlist_id))
    
if __name__ == '__main__':
    app.run()