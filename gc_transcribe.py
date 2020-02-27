#!/usr/bin/env python

"""
Simple Google Clout Speech to Text script
Appropriated from https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/speech/cloud-client/transcribe_async.py

Usage:
    1. create a account on Google Cloud & create first app
    2. get auth .json like here: https://cloud.google.com/docs/authentication/getting-started
    3. save json somewhere to disk and point the GOOGLE_CRED bellow to its location
    4. create a new bucket, or use an existing one and set BUCKET_NAME bellow to its name
    5. run like:

            python gc_transcribe.py /path/to/file.wav sk-SK

    The script will generate a /path/to/file_transcribed.txt with the transcription
    The file has to be a mono 16kbps 44100 Microsoft WAV

    gnd, 2020
"""

#TODO
# - look into possible sentence regularisation
# - is it hard to slap a .js overlay on this to be able to fix transcription ala trint ?
# - compare with Amazon

import io
import os
import sys
import argparse
import subprocess
from google.cloud import speech
from google.cloud import storage
from google.cloud.speech import types
from google.cloud.speech import enums


""" Set some globals here """
GOOGLE_CRED = "/home/gnd/apps/gnd_gcp.json"             # location of google coud auth json
BUCKET_NAME = "gnd_transcription_audio"                     # name of google cloud bucket


"""
    Checks if the given file exists.
"""
def verify_file(input_filename):
    if not (os.path.isfile(input_filename)):
        print("Filename does not exist.")
        sys.exit("Exiting.")
    else:
        if (input_filename.endswith('.wav') |
            input_filename.endswith('.mp3') |
            input_filename.endswith('.ogg') |
            input_filename.endswith('.flac')):
                return True
        else:
            print("Unknown filename. Please provide a .wav / .mp3 / .ogg / .flac")
            sys.exit("Exiting.")
    return False


"""
    Converts file into a mono WAV
"""
def convert_audio(input_file, audio_file):
    ffmpeg_command = ["ffmpeg", "-y", "-i", input_file, "-ac", "1", "-ar", "44100", audio_file]

    ### run the extraction
    try:
        print("Trying to convert audio from {} to {}\nUsing \"{}\"".format(input_file, audio_file, " ".join(ffmpeg_command)))
        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (data_out, err_out) = process.communicate()
        returncode = process.returncode
    except:
        print("ERROR Couldnt run audo extraction")
        print("{}".format(sys.exc_info()[1]))
        sys.exit("Exiting")

    print("Audio converted")


"""
    Uploads the audiofile to a google cloud storage bucket
"""
def gcs_upload_file(bucket_name, audio_file, destination_blob_name):
    print("Trying to login to Google Cloud Storage using credentials from {}".format(GOOGLE_CRED))
    storage_client = storage.Client.from_service_account_json(GOOGLE_CRED)

    print("Trying to upload {} to google cloud bucket \"{}\"".format(audio_file, bucket_name))
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name, chunk_size=1048576)     #set smaller chunk_size to prevent timeouts on large files
    blob.upload_from_filename(audio_file)

    print(
        "File {} uploaded to {}.".format(
            audio_file, destination_blob_name
        )
    )


"""
    Asynchronously transcribes the audio file specified by the gcs_uri.
    Taken from: https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/speech/cloud-client/transcribe_async.py
"""
def gcs_transcribe(gcs_uri, lang):
    transcription = []

    print("Trying to login to Google Cloud Speech using credentials from {}".format(GOOGLE_CRED))
    speech_client = speech.SpeechClient.from_service_account_json(GOOGLE_CRED)

    print("Trying to start transcription..")
    audio = types.RecognitionAudio(uri=gcs_uri)
    config = types.RecognitionConfig(
        #enable_word_time_offsets=True, # to get word start and stop times
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code=lang)
    operation = speech_client.long_running_recognize(config, audio)
    print('Waiting for transcription to complete...')
    response = operation.result(timeout=2500)
    print("Transcription done !")

    return response


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('file', help='Audio file to be transcribed')
    parser.add_argument('lang', help='Language code of the file to be transcribed')
    args = parser.parse_args()

    """
        Transcription
    """
    ### verify if file exists
    print("Verifying {}".format(args.file))
    if (verify_file(args.file)):
        if (args.file.endswith('.wav')):
            input_filename = os.path.basename(args.file).replace('.wav','')
            outfile = args.file.strip('.wav') + '_transcribed.txt'
        if (args.file.endswith('.mp3')):
            input_filename = os.path.basename(args.file).replace('.mp3','')
            outfile = args.file.strip('.mp3') + '_transcribed.txt'
        if (args.file.endswith('.flac')):
            input_filename = os.path.basename(args.file).replace('.flac','')
            outfile = args.file.strip('.flac') + '_transcribed.txt'
        if (args.file.endswith('.ogg')):
            input_filename = os.path.basename(args.file).replace('.ogg','')
            outfile = args.file.strip('.ogg') + '_transcribed.txt'
        input_file = args.file

    ### convert the file
    convert_audio(input_file, '/tmp/' + input_filename + '.wav')

    ### upload file to google cloud
    blob_name = '{}_transcribe.wav'.format(input_filename)
    gcs_upload_file(BUCKET_NAME, '/tmp/' + input_filename + '.wav', blob_name)

    ### transcribe audio
    response = gcs_transcribe("gs://{}/{}".format(BUCKET_NAME, blob_name), args.lang)

    ### print response into textfile
    f = open(outfile, 'w')
    for result in response.results:
        f.write("{}\n".format(result.alternatives[0].transcript.encode('utf-8')))
    f.close()

    print("Done !")
