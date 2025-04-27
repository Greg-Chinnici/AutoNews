#!/bin/bash

clear

# # Initialize Conda
# eval "$(conda shell.bash hook)"
# # Initialize Conda for the current shell session
# CONDA_BASE=$(conda info --base)
# source "$CONDA_BASE/etc/profile.d/conda.sh"

# # Activate the conda environment
# conda activate AutoNews

#pip install -r requirements.txt
python3 -m pip install -r requirements.txt

clear

python3 src/ArticleIngest.py

python3 src/ScrapeArticle.py

python3 src/ScriptCreator.py

python3 src/AudioCreator.py

python3 src/AudioCreator.py