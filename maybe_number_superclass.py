"""
(c) 2022 Shoshi (Sharon) Cooper.  No duplication is permitted for commercial use.  Any significant changes made must be
stated explicitly and the original source code, if used, must be available and credited to Shoshi (Sharon) Cooper.

The MaybeNumber superclass.  Python version.
"""
import math


class MaybeNumber(object):
    """
    Possibly a number or possibly not.  Essentially, this is a semi-mutable string class that turns itself immutable
    once you run convert() method.
    """
    # These sets are used for the conversion between numbers and letters
    CURRENCIES = {"$", '€', '£'}
    IGNORE = CURRENCIES.union({",", " ", ")", "", '%', '\n', '\t', "(", "-", "'"})
    ALL_NUM_ELEMENTS = set(map(str, range(10))).union(IGNORE)
    ALL_NUM_ELEMENTS.add(".")
    ACCEPTABLE_ENDS = {' ', ')'}


    # This is the default bitmask names.  I'll shove them up here so people can tell what to they want to
    # add or subtract from the method that establishes what bitmasks you want in the actual class.

    # I'll add the variable names for upper and lower from the C++ version as well just for cross-reference purposes.

    # These are required to see if it's a number
    DEFAULT_BITMASK_NUMBER_NAMES = [
        # Checks if each letter is in ALL_NUM_ELEMENTS set
        'isnumberelement',
        # Checks if the letter is a '-' character
        'isdash',
        # Checks if the letter is a period ('.')
        'isdot',
        # Checks if the number is zero.  If _forcenumber == 0, either it's not a number or it's 0.
        # So we'd have our answer easily if we knew whether or not '0' is in the character array.
        'iszero',
        # Required to fix a bug where it would say that just ',' or '.' was a number.  Oops.
        'isdigit',
        # Checks if there are any symbols that definitely make it not be a number
        'isdefnotnumber',
        # to see if a negative number is lead by the negative sign or a currency symbol plus the negative sign
        'isacceptablestart',
        # to see if a percent ends with % or %) or % )
        'isacceptableend',
        # To see if the open parentheses is closed
        'isclosedparen',
        # To see where the currency symbols appear
        'iscurrency',
        # To see where the %'s are
        'ispercent',
        # Check for open parentheses
        'isopenparen',
    ]
    # Some optional bitmask names you can use for other bitmasks
    DEFAULT_BITMASK_NAMES = [
        # Checks if it's the token you added at the beginning.  Not so useful if you need to tokenize using a stack.
        'istoken',
        # For C++ code - mutable strings
        'isupper',
        # For C++ code - mutable strings
        'islower']


    # I'm using __slots__ here to keep the class relatively compact where it can be
    __slots__ = ["_original", "_multiplier", "_token", "_place", "_forcenumber", "_len_bitmasks", "_the_bitmasks",
                 "_bitmask_additive_functions"]

    def __init__(self, string="", tokenize_by=' '):
        """
        Initializes the MaybeNumber class.

        :param string: The string you are iterating through
        :param tokenize_by: a single character that will be kept track of throughout the MaybeNumber.  Allows user to
            easily keep track of something simple without having to subclass.
        """
        if len(tokenize_by) > 1:
            raise ValueError("Token must be single character")

        self._the_bitmasks = {k: 0b0 for k in self._bitmask_names()}
        self._bitmask_additive_functions = self._get_additive_functions()

        # Some useful information
        self._original = ""
        self._multiplier = 1
        self._token = tokenize_by
        self._len_bitmasks = 0

        # I need this to do the number conversion in real time
        self._place = 1
        self._forcenumber = 0

        # This is also accomplished using append
        self.__iadd__(string)



    @property
    def unwrapped(self):
        return self._original


    # Setup Methods (on their own to allow easier subclassing)


    def _bitmask_names(self):
        """
        A list of the names of the bitmasks you will be using.
        They are in their own method for two reasons:
            1) Subclassing: Someone can easily override this subclass and add as many bitmasks as they like.
            2) Ordering: MaybeNumber always adjusts bits in the order in which they appear here.
                        So by changing the order here, you can change the order in which the bits are adjusted.
        The ordering component is why self._bitmask_names() is required in addition to self._get_additive_functions().
        """
        return self.DEFAULT_BITMASK_NUMBER_NAMES + self.DEFAULT_BITMASK_NAMES

    def _get_additive_functions(self):
        """
        These are the lambda functions that will be used to add bits to each bitmask.  Each must take a single
        parameter: letter.  Only bitmasks included in _bitmask_names() will be used.

        Bits will be set in the order given in self._bitmask_names()
        """
        # I'm putting this function in separately because otherwise it's a bit confusing
        def acceptable_start(ltr):
            if ltr != ' ' and ltr not in self.CURRENCIES:
                return False
            # This just is checking to see if we're only dealing with the start of the number
            if self._len_bitmasks > 0:
                expected = ((1 << self._len_bitmasks) - 1)
                if self._isacceptablestart == expected:
                    return True
                return False
            return True

        return {
            'isnumberelement': lambda letter: letter in self.ALL_NUM_ELEMENTS,
            'isdash': lambda letter: letter == '-',
            'isdot': lambda letter: letter == '.',
            'iszero': lambda letter: letter == '0',
            'istoken': lambda letter: letter == self.token,
            'isdigit': lambda letter: 48 <= ord(letter) < 58,
            'isdefnotnumber': lambda letter: letter not in self.ALL_NUM_ELEMENTS,
            'isupper': lambda letter: 65 <= ord(letter) < 91,
            'islower': lambda letter: 97 <= ord(letter) < 123,
            'isacceptablestart': acceptable_start,
            'isacceptableend': lambda letter: letter in self.ACCEPTABLE_ENDS,
            'isclosedparen': lambda letter: letter == ')',
            'iscurrency': lambda letter: letter in self.CURRENCIES,
            'ispercent': lambda letter: letter == '%',
            'isopenparen': lambda letter: letter == '(',
        }


    # For ease of reading the code


    def __getattr__(self, item):
        """
        The idea is that I could do "if self._isdot:" and it'd give me the isdot bitmask.
        This will make the code easier to read.
        """
        if item.startswith("_") and item != "_the_bitmasks":
            try:
                return self._the_bitmasks[item[1:]]
            except KeyError:
                pass
        return super().__getattribute__(item)

    def __setattr__(self, key, value):
        """See docstring for getattr"""
        if key == "_the_bitmasks":
            return super().__setattr__(key, value)

        if key.startswith("_") and key[1:] in self._the_bitmasks:
            if not isinstance(value, int):
                raise TypeError("Must be positive integer")
            self._the_bitmasks[key[1:]] = value
        else:
            return super().__setattr__(key, value)

    @property
    def token(self):
        return self._token


    # Bitmask Adjustments and Additions


    def _adjust_bits(self, letter="", **kwargs):
        """Pops or adds bits"""
        if not kwargs:
            final = []
            for attr_name in self._bitmask_names():
                mask = getattr(self, f"_{attr_name}")
                final.append((f"_{attr_name}", mask & 1))
                setattr(self, f"_{attr_name}", mask >> 1)
            return final

        # I iterate over self._bitmask_names() on purpose here because I feel that the order in which the bits are set
        # is actually really important. A user who is subclassing may be setting one bitmask based on the final value
        # of a different bitmask (in fact, this happens a lot).  So it's important to know with 100% certainty which
        # will be set first. Therefore, the bitmasks will always be set using the order they appear in
        # self._bitmask_names().

        # I will write this out in the code in a slightly more ugly way to make that obvious.
        for attr_name in self._bitmask_names():
            if attr_name not in kwargs:
                continue
            bit_func = kwargs[attr_name]

            try:
                mask = getattr(self, f"_{attr_name}")
                bit = bit_func(letter)
                setattr(self, f"_{attr_name}", (mask << 1) | bit)
            except AttributeError:
                pass
        self._len_bitmasks += 1


    def _add_bits(self, letter):
        """Adds bits"""
        self._adjust_bits(letter, **self._bitmask_additive_functions)

    def _remove_bits(self):
        """Removes final bit and returns it"""
        return self._adjust_bits()



    #################################################################################
    # This is where we get into the heart of the class and what it does

    # Append and pop:


    def append(self, letter):
        """The equivalent of C's 'push_back' method"""
        # Convert ascii letter to integer as we would in C
        if isinstance(letter, int):
            letter = chr(letter)

        # Type checking b/c no strict typing in Python (append is only for char's.  Use __iadd__ for entire string.)
        if not isinstance(letter, str) or len(letter) > 1:
            raise TypeError("Must be single string character")

        # Mostly comes up in C++ code.  Added here for cross-reference purposes
        if letter == '\0':
            return

        # Checking if letter is "(" or "-".  (number) means negative in accounting.  -number also means negative.
        if letter == '(' or letter == '-':
            self._multiplier *= -1.0
        # If it's a percent, multiply by 1/100.  I will write as decimal to make extra sure this is still double in C
        if letter == '%':
            self._multiplier *= 0.01

        # Add bits for the letter we are adding
        self._add_bits(letter)
        # Modify original string
        self._original += letter

        # If we're adding a period, the current number is not changed, but we must adjust the place for the next digit
        if letter == '.':
            self._place = 0.1
            return

        # This is the part where we create the numeric value of the item in real time while we are already parsing it.
        # This will be helpful because it means that we will not have to reparse it later to convert it into a number.

        if letter in self.ALL_NUM_ELEMENTS and letter not in self.IGNORE:
            if self._isdot:
                self._forcenumber += (float(letter) * self._place)
                self._place /= 10.0
            else:
                self._forcenumber = (self._forcenumber * 10.0) + float(letter)


    def __iadd__(self, phrase):
        """This is the same thing as append but does an entire phrase"""
        for letter in str(phrase):
            self.append(letter)
        return self

    def extend(self, phrase):
        """Same as append but for an entire string instead of a single character"""
        for letter in str(phrase):
            self.append(letter)

    def pop(self, masked=False):
        """
        Pops the final item in the string.

        :param masked: if True, the popped item will be returned to you as another MaybeNumber.
                        Otherwise, the popped item will be returned to you as a string.
        """
        letter = self._original[-1]
        self._remove_bits()

        self._original = self._original[:-1]
        if letter == '%':
            self._multiplier *= 100.0
        if letter == '-' or letter == '(':
            self._multiplier *= -1.0

        to_return = letter
        if masked:
            to_return = type(self)(letter)

        # Real-time adjustment to the converted number as we pop:
        if letter in self.ALL_NUM_ELEMENTS and letter not in self.IGNORE:
            if letter == '.':
                self._place *= 10.0

            elif self._isdot:
                self._place *= 10.0
                self._forcenumber = self._forcenumber - (self._place * float(letter))
            else:
                self._forcenumber = (self._forcenumber - float(letter)) / 10.0
                self._place /= 10

        return to_return


    # Conversion and isnumber:


    def convert(self, additional_function=lambda x: x.unwrapped):
        """
        Converts between this mutable object and the immutable counterpart.
        If it's:
            An integer: an integer value is returned
            A float: a float value is returned
            infinity: a float value is returned
            A boolean: the correct boolean is returned
            None: a Nonetype object is returned
            Anything else: a string is returned

        This method has no equivalent in the C++ code because the C++ code requires strict typing.  So in C++,
        I had to create a method that'd tell you what the type was, then override the cast operators accordingly.

        This works out well for both languages because C++ does not support mixed-type arrays, while Python lists do.
        So for both languages, you do the same thing -- just at slightly different times.
        In Python, you can convert the MaybeNumber before it's placed into your parsing list.
        In C++, you create an array of MaybeNumber objects, then cast each MaybeNumber to the correct type only when it
        is extracted from the array and is actually used in the code (so later than in the Python version).
        """
        # If it's not a number, then I must check if it's None, True, or False
        if not self.isnumber():
            other_conversions = [None, True, False]
            for value in other_conversions:
                if self._original.lower() == str(value).lower():
                    return value
            # also, check for if it's float("inf")
            if self._original.lower() == 'inf':
                return float('inf')
            # The additional function exists to allow you to either do one additional parsing step in the middle here.
            # I needed this when doing speech-pattern parsing for AI and thought it was useful enough to leave in.
            return additional_function(self)

        try:
            return self.force_to_number()
        except ValueError:
            return additional_function(self)


    def force_to_number(self):
        """
        Forces the item to become a number.  Essentially, this only returns the number part of the string.
        If there is no number part, this will raise a ValueError.

        Warning: If this MaybeNumber is NOT a number and you use force_to_number, you may wind up with something that
        bears little resemblance to the original item you were trying to parse.
        """
        as_number = self._forced
        if as_number == 0 and not self._iszero:
            raise ValueError("No number part exists")
        return as_number

    @property
    def _forced(self):
        """
        Performs the final step to turn self._forcenumber into the number we expect it to be.
        In other words, this multiplies self._forcenumber by the multiplier and checks to see what numeric type it is
        """
        forced_item = self._forcenumber * self._multiplier

        if forced_item == int(float(forced_item)):
            return int(forced_item)
        return forced_item



    def isnumber(self):
        """
        Checks if the string value given is actually a number or not.
        Because I am using bitmasks, this method is done in O(1)
        """
        # if there are no number elements or there are no digits found inside the string, then this is false
        if self._isnumberelement == 0 or self._isdigit == 0:
            return False
        # Check to see if there are any symbols that make this definitely not a number.
        if self._isdefnotnumber != 0:
            return False

        # Numbers cannot have more than one: period, dash, currency symbol, %
        cannot_be_doubled = ['isdot', 'isdash', 'iscurrency', 'ispercent', 'isopenparen', 'isclosedparen']
        for attr_name in cannot_be_doubled:
            bitmask = getattr(self, f"_{attr_name}")
            if bitmask > 0 and not self._is_only_one_bit_on(bitmask):
                return False

        # -200 and (200) are two different ways of writing negative two hundred.  However, (-200) does not mean
        # -1 * -1 * 200.  Instead, the extra () make this no longer be a number.
        # So we must make sure that isdash and isopenparen/isclosedparen don't mix in same number
        if self._isdash and self._isopenparen:
            return False
        if self._isdash and self._isclosedparen:
            return False

        # Check open parenthesis is closed
        if self._isopenparen and not self._isclosedparen:
            return False

        # Make sure that, if it's negative, the negative symbol starts the number (except for currency & spaces)
        if self._multiplier < 0:
            start = 0
            # Use the bitmask 'isacceptablestart' to leap to whichever character starts the number itself
            # This bitmask only operates while the start is "acceptable" for the start of a number
            if self._isacceptablestart:
                start = self._get_slice_index(self._isacceptablestart)

            if self._isdash and self._original[start] != '-':
                return False
            if not self._isdash and self._original[start] != '(':
                return False
        # If multiplier is fractional, see if the % ends the string
        if self._ispercent:
            original = self._original.strip()
            if original[-1] == ')':
                original = original[:-1]
            if not original.endswith('%'):
                return False
        # If all the above eliminating criteria is not met, then this is indeed a number
        return True


    ##########################################################################################
    # The methods below are for another useful thing the class can do -- it can slice a string
    # with a much shorter average time than normal.

    # In C++, because the string is mutable, this translates to changing the string in-place faster.
    # In Python, it allows us to slice things more quickly and move most of the looping out of Python.

    # Instead of looping over every single letter, we can use bitwise operations to "leap" between on-bits in
    # any bitmask.  Using logarithms, we can convert this to a negative index (and later to a positive index).

    # True, this does not change the O(n).  But it should decrease the average time.


    @staticmethod
    def _is_only_one_bit_on(number):
        """
        Checks if only a single bit is on in the bitmask.
        This method is only here to enhance code readability
        """
        return number & (number - 1) == 0

    def _get_slice_index(self, bitmask, length=None):
        """This is a general method that takes a bitmask and figures out what the index is for the LSB"""
        if length is None:
            length = len(self._original)

        lsb_off = (bitmask & (bitmask - 1))
        difference = bitmask - lsb_off
        neg_index = -1 - int(math.log2(difference))
        # Note: in C++, do not add the +1 below because '/0' counts as a character
        pos_index = length + (neg_index + 1)
        return pos_index


    def _slice_by_bitmask(self, bitmask, concatenate=False, subclass=str, bitval_to_compile=0):
        """
        Slices the original string into segments based on any bitmask we stored whilst adding chars.

        :param bitmask: int.  The bitmask you want to slice by.  Anywhere that's a 1 will be a token.  The 0's will be
            your slices.
        :param concatenate: bool.  If true, the value will be returned as a string.  This allows you to cut out all
            punctuation or numbers or whatever else you want, while preserving everything else.
        :param subclass: type.  If you want all internal items in the list to be MaybeNumbers, you can pass
            MaybeNumber through here and it will cast everything to a MaybeNumber.  Same with anything else.
            Default is str.
        :param bitval_to_compile: Which bit values you want compiled together, the ones where the bit is turned on (1)
            or off (0).  Example: isdigit bitmask turns bits on where there's a digit.  So if you want to get a list of
            all digits in the string, you would pass through bitval_to_compile=1.
            However, if you want to slice by spaces (similar to str.split()), then you should do is_space bitmask and
            bitval_to_compile = 0.  That will cut out all spaces and return a list of what's between the spaces.
        """
        if not self.unwrapped:
            return subclass(self.unwrapped) if concatenate else []
        if bitmask == 0 and bitval_to_compile == 0:
            return subclass(self.unwrapped) if concatenate else [subclass(self.unwrapped)]
        if bitmask == 0 and bitval_to_compile == 1:
            return subclass("") if concatenate else []

        # Add artificial 1 at beginning
        bitmask = bitmask | (1 << (self._len_bitmasks + 1))

        get_start_stop = (lambda prv_idx, crnt_idx: (crnt_idx.start, prv_idx.stop) if bitval_to_compile == 0
                          else (crnt_idx.stop, crnt_idx.start))

        IndexType = type("Index", (), {'start': len(self.unwrapped), 'stop': len(self.unwrapped)})

        prev_index = IndexType()
        string = subclass("")
        list_ = []

        # The idea here is that if we see there are consecutive bits on, we invert the bitmask to jump to the other
        # side of the cluster of on-bits.  Then re-invert to get back.
        while bitmask:
            pos_index = self._get_slice_index(bitmask, len(self.unwrapped))
            neg_index = len(self.unwrapped) - (pos_index - 1)

            current_indices = IndexType()
            current_indices.start = pos_index

            scooched_bitmask = bitmask >> (neg_index - 1)
            # Because I put in an artificial 1 to flush things out
            if scooched_bitmask == bitval_to_compile:
                break

            # So the trick is that if there is more than 1 bit turned on, I want to leap to the next change.
            # And when I do that leap, I'd rather use bitwise equations instead of a loop b/c it's faster.
            new_length = len(self.unwrapped) - neg_index + 1

            localized_end_of_cluster = self._get_slice_index(~scooched_bitmask, new_length)
            cluster_length = new_length - localized_end_of_cluster

            # Get ending index
            current_indices.stop = pos_index - cluster_length - (1 - bitval_to_compile)
            # next bitmask should be different as well
            blank_these_bits_please = (1 << (neg_index + cluster_length - bitval_to_compile)) - 1
            next_bitmask = bitmask & ~blank_these_bits_please

            start, stop = get_start_stop(prev_index, current_indices)

            if start < 0:
                start = 0
            elif stop < 0:
                break

            if concatenate:
                string = subclass(self.unwrapped[start:stop] + string)
            elif start != stop:
                list_ = [subclass(self.unwrapped[start:stop])] + list_

            # Now we set our previous index to exclude the bitvals we're slicing out
            prev_index.stop = current_indices.start - cluster_length
            # Finally, we set the new bitmask so the values we just looked at are blanked
            bitmask = next_bitmask

        if concatenate:
            return string
        return list_


    def sliceby(self, name_of_bitmask, concatenate=False, subclass=str, bitval_to_compile=0):
        return self._slice_by_bitmask(getattr(self, f"_{name_of_bitmask}"), concatenate=concatenate,
                                      bitval_to_compile=bitval_to_compile, subclass=subclass)


    # The methods below make the MaybeNumber object usable as an int/float/string without explicit conversion.
    # This is a more "Pythonic" way of looking at MaybeNumber, which allows you to use ducktyping and exception
    # handling to brute force your way through a parse.


    def __bool__(self):
        return bool(self._original)

    def __str__(self):
        return str(self._original)

    def __add__(self, other):
        return self.convert() + other

    def __sub__(self, other):
        return self.convert() - other

    def __radd__(self, other):
        return other + self.convert()

    def __rsub__(self, other):
        return other - self.convert()

    def __mul__(self, other):
        return self.convert() * other

    def __truediv__(self, other):
        return self.convert() / other

    def __invert__(self):
        return 1 / self.convert()

    def __repr__(self):
        return repr(self.unwrapped)

    def __iter__(self):
        yield from self.unwrapped

    def __getitem__(self, item):
        return self._original.__getitem__(item)

    def __len__(self):
        return len(self._original)

    def __eq__(self, other):
        if other == self.unwrapped:
            return True
        if other == self.convert():
            return True
        return False

    def __contains__(self, item):
        return item in self.unwrapped

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

    def __neg__(self):
        return -self.convert()

    def __and__(self, other):
        return self.convert() & other

    def __or__(self, other):
        return self.convert() | other

