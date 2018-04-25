# much code can be improved by using a datastructe.

def ordinal(num):
    """
    Take number and return the ordinal st, nd, th.
    :num: int
    :return: str
    """
    num_str = str(num)

    SUFFIXES = {1: 'st', 2: 'nd', 3: 'rd'}
    # Check for 11-14 because those are abnormal
    if int(num_str[-2:]) > 10 and int(num_str[-2:]) < 14:
        return 'th'
    else:
        suffix = SUFFIXES.get(int(num_str[-1:]), 'th')
    return suffix


def test_format_1(num):
    """
    Generates test questions to write to a text file.
    Questions are as strings, answers in a list.

    Returns long string in the format:

    Question 1: This is the 1st question.///Answer 1a///Answer 1b///Answer 1c///Answer 1d
    Question 2: This is the 2nd question.///Answer 2a///Answer 2b///Answer 2c///Answer 2d


    :num: int
    :return: str
    """
    return_string =''
    for i in range(1, num+1):
        return_string += f'Question {i}: This is the {i}{ordinal(i)} question.'
        return_string += ''
        for j in ['a', 'b', 'c', 'd']:
            return_string += (f'///Answer {i}{j}')
        return_string += '\n'

    return return_string

if __name__ == '__main__':
    n = int(input('Generate how many questions? '))
    print(test_format_1(n))
