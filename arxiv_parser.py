import imaplib
import email
import re
import os
import logging

from dotenv import load_dotenv # type: ignore

# --- Logging Configuration ---
# Format includes timestamp, logging level, and the message
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logging.info("Loading environment variables from .env file")
load_dotenv()
gmail_imap_host = os.getenv("GMAIL_IMAP_HOST")
gmail_imap_port = os.getenv("GMAIL_IMAP_PORT")
keywords_file = os.getenv("KEYWORDS_FILE")
output_file = os.getenv("OUTPUT_FILE")
arxiv_sender = os.getenv("ARXIV_SENDER")
email_subject_contains = os.getenv("EMAIL_SUBJECT_CONTAINS")


# --- Function to Read Keywords ---
def load_keywords(filename):
    """Loads keywords from a file, one per line."""
    keywords = []
    if not os.path.exists(filename):
        logging.error(f"Error: Keywords file '{filename}' not found.", exc_info=True)
        return None
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                keyword = line.strip()
                if keyword:  # Ignore empty lines
                    keywords.append(keyword)
        logging.info(f"Loaded {len(keywords)} keywords from '{filename}'.")
        return keywords
    except Exception as e:
        logging.error(f"Error reading keywords file '{filename}': {e}", exc_info=True)
        return None


# --- Function to Parse Email Body and Find Matches ---
def process_email_body(body, keywords):
    """
    Parses the plain text body of an arXiv email, extracts papers,
    and checks titles and abstracts against keywords.

    Args:
        body (str): The plain text content of the email.
        keywords (list): A list of keywords (strings) to search for.

    Returns:
        list: A list of dictionaries, where each dictionary represents a
              matching paper and contains 'title' and 'link' keys.
              Returns an empty list if no matches are found.
    """
    found_papers = []
    # Define the separator between paper entries
    paper_delimiter = (
        "------------------------------------------------------------------------------"
    )
    # Regex to find the arXiv link at the end of a paper section
    # It looks for \ ( link , sizekb)
    link_regex = re.compile(r"\\ \( (https?://arxiv\.org/abs/\S+) ,\s*\d+kb\)")
    # Regex to identify header lines we want to skip when building the abstract
    header_regex = re.compile(
        r"^(arXiv:|Date:|Title:|Authors:|Categories:|Comments:|Journal-ref:|DOI:|ACM-class:|MSC-class:)",
        re.IGNORECASE,
    )

    # Split the email body into sections based on the delimiter
    sections = body.split(paper_delimiter)

    # Convert keywords to lowercase once for efficient comparison
    lower_keywords = [k.lower() for k in keywords]

    for section in sections:
        section = section.strip()
        # Valid paper sections usually start with '\\' followed by arXiv:
        if not section.startswith("\\"):
            continue

        current_title = None
        current_link = None
        abstract_lines = []
        in_abstract = False  # Flag to know when we are past the headers

        lines = section.splitlines()
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:  # Skip empty lines
                continue

            # Find the title
            if line.lower().startswith("title:"):
                current_title = line[len("title:") :].strip()
                in_abstract = True  # Assume abstract starts after title
                continue

            # Find the link using regex (usually near the end)
            link_match = link_regex.search(line)
            if link_match:
                current_link = link_match.group(1)  # Extract the URL part
                in_abstract = False  # Link marks the end of the abstract part
                continue  # Don't add the link line itself to the abstract

            # If we are between title and link, and it's not a known header, collect as abstract
            if in_abstract and current_title and not header_regex.match(line):
                abstract_lines.append(line)

        # Combine abstract lines
        current_abstract = " ".join(abstract_lines).strip()

        # Perform keyword matching if we have title, abstract, and link
        if current_title and current_abstract and current_link:
            title_lower = current_title.lower()
            abstract_lower = current_abstract.lower()

            for keyword in lower_keywords:
                # Check if keyword is in title OR abstract
                if keyword in title_lower or keyword in abstract_lower:
                    logging.info(
                        f"    Found match: Keyword '{keyword}' in title/abstract of '{current_title}'"
                    )
                    found_papers.append({"title": current_title, "link": current_link})
                    break  # Found a match for this paper, no need to check other keywords

    return found_papers


# --- Function to Write Matches to File ---
def write_results(matches, filename):
    """
    Writes the found paper titles and links to a text file.

    Args:
        matches (list): A list of dictionaries [{'title': ..., 'link': ...}].
        filename (str): The path to the output file.
    """
    logging.info(f"\nWriting {len(matches)} matches to '{filename}'...")
    try:
        with open(filename, "w", encoding="utf-8") as f:
            if not matches:
                f.write("No matching papers found in the processed emails.\n")
                logging.info("No matching papers found.")
                return

            f.write("# arXiv Papers Matching Your Keywords\n")
            f.write(
                f"# Processed on: {email.utils.formatdate(localtime=True)}\n\n"
            )  # Add timestamp

            for i, match in enumerate(matches):
                f.write(f"Match {i + 1}:\n")
                f.write(f"  Title: {match['title']}\n")
                f.write(f"  Link: {match['link']}\n\n")

        logging.info(f"Successfully wrote {len(matches)} matches to '{filename}'.")

    except IOError as e:
        logging.error(f"Error writing results to file '{filename}': {e}", exc_info=True)
    except Exception as e:
        logging.error(
            f"An unexpected error occurred during file writing: {e}", exc_info=True
        )


if __name__ == "__main__":
    logging.info("--- arXiv Email Parser ---")

    logging.info("Reading credentials from environment variables...")
    user_email = os.environ.get("GMAIL_ADDRESS")
    user_password = os.environ.get("GMAIL_APP_PASSWORD")

    if not user_email or not user_password:
        logging.error(
            "Error: Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD environment variables."
        )
        logging.error("set GMAIL_APP_PASSWORD=yourapppassword")
        logging.error("Exiting due to missing credentials.")
        exit(1)
    else:
        logging.info(f"Using email address: {user_email}")

    # 2. Load Keywords
    keywords = load_keywords(keywords_file)
    if keywords is None:
        # Stop if keywords couldn't be loaded
        exit()

    # 3. Connect to Gmail
    logging.info(f"\nConnecting to {gmail_imap_host}...")
    try:
        # Connect using SSL for security
        mail = imaplib.IMAP4_SSL(gmail_imap_host, gmail_imap_port)
        logging.info("Connection successful.")

        # 4. Login
        logging.info(f"Logging in as {user_email}...")
        mail.login(user_email, user_password)
        logging.info("Login successful.")

        all_matches = []  # List to store all found papers (title, link)

        try:
            # 5. Select Mailbox
            logging.info("Selecting INBOX...")
            # Use readonly=False to allow marking emails as read
            status, messages = mail.select("INBOX", readonly=False)
            if status != "OK":
                raise imaplib.IMAP4.error("Failed to select INBOX")
            logging.info("INBOX selected.")

            # 6. Construct Search Criteria
            # Search for UNSEEN emails FROM the sender with the specified SUBJECT part
            search_criteria = (
                f'(UNSEEN FROM "{arxiv_sender}" SUBJECT "{email_subject_contains}")'
            )
            logging.info(f"Searching for emails with criteria: {search_criteria}")

            # 7. Search for Emails (using UID)
            status, uid_data = mail.uid("search", None, search_criteria)
            if status != "OK":
                raise imaplib.IMAP4.error("Email search failed")

            # uid_data[0] contains a space-separated string of UIDs, e.g., b'10 15 23'
            # If no matches, it's often b''
            uids = uid_data[0].split()
            num_emails = len(uids)
            logging.info(f"Found {num_emails} matching unread emails.")

            # 8. Fetch and Process Emails
            for i, uid in enumerate(uids):
                uid_str = uid.decode("utf-8")  # Convert UID from bytes to string
                logging.info(
                    f"\nProcessing email {i + 1}/{num_emails} (UID: {uid_str})..."
                )

                # Fetch the full email message (RFC822 format)
                status, msg_data = mail.uid("fetch", uid, "(RFC822)")
                if status != "OK":
                    logging.warning(
                        f"  Error fetching email UID {uid_str}. Status: {status}"
                    )
                    continue  # Skip to the next email

                # msg_data is a list containing tuples, the raw email is in msg_data[0][1]
                raw_email = msg_data[0][1]
                # Parse the raw email bytes into an EmailMessage object
                msg = email.message_from_bytes(raw_email)

                # Extract subject and date for info
                subject = msg.get("subject", "N/A")
                date = msg.get("date", "N/A")
                logging.info(f"  Subject: {subject}")
                logging.info(f"  Date: {date}")

                # Get the email body (payload)
                body = ""
                if msg.is_multipart():
                    # If multipart, find the plain text part
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        # Get disposition to ignore attachments
                        content_disposition = str(part.get("Content-Disposition"))

                        if (
                            content_type == "text/plain"
                            and "attachment" not in content_disposition
                        ):
                            try:
                                # Decode the payload
                                body = part.get_payload(decode=True).decode(
                                    "utf-8", errors="replace"
                                )
                                break  # Found the plain text body
                            except Exception as e:
                                logging.error(
                                    f"  Error decoding multipart body part: {e}",
                                    exc_info=True,
                                )
                                body = ""  # Reset body on error
                else:
                    # If not multipart, assume it's plain text
                    try:
                        body = msg.get_payload(decode=True).decode(
                            "utf-8", errors="replace"
                        )
                    except Exception as e:
                        logging.error(
                            f"  Error decoding non-multipart body: {e}", exc_info=True
                        )
                        body = ""

                if not body:
                    logging.warning("Could not extract email body. Skipping.")
                    continue

                matches_in_email = process_email_body(body, keywords)
                all_matches.extend(matches_in_email)

                # 9. Mark Email as Read
                try:
                    logging.info(f"  Marking email UID {uid_str} as read...")
                    status, response = mail.uid("store", uid, "+FLAGS", "\\Seen")
                    if status != "OK":
                        logging.warning(
                            f"  Warning: Could not mark email UID {uid_str} as read. Status: {status}, Response: {response}"
                        )
                    else:
                        logging.info("  Marked as read.")
                except Exception as e:
                    logging.warning(
                        f"  Warning: Error marking email UID {uid_str} as read: {e}",
                        exc_info=True,
                    )

        except imaplib.IMAP4.error as e:
            logging.error(f"\nIMAP Error during processing: {e}", exc_info=True)
        except Exception as e:
            logging.error(
                f"An unexpected error occurred during processing: {e}", exc_info=True
            )
        finally:
            logging.info("Logging out...")
            mail.logout()
            logging.info("Logged out.")

        write_results(all_matches, output_file)

    # --- Keep the error handling for connection/initial login ---
    except imaplib.IMAP4.error as e:
        logging.error(f"IMAP Error occurred: {e}", exc_info=True)
        if "LOGIN failed" in str(e):
            logging.error(
                "Login failed. Please check GMAIL_ADDRESS and GMAIL_APP_PASSWORD environment variables."
            )
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
