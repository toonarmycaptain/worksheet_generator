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
    equation_str = ''
    if a == 0:  # y = c/b
        return zero_ab_format('y', b, c)
    if b == 0:  # x = c/a
        return zero_ab_format('x', a, c)

    equation_str += 'y = '

    # x var/fraction
    if -a / b < 0:
        equation_str += '-'
    if abs(a / b) != 1:
        # put x in denominator of fraction
        equation_str += fraction_format_without_sign(a, b, num_var='x')
    else:  # |a/b| = 1
        equation_str += 'x'

    # constant
    if c / b > 0:
        equation_str += ' + '
    elif c == 0:
        return equation_str
    else:
        equation_str += ' - '
    equation_str += fraction_format_without_sign(c, b)
    return equation_str


def zero_ab_format(xy_eq, coefficient, c):
    """
    Function to return xy_eq (ie 'y = ' or 'x = ') plus constant.

    :param xy_eq: str
    :param coefficient: int
    :param c: int
    :return: str
    """
    equation_str = f'{xy_eq} = '
    if c == 0:
        return equation_str + '0'
    elif c/coefficient < 0:
        equation_str += '-'
    return equation_str + fraction_format_without_sign(c, coefficient)


def fraction_format_without_sign(numerator: int, denominator: int,
                                 num_var=None, denom_var=None):
    """
    Format a fraction for printing, assuming neither numerator/denominator = 0,
    and that sign is handled outside of function.
    NB Sign handled outside because -3/4 + 2 needs no space: 2 - 3/4 does.

    :param numerator: int
    :param denominator: int
    :return: str
    """
    numerator, denominator = abs(numerator), abs(denominator)

    # if numerator == 0:  # This should never be triggered.
    #     return '0'
    if abs(numerator / denominator) == 1:
        if num_var or denom_var:  # 1/x or x
            return f"{num_var if num_var else '1'}{f'/{denom_var}' if denom_var else ''}"
        return '1'
    else:
        # numerator
        if num_var:
            fraction_str = f"{abs(numerator) if abs(numerator) != 1 else ''}{num_var}"
        else:
            fraction_str = f"{abs(numerator)}"
        # denominator
        if denominator != 1:
            return fraction_str + f"/{abs(denominator)}{denom_var if denom_var else ''}"
        elif denom_var:  # denominator coefficient = 1
            return fraction_str + f"/{denom_var if denom_var else ''}"
    return fraction_str


if __name__ == '__main__':
    pass