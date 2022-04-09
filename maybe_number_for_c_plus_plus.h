#ifndef MaybeNumber_h
#define MaybeNumber_h
#include <iostream>
#include <vector>
#include <limits>
#include <math.h>
#include <deque>
#include <functional>
#include "maybe_number_constants.h"

// (c) 2022 Shoshi (Sharon) Cooper.  No duplication is permitted for commercial use.  Any significant changes made must be
// stated explicitly and the original source code, if used, must be available and credited to Shoshi (Sharon) Cooper.


// This class is about converting things from non-numbers to numbers without having to re-iterate the number a second time upon conversion.
// It is useful in a number of ways:
//    1) O(1) conversion to a number is mutable along with the string
//         a) As you push_back to the string or pop_back from the string, the number changes as well
//         b) That conversion is also O(1) time.
//    2) Many useful tokenization methods
//    3) For delimited spreadsheet that contain the delimiter inside quotation marks, this class has a way to tokenize around that problem.
//    4) Conversion of strings "TRUE", "FALSE" to proper booleans and "inf" to infinity
//    5) Lowercase/Uppercase conversion (special for C++) -- if done inplace, this can be much faster average time than normal.
//    6) You can immediately tell if a number is a double, an int, or a negative number by checking the multiplier and isdot
//    7) If you tokenize based on dashes, you can use this to extract the numbers you need for a date.

// Since this is C++, where classes tend to be sparser, I might have crammed too much utility into this class.
// It may be more useful to create subpieces of this class and use those instead.


// TODO:
//   This was very much designed for really short strings (ex. like you'd have on one cell of a spreadsheet).
//   However, when I discovered the class could be used more broadly, it became clear that I had to get the
//   MaybeNumber class to support longer strings.
//   RIGHT NOW, THE MAYBENUMBER CLASS OVERFLOWS FOR LONGER STRINGS.
//   This is particularly causing trouble in the sliceby method, because to leap from cluster to cluster, I flip between
//   bitmask and ~bitmask, which allows me to use the (bitmask & (bitmask - 1)) trick to figure out where to leap to.
//   However, ~bitmask is a signed integer, so it's getting truncated even when the size_t bitmask is not.  Since I also
//   use ~bitmask to cancel off the bits I don't want in bitmask, I wind up in an endless loop where the bits I want to cancel
//   are never actually cancelled.
//
//   For now, I'll raise an exception if the string is too long and you try to use the sliceby
//   method, but this really should be fixed in the future.

// Other TODO items:
//   Find a different way to identify the bitmasks.  Currently using strings, which is not C++ish.
//     Strings are big and bulky and should not thrown around lightly in C++.
//   I shoved in the for-loop in _get_bitmask because I just needed to write something fast.  I hate it.
//     I do not want to iterate the entire vector just to get one bitmask inside of it!
//   Although passing lambdas seems to work pretty well, it does not feel so C++ish to me.


// For now, this will be the error I throw if the string is too long to do sliceby
struct TooLongStringError : public std::exception{
   std::string s;
   TooLongStringError(std::string ss) : s(ss) {}
   ~TooLongStringError() throw () {}
   const char* what() const throw() { return s.c_str(); }
};




class MaybeNumber{
    public:
        // Where we will store the bitmasks and their names and additive functions.
        struct Bitmask {
            public:
                typedef std::function<bool(char, std::vector<Bitmask>&, size_t)> LambdaType;
                std::string name;
                size_t bitmask;
                LambdaType alt_func;

                Bitmask(std::string bitmask_name, LambdaType function):
                    name(bitmask_name), bitmask(0b0), alt_func(function){};
                void push_back(char letter, std::vector<Bitmask>& btmsks, size_t len_bitmasks){
                    bool bit = alt_func(letter, btmsks, len_bitmasks);
                    bitmask = (bitmask << 1) | (int)bit;
                }
                void pop_back(){bitmask >>= 1;}

                std::string to_string() const;
        };

    private:
        std::string original;
        char _token;
        std::vector<Bitmask> the_bitmasks;
        double _multiplier, _place, _forcenumber;
        size_t _len_bitmasks;

        void _setup();
        void _pop_back_internals();

        // This method generally adjusts the bitmask in compliance with the vector
        void _adjust_bits(const char c);
        void _adjust_bits();

    protected:
        size_t len_bitmasks() const {return _len_bitmasks;}

        static bool is_in(const char letter, const char* array, size_t array_length){
            for (size_t i = 0; i < array_length; i++){
                if (array[i] == letter){
                    return true;
                }
            }
            return false;
        }
        static bool not_in(const char letter, const char* array, size_t array_length){return is_in(letter, array, array_length)? false: true;}

        Bitmask _get_bitmask(std::string bitmask_name) const;
        size_t _get_slice_index(size_t bitmask) const;
        size_t _get_slice_index(long long int bitmask, size_t length) const;

        bool static _is_only_one_bit_on(size_t number){return (number & (number - 1)) == 0;}

        std::string _convert_upper_or_lower(std::string bitmask_name) const;
        void _convert_upper_or_lower_inplace(std::string bitmask_name);
        void _convert_bool(size_t* ptr) const;

        struct AnIndex{long long int start, stop;};
        void _slice_by_bitmask(std::deque<MaybeNumber>& vec, size_t bitmask, bool bitval_to_compile=false) const;
        std::string _concat_by_bitmask(size_t bitmask) const;

        struct Slice{size_t start, end;};
        size_t _get_slice_indices_from_bitmask(std::deque<Slice>& vec, size_t bitmask) const;


        // populates the vector containing all bitmasks -- use this to add new bitmasks
        virtual void _populate_bitmask_vector(std::vector<Bitmask>& bitmask_vector);
        // some useful getters
        size_t isdot(){return _get_bitmask("ISDOT").bitmask;}

    public:
        MaybeNumber(std::string s="", char token=32);
        MaybeNumber(const char c, char token=32);
        // MaybeNumber(const MaybeNumber& that);
        void push_back(const char letter);
        void pop_back(MaybeNumber& empty);
        void pop_back();
        char token(){return _token;}


        // To figure out what it actually is inside here
        enum TypeValues {SIGNEDINTTYPE, DOUBLETYPE, SIZE_TTYPE, BOOLTYPE, STRINGTYPE};

        TypeValues get_type() const;
        // returns true if the string value in the MaybeNumber is actually a number
        bool isnumber() const;
        // returns true if there is no string value inserted into the MaybeNumber
        bool isempty() const {return original.size() == 0;}

        // clears the string
        void clear();

        // returns the size of the string
        size_t size() const {return original.size();}

        // convert all elements that are lowercase to uppercase and vice versa
        std::string lower() const {return _convert_upper_or_lower("ISUPPER");}
        std::string upper() const {return _convert_upper_or_lower("ISLOWER");}
        void lower_inplace() {_convert_upper_or_lower_inplace("ISUPPER");}
        void upper_inplace() {_convert_upper_or_lower_inplace("ISLOWER");}

        MaybeNumber& operator =(const MaybeNumber& that);
        MaybeNumber& operator +=(const char letter){push_back(letter); return *this;}
        MaybeNumber& operator +=(std::string s){for (size_t i = 0; i < s.size(); i++){push_back(s[i]);}; return *this;}

        double force_to_number() const {return _forcenumber * _multiplier;}

        operator bool() const;
        operator int() const;
        operator size_t() const;
        operator double() const;
        operator std::string() const {return original;}

        std::string unwrapped() const {return original;}

        std::string tostring_all_bitmasks() const;
        std::string tostring_one_bitmask(std::string bitmask_name) const;

        // Allowing you to slice by different bitmasks
        std::deque<MaybeNumber> sliceby(std::string bitmask_name, bool bitval_to_compile=0) const;

        friend class TestMaybeNumber;
};

#endif