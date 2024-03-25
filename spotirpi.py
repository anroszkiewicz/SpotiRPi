import spotipy #python library for the Spotify web API
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
import sqlite3
import speech_recognition as sr #library for speech recognition
import bluetooth
import os

SPOTIPY_CLIENT_ID = #client ID from Spotify for Developers website
SPOTIPY_CLIENT_SECRET = #client secret from Spotify for Developers website
SPOTIPY_REDIRECT_URI = 'http://localhost:3000'
RPI_ID = #insert your device id. You can get it by making a call to the Spotify web API

conn = sqlite3.connect('baza.db') #establish database connection
playing = 0

def createdatabase():
    cursor.execute('''CREATE TABLE IF NOT EXISTS utwory
                    (id STRING PRIMARY KEY,
                    title STRING,
                    artist STRING,
                    plays INTEGER)''')
    conn.commit()

def updatedatabase(uri,title,artist):
    select = cursor.execute("SELECT * FROM utwory WHERE id=?",[uri])

    if select.fetchone() == None: #if song has never been played, insert it into database
        cursor.execute("INSERT INTO utwory VALUES(?,?,?,?)",(uri,title,artist,1))
        conn.commit()
    else: #if song has been played before, update the number of plays
        cursor.execute("UPDATE utwory SET plays = plays + 1 WHERE id=?",[uri])
        conn.commit()

def favouritesong(): #find song that has the most plays, update it and return spotify uri
    cursor.execute("UPDATE utwory SET plays = plays + 1 WHERE plays=(SELECT MAX(plays) FROM utwory)")
    conn.commit()
    select = cursor.execute("SELECT id FROM utwory WHERE plays=(SELECT MAX(plays) FROM utwory)").fetchone()
    return str(select[0])

def listen(language):
    r = sr.Recognizer() #set up Speech Recognizer class
    mic = sr.Microphone() #select microphone
    with mic as source:
        audio = r.listen(source, phrase_time_limit=5) #start listening
    recognize = r.recognize_google(audio, language=language) #use Google's speech recognition API
    return recognize

if __name__ == "__main__":

    #database connection
    cursor = conn.cursor()
    createdatabase()

    #spotify connection
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                                   client_secret=SPOTIPY_CLIENT_SECRET,
                                                   redirect_uri=SPOTIPY_REDIRECT_URI,
                                                   open_browser=False,
                                                   scope="user-read-playback-state user-modify-playback-state"))


    #bluetooth connection
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", bluetooth.PORT_ANY))
    server_sock.listen(1)

    port = server_sock.getsockname()[1]

    uuid = "00001101-0000-1000-8000-00805F9B34FB"

    bluetooth.advertise_service(server_sock, "SampleServer", service_id=uuid,
                                service_classes=[uuid, bluetooth.SERIAL_PORT_CLASS],
                                profiles=[bluetooth.SERIAL_PORT_PROFILE])

    while True:
        conn = sqlite3.connect('baza.db') #establish database connection
        cursor = conn.cursor()

        print("Waiting for connection on RFCOMM channel", port)
        client_sock, client_info = server_sock.accept()
        print("Accepted connection from", client_info)

        try:
            while True:
                data = client_sock.recv(1024)
                if data==b'L': #start listening
                    print("started listening...")
                    os.system("aplay start.wav")
                    while True:
                        try:
                            recognize = listen("en-US")
                            print(recognize)
                            break
                        except sr.UnknownValueError:
                            os.system("aplay err.wav")

                    if "favorite" in recognize: #select favourite song from database
                        uri = favouritesong()
                        print(uri)
                    else:
                        result = sp.search(recognize, type='track', limit=1) #search for tracks on Spotify
                        uri = result['tracks']['items'][0]['uri'] #Spotify track id
                        title = result['tracks']['items'][0]['name']
                        artist = result['tracks']['items'][0]['artists'][0]['name']

                        updatedatabase(uri,title,artist)
                    sp.start_playback(device_id=RPI_ID,uris=[uri]) #start playing selected track
                    playing = 1

                if data==b'F': #start listening
                    print("started listening...")
                    os.system("aplay startpl.wav")
                    while True:
                        try:
                            recognize = listen("pl")
                            print(recognize)
                            break
                        except sr.UnknownValueError:
                            os.system("aplay errpl.wav")

                    if "ulubion" in recognize: #select favourite song from database
                        uri = favouritesong()
                        print(uri)
                    else:
                        result = sp.search(recognize, type='track', limit=1) #search for tracks on Spotify
                        uri = result['tracks']['items'][0]['uri'] #Spotify track id
                        title = result['tracks']['items'][0]['name']
                        artist = result['tracks']['items'][0]['artists'][0]['name']

                        updatedatabase(uri,title,artist)
                    sp.start_playback(device_id=RPI_ID,uris=[uri]) #start playing selected track
                    playing = 1

                if data==b'P': #volume up
                    currentvolume = sp.current_playback()['device']['volume_percent']
                    if currentvolume <= 90:
                        currentvolume += 10
                        sp.volume(currentvolume)
                if data==b'M': #volume down
                    currentvolume = sp.current_playback()['device']['volume_percent']
                    if currentvolume >= 0:
                        currentvolume -= 10
                        sp.volume(currentvolume)
                if data==b'S': #stop/resume playing
                    if playing == 1:
                        sp.pause_playback(device_id=RPI_ID)
                        playing = 0
                    elif playing == 0:
                        sp.start_playback(device_id=RPI_ID)
                        playing = 1
        except OSError as e: 
            print(e)
            print("Error")
            pass

        print("Disconnected.")

        conn.close()

        client_sock.close()

    server_sock.close()

