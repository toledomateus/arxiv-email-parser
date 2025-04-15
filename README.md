# arXiv email parser: A Keyword Filter

## Description

This Python script connects to a Gmail account, searches for unread daily digest emails from arXiv (specifically for Computer Science categories in this configuration), and filters the papers listed in those emails based on a user-defined list of keywords.

It extracts the titles and arXiv links of matching papers and saves them to a text file. Processed emails are marked as read in Gmail to avoid reprocessing. The script uses a `.env` file for configuration (credentials, filenames) and includes structured logging for monitoring.

## Features

* Connects securely to Gmail via IMAP using an App Password.
* Searches for specific unread arXiv digest emails.
* Parses plain text email bodies to identify individual paper listings.
* Extracts paper titles, abstracts, and arXiv links.
* Filters papers based on keywords found in titles or abstracts (case-insensitive).
* Reads configuration (credentials, filenames) from a `.env` file.
* Uses the `python-dotenv` library for easy environment variable management.
* Outputs matching titles and links to a configurable text file (default: `arxiv_matches.txt`).
* Marks processed emails as read (`\Seen`) on the Gmail server.
* Provides console logging with timestamps and severity levels (INFO, WARNING, ERROR).

## Prerequisites

* Python 3.6 or higher.
* `pip` (Python package installer).
* A Gmail account with:
    * IMAP access enabled (See [Gmail IMAP Settings](https://support.google.com/mail/answer/7126229)).
    * 2-Step Verification enabled (See [Google 2-Step Verification](https://www.google.com/landing/2step/)).

## Setup & Installation

1.  **Clone or Download:**
    * If using Git: `git clone <repository_url>`
    * Alternatively, download the `arxiv_parser.py` script.

2.  **Navigate to Project Directory:**
    ```bash
    cd path/to/your/project
    ```

3.  **Install Dependencies:**
    Create a file named `requirements.txt` in the project directory with the following content:
    ```txt
    python-dotenv
    ```
    Then run:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Gmail App Password:**
    Generate a 16-character App Password for this script in your Google Account settings. You'll need 2-Step Verification enabled first.
    * Go to [Google Account Security](https://myaccount.google.com/security).
    * Under "Signing in to Google", click "App passwords".
    * Select "Other (Custom name)", give it a name (e.g., "arXiv Parser"), and click "Generate".
    * **Copy the generated 16-character password immediately.** You will need it for the configuration.

## Configuration

The script uses a `.env` file to manage configuration settings securely.

1.  **Create `.env` file:**
    Create a file named `.env` in the root of the project directory.

2.  **Add Configuration:**
    Add the following variables to your `.env` file, replacing the placeholder values with your actual details. Only `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` are strictly required if the default filenames are suitable.

    ```dotenv
    # --- Required Gmail Credentials ---
    # Your full Gmail address
    GMAIL_ADDRESS="your_email@gmail.com"
    # The 16-character App Password you generated
    GMAIL_APP_PASSWORD="your_16_character_app_password"
    # The standart google's imap host
    GMAIL_IMAP_HOST="imap.gmail.com"
    # The standart google's imap port
    GMAIL_IMAP_PORT=993
    # The file that you will include the look up terms
    KEYWORDS_FILENAME="keywords.txt"
    # Name of the file for the output
    OUTPUT_FILENAME="arxiv_matches.txt"
    # The arxiv sender
    ARXIV_SENDER="no-reply@arxiv.org"
    # Yours email subject contains
    EMAIL_SUBJECT_CONTAINS="cs daily"
    ```

3.  **IMPORTANT: Add `.env` to `.gitignore`:**
    Create or edit your `.gitignore` file in the project root and add `.env` to it to prevent accidentally committing your credentials:
    ```gitignore
    .env
    *.pyc
    __pycache__/
    *.log
    ```

4.  **Create Keywords File:**
    Create the file specified by `KEYWORDS_FILENAME`. Add your keywords to this file, one keyword or key phrase per line. Example `keywords.txt`:
    ```txt
    machine learning
    natural language processing
    reinforcement learning
    computer vision
    multi-agent system
    ```
## Usage

1.  **Ensure Configuration:** Make sure your `.env` file is correctly set up with your credentials and that your keywords file exists.
2.  **Run the Script:**
    Open your terminal or command prompt, navigate to the project directory, and run:
    ```bash
    python arxiv_parser.py
    ```
3.  **Check Output:**
    * The script will log its progress to the console (connecting, searching, processing, writing results).
    * Check the file specified by `OUTPUT_FILENAME` for the extracted titles and links of papers matching your keywords.
    * Check your Gmail account; the processed arXiv emails should now be marked as read.

## Output File Format (`arxiv_matches.txt` or as configured)

```text
# arXiv Papers Matching Your Keywords
# Processed on: Tue, 15 Apr 2025 17:30:00 +0200

Match 1:
  Title: GridMind: A Multi-Agent NLP Framework for Unified, Cross-Modal NFL Data Insights
  Link: [https://arxiv.org/abs/2504.08747](https://arxiv.org/abs/2504.08747)

Match 2:
  Title: Another Matching Paper Title
  Link: [https://arxiv.org/abs/xxxx.xxxxx](https://arxiv.org/abs/xxxx.xxxxx)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.