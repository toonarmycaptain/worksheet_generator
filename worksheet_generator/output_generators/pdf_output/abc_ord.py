a_to_z = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

def letter_seq(start: str, final: str, step=1):
    """

    :return: Generator[str, float, str]
    """
    for ordinal in range(ord(start.lower()), ord(final.lower())+1, step):
        yield chr(ordinal)


def letter_list(start: str, final: str, step=1):
    """
    Yield a list of lowercase letters.
    NB syntax different from general python syntax, as stop is nth term, rather
    than n+1th term. ie letter_list('a', 'c') yields ['a', 'b', 'c'] rather than
    ['a', 'b']
    :param start: str
    :param stop: str
    :param step: int
    :return: list
    """
    return [letter for letter in letter_seq(start, final)]


def ord_char(number: int):
    """
    Returns letter for nth letter of alphabet.
    number = 1, 3, 26 returns a, c, z respectively.

    :param number: int
    :return: str
    """
    return a_to_z[number -1]

if __name__ == '__main__':
    for letter in letter_seq('a', 'c'):
        print(letter)

    for letter in letter_list('d', 'l'):
        print(letter)

    print(f'The third letter is {ord_char(3)}')