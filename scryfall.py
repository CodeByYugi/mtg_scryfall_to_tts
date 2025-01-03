import os
import errno
import requests
import shutil
import unicodedata
import re
from dotenv import load_dotenv


def convert_card_name_to_slug(card_name: str) -> str:
    """Function to convert arbitrary card name into a filename-safe name.

    Parameters
    -------
    card_name (str) -- original card name
    
    Returns
        (str) filename-safe conversion of original card name
    """
    slug_card_name = (
        unicodedata.normalize("NFKD", str(card_name))
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    slug_card_name = re.sub(r"[^\w\s-]", "", slug_card_name.lower())
    slug_card_name = re.sub(r"[-\s]+", "-", slug_card_name).strip("-_")

    return slug_card_name


def get_cards_from_print_sets(set_code: str, rarity: str|None=None) -> dict:
    """Function that returns unique card names for a given set code and rarity.

    Parameters
    set_code (str) -- three-letter set code to identify the magic set in question (e.g. DSK)
    rarity (str or None) -- optional filter for card rarity, possible values include 'c', 'u', 'r', 'm' (default: None)
    """
    r = requests.get(f"{root_url}/cards/search?q=set%3A{set_code}+is:booster+r%3D{rarity}")
    
    if r.status_code == 200:
        return r.json().get('data')
    
    return None


def parse_set_by_rarity(set_code: str) -> dict:
    """Function to parse a Magic set on Scryfall for unique cards contained in booster packs by rarity.

    Parameters
    ------
    set_code (str) -- three-letter set code denoting the set

    Returns
        (dict) dictionary of card objects from Scryfall API by rarity
    """
    set_dict = dict()

    for rarity in ['common', 'uncommon', 'rare', 'mythic']:
        card_objects = get_cards_from_print_sets(set_code=set_code, rarity=rarity)
        if card_objects is not None:
            set_dict[rarity] = card_objects
    
    return set_dict


def download_card_image_from_url(image_uri: str, file_path: str) -> None:
    """Function that downloads a card image JPEG from Scryfall for a given scryfall image uri.

    Parameters
    ------
    image_uri (str) -- uri to card image on scryfall
    file_path (str) -- output file path to save image (.jpg) to
    """
    r = requests.get(image_uri, stream=True)

    if r.status_code == 200:
        if not os.path.exists(os.path.dirname(file_path)):
            try:
                os.makedirs(os.path.dirname(file_path))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        with open(file_path, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f) 


def download_card_images_by_parsing_dict(set_dict: dict, output_dir:str) -> None:
    """Function that parses over a grouped dictionary of scryfall card objects.
    
    Dictionary grouping could for example be by rarity, the dictionary grouping will translate into subfolders
    in the specified output directory where card images will be stored.
    """
    for key, item in set_dict.items():
        for card_object in item:
            filename=f"{output_dir}/{key}/{convert_card_name_to_slug(card_object.get('name'))}.jpg"
            download_card_image_from_url(card_object.get('image_uris').get('large'), filename)


load_dotenv()

root_url = "https://api.scryfall.com"
set_code = os.environ.get("SET_CODE")

img_out_dir = f'{os.environ.get("OUTPUT_ROOT_DIR")}/{set_code}'

list_of_set_cards_by_rarity = parse_set_by_rarity(set_code)

download_card_images_by_parsing_dict(set_dict=list_of_set_cards_by_rarity, output_dir=img_out_dir)
