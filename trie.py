

class Node(object):
    MAX_CHARS = 256

    def __init__(self):
        self.next = {}

    def insert(self, letter):
        return self.next.setdefault(letter, Node())

    def insert_recursive(self, substring):
        node = self.insert(substring[0])
        node.insert(substring[1:])



class Trie(object):

    def __init__(self):
        self._root = Node()
        # Last node looked up
        self._last_node = None

    def __contains__(self, item):
        return self.lookup(item, endword='\0')
        # return self._more_intelligent_lookup(item)

    def _cache(self, node):
        self._last_node = node
        return node

    def insert(self, a_string):
        node = self._root
        for letter in a_string + "\0":
            node = self._cache(node.insert(letter.lower()))

    def insert_prefix(self, prefix):
        node = self._root
        for letter in prefix:
            node = self._cache(node.insert(letter.lower()))
        return node

    def is_wordstart(self, a_string):
        """Returns whether or not the current string is the start of a word"""
        try:
            self._traverse(a_string, ending="")
            return True
        except KeyError:
            return False

    @property
    def root(self):
        return self._root

    def _iter_word(self, a_string, ending='\0'):
        """Iterates through the word.  Will raise a KeyError if the word is not in the tree"""
        node = self._root
        so_far = ""
        for letter in a_string + ending:
            is_letter = False
            for letter_variant in [letter.upper(), letter.lower()]:
                try:
                    node = self._cache(node.next[letter_variant])
                    so_far += letter_variant
                    is_letter = True
                    break
                except KeyError:
                    pass
            if not is_letter:
                raise KeyError(f"{letter} not found after {so_far}")

            yield node

    def _traverse(self, a_string, ending='\0'):
        """Returns last letter before the end"""
        prev = None
        prev_to_prev = None
        for node in self._iter_word(a_string, ending):
            prev_to_prev = self._cache(prev)
            prev = node

        return prev_to_prev

    def lookup(self, word, so_far=None, nodes=None, endword='\0'):
        """Returns true if the word is in here, false if it's not"""
        # if len(word) == 1 and word[0] == "'" or word[0] == "’":
        #     return False
        return self._more_intelligent_lookup(word=word, so_far=so_far, nodes=nodes, end_word=endword)
        # try:
        #     return "\0" in self._traverse(word).next
        # except KeyError:
        #     return False


    def _get_list_for_lookup(self, word, end_of_word='\0'):
        """Gets the nodes as a list rather than a single node so I can pop off the back and stem the word"""
        iterator = self._iter_word(word, ending=end_of_word)
        so_far = ""
        wordi = word + end_of_word
        nodes = []

        i = 0
        while i < len(wordi):
            try:
                nodes.append(self._cache(next(iterator)))
                so_far += wordi[i]
                i += 1
            except KeyError:
                break
        return so_far, nodes

    def _more_intelligent_lookup(self, word, so_far=None, nodes=None, end_word='\0'):
        """Does a more intelligent lookup dealing with suffixes"""
        if so_far is None and nodes is None:
            so_far, nodes = self._get_list_for_lookup(word, end_of_word=end_word)

        if end_word == '\0' and so_far.endswith('\0'):
            return True

        if word.endswith('iest') or word.endswith('ies'):
            i = -4
            mystr = 'ies'
            while mystr:
                if so_far.endswith(mystr):
                    break
                mystr = mystr[:-1]
                i += 1

            node = nodes[i]
            # Check for '-ies' instead of y or 'iest' instead of 'y'
            if self._is_ending(node, 'y', end_word):
                return True

        # If there's an s on the end
        if word.endswith('s') and so_far == word[:-1]:
            return True

        # If it's a verb and it ends differently
        if word.endswith('ed'):
            node = nodes[-1]
            if so_far.endswith('e'):
                node = nodes[-2]

            if self._is_ending(node, 'ing', end_word):
                return True

        if word.endswith('ing'):
            i = -3
            mystr = 'in'
            while mystr:
                if so_far.endswith(mystr):
                    break
                mystr = mystr[:-1]
                i += 1

            node = nodes[i]
            if self._is_ending(node, 'ed', end_word):
                return True

        # Ends with an apostrophe -- ignore the apostrophe
        if word.endswith("'") or word.endswith("’"):
            if len(word) == 1:
                return True
            if self._is_ending(nodes[-1], '', end_word):
                return True


        # If there's an apostrophe
        if "'" in word or "’" in word:
            subword, i = self.get_apostrophe_subword(word, so_far)
            if self._is_ending(nodes[i], '', end_word):
                return True


        # stemmed = self._stemmer.stem(word)
        # print(f"{stemmed=}")
        return False

    def _is_ending(self, node, suffix, endword='\0'):
        mynode = node
        for letter in suffix + endword:
            try:
                mynode = mynode.next[letter.lower()]
            except KeyError:
                return False
        return True

    @staticmethod
    def get_apostrophe_subword(word, so_far):
        if word.endswith("'") or word.endswith("’"):
            return word[:-1], -1

        # If there's an apostrophe
        if "'" in word or "’" in word:
            apostr = "'" if "'" in word else "’"
            where_is = list(word).index(apostr)
            non_apostr = word[:where_is]
            if non_apostr.endswith("n"):
                non_apostr = non_apostr[:-1]

            mystr = so_far
            i = -1
            while mystr != non_apostr:
                mystr = mystr[:-1]
                i -= 1

            return non_apostr, i
        return so_far, -1


    def find_part(self, word):
        """Returns the largest part of the word that exists in the trie"""
        iterator = self._iter_word(word)
        so_far = ""
        wordi = word + '\0'
        node = self._root

        i = 0
        while i < len(wordi):
            try:
                node = self._cache(next(iterator))
                so_far += wordi[i]
                i += 1
            except KeyError:
                return so_far, node
        return so_far, node

    def insert_from_node(self, rest_of_word, node):
        """Inserts remainder of word starting from node.  This is my attempt to try to get this to load faster"""
        mynode = node
        for letter in rest_of_word + '\0':
            mynode = mynode.insert(letter.lower())

    def is_last_lookup_complete(self):
        """Looks at the value stored in last node and checks to see if it's a complete word"""
        return '\0' in self._last_node.next

