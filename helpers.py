import random
import json
import string
from constants import (
    DURATION_COEFFICIENTS,
    DEFAULT_VOICES_SPEED,
    LANG_MAP
    )
import os
import uuid
import deepl
import requests
import openai

from dotenv import load_dotenv

load_dotenv()
SEGMENTERAPI = "http://127.0.0.1:8000"#os.environ.get("SEGMENTERAPI")
TRANSLATE_API_URL = os.environ.get("TRANSLATE_API_URL")
TRANSLATE_API_KEY = os.environ.get("TRANSLATE_API_KEY")
TRANSLATE_API_REGION = os.environ.get("TRANSLATE_API_REGION")
PARAPHRASE_API_URL = os.environ.get("PARAPHRASE_API_URL")
PARAPHRASE_API_AUTHORIZATION = os.environ.get("PARAPHRASE_API_AUTHORIZATION")
TRANSLATE_DEEPL_API_KEY = os.environ.get("TRANSLATE_DEEPL_API_KEY")
OPENAI_KEY = os.environ.get("OPENAI_KEY")

openai.api_key = OPENAI_KEY

def login_authentication(email, password):
    """
    simple hardcoded loging to avoid undesired eyes
    """

    # hardcoded login for quick check
    if email == "admin@gmail.com" and password == "kudoadmin2022#":
        response = {
            "status": "allowed",
            "role": "sender",
        }
        return response
    else:
        response = {
            "status": "user unkown",
            "role": "sender",
        }
        return response


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    """
    this generates our session ID
    """
    return "".join(random.choice(chars) for _ in range(size))


def calculate_voice_speeds(segment_translation,
                           target_languages,
                           src_segment_duration,
                           voice_speeds):
    """
    Parameters
    ----------
    segment_translation : dict
        Dictionary of translations.
    target_languages : dict
        Dictionary  of language codes.
    src_segment_duration : float
        Float representing duration of source segment in milliseconds.
    voice_speeds : dict
        Dictionary of voice speeds.

    Returns
    -------
    voice_speeds : dict
        Updated dictionary of voice speeds.

    """
    for language_code in target_languages:
        # Get current voice speed
        voice_speed = voice_speeds[language_code]
        
        # Calculate target segment duration
        translation = segment_translation[language_code]
        duration_coefficient = DURATION_COEFFICIENTS[language_code]
        tgt_segment_duration = round(
            (len(translation) * duration_coefficient  * 1000), 2) + 1000
        
        # If target segment is longer than source segment
        if src_segment_duration < tgt_segment_duration:
            # increase voice speed by 40%
            voice_speed = round(int(voice_speed * 1.4))
            # set a maximum voice speed
            voice_speed = min(voice_speed, 40)
        else:
            # Reset voice speed
            voice_speed = DEFAULT_VOICES_SPEED[language_code]
        # Update voice speeds
        voice_speeds[language_code] = voice_speed

    return voice_speeds


def translateJA(text, sourceLanguage, targetLanguages):
    """
    this calls the translation API for JA (now DEEPL)
    """
    print("Calling Translation API (deepl)")
    translator = deepl.Translator(TRANSLATE_DEEPL_API_KEY)
    
    #please specify source too
    result = translator.translate_text(text, target_lang="JA")
    result_string = str(result)

    return result_string


def translate(text, sourceLanguage, targetLanguages):
    """
    this calls the translation API (now AZURE)
    """
    print("Calling Translation API (azure")

    # Azure endpoint
    endpoint = TRANSLATE_API_URL
    subscription_key = TRANSLATE_API_KEY
    region = TRANSLATE_API_REGION

    # constructing language parameters for call
    params = "&from=" + sourceLanguage
    for tl in targetLanguages:
        params = params + "&to=" + tl
    constructed_url = endpoint + params

    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Ocp-Apim-Subscription-Region": region,
        "Content-type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4()),
    }

    # You can pass more than one object in body
    body = [{"text": text}]

    request = requests.post(constructed_url, headers=headers, json=body)
    response = request.json()
    translations_list = response[0]["translations"]

    # create response data structure
    translations = {sourceLanguage: text}
    for translation_language in translations_list:
        translation = translation_language["text"]
        language = translation_language["to"]
        translations[language] = translation

    return translations


def segment(text, asr_status, sessionID):
    """
    this calls the Segmenter
    """
    print("Calling Segmentation API")

    # constructing parameters for call. tl should contain more languages
    pload = {"text": text, "status": asr_status, "sessionID": sessionID}
    endpoint = SEGMENTERAPI + "/parse"

    response = requests.post(url=endpoint, json=pload)
    if response.ok:
        result = response.json()
        mysegment = ""
        try:
            mysegment = result[0]
        except:
            print("SEGMENTER did not return any segment")
        return mysegment
    else:
        result = {"error": response}
        return result


def paraphrase(text, sl):
    """
    this calls the paraphrasing LM which is now a huggingface model hosted on their servers
    we may switch to other models. We may want to host it ourselves
    """
    print("Calling Paraphrasing API")
    API_URL = PARAPHRASE_API_URL
    headers = {"Authorization": PARAPHRASE_API_AUTHORIZATION}

    payload = {"inputs": text}
    response = requests.post(API_URL, headers=headers, json=payload)
    paraphrased_dic = response.json()
    paraphrased = paraphrased_dic[0]["generated_text"]

    return paraphrased

def call_openai(text, model, prompt, previous=None):

    #Note: The next parameters should be available in the Settings DB! 
    temperature = 0.3
    max_tokens = 256
    top_p = 1
    frequency_penalty = 0
    presence_penalty = 0
    stop=["### Sentence ###"]

    response = openai.Completion.create(
        model=model,
        prompt=prompt.format(sentence=text, previous=previous),
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        stop=stop
    )
    response_json = json.dumps(response)
    return response_json


def initialize_segmenterAPI(sessionID, source_language):
    """
    this inizializes a session of the Segmenter for this specific Session ID
    """
    print(PARAPHRASE_API_AUTHORIZATION)
    # we initialize the session with some parameters. The most important is the Session ID
    pload = {
        "lang": source_language,
        "sessionID": sessionID,
        'collapse_finals': True,
    }
    endpoint = SEGMENTERAPI + "/startSession"

    response = requests.post(url=endpoint, json=pload)
    if response.ok:
        result = response.json()
        print("Initializing API: " + str(result))
        return result
    else:
        print("Error initializing of API: " + str(response))
        result = "API initialisation error"

def print_changelog():

    changelog = [
        {"minor version": 0, "details": "initial POC commit", "date": "2022-09-14"},
        {"minor version": 1, "details": "adds version changelog", "date": "2022-09-14"},
        {"minor version": 2, "details": "adds multichannel", "date": "2022-09-14"},
        {
            "minor version": 3,
            "details": "improves UI for Sender/Receiver",
            "date": "2022-09-15",
        },
        {
            "minor version": 4,
            "details": "adds automatic scrolling in Sender table",
            "date": "2022-09-15",
        },
        {
            "minor version": 5,
            "details": "adds timestamp of segment processing",
            "date": "2022-09-15",
        },
        {"minor version": 6, "details": "adds logfile", "date": "2022-09-15"},
        {
            "minor version": 7,
            "details": "adds parameter to reduce calls of API",
            "date": "2022-09-16",
        },
        {
            "minor version": 8,
            "details": "adds feature to improve accuracy with list of terms",
            "date": "2022-09-17",
        },
        {
            "minor version": 9,
            "details": "improves SENDER UI; fix sampling frequency logic",
            "date": "2022-09-19",
        },
        {"minor version": 10, "details": "improves Receiver UI;", "date": "2022-09-19"},
        {
            "minor version": 11,
            "details": "improves sampling frequency logic from APP",
            "date": "2022-09-20",
        },
        {
            "minor version": 12,
            "details": "improves UI Sender; make logging optional (hard coded switch)",
            "date": "2022-09-21",
        },
        {
            "minor version": 13,
            "details": "adds optional AI rephrasing for longer sentences >20 tokens",
            "date": "2022-09-21",
        },
        {
            "minor version": 14,
            "details": "adds API initialisation call with sessionID",
            "date": "2022-09-21",
        },
        {
            "minor version": 15,
            "details": "minor improvements to Receiver UI",
            "date": "2022-09-22",
        },
        {
            "minor version": 16,
            "details": "adds multilingual support",
            "date": "2022-09-22",
        },
        {
            "minor version": 17,
            "details": "adding new timer logic",
            "date": "2022-09-29",
        },
        {
            "minor version": 18,
            "details": "adding controller of voice speed in SENDER",
            "date": "2022-10-02",
        },
        {
            "minor version": 19,
            "details": "new control of session initialisation for segmentation API",
            "date": "2022-10-05",
        },
        {
            "minor version": 20,
            "details": "improved responsivness of RECEIVER",
            "date": "2022-10-06",
        },
        {
            "minor version": 21,
            "details": "adding simple SENDER page with standard settings",
            "date": "2022-10-12",
        },
        {
            "minor version": 22,
            "details": "adding simple login page",
            "date": "2022-10-13",
        },
        {"minor version": 23, "details": "cleaning code", "date": "2022-10-17"},
        {
            "minor version": 24,
            "details": "fix stop translation after 10 segments",
            "date": "2022-10-18",
        },
        {
            "minor version": 25,
            "details": "add deepl for JP",
            "date": "2022-11-14",
        },
    ]

    return changelog
