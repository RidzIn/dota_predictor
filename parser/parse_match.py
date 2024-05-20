import os
import time

import pandas as pd
import requests
from tqdm import tqdm

from parser.util import pos_reshape_csv

MATCH_COUNT = 0


class MatchParser:
    def __init__(self, match_file_path=None, match_link=None, match_string=None):
        if match_file_path is not None:
            with open(match_file_path, encoding="utf-8") as match_file:
                self.data_match = match_file.readlines()
        elif match_string:
            self.data_match = match_string
        else:
            response = requests.get(match_link)
            temp = response.text

            self.data_match = temp.splitlines()

            print(len(self.data_match))

    def _get_score_list(self):
        """Parse the scores from HTML file and return a list of them."""
        dirty_score = []
        count = 0
        for i in self.data_match:
            if i.find('<div class="team__scores-kills">') != -1:
                count = 1
                continue
            if count == 1:
                dirty_score.append(i)
                count = 0
        score = [i.strip() for i in dirty_score]
        return score

    def get_heroes_list(self):
        """Parse the heroes from HTML file and return a list of them."""
        dirty_data = [
            i
            for i in self.data_match
            if i.find('<div class="pick" data-tippy-content=') != -1
        ]
        without_spaces = [hero.strip() for hero in dirty_data]
        clear_hero_names = [
            i[i.find("data-tippy-content=") + len("data-tippy-content=") + 1 : -2]
            for i in without_spaces
        ]
        for i in range(len(clear_hero_names)):
            if clear_hero_names[i] == "Nature&#039;s Prophet":
                clear_hero_names[i] = "Nature's Prophet"
        return clear_hero_names

    def _get_tournament_and_teams(self):
        """Parse the tournament and teams from HTML file and return a list of them."""
        my_str = ""
        for i in self.data_match:
            if i.find('<meta property="og:title" content="') != -1:
                x = len('<meta property="og:title" content="')
                my_str = i[x + 4 : -5]
                break
        local_team_1 = my_str[: my_str.find(" vs ")].strip()
        local_team_2 = my_str[len(local_team_1) + 4 : my_str.find(" at ")]
        local_tournament = my_str[my_str.find(" at ") + 4 :]
        return [local_team_1, local_team_2, local_tournament]

    def _get_duration_list(self):
        """Parse the durations from HTML file and return a list of them."""
        local_durations = []
        for i in self.data_match:
            if i.find('<div class="info__duration">') != -1:
                start_index = i.find('">') + 2
                end_index = i.find("</div>")
                local_durations.append(i[start_index:end_index])
        return local_durations

    def _get_side_list(self):
        """Parse the side from HTML file and return a list of them."""
        local_side_list = []
        for i in self.data_match:
            if i.find('<span class="side ') != -1:
                start_index = i.find('<span class="side ') + len('<span class="side ')
                end_index = i.find('">')
                local_side_list.append(i[start_index:end_index])
        return local_side_list

    def _get_results(self):
        """Parse the result from HTML file and return a list of them."""
        count = 0
        slices_of_data = []
        number_of_line_found_winner = []
        result_list = []
        for i in self.data_match:
            count += 1
            if i.find('<div class="info__duration">') != -1:
                slices_of_data.append(count)
        for i in range(len(self.data_match)):
            if self.data_match[i].find('<div class="winner">win</div>') != -1:
                number_of_line_found_winner.append(i)
        for i in range(len(slices_of_data)):
            if slices_of_data[i] > number_of_line_found_winner[i]:
                result_list.append("WIN")
                result_list.append("LOSE")
            else:
                result_list.append("LOSE")
                result_list.append("WIN")

        return result_list

    def generate_csv_data_map(self):
        """Generate CSV data from parsed match data."""

        def get_team(map_index):
            if map_index % 2 == 1:
                return self.tournament_and_teams[0]
            return self.tournament_and_teams[1]

        global MATCH_COUNT
        MATCH_COUNT += 1
        str_representation_of_row_in_csv = ""
        results = self._get_results()
        side_list = self._get_side_list()
        duration_list = self._get_duration_list()
        score_list = self._get_score_list()
        heroes_list = self.get_heroes_list()
        self.tournament_and_teams = self._get_tournament_and_teams()

        for i in range(1, len(results) + 1):
            pick = ""
            for j in range(1, 6):
                pick += heroes_list[5 * i - j] + ","
            str_representation_of_row_in_csv += (
                str(MATCH_COUNT)
                + ","
                + str((i - 1) // 2 + 1)
                + ","
                + self.tournament_and_teams[2]
                + ","
                + get_team(i)
                + ","
                + side_list[i - 1]
                + ","
                + score_list[i - 1]
                + ","
                + results[i - 1]
                + ","
                + duration_list[(i - 1) // 2]
                + ","
                + pick[:-1]
                + "\n"
            )

        return str_representation_of_row_in_csv


def read_match(file_name_to_save="test"):
    """
    Read match files from the "parser/datasets" directory, process them,
    and generate a data files with the extracted data.

    Args:
        file_name_to_save (str): The name of the CSV file to be saved.

    Raises:
        FileNotFoundError: If the "parser/datasets" directory does not exist.
    """
    match_dir = "parser/matches"
    if not os.path.exists(match_dir):
        raise FileNotFoundError(f"Match directory not found: {match_dir}")

    my_files = os.listdir(match_dir)
    my_data = []

    for filename in tqdm(my_files):
        try:
            time.sleep(1)
            match_parser = MatchParser(os.path.join(match_dir, filename))
            match = match_parser.generate_csv_data_map()
            match = match.split("\n")
            for j in match:
                if len(j) > 10:
                    my_data.append(j)
        except UnicodeDecodeError:
            print(f"Couldn't read the file: {filename.upper()}")
        except Exception as e:
            print(f"Error occurred while processing file: {filename}")
            print(f"Error message: {str(e)}")

    columns = [
        "MATCH_ID",
        "MAP",
        "TOURNAMENT",
        "TEAM",
        "SIDE",
        "SCORE",
        "RESULT",
        "DURATION",
        "HERO_1",
        "HERO_2",
        "HERO_3",
        "HERO_4",
        "HERO_5",
    ]

    data = [list(i.replace(", ", "").split(",")) for i in my_data]

    df = pd.DataFrame(data, columns=columns)
    df.to_csv(os.path.join("parser/generated_data", file_name_to_save), index=False)

    pos_reshape_csv(
        os.path.join("parser/generated_data", file_name_to_save), is_reshaped=False
    )
    pos_reshape_csv(
        os.path.join("parser/generated_data", file_name_to_save), is_reshaped=True
    )

