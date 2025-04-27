import os
import shutil
import sys
import json
import time
import requests
import unicodedata
import argparse
import yaml
from typing import List
from pydantic import BaseModel, Field, field_validator, model_validator
from langchain_community.chat_models import ChatOllama
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import OutputFixingParser
from langchain_core.exceptions import OutputParserException


# Define the expected Pydantic structure of the news script
class DialogueLine(BaseModel):
    character: str
    line: str

    @field_validator('character')
    @classmethod
    def validate_character(cls, v):
        if v not in {"Emily", "David"}:
            raise ValueError("Character must be 'Emily' or 'David'")
        return v

class NewsScript(BaseModel):
    mainTitle: str = Field(description="Summarized title of the article")
    characters: List[str] = Field(description="List containing only ['Emily', 'David']")
    dialogue: List[DialogueLine] = Field(
        description="List of dialogue entries. Each entry is a dictionary with a 'character' (Emily or David) and a 'line' (their dialogue)."
    )

    @field_validator('characters')
    @classmethod
    def validate_characters(cls, v):
        allowed_characters = {"Emily", "David"}
        if not all(c in allowed_characters for c in v):
            raise ValueError("Characters must only include 'Emily' and 'David'")
        return v

    @model_validator(mode="after")
    def validate_dialogue_counts(self):
        """Check that each character has at least 15 lines."""
        counts = {"Emily": 0, "David": 0}
        for entry in self.dialogue:
            if entry.character in counts:
                counts[entry.character] += 1

        if counts["Emily"] < 15 or counts["David"] < 15:
            raise ValueError(
                f"Each character must have at least 15 lines. Current counts: Emily={counts['Emily']}, David={counts['David']}"
            )

        return self
    

class ScriptCreator:
    def __init__(self, config_filename="config.yaml", verbose=False):
        self.verbose = verbose
        self.config = self._load_config(config_filename)
        num_lines=self.config.get("num_lines", 17),
        self.model = ChatOllama(
            model=self.config["deepseek"]["model_name"],
            temperature=self.config["deepseek"].get("temperature", 0.7),
            top_p=self.config["deepseek"].get("top_p", 0.9),
            max_tokens=self.config["deepseek"].get("max_tokens", 1024),
            streaming=False
        )
        self.parser = JsonOutputParser(pydantic_object=NewsScript)
        self.fixing_parser = OutputFixingParser.from_llm(parser=self.parser, llm=self.model)
        self.prompt = PromptTemplate(
            template = """
            You are a strict JSON API, and are tasked with creating a script for a news show based on the provided article;
            there are two characters in the script: Emily and David, and they will alternate speaking lines.

            You will ONLY generate a valid JSON object, exactly matching the following schema, based on the input article.

            ARTICLE:
            {article}

            Each character must alternate naturally and summarize the key points conversationally, without inventing details.

            IMPORTANT:

            - Each dialogue entry MUST be an object with exactly two fields:
                - "character": either "Emily" or "David"
                - "line": the text they say
            - Do NOT use "speaker", "text", "name", or "lines" fields.
            - Do NOT group multiple lines under a character.
            - Only use the field names "character" and "line" exactly.
            - Each character must have at least {num_lines} lines.

            JSON structure:

            {{
                "mainTitle": "TITLE OF ARTICLE",
                "characters": ["Emily", "David"],
                "dialogue": [
                    {{
                        "character": "Emily",
                        "line": "First line"
                    }},
                    {{
                        "character": "David",
                        "line": "Second line"
                    }},
                    {{
                        "character": "Emily",
                        "line": "Third line"
                    }},
                    {{
                        "character": "David",
                        "line": "Fourth line"
                    }},
                    {{
                        "character": "Emily",
                        "line": "Fifth line"
                    }},
                    {{
                        "character": "David",
                        "line": "Sixth line"
                    }}
                ]
            }}
            """,
            input_variables=["article"],
            partial_variables={"format_instructions": self.parser.get_format_instructions(), "num_lines": num_lines}
            #partial_variables={"num_lines": num_lines}
    )

    def _load_config(self, config_filename):
        config_path = os.path.join(os.getcwd(), "config", config_filename)
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def is_ollama_running(self):
        try:
            response = requests.get('http://localhost:11434')
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False

    def start_ollama(self):
        try:
            os.system("open -a Ollama")
            print("Starting Ollama...")
            for _ in range(20):
                if self.is_ollama_running():
                    print("Ollama is now running!")
                    return
                time.sleep(0.5)
            print("Warning: Ollama may not have started properly.")
        except Exception as e:
            print(f"Failed to start Ollama: {e}")

    def normalize_text(self, text):
        return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")

    def load_article(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
        
    def filter_dialogue(script_data):
        allowed_characters = {"Emily", "David"}
        script_data.dialogue = [
            line for line in script_data.dialogue if line.character in allowed_characters
        ]
        return script_data
    

    def generate_script(self, article_text):
        formatted_prompt = self.prompt.format(article=article_text)
        response_stream = self.model.stream(formatted_prompt)
        script_output = ""

        for chunk in response_stream:
            print(chunk.content, end="", flush=True) 
            script_output += chunk.content

        try:
            parsed_output = self.fixing_parser.parse(script_output)

            if parsed_output is None:
                print("Parsing returned None. Skipping this article.")
                return None
            
            # Validate and correct structure
            required_keys = {"mainTitle", "characters", "dialogue"}
            missing_keys = required_keys - parsed_output.keys()

            if missing_keys:
                print(f"Invalid output structure: missing keys {missing_keys}")
                if "characters" in missing_keys:
                    parsed_output["characters"] = ["Emily", "David"]
                    print("Auto-filled missing 'characters' field.")

            if "mainTitle" in parsed_output:
                parsed_output["mainTitle"] = unicodedata.normalize("NFKD", parsed_output["mainTitle"]).encode("ascii", "ignore").decode("ascii")

            if "dialogue" in parsed_output:
                for entry in parsed_output["dialogue"]:
                    if "character" in entry:
                        entry["character"] = unicodedata.normalize("NFKD", entry["character"]).encode("ascii", "ignore").decode("ascii")
                    if "line" in entry:
                        entry["line"] = unicodedata.normalize("NFKD", entry["line"]).encode("ascii", "ignore").decode("ascii")

            return parsed_output

        except OutputParserException as e:
            print(f"Parsing failed: {e}")
            return None

    
    def save_script(self, script_data, output_path):
        if script_data is None:
            print(f"Skipping saving for {output_path} due to parsing failure.")
            return
        try:
            # Determine if script_data is a Pydantic model or a dictionary
            data_dict = script_data.dict() if hasattr(script_data, 'dict') else script_data

            # Force the correct key order: mainTitle -> characters -> dialogue
            ordered_data = {
                "mainTitle": data_dict.get("mainTitle", ""),
                "characters": data_dict.get("characters", ["Emily", "David"]),
                "dialogue": data_dict.get("dialogue", [])
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(ordered_data, f, indent=4)

            print(f"Saved script to {output_path}")

        except Exception as e:
            print(f"Error saving JSON for {output_path}: {e}")


    def process_articles(self, input_folder='scraped_articles', output_folder='generated_scripts'):
        if not self.is_ollama_running():
            self.start_ollama()

        os.makedirs(output_folder, exist_ok=True)

        for filename in os.listdir(input_folder):
            if filename.endswith('.txt'):
                file_path = os.path.join(input_folder, filename)
                article_text = self.load_article(file_path)

                print(f"Processing {filename}...")
                script_data = self.generate_script(article_text)

                output_filename = filename.replace('.txt', '.json')
                output_path = os.path.join(output_folder, output_filename)
                self.save_script(script_data, output_path)

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", type=bool, default=False, help="Verbose output (True/False)")
    return parser.parse_args()

OUTPUT_DIR = os.path.join("generated_scripts")

if __name__ == "__main__":
    args = parse_arguments()
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    creator = ScriptCreator(config_filename="script_creator.yaml", verbose=args.verbose)
    creator.process_articles()