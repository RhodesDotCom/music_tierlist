import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from pprint import pprint as pp
import requests
from PIL import Image
from io import BytesIO
import re
import os
import argparse
import sys
from jinja2 import Environment, FileSystemLoader
import webbrowser


INVALID = ['<','>',':','"','/','\\','|','?','*']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-pid', '--playlistid', help='playlist id')
    parser.add_argument('-url', '--playlisturl', help='playlist url')
    parser.add_argument('-c', '--clientid', help='client id for sspotify API')
    parser.add_argument('-s', '--secret', help='secret key for spotify API')
    args = parser.parse_args()

    if args.clientid:
        client_id = args.clientid
    else:
        print('''missing client id for Spotify API. 
              Set up endpoint from here to get 
              client ID and secret key: https://developer.spotify.com/dashboard''')
        sys.exit(1)
    if args.secret:
        secret = args.secret
    else:
        print('''missing secret key for Spotify API. 
              Set up endpoint from here to get 
              client ID and secret key: https://developer.spotify.com/dashboard''')
        sys.exit(1)
    
    if args.playlisturl:
        playlist_id = get_uri_from_url(args.playlisturl)
    else:
        playlist_id = args.playlistid

    if not playlist_id:
        print('Invalid playlist URL or URI')
        sys.exit(1)

    try:
        sp = connect(client_id, secret)
        playlist_name = sp.playlist(playlist_id)['name']
    except Exception as e:
        print(e)
        sys.exit(1)

    foldername = re.sub(r'[^\w\-\.]', '_', playlist_name.lower())
    if not os.path.exists(foldername):
        try:
            os.makedirs(foldername)
        except OSError as e:
            print(e)
            sys.exit(1)
    
    artwork_from_playlist(sp, playlist_id, foldername)
    tierlist = create_HTML(playlist_name, foldername)
    webbrowser.open_new(tierlist)


def connect(client_id, secret):

    client_credentials_manager = SpotifyClientCredentials(
        client_id=client_id, client_secret=secret)
    sp = spotipy.Spotify(
        client_credentials_manager=client_credentials_manager)
    return sp


def get_uri_from_url(playlist_url):
    match = re.search(r'/([^/]+)\?', playlist_url)
    if match:
        playlist_uri = match.group(1)
        return playlist_uri
    else:
        return None
    

def artwork_from_playlist(sp, playlist_id, folder):
    playlist = sp.playlist(playlist_id)
    tracks = playlist['tracks']['items']

    artwork = set()
    i, length = 1, len(tracks)
    for track in tracks:
        print(f'Generating artwork: {i}/{length}', end='\r', flush=True)
        i+=1

        artist_name = ''
        for artist in track['track']['artists']:
            artist_name += ',' + artist['name'] if artist_name else artist['name']

        track_name = (track['track']['name'])
        track_name += ' - ' + artist_name
        for chr in INVALID:
            track_name = track_name.replace(chr,'')

        url = (track['track']['album']['images'][0]['url'])
        
        if url not in artwork:
            artwork.add(url)
            try:
                imagename = re.sub(r'[^\w\-\.]', '_', track_name)

                response = requests.get(url)
                with Image.open(BytesIO(response.content)) as im:
                    im.save(f'{folder}/{imagename}.png')
            except Exception as e:
                print(e)
                sys.exit(1)


def artwork_from_song(song_id, sp):
    song = sp.track(song_id)
    
    artist_name = ''
    for artist in song['artists']:
        artist_name += ',' + artist['name'] if artist_name else artist['name']
    track_name = (song['name'])
    track_name += ' - ' + artist_name

    url = song['album']['images'][0]['url']
    response = requests.get(url)
    with Image.open(BytesIO(response.content)) as im:
        im.save(f'album_artwork/{track_name}.png')


def create_HTML(playlist_name, foldername):
    filename = playlist_name.replace(' ','_') + '_Tier_List.html'
    print(f'generating tier list: {filename}')
    
    images = os.listdir(foldername)
    environment = Environment(loader=FileSystemLoader(''))
    template  = environment.get_template('tier_list.html')

    html = template.render(playlist_name=playlist_name, folder=foldername, images=images)
    with open(filename, 'w', encoding="utf-8") as f:
        f.write(html)
    
    return filename


if __name__ == "__main__":
    main()