import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, redirect, session, request, render_template
from flask_session import Session
import time
import json 
from dotenv import load_dotenv
import os
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv("secret_key")
app.config["SESSION_TYPE"] = "filesystem"  # Stores sessions on the server
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_KEY_PREFIX"] = "spotify_"  # Prevents key conflicts
app.config["SESSION_FILE_DIR"] = os.path.abspath("/home/manfred/Documents/SPOTIFY_WEBSITE/flask_sessions")  # Where session files are stored
Session(app)



# Set your Spotify credentials and redirect URI
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

# Define Spotify OAuth settings and scopes
SCOPE = 'user-library-read playlist-read-private user-read-playback-state streaming user-top-read user-modify-playback-state'
#CACHE = '.spotipyoauthcache'

sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET,
                            redirect_uri=SPOTIPY_REDIRECT_URI, scope=SCOPE)
    
#@app.route('/xd')
def expired():
    #print("Inside expired function")
    
    user_id = session.get("spotify_username")
    token_info = session.get(f"token_info_{user_id}")
    print(token_info)

    if not token_info:
        return None
    
    #print("shdd")

    #print(token_info['expires_at'])
    #print(int(time.time()))
    
    # if token_info['expires_at'] - time.time() < 60:
    #     print("access token expired... requesting new one")
    #     token_info = sp_oauth.refresh_access_token(refresh_token=token_info['refresh_token'])
    #     session['token_info'] = token_info
    token = sp_oauth.validate_token(token_info)

    return spotipy.Spotify(auth=token_info)

def save_json_to_file(data, filename='user_activity.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)  
        

@app.route('/')
def home():
    #print(f"something{app.config['SESSION_FILE_DIR']}")
    return render_template('index.html')


@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code, as_dict=False,check_cache=False)

    

    sp = spotipy.Spotify(auth=token_info)
    user_info = sp.current_user()
    print(token_info)
    print(user_info)
    user_id = user_info["id"]
    
    session['spotify_username'] = user_id
    session[f"token_info_{user_id}"] = token_info
    
    return redirect('/')

@app.route('/playlists')
def get_playlists():
    sp = expired()
    if not sp:
        return redirect('/login')
    playlists = sp.current_user_playlists()
    save_json_to_file(playlists,"playlists.json")
    pl = playlists['items']

    return render_template("Playlists.html", playlists=pl)

@app.route('/get_activity')
def get_activity():
    sp = expired()
    if not sp:
        return redirect('/login')
    useractivity = sp.current_user_playing_track()
    save_json_to_file(useractivity, 'user_activity.json')
    if useractivity and useractivity.get('item'):
        track = useractivity['item']
    else: 
        #print("nothing rn")
        return None 
    #print("something")
    return track

@app.route('/activity')
def currently_playing(): 
    sp = expired()
    if not sp:
        return redirect('/login')
    return render_template('currentlyplaying.html')

@app.route('/skip')
def skip_track():
    sp = expired()
    sp.next_track()
    
    return '', 204

@app.route('/back')
def back():
    sp = expired()
    sp.previous_track()
    
    return '', 204

@app.route('/top_songs')
def top_songs(time_range="medium_term"):
    sp = expired()
    if not sp:
        return redirect('/login')
    user = sp.current_user()
    josn = sp.current_user_top_tracks(time_range='short_term')
    save_json_to_file(josn, "toptracks.json")
    songs = josn['items']
    ##exit()

    return render_template('Top_Songs.html', songs = songs, user = user)

@app.route('/top_artists')
def top_artists():
    sp = expired()
    if not sp:
        return redirect('/login')
    josn = sp.current_user_top_artists(time_range='short_term')
    save_json_to_file(josn, "toptracks.json")

    artists = josn['items']
    return render_template('Top_Artists.html', artists = artists)

@app.route('/genre')
def genre():
    sp = expired()
    if not sp:
        return redirect('/login')
    josn = sp.current_user_top_artists(time_range='short_term')
    genre = josn['items']
    save_json_to_file(genre, "genres.json")
    return render_template('Top_Genres.html', genres= genre)

@app.route('/queue')
def queue():
    return render_template('queue.html')

@app.route('/songsearch', methods=['GET'])
def searchsong():
    sp = expired()
    if not sp:
        return redirect('/login')
    lookingfor = request.args.get('song')
    #print(lookingfor)
    josn = sp.search(q=lookingfor)
    save_json_to_file(josn, 'queuestuff.json')
    songname = josn['tracks']['items'][0]['name']
    songid = josn['tracks']['items'][0]['id']
    print(songname, songid)

    return songid
    
@app.route('/songqueue', methods=['GET'])
def songqueue():
    sp = expired()
    if not sp:
        return redirect('/login')
    id = request.args.get('id')
    print(id)
    response = sp.add_to_queue(uri=id)

    if response:
        return '', response['error']['status']

    return '', 204

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8080, debug=True)
