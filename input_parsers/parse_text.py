"""
Parse text file formatted with question, answer choices, solutions, one line per
 question, with question/line format:
Question 1|||Answer 1a///Answer 1b///Answer 1c///Answer 1d***Answer1///Answer2///
    ie question ||| answer choices *** solutions
    ie multiple answers, solutions split by ///
Parser returns question string, list_of_answer_choices, list_of_solutions,
    or None in place if no answer choices, solutions are supplied.

Lists can then be passed into a formatting or storage format:

for question_text, question_answers in parse_text_file(text_file_name):
    # do whatever
        ->store in dict {question_text: list_of_answers}
            -dict form could use iteration through keys to output
        ->store in database or object

TODO: Do testing for more than one Question/answer delimiter ('|||','***') eg if line.count('|||') > 1: throw error
NB Raise error in extract_ functions, log, pass to caller, caller provides feedback to user.

"""


def extract_question(line: str):
    """
    Takes question string (line from file), returns question text as a string.

    :param line: str
    :return: str
    """
    if '|||' in line:
        return line.split('|||')[0].strip()
    return line.strip()


def extract_answers(line: str):
    """
    Takes question string (line from file), returns list of answer choices, or None if no answers are provided.

    :param line: str
    :return: list: answer_choices or None
    """
    if '|||' not in line:
        return None
    answers_sep = line.split('|||')[1].split('***')[0]
    answers = answers_sep.split('///')
    if answers != ['']:
        return [x.strip() for x in answers if x != '' and x.strip() != '']
    return None


def extract_solution(line: str):
    """
    Takes question string (line from file), returns solution/s as list
    Returns None if no solutions are available.

    :param line: str
    :return: list: solutions or None
    """
    if '***' in line:
        solution_sep = line.split('***')[1]
        solutions = solution_sep.split('///')
        if solutions != ['']:
            return [x.strip() for x in solutions if x != '' and x.strip() != '']
    return None


def parse_question(line: str):
    """
    Takes line of a text file with the form:
Question 1|||Answer 1a///Answer 1b///Answer 1c///Answer 1d***Answer1///Answer2///
    and returns question string, lists of answers and solutions, or None if
    no answers/lists are provided.

    :param line: line of text file containing question text
    :return: str, list, list: question, list or None, list or None
    """
    question = extract_question(line)
    answer_choices = extract_answers(line)
    solution = extract_solution(line)

    return question, answer_choices, solution


def parse_text_file(question_filename):
    """
    Takes questions from none-empty lines of a text file with the form:
    Question 1///Answer 1a///Answer 1b///Answer 1c***correct***ans***etc
        and yields question string, lists of answers and solution

    :param question_filename: filepath/filename of text file
    :yield: str, list or None, list or NOne: question, answers, solutions
    """
    with open(question_filename) as f:
        for line in f.readlines():
            if line[-1:] == '\n':  # Strip newlines
                line = line[:-1]
            if line == '':
                continue
            question, answer_choices, solution = parse_question(line)
            yield question, answer_choices, solution
#TODO: add some error checking to give feedback to the user if solution isn't contained in answers'

if __name__ == '__main__':

    text_file_name = input('Path_to_text_file\\filename: ')
    for question_text, answer_choices, solution in parse_text_file(text_file_name):
        print(
		f'Question: {question_text}\nAnswer choices: {answer_choices}\n Solution: {solution}\n'
		)
