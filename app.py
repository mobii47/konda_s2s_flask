import json
import os
import flask
from dotenv import load_dotenv
from flask import (
    Response,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for
    )

from flask_caching import Cache
from flask_socketio import SocketIO, emit, join_room, leave_room

from constants import TLS_LIST, USE_REWRITING, DEFAULT_VOICES_SPEED, LANG_MAP #SL
from decorators import roles_required
from helpers import id_generator, login_authentication, print_changelog, initialize_segmenterAPI
from orchestrator import data_orchestrator

load_dotenv()
SECRET_KEY = os.environ.get("SECRET_KEY")
app = flask.Flask(__name__)
app.secret_key = SECRET_KEY
socketio = SocketIO(app)
cache = Cache()
cache.init_app(app=app, config={
    "CACHE_TYPE": "simple",
    "CACHE_DEFAULT_TIMEOUT": 36000
    })


###############################################
# SERVICE API TO CALL FOR real-time S2S
###############################################


@app.route("/api/startSession/<sessionId>")
def startSession(sessionId):
    # initiate a new Segmenter session
    initialize_segmenterAPI(sessionId)
    # initialize cache
    initialize_cache_session(sessionId)
    return "Session initialized"


@app.route("/api/stopSession/<sessionId>")
def stopSession(sessionId):
    '''Flush the cache and stop the session'''
    print("Stopping session: " + str(sessionId))
    return "Session stopped"


@app.route("/api/parse", methods=["POST"])
def parse():
    """Main call coming from the client."""
    data = request.get_json()
    sourceLanguage = data["sourceLanguage"]
    targetLanguages = data["targetLanguages"]

    # Add default parameters
    data["rewriting"] = USE_REWRITING

    # TO DO: add a check that the session corresponding to this call exists
    response = data_orchestrator(data, cache, sourceLanguage, targetLanguages)

    json_object = json.dumps(response, indent=4)
    return json_object


def initialize_cache_session(sessionId):
    """Initialize cache session."""

    session_settings = {
        "asr_callbacks": 0,
        "segment_nr": 0,
        "voice_speeds": DEFAULT_VOICES_SPEED,
        "prev_timestamp": 0,
        "prev_chars_per_seconds": []
    }
    cache.set(sessionId, session_settings)

###############################################
# END SERVICE API
###############################################


##############################################################################################
# THIS ARE THE ROUTS FOR THE USER FACING POC - TO BE DISCARDED FOR THE SERVICE API
# !!! All this is not needed for the s2s service
##############################################################################################
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        form_data = request.form.to_dict()
        email = form_data.get("email", None)
        password = form_data.get("password", None)
        if email and password:
            app.logger.info(f"User email: {email}")
            response = login_authentication(email, password)
            if response["status"] in ["user unkown", "not allowed"]:
                flash("Invalid username or password")
                return redirect(url_for("login"))
            else:
                session.clear()
                session["role"] = response["role"]
                return redirect(url_for(session["role"]))
        else:
            flash("Empty username or password")
            return redirect(url_for("login"))
    return render_template("login.html", title="Login")


# this is the default SENDER view. Opening this page generates a session ID, initializes the Segmenter API with the session ID and creates the view
@app.route("/sender", methods=["GET", "POST"])
@roles_required("sender")
def sender():
    # create a random session ID
    sessionId = id_generator()
    return render_template("consolle.html", sessionId=sessionId, languages=TLS_LIST)


# this is the advanced SENDER view (with testing options). Opening this page generates a session ID, initializes the Segmenter API with the session ID and creates the view
@app.route("/consolle", methods=["GET", "POST"])
@roles_required(["sender"])
def consolle():
    # create a random session ID
    sessionId = id_generator()
    return render_template("consolle.html", sessionId=sessionId, languages=TLS_LIST)


# this is the receiver view which will receive the translation and the interpretation
@app.route("/receiver", methods=["GET", "POST"])
def receiver():
    return render_template("receiver.html", languages=TLS_LIST)


# this route returns info on the version log
@app.route("/info")
def info():
    changelog = print_changelog()
    return Response(json.dumps(changelog), mimetype="application/json")


# this is the orchestrator which is continuously called with the transcription and metadata
@socketio.on("message")
def receive_socket(data):
    sessionID = data["room"]
    SL = LANG_MAP[data["sourceLanguage"]]
    response = data_orchestrator(data, cache, SL, TLS_LIST)

    #creating log file of session to be used with CLI
    
    asr = data["asr"]
    status = data["status"]
    f = open("session_log.txt", "a")
    f.write(f'{asr}\t{status}\n')
    f.close()

    # emitting payload to client for TTS
    print("Emitting payload to receiver")
    emit(
        "caption",
        response,
        broadcast=True,
        room=sessionID,
    )

@socketio.on("join")
def on_join(data):
    user = data["user"]
    sessionID = data["room"]
    source_language = LANG_MAP[data["sourceLanguage"]]
    # initiate a new session of API
    initialize_segmenterAPI(sessionID, source_language)
    # initialize cache
    initialize_cache_session(sessionID)
    print(f"client {user} wants to join: {sessionID}")
    join_room(sessionID)
    emit("caption", f"User {user} joint event {sessionID},", room=sessionID)


@socketio.on("leave")
def on_left(data):
    user = data["user"]
    sessionID = data["room"]
    print(f"client {user} wants to leave: {sessionID}")
    leave_room(sessionID)

    emit("caption", f"User {user} left event {sessionID},", room=sessionID)


###############################################
# END OF USER FACING POC
###############################################

if __name__ == "__main__":
    socketio.run(app, debug=True)
