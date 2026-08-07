import errno
import os
import re
import shutil
import unicodedata
import requests


def parse_response_warnings(response):
    print(
        f"URL: {response.url}\n"
        f"Status code: {response.status_code}\n"
        f"Reason: {response.reason}\n"
        f"Detail: {response.text}\n"
    )


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


def get_cards_from_print_sets(
        root_url:str, headers:dict, set_code: str,
        rarity: str|None=None, collector_numbers: list|None=None
    ) -> dict:
    """Function that returns unique card names for a given set code and rarity.

    Parameters
    root_url (str) -- base URL for Scryfall API
    headers (dict) -- HTTP request headers
    set_code (str) -- three-letter set code to identify
        the magic set in question (e.g. DSK)
    rarity (str or None) -- optional filter for card rarity,
        possible values include 'c', 'u', 'r', 'm' (default: None)
    collector_numbers (list or None) -- if a list of two numbers are passed,
        the scryfall search will limit the range of cards
        to the given range of collector numbers. If omitted, the scryfall
            search option is:booster is used instead.
    """
    # if collector number range given, use to determine draft card range
    if collector_numbers is not None:
        url = f"{root_url}/cards/search?q=set%3A{set_code}+cn≥{collector_numbers[0]}+cn≤{collector_numbers[1]}+r%3D{rarity}"
        r = requests.get(url, headers=headers)
    # otherwise use scryfall filter of "is:booster" to determine draft cards
    else:
        url = f"{root_url}/cards/search?q=set%3A{set_code}+is:booster+r%3D{rarity}"
        r = requests.get(url, headers=headers)
    
    if r.status_code == 200:
        return r.json().get('data')
    else:
        print(f"WARNING! Could not get {rarity} for set code {set_code}.\n")
        parse_response_warnings(r)
    return None


def parse_set_by_rarity(
        root_url:str, headers:dict, set_code: str, collector_numbers: list|None=None
    ) -> dict:
    """Function to parse a Magic set on Scryfall for cards by rarity.

    Parameters
    ------
    root_url (str) -- base URL for Scryfall API
    headers (dict) -- HTTP request headers
    set_code (str) -- three-letter set code denoting the set
    collector_numbers (list or None) -- if a list of two numbers are passed,
        the scryfall search will limit the range of cards to the given range of
        collector numbers. If omitted, the scryfall search option is:booster is
        used instead.

    Returns
        (dict) dictionary of card objects from Scryfall API by rarity
    """
    set_dict = dict()

    for rarity in ['common', 'uncommon', 'rare', 'mythic']:
        card_objects = get_cards_from_print_sets(
            root_url=root_url, headers=headers, set_code=set_code,
            rarity=rarity, collector_numbers=collector_numbers
        )
        if card_objects is not None:
            set_dict[rarity] = card_objects
    
    return set_dict


def get_set_basics(root_url:str, headers:dict, set_code: str) -> dict:
    """Function to get basic lands for a given set code.

    Parameters
    ------
    root_url (str) -- base URL for Scryfall API
    headers (dict) -- HTTP request headers
    set_code (str) -- three-letter set code denoting the set

    Returns
        (dict) dictionary of basic land card objects from Scryfall API
    """
    url = f"{root_url}/cards/search?q=set%3A{set_code}+t:basic"
    r = requests.get(url, headers=headers)
    
    if r.status_code == 200:
        return r.json().get('data')
    else:
        print(f"WARNING! Could not get basics for set code {set_code}.\n")
        parse_response_warnings(r)
    return None


def parse_set(
        root_url:str, headers:dict, set_code: str, collector_numbers: list|None=None
    ) -> dict:
    """Function to parse a Magic set on Scryfall for unique cards.

    Parameters
    ------
    root_url (str) -- base URL for Scryfall API
    headers (dict) -- dictionary of HTTP request headers
    set_code (str) -- three-letter set code denoting the set
    collector_numbers (list or None) -- if a list of two numbers are passed,
        the scryfall search will limit the range of cards to the given range of
        collector numbers. If omitted, the scryfall search option is:booster is
        used instead.

    Returns
        (dict) dictionary of card objects from Scryfall API
    """
    # parse set cards by rarity
    set_dict = parse_set_by_rarity(
        root_url=root_url, headers=headers,
        set_code=set_code, collector_numbers=collector_numbers,
    )
    # Add basic lands to the set dictionary
    set_dict['basics'] = get_set_basics(root_url=root_url, headers=headers, set_code=set_code)

    return set_dict

def download_card_image_from_url(image_uri: str, headers:dict, file_path: str) -> None:
    """Function to download card image JPEG from Scryfall by scryfall image uri

    Parameters
    ------
    image_uri (str) -- uri to card image on scryfall
    headers (dict) -- HTTP request header
    file_path (str) -- output file path to save image (.jpg) to
    """
    r = requests.get(image_uri, headers=headers, stream=True)

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
    else:
        print("WARNING!!! Image could not be donwloaded!")
        parse_response_warnings(r) 


def download_card_images_by_parsing_dict(
        set_dict: dict, output_dir:str, headers:dict
    ) -> None:
    """Function that parses over a grouped dictionary of scryfall card objects.
    
    Dictionary grouping could for example be by rarity, the dictionary grouping
    will translate into subfolders in the specified output directory where card
    images will be stored.

    headers (dict) -- HTP Request headers
    """
    for key, item in set_dict.items():
        for card_object in item:
            # single-faced cards will have image_uris as key
            if card_object.get('image_uris') is not None:
                filename=f"{output_dir}/{key}/{convert_card_name_to_slug(card_object.get('name'))}.jpg"
                download_card_image_from_url(
                    card_object.get('image_uris').get('large'),
                    headers,
                    filename,
                )
            # double-faced cards have info for each side nested in 'card_faces'
            elif card_object.get('card_faces') is not None:
                # for each card face extract name and image
                for card_face in card_object.get('card_faces'):
                    filename=f"{output_dir}/{key}/{convert_card_name_to_slug(card_face.get('name'))}.jpg"
                    download_card_image_from_url(
                        card_face.get('image_uris').get('large'),
                        headers,
                        filename,
                    )
            else:
                raise AttributeError(
                    f"card object {card_object.get('name')} does not have "
                    f"attributes image_uris or card_faces!"
                )
