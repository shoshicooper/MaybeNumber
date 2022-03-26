"""
(c) 2022 Shoshi (Sharon) Cooper.  No duplication is permitted for commercial use.  Any significant changes made must be
stated explicitly and the original source code, if used, must be available and credited to Shoshi (Sharon) Cooper.

A subclass of MaybeNumber.

What it does that's extra:
    BIG DIFFERENCE: it's hooked up to a trie so it can see if something is a word or not.
        At the moment, I only have this to look for month names but could be expanded to look for other words.

    Additional functionality:
        isdate(): checks if there is a date inside the string somewhere.  Returns bool.
        convert_date(): Parses and converts string dates to datetime class
                        Works for "1/1/2020", "1.1.2020", "1-1-2020", "1 1 2020", etc.
                        Also for "Dec. 31st, 2020" and "the 13th day of November in the year 2020"
        better token splitting: Splits by the token given in __init__.  However, if a date is detected,
                                the date will be kept as a single unit rather than being split up by the token.
                                This allows you to split by space, but still keep the dates together for conversion.

                    Example: "Sally bought the property on this 11th day of August, 2021"
                            Will be split into:
                                ["Sally", "bought", "the", "property", "on", "this",
                                 "11th day of August, 2021"]
                            That will give you the ability to convert the final date into a datetime obj.

Known issues:
    - Did not write this one in C++
    - Gets confused when someone is named April or June or any other month name.
    - There are issues when there are two extended word-dates in a row.  Sometimes, chooses day/year for wrong month.
    - Requires a 4 digit year (I did that deliberately but have not decided if I am happy with that.)
"""
import collections
import datetime
from maybe_number_superclass import *
from trie import Trie


class CheckDate(MaybeNumber):
    MONTHS = {'Jan': 1, 'January': 1, 'Jan.': 1, 'Feb': 2, 'Feb.': 2, 'February': 2,
              'Mar': 3, 'Mar.': 3, 'March': 3, 'Apr': 4, 'Apr.': 4, 'April': 4,
                     'May': 5, 'June': 6, 'Jun': 6, 'Jun.': 6, 'July': 7, 'Jul': 7, 'Jul.': 7,
              'Aug': 8, 'Aug.': 8, 'August': 8, 'Sept': 9, 'Sept.': 9, 'Sep': 9, 'Sep.': 9,
              'September': 9, 'Oct': 10, 'Oct.': 10, 'October': 10,
                     'Nov': 11, 'Nov.': 11, 'November': 11, 'Dec': 12, 'Dec.': 12, 'December': 12}


    # OVERRIDE FOR __INIT__:


    def __init__(self, text="", token=' '):
        super().__init__(tokenize_by=token)
        self._month_trie = import_month_trie(Trie())

        self._date_items = {
            'date_numbers': [],
            'is_over_12': 0b0,
            'is_four_digits': 0b0,
            'is_over_31': 0b0,
            'is_zero': 0b0,
            'date_bitlength': 0,
            # Date lambdas are what we'll use to assess whether or not the bit is turned on
            # tuple format: (keyvalue, lambda expression, clear bit first?)
            'date_lambdas': [('is_over_12', lambda x: x > 12, False),
                             ('is_over_31', lambda x: x > 31, False),
                             ('is_zero', lambda x: x == 0, True),
                             ('is_four_digits', lambda x: 999 < x < 10_000, True)],
            'indices': [],
        }


        for letter in text:
            self.append(letter)


    # ADDITIONAL BITMASKS ADDED:


    def _bitmask_names(self):
        lst = super()._bitmask_names()
        additional = ['is_comma', 'is_space', 'is_in_nodeword',
                      'is_month', 'isslash', 'is_part_month', 'is_part_month_finished', 'is_apostrophe',
                      'isfourdigits',
                      ]
        return lst + additional

    def _get_additive_functions(self):
        """Override for this to add some bitmasks"""

        # Some extra complex functions to figure out if it's a 1 or a 0 at the end

        def get_pos_index(bitmask_names):
            possible = []
            for name in bitmask_names:
                bitmask = getattr(self, f"_{name}")
                if bitmask:
                    possible += [self._get_slice_index(bitmask)]
            if not possible:
                return None
            return max(possible)

        def is_part_english_word(trie, letter):
            """
            This could get really difficult here as I'd need to backtrack, so let's just make this simple and
            say that if there's a space, I'm treating that as a new opportunity to create a word.
            """
            # I say a space, but it could also be a period, whichever is closer
            BITMASKS = ['is_space', 'isdot']
            pos_index = get_pos_index(BITMASKS)
            if pos_index is None:
                return trie.is_wordstart(self.unwrapped + letter)
            return trie.is_wordstart(self.unwrapped[pos_index + 1:] + letter)

        def month_finish(letter):
            BITMASKS = ['is_space', 'isdot']

            if not self._is_part_month & 1:
                return False
            pos_index = get_pos_index(BITMASKS)
            if pos_index is None:
                return (self.unwrapped + letter).lower().capitalize() in self.MONTHS
            return (self.unwrapped[pos_index + 1:] + letter).lower().capitalize() in self.MONTHS




        dictionary = super()._get_additive_functions()
        dictionary['is_comma'] = lambda letter: letter == ','
        dictionary['is_space'] = lambda letter: letter == ' '
        dictionary['isslash'] = lambda letter: letter == '/'
        dictionary['is_month'] = lambda letter: self._month_trie.is_wordstart(self.unwrapped + letter)
        dictionary['is_part_month'] = lambda letter: is_part_english_word(self._month_trie, letter) and letter != ' '
        dictionary['is_part_month_finished'] = month_finish
        dictionary['is_complete_english_word'] = lambda letter: self._trie.lookup(self._nodeword[0])
        dictionary['is_apostrophe'] = lambda letter: letter == "'" or letter == "’"
        dictionary['isfourdigits'] = lambda letter: self._isdigit & 0xf == 0xf
        return dictionary



    # CHANGES TO APPEND AND POP FOR THE NEW BITMASKS


    def append(self, letter):
        super().append(letter)

        # For indices -- if the current letter is not a digit but the previous one was
        if not self._isdigit & 1 and self._isdigit & 2:
            self._date_items['indices'][-1].append(len(self.unwrapped) - 1)

        # The rest only applies if the letter is a digit.
        # These are things to allow me to construct the date as I go, rather than slicing it afterwards
        if not self._isdigit & 1:
            return

        # Adjust the date items
        scooch = False
        date_numbers = self._date_items['date_numbers']

        # If the first bit is on (last letter I checked) and the second bit is on (letter before that) then additive
        if self._isdigit & 2:
            number = date_numbers[-1] * 10 + int(letter)
            date_numbers[-1] = number

        # If the first bit is on (last letter I checked) but not the second bit, it's a new number
        else:
            scooch = True
            number = int(letter)
            date_numbers.append(number)
            self._date_items['date_bitlength'] += 1
            self._date_items['indices'].append([len(self.unwrapped) - 1])

        for key, lambda_expression, clear_first in self._date_items['date_lambdas']:
            if scooch:
                self._date_items[key] <<= 1
            elif clear_first:
                self._date_items[key] &= ~0b1
            self._date_items[key] |= lambda_expression(number)




    def pop(self, masked=False):
        popped_item = super().pop(masked)

        # To pop the ending index for a digit that may potentially keep going
        if self._isdigit & 1 and not str(popped_item).isdigit():
            self._date_items['indices'][-1].pop()

        # date adjustment
        if not str(popped_item).isdigit():
            return

        # Adjust the date items
        date_numbers = self._date_items['date_numbers']

        number = (date_numbers[-1] - int(str(popped_item))) // 10
        if number == 0:
            scooch = True
            date_numbers.pop()
            self._date_items['date_bitlength'] -= 1
            self._date_items['indices'].pop()

        else:
            scooch = False
            date_numbers[-1] = number

        for key, lamba_expression, clear_first in self._date_items['date_lambdas']:
            if scooch:
                self._date_items[key] >>= 1
            elif clear_first:
                self._date_items[key] &= 0
            self._date_items[key] |= lamba_expression(number)


    # DATE DETECTION



    def isdate(self):
        """The public method that sees if the item inside this object is or contains a date"""
        starts, monthwords = self._detect_date_locations()[:2]
        for start, monthword in zip(starts, monthwords):
            if self._isdate(start, monthword) is not False:
                return True
        return False

    def _isdate(self, start=0, monthword=None):
        """
        Private version.  If true, it returns a datetime object.  Otherwise, it returns False.
        Additionally, you can pass which date numbers you want to look at by using start and end
        """
        # This should pick up the second part of the numbers-only parse, where I try to parse it and see if it parses
        try:
            month = None
            if monthword is not None:
                month = self.MONTHS[monthword]
            return self._is_valid_date_comprehensive(start, month)
        except (ValueError, KeyError):
            return False

    def convert_date(self):
        """Detects dates in the current object and converts them into datetime objects"""
        start_locations, monthwords = self._detect_date_locations()[:2]
        dates_included = []
        for start_loc, monthword in zip(start_locations, monthwords):
            my_date = self._isdate(start=start_loc, monthword=monthword)
            if my_date is False:
                continue
            dates_included.append(my_date)

        if len(dates_included) == 0:
            raise ValueError(f"{self.unwrapped} does not contain any detected dates")

        if len(dates_included) == 1:
            return dates_included.pop()
        return dates_included


    def _get_monthword(self, bitmask):
        """
        Gets the start and ending indices for whatever word is the month name, assuming it's a word.
        I'll have it take the parameter bitmask in case there's more than one month name in the string, so I can
        choose which one I want to parse.
        """
        if not bitmask:
            raise ValueError("Month is not a word")

        # Figure out where the month name stops
        end_index = self._get_slice_index(bitmask)

        # Starting index of month name
        # To do this, I'll invert the bitmask and see where the one is.  To make it work with negative indexing, I must
        # still keep the length the same regardless
        neg_index = abs(end_index - len(self.unwrapped))
        remaining = ~(self._is_part_month >> neg_index)
        remaining <<= neg_index
        # Yes, I know I'm basically just turning all the things before neg_index to zero here and I should have a better
        # way of doing that using &.  I'm just having a brainfreeze right now.
        start_index = self._get_slice_index(remaining)
        return start_index, end_index


    # Some explanation of what I'm doing to figure out where everything is and these checks:
    #
    # First of all, I need to make sure we only look at the numbers comprising the date.  Since there may be other
    # numbers in the line, I will use another method to figure out which numbers are applicable and then pass through
    # the start and end parameters to the _is_valid_date_comprehensive method to see how to slice my date numbers.
    # start = starting index
    # end = exclusive ending index
    #
    # For the informational bitmasks, I will create a new mask to hide whichever bits I don't care about at the moment.
    # The most confusing part of all this is the fact that these bitmasks, unlike most of the others in this class,
    # actually do go forward (not backward).  So start cancels off the MSBs and end cancels of the LSBs.
    #
    # My informational bitmasks contain the following:
    #    is_over_12: if a number is larger than 12, it cannot possibly be the month
    #    is_zero: For a series of numbers to be a date, no number can be zero
    #    is_over_31: If a number is larger than 31, it must be a year
    #    is_four_digits: I added this one to just make the year clearer and to establish that I'm not going to be
    #                    messing around with the possibility that 29 is the year not the day because it's February
    #                    or anything like that.  I'm keeping this on a somewhat simpler level.
    #
    # Using these, I should be able to get an estimate of generally where the day and month are -- and to cancel out
    # obviously incorrect dates.  I'll detail some of that below:
    #
    #   ESTABLISHING THE MONTH:
    #      If the month is a word, this section is skipped.
    #
    #      'could_be_month' is a variable that represents any indices that feasibly could be the month.
    #      It's derived by seeing which of the three bits in is_over_12 is turned off.
    #          > Computing the date:
    #                The trick is to see if only 1 bit is on in could_be_month
    #                If 2 bits are on, then we have a situation where we have 2 numbers below 12 and don't know which
    #                 is the month and which is the day.
    #          > Invalidity check:
    #                If no bits are on (i.e. all numbers are > 12), then this is not a date.
    #                Alternate check: determine if is_over_12 is kinda like 0b111 but shifted over << a smidge
    #
    #   ESTABLISHING THE DAY:
    #       In cases where the day is over 12 but under 31, we must extract the day's index from the bitmask.
    #         We have is_over_31, which turns bits on if the index CANNOT be a day.
    #         We have is_over_12, which turns bits on if the index is EITHER a day or a year.
    #         We do not want to flip the month bit back on.
    #
    #       > Computing the date:
    #           What I needed was a way to cancel the bit that is_over_31 has in common with is_over_12, but without
    #           turning back on the month bit.
    #           Therefore, I decided to do is_over_31 ^ is_over_12 to cancel off the two set bits.
    #           Then, I & the result with is_over_12, which will turn that month bit back to 0.
    #               # Example: 12/15/2001 is 0b011 for is_over_12 and 0b001 for is_over_31:
    #               #           0b011 ^ 0b001 = 0b110
    #               #           0b110 & 0b011 = 0b010 which gives 15 as the day which is the correct answer
    #           If this procedure results in 0b0, then there are two numbers that are less than 12 and we have to
    #           guess which is the month and which is the day.
    #
    #       > Invalidity Check:
    #            If the above procedure results in 2 bits that are turned on (instead of one bit), then it's not a date.
    #
    # There are a few other validity checks, which I get into in the method itself.
    #
    # However, beyond the basic validity checks, we really do need to parse the date to determine its validity.  So
    # this can't be quite as nice as with isnumber, where we can use bitmasks to instantly know if it's a number
    # without ever having to compute what the value might be.  For languages with compilers (not Python), having a
    # compile-time check rather than a try/except runtime check is extremely desirable.
    #
    # But for dates, the numbers all depend on one another.  To determine if the day is valid, we must know the month.
    # To determine if February 29 is valid, we must know the year.  Therefore, we have to parse the entire date.
    #
    # As a result, I decided to play a cute little Python trick and -- instead of returning a boolean -- if it is
    # a date, I return the datetime object itself.  Since __bool__ is true on that object, it still casts correctly.


    def _is_valid_date_comprehensive(self, start=0, month_number=None):
        """
        Checks if the three/two numbers from start to end are, in fact, a date -- or if they're not a valid date.
        Month number is passed if the month is a word rather than an integer.

        :param start: If you know what index in date_numbers we are starting on, then enter it here.
                      Default is 0.
        :param month_number: If the month is a word instead of an integer, then pass the number corresponding to the
                             month's name here.  The program will only look for the year and day, not the month.
        :return: If it's not a valid date, False will be returned.  If it is a valid date, the datetime object will be
                returned instead.
        """
        # Characteristics required of dates:
        #   1) Three numbers separated by something -- if word for month, then this will be 2
        #   2) At least one of those 3 numbers must be 12 or less -- unless month is a word, then this goes away
        #   3) None of the numbers can be 0
        #   4) Only one number can be greater than 31
        #   5) I also institute a check to see if the year is a 4 digit number

        # Make sure there are enough numbers that we can even have a date in the first place
        if len(self._date_items['date_numbers']) < 2:
            return False

        # First, slicing stuff
        length = 3 if month_number is None else 2

        date_numbers = self._date_items['date_numbers']
        end = length + start

        # Must cancel off any bits in informational bitmasks that apply to numbers that are not in range(start, end)
        date_bitlength = self._date_items['date_bitlength']
        all_ones = (1 << date_bitlength) - 1
        # my_mask will store the mask used to turn off all bits except in range(start, end)
        my_mask = all_ones

        # end adjustment cancels off the right side (->) of the bitmask. Ex: 0b11111 becomes 0b11110
        if end < date_bitlength:
            my_mask &= ~((1 << (date_bitlength - end)) - 1)

        # start adjustment cancels off the left side (<-) of the bitmask. Ex: 0b11110 becomes 0b01110
        if start != 0:
            var = date_bitlength - (start + 1)
            new = (1 << (var + 1)) - 1
            my_mask &= new

        # This is just a double check to make sure the mask is correct
        # shifted_mask = my_mask >> (date_bitlength - (start + length))
        # assert(shifted_mask.bit_length() == end - start), f"Mask trimmed to the wrong number of bits \n" \
        #                                                   f"{bin(shifted_mask)=}\n" \
        #                                                   f"bitlength: {shifted_mask.bit_length()}\n" \
        #                                                   f"end - start = {end - start}"

        # In my informational bitmasks, turn off any bits not in range(start, end)
        is_over_12 = self._date_items['is_over_12'] & my_mask
        is_zero = self._date_items['is_zero'] & my_mask
        is_over_31 = self._date_items['is_over_31'] & my_mask
        is_four_digits = self._date_items['is_four_digits'] & my_mask

        # Now, go down the list of rules and requirements:

        # None of the numbers can be 0
        if is_zero:
            return False
        # Only one number can be greater than 31 -- turn off lsb and see if it's 0.  If not, then more than 1 bit on.
        if not self._is_only_one_bit_on(is_over_31):
            return False

        # I'm adding this requirement for a 4-digit year because I want to make it obvious what I'm doing.  See note.
        if not is_four_digits:
            return False

        # At least one integer must be 12 or less -- unless month_number is given (then this section can be skipped)
        could_be_month, only_day = None, None
        if month_number is None:
            # Because we're slicing our bitmask, I need to slide the 0b111 (mentioned in note above) over a smidge
            shift = date_bitlength - (start + length)
            no_month = 0b111 << shift
            # Check to see if there is no number that could be a valid month
            if is_over_12 == no_month:
                return False
            # could_be_month figures out where the month may be located.  Might as well do alt check while at it.
            could_be_month = (no_month ^ is_over_12) & my_mask
            if could_be_month == 0:
                return False

            # Make sure there's a maximum of 1 integer that is > 12 and is <= 31 (i.e. only day)
            month_and_day = (is_over_12 ^ is_over_31) & my_mask
            only_day = is_over_12 & month_and_day
            if not self._is_only_one_bit_on(only_day):
                return False


        # Since it comes up for both, get the index of where we can find the year.
        # I'll do this using is_over_31 in case I want to go deeper and start playing around with years vs. days.
        yeardex = self._get_slice_index(is_over_31, date_bitlength) - 1

        # Now we get to the part where I can't determine if it's a date unless I parse the date in full.
        # Without the month_number given, this can get quite involved because it's based on societal conventions
        if month_number is None:
            day, month_number = self._parse_numeric_date(yeardex=yeardex,
                                            date_numbers=date_numbers,
                                            start=start, end=end,
                                            could_be_month=could_be_month,
                                            only_day=only_day,
                                            )
        else:
            # With the month, however, the parse is fairly simple, so I'll shove it here.
            daydex = self._get_slice_index((all_ones ^ is_over_31) & my_mask, date_bitlength) - 1
            day = date_numbers[daydex]

        # Get the year
        year = date_numbers[yeardex]

        # I'm writing this out without a try/except clause so I can re-use for compile-time languages.
        months_with_30 = {9, 4, 6, 11}
        if day > 30 and month_number in months_with_30:
            return False
        # February checks -- I could put these on the same line but I thought this was more readable
        if month_number == 2 and day > 29:
            return False
        if month_number == 2 and not self.is_a_leap_year(year) and day == 29:
            return False
        # Create datetime object
        return datetime.date(year=year, day=day, month=month_number)


    def _parse_numeric_date(self, could_be_month, only_day, yeardex,
                            date_numbers, start=0, **kwargs):
        """
        Parses a date if it's entirely made up of numbers.
        While the code here is a little long, the hope is that because it's all using bitmasks and no loops, it's
        ultimately quite a bit shorter and smoother to run.  May only be true in C though.
        """
        date_kwargs = {'month': None, 'day': None, 'year': None}
        used = 0b1000

        shift = self._date_items['date_bitlength'] - (start + 3)
        # 4 = first, 2 = middle, 1 = last
        position = {4 << shift: 0 + start, 2 << shift: 1 + start, 1 << shift: 2 + start}

        # Get the year
        used |= (1 << (yeardex - start))
        date_kwargs['year'] = int(date_numbers[yeardex])


        # Check for day
        if only_day:
            daydex = position[only_day]
            date_kwargs['day'] = int(date_numbers[daydex])
            used |= (1 << (daydex - start))

        # Check for month
        if self._is_only_one_bit_on(could_be_month):
            monthdex = position[could_be_month]
            date_kwargs['month'] = int(date_numbers[monthdex])
            used |= (1 << (monthdex - start))

        # So now we get into what to do if not all the numbers have been filled in.
        # This winds up being less about math and more about convention.  I'll default to the american convention.
        if used != 0xf:
            # If the year comes first, the format is probably YYYY-MM-DD
            if yeardex == start:
                date_kwargs['month'] = int(date_numbers[1 + start])
                date_kwargs['day'] = int(date_numbers[2 + start])
            # Otherwise, I'll default to the american convention
            else:
                date_kwargs['month'] = int(date_numbers[0 + start])
                date_kwargs['day'] = int(date_numbers[1 + start])

        return date_kwargs['day'], date_kwargs['month']



    def _detect_date_locations(self):
        """
        This is for when you have a larger line item that you want chopped up into pieces.
        It's trying to figure out where the date is and extract that from the text.

        That way, the split can put the date in its own object separate from the others.
        """
        # Okay, so the date will be buried inside a bunch of other text and so on.  I have to figure out which numbers
        # are the ones I will be using

        # For the two formats:
        #   1) #/#/#### type formats: look for bitmask pattern that contains numbers with a single char in between them
        #   2) Other formats: We have where the month is and where it ends.  We must extend forward and see if we can
        #      catch the date.  Then we must also extend back.  Basically, we extend around the month name to see
        #      which digit clusters are relevant.

        # First things first, if there's no 4-digit year given, then date detection will not work
        if not self._isfourdigits:
            # raise ValueError("Year not found.  Cannot use automatic date detection")
            return [], [], []

        starts = []
        monthword = []
        where_monthwords = []
        # Start with letter months
        if self._is_part_month_finished:
            l_starts, l_monthwords, l_where = self._letter_month_find_date()
            monthword += l_monthwords
            starts += l_starts
            where_monthwords += l_where
        # Even if there is a letter month, it may also contain a number date as well
        nd_starts = self._find_three_numbers_in_pattern()
        starts += nd_starts
        monthword += [None for _ in range(len(nd_starts))]
        where_monthwords += [None for _ in range(len(nd_starts))]

        # This should detect all possible starting points for a date.  Now, I need to see if any of those are dates.
        # However, I think I'll do that in a different method, so I'll just return the starting indices here.
        return starts, monthword, where_monthwords



    def _letter_month_find_date(self):
        """
        Tries to puzzle out where the date is if there's a letter month in the string.
        This really will be a guess, though.
        """

        starts = []
        monthwords = []
        where_monthwords = []
        starts_set = set()
        months_set = set()
        month_bitmask = self._is_part_month_finished

        while month_bitmask:
            start_index, end_index = self._get_monthword(month_bitmask)

            # This is a quick check to make sure I haven't already done the month.  Ex: December and Dec
            month_text = self.unwrapped[start_index:end_index].lower()
            if (start_index, month_text) in months_set:
                month_bitmask = month_bitmask & (month_bitmask - 1)
                continue

            # I will add in the shortened month names into the month_set as well just to make sure
            months_set.add((start_index, month_text))
            for q in [3, 4]:
                if len(month_text) > q:
                    months_set.add((start_index, month_text[:q]))

            # If there's more than one place where there's a four digit number, choose the one closest to the month
            year_index = []
            where_year = None
            curr_distance = float('inf')

            year_bitmask = self._date_items['is_four_digits']
            while year_bitmask:
                i = self._get_slice_index(year_bitmask, self._date_items['date_bitlength'] - 1)
                indices = self._date_items['indices'][i]
                if len(indices) == 1:
                    indices.append(len(self.unwrapped))
                # Get distance
                if min(indices) > end_index:
                    distance = min(indices) - end_index
                elif max(indices) < start_index:
                    distance = start_index - max(indices)
                else:
                    raise IndexError("Something went wrong")

                # print(f"Month: {start_index}, {end_index};   Year: {indices} {i};   Distance: {distance}")
                if distance < curr_distance:
                    year_index = indices
                    where_year = i
                    curr_distance = distance

                year_bitmask = year_bitmask & (year_bitmask - 1)

            # now we look at the digit clusters surrounding the start and end of the month.
            after_end = (1 << (self._len_bitmasks - end_index + 1)) - 1
            previous_integers = ~after_end & self._isdigit

            # Prev integers:
            indices_before = self._loop_bitmask(previous_integers)

            # After integers:
            after_indices = self._date_items['indices'][len(indices_before):]

            # See where the year is in relation to the month
            startval = None
            # If the year is the first number after the month word, then the day is probably just before the month word
            # If the year is the second number after month word, probably month DD YYY
            if year_index in after_indices:
                year_loc = after_indices.index(year_index)
                if year_loc <= 2:
                    startval = where_year - 1

            # If the year comes first, could be "in the year YYYY, on the DDth day in the month of monthname"
            elif year_index in indices_before:
                year_loc = indices_before.index(year_index)
                if len(indices_before) - year_loc <= 2:
                    startval = where_year

            if startval is not None and startval not in starts_set:
                starts.append(startval)
                starts_set.add(startval)

                monthword = (self.unwrapped[start_index: end_index]).lower().capitalize()
                monthwords.append(monthword)
                where_monthwords.append((start_index, end_index))

            month_bitmask = month_bitmask & (month_bitmask - 1)


        return starts, monthwords, where_monthwords


    def _find_three_numbers_in_pattern(self):
        """For finding the pattern of three numbers separated by a single symbol"""
        # Check for all year numbers to see if they are good candidates.  Then see what the spaces are between
        # different integer clusters around the year
        start_date = []

        bitmask = self._date_items['is_four_digits']
        while bitmask:
            i = self._get_slice_index(bitmask, self._date_items['date_bitlength'] - 1)
            year_index = self._date_items['indices'][i]
            if len(year_index) == 1:
                year_index.append(len(self.unwrapped))

            # Now we need to figure out how much distance is between the different integers surrounding the year

            # Since year can't go in the middle, I'll do 2 ranges: one with year at start and one with year at end.
            # So it'll be
            #   range(-2, 1) where each number in range is added to year_i
            #   range(0, 3) where each number in range is added to year_i
            # Since I don't want to iterate unnecessarily, I'll optimize this by using mins and maxes
            #   max(-2 + i, 0) => it should be -2 + i, but if that's negative, then start at 0
            #   min(1 + i, end) => it should be 1 + i, but if it's longer than my list, then truncate
            #   min(i + 3, end) => it should be i + 3, but if it's longer than my list, then truncate
            end = self._date_items['date_bitlength']
            for my_range in [range(max(-2 + i, 0), min(1 + i, end)), range(i, min(i + 3, end))]:
                start_x = None
                cluster_length = 0
                prev_index = None

                for x in my_range:
                    index_of_cluster = self._date_items['indices'][x]

                    # Now I go through and tally up how many are 1 apart from each other

                    if prev_index is None:
                        cluster_length, start_x = 1, x
                    # More than one apart
                    elif prev_index[-1] + 1 != index_of_cluster[0]:
                        cluster_length, start_x = 1, x
                    else:
                        cluster_length += 1

                    prev_index = index_of_cluster
                    if cluster_length == 3:
                        break

                # Outside of the inner loop
                if cluster_length < 3:
                    continue

                if self._is_valid_date_comprehensive(start_x):
                    start_date.append(start_x)

            bitmask = bitmask & (bitmask - 1)
        return start_date




    def _loop_bitmask(self, bitmask):
        indices = collections.deque([])
        while bitmask:
            pos_index = self._get_slice_index(bitmask, len(self.unwrapped))
            neg_index = len(self.unwrapped) - (pos_index - 1)

            stop = pos_index

            scooched_bitmask = bitmask >> (neg_index - 1)
            if scooched_bitmask == 1:
                break

            new_length = len(self.unwrapped) - neg_index + 1
            cluster_length = new_length - self._get_slice_index(~scooched_bitmask, new_length)

            start = pos_index - cluster_length
            blank_these_bits_please = (1 << (neg_index + cluster_length - 1)) - 1

            if start < 0:
                start = 0
            elif stop < 0:
                break

            indices.appendleft([start, stop])
            bitmask = bitmask & ~blank_these_bits_please
        return indices


    @staticmethod
    def is_a_leap_year(yyyy):
        """Checks if a date is a leap year or not"""
        if yyyy % 4 != 0:
            return False
        if yyyy % 100 != 0:
            return True
        return yyyy % 400 == 0






    ####  A new version of tokenize and some piecemeal methods to help you do custom loops


    def get_date_indices(self):
        """Gets all date indices"""
        # First, get all indices where a date appears.  Get the index where it starts and the index where it ends
        date_locations = []
        dateindex_locations, date_monthwords, where_monthwords = self._detect_date_locations()
        for start_loc, monthword, monthword_indices in zip(dateindex_locations, date_monthwords, where_monthwords):
            my_date = self._isdate(start=start_loc, monthword=monthword)
            if my_date is False:
                continue
            length = 3 if monthword is None else 2
            starting_index = self._date_items['indices'][start_loc][0]
            e = self._date_items['indices'][start_loc + length - 1]
            if len(e) == 1:
                ending_index = len(self.unwrapped)
            else:
                ending_index = e[-1]

            if monthword_indices is not None:
                starting_index = min(starting_index, monthword_indices[0])
                ending_index = max(ending_index, monthword_indices[-1])

            date_locations.append((starting_index, ending_index))

        # Sort these so I can pop them later
        date_locations.sort(key=lambda x: x[0])
        return date_locations

    def tokenize_self(self):
        """
        Tokenizes the line in self based on the token character given in the beginning, but also taking care not to
        split up dates or numbers.
        """
        subclass = type(self)

        if not self.unwrapped:
            return []
        if self._istoken == 0:
            return [subclass(self.unwrapped)]


        date_locations = self.get_date_indices()

        # The rest is similar to my split by bitmask method, except that it adds in the date detection

        # Create small struct to store indices
        IndexType = type("Index", (), {'start': len(self.unwrapped), 'stop': len(self.unwrapped)})
        get_start_stop = (lambda prv_idx, crnt_idx, btc: (crnt_idx.start, prv_idx.stop) if btc == 0
                          else (crnt_idx.stop, crnt_idx.start))

        # istoken with artificial 1 at beginning
        bitmask = self._istoken | (1 << (self._len_bitmasks + 1))
        prev_index = IndexType()
        list_ = collections.deque()
        bittocomp = 0

        # Now we go ahead and loop but we don't subdivide the dates
        while bitmask:
            # print(bin(bitmask))
            pos_index = self._get_slice_index(bitmask, len(self.unwrapped))
            begin = pos_index
            extra_cluster_length = 0
            # Don't divide up dates, but keep them in their own separate objects
            if date_locations:
                date_start, date_end = date_locations[-1]
                if pos_index < date_start:
                    date_locations.pop()
                # If there's a date in the middle of whatever I'm currently looking at
                elif pos_index < date_end:
                    # First, add anything currently queued up that's not a date
                    start, stop = date_end, prev_index.stop
                    if start != stop:
                        list_.appendleft(subclass(self.unwrapped[start:stop]))
                    # Now, add the date object
                    date_obj = subclass(self.unwrapped[date_start:date_end], token=self.token)
                    list_.appendleft(date_obj)
                    # Now cancel off the part of the bitmask that comprises the date
                    prev_index.stop = date_start
                    date_locations.pop()
                    begin = date_start


            neg_index = len(self.unwrapped) - (begin - 1)

            current_indices = IndexType()
            current_indices.start = begin

            scooched_bitmask = bitmask >> (neg_index - 1)
            if scooched_bitmask == bittocomp:
                break

            # So the trick is that if there is more than 1 bit turned on, I want to leap to the next change.
            # And when I do that leap, I'd rather use bitwise equations instead of a loop b/c it's faster.
            new_length = len(self.unwrapped) - neg_index + 1

            localized_end_of_cluster = self._get_slice_index(~scooched_bitmask, new_length)
            cluster_length = new_length - localized_end_of_cluster + extra_cluster_length

            # Get ending index
            current_indices.stop = begin - cluster_length - (1 - bittocomp)
            # next bitmask should be different as well
            blank_these_bits_please = (1 << (neg_index + cluster_length - bittocomp)) - 1
            next_bitmask = bitmask & ~blank_these_bits_please

            start, stop = get_start_stop(prev_index, current_indices, bittocomp)

            if start < 0:
                start = 0
            elif stop < 0:
                break

            if stop > start and bittocomp == 0:
                list_.appendleft(subclass(self.unwrapped[start:stop]))

            # Now we set our previous index to exclude the punctuation mark.  That will be our next slice point
            prev_index.stop = current_indices.start - cluster_length
            # Finally, we make the new ispunct be without the part we just sliced out
            bitmask = next_bitmask
            bittocomp = 0

        return list_


    def iter_tokens(self, bittocomp=0, subclass=str):
        """
        Iterator, iterating over token segments.
        WARNING: THIS WILL ITERATE BACKWARDS OVER THE TOKENS, NOT FORWARD!

        It yields:
            (start_index, stop_index),
            either subclass(slice) or the object it is, if it's datetime or number
        for each slice.
        To avoid slicing the object at all, just pass through subclass as None.
        """
        def yield_start_stop(starting_index, stopping_index):
            if subclass is None:
                yield starting_index, stopping_index
                return
            obj = type(self)(self.unwrapped[starting_index:stopping_index])
            if obj.isdate():
                yield (starting_index, stopping_index), obj.convert_date()
            elif obj.isnumber():
                yield (starting_index, stopping_index), obj.force_to_number()
            else:
                yield (starting_index, stopping_index), subclass(obj)

        if not self.unwrapped:
            return
        if self._istoken == 0:
            yield 0, len(self.unwrapped)
            return


        date_locations = self.get_date_indices()

        # Create small struct to store indices
        IndexType = type("Index", (), {'start': len(self.unwrapped), 'stop': len(self.unwrapped)})
        get_start_stop = (lambda prv_idx, crnt_idx, btc: (crnt_idx.start, prv_idx.stop) if btc == 0
                          else (crnt_idx.stop, crnt_idx.start))

        # istoken with artificial 1 at beginning
        bitmask = self._istoken | (1 << (self._len_bitmasks + 1))
        prev_index = IndexType()

        # Now we go ahead and loop but we don't subdivide the dates
        while bitmask:
            pos_index = self._get_slice_index(bitmask, len(self.unwrapped))
            begin = pos_index
            extra_cluster_length = 0
            # Don't divide up dates, but keep them in their own separate objects
            if date_locations:
                date_start, date_end = date_locations[-1]
                if pos_index < date_start:
                    date_locations.pop()
                # If there's a date in the middle of whatever I'm currently looking at
                elif pos_index < date_end:
                    # First, add anything currently queued up that's not a date
                    start, stop = date_end, prev_index.stop
                    if start < stop:
                        yield from yield_start_stop(start, stop)
                    # Now, yield the date as a unit
                    yield from yield_start_stop(date_start, date_end)
                    # Now cancel off the part of the bitmask that comprises the date
                    prev_index.stop = date_start
                    date_locations.pop()
                    begin = date_start

            neg_index = len(self.unwrapped) - (begin - 1)

            current_indices = IndexType()
            current_indices.start = begin

            scooched_bitmask = bitmask >> (neg_index - 1)
            if scooched_bitmask == bittocomp:
                break

            # So the trick is that if there is more than 1 bit turned on, I want to leap to the next change.
            # And when I do that leap, I'd rather use bitwise equations instead of a loop b/c it's faster.
            new_length = len(self.unwrapped) - neg_index + 1

            localized_end_of_cluster = self._get_slice_index(~scooched_bitmask, new_length)
            cluster_length = new_length - localized_end_of_cluster + extra_cluster_length

            # Get ending index
            current_indices.stop = begin - cluster_length - (1 - bittocomp)

            start, stop = get_start_stop(prev_index, current_indices, bittocomp)

            if start < 0:
                start = 0
            elif stop < 0:
                break

            if stop > start:
                yield from yield_start_stop(start, stop)

            prev_index.stop = current_indices.start - cluster_length
            blank_these_bits_please = (1 << (neg_index + cluster_length - bittocomp)) - 1
            bitmask &= ~blank_these_bits_please

        return

    def iter_tokens_forward(self, bittocomp=0, subclass=str):
        mylist = list(self.iter_tokens(bittocomp, subclass))
        yield from reversed(mylist)





    # Slicing by indices


    def sliceby_indices(self, bitmask_name, bit_to_compile=0):
        """This just gives you the starting/stopping indices for whatever bitmask you want to slice"""
        bitmask = getattr(self, f"_{bitmask_name}")
        # Add artificial 1 at beginning
        bitmask = bitmask | (1 << (self._len_bitmasks + 1))

        get_start_stop = (lambda prv_idx, crnt_idx: (crnt_idx.start, prv_idx.stop) if bit_to_compile == 0
                          else (crnt_idx.stop, crnt_idx.start))

        IndexType = type("Index", (), {'start': len(self.unwrapped), 'stop': len(self.unwrapped)})

        prev_index = IndexType()
        indices = collections.deque()

        while bitmask:
            pos_index = self._get_slice_index(bitmask, len(self.unwrapped))
            neg_index = len(self.unwrapped) - (pos_index - 1)

            current_indices = IndexType()
            current_indices.start = pos_index

            scooched_bitmask = bitmask >> (neg_index - 1)
            # Because I put in an artificial 1 to flush things out
            if scooched_bitmask == bit_to_compile:
                break

            # So the trick is that if there is more than 1 bit turned on, I want to leap to the next change.
            # And when I do that leap, I'd rather use bitwise equations instead of a loop b/c it's faster.
            new_length = len(self.unwrapped) - neg_index + 1

            localized_end_of_cluster = self._get_slice_index(~scooched_bitmask, new_length)
            cluster_length = new_length - localized_end_of_cluster

            # Get ending index
            current_indices.stop = pos_index - cluster_length - (1 - bit_to_compile)

            start, stop = get_start_stop(prev_index, current_indices)

            if start < 0:
                start = 0
            elif stop < 0:
                break

            indices.appendleft((start, stop))
            prev_index.stop = current_indices.start - cluster_length

            blank_these_bits_please = (1 << (neg_index + cluster_length - bit_to_compile)) - 1
            bitmask &= ~blank_these_bits_please

        return indices


def import_month_trie(mytrie):
    """Adds all the months to a trie"""
    months = [["Jan", ["uary", ".", ""]], ["Feb", ["ruary", ".", ""]], ["Mar", ["ch", ".", ""]],
              ["Apr", ["il", ".", ""]], ["May", ["", "."]], ["Jun", ["e", ".", ""]], ["Jul", ["y", ".", ""]],
              ["Aug", ["ust", ".", ""]], ["Sep", ["t", "t.", ".", "", "tember", "temb", "temb."]],
              ["Oct", ["ober", ".", ""]], ["Nov", ["ember", ".", ""]], ["Dec", ["ember", ".", ""]],
              ]
    for month_cluster in months:
        stem = month_cluster[0]
        node = mytrie.insert_prefix(stem)
        for suffix in month_cluster[1]:
            mytrie.insert_from_node(suffix, node)
    return mytrie



