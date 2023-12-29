## How to run

#### Create a .env file
It should look like this:
```
CLIENT_ID=<client_id_from_your_Spotify_Web_API_project>
CLIENT_SECRET=<client_secret_from_your_Spotify_Web_API_project>
SECRET_KEY=<your_secret_key_just_random_characters>
REDIRECT_URI=http://localhost:5000/callback
```
#### Run the docker container
```
$ docker run --env-file /path/to/your/.env/file -p 5000:80 spotify-autoplaylist
```

If you decide to change the port, make sure to change it in Spotify Web API project settings, .env file and docker run command