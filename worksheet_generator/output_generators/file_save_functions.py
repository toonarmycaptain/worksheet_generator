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
