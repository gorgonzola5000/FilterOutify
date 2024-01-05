## FilterOutify
It is a Docker container for filtering your public Spotify playlists.
You can filter out:
- all of the tracks of a specified artist
- specific tracks
#### Run using Docker Compose
```
version: "3.8"
services:
  filteroutify:
    image: gorgonzola5000/filteroutify
    container_name: FilterOutify
    ports:
      - 5000:80
    environment:
      - UID=1000
      - GID=1000
      - CLIENT_ID=<client_id_from_your_Spotify_Web_API_project>
      - CLIENT_SECRET=<client_secret_from_your_Spotify_Web_API_project>
      - SECRET_KEY=<your_secret_key_just_random_characters>
      - REDIRECT_URI=http://<your_server_ip_address>/callback
    restart: unless-stopped
```
#### Tips
- If you have a DNS server running, you should use the domain name pointing to the server running this app instead of hardcoding the IP address
  As <your_server_ip_address> use the domain name pointing to the machine running this app
  e.g. use your domain name "domain.example" as <your_server_ip_address>
- If you want to access this app remotely, I recommend setting up a VPN access to your home network using Wireguard or Tailscale
- If you decide to change the port, make sure to change it in Spotify Web API project settings, .env file and Docker run command or Docker Compose file
