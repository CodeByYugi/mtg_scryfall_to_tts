import os
from dotenv import dotenv_values
from scryfall import parse_set, download_card_images_by_parsing_dict
from generate_tts_montage import parse_set_image_folders, read_image_files_from_folder, generate_image_montage


if __name__ == "__main__":
    # load configuration from .env file
    config = dotenv_values(".env")
    # get set code from config
    set_code = config.get("SET_CODE")
    # get output directory from config
    img_dir = f'{config.get("OUTPUT_ROOT_DIR")}/{set_code}'

    # check if set image files need to be downloaded
    if config.get("SOURCE_IMAGES") == 'True':
        # get API root URL from config
        root_url = config.get("SCRYFALL_API_URL")
        # parse Scryfall for set code and compile card information
        list_of_set_cards = parse_set(root_url, set_code)
        # download card images and store to output directory
        download_card_images_by_parsing_dict(set_dict=list_of_set_cards, output_dir=img_dir)

    # check if montage generation needed
    if config.get("GENERATE_MONTAGE") == 'True':
        # parse set image folders
        parse_set_image_folders(source_dir=img_dir, set_code=set_code)
