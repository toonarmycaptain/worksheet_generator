"""
Question classes


# new version to be merged after tests for current class are written, to ensure compatibility and test suite function.
"""

from error_classes import SolutionUnavailableError


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
    Text Question class with question and answers solely composed of text.


    Attributes:
        question_text: str,
        answers: list,
        solution: list,
        num_answers: int,  # document that this is a @property method rather than a set attribute?
        num_solutions: int,  # document that this is a @property method rather than a set attribute?

    Methods:



    # some of these methods might be generalised and moved to Question class


    #documentation should include warning to call with try/except if unsure whether solutions are available in answers,
    #and must be handled by caller, possibly make habit of caller doing sanity test before passing to constructor (eg if
    #user is hand-inputting questions, as opposed to from-database.


    TODO: properly document class and functions, including 'raises'
    """
    def __init__(self,
                 question_text: str,
                 answers: list=None,
                 solution: list=None):
        self.question_text = question_text
        self.answers = answers
        self.solution = solution

# =====> TODO: implement __repr__ method!!!

    # question_text
    @property
    def question_text(self):
        return self.__question_text

    @question_text.setter
    def question_text(self, question_text):
        self.__question_text = question_text

    # answers
    @property
    def answers(self):
        return self.__answers

    @answers.setter
    def answers(self, answers):
        self.__answers = answers

    # solution
    @property
    def solution(self):
        return self.__solution

    @solution.setter
    def solution(self, solution):
        # ensure all solutions  are in the answer choices
        if solution and self.answers:
            self.__validate_solution(self.answers, solution)  # ===> abstract into validate_solution() function
            # => throws error if solution/s not part of answer set, otherwise passes uneventfully

            # assert (
            #     set(solution) & set(self.answers) == set(solution)
            # ), "Answer not in answer choices." # TODO: replace assert (assert won't run in optimised/production
        self.__solution = solution

    @staticmethod
    def __validate_solution(answers, solution):
        if not set(solution).issubset(answers):
            raise SolutionUnavailableError

    # for use with 'in range(num_answers) or in range(num_solutions)
    # num_answers
    @property
    def num_answers(self):
        return None if not self.answers else len(self.answers)

    # num_solutions
    @property
    def num_solutions(self):
        return None if not self.solution else len(self.solution)


if __name__ == "__main__":
    # test cases
    test_q1 = TextQ('Hope this works', ['1', '2', 3], [3, '1'])
    # test_q2 = TextQ('Hope this works to throw an error', [1, 2, 3], [3, 7])
    test_q3 = TextQ('Testing assertion', None, [1, 2, 3])
    test_q4 = TextQ('Testing assertion', [1, 2, 3], None)
    # test_q5 = TextQ('Testing assertion', None, None)
    #
    print(test_q3.solution)
    print(test_q4.solution)
    # test_q6 = TextQ(17, ["question wasn't a string", 17], [17])  # TODO: implement check for non-string questions?
    # print(test_q1.question_text)
    # print(test_q3.answers)
    # print(test_q4.answers)
    # print(test_q6.answers)
    # print(test_q3.num_answers)
    # print(test_q4.num_answers)
    # print(test_q6.num_answers)
    print(test_q4.num_answers)
    print(test_q3.num_solutions)
    pass
