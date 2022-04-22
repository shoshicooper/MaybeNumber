"""
This is a descriptor that to basically make the code look nicer inside ctypes methods.
I experimented with different kinds of descriptors that ran the c-function before vs. after, but in the end,
I realized the best thing to do was let me decide when to run the c-function.  So I made the descriptor give
back an extra parameter, 'c_func', which will run the c-func when called.

That way, if I had to convert types around beforehand, I could do that.  Same for afterward.

Now, it is possible to create a descriptor that will set the argtypes and the restype for you as well.
But that descriptor was agonizingly slow.  I opted for this one instead -- which is nice and fast!
And you can use super() on it.

Again, though, this is mostly just so the code looks nicer.

"""


class CStructWrapper(object):
    """A Descriptor"""

    def __set_name__(self, owner, name):
        """Establishes the name of the method we are using and the owner"""
        if not hasattr(self, 'name'):
            self.name = name

    def __init__(self, function):
        self.function = function

    def __get_func(self, obj):
        func = obj._imported_methods[self.name]
        return lambda *args, **kwargs: self.function(obj, *args, c_func=func, **kwargs)

    def __get__(self, obj, objtype=None):
        if not hasattr(self, 'name') or obj is None:
            return self
        # Returns the getter with the additional parameter c_func
        return self.__get_func(obj)







