"""Class for domain/range set object."""
from typing import Callable, List


class RangeSet:
    """
    Class to for a domain/range set, allowing membership testing.

    Allows specific integer/floats, inequalities and compound inequalities.
    eg  x == 1.6, x != 6, x <= 4, 1 < x <= 14

    Excluded values must be explicitly defined rather than 'not defined'.
    eg self._excluded = [lambda x: x != 5, lambda x: x > 2] will exclude any value that *doesn't*
    equal 5, as well as a value that is greater than 2.

    Note: if only excluding constraints are provided, self._included will be initialised with
    `lambda x: True` such that `self._included = [lambda x: True]`

    # Doctests:
    >>> d = RangeSet(included=[lambda x: 2 < x < 15,
    ...                        lambda x: x == 1.2,
    ...                        lambda x: x > 22
    ...                        ],
    ...              excluded=[lambda x: x == 4.7,
    ...                        lambda x: x > 60,  # ie x not > 60
    ...                        lambda x: 12 < x < 13,
    ...                        ]
    ...              )
    >>> 4 in d
    True
    >>> 1 in d
    False
    >>> 1.2 in d
    True
    >>> 4.7 in d
    False
    >>> 20 in d
    False
    >>> 27 in d
    True
    >>> 67 in d
    False
    >>> 12.5 in d
    False
    
    # Examples
    # y = 1/x
    >>> domain_1_over_x = RangeSet(excluded=[lambda x: x == 0])
    >>> range_1_over_x = RangeSet(excluded=[lambda x: x == 0])

    # y = x^2 + 2
    >>> domain_x_squared_add_two =  RangeSet()
    >>> range_x_squared_add_two =  RangeSet(included=[lambda x: x >= 2])

    ...
    Attributes
    ----------
    _included:  List[Callable]
       Constraints included in the defined range.
    _excluded:  List[Callable]
       Constraints excluded from the defined range.
    """

    def __init__(self, *,
                 included: List[Callable] = None,
                 excluded: List[Callable] = None):
        self._included: List[Callable] = []
        if included:
            self._included += included
        else:
            self._included += [lambda x: True]

        self._excluded: List[Callable] = []
        if excluded:
            self._excluded += excluded

    def __contains__(self, value) -> bool:
        """
        Checks if value in allowed values/ranges.
        :param value: Any, nominally int/float.
        :return: bool
        """
        return (any(constraint(value) for constraint in self._included) and
                not any(constraint(value) for constraint in self._excluded)
                )


"""
Add add/remove constraint machinery:
    - if self._included was empty and given a default blanket lambda x: True, and an item is then added to 
      self._included, it should remove/overwrite the blanket value. This could be accomplished in the __init__ using a
      variable for the blanket value: 
            self.___include_all_values = lambda x: True
                    if included:
            self._included += included
        else:
            self._included += [self.include_all_values]
            
    def __add_constraint(constraint: Callable):
        if self.include_all_values in self._included:
            self.included = [constraint]  # Make sure blanket value is overridden if present.
        else: self.included.append(constraint)
"""

if __name__ == "__main__":
    import doctest

    print('doctesting')
    doctest.testmod()
