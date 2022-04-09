<b>About MaybeNumber</b>

This was originally designed to solve a very specific problem, but it has wound up being
useful in other situations as well.

<b>The original problem:</b>

text.split() doesn't work well when you have a delimiter appearing inside a delimited spreadsheet.  You have
to use a stack to tell which is the delimiter and which you have to add back in.
For example, if parsing a *.csv file that contains a line of numbers, all of which have internal commas:

    Example Line:
        '"123,456.89", "888,444,111.20", "$ (13,146.01)", "8,000%"'
    Using line.split(',') results in:
        ['"123', '456.89"', ' "888', '444', '111.20"', ' "$ (13', '146.01)"', ' "8', '000%"']
    But what we want is:
        ["123,456.89", "888,444,111.20", "$ (13,146.01)", "8,000%"]
        which is simple to do if you use a stack to tell you which "," is inside the quotes.

However, while this is simple to do, you have to loop through each character again to cast this from a string to a
float/double.  The accounting format negatives (and the % symbol) add an additional complexity, as the string must be
modified to convert properly into the correct float/double.
And what if you're unsure whether or not the column you're converting is actually a number rather than (for example)
a date?  Or if you're parsing an IRS table and come across the typical IRS trick of putting in BOTH the percent and the
float/double so it looks like "50% (0.50)"?

By the time you are done, the strings have been looped over and over and over again.  With a large spreadsheet,
this can make a huge difference in runtime!


<b>The solution to the original problem:</b>

The original idea was that MaybeNumber would attempt to convert the text into a number as you parsed it.  Each
time a character is added to the MaybeNumber, the class figures out what that new character does to the potential
number it's creating.

But how do we know if this really is number without looping through letters yet again?

Answer: bitmasks.

MaybeNumber contains a series of bitmasks, each analyzing a certain crucial element of the text.  For example,
the isdash bitmask adds a 1 if a letter is a dash '-' character, and a 0 otherwise.
There are things we can do with bitmasks in O(1) time that would otherwise require iteration.  For example, how do
we tell that '07-15-2022' is not a number?  It has two '-' characters, which means it can't be.  MaybeNumber knows
this in O(1) time because it can turn off the least significant bit of the isdash bitmask.  If the result is 0,
there is only 1 dash.  Otherwise, there are several.

It's true that this adds some additional runtime each time you add a letter, but the idea is that this additional
runtime would not take very long, and the memory required to store it would not be very large.
Small note: in languages that are not Python, long strings may be problematic.

<b>Push/Pop</b>

Python does not have mutable strings.  I wanted to give people a way to "push_back" or "pop_back" to a MaybeNumber
the way one does with a std::string in C++.  Pushing/popping allows us to do the following:

    maybe = MaybeNumber("")
    while len(maybe) == 0 or maybe.isnumber():
        maybe.append(text_i_am_parsing[i])
    maybe.pop()

This winds up being quite useful if you are parsing, let's say, two numbers listed one after the other.

Example: "50% (0.50)"

Once we get to the "(0.50)", MaybeNumber will recognize that the '(' is not in front so this is no longer
a number.  This leaves us with 50%, which MaybeNumber already knows is 0.50.

<b>Expanded uses</b>

I later discovered some other uses for MaybeNumber:

1) Language parser requires you to parse the same thing over and over again
    While attempting to program an AI chatbot, the number of loops I did over the same text quickly grew out of
    hand.  We have to remove punctuation, except if it's a number, and we have to split it in several ways...
    oy vey!  Why not do all of this in a single step during that first iteration?  Add a bitmask for what to
    exclude (ex. punctuation) and we can easily get rid of it later.

2) Changing one or two letters in a mutable string (C++)
    In C, string are character arrays.  Array length is immutable, but all array contents are mutable.  Yet we
    know basically nothing about C-strings (not even how long they are) so we quickly throw away our advantage
    and resort to using loops instead.
    So why not record attributes about the characters as we add them?  We can leap back and change them easily!
    This won't affect the O(n) but will drastically decrease the average time.

3) Same problem parsing web text -- the "<" and ">" require a stack to parse them, so you're stuck re-iterating
    to do anything else to the text inside!

4) Slicing by a category of characters or a particular situation, rather than a single character.
    There's a trick you can use to slice bitmasks more efficiently by "leaping" to the spot where you have to
    slice next without having to iterate the middle characters.  This is achieved by using ~bitmask and some
    mathematics to derive the index you need to arrive at next.
    This trick allows you to see if a bitmask has a particular start or end in O(1) time.  However, it does not
    change the O(n) for slicing -- since there is always the possibility that your bitmask is 1010101010101.
    However, there should be a much improved average time, especially in C (where bitmasks are fast).
    
    
        Example: Given a phrase with many numbers in it, you can slice the phrase to only show you the digits.
    
        "This morning I walked 5 miles and bought 200 apples at 4991 Main Street"
        slice by isdigit:
            [5, 200, 4991]



<b>Known issues:</b>

- I do not check that the closing parentheses ) is at the end of the string.
- For 'inf': *.isnumber() returns False in the Python version, but True in the C++ version.
    The inconsistency is because of how I had to do the casting in C++, which required me to figure out
    each type's equivalent of infinity so I could convert it properly -- hence, I had to make isnumber return
    True so the casting would work.
    In Python, however, doing the same thing would cause the convert() method to not work properly.
    I should find some way to make the behavior more consistent between the two languages.
- In the subclass that parses dates, I have problems when a person's name is a month
    (ex. a woman named April or June) or when there are two dates that are close together.  It sometimes has
    trouble telling which numbers go with which date.
- subclassing is much easier in the Python version than the C++ version.
- In C++ version: when string gets too long, bitmask will overflow.  Particularly problematic in slicing method.  For now, I throw an exception in the C++ version, but this should be easy enough to fix.  I just haven't yet.







