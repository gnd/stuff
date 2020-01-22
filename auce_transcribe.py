#!/usr/bin/env python3
"""
    Artyoucaneat.sk subtitle extractor / transcriber / translator & composer

    This script akes life easier for translators & subs makers of Artyoucaneat.sk

    In particular:
        - extracts the audio track from a MP4 video
        - transcribes given track using Google Cloud Speech to Text
        - generates initial subtitles from the transcription
        - (TODO) translates the (manually) corrected subtitles into English
        - (TODO) outputs the translation in the form of a .vtt subtitle file

    Installation:
        1. Create a account on Google Cloud & create first app
        2. Get auth .json like here: https://cloud.google.com/docs/authentication/getting-started
        3. Add the path to the auth .json into the google_cred global variable below
        4. Create a google cloud storage bucket
        5. Add the name of the bucket into the bucket_name global variable below
        6. Install requirements: pip3 install --upgrade google-cloud-storage google-oauth google-cloud-speech

    Usage:
        Run the script like ./auce_transcribe.py sk-SK en-US /path/to/video.mp4
        The transcribed subtitles will be stored into /path/to/video.srt

    gnd, 2020
"""

import os
import sys
import pickle
import argparse
import subprocess
from math import modf
from google.cloud import storage
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types


### Set some globals
BUCKET_NAME = "" # the bucket where we store the files for transcription
GOOGLE_CRED = "" # location of google coud auth json
SUBS_PERIOD = "" # how many seconds for one subtitle unit


"""
    Checks if globals set
"""
def check_globals():
    variables = ["BUCKET_NAME", "GOOGLE_CRED", "SUBS_PERIOD"]
    for variable in variables:
        if (globals()[variable] == ""):
            sys.exit("Global variable {} not set. Exiting.".format(variable))


"""
    Checks of the given file exists.
"""
def verify_mp4(input_filename):
    if not (os.path.isfile(input_filename)):
        print("Filename does not exist.")
        sys.exit("Exiting.")
    else:
        if ('.mp4' != input_filename[-4:]):
            print("Filename malformed.")
            sys.exit("Exiting.")
        else:
            return True
    return False


"""
    Extracts audio from the filename
"""
def extract_audio(video_file, audio_file):
    ffmpeg_command = ["ffmpeg", "-y", "-i", video_file, "-ac", "1", "-ar", "44100", audio_file]

    ### run the spider
    try:
        print("Trying to extract audio from {} to {}\nUsing \"{}\"".format(video_file, audio_file, " ".join(ffmpeg_command)))
        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (data_out, err_out) = process.communicate()
        returncode = process.returncode
    except:
        print("ERROR Couldnt run audo extraction")
        print("{}".format(sys.exc_info()[1]))
        sys.exit("Exiting")

    print("Audio extracted")


"""
    Uploads the audiofile to a google cloud storage bucket
"""
def upload_file(bucket_name, audio_file, destination_blob_name):
    print("Trying to login to Google Cloud Storage using credentials from {}".format(GOOGLE_CRED))
    storage_client = storage.Client.from_service_account_json(GOOGLE_CRED)

    print("Trying to upload {} to google cloud bucket \"{}\"".format(audio_file, bucket_name))
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(audio_file)

    print(
        "File {} uploaded to {}.".format(
            audio_file, destination_blob_name
        )
    )


"""
    Asynchronously transcribes the audio file specified by the gcs_uri.
    Taken from:  https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/speech/cloud-client/transcribe_async.py
"""
def transcribe_gcs(gcs_uri, lang):
    transcription = []

    print("Trying to login to Google Cloud Speech using credentials from {}".format(GOOGLE_CRED))
    speech_client = speech.SpeechClient.from_service_account_json(GOOGLE_CRED)

    print("Trying to start transcription..")
    audio = types.RecognitionAudio(uri=gcs_uri)
    config = types.RecognitionConfig(
        enable_word_time_offsets=True, # to get word start and stop times
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code=lang)
    operation = speech_client.long_running_recognize(config, audio)
    print('Waiting for transcription to complete...')
    response = operation.result(timeout=2500)
    print("Transcription done !")

    return response


"""
    Process transcribed sentences and subdivide them into a potential subtitle units

    This is currently very primitive and relies heavily on the way google divides
    the transcription into several parts (results). These are in turn divided into parts of
    <subtitle_period> length (global SUBS_PERIOD).

    An ideal variant would be to aim for a division based on sentence structure.
    This is however currently impossible with the state of the transcription.

    Another improvement would be to count a WPM rate per google division (result)
    and then use a 160-180 recommended WPM with 0.3 secs for word.
    Check BBC subtitle guidelines: https://bbc.github.io/subtitle-guidelines/

    TODO see if WPM subdivision any better.
"""
def process_transcription(results, subtitle_period):
    print("Processing transcription into subtitles..")
    subs = []
    first = True
    old_word = results[0].alternatives[0].words[0]
    for result in results:
        alternative = result.alternatives[0]
        transcript = alternative.transcript
        first_word = alternative.words[0]
        last_word = alternative.words[-1:][0]

        ### determine the start and end times of the whole alternative
        if first: # if processing the very first sentence
            start = first_word.end_time.seconds + (first_word.end_time.nanos / 10**9)
        else:
            start = first_word.start_time.seconds + (first_word.start_time.nanos / 10**9)
        end = last_word.start_time.seconds + (last_word.start_time.nanos / 10**9)

        ### subdivide the sentence(s) within 'alternative' by subtitle_period
        temp_sub = {'text': '', 'start': start, 'end': 0}
        old_index = start//subtitle_period
        if ((end-start) > subtitle_period):
            for word in alternative.words:
                if first: # if processing the very first sentence
                    word_start = word.end_time.seconds
                    first = False
                else:
                    word_start = word.start_time.seconds
                if ((word_start//subtitle_period) != old_index):
                    temp_sub['end'] = old_word.end_time.seconds + (old_word.end_time.nanos / 10**9)
                    subs.append(temp_sub)
                    old_index = (word_start//subtitle_period)
                    temp_sub = {'text': '', 'start': 0, 'end': 0}
                    temp_sub['start'] = word_start + (word.start_time.nanos / 10**9)
                temp_sub['text'] += word.word + " "
                old_word = word
            # append last temp_sub
            temp_sub['end'] = word.end_time.seconds + (word.end_time.nanos / 10**9)
            subs.append(temp_sub)
    print("Subtitles done !")
    return subs


"""
    Generates a subtitle file

    The generated subs are in SRT format:

    --- snip ---
    1
    00:01:48,680 --> 00:01:50,238
    Subtitle text.

    2
    00:01:51,280 --> 00:01:53,700
    Next subtitle text.
    ---- snip ---

"""
def generate_subs(subs_filename, subs):
    print("Saving subtitles..")
    index = 1
    f = open(subs_filename,'w')
    for sub in subs:
        start_hour = int(sub['start'] // 3600)
        start_min = int(sub['start'] // 60)
        start_sec = int(sub['start'] % 60)
        start_msec = int(round(modf(sub['start'])[0],2)*1000)
        end_hour = int(sub['end'] // 3600)
        end_min = int(sub['end'] // 60)
        end_sec = int(sub['end'] % 60)
        end_msec = int(round(modf(sub['end'])[0],2)*1000)
        #print("{}\n{:02d}:{:02d}:{:02d},{} --> {:02d}:{:02d}:{:02d},{}\n{}\n".format(index, start_hour, start_min, start_sec, start_msec, end_hour, end_min, end_sec, end_msec, sub['text']))
        k = f.write("{}\n{:02d}:{:02d}:{:02d},{} --> {:02d}:{:02d}:{:02d},{}\n{}\n\n".format(index, start_hour, start_min, start_sec, start_msec, end_hour, end_min, end_sec, end_msec, sub['text']))
        index+=1
    f.close()
    print("Subtitles saved !")


def main():
    ### check if globals set
    check_globals()

    ### init argparse
    parser = argparse.ArgumentParser(description="Subtitle extractor / transcriber / translator & composer")
    parser.add_argument('lang_from', help='The language code of the input language in the video')
    parser.add_argument('lang_to', help='The language code of the output language in the subs')
    parser.add_argument('video', help='The video to be transcribed')
    args = parser.parse_args()

    ### parse args
    print("Verifying {}".format(args.video))
    if (verify_mp4(args.video)):
        video_file = args.video
        video_filename = os.path.basename(args.video).replace('.mp4','')

    ### make a temp audio filename
    audio_file = '/tmp/{}.wav'.format(video_filename)

    ### extract audio from the filename
    extract_audio(video_file, audio_file)

    ### upload file to google cloud
    blob_name = '{}_auce.wav'.format(video_filename)
    upload_file(BUCKET_NAME, audio_file, blob_name)

    ### transcribe audio
    response = transcribe_gcs("gs://{}/{}".format(BUCKET_NAME, blob_name), args.lang_from)

    ### pickle the response in case something goes wrong
    f = open('/tmp/results.pickle', 'wb')
    pickle.dump(response, f)
    f.close()

    ### process response word times
    subs = process_transcription(response.results, int(SUBS_PERIOD))

    ### generate a initial subtitle file
    subtitle_filename = args.video.replace('.mp4','.srt')
    generate_subs(subtitle_filename, subs)


if __name__ == '__main__':
    main()
