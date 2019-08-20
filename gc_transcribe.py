#!/usr/bin/env python
#
# taken from:
#   https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/speech/cloud-client/transcribe_async.py

"""Google Cloud Speech API sample application using the REST API for async
batch processing.

Usage:
    1. create a account on Google Cloud & create first app
    2. get auth .json like here: https://cloud.google.com/docs/authentication/getting-started
    3. export GOOGLE_APPLICATION_CREDENTIALS=/path/to/json
    4. create a new bucket, or use an existing one and upload file to be transcribed (has to be mono)
    5. update bucket permissions (make urself be in Storage Legacy Bucket Owner)
    6. get link of file (eg. gs://myfile.wav)
    7. run like:
            python gc_transcribe.py audio.raw
            python gc_transcribe.py gs://cloud-samples-tests/speech/vr.flac
"""

import argparse
import io

"""Transcribe the given audio file asynchronously."""
def transcribe_file(speech_file, lang):
    from google.cloud import speech
    from google.cloud.speech import enums
    from google.cloud.speech import types
    client = speech.SpeechClient()

    with io.open(speech_file, 'rb') as audio_file:
        content = audio_file.read()

    audio = types.RecognitionAudio(content=content)
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=48000,
        language_code='en-US')

    operation = client.long_running_recognize(config, audio)

    print('Waiting for operation to complete...')
    response = operation.result(timeout=2500)
    for result in response.results:
        print(u'Transcript: {}'.format(result.alternatives[0].transcript))
        #print('Confidence: {}'.format(result.alternatives[0].confidence))

"""Asynchronously transcribes the audio file specified by the gcs_uri."""
def transcribe_gcs(gcs_uri, lang):
    from google.cloud import speech
    from google.cloud.speech import enums
    from google.cloud.speech import types
    client = speech.SpeechClient()

    audio = types.RecognitionAudio(uri=gcs_uri)
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code=lang)

    operation = client.long_running_recognize(config, audio)

    print('Waiting for operation to complete...')
    response = operation.result(timeout=2500)
    for result in response.results:
        print(u'{}'.format(result.alternatives[0].transcript))
        #print('Confidence: {}'.format(result.alternatives[0].confidence))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('path', help='File or GCS path for audio file to be recognized')
    parser.add_argument('lang', help='The language code of the file to be recognized')
    args = parser.parse_args()
    if args.path.startswith('gs://'):
        transcribe_gcs(args.path, args.lang)
    else:
        transcribe_file(args.path, args.lang)
