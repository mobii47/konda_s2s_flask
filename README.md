# KUDO STS - API AND APP

This is the FLASK S2S POC for speech-to-speech translation. 

The API provide a progammatical way to access the S2S service. The APP also integrates FE, audio capturing, etc. and aims at R&D testing and demos.

This API contains three nodes:

- /parse: to continuously send transcription in Json and receive translated short sentences to convert to speech
- /startSession: to initialize a session with a unique ID
- /stopSession: to flush the session

The APP also creates a log file with the ASR response and status to be used with the CLI available in ASR-Segmenter to test the Segmenter.

The APP has three views:

- Sender/Consolle: uses AZURE ASR to transcribe the audio input (mic or other input audio), then it processes the stream in realtime and sends the results to the Receiver via websockets. Sender is a simplified view. Consolle has R&D settings exposed.
- Receiver: it receives the translation from the the S2S-App backend, requests text-to-speech from Azure

# Local installation

cd this-app-folder
pipenv install

Note: Requires python 3.9 for compatibility reasons with eventlet 

# How to run locally
- cd into app
- python app.py
- app is available in Browser http://127.0.0.1:5000
- click on Connect and start speaking in the mic (allow permissions)

Note: as default, the APP will use the Segment Segmenter deployed on the Web. If you want to use a local version of the Sentence Segmenter, run it in a new Terminal following the instructions indicated in its respective repo. Adapt Endpoint in app.py (search for #API endpoint) to local. 

# How to run on Web
- open Simple Sender https://www.s2s.meetkudo.com/
- open Advanced Sender (with testing options): https://www.s2s.meetkudo.com/consolle
- open Receiver https://www.s2s.meetkudo.com/receiver in a Chrome browser, wear headset or use a different computer to receive the interpretation

# Deployment on Heroku with git

heroku login
git add . 
git commit -am "make it better" 
git push heroku master

# I/O API

As input it accepts a JSON payload:
```
{'asr': 'transcription text', 'status': 'azure_flag 
temporary/final/silence', 'room': 'session_id', 'sourceLanguage': 'the 
source language', 'targetTanguages': 'the target languages' }
```

It responds with a JSON payload:
```
{'asr': 'original transcription text', 'segment': 
'{'en' : 'translation in english', 'fr': 'translation in french'}', 
'voiceSpeed' : '{'en' : '10', 'fr': '20'}, 'voiceStyle': 'this is the style of the voice for TTS'}
```

# Session initialisation

To initialize a session, call 

```
/api/startSession/<sessionId>
```

where <sessionId> is your unique session ID

# API Info

- initialize a session with ```/startSession<sessionId>```  This is a GET request 
- send payload to ```/parse``` This is POST request. Note that the ID needs to be sent in any call, see dedicated parameter in payload. This allws the API to be stateless

Note: ```test/parseAPItest.pl``` tests the API simulating a new session and sending continuously AZURE transcripts to the API.

 
