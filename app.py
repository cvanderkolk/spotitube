import functools
import json
import os
import random
import time
from datetime import datetime

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import flask
import google.oauth2.credentials
import google_auth
import youtube

import googleapiclient.discovery
from authlib.client import OAuth2Session
from flask import Flask, render_template, request, redirect
# from flask_sqlalchemy import SQLAlchemy
from pyyoutube import Api

app = flask.Flask(__name__)
app.secret_key = os.environ.get("FN_FLASK_SECRET_KEY", default=False)

app.register_blueprint(google_auth.app)
app.register_blueprint(youtube.app)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
# db = SQLAlchemy(app)

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
youtube_api = Api(api_key=YOUTUBE_API_KEY)
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(SPOTIFY_CLIENT_ID,SPOTIFY_CLIENT_SECRET))

# test_playlist_uri = 'spotify:playlist:0FGCDjzPQA0TgzEvT9cTFC'
# zack_playlist_uri = 'spotify:playlist:3AvzARrfmI3EiSi2PBTTjq'



def get_spotify_playlist(playlist_uri):
    playlist_items = spotify.playlist_items(playlist_uri)
    playlist = spotify.playlist(playlist_uri, fields='name,description')
    name = playlist.get('name')
    description = playlist.get('description')
    songs = []
    ## TODO: paginate thru so we get ALL songs goddamnit
    for track in playlist_items['items']:
       song_name = track['track']['name']
       artists = track['track']['artists']
       artist_names = ', '.join([artist['name'] for artist in artists])
       songs.append('{} {}'.format(artist_names, song_name))
    
    return (songs, name, description)

def search_youtube_for_song(query):
    search_result = youtube_api.search_by_keywords(q=query, search_type=["video"], count=1, limit=1).to_dict()
    # if there are results, return the first one
    if len(search_result.get('items')) > 0:
        return search_result['items'][0]
    else:
        return None

def add_songs_to_playlist(songs, youtube_playlist_id):
    for song in songs:
        youtube_video = search_youtube_for_song(song)
        if youtube_video:
            video_id = youtube_video['id']['videoId']
            response = youtube.add_video_to_playlist(video_id, youtube_playlist_id)
            # let's wait a moment so we don't get rate limited
            print('Added {} to your playlist!'.format(response['snippet']['title']))
            time.sleep(1)
        else:
            print('No video found for {}. \n Video info: {}'.format(song, youtube_video))

# max of 100, this does not yet paginate because we are cheap
def main(spotify_playlist_id, youtube_playlist_id=None):
    songs, name, description = get_spotify_playlist(spotify_playlist_id)
    now = datetime.now()
    # set some defaults if not provided
    if not name:
        name = 'SpotifyToYoutube Playlist {}'.format(now.strftime('%m/%d/%Y'))
    if not description:
        description = ''
    description += '\n Generated by SpotifyToYoutube on {}'.format(now.strftime('%m/%d/%Y, %H:%M:%S'))
    if not youtube_playlist_id:
        youtube_playlist = create_youtube_playlist(title=name, description=description)
        youtube_playlist_id = youtube_playlist['id']
    
    add_songs_to_playlist(songs, youtube_playlist_id)

@app.route('/')
def index():
    if google_auth.is_logged_in():
        user_info = google_auth.get_user_info()
        return render_template('index.html',  user_info=google_auth.get_user_info())

    return 'You are not currently logged in.'

from flask import request
@app.route('/dothing', methods=['POST'])
def do_thing():
    playlist_uri = request.form['playlist_uri']
    songs, name, description = get_spotify_playlist(playlist_uri)
    data = {
        'playlist_uri': playlist_uri,
        'songs': songs,
        'name': name,
        'description': description,
    }
    return render_template('songs.html', data=data)

@app.route('/makePlaylist', methods=['POST'])
def make_playlist():
    playlist_uri = request.form['playlist_uri']
    songs, name, description = get_spotify_playlist(playlist_uri)

    if not name:
        name = 'SpotifyToYoutube Playlist {}'.format(now.strftime('%m/%d/%Y'))
    if not description:
        description = ''
    description += '\n Generated by SpotifyToYoutube on {}'.format(now.strftime('%m/%d/%Y, %H:%M:%S'))
    # youtube_playlist = youtube.create_playlist(title=name, description=description)
    youtube_playlist = { 'id': 'PLR0TUXxwTRCoEU_67jo1IENOav5kIj45p' }

    add_songs_to_playlist(songs[5:10], youtube_playlist['id'])
    print('doing the thing')
    return redirect('https://www.youtube.com/playlist?list={}'.format(youtube_playlist['id']))