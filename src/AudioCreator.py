import json
import sys

from google.cloud import texttospeech
import os
import glob
import time

OUTPUT_FOLDER = "entire-broadcast"


GOOGLE_CHIRP_HD_VOICES = {
    "charon_m": "en-US-Chirp3-HD-Charon",
    "claude_m": "en-US-Chirp3-HD-Enceladus",
    "kore_w": "en-US-Chirp3-HD-Kore",
    "leda_w": "en-US-Chirp3-HD-Leda",
    "lao_w": "en-US-Chirp3-HD-Laomedeia",
}


"""json defined as 
{
  mainTitle: str
  characters: list<str>
  dailogue: list<{
    character: str
    line: str
  }>
}
"""



def synthesise_speech(text, filename, speaker):
    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name=GOOGLE_CHIRP_HD_VOICES[speaker],
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3, sample_rate_hertz=16000
    )
    print(f"Generating {filename} with {speaker} voice...")
    print(f"Input text: {text}")
    print(f"Voice: {voice.name}")
    print(f"Audio config: {audio_config.audio_encoding.name}, {audio_config.sample_rate_hertz} Hz")

    try:
        response = client.synthesize_speech(
            input=input_text, voice=voice, audio_config=audio_config
        )
        # if hte does not exist, create it
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        # Write the response to the output file
        with open(filename, "wb") as out:
            out.write(response.audio_content)
        
    except Exception as e:
        print(f"Error generating speech: {e}")
        sys.exit(1)



generated_scripts_folder = "generated_scripts"
script_files = glob.glob(os.path.join(generated_scripts_folder, "*.json"))

print(f"Found {len(script_files)} script files in {generated_scripts_folder}")

scripts = []
#! TODO: add the char list in header of json scripts

for script_path in script_files:
    with open(script_path, "r") as file:
        try:
            script = json.load(file)
            scripts.append(script)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {script_path}: {e}")


                    
for script in scripts:
    print (f"Processing script: {script['mainTitle']}")
    # yn = input(f"Do you want to generate audio for {script['mainTitle']}? (y/n): ")
    # if yn.lower() != "y":
    #     print("Skipping...")
    #     continue
    
    speaking_order = []
    final_lines = []

    for idx, line in enumerate(script["dialogue"], start=1):
        character = line["character"]
        dialogue = line["line"]
        speaker = ""
        if character == "Emily":
            speaker = "lao_w"
        elif character == "David":
            speaker = "claude_m"
        else:
            speaker = "charon_m"

        segment_title = script["mainTitle"].replace(" ", "-")
        synthesise_speech(dialogue, f"{OUTPUT_FOLDER}/{segment_title}/audio/{idx}_{character}.mp3", speaker)

        speaking_order.append(character)
        filename = f"{idx}_{character}.mp3"
        print(f"{OUTPUT_FOLDER}/{filename}->", end="")
        print(f"{character}: {dialogue}")
        
        time.sleep(0.5)  # Sleep for 0.5 seconds between each line so i dont get rate limted

    metadata_path = f"{OUTPUT_FOLDER}/{segment_title}/metadata.json"
    os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
    with open(metadata_path, "w") as out:
        json.dump(script, out, indent=4)