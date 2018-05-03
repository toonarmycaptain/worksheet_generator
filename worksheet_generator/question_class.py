"""
Question classes

"""


class Question:
    """
    Base Question class

    Attributes:
        question: The question.
        answers: Possible answers to choose from.
        solution: The correct answer/s to the question.
    """
    pass


class TextQ(Question):
    """
    Question class with question and answers solely composed of text.


    # for more than one answer, use tuple, or slice? This will output a list
    # eg answers = [1, 2, 3, 4] => correct = [1:4:2] => correct >>> [2, 4]


    """
    def __init__(self,
                 question_text: str,
                 answers: list=None,
                 solution: list=None):
        self.question_text = question_text
        self.answers = answers
        self.solution = solution
        # for use with 'in range(num_answers) or in range(num_solutions
        self.num_answers = None if not answers else len(answers) + 1
        self.num_solutions = None if not solution else len(solution) + 1
        # assert all solutions  are in the answer choices
        if solution and answers:
            assert (
                set(solution) & set(answers) == set(solution)
            ), "Answer not in answer choices."

if __name__ == '__main__':

    # They may need to be decorated to enable correction/modification via GUI

    # ?Need method for answers/solutions that can return "No answers/solutions provided." if answers == None

    # test cases
    test_q1 = TextQ('Hope this works', ['1', '2', 3], [3, '1'])
    test_q2 = TextQ('Hope this works to throw an error', [1, 2, 3], [3, 7])
    # test_q3 = TextQ('Testing assertion', None, [1, 2, 3])
    # test_q4 = TextQ('Testing assertion', [1, 2, 3], None)
    # test_q5 = TextQ('Testing assertion', None, None)
    #
    # print(test_q3.solution)
    # print(test_q4.solution)
