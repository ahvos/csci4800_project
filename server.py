#import libraries
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect, jsonify, render_template

from chatbot import track_ids


#create new app with flask
app = Flask(__name__)
app.config['SESSION_COOKIE_NAME'] = 'spotify cookie'
app.secret_key = 'eowkfo2435sfds302'
TOKEN_INFO = 'token_info'


#login page
@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)


#redirect
@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('generate_playlist', external=True))


#create playlist
@app.route('/generate_playlist')
def generate_playlist():
    try:
        token_info = get_token()
    except:
        print('user not logged in')
        return redirect('/')
        
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_id = sp.current_user()['id']
    current_playlists = sp.current_user_playlists()['items']
    generated_playlist_id = None
    
    #create new playlist to add generated songs
    for playlist in current_playlists:
        if playlist and 'name' in playlist:
            if playlist['name'] == 'Generated Playlist':
                generated_playlist_id = playlist['id']
        else:
            print('invalid playlist object:', playlist)

    if not generated_playlist_id:
        new_playlist = sp.user_playlist_create(user_id, 'Generated Playlist', True)
        generated_playlist_id = new_playlist['id']

    #load in track_ids of generated songs
    track_ids_str = request.args.get('track_ids', '')
    track_ids_list = track_ids_str.split(',')

    #add generated songs into new playlist
    song_uris = []
    for track_id in track_ids_list:
        try:
            track_details = sp.track(track_id)
            song_uris.append(track_details['uri'])
        except spotipy.exceptions.SpotifyException as e:
            print(f"error fetching track details for {track_id}: {e}")

    sp.user_playlist_add_tracks(user_id, generated_playlist_id, song_uris, None)
    return('success!')



#create spotify oauth
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = '642956e848744e8e9bd0854284bf25b4',
        client_secret = 'cf51914572dc43ef85da76e3d1fbf6d3',
        redirect_uri = url_for('redirect_page', _external=True),
        scope = 'user-library-read playlist-modify-public playlist-modify-private'
    )

#generate new token for each session
def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        redirect(url_for('login', _external=False))
    
    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if(is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])

    return token_info


app.run(debug=True)
