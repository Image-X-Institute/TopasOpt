"""A brief summary of what this module does goes here.

Here you would write a more detailed summary of what this module does.
This text is written in python/my_module.py, but shows up nicely in the docs.
"""


def my_function(a: str, b: int):
    """A brief summary of a python function.

    A more detailed summary of a python function.

    Args:
        a (str): description of input argument a
        b (int): description of input argument b

    Returns:
        str: description of return value, with type str
    """
    return a + str(b)


class MyClass():
    """A brief summary of a python class.

    A more detailed summary of a python class.

    Args:
        a (str): description of input argument a, with type str
        b (int): description of input argument b, with type int
        c (float): description of input argument c, with type float
    """

    def __init__(self, a: str, b: int, c: float):
        pass

    def my_method(self, a: str, c: float):
        """A brief summary of a method in a python class.

        A more detailed summary of a method in a python class.

        Args:
            a (str): description of input argument a, with type str
            c (float): description of input argument c, with type float
        Returns:
            str: description of return value, with type str
        """
        return a + str(c)
