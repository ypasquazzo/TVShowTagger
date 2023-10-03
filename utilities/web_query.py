import json
import logging
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

EPGUIDES_URL = "https://epguides.com/"
IMDB_URL = "https://www.imdb.com/"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/81.0.4044.138 Safari/537.36")
HEADERS = {"User-Agent": USER_AGENT}
TV_SHOWS_FILE = "../utilities/tv_shows_list.json"


def _remove_invalid_characters(filename: str) -> str:
    """Strip invalid characters from a given filename."""
    invalid_characters = r'<>:"/\\|?*'
    cleaned_filename = re.sub(f'[{re.escape(invalid_characters)}]', '', filename)
    return cleaned_filename


def _capitalize_after_special_chars(text: str) -> str:
    """Capitalize the first character after specific special characters in a given text."""
    pattern = r'([.+\( ])\s*([a-z])'

    def replace_func(match):
        return match.group(1) + match.group(2).upper()

    return re.sub(pattern, replace_func, text)


def get_response(url: str, headers: dict = None) -> requests.Response:
    """Fetch a URL and log if there's an issue."""
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logging.warning(f"Failed to fetch data from {url}. Status code: {response.status_code}.")
    return response


def _fetch_start_date(soup: BeautifulSoup) -> str:
    try:
        return soup.find_all(class_="half column")[1].find_all(class_="pads")[1].find('a').text
    except AttributeError:
        logging.warning(f"Attribute error encountered when fetching start date.")
        return soup.find(class_="half column").find_all(class_="pads")[1].find('a').text
    except IndexError:
        logging.warning(f"No start date found for show.")
        return ""


def _fetch_run_time(soup: BeautifulSoup) -> str:
    try:
        return \
            str(soup.find_all(class_="half column")[1].find_all(class_="pads")[1]).split('<br/>')[4].split(': ')[1]
    except (AttributeError, IndexError):
        logging.warning(f"Run time not found for show.")
        return ""


def _fetch_synopsis(soup: BeautifulSoup, name: str) -> str:
    synopsis = soup.find(id="blurb", class_="pads").text.strip()
    if not synopsis:
        logging.info(f"Using IMDB as a fallback for the synopsis of {name}.")
        imdb = soup.find(class_="center titleblock").find('a')["href"]
        soup = WebQuery.fetch_url_content(imdb, HEADERS)
        synopsis = soup.find("span", {"data-testid": "plot-xl"}).text.strip()
    return synopsis or "No synopsis available on Epguides or IMDB."


def _fetch_poster(url: str, soup: BeautifulSoup = None) -> bytes:
    poster_endpoints = ["/cast.jpg", "/logo.jpg"]
    for endpoint in poster_endpoints:
        response = get_response(url + endpoint)
        if response.status_code == 200:
            return response.content

    # Fallback to IMDb for poster
    if not soup:
        soup = WebQuery.fetch_url_content(url)
    imdb = soup.find(class_="center titleblock").find('a')["href"]
    soup = WebQuery.fetch_url_content(imdb, HEADERS)
    poster_url = soup.find(class_="ipc-lockup-overlay ipc-focusable")["href"]
    soup = WebQuery.fetch_url_content(urljoin(IMDB_URL, poster_url), HEADERS)
    image_url = soup.find_all("img")[1]["src"]
    return get_response(image_url).content


def _fetch_episode_data(soup: BeautifulSoup) -> list:
    """Fetch and clean episode names and seasons from the soup."""
    table = soup.find(id="eplist", class_="pads").find('table')
    rows = table.find_all('tr')

    data = []
    for r in rows[2:]:
        season = r.find('td', class_='bold')
        if season:
            data.append(_remove_invalid_characters(season.text.strip()))

        episode = r.find('td', class_='eptitle')
        if episode:
            data.append(_remove_invalid_characters(episode.find('a').text.strip()))

    return data


def _organize_season_data(data: list) -> dict:
    """Organize the fetched episode data into a dictionary structured by seasons."""
    season_data = {}
    episode_counter = 1
    current_season = 0

    for item in data:
        if item.startswith('Season'):
            current_season = item
            season_data[current_season] = []
            episode_counter = 1
        else:
            formatted_episode = "{:02} - {}".format(episode_counter, item)
            season_data[current_season].append(_capitalize_after_special_chars(formatted_episode))
            episode_counter += 1

    return season_data


class WebQuery:
    def __init__(self):
        self.episode_names = {}

    @staticmethod
    def fetch_url_content(url: str, headers: dict = None) -> BeautifulSoup:
        """Fetch content from a URL and return a BeautifulSoup object."""
        response = get_response(url, headers)
        return BeautifulSoup(response.text, "html.parser")

    @staticmethod
    def update_shows():
        logging.info("Starting the update process.")
        alphabet = [chr(i) for i in range(ord('a'), ord('z'))]

        shows_data = {}

        for letter in alphabet:
            soup = WebQuery.fetch_url_content(EPGUIDES_URL + "menu" + letter)
            data = soup.find('div', class_="cont")
            links = [link.find('a') for link in data.find_all('li') if
                     link.text.strip() and not link.text.strip().endswith(" [radio]")]
            shows_data.update({link.text: EPGUIDES_URL + link['href'][3:] for link in links})

        with open(TV_SHOWS_FILE, "w", encoding='utf-8') as json_file:
            json.dump(shows_data, json_file, indent=4)

        logging.info("Finished updating shows.")

    @staticmethod
    def get_info(show: dict) -> dict[str, str, str, str, bytes, str]:
        name = next(iter(show))
        logging.info(f"Fetching details for show: {name}.")
        url = show[name]
        soup = WebQuery.fetch_url_content(url)

        start_date = _fetch_start_date(soup)
        run_time = _fetch_run_time(soup)
        synopsis = _fetch_synopsis(soup, name)
        poster = _fetch_poster(url, soup)

        return {"name": name, "date": start_date, "time": run_time, "synopsis": synopsis, "poster": poster,
                "url": url}

    @staticmethod
    def get_episode_names(url: str):
        logging.info(f"Fetching episode names for the show with URL: {url}.")
        soup = WebQuery.fetch_url_content(url)

        data = _fetch_episode_data(soup)
        season_data = _organize_season_data(data)

        return season_data
