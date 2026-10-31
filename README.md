📖 CodeStory AI

Understand Your Codebase Through Evidence, Not Guesses.

CodeStory AI is an evidence-first developer tool that analyzes Git repositories to help developers explore code changes, investigate commit history, and discover evidence about how a codebase has evolved.

Instead of guessing why code was written a certain way, developers can examine source code, commit messages, and code diffs to investigate the available evidence.

🚀 Features

* Repository Analyzer: Detect and inspect local Git repositories.
* Repository Overview: View commits, contributors, branches, and scanned source files.
* Commit Investigation: Explore commit metadata, authors, timestamps, and commit messages.
* Code Diff Viewer: Inspect code changes between commits.
* Source Code Search: Find matching lines in repository source files.
* Commit History Search: Search commit messages for relevant evidence.
* Diff Search: Search code changes for matching evidence.
* Evidence-Based Reports: Separate observable facts from possible explanations.
* Privacy-Friendly Prototype: No paid AI API key is required.

🛠️ Technology Stack

* Python
* Streamlit
* GitPython
* Pandas
* Git

📋 Requirements

* Python 3.10 or later
* Git
* pip

⚙️ Installation

1. Clone the repository

git clone https://github.com/kuruvalakshmi11428-coder/codestory-ai.git
cd codestory-ai

2. Create and activate a virtual environment

macOS / Linux

python3 -m venv .venv
source .venv/bin/activate

3. Install dependencies

python -m pip install -r requirements.txt

▶️ Run the Application

Start the application with:

python -m streamlit run app.py

Open the local URL displayed in your terminal.

Enter the path to a local Git repository and begin exploring its history, code changes, and searchable evidence.

🔍 How It Works

1. Select a local Git repository.
2. Inspect repository metadata and commit history.
3. Select a commit to examine its details and changed files.
4. Search source code, commit messages, or commit diffs.
5. Review matching evidence to investigate the codebase.

⚠️ Limitations

CodeStory AI is an evidence-search prototype. Matching text and commit metadata do not independently establish why a developer made a change.

Commit history may be limited, and source scanning may skip certain files. Search results identify matching evidence but do not guarantee that the evidence explains the developer’s original intent.

The current prototype does not guarantee AI-generated explanations or independently verify developer intent.

🎯 Vision

Help developers understand unfamiliar codebases faster by connecting source code, repository history, and evidence in one place.

👩‍💻 Author

Kuruva Lakshmi

GitHub: kuruvalakshmi11428-coder

⸻

CodeStory AI — Evidence-first codebase exploration.
