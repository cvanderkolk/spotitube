import flask

import googleapiclient.discovery
from google_auth import build_credentials, get_user_info

app = flask.Blueprint('youtube', __name__)

def build_youtube_api_v3():
    credentials = build_credentials()
    return googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)

def get_playlists(playlist_id=None):
    ## TODO: Paginate
    youtube = build_youtube_api_v3()
    if playlist_id:
        return youtube.playlists().list(part='snippet', id=playlist_id).execute()
    else:
        return youtube.playlists().list(part='snippet', mine=True, maxResults=50).execute()

def add_video_to_playlist(video_id, playlist_id):
    youtube = build_youtube_api_v3()
    body = {
        "snippet": {
            "playlistId": playlist_id,
            "position": 0,
            "resourceId": {
                "kind": 'youtube#video',
                "videoId": video_id,
            }
        }
    }
    return youtube.playlistItems().insert(part='snippet', body=body).execute()

def create_playlist(title, description, public=False):
    youtube = build_youtube_api_v3()
    body = {
        'snippet': {
            'title': title,
            'description': description,
            # 'tags': tags or [],
            'defaultLanguage': 'en',
        },
        'status': {
            'privacyStatus': 'private' if not public else 'public',
        }
    }
    return youtube.playlists().insert(part='snippet, status', body=body).execute()