#!/usr/bin/env python3

import copy
import string
import sys


def is_letter(letter):
    """Returns whether or not letter is a a lowercase English character."""
    return letter in string.ascii_lowercase


class LetterInventory():
    """A bag of letters that can be added or subtracted from others."""

    def __init__(self, word: str=""):
        self.letters = {}
        if word == "":
            return
        for letter in string.ascii_lowercase:
            self.letters[letter] = word.count(letter)

    def get(self, letter: str) -> int:
        """Returns count for letter."""
        return self.letters[letter]

    def set(self, letter: str, count: int):
        """Sets count to count for letter."""
        self.letters[letter] = count

    def sub(self, other):
        """Subtracts other from this inventory and returns it as a new
        inventory. Returns None if it cannot be.
        """
        if len(other.letters) > len(self.letters):
            return None
        difference = LetterInventory()
        for letter in string.ascii_lowercase:
            count = self.get(letter) - other.get(letter)
            if count < 0:
                return None
            difference.letters[letter] = count
        return difference

    def add(self, other):
        """Adds other to this inventory and returns a the result as a new
        inventory.
        """
        result = LetterInventory()
        for letter in string.ascii_lowercase:
            result.letters[letter] = self.get(letter) + other.get(letter)
        return result

    def copy(self):
        """Returns a copy of this inventory."""
        result = LetterInventory()
        result.letters = self.letters.copy()
        return result


def make_letter_maps(phrase: str):
    """Returns a list with the same length as phrase, each element is None if
    is not a letter or a dictionary mapping letters to lists of indices where
    that letter can be found later in the phrase."""
    maps = [None] * len(phrase)
    last = None
    lastLetter = None
    lastIndex = 0
    for i in range(len(phrase)-1, -1, -1):
        letter = phrase[i]
        if is_letter(letter):
            if last is None:
                maps[i] = {}
            else:
                maps[i] = copy.deepcopy(last)
                if lastLetter in maps[i]:
                    maps[i][lastLetter].append(lastIndex)
                else:
                    maps[i][lastLetter] = [lastIndex]
            last = maps[i]
            lastLetter = letter
            lastIndex = i
        else:
            maps[i] = None
    return maps


# DICT_PATH = "/usr/share/dict/words"

# The path to read the dictionary from.
DICT_PATH = "dict.txt"


def read_dict(path: str=DICT_PATH) -> list:
    """Reads the dictionary at path and returns a list of the words in it in
    lower case with duplicates removed.
    """
    with open(path, "r") as f:
        words = set([line.lower().rstrip() for line in f.readlines()])
        return sorted(list(words))


def print_word_list(word_list: list, phrase: str):
    """Prints the words in word_list by getting indices from phrase. word_list
    is a list of list of int. Each element is a list of indices in phrase and
    the output is constructed by using those indices of phrase. Note, the
    indices themselves are often build with case insensitive methods and then
    the cased letters are taken from the original phrase.
    """
    result = ["_" if is_letter(letter.lower()) else letter for letter in
              phrase]
    words = []
    for word in word_list:
        current = ""
        for index in word:
            result[index] = phrase[index]
            current += phrase[index]
        words.append(current)
    combined = list(" ".join(result))
    space_indices = [next_index(word) for word in word_list]
    last_index = max(space_indices)
    for i in space_indices:
        if i != last_index:
            combined[2 * i - 1] = "|"
    print("{} ({})".format("".join(combined), " ".join(words)))


def trim_dictionary(phrase: str, dictionary: list, dictionary_inventories:
                    list) -> list:
    """Returns a new list of words from the original dictionary. This new
    dictionary only contains words that can be subtracted from the phrase,
    meaning the phrase has all the necessary letters for that word.
    dictionary_inventories must be the same length as dictionary and contain
    corresponding LetterInventory objects at corresponding indices.
    """
    inventory = LetterInventory(phrase)
    trimmed_dict = []
    for i in range(len(dictionary)):
        if inventory.sub(dictionary_inventories[i]) is not None:
            trimmed_dict.append(dictionary[i])
    return trimmed_dict


def next_index(word):
    """Returns one past the last index of the list of indexes."""
    # TODO: Change this to use the last index instead of max.
    return max(word) + 1


class MatchResults():
    """A incremental result of finding words by covering letters of a phrase.
    Stores the original phrase as well as the lower case version and can give a
    list of word indices for words that begin at any given index of the
    phrase.
    """

    def __init__(self, phrase: str, count: int=0, allow_less: bool=True):
        self.original_phrase = phrase
        self.phrase = phrase.lower()
        self.count = count
        self.allow_less = allow_less
        self.words = []
        self.maps = make_letter_maps(self.phrase)
        self.initial_map = {}
        for letter in string.ascii_lowercase:
            for i in range(len(self.phrase)):
                if self.phrase[i] == letter:
                    if letter in self.initial_map:
                        self.initial_map[letter].append(i)
                    else:
                        self.initial_map[letter] = [i]
        for letter in self.phrase:
            if is_letter(letter):
                self.words.append([])
            else:
                self.words.append(None)

    def add_match(self, indexes: list, index: int, print_results: bool=False,
                  count: int=0, allow_less: bool=False):
        """Stores a match with indices at indexes assuming it starts at index.
        If print_results is True, print all results that include that word and
        all combinations that include count words or less if allow_less is
        True.
        """
        self.words[index].append(indexes)
        if print_results:
            current_words = [indexes]
            if count <= 1 or allow_less:
                print_word_list(current_words, self.original_phrase)
            start = next_index(indexes)
            for i in range(start, len(self.phrase)):
                for word_list in self._iterate_matches(count, i, current_words,
                                                       allow_less):
                    print_word_list(word_list, self.original_phrase)

    def _iterate_matches(self, count: int, index: int, current_words: list,
                         allow_less: bool=False):
        """Iterates throuh all matches that have a word starting at index and
        using any word already in current_words.
        """
        word_list = self.words[index]
        if word_list is not None:
            for word in word_list:
                current_words.append(word)
                if ((allow_less and len(current_words) < count) or count < 1 or
                        len(current_words) == count):
                    yield(current_words.copy())
                if count < 1 or len(current_words) < count:
                    start = next_index(word)
                    for i in range(start, len(self.phrase)):
                        for sub_list in self._iterate_matches(count, i,
                                                              current_words,
                                                              allow_less):
                            yield(sub_list)
                current_words.pop()

    def iterate_matches(self, count, index=0, allow_less=True):
        """Iterates through all matches that have a word starting at index with
        the same number of words as count or any number of words if it is less
        than 1.
        """
        for word_list in self._iterate_matches(count, index, [], allow_less):
            yield(word_list)


class WordMatcher():
    """An object that takes phrases and produces matches formed by covering
    letters of that phrase using a dictionary of words.
    """

    def __init__(self):
        self.set_dict(read_dict())

    def set_dict(self, dictionary: list):
        """Takes a list of words and stores them as the dictionary to use."""
        self._dictionary = [word.lower() for word in dictionary]
        self._dictionary_inventories = [LetterInventory(word) for word in
                                        self._dictionary]

    def set_dict_file(self, path: str):
        """Loads the dictionary from the file located at path."""
        self.set_dict(read_dict(path))

    def _print_word_matches(self, word: str, start_index: int, word_index: int,
                            index: int, indexes: list, words):
        """Checks if word matches the phrase starting at start_index from
        word_index at index in the phrase assuming the indices in indexes have
        already been matches using maps containing lists of dictionaries of
        letters to where they occur later in the phrase where words is a
        MatchResults object. Note, this method updates words as it goes with
        the new words it finds.
        """
        if word_index == len(word):
            words.add_match(indexes, start_index)
        elif word[word_index] in words.maps[index]:
            for i in words.maps[index][word[word_index]]:
                new_indexes = indexes + [i]
                self._print_word_matches(word, start_index, word_index + 1, i,
                                         new_indexes, words)

    def print_matches(self, phrase: str, count: int=0, allow_less: bool=True):
        """Prints all word combinations that can be formed by taking phrase and
        covering certain letters. The combinations will have count words or
        less if allow_less is True or any number of words is count is less than
        1.
        """
        words = MatchResults(phrase, count, allow_less)
        # Get lower case version
        phrase = words.phrase
        trimmed_dictionary = trim_dictionary(phrase, self._dictionary,
                                             self._dictionary_inventories)
        for word in trimmed_dictionary:
            if word[0] in words.initial_map:
                next_indices = words.initial_map[word[0]]
                for i in next_indices:
                    self._print_word_matches(word, i, 1, i, [i], words)
        for i in range(len(phrase)):
            for word_list in words.iterate_matches(count, i, allow_less):
                print_word_list(word_list, words.original_phrase)


def main(argv):
    matcher = WordMatcher()
    while True:
        phrase = input("Enter a phrase (empty to quit): ")
        if not phrase:
            return
        count_input = input("How many words? (0 or empty for any number): ")
        count = 0
        try:
            count = int(count_input)
        except ValueError:
            pass
        allow_less = True
        if count > 1:
            allow_less_input = input(
                "Allow combinations with less words? (Y/n) ")
            if allow_less_input and allow_less_input.lower()[0] == "n":
                allow_less = False
        matcher.print_matches(phrase, count, allow_less)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
