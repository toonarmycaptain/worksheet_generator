from pathlib import Path

import pytest

from worksheet_generator.output_generators.file_save_functions import check_add_file_extension


class TestCheckAddFileExtension:
    @pytest.mark.parametrize(
        'test_filename, test_extension,'
        ' returned_object',
        [('test_filename_str', '.test_extension',
          Path('test_filename_str.test_extension')),  # String input
         (Path('test_filename_path'), '.test_extension',
          Path('test_filename_path.test_extension')),  # Path obj input
         ]
    )
    def test_check_add_file_extension_file_without_extension(self,
                                                             test_filename,
                                                             test_extension,
                                                             returned_object):
        assert check_add_file_extension(test_filename, test_extension) == returned_object

    @pytest.mark.parametrize(
        'test_filename, test_extension,'
        ' returned_object',
        [('test_filename_str.test_extension', '.test_extension',
          Path('test_filename_str.test_extension')),  # String input
         (Path('test_filename_path.test_extension'), '.test_extension',
          Path('test_filename_path.test_extension')),  # Path obj input
         ]
    )
    def test_check_add_file_extension_file_with_extension(self,
                                                          test_filename,
                                                          test_extension,
                                                          returned_object):
        assert check_add_file_extension(test_filename, test_extension) == returned_object

    @pytest.mark.parametrize(
        'test_filename, test_extension,'
        'returned_object',
        [('test_filename_str.test_extension', '.replaced_extension',
          Path('test_filename_str.replaced_extension')),  # String input
         (Path('test_filename_path.test_extension'), '.replaced_extension',
          Path('test_filename_path.replaced_extension')),  # Path obj input
         ]
    )
    def test_check_add_file_extension_file_with_extension_replaced_extension(self,
                                                                             test_filename,
                                                                             test_extension,
                                                                             returned_object):
        assert check_add_file_extension(test_filename, test_extension) == returned_object
