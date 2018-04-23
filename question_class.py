"""
Question classes

"""
class Question():
    pass

class TextQ(Question):
    """
    Question class with question and answers solely composed of text.
    """
    def __init__(self, question_text: str, answer_tuple: tuple, correct_ans: tuple=None):
        question_text = question_text
        answers = answer_tuple
        num_answers = len(answer_tuple) + 1 # for use with 'in range(num_answers)
        # for more than one answer, use tuple, or slice? This will output a list
        # eg answers = [1, 2, 3, 4] => correct = [1:4:2] => correct >>> [2, 4]
        correct_answer = correct_ans

        # assert all correct answers in answers
        if correct_answer is not None:
            assert set(correct_answer) & set(answers) == set(correct_ans),\
                "Answer not in answer choices."


# test cases
# test_q1 = TextQ('Hope this works', ('1', '2', 3), (3, '1'))
# test_q2 = TextQ('Hope this works to throw an error', (1, 2, 3), (3, 7))
