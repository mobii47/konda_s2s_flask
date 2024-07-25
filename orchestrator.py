import json
from datetime import datetime
#from api import
from constants import SL, TLS_LIST, VOICE_STYLE, SAMPLING_RATE, CHARS_PER_SECOND_THRESHOLD
from helpers import (
    calculate_voice_speeds,
    segment,
    translate,
    call_openai
    ) #translateJA, 

def data_orchestrator(data, cache, sourceLanguage, targetLanguages):
    """Orchestrate cache, datamatrix, segmentation and translation."""
    asr_text = data["asr"]  # ASR text
    #asr_duration = 1#data["duration"]  # ASR text's duration
    asr_status = data["status"]  # ASR status (temporary/final/silence)
    sessionID = data["room"]  # Session ID
    use_rewriting = data["rewriting"]  # Enable rewriting feature
   
    # Get current session settings
    session_settings = cache.get(sessionID)
    asr_callbacks = session_settings["asr_callbacks"]
    segment_nr = session_settings["segment_nr"]
    voice_speeds = session_settings["voice_speeds"]
    prev_timestamp = session_settings["prev_timestamp"]
    prev_chars_per_seconds = session_settings["prev_chars_per_seconds"]
       
    # Default values if no values are passed
    if use_rewriting == "":
        use_rewriting = False
    if targetLanguages == "":
        targetLanguages = TLS_LIST
    if sourceLanguage == "":
        sourceLanguage = SL

    print(
        f'Data received from CONSOLLE:\n'
        f"\tsession ID: '{sessionID}'\n"
        f"\ttext: '{asr_text}'\n"
        f"\tstatus: '{asr_status}'\n"
        f"\tasr_callbacks: '{asr_callbacks}'\n"
        f"\tvoiceSpeed: '{voice_speeds}'\n"
        f"\tuse_rewriting: '{use_rewriting}'\n"
        f"\tsourceLanguage: '{sourceLanguage}'\n"
        )

    # Call the Segmenter API with a given sampling rate. 1 is better
    mysegment = ''
    mysegment_origin = ''
    flag_rewritten = ""  # this is a flag for ML rewriting to show in R&D UI

    # If source language is not supported by segmenter, translate final segment and emit it
    if sourceLanguage == 'ja':
        print("LANGUAGE WITHOUT SEGMENTER")
        if asr_status == 'final':
            mytranslations = translate(asr_text, sourceLanguage, targetLanguages)
            # Create response payload
            mytranslations_json = json.dumps(mytranslations)
            payload = {
                "asr": asr_text,
                "segment": '',
                "segment_origin": '',
                "translations": mytranslations_json,
                "paraphraseFeature": flag_rewritten,
                "voiceSpeed": voice_speeds['es'],
                "voiceStyle": VOICE_STYLE,
                "status": "ok",
                "src_chars_per_second": '',
                "speaker_speed_fast_flag": ''
            }
            return payload
        else:
            # Respond with an empty status
            payload = {"status": "empty"}
            return payload

    if asr_status == 'temporary':
        if asr_callbacks % SAMPLING_RATE == 0:
            mysegment = segment(asr_text, asr_status, sessionID)
        else:
            print("skipping this callback to save computational power."
                  " 1 is not supported by live deployment")
    else:
        mysegment = segment(asr_text, asr_status, sessionID)

    # Continue with the NLP pipeline only if a segment has been returned
    if mysegment:
        print("Data received from SEGMENTER:\n\ttext: " + mysegment)

        # Calculate speaker's speed (characters/second)
        timestamp = datetime.timestamp(datetime.now())
        src_segment_duration = timestamp - prev_timestamp
        src_chars_per_second = round(len(mysegment)/src_segment_duration, 2)
        
        # get average of last 5 speaker speeds
        prev_chars_per_seconds.append(src_chars_per_second)        
        prev_chars_per_seconds_avg = round(sum(prev_chars_per_seconds)/5, 2)

        # consider 30 characters/second as a "fast" speaking threshold
        chars_per_second_threshold = CHARS_PER_SECOND_THRESHOLD[sourceLanguage]
        if prev_chars_per_seconds_avg >= chars_per_second_threshold:
            speaker_speed_fast_flag = True
        else:
            speaker_speed_fast_flag = False

        # deciding if a segment needs to be rewritten, now off as default
        # this is in focus of R&D work
        mysegment_origin = mysegment
        if use_rewriting:
            countOfWords = len(mysegment.split())
            # we paraphrase only long segments for now.
            # This parameter should be moved to Orchestrator default settings
            if countOfWords > 4:
                print("Sending to GPT: " + mysegment)
                #IMPORTANT both 'prompt' and 'model' needs to be saved in setting DB!
                model = 'text-davinci-003'
                prompt = """ 

### Instructions ###
You are a bot specialized in rewriting speeches sentence by sentence. You receive a sentence. Your task is to rewrite it according to the following rules:
1. Keep the same meaning of the original sentence, without adding new parts
2. Make the sentence shorter
3. Make the sentence sound as natural as possible
4. Keep the tone, register and style of the original sentence

### Original Sentence ###
{sentence}

### Rewritten Sentence ###
"""
                #prompt ="You will be given a sentence. Rewrite the sentence in a shorter form. Avoid using contractions. Do not suppress conjunctions and linking words. \n Sentence: {sentence} \n Rewrite:"
                json_string = call_openai(mysegment, model ,prompt=prompt)
                # Parse the JSON data
                json_data = json.loads(json_string)

                # Extract the value of "text" from the parsed JSON data
                mysegment = json_data["choices"][0]["text"]
                mysegment = mysegment.replace("\n", "")
                print("Receiving from GPT: " + mysegment)

            flag_rewritten = True

        # translate the segment in target languages
        mytranslations = translate(mysegment, sourceLanguage, targetLanguages)
        #print("Data returned from AZURE translator: ")
        #print(mytranslations)

        # overwrite JA translation with a better one
        # if 'ja' in targetLanguages:
        # mytranslationJA = translateJA(mysegment, sourceLanguage, 'JA')
        # print("Data returned from DEEPL translator: ")
        # print(mytranslationJA)
        # mytranslations.update(ja=mytranslationJA)

        # Recalculate voice speeds
        voice_speeds = calculate_voice_speeds(mytranslations,
                                              targetLanguages,
                                              src_segment_duration,
                                              voice_speeds)

        # Increase counters and add one row to dm
        asr_callbacks += 1
        segment_nr += 1

        # Save current settings
        session_settings = {
            "asr_callbacks": asr_callbacks,
            "segment_nr": segment_nr,
            "voice_speeds": voice_speeds,
            "prev_timestamp": timestamp,
            "prev_chars_per_seconds": prev_chars_per_seconds[-5:]
            }
        cache.set(sessionID, session_settings)

        # Create response payload
        mytranslations_json = json.dumps(mytranslations)
        payload = {
            "asr": asr_text,
            "segment": mysegment,
            "segment_origin": mysegment_origin,
            "translations": mytranslations_json,
            "paraphraseFeature": flag_rewritten,
            "voiceSpeed": voice_speeds['es'],
            "voiceStyle": VOICE_STYLE,
            "status": "ok",
            "src_chars_per_second": src_chars_per_second,
            "speaker_speed_fast_flag": speaker_speed_fast_flag
        }

    else:
        # Update session info in cache
        asr_callbacks += 1
        session_settings = {
            "asr_callbacks": asr_callbacks,
            "segment_nr": segment_nr,
            "voice_speeds": voice_speeds,
            "prev_timestamp": prev_timestamp,
            "prev_chars_per_seconds": prev_chars_per_seconds[-5:]
        }
        cache.set(sessionID, session_settings)

        # Respond with an empty status
        payload = {"status": "empty"}

    return payload
