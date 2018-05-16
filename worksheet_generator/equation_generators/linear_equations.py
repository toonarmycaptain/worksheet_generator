import random


def generate_linear_equation(max_value, max_denominator):
    """
    ax + by = c

    :param max_val: int
    :param max_denominator: int
    :return: int, int, int
    """
    test_passing = False
    while not test_passing:
        a = random.randint(-max_val, max_value)
        b = random.randint(-max_val, max_value)
        c = random.randint(-max_val, max_value)
        test_passing = test_linear_eq(a, b, c, max_value, max_denominator)
    return a, b, c

def test_linear_eq(a: int, b: int, c: int, max_value, max_denominator: int):
    """
    Test slope, intercepts for fraction_complexity.

    :param a: int
    :param b: int
    :param c: int
    :param max_value: int
    :param max_denominator: int
    :return: bool
    """
    if a == 0 and b == 0:
        return False
    a, b, c = abs(a), abs(b), abs(c)
    if a > max_value or b > max_value or c > max_value:
    # if abs(a) >= max_value or abs(b) >= max_value > abs(c) >= max_value:
        return False
    if not test_linear_slope(b, max_denominator):
        return False
    if not test_linear_y_int(b, max_denominator):
        return False
    if not test_linear_x_int(a, max_denominator):
        return False

    return True


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


def generate_linear_eqs(num_eqs, max_val, max_denominator):
    for i in range(num_eqs):
        yield generate_linear_equation(max_val, max_denominator)

def format_linear_eq_to_print(a: int, b: int, c: int):
    """
    Format linear equation of form ax + bx = c into y = -(a/b)x + c/b
    NB a, b cannot both be zero.

    :param a: int
    :param b: int
    :param c: int
    :return: str
    """
    equation_string = ''
    if a == 0:  # y = c/b
        return zero_ab_format('x', b, c)
    if b == 0:  # x = c/a
        return zero_ab_format('y', a, c)

    return equation_string + 'this hit big return'

def zero_ab_format(xy_eq, coefficient, c):
    equation_string = f'{xy_eq} = '
    if c == 0:
        return equation_string + '0'
    if c/coefficient < 0:
        equation_string += '-'
    if abs(c/coefficient) == 1:
        return equation_string + '1'
    else:
        equation_string += str(abs(c))
        if coefficient != 1:
            return equation_string + f'/{abs(coefficient)}'
        return equation_string


if __name__ == '__main__':
    num_eqs = int(input('Enter number of equations to generate: '))
    max_val = int(input('Enter maximum value in equation: '))
    max_denominator = int(input('Enter maximum denominator: '))

    for a, b, c in generate_linear_eqs(num_eqs, max_val, max_denominator):
        # print(f"y = {f'{-a}x' if abs(a) > 1 else '' if a == 0 else 'x' if a == -1 else 'x'}{f'/{b}' if b != 0 and a else ''} + {c if c != 0 else ''}")
        print(f'a={a}, b={b}, c={c}')
        print(format_linear_eq_to_print(a, b, c))
