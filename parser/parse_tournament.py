import os
import re
import urllib.request
from tqdm import tqdm


def generate_data(tournament_html):
    """
    Read the tournament HTML file, extract links to finished datasets,
    download their HTML, and save it to separate files.

    Args:
        tournament_html (str): Path to the tournament HTML file.

    Raises:
        FileNotFoundError: If the specified tournament HTML file does not exist.
    """
    if not os.path.exists(tournament_html):
        raise FileNotFoundError(f"Tournament HTML file not found: {tournament_html}")

    with open(tournament_html, "r", encoding="utf-8") as tournament:
        data = tournament.readlines()

    start = 0
    for i in range(len(data)):
        if "Finished datasets" in data[i]:
            start = i
            break

    row_matches = []
    pattern = r"https://dltv\.org/matches/\d+"
    for i in range(start, len(data)):
        if ' <a href="https://dltv.org/matches/' in data[i]:
            match = re.findall(pattern, data[i])
            if match:
                row_matches.append(match[0])

    headers = {"User-Agent": "Mozilla/5.0"}

    # Loop through the links
    for link in tqdm(row_matches):
        try:
            # Create the request
            request = urllib.request.Request(link, headers=headers)

            # Download the HTML code
            with urllib.request.urlopen(request) as response:
                html = response.read()

            # Save the HTML code to a file
            with open(
                "parser/matches/" + link.split("/")[-1] + ".html", "w", encoding="utf-8"
            ) as f:
                f.write(html.decode())

        except Exception as e:
            print(f"Error occurred while processing link: {link}")
            print(f"Error message: {str(e)}")


def read_tournament():
    """
    Read tournament files from the "parser/tournaments" directory
    and call the generate_data function for each tournament file.

    Handles UnicodeDecodeError when reading files.

    Raises:
        FileNotFoundError: If the "parser/tournaments" directory does not exist.
    """
    tournament_dir = "parser/tournaments"
    if not os.path.exists(tournament_dir):
        raise FileNotFoundError(f"Tournament directory not found: {tournament_dir}")

    my_files = os.listdir(tournament_dir)
    for filename in my_files:
        try:
            tournament_path = os.path.join(tournament_dir, filename)
            generate_data(tournament_path)
        except Exception as e:
            print(f"Error occurred while processing file: {filename}")
            print(f"Error message: {str(e)}")
