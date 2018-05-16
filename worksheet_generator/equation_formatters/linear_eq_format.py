"""
Functions for formatting linear functions provided in form (a, b, c) where
ax + bx = c

Function formatting ax + bx = c to string form y = mx + n via y = -(a/b)x + c/b
Function for formatting fractions from pairs of integers.
TODO: Function simplifying fractions, with configurable degree of allowed complexity, "limited simplification"
eg 9/27 -> 3/9 or simplify 9/27 to 3/9 or 1/3, but not 3/9 or 8/4...

"""


def format_linear_eq_to_print(a: int, b: int, c: int):
    """
    Format linear equation of form ax + by = c into y = -(a/b)x + c/b
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

    equation_string += 'y = '
    if -a / b < 0:
        equation_string += '-'
    if abs(a / b) != 1:
        # put x in denominator of fraction
        split_fraction = fraction_format_without_sign(a, b).split('/')
        if split_fraction[0] == '1':
            split_fraction[0] = 'x'
        else:
            split_fraction[0] += 'x'
        fraction = ('/').join(split_fraction)
        equation_string += fraction
    else:  # |a/b| = 1
        equation_string += 'x'

    if c / b > 0:
        equation_string += ' + '
    else:
        equation_string += ' - '
    equation_string += fraction_format_without_sign(c, b)
    return equation_string


def zero_ab_format(xy_eq, coefficient, c):
    """
    Function to return xy_eq (ie 'y = ' or 'x = ') plus constant.

    :param xy_eq: str
    :param coefficient: int
    :param c: int
    :return: str
    """
    equation_string = f'{xy_eq} = '
    if c == 0:
        return equation_string + '0'
    return equation_string + fraction_format_without_sign(c, coefficient)


def fraction_format_without_sign(numerator: int, denominator: int):
    """
    Format a fraction for printing, assuming neither numerator/denominator = 0,
    and that sign is handled outside of function.
    NB Handled outside because -3/4 + 2 needs no space after sign: 2 - 3/4 does.

    :param numerator: int
    :param denominator: int
    :return: str
    """
    numerator, denominator = abs(numerator), abs(denominator)

    if numerator == 0:
        return '0'
    if abs(numerator / denominator) == 1:
        return '1'
    else:
        fraction_string = str(abs(numerator))
        if denominator != 1:
            return fraction_string + f'/{abs(denominator)}'
        return fraction_string


if __name__ == '__main__':
    pass
