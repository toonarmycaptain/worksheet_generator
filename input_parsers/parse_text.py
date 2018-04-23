"""
Parse text file in line format:
Question 1///Answer 1a///Answer 1b///Answer 1c///Answer 1d***Answer1***Answer2***
    into tuples: question, tuple_of_answer_choices, tuple_of_correct_answers

Tuples can then be passed into a formatting or storage format:

for question_text, question_answers in parse_text_file(text_file_name):
    # do whatever
        ->store in dict {question_text: list_of_answers}
            -dict form could use iteration through keys to output
        ->store in database or object
"""
def parse_text_file(question_filename):
    """
    Takes questions from lines of a text file with the form:
    Question 1///Answer 1a///Answer 1b///Answer 1c***correct***ans***
        and yields question string, tuples of answers and correct answers

    :param question_filename: filepath\filename of text file
    :yield: str, tuple, tuple question, tuple_of_answers, tuple_correct_answers
    """
    with open(question_filename) as f:
        for line in f.readlines():
            if line[-1:] == '\n':  # Strip newlines
                line = line[:-1]
            if line == '':
                continue


            if '***' in line:
                answer_sep = line.split('***')
                answers = tuple([x.strip() for x in answer_sep[1:] if x != ''])
            else:
                answers = None

            q_and_a = line.split('///')
            # q_and_a[0] is question, q_and_a[-1] is answers
            question = q_and_a[0].strip(' ')
            answer_choices = tuple([x.strip() for x in q_and_a[1:-1] if x != ''])

            yield question, answer_choices, answers


if __name__ == '__main__':

    text_file_name = input('Path_to_text_file\\filename: ')
    for question_text, answer_choices, answers in parse_text_file(text_file_name):
        print(f'Question: {question_text}\nAnswer choices: {answer_choices}\nCorrect answer/s: {answers}')
