"""
Parse text file in line format:
Question 1///Answer 1a///Answer 1b///Answer 1c///Answer 1d
    into tuples: question, list_of_answers

Tuples can then be passed into a formatting or storage format:

for question_text, answers in parse_text_file(text_file_name):
    # do whatever
        ->store in dict {question_text: list_of_answers}
            -dict form could use iteration through keys to output
        ->store in database or object
"""
def parse_text_file(question_filename):
    """
    Takes questions from lines of a text file with the form:
    Question 1///Answer 1a///Answer 1b///Answer 1c///Answer 1d
        and returns tuples of question and answers

    :param question_filename: filepath\filename of text file
    :yield: tuple (question, list_of_answers)
    """
    with open(question_filename) as f:
        for line in f.readlines():
            if line[-1:] == '\n':  # Strip newlines
                line = line[:-1]
            if line == '':
                continue
            if line == '':
                print("line was ''")
            q_and_a = line.split('///')

            yield q_and_a[0], [x for x in q_and_a[1:] if x != '']



if __name__ == '__main__':
    import os
    os.chdir('C:\\Users\\david\\OneDrive\\Programming\\PycharmProjects\\worksheet_generator\\input_parsers')
    text_file_name = input('Path_to_text_file\\filename: ')
    for question_text, answers in parse_text_file(text_file_name):
        print(f'Question: {question_text}, Answers: {answers}')
