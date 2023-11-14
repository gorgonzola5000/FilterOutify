import base64
from flask import Flask, url_for, render_template, request, redirect, session
import urllib.parse
import secrets
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.debug = True

client_id = 'ffb1d8d326f248fb9e5ebce160bb77b7'
client_secret = '9ad69e31226141348c25d56ad4d25aa5'
redirect_uri = 'http://localhost:5000/callback'

@app.route('/')
def index(name=None):
    return render_template('index.html', name=name)

@app.route("/<name>")
def hello(name):
    return render_template('index.html', name=name)

# @app.route(url_for(url_for('static', filename='style.css')))
# def style():
#     return 'Style Page'

@app.route('/login') # request user authorization
def login():
    state = secrets.token_hex(16)
    scope = 'user-read-private user-read-email'

    params = urllib.parse.urlencode({
        'response_type': 'code',
        'client_id': client_id,
        'scope': scope,
        'redirect_uri': redirect_uri,
        'state': state
    })

    return redirect(f'https://accounts.spotify.com/authorize?{params}')

@app.route('/callback')
def callback():
    auth_token = request.args.get('code', default=None)

    # Prepare the headers
    client_credentials = f"{client_id}:{client_secret}"
    client_credentials_b64 = base64.b64encode(client_credentials.encode()).decode()
    headers = {
        'Authorization': f'Basic {client_credentials_b64}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Prepare the data
    data = {
        'grant_type': 'authorization_code',
        'code': auth_token,
        'redirect_uri': redirect_uri
    }

    # Send the POST request
    response_json = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data).json()
    access_token = response_json['access_token']

    # Store the access token in the session
    session['access_token'] = access_token

    return render_template('index.html')