"""
A transitional data structure from const char* to python string.
CString class is written in C, not C++, so it presupposes no std::string class.

Had this lying around.  Thought it'd be useful here so I could use mutable strings with context manager.
Gutted most of original and the rest is here.

"""
import ctypes as ct
import os

from c_import_to_python.import_dependents.ctypes_imported_datastructure_superclass import SuperclassCStructs
from c_import_to_python.import_dependents.c_struct_descriptor import CStructWrapper
from c_import_to_python.import_dependents.load_c_lib import load_library


def load_string_library():
    path = os.path.abspath(os.path.join(__file__, f'../../dlls/'))
    name = "c_string_class_libshared.dll"
    return load_library(path, name)


class CStrFromC(ct.Structure):
    _fields_ = [('a_string', ct.c_char_p)]


class CStringPyth(SuperclassCStructs):
    """Python version of my CString class from C"""
    CLIB = load_string_library()
    STRUCT_CLASS = CStrFromC

    @classmethod
    def Temp(cls, string=""):
        return cls._CStrTemp(cls, string)

    class _CStrTemp(SuperclassCStructs._Temp):
        """Like the temporary context manager but has a tostring() method inside it"""

        def tostring(self):
            """converts the temporary value into a Python string"""
            if hasattr(self, '_temp'):
                return str(self._temp)
            temp = CStringPyth.cstring_pointer_to_python_string(self.__ptr)
            return str(temp)




    def __init__(self, string=""):
        # typedef p
        p = ct.POINTER(CStrFromC)

        # The hope is that by initializing these all at the start, I can make them faster later!
        methods = [
            ('constructor', 'make_cstring_charstar', p, None),
            ('destructor', 'destroy_cstring', None, [p]),
            ('__iadd__', 'iadd_ptrs', None, [p, p]),
            ('push_back', 'push_back_c_string', None, [p, ct.c_int]),
            ('__len__', 'string_size', ct.c_int, [p]),
            ('_c_at', 'string_at', ct.c_int, [p, ct.c_int]),
            ('charstar', 'make_string_char_star', ct.c_char_p, [p]),
            ('get_char', 'get_letter', ct.c_char, [CStrFromC, ct.c_int])
        ]
        super().__init__(methods, "")

        if isinstance(string, ct.POINTER(self.STRUCT_CLASS)):
            self._impt_ptr(string)
        else:
            # Add string
            [self.push_back(letter) for letter in str(string)]


    def _impt_ptr(self, ptr):
        i = 0
        while True:
            char = self._imported_methods['_c_at'](ptr, i)
            if char == 0:
                break
            self.push_back(chr(char))
            i += 1

    @staticmethod
    def convert_to_charstar(string):
        return ct.create_string_buffer(str.encode(string))

    @staticmethod
    def convert_to_pythonstring(charstar):
        as_bytes = bytes(charstar)
        # cut off b' at front (there b/c it's bytes) and the termination character '\0' (b/c it's a char star)
        return str(as_bytes)[2:-5]

    @classmethod
    def convert_to_selftype(cls, string):
        if not isinstance(string, cls):
            return cls(string)
        return string

    # Indexing and length

    @CStructWrapper
    def __len__(self, c_func=None):
        return int(c_func(self._ptr))

    @CStructWrapper
    def _c_at(self, i, c_func=None):
        return c_func(self._ptr, i)

    # Add letters

    @CStructWrapper
    def __iadd__(self, other, c_func=None):
        if c_func is None:
            for letter in other:
                self.push_back(letter)
        else:
            with self.Temp(other) as s:
                c_func(self._ptr, s.pointer)
        return self

    @CStructWrapper
    def push_back(self, letter, **kwargs):
        if isinstance(letter, CStrFromC):
            as_char = self._imported_methods['get_char'](ct.POINTER(letter), 0)
            kwargs['c_func'](self._ptr, as_char)
            return
        if len(letter) > 1:
            raise TypeError("Must be single letter character")
        elif letter == '\0':
            return
        kwargs['c_func'](self._ptr, ord(letter[0]))

    def __eq__(self, other):
        if isinstance(other, CStringPyth):
            other = str(other)
        return str(self) == other

    @classmethod
    def cstring_pointer_to_python_string(cls, ptr):
        string = cls.from_pointer(ptr)
        python_string = str(string)
        string = string.destroy()
        return python_string

    def __str__(self):
        return ''.join([chr(self._c_at(i)) for i in range(len(self))])

    def __repr__(self):
        return str(self)

    def __add__(self, other):
        return type(self)(self._ptr).__iadd__(other)

    def __copy__(self):
        return type(self)(self._ptr)

    def __getitem__(self, item):
        ret_item = chr(self._c_at(item))
        if ret_item == '\0':
            raise IndexError("index out of bounds")
        return ret_item

