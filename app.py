import functools
import json
import logging
import os
import random
import sys
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
from pyyoutube import Api

app = flask.Flask(__name__)
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)
app.secret_key = os.environ.get("FN_FLASK_SECRET_KEY", default=False)

app.register_blueprint(google_auth.app)
app.register_blueprint(youtube.app)

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
youtube_api = Api(api_key=YOUTUBE_API_KEY)
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(SPOTIFY_CLIENT_ID,SPOTIFY_CLIENT_SECRET))

def get_spotify_playlist(playlist_uri):
    playlist_items = spotify.playlist_items(playlist_uri)
    playlist = spotify.playlist(playlist_uri, fields='name,description,uri,images')
    songs = []
    ## TODO: paginate thru so we get ALL songs goddamnit
    for track in playlist_items['items']:
       song_name = track['track']['name']
       artists = track['track']['artists']
       artist_names = ', '.join([artist['name'] for artist in artists])
       songs.append('{} {}'.format(artist_names, song_name))
    
    return (songs, playlist)

def search_youtube_for_song(query):
    # using a diff api because this API key use uses less quota :D
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
            if response:
                print('Added {} to your playlist!'.format(response['snippet']['title']))
            else:
                print('Something went wrong, not adding video')
            time.sleep(1)
        else:
            print('No video found for {}. \n Video info: {}'.format(song, youtube_video))

@app.route('/')
def index():
    if google_auth.is_logged_in():
        user_info = google_auth.get_user_info()
        playlists = youtube.get_playlists()['items']
        return render_template('index.html',  user_info=user_info, playlists=playlists)
    else:
        return render_template('login.html')
    return 'You are not currently logged in.'

from flask import request
@app.route('/dothing', methods=['POST'])
def do_thing():
    playlist_uri = request.form['spotify_playlist_uri']
    youtube_playlist_id = request.form.get('youtube_playlist')
    songs, playlist = get_spotify_playlist(playlist_uri)

    if youtube_playlist_id:
        youtube_playlist = youtube.get_playlists(youtube_playlist_id)['items'][0]
    else:
        youtube_playlist = None

    return render_template(
        'songs.html',
        songs=songs, 
        playlist=playlist,
        youtube_playlist=youtube_playlist,
    )

@app.route('/makePlaylist', methods=['POST'])
def make_playlist():
    playlist_uri = request.form['spotify_playlist_uri']
    youtube_playlist_id = request.form.get('youtube_playlist_id')

    songs, playlist = get_spotify_playlist(playlist_uri)
    now = datetime.now()
    name = playlist.get('name', 'SpotifyToYoutube Playlist {}'.format(now.strftime('%m/%d/%Y')))
    description = playlist.get('description', '')
    description += '\n Generated by SpotifyToYoutube on {}'.format(now.strftime('%m/%d/%Y, %H:%M:%S'))
    print(request.form)

    if youtube_playlist_id:
        youtube_playlist = youtube.get_playlists(youtube_playlist_id)['items'][0]
    else:
        youtube_playlist = youtube.create_playlist(title=name, description=description)
    
    add_songs_to_playlist(songs[0:5], youtube_playlist['id'])
    return redirect('https://www.youtube.com/playlist?list={}'.format(youtube_playlist['id']))


# TODO: next features
# 1) list youtube playlists and add checkboxes so a user can select an existing playlist to add to
# 2) make it prettier
# 3) spotify auth, list YOUR public playlists