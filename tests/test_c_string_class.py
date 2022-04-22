import copy
import unittest
from c_import_to_python.import_dependents.c_str_cls import CStringPyth


class TestCStringClass(unittest.TestCase):

    def setUp(self) -> None:
        self.my_test_strings = ["hello", "Hi!", "Yo-yo-yo what up?",
                                "this is a string", "this is another string", "!$#*(&%6748",
                                "87867324310", "{}|<>?:", "\t\n\e\r", "uuuuuuuu", "a", "1", "0",
                                ")",
                                "\0"]
        self.exp_test_strings = ["hello", "Hi!", "Yo-yo-yo what up?",
                                   "this is a string", "this is another string", "!$#*(&%6748",
                                   "87867324310", "{}|<>?:", "\t\n\e\r", "uuuuuuuu", "a", "1", "0", ")",
                                   ""]

    def get_pointer(self, string):
        return string._ptr

    def get_as_std_string(self, string):
        return str(string)

    def assertStringEqual(self, str1, str2, msg=""):
        expected = str(str1)
        actual = str(str2)
        self.assertEqual(expected, actual, msg=msg)

    def test_new_string_empty(self):
        with CStringPyth("") as s:
            self.assertEqual(str(s), "")
            self.assertEqual(0, len(s))

    def test_new_string_one_char(self):
        with CStringPyth("a") as s:
            self.assertEqual("a", s)
            self.assertEqual(1, len(s))

    def test_new_string_one_letter(self):
        with CStringPyth('d') as s:
            self.assertEqual("d", s)
            self.assertEqual(1, len(s))

    def test_new_string_many_chars(self):
        for i, word in enumerate(self.my_test_strings):
            expected = self.exp_test_strings[i]
            with CStringPyth(word) as s:
                print(f"'{s}'")
                self.assertEqual(expected, s)
                self.assertEqual(len(expected), len(s), msg=f"'{word}'")

    def test_string_with_f_formatting(self):
        for i, word in enumerate(self.my_test_strings):
            with CStringPyth(word) as s:
                string_version = f"'{s}'"
                expected = f"'{self.exp_test_strings[i]}'"
                print(string_version)
                self.assertEqual(expected, string_version)
                self.assertEqual(len(expected), len(string_version))

    def test_cast_to_python_string(self):
        for i, word in enumerate(self.my_test_strings):
            with CStringPyth(word) as s:
                self.assertEqual(str(self.exp_test_strings[i]), str(s))

            with CStringPyth.Temp(word) as s:
                self.assertEqual(str(self.exp_test_strings[i]), s.tostring())

    def test_cast_to_python_string_through_pointer(self):
        for i, word in enumerate(self.my_test_strings):
            with CStringPyth.Temp(word) as s:
                with CStringPyth(s.pointer) as t:
                    self.assertEqual(str(self.exp_test_strings[i]), str(t))

    def test_cast_to_std_string_from_no_chars(self):
        with CStringPyth('') as s:
            self.assertEqual(0, len(s))
            self.assertEqual("", s)

    def test_cast_to_string_one_char(self):
        for i in range(97, 97 + 26):
            with CStringPyth(chr(i)) as s:
                self.assertStringEqual(s, chr(i))

    def test_really_really_short_strings(self):
        """Testing writing and rewriting same memory location with really short strings"""
        with CStringPyth("") as s:
            self.assertStringEqual(s, "")
            self.assertEqual(s, "")

        with CStringPyth("A") as s:
            self.assertStringEqual(s, "A")
            self.assertEqual(s, "A")

        with CStringPyth("") as s:
            self.assertStringEqual(s, "")
            self.assertEqual(s, "")

        with CStringPyth("a") as s:
            self.assertStringEqual(s, "a")
            self.assertEqual(s, "a")

        with CStringPyth("") as s:
            self.assertStringEqual(s, "")
            self.assertEqual(s, "")

    def test_when_already_initialized_and_no_string(self):
        with CStringPyth('') as s:
            self.assertEqual(s, "")

            s += "A"
            self.assertEqual("A", s)

        with CStringPyth() as s:
            self.assertEqual("", s)

            s.push_back("a")
            self.assertEqual("a", s)

    def test_equal(self):
        for word in self.my_test_strings:
            with CStringPyth(word) as str1:
                with CStringPyth(word) as str2:
                    self.assertTrue(str1 == str2)
                    self.assertFalse(str1 != str2)

    def test_equal_string(self):
        for i, word in enumerate(self.my_test_strings):
            expected = self.exp_test_strings[i]
            with CStringPyth(word) as s:
                self.assertTrue(s == expected)
                self.assertFalse(s != expected)

    def test_notequal(self):
        for word in self.my_test_strings:
            with CStringPyth(word) as s1:
                with CStringPyth(word + " ") as s2:
                    self.assertNotEqual(s1, s2)
                    self.assertFalse(s1 == s2)
                    self.assertTrue(s1 != s2)

    def test_unequal_string(self):
        for word in self.my_test_strings:
            with CStringPyth(word) as s:
                new_word = word + " "
                self.assertFalse(s == new_word)
                self.assertTrue(s != new_word)

    def test_push_back(self):
        for word in self.my_test_strings:
            with CStringPyth('') as s:
                for letter in word:
                    s.push_back(letter)
                if word == '\0':
                    self.assertEqual(0, len(s))
                    self.assertEqual('', s)
                    self.assertTrue('' == s)
                else:
                    self.assertEqual(len(word), len(s))
                    self.assertEqual(s, word)
                    self.assertTrue(word == s)

    def test_push_back_empty_char(self):
        for word in self.my_test_strings:
            with CStringPyth(word) as s:
                if word == '\0':
                    word = ''
                s.push_back('\0')
                self.assertEqual(len(word), len(s))
                self.assertEqual(s, word)
                self.assertTrue(word == s)

    def test_concatenate(self):
        for word in self.my_test_strings:
            with CStringPyth(word) as s:
                with CStringPyth(" yo ho ho and a bottle of rum") as str2:
                    if word == '\0':
                        word = ''
                    str3 = s + str2
                    print(str3)
                    exp = f"{word} yo ho ho and a bottle of rum"
                    self.assertEqual(exp, str3)
                    self.assertEqual(len(exp), len(str3))
                    self.assertTrue(str3 == exp)
                    self.assertNotEqual(s, str3)
                    if word != '':
                        self.assertNotEqual(str2, str3)
                    str3 = str3.destroy()

    def test_copy(self):
        for i, word in enumerate(self.my_test_strings):
            expected = self.exp_test_strings[i]
            with CStringPyth(word) as s1:
                s2 = copy.copy(s1)
                self.assertEqual(s1, s2)
                self.assertEqual(s1, expected)
                self.assertEqual(s2, expected)
                s2.push_back('!')
                self.assertNotEqual(s1, s2)
                self.assertNotEqual(expected, s2)
                self.assertEqual(expected, s1)

    def test_concatenate_string(self):
        for word in self.my_test_strings:
            with CStringPyth(word) as s:
                with CStringPyth(" yo ho ho and a bottle of rum") as str2:
                    s += str2
                    if word == '\0':
                        word = ''
                    exp = f"{word} yo ho ho and a bottle of rum"
                    self.assertEqual(len(exp), len(s))
                    self.assertEqual(exp, s)
                    self.assertTrue(s == exp)
                    if word != "":
                        self.assertNotEqual(str2, s)

    def test_resize(self):
        with CStringPyth('aeiou') as s:
            exp = 'aeiou'
            self.assertEqual(len(exp), len(s))
            for i in range(1000):
                s.push_back('a')
                exp += 'a'
                self.assertEqual(len(exp), len(s))

    def test_at_indexing_positive(self):
        with CStringPyth("abacus") as s:
            self.assertEqual('a', s[0])
            self.assertEqual('b', s[1])
            self.assertEqual('a', s[2])
            self.assertEqual('c', s[3])
            self.assertEqual('u', s[4])
            self.assertEqual('s', s[5])

        for word in self.my_test_strings:
            with CStringPyth(word) as s:
                if word == '\0':
                    word = ''
                for i, letter in enumerate(word):
                    self.assertEqual(letter, s[i])

    def test_at_indexing_negative(self):
        with CStringPyth("abacus") as s:
            self.assertEqual('s', s[-1])
            self.assertEqual('u', s[-2])
            self.assertEqual('c', s[-3])
            self.assertEqual('a', s[-4])
            self.assertEqual('b', s[-5])
            self.assertEqual('a', s[-6])

        for word in self.my_test_strings:
            with CStringPyth(word) as s:
                if word == '\0':
                    word = ''
                i = -1
                while True:
                    try:
                        letter = word[i]
                        self.assertEqual(letter, s[i])
                        i -= 1
                    except IndexError:
                        break

    def test_at_indexing_out_of_bounds(self):
        with CStringPyth("abacus") as s:
            with self.assertRaises(IndexError):
                a = s[-7]
            with self.assertRaises(IndexError):
                b = s[6]

    def test_at_indexing_no_letters(self):
        with CStringPyth('') as s:
            with self.assertRaises(IndexError):
                a = s[0]
            with self.assertRaises(IndexError):
                a = s[-1]

    def test_at_indexing_one_letter(self):
        with CStringPyth('a') as s:
            self.assertEqual('a', s[0])
            self.assertEqual('a', s[-1])
            with self.assertRaises(IndexError):
                x = s[1]
            with self.assertRaises(IndexError):
                x = s[-2]






