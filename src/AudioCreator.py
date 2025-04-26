import json
import sys

from google.cloud import texttospeech
import os

OUTPUT_FOLDER = "radio-show"


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

script = {
    "mainTitle": "Tapping the Sun: Big Box Stores as Solar Farms?",
    "characters": ["Emily", "David"],
    "dialogue": [
        {
            "character": "Emily",
            "line": "Good evening and welcome back to the news desk.",
        },
        {
            "character": "David",
            "line": "Thanks for joining us. Tonight, we're looking at a potentially massive untapped resource for clean energy: the rooftops of America's big box stores and warehouses.",
        },
        {
            "character": "Emily",
            "line": "That's right, David. When you think of renewable energy, you might picture sprawling solar farms or residential rooftop panels. But reports highlight the enormous potential right in the heart of our communities, atop stores like Walmart, Target, and others.",
        },
        {
            "character": "David",
            "line": "The numbers are quite striking, Emily. We're talking billions of square feet of flat, open, sun-exposed space. Studies suggest that covering these roofs with solar panels could generate enough electricity to power millions of homes annually and significantly cut carbon emissions.",
        },
        {
            "character": "Emily",
            "line": "Beyond the environmental benefits, there are clear advantages for the businesses themselves, such as reduced electricity bills and increased energy independence. It also helps reduce energy lost during transmission because the power is generated so close to where it's used.",
        },
        {
            "character": "David",
            "line": "And some major retailers are already leading the way. Companies like Walmart, Amazon, IKEA, and Target have invested in rooftop solar on many of their locations, demonstrating that it's feasible on a large scale.",
        },
        {
            "character": "Emily",
            "line": "However, it's not without its challenges. The upfront cost of installation can be significant, and there can be complexities with grid connection and navigating local regulations.",
        },
        {
            "character": "David",
            "line": "Policy and incentives play a crucial role here. Experts say extending tax credits, streamlining permitting processes, and implementing supportive policies like net metering are key to unlocking this potential on a wider scale.",
        },
        {
            "character": "Emily",
            "line": "Harnessing the solar power from these massive rooftops could be a significant step towards meeting our clean energy goals, turning everyday shopping centers into vital power generators.",
        },
        {
            "character": "David",
            "line": "Indeed. It's a compelling idea with substantial potential. We'll continue to follow the progress on this front.",
        },
        {"character": "Emily", "line": "Absolutely. Coming up next..."},
    ],
}


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

        with open(filename, "wb") as out:
            out.write(response.audio_content)
        
    except Exception as e:
        print(f"Error generating speech: {e}")
        sys.exit(1)


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

    synthesise_speech(dialogue, f"{OUTPUT_FOLDER}/audio/{idx}_{character}.mp3", speaker)

    speaking_order.append(character)
    filename = f"{idx}_{character}_{speaking_order.count(character)}.mp3"
    print(f"{OUTPUT_FOLDER}/{filename}->", end="")
    print(f"{character}: {dialogue}")

metadata_path = f"{OUTPUT_FOLDER}/metadata.json"
os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
with open(metadata_path, "w") as out:
    json.dump(script, out, indent=4)

