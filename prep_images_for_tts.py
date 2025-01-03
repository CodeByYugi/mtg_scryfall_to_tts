import os
import imageio.v3 as iio
from skimage.util import montage
from pathlib import Path
from dotenv import load_dotenv


def read_image_files_from_folder(folder_path: str) -> list:
    """Function that parses a folder containing image files and concatenates them into a list
    
    Parameters
    ------
    folder_path (str) -- path to folder containing image files

    Returns
        list of numpy arrays for each image file loaded
    """
    list_of_images = list()
    for file in Path(folder_path).iterdir():
        if not file.is_file():
            continue

        list_of_images.append(iio.imread(file))
    
    return list_of_images


def generate_image_montage(
        images: list, output_folder: str, output_filename: str,
        montage_grid: tuple=(7,10), montage_channel_axis: int=3
    ) -> None:
    """Function that combines images from list into a single montage.

    Parameters
    ------
    images (list) -- list of numpy arrays representing image data
    output_folder (str) -- path to folder where ontage image is to be saved
    output_filename (str) -- filename for montage image output
    montage_grid (tuple) -- tuple of (n_rows, n_cols) for montage image (default: (7, 10))
    montage_channel_axis (int) -- axis for colour information needed by scikit.util.montage (default: 3)
    """
    image_montage = montage(images, grid_shape=montage_grid, channel_axis=montage_channel_axis)
    iio.imwrite(f'{output_folder}/{output_filename}.jpg', image_montage)


load_dotenv()

loaded_images = read_image_files_from_folder(folder_path=os.environ.get('MONTAGE_IMAGE_INPUT_DIR'))

generate_image_montage(
    images=loaded_images,
    output_folder=os.environ.get('MONTAGE_IMAGE_OUTPUT_DIR'),
    output_filename=os.environ.get('SET_CODE')
)