#include "maybe_number_for_c_plus_plus.h"
#include <functional>
#include <deque>

std::string MaybeNumber::Bitmask::to_string() const{
    std::string my_string = "<" + name + ", 0b";
    std::string backwards_string_of_bitmask;
    size_t my_btmsk = bitmask;
    if (my_btmsk == 0)
        return my_string + "0>";

    while (my_btmsk){
        backwards_string_of_bitmask.push_back((my_btmsk & 1) ? '1': '0');
        my_btmsk >>= 1;
    }
    for (size_t x = 0; x < backwards_string_of_bitmask.size(); x++){
        size_t index = backwards_string_of_bitmask.size() - 1 - x;
        my_string.push_back(backwards_string_of_bitmask[index]);
    }
    return my_string + ">";
}



void MaybeNumber::_setup(){
    _multiplier = 1.0;
    _place = 1.0;
    _forcenumber = 0.0;
    _populate_bitmask_vector(the_bitmasks);
    _len_bitmasks = 0;
}

MaybeNumber::MaybeNumber(std::string s, char token): original(""), _token(token){
    _setup();
    for (size_t i = 0; i < s.size(); i++){
        push_back(s[i]);
    }
}

MaybeNumber::MaybeNumber(const char c, char token): original(""), _token(token){
    _setup();
    push_back(c);
}

void MaybeNumber::_populate_bitmask_vector(std::vector<Bitmask>& bitmask_vector){
    bitmask_vector.push_back(MaybeNumber::Bitmask("ISNUMBERELEM",
        [](const char letter, std::vector<Bitmask>& bitmasks, size_t length)
        {return is_in(letter, ALL_NUM_ELEMENTS, 24);}));
    bitmask_vector.push_back(MaybeNumber::Bitmask("ISDASH",
        [](const char letter, std::vector<Bitmask>& bitmasks, size_t length)
        {return letter == '-';}));
    bitmask_vector.push_back(MaybeNumber::Bitmask("ISDOT",
        [](const char letter, std::vector<Bitmask>& bitmasks, size_t length)
        {return letter == '.';}));
    bitmask_vector.push_back(MaybeNumber::Bitmask("ISDIGIT",
        [](const char letter, std::vector<Bitmask>& bitmasks, size_t length)
        {return letter >= 48 && letter < 58;}));
    bitmask_vector.push_back(MaybeNumber::Bitmask("ISTOKEN",
        [&](const char letter, std::vector<Bitmask>& bitmasks, size_t length)
        {return letter == this->token();}));
    bitmask_vector.push_back(MaybeNumber::Bitmask("ISDEFNOTNUMBER",
        [](const char letter, std::vector<Bitmask>& bitmasks, size_t length)
        {return not_in(letter, ALL_NUM_ELEMENTS, 24);}));
    bitmask_vector.push_back(MaybeNumber::Bitmask("ISUPPER",
        [](const char letter, std::vector<Bitmask>& bitmasks, size_t length)
        {return letter >= 65 && letter < 91;}));
    bitmask_vector.push_back(MaybeNumber::Bitmask("ISLOWER",
        [](const char letter, std::vector<Bitmask>& bitmasks, size_t length)
        {return letter >= 97 && letter < 123;}));
    bitmask_vector.push_back(MaybeNumber::Bitmask("ISACCEPTABLESTART",
        [](const char letter, std::vector<Bitmask>& bitmasks, size_t length)
        {
            if (letter != ' ' && not_in(letter, CURRENCIES, 3))
                return false;
            // This just is checking to see if we're only dealing with the start of the number
            for (size_t i = 0; i < bitmasks.size(); i++){
                if (bitmasks[i].name == "ISACCEPTABLESTART"){
                    if (length > 0)
                        return bitmasks[i].bitmask == (size_t)((1 << length) - 1);
                    break;
                }
            };
            return true;
        }));
    bitmask_vector.push_back(MaybeNumber::Bitmask("ISACCEPTABLEEND",
        [](const char letter, std::vector<Bitmask>& bitmasks, size_t length)
        {return is_in(letter, ACCEPTABLE_ENDS, 2);}));
    bitmask_vector.push_back(MaybeNumber::Bitmask("ISCLOSEDPAREN",
        [](const char letter, std::vector<Bitmask>& bitmasks, size_t length)
        {return letter == ')';}));
    bitmask_vector.push_back(MaybeNumber::Bitmask("ISOPENPAREN",
        [](const char letter, std::vector<Bitmask>& bitmasks, size_t length)
        {return letter == '(';}));
    bitmask_vector.push_back(MaybeNumber::Bitmask("ISPERCENT",
        [](const char letter, std::vector<Bitmask>& bitmasks, size_t length)
        {return letter == '%';}));
    bitmask_vector.push_back(MaybeNumber::Bitmask("ISCURRENCY",
        [](const char letter, std::vector<Bitmask>& bitmasks, size_t length)
        {return is_in(letter, CURRENCIES, 2);}));
}


MaybeNumber::Bitmask MaybeNumber::_get_bitmask(std::string bitmask_name) const{
    for (size_t i = 0; i < the_bitmasks.size(); i++){
        if (the_bitmasks[i].name == bitmask_name)
            return the_bitmasks[i];
    }
    throw std::out_of_range("Cannot return " + bitmask_name);
}




// Adjust for push_back
void MaybeNumber::_adjust_bits(const char c){
    for (size_t i = 0; i < the_bitmasks.size(); i++){
        the_bitmasks[i].push_back(c, the_bitmasks, _len_bitmasks);
    }
    _len_bitmasks ++;
}

// Adjust for pop_back
void MaybeNumber::_adjust_bits(){
    for (size_t i = 0; i < the_bitmasks.size(); i++){
        the_bitmasks[i].pop_back();
    }
    _len_bitmasks --;
}


void MaybeNumber::push_back(const char letter){
    if (letter == '\0')
        return;

    // checking if letter is "(" or "-".  (number) means negative in accounting.  -number also means negative.
    if (letter == '(' or letter == '-'){
        _multiplier *= -1.0;
    }
    // if letter == "%"
    else if (letter == '%'){
        _multiplier *= 0.01;
    }

    // add bits for the letter we are adding and push back onto the original
    _adjust_bits(letter);
    original.push_back(letter);

    // If it's a period, we must adjust the place
    if (letter == 46){
        _place = 0.1;
        return;
    }

    // This is the part where we create the numeric value of the item in real time while we are already parsing it.
    // This will be helpful because it means that we will not have to reparse it later to is if it is a number and/or convert it into a number.
    if (is_in(letter, ALL_NUM_ELEMENTS, 24) && not_in(letter, IGNORE, 13)){
        double ltr = letter;
        double to_add = ltr - 48;
        if (!isdot()){
            _forcenumber = (_forcenumber * 10.0) + to_add;
        }
        else{
            _forcenumber += (to_add * _place);
            _place = _place / 10.0;
        }
    }
}

bool MaybeNumber::isnumber() const{
    // if there are no number elements or there are no digits found inside the string, then this is false
    if (_get_bitmask("ISNUMBERELEM").bitmask == 0 || _get_bitmask("ISDIGIT").bitmask == 0)
        return false;
    if (_get_bitmask("ISDEFNOTNUMBER").bitmask != 0)
        return false;
    // numbers cannot have more than one period or dash
    // So if these bitmasks have more than one
    std::string cannot_be_doubled[6] = {"ISDOT", "ISDASH", "ISCURRENCY", "ISOPENPAREN", "ISCLOSEDPAREN",
                                "ISPERCENT"};
    for (size_t i = 0; i < 6; i++){
        MaybeNumber::Bitmask btmsk = _get_bitmask(cannot_be_doubled[i]);
        if (btmsk.bitmask == 0)
            continue;
        // If there's only one bit on, then turning off the lsb will give us 0.  If there's more than one bit on, this won't be true.
        if (btmsk.bitmask > 0 && ((btmsk.bitmask & (btmsk.bitmask - 1)) != 0))
            return false;
    }

    // -200 and (200) are two different ways of writing negative two hundred.  However, (-200) does not mean
    // -1 * -1 * 200.  Instead, the extra () make this no longer be a number.
    // So we must make sure that isdash and isopenparen/isclosedparen don't mix in same number
    if (_get_bitmask("ISDASH").bitmask != 0 && _get_bitmask("ISOPENPAREN").bitmask != 0)
        return false;
    if (_get_bitmask("ISDASH").bitmask != 0 && _get_bitmask("ISCLOSEDPAREN").bitmask != 0)
        return false;

    // Check open parenthesis is closed
    if (_get_bitmask("ISOPENPAREN").bitmask != 0 && _get_bitmask("ISCLOSEDPAREN").bitmask == 0)
        return false;
    if (_get_bitmask("ISCLOSEDPAREN").bitmask != 0 && _get_bitmask("ISOPENPAREN").bitmask == 0)
        return false;

    // make sure the negative starts the number
    if (_multiplier < 0){
        size_t start = 0;
        size_t is_acceptable_start = _get_bitmask("ISACCEPTABLESTART").bitmask;
        if (is_acceptable_start > 0){
            start = _get_slice_index(is_acceptable_start);
        }
        bool is_dash = _get_bitmask("ISDASH").bitmask > 0;
        if (is_dash && original[start] != '-')
            return false;
        if (!is_dash && original[start] != '(')
            return false;
    }
    // If multiplier is fractional, see if the % ends the string
    size_t is_percent = _get_bitmask("ISPERCENT").bitmask;
    if (is_percent > 0){
        size_t o = original.size() - 1;
        while (original[o] == ')' || original[o] == ' ')
            o--;

        if (original[o] != '%')
            return false;
    }
    return true;
}

size_t MaybeNumber::_get_slice_index(size_t bitmask) const{
    return _get_slice_index(bitmask, original.size());
}

size_t MaybeNumber::_get_slice_index(long long int bitmask, size_t length) const {
    size_t difference, pos_index;
    long long signed int index;

    // Turn off the least significant bit to figure out where the next index is
    difference = bitmask - (bitmask & (bitmask - 1));

    // Since we added bits as we went, this will actually be a negative index with 0b1 being index -1
    index = -1 - int(log2(difference));
    // Convert this to a positive index.
    pos_index = length + index;
    return pos_index + 1;
}

std::string MaybeNumber::_convert_upper_or_lower(std::string bitmask_name) const{
    size_t bitmask = _get_bitmask(bitmask_name).bitmask;
    std::string s = original;

    if (original.size() == 0 || bitmask == 0)
        return s;

    size_t difference, pos_index;
    long long signed int index;

    while (bitmask > 0){
        // Turn off the least significant bit to figure out where the next index is
        difference = bitmask - (bitmask & (bitmask - 1));

        // Since we added bits as we went, this will actually be a negative index with 0b1 being index -1
        index = -1 - int(log2(difference));
        // Convert this to a positive index.
        pos_index = s.size() + index;

        if (bitmask_name == "ISUPPER")
            s[pos_index] += 32;
        else
            s[pos_index] -= 32;

        bitmask = (bitmask & (bitmask - 1));
    }
    return s;
}

void MaybeNumber::_convert_upper_or_lower_inplace(std::string bitmask_name){
    size_t bitmask = _get_bitmask(bitmask_name).bitmask;

    if (original.size() == 0 || bitmask == 0)
        return;

    size_t difference, pos_index;
    long long signed int index;


    while (bitmask > 0){
        // Turn off the least significant bit to figure out where the next index is
        difference = bitmask - (bitmask & (bitmask - 1));

        // Since we added bits as we went, this will actually be a negative index with 0b1 being index -1
        index = -1 - int(log2(difference));
        // Convert this to a positive index.
        pos_index = original.size() + index;

        if (bitmask_name == "ISUPPER")
            original[pos_index] += 32;
        else
            original[pos_index] -= 32;

        bitmask = (bitmask & (bitmask - 1));
    }
}



MaybeNumber::TypeValues MaybeNumber::get_type() const{
    if (isnumber() == true){
        double forced = force_to_number();
        if (std::trunc(forced) != forced){
            return DOUBLETYPE;
        }
        if (_multiplier < 0){
            return SIGNEDINTTYPE;
        }
        return SIZE_TTYPE;
    };
    std::string lowercase = lower();
    if (lowercase == "false" || lowercase == "true"){
        return BOOLTYPE;
    }
    if (lowercase == "inf"){
        return DOUBLETYPE;
    }
    return STRINGTYPE;
}

MaybeNumber& MaybeNumber::operator =(const MaybeNumber& that){
    original = that.original;
    _token = that._token;
    _multiplier = that._multiplier;
    _place = that._place;
    _forcenumber = that._forcenumber;

    std::vector<Bitmask> the_bitmasks = that.the_bitmasks;

    _len_bitmasks = that._len_bitmasks;

    return *this;
}

// Does the internal modifications required for popping back
void MaybeNumber::_pop_back_internals(){
    char letter = original[original.size() - 1];
    original.pop_back();
    if (letter == 37){
        _multiplier *= 100.0;
    }
    if (letter == 40 or letter == 45){
        _multiplier *= -1.0;
    }

    // if the letter is a digit or a period
    if ((letter >= 48 && letter < 58) || letter == 46){
        double ltr = letter - 48.0;
        // if letter == "."
        if (letter == '.'){
            _place *= 10.0;
        }
        else if (isdot() != 0){
            _place *= 10.0;
            _forcenumber = _forcenumber - (_place * ltr);
        }
        else{
            _forcenumber = (_forcenumber - ltr) / 10.0;
            _place /= 10.0;
        }
    }
}

// places the letter into the empty MaybeNumber object
void MaybeNumber::pop_back(MaybeNumber& empty){
    char letter = original[original.size() - 1];
    std::vector<size_t> finals;
    _adjust_bits();
    // _remove_bits(finals);
    _pop_back_internals();
    empty.push_back(letter);
}

// Also pops back but no way to get the popped back letter
void MaybeNumber::pop_back(){
    _adjust_bits();
    _pop_back_internals();
}

// If this is a bool, it returns 0 or 1.  If it's infinity, returns 3.  otherwise, the pointer remains a nullpointer
void MaybeNumber::_convert_bool(size_t* ptr) const {
    std::string lowercase = lower();
    if (lowercase == "false")
        *ptr = 0;
    else if (lowercase == "true")
        *ptr = 1;
    else if (lowercase == "inf")
        *ptr = 3;
}

// casts MaybeNumber to a boolean
MaybeNumber::operator bool() const{
    size_t* ptr = nullptr;
    _convert_bool(ptr);
    if (ptr != nullptr){
        switch(*ptr){
            case 0:
                return false;
            case 1:
                return true;
            case 3:
                return std::numeric_limits<bool>::infinity();
        }
    }
    if (isnumber())
        return force_to_number() != 0;
    return original.size() > 0;
}

// casts MaybeNumber to an integer
MaybeNumber::operator int() const{
    size_t* ptr = nullptr;
    _convert_bool(ptr);
    if (ptr != nullptr){
        switch(*ptr){
            case 0:
                return 0;
            case 1:
                return 1;
            case 3:
                return std::numeric_limits<int>::max();
        }
    }
    return int(force_to_number());
}

// casts MaybeNumber to an unsigned integer
MaybeNumber::operator size_t() const{
    size_t* ptr = nullptr;
    _convert_bool(ptr);
    if (ptr != nullptr){
        switch(*ptr){
            case 0:
                return 0;
            case 1:
                return 1;
            case 3:
                return std::numeric_limits<size_t>::max();
        }
    }
    return size_t(force_to_number());
}

// casts MaybeNumber to a double
MaybeNumber::operator double() const{
    size_t* ptr = nullptr;
    _convert_bool(ptr);
    if (ptr != nullptr){
        switch(*ptr){
            case 0:
                return 0.0;
            case 1:
                return 1.0;
            case 3:
                return std::numeric_limits<double>::max();
        }
    }
    return force_to_number();
}


void MaybeNumber::clear(){
    while (original.size() > 0)
        pop_back();
}

void MaybeNumber::_slice_by_bitmask(std::deque<MaybeNumber>& vec, size_t bitmask, bool bitval_to_compile) const{
    // Due to the overflow problem on my TODO list, I will raise an exception for now if there is going to be a
    // problem with integer overflow causing an endless loop.
    if (unwrapped().size() > 64)
        throw TooLongStringError("String is too long to use sliceby");

    size_t bitval = bitval_to_compile;
    long long int my_bitmask = bitmask;

    if ((unwrapped().size() == 0) || (bitmask == 0 && bitval == 1))
        return;
    if (bitmask == 0 && bitval == 0){
        vec.push_back(MaybeNumber(unwrapped()));
        return;
    }

    // Add artificial 1 at beginning
    my_bitmask = my_bitmask | (1 << (_len_bitmasks + 1));

    MaybeNumber::AnIndex prev_index = {(long long)unwrapped().size(), (long long)unwrapped().size()}, current_indices;

    // The idea here is that if we see there are consecutive bits on, we invert the bitmask to jump to the other
    // side of the cluster of on-bits.  Then re-invert to get back.
    long long int scooched_bitmask, blank_these_bits_please, next_bitmask, pos_index, neg_index, new_length, localized_end_of_cluster, cluster_length, start, stop;

    while (my_bitmask > 0){
        pos_index = _get_slice_index(my_bitmask);
        // This is actually computing abs(negative index) so it's a positive number
        // I need that because the bitmask is backwards, so I need to know how far from the end we are
        neg_index = unwrapped().size() - (pos_index - 1);

        current_indices.start = pos_index;
        current_indices.stop = unwrapped().size();

        scooched_bitmask = my_bitmask >> (neg_index - 1);
        // Because I put in an artificial 1 to flush things out
        if (scooched_bitmask == (long long int)bitval)
            break;

        // So the trick is that if there is more than 1 bit turned on, I want to leap to the next change.
        // And when I do that leap, I'd rather use bitwise equations instead of a loop b/c it's faster.
        new_length = unwrapped().size() - neg_index + 1;

        localized_end_of_cluster = _get_slice_index(~scooched_bitmask, new_length);
        cluster_length = new_length - localized_end_of_cluster;

        // Get ending index
        current_indices.stop = pos_index - cluster_length - (1 - bitval);
        // Blank this cluster for the next bitmask so that we don't have to go one by one
        blank_these_bits_please = (1 << (neg_index + cluster_length - bitval)) - 1;
        next_bitmask = my_bitmask & ~blank_these_bits_please;


        // If bitval to compile == 0 then start/stop = current_index.start, prev_index.stop
        // Otherwise, start/stop = current_index.start, current_index.stop
        if (bitval == 0){
            start = current_indices.start;
            stop = prev_index.stop;
        }
        else{
            start = current_indices.stop;
            stop = current_indices.start;
        }

        if (start < 0 && stop < 0)
            break;
        else if (start < 0)
            start = 0;
        else if (stop < 0)
            break;

        if (start != stop){
            MaybeNumber current;
            for (size_t x = (size_t)start; x < (size_t)stop; x ++){
                current.push_back(unwrapped()[x]);
            }
            vec.push_front(current);
        }

        // Now we set our previous index to exclude the bitval we are slicing out.  That will be our next slice point
        prev_index.stop = current_indices.start - cluster_length;
        // Finally, we set the new bitmask
        my_bitmask = next_bitmask;
    }
}


// a deque of slices is filled up, and the total number of characters used in the final resulting string is returned
size_t MaybeNumber::_get_slice_indices_from_bitmask(std::deque<Slice>& vec, size_t bitmask) const {
    if (original.size() == 0)
        return 0;
    if (bitmask == 0){
        Slice entire = {0, original.size()};
        vec.push_back(entire);
        return original.size();
    }
    size_t prev_index = original.size();
    size_t lsb_off, difference, pos_index;
    long long signed int index;
    size_t total = 0;

    while (bitmask > 0){
        // Turn off the least significant bit to figure out where the next index is
        lsb_off = bitmask & (bitmask - 1);
        difference = bitmask - lsb_off;

        // Since we added bits as we went, this will actually be a negative index with 0b1 being index -1
        index = -1 - int(log2(difference));
        // Convert this to a positive index.
        pos_index = original.size() + (index + 1);
        if (pos_index < prev_index){
            Slice c = {pos_index, prev_index};
            vec.push_front(c);
            total += (prev_index - pos_index);
        }

        // Now we set our previous index to exclude the token.  That will be our next slice point
        prev_index = pos_index - 1;
        bitmask = (bitmask & (bitmask - 1));
    }

    if (prev_index == 0)
        return total;
    Slice c = {0, prev_index};
    vec.push_front(c);
    total += prev_index;
    return total;
}


std::deque<MaybeNumber> MaybeNumber::sliceby(std::string bitmask_name, bool bitval_to_compile) const{
    size_t bitmask = _get_bitmask(bitmask_name).bitmask;
    std::deque<MaybeNumber> sliced;
    _slice_by_bitmask(sliced, bitmask, bitval_to_compile);
    return sliced;
}


std::string MaybeNumber::_concat_by_bitmask(size_t bitmask) const{
    std::deque<Slice> slicepoints;
    size_t stringsize = _get_slice_indices_from_bitmask(slicepoints, bitmask);

    std::string s;
    s.resize(stringsize);

    size_t s_index = 0;

    for (size_t i = 0; i < slicepoints.size(); i++){
        for (size_t j = slicepoints[i].start; j < slicepoints[i].end; j++){
            s[s_index++] = original[j];
        }
    }
    return s;
}

std::string MaybeNumber::tostring_all_bitmasks() const{
    std::string my_string = "Unwrapped: " + unwrapped() + "\n";
    for (size_t i = 0; i < the_bitmasks.size(); i++)
        my_string += "    " + the_bitmasks[i].to_string() + "\n";
    return my_string;
}

std::string MaybeNumber::tostring_one_bitmask(std::string bitmask_name) const{
    MaybeNumber::Bitmask the_bitmask = _get_bitmask(bitmask_name);
    return the_bitmask.to_string();
}
