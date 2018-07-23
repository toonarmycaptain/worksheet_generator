"""
Helper functions for saving worksheets and files.
"""


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
