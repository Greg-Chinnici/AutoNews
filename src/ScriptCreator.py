import os
import sys
import json
import time
import requests
import argparse
import yaml
from typing import List
from pydantic import BaseModel, Field, field_validator
from langchain_community.chat_models import ChatOllama
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import OutputFixingParser
from langchain_core.exceptions import OutputParserException


# Define the expected structure of the news script
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
    dialogue: List[DialogueLine] = Field(description="List of dialogue lines")

class ScriptCreator:
    def __init__(self, config_filename="config.yaml", verbose=False):
        self.verbose = verbose
        self.config = self._load_config(config_filename)
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
            template="""
                You are a news show scriptwriter. Given the following news article, generate a JSON structured news segment with a casual, professional tone.

                The segment should feature two newscasters:
                - Emily: a seasoned anchor with a calm and authoritative presence.
                - David: a younger co-anchor who brings energy and curiosity.

                The dialogue should alternate between Emily and David, capturing their distinct personas.

                Focus on the actual content of the article, ensuring that the dialogue is engaging and informative. 
                
                The script should be structured as a conversation between the two characters, summarizing the key points of the article.

                Ensure that each character has at least 10 lines of dialogue.

                {format_instructions}

                Each character should alternate naturally. Focus on summarizing the key points conversationally without making things up.

                ARTICLE:
                {article}
            """,
            input_variables=["article"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
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

        # for chunk in response_stream:
        #     words = chunk.content.split()
        #     for word in words:
        #         print(word + ' ', end='', flush=True)
        #         time.sleep(0.3)

        # After streaming, parse the complete output
        try:
            parsed_output = self.fixing_parser.parse(script_output)
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

            # Pretty-print the JSON to the terminal
            print("\nGenerated Script:")
            print(json.dumps(data_dict, indent=4))

            # Write the JSON to a file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=4)
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
                # if script_data:
                #     script_data = filter_dialogue(script_data)
                #     self.save_script(script_data, output_path)

                output_filename = filename.replace('.txt', '.json')
                output_path = os.path.join(output_folder, output_filename)
                self.save_script(script_data, output_path)

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", type=bool, default=False, help="Verbose output (True/False)")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    creator = ScriptCreator(config_filename="script_creator.yaml", verbose=args.verbose)
    creator.process_articles()