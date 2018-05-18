"""
Functions for generating linear equations.
"""

import random


def generate_linear_equation(max_value, max_denominator):
    """
    ax + by = c

    :param max_value: int
    :param max_denominator: int
    :return: tuple: (a: int, b: int, c: int)
    """
    test_passing = False
    while not test_passing:
        a = random.randint(-max_value, max_value)
        b = random.randint(-max_value, max_value)
        c = random.randint(-max_value, max_value)
        test_passing = test_linear_eq((a, b, c), max_value, max_denominator)
    return a, b, c


def test_linear_eq(equation: tuple, max_value, max_denominator: int):
    """
    Test slope, intercepts for fraction_complexity.

    :param equation: tuple: (a: int, b: int, c: int) equation coefficients ax + by = c
    :param max_value: int
    :param max_denominator: int
    :return: bool
    """
    a = equation[0]
    b = equation[1]
    if a == 0 and b == 0:
        return False
    c = equation[2]
    a, b, c = abs(a), abs(b), abs(c)
    # if abs(a) >= max_value or abs(b) >= max_value > abs(c) >= max_value:
    if a > max_value or b > max_value or c > max_value:

        return False
    if (
            test_linear_slope(b, max_denominator)
            and test_linear_y_int(b, max_denominator)
            and test_linear_x_int(a, max_denominator)
            ):
        return True
    # else:
    return False


def test_linear_slope(b: int, max_denominator: int):
    """
    Test that slope fraction isn't too complex.
    For ax + by = c => y = -(a/b)x + c/b: slope is -a/b

    :param b: int
    :param max_denominator: int
    :return: bool
    """
    if b > max_denominator:
        return False
    # if a/b > max_value:  # Not currently necessary because
    #     return False     # if max(a, b, c) < max_value, c/a is < max_value
    # else:
    return True


def test_linear_y_int(b: int, max_denominator: int):
    """
    Test that slope fraction isn't too complex.
    For ax + by = c => y = -(a/b)x + c/b: y-intercept is c/b

    :param b: int
    :param max_denominator: int
    :return: bool
    """
    if b > max_denominator:
        return False
    # if c/b > max_value:  # Not currently necessary because
    #     return False     # if max(a, b, c) < max_value, c/a is < max_value
    # else:
    return True


def test_linear_x_int(a: int, max_denominator: int):
    """
    Test that slope fraction isn't too complex.
    For ax + by = c => y = -(a/b)x + c/b: x-intercept is c/a

    :param a: int
    :param max_denominator: int
    :return: bool
    """
    if a > max_denominator:
        return False
    # if c/a > max_value:  # Not currently necessary because
    #     return False     # if max(a, b, c) < max_value, c/a is < max_value
    # else:
    return True


def generate_linear_eqs(num_eqs, max_val, max_denominator, unique=False):
    """
    Generate given number of linear equations in the form of coefficient ints:
    a, b, c, with ax + by = c.

    unique flag when set collects generated equations in a list, tests new
    equations against list, to allow generation of unique ax +by = c equations.
    NB:  0,  1,  1: 0x +  1y =>  1 --> y = 1
     and 0, -1, -1: 0x + -1y => -1 --> y = 1
    as well as:
         3,  9, 27:  3x +  9y = 27 --> y = -3x/9 + 27/9  --> y = -x/3 + 3
    and -1, -3, -9: -1x + -3y = -9 --> y =  x/-3 + -9/-3 --> y = -x/3 + 3
    return as different even though they are algebraically equivalent, in the
    current implementation.

    :param num_eqs: int
    :param max_val: int
    :param max_denominator: int
    :param unique: bool
    :return: tuple (a: int, b: int, c: int)
    """
    if unique:
        generated_equations = []
        for i in range(num_eqs):
            while True:
                new_equation = generate_linear_equation(max_val, max_denominator)
                if new_equation not in generated_equations:
                    generated_equations.append(new_equation)
                    break
            yield new_equation
    else:
        for i in range(num_eqs):
            yield generate_linear_equation(max_val, max_denominator)

if __name__ == '__main__':
    from worksheet_generator.equation_formatters.linear_eq_format import format_linear_eq_to_print

    num_eqs = int(input('Enter number of equations to generate: '))
    max_value = int(input('Enter maximum value in equation: '))
    max_denominator = int(input('Enter maximum denominator: '))
    unique = bool(input('Enter 1 for unique equations, 0 otherwise: '))

    for a, b, c in generate_linear_eqs(num_eqs, max_value, max_denominator, unique):
        print(f'a={a}, b={b}, c={c} =>' + format_linear_eq_to_print(a, b, c))
