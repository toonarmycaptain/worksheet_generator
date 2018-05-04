"""
Base text output format:

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




if __name__ == '__main__':

    rel_path = '..\\..\\generated_worksheets'

    input_filename = input('Please input path of text file to parse: ')

    output_filename = input('Please select output filename: ')

    output_path = os.path.join(rel_path, output_filename)

    output_questions = [x for x in parse_text.generate_questions(input_filename)]

    with open(output_path, 'w') as output_file:

        for question in output_questions:
            output_file.write(f'Question {output_questions.index(question) + 1}: {question.question_text}')
            output_file.write('\n')
            if question.answers:
                for answer in question.answers:
                    output_file.write(f'Answer {question.answers.index(answer) + 1}: {answer} ')
                output_file.write('\n')
            output_file.write('\n\n')
