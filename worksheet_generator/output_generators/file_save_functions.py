"""
Helper functions for saving worksheets and files.
"""
from pathlib import Path
from typing import Union


def check_add_file_extension(filename: Union[str, Path], file_extension: str='.pdf'):
    """
    Checks whether supplied filename has the supplied extension, and
    adds or replaces with the supplied extension if necessary.

    :param filename: str
    :param file_extension: str
    :return: Path
    """
    filename_path = Path(filename)
    if filename_path.suffix != file_extension:  # check period? Probably unnecessary if file_format not user-input
        filename_path = filename_path.with_suffix(file_extension)

    return filename_path


def make_full_path(folder_path: str, filename: str):
    """
    Takes folder path and filename and concatenates into os agnostic full path.

    :param folder_path: str - with forward slashes.
    :param filename: str
    :return: class 'pathlib.PosixPath'
    """
    folder = Path(folder_path)

    return folder / filename


def check_file_path_name():
    """
    check filepath and filename for existence/nonexistence.
    :return:
    """
    if check_filepath():
        if check_filename():
            return True
    return False


def check_filepath():
    """ check file path for existence, create if doesn't exist?
    """
    pass


def check_filename():
    """check filename for existence"""
    pass
    # return not filename_exists
