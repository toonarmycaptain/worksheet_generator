"""
Generic/default text output format:

header information (eg author etc)
Title of worksheet
2 blank lines
Question para
blank line
answers
2 blank lines
"""
import os

from worksheet_generator.input_parsers import parse_text

_output_repository = '..\\..\\generated_worksheets'


def generate_text_worksheet(output_filename: str, questions: list, target_path=_output_repository):
    """
    Take filename, question list, path to save file at, generate a text file at
    specified path.
    Return path of created text file.

    :param output_filename: str
    :param questions: list of TextQ question objects
    :param target_path: str
    :return output_path: str
    """
    os.makedirs(target_path, exist_ok=True)

    rel_path = target_path
    output_path = os.path.join(rel_path, output_filename + '.txt')

    # TODO: error handling if file already exists

    spacing = '\n'

    question_answer_spacing = 1 * spacing  # blank lines
    question_question_spacing = 2 * spacing  # blank lines

    with open(output_path, 'w') as output_file:
        for question in questions:
            output_file.write(f'Question {questions.index(question) + 1}: {question.question_text}')
            output_file.write(question_answer_spacing)
            if question.answers:
                for answer in question.answers:
                    output_file.write(f'Answer {question.answers.index(answer) + 1}: {answer} ')
                output_file.write(spacing)  # blank line terminating answers
            output_file.write(question_question_spacing)

    return output_path


if __name__ == '__main__':

    generated_worksheets_folder = '..\\..\\generated_worksheets'

    input_filename = input('Please input path of text file to parse: ')

    test_filename = input('Please select output filename: ')

    output_questions = [x for x in parse_text.generate_questions(input_filename)]

    generate_text_worksheet(test_filename,
                            output_questions,
                            # generated_worksheets_folder+'_chicken' <- additional param tested working.
                            )
