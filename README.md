# AutoNews

- Submission for Chapman University PantherHacks 2025. 

- Group: Greg Chinnici and Spencer Au

## Installation

- `pip install -r requirements.txt`

## To Run

- `bash scripts/create_script.sh` to generate the scripts and audio
- Build and Run in Unity 

## Pulled from Devpost Submission

### Inspiration
We wanted to create a faster, smarter way to turn live news into engaging, app-ready shows. The goal was to blend real-time content with a conversational, human feel.

### What it does
AutoNews pulls real articles from multiple sources via RSS feeds, clusters them using semantic similarity, and picks the most popular topics From there, a script is created via AI, transcribed to audio via the Google TTS, and then played in a news broadcast.

### How we built it
We built the backend using Python for article scraping, clustering, summarization, and TTS generation, while the frontend app was developed in Unity for playback.

### Challenges we ran into
Initially used NLP via SpaCey for grabbing topics, but embeddings for semantic similarity was better. Also issues getting AI to generate the proper format and length of the json.

### Accomplishments that we're proud of
We’re proud of building a full pipeline — from raw news feeds to playable, realistic news shows — and integrating it smoothly into a functioning Unity app.

### What we learned
We learned a lot about efficient data processing and natural language generation

### What's next for Auto News
We plan to add real-time voting for which topics users want to hear next, expand the voice options, and make the news shows even more interactive.

I do not know how to properly record audio and used the mic with the speakers and Greg was not here. 
Voila.
