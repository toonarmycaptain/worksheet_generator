"""
Create pdf from pure text questions.

Currently draft state with limited functionality.

Needs options around lines to write on, blank space between questions, etc.

"""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from worksheet_generator.output_generators.file_save_functions import check_add_file_extension


def save_pdf(worksheet_html: str, filename: str, location: str = '../../../generated_worksheets'):
    """
    Saves generated HTML to pdf in the specified location.

    :param worksheet_html: str
    :param filename: str
    :param location: str
    :return: None
    """
    filename = check_add_file_extension(filename, file_extension='.pdf')
    write_target = Path(location, filename)

    HTML(string=worksheet_html).write_pdf(write_target)


if __name__ == '__main__':
    # this workflow should be a test

    import worksheet_generator.question_class as question_class
    import worksheet_generator.input_parsers.parse_text as parse_text
    from worksheet_generator.output_generators.pdf_output.abc_ord import a_to_z as ordinal_abc

    import os
    import sys

    os.chdir(os.path.dirname(sys.argv[0]))
    print(os.getcwd())

    # read test_test_questions
    worksheet_q_list = []

    text_file_name = Path('../../../worksheet_generator/input_parsers', 'test_text_questions.txt')
    for question_text, answer_choices, solution in parse_text.parse_text_file(text_file_name):
        worksheet_q_list.append(question_class.TextQ(question_text, answer_choices, solution))

    env = Environment(
        loader=FileSystemLoader('./PDF_templates'), autoescape=True
    )

    template = env.get_template("draft_single_column_pdf.jinja2.template")  # TODO: factor template fetch into function

    # TODO: factor template dict into function, possibly drawing needed data based on chosen template
    template_vars = {"title": "Test worksheet",
                     "question_list": worksheet_q_list,
                     "ordinal_abc": ordinal_abc
                     }

    # render html of these questions
    html_out = template.render(template_vars)

    # render pdf from html
    save_pdf(html_out, 'test_text_worksheet3')  # TODO: check for folder existence and create if doesn't exist
