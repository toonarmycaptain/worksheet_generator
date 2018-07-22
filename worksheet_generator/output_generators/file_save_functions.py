"""
Helper functions for saving worksheets and files.
"""


def check_add_file_extension(filename, file_format='.pdf'):
    """
    Checks whether entered filename contains necessary extension, and adds
    appropriate extension if needed.

    :param filename: str
    :param file_format: str
    :return: str
    """
    if filename[:4].lower() is not file_format:  # check period? Probably unnecessary if file_format not user-input
        return filename + file_format