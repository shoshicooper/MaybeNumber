"""
(c) 2022 Shoshi (Sharon) Cooper.  No duplication is permitted for commercial use.  Any significant changes made must be
stated explicitly and the original source code, if used, must be available and credited to Shoshi (Sharon) Cooper.

In this file, I present an alternative way of doing MaybeNumber:
    Use the C++ version of MaybeNumber.  Import into Python.
    Makes everything much, much faster!  About 1/4 of the time, after I did some speed tests.
    However, because Python is not strictly typed like C++, the object should still ducktype as both a number and a
        string depending on how you use it.
    Known problems still apply.
"""

import os.path
from c_import_to_python.import_dependents.c_str_cls import *


def load_maybenumber_library():
    """Where we load our library for MaybeNumber"""
    path = os.path.abspath(os.path.join(__file__, f'../dlls/'))
    name = "maybenumber_libshared.dll"
    return load_library(path, name)


class CImptMaybeNumber(ct.Structure):
    """
    This is the basic CTypes Struct that we won't touch.  Best to leave this all in C, as
    doing so clearly delineates between the C-code and Python code.
    """
    _fields_ = [('c', ct.c_char), ('token', ct.c_char)]


class MaybeNumberFromC(SuperclassCStructs):
    """The Python class for MaybeNumber imported from C"""
    CLIB = load_maybenumber_library()
    STRUCT_CLASS = CImptMaybeNumber

    def __init__(self, string="", token=' '):
        # Typedef p
        p = ct.POINTER(self.STRUCT_CLASS)

        # It wound up being fastest to set all these up during __init__
        # Below is a list of the methods to import in the following format:
        # (python_class_name, c_function_name, restype, argtypes)
        methods_list = [
            ('constructor', "make_maybenumber", p, None),
            ('destructor', "free_maybenumber", None, [p]),
            ('push_back', "maybenumber_push_back", None, [p, ct.c_int]),  # Easier to use c_int as char
            ('pop', "maybenumber_pop_back", None, [p]),
            ('isnumber', "maybenumber_isnumber", ct.c_bool, [p]),
            ('isempty', "maybenumber_isempty", ct.c_bool, [p]),
            ('__len__', 'maybenumber_size', ct.c_int, [p]),
            ('clear', 'maybenumber_clear', None, [p]),
            ('_lower_inplace', 'maybenumber_lower_inplace', None, [p]),
            ('_upper_inplace', 'maybenumber_upper_inplace', None, [p]),
            ('__iadd__', 'maybenumber_iadd', None, [p, ct.POINTER(CStrFromC)]),
            ('force_to_number', 'maybenumber_force_to_number', ct.c_double, [p]),
            ('_make_bool', 'maybenumber_make_bool', ct.c_bool, [p]),
            ('_make_double', 'maybenumber_make_double', ct.c_double, [p]),
            ('_make_string', 'maybenumber_make_string', None, [p, ct.POINTER(CStrFromC)]),
            ('unwrapped', 'maybenumber_get_unwrapped', None, [p, ct.POINTER(CStrFromC)]),
            ('back', 'maybenumber_back', ct.c_int, [p]),
        ]
        # initialize the superclass
        super().__init__(methods_list, token)

        # add the starting value
        for letter in string:
            self.push_back(letter)


    @CStructWrapper
    def push_back(self, letter, **kwargs):
        # Python addition: ducktyping for letter
        if len(letter) > 1:
            return self.__iadd__(letter)
        kwargs['c_func'](self._ptr, ord(letter[0]))

    def append(self, letter):
        # Python addition: Python calls push_back append, so added this method too
        return self.push_back(letter)

    @CStructWrapper
    def pop(self, **kwargs):
        # Python addition: In Python, pop usually returns something.  So created return value.
        final = chr(self._imported_methods['back'](self._ptr))
        kwargs['c_func'](self._ptr)
        return final

    @CStructWrapper
    def isnumber(self, **kwargs):
        # Method in C
        return bool(kwargs['c_func'](self._ptr))

    @CStructWrapper
    def isempty(self, **kwargs):
        # Method in C
        return bool(kwargs['c_func'](self._ptr))

    @CStructWrapper
    def __len__(self, **kwargs):
        # Method in C
        return kwargs['c_func'](self._ptr)

    @CStructWrapper
    def clear(self, **kwargs):
        # Method in C
        return kwargs['c_func'](self._ptr)

    @CStructWrapper
    def unwrapped(self, **kwargs):
        # Method in C.  Additional code for temporary mutable string variable
        with CStringPyth.Temp('') as s:
            kwargs['c_func'](self._ptr, s.pointer)
            return s.tostring()

    @CStructWrapper
    def force_to_number(self, **kwargs):
        # Method in C
        return float(kwargs['c_func'](self._ptr))

    def lower(self, inplace=False, **kwargs):
        if inplace:
            self._imported_methods['_lower_inplace'](self._ptr)
            return self
        return self.unwrapped().lower()

    def upper(self, inplace=False, **kwargs):
        if inplace:
            self._imported_methods['_upper_inplace'](self._ptr)
            return self
        return self.unwrapped().upper()

    @CStructWrapper
    def __iadd__(self, other, **kwargs):
        with CStringPyth.Temp(other) as s:
            kwargs['c_func'](self._ptr, s.pointer)
        return self

    def convert(self, additional_function=lambda x: x.unwrapped()):
        """
        Converts between this mutable object and the immutable counterpart.
        This is inherently a Python method because Python has no set return type.
        """
        # Note: known issue: infinity will return C-version of infinity, not python version. Unsure if problem.
        if self.isnumber():
            return self.force_to_number()
        other_conversions = [None, True, False]
        for value in other_conversions:
            if self.unwrapped().lower() == str(value).lower():
                return value
        return additional_function(self)


    # Ducktyping for Python use


    def __bool__(self):
        return bool(self.unwrapped())

    def __str__(self):
        return str(self.unwrapped())

    def __neg__(self):
        return -self.convert()

    def __add__(self, other):
        return self.convert() + other

    def __sub__(self, other):
        return self.convert() - other

    def __radd__(self, other):
        return other + self

    def __rsub__(self, other):
        return other + -self

    def __mul__(self, other):
        return self.convert() * other

    def __truediv__(self, other):
        return self.convert() / other

    def __invert__(self):
        return 1 / self.convert()

    def __repr__(self):
        return repr(self.unwrapped())

    def __iter__(self):
        yield from self.unwrapped()

    def __getitem__(self, item):
        return self.unwrapped().__getitem__(item)

    def __eq__(self, other):
        if other == self.unwrapped():
            return True
        if other == self.convert():
            return True
        return False

    def __contains__(self, item):
        return item in self.unwrapped()

    def __lt__(self, other):
        return self.convert() < other

    def __gt__(self, other):
        return self.convert() > other

    def __abs__(self):
        return abs(self.convert())

    def __pow__(self, power, modulo=None):
        return self.convert().__pow__(power, modulo)

    def __rmul__(self, other):
        return other * self.convert()

    def __floordiv__(self, other):
        return self.convert() // other

    def __round__(self, n=None):
        return self.convert().__round__(n)

    def __format__(self, format_spec):
        return self.convert().__format__(format_spec)

    def __float__(self):
        return float(self.convert())

    def __int__(self):
        return int(self.convert())

    def __and__(self, other):
        return self.convert() & other

    def __or__(self, other):
        return self.convert() | other
