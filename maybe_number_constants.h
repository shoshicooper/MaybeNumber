# ifndef MaybeNumberConstants_h
#define MaybeNumberConstants_h
// Constants for maybenumber


// const int CURR1 = '£', CURR2 = '€';  // Except these are not ASCII, must think up solution
const char CURR1 = '$', CURR2 = '$';

const char CURRENCIES[3] = {'$', CURR1, CURR2};
const char IGNORE[13] = {'$', ',', ' ', ')', '%', '\n', '\t', '(', '-', '\'', CURR1, CURR2};
const char ALL_NUM_ELEMENTS[24] = {'$', ',', ' ', ')', '%', '\n', '\t', '(', '-', '\'', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.',  CURR1, CURR2};
const char ACCEPTABLE_ENDS[2] = {' ', ')'};


#endif
