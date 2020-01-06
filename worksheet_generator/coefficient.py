class Coefficient(int):
    """
    >>> a = Coefficient(3)
    >>> b = Coefficient(5)
    >>> c = Coefficient(8)
    >>> x = 2
    >>> a(x**2)+b(x)+c
    30
    >>> a*x**2 + b*x + c
    30
    """
    def __new__(cls, value):
        return int.__new__(cls, value)

    def __call__(self, arg=None):
        if arg:
            return self * arg
        return self

# pytest currently throws an error when running doctests, but the doctests pass if this module is run directly:
if __name__ == "__main__":
    import doctest
    doctest.testmod()