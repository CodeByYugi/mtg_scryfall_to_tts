from dotenv import dotenv_values
from scryfall import parse_set, download_card_images_by_parsing_dict
from generate_tts_montage import parse_set_image_folders


if __name__ == "__main__":
    # load configuration from .env file
    config = dotenv_values(".env")
    # get set code from config
    set_code = config.get("SET_CODE")
    # get collector numbers (if set)
    collector_number_range = None
    cn_min = config.get("CN_MIN")
    cn_max = config.get("CN_MAX")
    if (cn_min is not None) and (cn_max is not None):
        collector_number_range = [cn_min, cn_max]
    # get output directory from config
    img_dir = f'{config.get("OUTPUT_ROOT_DIR")}/{set_code}'

    # check if set image files need to be downloaded
    if config.get("SOURCE_IMAGES") == 'True':
        # get API root URL from config
        root_url = config.get("SCRYFALL_API_URL")
        request_headers = {
            'User-Agent': config.get("HEADER_USER_AGENT"),
            'Accept': config.get("HEADER_ACCEPT"),
        }
        # parse Scryfall for set code and compile card information
        list_of_set_cards = parse_set(
            root_url, request_headers, set_code,
            collector_numbers=collector_number_range
        )
        # check if set dictionary is empty
        if not list_of_set_cards:
            raise ValueError(
                f"Set dictionary is empty for set code: {set_code}. "
                "Check if set code is valid or if collector number range is correct."
            )
        # download card images and store to output directory
        download_card_images_by_parsing_dict(
            set_dict=list_of_set_cards, output_dir=img_dir,
            headers=request_headers,
        )

    # check if montage generation needed
    if config.get("GENERATE_MONTAGE") == 'True':
        # parse set image folders
        parse_set_image_folders(source_dir=img_dir, set_code=set_code)
