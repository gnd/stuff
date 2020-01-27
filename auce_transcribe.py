#!/usr/bin/env python3
"""
    Artyoucaneat.sk audio extractor / transcriber / translator & subtitle generator

    This script makes life easier for translators & subs makers of Artyoucaneat.sk

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
        6. Install requirements: pip3 install --upgrade google-cloud-storage google-oauth google-cloud-speech google-cloud-translate==2.0.0

    Usage:
        -------------------------------------------------
        1. For initial transcription, run the script like:

                ./auce_transcribe.py -s <lang_from> /path/to/video.mp4

        where <lang_from> is the language that is spoken in the video, eg sk-SK for Slovak
        or en-US for English.

        The transcribed subtitles will be stored into /path/to/video.srt
        The raw transcription data are saved into /path/to/video.pickle
        and can be used later with --generate.
        -------------------------------------------------
        2. For translation of corrected subtitles, run:

                ./auce_transcribe.py -l <lang_from> <lang_to> /path/to/subtitles.srt

        where <lang_from> is the original language of the subtitles eg. 'sk' or 'en'
        and <lang_to> is the language into which the subtitles should be translated ('en' or 'sk')

        The translated subtitles will be stored into /path/to/subtitles_EN.vtt
        The original subtitles will be copied into /path/to/subtitles_SK.vtt
        -------------------------------------------------
        3. To generate initial subtitles from a pickled transcription, run:

                ./auce_transcribe.py -g <subs_period> /path/to/video.pickle

        The translated subtitles will be stored into /path/to/subtitles_EN.vtt
        The original subtitles will be copied into /path/to/subtitles_SK.vtt
        -------------------------------------------------

    gnd, 2020
"""

import os
import sys
import pickle
import argparse
import subprocess
from math import modf
from google.cloud import speech
from google.cloud import storage
from google.cloud import translate
from google.cloud.speech import types
from google.cloud.speech import enums


### Set some globals
BUCKET_NAME = "artyoucaneat_audio"                      # the bucket where we store the files for transcription
GOOGLE_CRED = "/home/gnd/apps/gnd_gcp.json"             # location of google coud auth json
GOOGLE_CPID = "flowing-athlete-230113"                  # google cloud project ID
SUBS_PERIOD = "4"                                       # how many seconds for one subtitle unit


"""
    Checks if globals set
"""
def check_globals():
    variables = ["BUCKET_NAME", "GOOGLE_CRED", "SUBS_PERIOD"]
    for variable in variables:
        if (globals()[variable] == ""):
            sys.exit("Global variable {} not set. Exiting.".format(variable))


"""
    Checks if the given MP4 file exists.
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
    Checks if the given SRT file exists.
"""
def verify_srt(input_filename):
    if not (os.path.isfile(input_filename)):
        print("Filename does not exist.")
        sys.exit("Exiting.")
    else:
        if ('.srt' != input_filename[-4:]):
            print("Filename malformed.")
            sys.exit("Exiting.")
        else:
            return True
    return False


"""
    Checks if the given SRT file exists.
"""
def verify_pickle(input_filename):
    if not (os.path.isfile(input_filename)):
        print("Filename does not exist.")
        sys.exit("Exiting.")
    else:
        if ('.pickle' != input_filename[-7:]):
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

    ### run the extraction
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
    Translate text via Google Cloud

    Args:
      text The content to translate in string format
      target_language Required. The BCP-47 language code to use for translation.
"""
def gcs_translate_text(lang_from, lang_to, text):
    print("Trying to login to Google Cloud Speech using credentials from {}".format(GOOGLE_CRED))
    client = translate.TranslationServiceClient.from_service_account_json(GOOGLE_CRED)

    print("Translating subtitles..")
    contents = [text]
    parent = client.location_path(GOOGLE_CPID, "global")
    response = client.translate_text(
        parent=parent,
        contents=contents,
        mime_type='text/plain',  # mime types: text/plain, text/html
        source_language_code=lang_from,
        target_language_code=lang_to)

    # return translated text
    print("Subtitles translated.")
    return response.translations[0].translated_text



"""
    Process transcribed sentences and subdivide them into potential subtitle units

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
        last_word = alternative.words[-1]

        ### determine the start and end times of the whole alternative
        if first: # if processing the very first sentence
            start = first_word.end_time.seconds + (first_word.end_time.nanos / 10**9)
            first = False
        else:
            start = first_word.start_time.seconds + (first_word.start_time.nanos / 10**9)
        end = last_word.start_time.seconds + (last_word.start_time.nanos / 10**9)
        old_index = start//subtitle_period

        ### subdivide the sentence(s) within 'alternative' by subtitle_period
        temp_sub = {'text': '', 'start': start, 'end': 0}
        if ((end-start) > subtitle_period):
            for word in alternative.words:
                # get some word data
                word_start = word.start_time.seconds + (word.start_time.nanos / 10**9)
                word_end = word.end_time.seconds + (word.end_time.nanos / 10**9)
                word_chars = len(word.word)
                word_duration = word_end - word_start
                # if we detect a unusually long word it might be a transcription errror
                # in that case push the beginning of the word closer to its end
                if (word_duration > 2):
                    word_start = round(word_end - (word_chars * 0.1),2)
                    #print("setting new start for {} to {}".format(word.word, word_start))
                if (int(word_start//subtitle_period) != old_index):
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
    Extract continuous text from subtitles.
"""
def extract_from_subs(subs_filename):
    print("Extracting subtitles for translation")
    f = open(subs_filename, 'r')
    lines = f.readlines()
    f.close()

    ### process the file
    subs = []
    text = ""
    index = 1
    reading_time = False
    reading_text = False
    temp_sub = {'start': '', 'end': '', 'text': ''}
    for line in lines:
        # submit subtitle unit
        if line == '\n':
            reading_text = False
            text_list = list(text)
            if (text_list[-1] == '\n'):
                text_list[-1] = '\n\n'
                text = "".join(text_list)
            subs.append(temp_sub)
            temp_sub = {'start': '', 'end': '', 'text': ''}
            index+=1
            continue
        # start reading subtitle unit
        if line == "{}\n".format(index):
            reading_time = True
            continue
        if reading_time:
            #print("splitting {}".format(line))
            temp_sub['start'] = line.split('-->')[0].strip()
            temp_sub['end'] = line.split('-->')[1].strip()
            reading_time = False
            reading_text = True
            continue
        if reading_text:
            text += line
            temp_sub['text'] += line + " "
    subs.append(temp_sub)
    print('Subtitles extracted')

    return (text, subs)



"""
    Generates a .SRT subtitle file

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
        k = f.write("{}\n{:02d}:{:02d}:{:02d},{} --> {:02d}:{:02d}:{:02d},{}\n{}\n\n".format(index, start_hour, start_min, start_sec, start_msec, end_hour, end_min, end_sec, end_msec, sub['text']        ))
        index+=1
    f.close()
    print("Subtitles saved !")


"""
    Generates a .VTT subtitle file

    The generated subs are in VTT format:

    --- snip ---
    1
    00:01:48,680 --> 00:01:50,238
    Subtitle text.

    2
    00:01:51,280 --> 00:01:53,700
    Next subtitle text.
    ---- snip ---

"""
def generate_translated_subs(subs_filename, subs, text):
    print("Saving translated subtitles to \"{}\"".format(subs_filename))
    #print(text)

    index = 1
    sub_text = ""
    f = open(subs_filename, 'w')
    f.write("WEBVTT\n\n")
    lines = text.split('\n')
    for line in lines:
        if line == '':
            start = subs[index-1]['start'].replace(',','.')
            end = subs[index-1]['end'].replace(',','.')
            #print("{}\n{} --> {}\n{}".format(index, start, end, sub_text))
            k = f.write("{} --> {}\n{}\n".format(start, end, sub_text))
            sub_text = ""
            index+=1
            continue
        sub_text += line + '\n'
    f.close()
    print("Subtitles saved !")


if __name__ == '__main__':
    ### check if globals set
    check_globals()

    ### init argparse
    ### actually this is ultra stupid i meed two mutually exclusive arguments, which have both two mandatory dependencies
    ### no way how to do it with argparse meh
    parser = argparse.ArgumentParser(description="Subtitle extractor / transcriber / translator & composer")
    parser.add_argument("-s", "--transcribe", help=("Transcribe and generate initial subtitles. "
    "Needed arguments: "
    "lang_from - the language code of the input language in the video (eg. sk-SK or en-US). "
    "video - the video to be transcribed in .mp4 format"
    'subs_period - The period in seconds into which the subs should be divided.'), metavar=('lang_from','video', 'subs_period'), nargs=3)
    parser.add_argument("-g", "--generate", help=("Generate initial subtitles from a pickled transcription. "
    "Needed arguments: "
    'subs_period - The period in seconds into which the subs should be divided.'
    "pickle - The pickled transcription (.pickle)"), metavar=('subs_period', 'pickle'), nargs=2)
    parser.add_argument("-l", "--translate", help=("Translate and generate final subtitles. "
    "Needed arguments: "
    "lang_from - the language code of the input language in the subs (eg. sk or en). "
    "lang_to - the language code of the output language in the subs (eg. sk or en). "
    "subs - The subtitles to be translated in .srt format"), metavar=('lang_from', 'lang_to', 'subs'), nargs=3)
    args = parser.parse_args()


    """
        Transcription & subtitle generation
    """
    if (args.transcribe):
        args_lang = args.transcribe[0]
        args_video = args.transcribe[1]
        args_period = args.transcribe[2]

        ### verify if file exists
        print("Verifying {}".format(args_video))
        if (verify_mp4(args_video)):
            video_file = args_video
            video_filename = os.path.basename(args_video).strip('.mp4')

        ### make a temp audio filename
        audio_file = '/tmp/{}.wav'.format(video_filename)

        ### extract audio from the filename
        extract_audio(video_file, audio_file)

        ### upload file to google cloud
        blob_name = '{}_auce.wav'.format(video_filename)
        gcs_upload_file(BUCKET_NAME, audio_file, blob_name)

        ### transcribe audio
        response = gcs_transcribe("gs://{}/{}".format(BUCKET_NAME, blob_name), args_lang)

        ### pickle the response in case we need to process the transcription later
        pickle_filename = args_video.replace('.mp4','.pickle')
        f = open(pickle_filename, 'wb')
        pickle.dump(response, f)
        f.close()

        ### process response word times
        subs = process_transcription(response.results, int(args_period))

        ### generate a initial subtitle file
        subtitle_filename = args_video.replace('.mp4','_initial.srt')
        generate_subs(subtitle_filename, subs)


    """
        Translation of corrected subtitles
    """
    if (args.translate):
        args_lang_from = args.translate[0]
        args_lang_to = args.translate[1]
        args_subs = args.translate[2]

        ### verify if file exists
        print("Verifying {}".format(args_subs))
        if (verify_srt(args_subs)):
            subs_file = args_subs
            subs_filename = os.path.basename(args_subs).replace('.srt','')

        ### extract text from subtitles
        (text_from, subs) = extract_from_subs(args_subs)

        ### translate the subtitles
        result = gcs_translate_text(args_lang_from, args_lang_to, text_from)
        text_to = str(result)
        #print(text_to)

        ### generate translated subtitles
        subtitle_filename = args_subs.replace('.srt', '_'+args_lang_to.upper()+'.vtt')
        generate_translated_subs(subtitle_filename, subs, text_to)

        ### save a copy of input subs
        subtitle_filename = args_subs.replace('.srt', '_'+args_lang_from.upper()+'.vtt')
        generate_translated_subs(subtitle_filename, subs, text_from)


    """
        Only process existing transcription
    """
    if (args.generate):
        args_period = args.generate[0]
        args_pickle = args.generate[1]

        ### verify if file exists
        print("Verifying {}".format(args_pickle))
        if (verify_pickle(args_pickle)):
            pickle_file = args_pickle

        ### load the pickled response
        print("Loading pickled transcription")
        f = open(pickle_file, 'rb')
        response = pickle.load(f)
        f.close()

        ### process response word times
        subs = process_transcription(response.results, int(args_period))

        ### generate a initial subtitle file
        subtitle_filename = args_pickle.replace('.pickle','_initial.srt')
        generate_subs(subtitle_filename, subs)


    """
        No option specified
    """
    if ((args.transcribe is None) & (args.translate is None)):
        print("Please specify an action.")
