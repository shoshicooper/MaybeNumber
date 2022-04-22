"""
(c) 2022 Shoshi (Sharon) Cooper.  No duplication is permitted for commercial use.  Any significant changes made must be
stated explicitly and the original source code, if used, must be available and credited to Shoshi (Sharon) Cooper.

I wrote a descriptor to make these ctypes classes work a little nicer.
This is the superclass I'm using to go with the descriptor I wrote.

Offers memory protection around the pointer.  Also creates the ability to use class as a context manager, which
ensures you automatically delete the pointer when you're done using it.

"""
import ctypes as ct


class MethodImportError(Exception):
    pass


class SuperclassCStructs(object):
    """A Superclass"""
    # The CLIB should be the actual C Library for this class that will be loaded with the class
    CLIB = NotImplementedError

    # Before creating this class, create a shell class that inherits from ct.Structure
    # which will contain the class in C.  SuperclassCStructs contains a pointer to
    # that (shell class) object.
    # This appears to make everything work faster and gives opportunity for more safety around
    # the pointer itself.
    # Anyways, for the attribute below, please enter the class you are using that inherits from ct.Structure.
    STRUCT_CLASS = NotImplementedError

    @classmethod
    def Temp(cls, *args, **kwargs):
        """
        This returns a context manager for a temporary version of the current object.
        Helps with memory management.
        See _Temp below.
        """
        return cls._Temp(cls, *args, **kwargs)


    class _Temp(object):
        """
        Builds a context manager that creates a temporary scope for an object.
        This accomplishes several things:
            1) It means we only give access to the pointer of a c-object within this temporary scope.
                This should help to reduce the possibility of memory leaks or memory management issues.
            2) If another function in C later requires a pointer to this struct, this allows external classes
                to still pass the pointer to the c-function as required.
        Should be particularly useful for transitionary objects between Python and C: ex. strings, dicts, etc.
        """
        def __init__(self, classtype, other, *args, **kwargs):
            # is_not_temp is whether or not the pointer is temporary.  If temporary pointer, must free memory at end
            self._is_not_temp = (isinstance(other, classtype) or
                                 isinstance(other, ct.POINTER(classtype.STRUCT_CLASS)))

            if not self._is_not_temp:
                self._temp = classtype(other, *args, **kwargs)
                self.__ptr = self._temp._ptr
            elif isinstance(other, classtype):
                self.__ptr = other._ptr
            else:
                self.__ptr = other

        def __enter__(self):
            return self

        @property
        def pointer(self):
            return self.__ptr


        def __exit__(self, exc_type, exc_val, exc_tb):
            # If this is a temporary object, free the pointer from memory
            self.__ptr = None
            if not self._is_not_temp:
                self._temp = self._temp.destroy()


    @staticmethod
    def _initialize(lib, f_pointer_name, returntype, argtypes):
        """For bulk initialization of imported methods (from C) at start"""
        f = lib.__getattr__(f_pointer_name)
        f.restype = returntype
        f.argtypes = argtypes
        return f

    def __init__(self, methods_list=(), *constructor_args, **kwargs):
        """
        :param methods_list: a list of the following information in a tuple:
            [
              (
                python_class_method_name: str,
                c_lib_function_name: str,
                restype,
                argtypes
              )
            ]
            Do this tuple for each method you want to initialize at the very start.  This will speed up the process
            of importing c methods and allow descriptor to be used.

            There are two that are REQUIRED and must contain the following as the first value in the tuple:
                "constructor": This must return a pointer to the c-struct.
                "destructor": This must take only the pointer and return void.
        """
        self.__ptr = None
        self._lib = self.CLIB

        # By initializing all the methods at the start, they become fast and easy to access!
        is_constructor = False
        is_destructor = False
        self._imported_methods = {}
        for meth_name, f_name, restype, argtypes in methods_list:
            self._imported_methods[meth_name] = self._initialize(self._lib, f_name, restype, argtypes)
            is_constructor |= meth_name == "constructor"
            is_destructor |= meth_name == "destructor"

        if not is_constructor or not is_destructor:
            raise MethodImportError("Methods list must contain both a constructor and a destructor")

        # Initialize the constructor
        constructor = self._imported_methods["constructor"]
        constructor.restype = ct.POINTER(self.STRUCT_CLASS)
        self.__ptr = constructor(*constructor_args)

        self._destructor = self._imported_methods["destructor"]
        self._destructor.argtypes = [ct.POINTER(self.STRUCT_CLASS)]
        self._destructor.restype = None


    # POINTER MALLOC/FREE


    @property
    def _ptr(self):
        """Pointer to the C object"""
        # Using property class is the closest I can get to overriding the assignment operator in Python
        return self.__ptr

    @_ptr.setter
    def _ptr(self, value):
        # De-allocate memory if the pointer is not None and set the pointer to None.
        # Then re-allocate memory again.
        # Note that this is NOT a copy constructor.  Should I make it one?  Or should I leave that to __copy__?
        if self.__ptr is not None:
            self._destructor(self.__ptr)
            self.__ptr = None
        self.__ptr = value

    @_ptr.deleter
    def _ptr(self):
        # This doesn't actually delete 'self.__ptr', but it deletes the memory allocation behind it and sets it
        # to a nullpointer.
        if self.__ptr is not None:
            self._destructor(self.__ptr)
            self.__ptr = None

    def destroy(self):
        """
        Unsets the pointer.  Intended to be used as:
            instance_name = instance_name.destroy()
        That will also set your instance to be None, thus avoiding segmentation errors.
        """
        delattr(self, '_ptr')
        return None


    @classmethod
    def from_pointer(cls, ptr):
        """Initializes the class from a pointer to the C-object"""
        if not isinstance(ptr, ct.POINTER(cls.STRUCT_CLASS)):
            raise TypeError(f"Must be pointer to {cls.STRUCT_CLASS.__name__}")
        instance = cls()
        instance._ptr = ptr
        return instance


    # CONTEXT MANAGER


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.destroy()
        return None




