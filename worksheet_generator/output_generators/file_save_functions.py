"""
Helper functions for saving worksheets and files.
"""
from pathlib import Path


def check_add_file_extension(filename: str, file_format: str='.pdf'):
    """
    Checks whether entered filename contains necessary extension, and adds
    appropriate extension if needed.

    :param filename: str
    :param file_format: str
    :return: str
    """
    if filename[:4].lower() is not file_format:  # check period? Probably unnecessary if file_format not user-input
        return filename + file_format


def make_full_path(folder_path: str, filename: str = "test.txt"):
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


if __name__ == "__main__":
    print(type(make_full_path(r"..\OddThinking\Documents\My_Source\Widget", "chicken.txt")))
