"""
Parse text file in line format:
Question 1///Answer 1a///Answer 1b///Answer 1c///Answer 1d***Answer1***Answer2***
    into tuples: question, tuple_of_answer_choices, tuple_of_solutions

Tuples can then be passed into a formatting or storage format:

for question_text, question_answers in parse_text_file(text_file_name):
    # do whatever
        ->store in dict {question_text: list_of_answers}
            -dict form could use iteration through keys to output
        ->store in database or object
"""


def extract_q_and_a(line: str):
    """
    Takes question string (line from file), returns question text as a string
    and a tuple of answer choices.

    :param line: str
    :return: str, tuple: question, answer_choices
    """
    q_and_a = line.split('///')
    # q_and_a[0] is question, q_and_a[-1] is answers
    question = q_and_a[0].strip(' ')
    answer_choices = tuple([x.strip() for x in q_and_a[1:-1] if x != ''])
    return question, answer_choices


def extract_solution(line: str):
    """
    Takes question string (line from file), returns solution/s as tuple.

    :param line: str
    :return: tuple
    """
    if '***' in line:
        solution_sep = line.split('***')
        return tuple([x.strip() for x in solution_sep[1:] if x != ''])
    else:
        return None


def parse_question(line: str):
    """
    Takes line of a text file with the form:
    Question 1///Answer 1a///Answer 1b///Answer 1c***correct***ans***
    and returns question string, tuples of answers and solution

    :param line: line of text file containing question text
    :return: str, tuple, tuple: question, tuple_answers, tuple_solutions or None
    """
    question, answer_choices = extract_q_and_a(line)
    solution = extract_solution(line)

    return question, answer_choices, solution


def parse_text_file(question_filename):
    """
    Takes questions from none-empty lines of a text file with the form:
    Question 1///Answer 1a///Answer 1b///Answer 1c***correct***ans***etc
        and yields question string, tuples of answers and solution

    :param question_filename: filepath/filename of text file
    :yield: str, tuple, tuple question, tuple_of_answers, tuple_of_solutions
    """
    with open(question_filename) as f:
        for line in f.readlines():
            if line[-1:] == '\n':  # Strip newlines
                line = line[:-1]
            if line == '':
                continue
            question, answer_choices, solution = parse_question(line)
            yield question, answer_choices, solution


if __name__ == '__main__':

    text_file_name = input('Path_to_text_file\\filename: ')
    for question_text, answer_choices, solution in parse_text_file(text_file_name):
        print(f'Question: {question_text}\nAnswer choices: {answer_choices}\n Solution: {solution}\n')
