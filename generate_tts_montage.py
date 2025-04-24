from functools import reduce
import imageio.v3 as iio
from skimage.util import montage
from pathlib import Path


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


def parse_set_image_folders(source_dir:str, set_code:str) -> None:
    """Function that parses a folder for default set image subfolders and creates montages
    
    Parameters
    ------
    source_dir (str) -- path to root folder containing default set image subfolders
    set_code (str) -- set code for the set being processed
    """
    for folder in Path(source_dir).iterdir():
        # skip if not a folder
        if not folder.is_dir():
            continue
        # load image files from folder
        loaded_images = read_image_files_from_folder(folder_path=folder)
        # generate montage(s)
        generate_image_montage(
            images=loaded_images,
            output_folder=source_dir,
            output_filename=f'{set_code}_{folder.name}'
        )


def generate_image_montage(
        images: list, output_folder: str, output_filename: str,
        montage_grid: tuple=(7,10), montage_channel_axis: int=3
    ) -> None:
    """Function that combines images from list into montages of a given max grid size.

    Parameters
    ------
    images (list) -- list of numpy arrays representing image data
    output_folder (str) -- path to folder where ontage image is to be saved
    output_filename (str) -- filename for montage image output
    montage_grid (tuple) -- tuple of (n_rows, n_cols) for montage image (default: (7, 10))
    montage_channel_axis (int) -- axis for colour information needed by scikit.util.montage (default: 3)
    """
    # establish maximum image count per montage grid (less 1 to leave last card blank as per TTS requirements)
    max_image_count = reduce(lambda nrows, ncols: nrows*ncols, montage_grid)-1
    # chunk image list into small enough groups to fit into montage grid
    chunked_images = [images[i:i + max_image_count] for i in range(0, len(images), max_image_count)]
    # plot each chunk into a montage and export
    for chunk_num, chunk_images in enumerate(chunked_images):
        image_montage = montage(chunk_images, grid_shape=montage_grid, channel_axis=montage_channel_axis)
        if len(chunked_images) > 1:
            iio.imwrite(f'{output_folder}/{output_filename}_{chunk_num}.jpg', image_montage)
        else:
            iio.imwrite(f'{output_folder}/{output_filename}.jpg', image_montage)
