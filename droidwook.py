#!/usr/bin/env python3

"""
Find ways to make words by covering certain letters of phrases.
"""

import argparse
import copy
import string
import sys


def is_letter(letter: str) -> bool:
    """Returns whether or not letter is a a lowercase English character."""
    return letter in string.ascii_lowercase


def make_letter_maps(phrase: str) -> list:
    """Returns a list with the same length as phrase, each element is None if
    it's not a letter or a dictionary mapping letters to lists of indices where
    that letter can be found later in the phrase."""
    maps = [None] * len(phrase)
    last_index = None
    for i in range(len(phrase)-1, -1, -1):
        letter = phrase[i]
        if last_index is None:
            maps[i] = {}
        else:
            maps[i] = copy.deepcopy(maps[last_index])
        if is_letter(letter):
            if letter not in maps[i]:
                maps[i][letter] = []
            maps[i][letter].append(i)
            last_index = i
    return maps

# Uncomment this and comment the other line below to use the system dictionary.
# This will probably work on Mac and most GNU/Linux distributions, although you
# may specifically have to install this file.
# DICT_PATH = "/usr/share/dict/words"


# The path to read the dictionary from.
DICT_PATH = "dict.txt"


def read_dict(path: str=DICT_PATH) -> list:
    """Reads the dictionary at path and returns a sorted list of the words in
    it in lower case with duplicates removed.
    """
    with open(path, "r") as f:
        words = set([line.lower().rstrip() for line in f.readlines()])
        return sorted(list(words))


def make_word_line(word_list: str, phrase: str) -> str:
    """Takes a list of list of indices and returns a line formed taking those
    indices of phrase.
    """
    words = []
    for word in word_list:
        current = ""
        for index in word:
            current += phrase[index]
        words.append(current)
    return " ".join(words)


def print_word_list(word_list: list, phrase: str, words_only: bool=False):
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
    if words_only:
        print(" ".join(words))
    else:
        combined = list(" ".join(result))
        space_indices = [next_index(word) for word in word_list]
        last_index = max(space_indices)
        for i in space_indices:
            if i != last_index:
                combined[2 * i - 1] = "|"
        print("{} ({})".format("".join(combined), " ".join(words)))


def next_index(word: list) -> int:
    """Returns one past the last index of the list of indices."""
    return word[-1] + 1


class MatchResults():
    """A incremental result of finding words by covering letters of a phrase.
    Stores the original phrase as well as the lower case version and can give a
    list of word indices for words that begin at any given index of the
    phrase.
    """

    def __init__(self, phrase: str, count: int=0, allow_less: bool=True,
                 words_only: bool=False):
        self.original_phrase = phrase
        self.phrase = phrase.lower()
        self.count = count
        self.allow_less = allow_less
        self.words_only = words_only
        self.words = []
        self.maps = make_letter_maps(self.phrase)
        for letter in self.phrase:
            if is_letter(letter):
                self.words.append([])
            else:
                self.words.append(None)

    def add_match(self, indices: list, index: int, print_results: bool=False):
        """Stores a match with indices at indices assuming it starts at index.
        If print_results is True, print all results that include that word and
        all combinations that include count words or less if allow_less is
        True.
        """
        self.words[index].append(indices)
        if print_results:
            current_words = [indices]
            if self.count <= 1 or self.allow_less:
                print_word_list(current_words, self.original_phrase)
            start = next_index(indices)
            for i in range(start, len(self.phrase)):
                for word_list in self._iterate_matches(i, current_words,):
                    print_word_list(word_list, self.original_phrase)

    def _iterate_matches(self, index: int, current_words: list):
        """Iterates throuh all matches that have a word starting at index and
        using any word already in current_words.
        """
        word_list = self.words[index]
        if word_list is not None:
            for word in word_list:
                current_words.append(word)
                if ((self.allow_less and len(current_words) < self.count)
                        or self.count < 1 or len(current_words) == self.count):
                    yield(current_words.copy())
                if self.count < 1 or len(current_words) < self.count:
                    start = next_index(word)
                    for i in range(start, len(self.phrase)):
                        yield from self._iterate_matches(i, current_words)
                current_words.pop()

    def iterate_matches(self, index=0):
        """Iterates through all matches that have a word starting at index with
        the same number of words as count or any number of words if it is less
        than 1.
        """
        for word_list in self._iterate_matches(index, []):
            yield(word_list)

    def iterate_all_matches(self):
        """Iterates over all matches currently found."""
        for i in range(len(self.phrase)):
            yield from self.iterate_matches(i)


class WordMatcher():
    """An object that takes phrases and produces matches formed by covering
    letters of that phrase using a dictionary of words.
    """

    def __init__(self, path: str=DICT_PATH):
        self.set_dict(read_dict(path))

    def set_dict(self, dictionary: list):
        """Takes a list of words and stores them as the dictionary to use."""
        self._dictionary = [word.lower() for word in dictionary]

    def set_dict_file(self, path: str):
        """Loads the dictionary from the file located at path."""
        self.set_dict(read_dict(path))

    def _print_word_matches(self, word: str, word_index: int, index: int,
                            indices: list, words):
        """Checks if word matches the phrase starting at start_index from
        word_index at index in the phrase assuming the indices in indices have
        already been matches using maps containing lists of dictionaries of
        letters to where they occur later in the phrase where words is a
        MatchResults object. Note, this method updates words as it goes with
        the new words it finds.
        """
        if word_index == len(word):
            # TODO: Make this check for non-empty indices.
            words.add_match(indices, indices[0])
        elif word[word_index] in words.maps[index]:
            for i in words.maps[index][word[word_index]]:
                new_indices = indices + [i]
                self._print_word_matches(word, word_index + 1, i, new_indices,
                                         words)

    def print_matches(self, phrase: str, count: int=0, allow_less: bool=True,
                      words_only: bool=False, unique_phrases: bool=False):
        """Prints all word combinations that can be formed by taking phrase and
        covering certain letters. The combinations will have count words or
        less if allow_less is True or any number of words is count is less than
        1.
        """
        words = MatchResults(phrase, count, allow_less)
        # Get lower case version
        phrase = words.phrase
        for word in self._dictionary:
            self._print_word_matches(word, 0, 0, [], words)
        if words_only and unique_phrases:
            lines = set()
            for line in (make_word_line(word_list, words.original_phrase) for
                         word_list in words.iterate_all_matches()):
                as_lower = line.lower()
                if as_lower not in lines:
                    print(line)
                    lines.add(as_lower)
        else:
            for word_list in words.iterate_all_matches():
                    print_word_list(word_list, words.original_phrase,
                                    words_only)


def make_parser():
    """Returns a new ArgumentParser for this program."""
    parser = argparse.ArgumentParser(description="Find new memes")
    parser.add_argument("phrase", nargs="?")
    parser.add_argument("-c", "--count", help="The number of words to print.",
                        type=int, default=0)
    parser.add_argument("-l", "--allow-less", help="Allow word combinations "
                        "with less words.", action="store_true", default=True)
    parser.add_argument("-w", "--words-only", help="Only print words",
                        action="store_true")
    parser.add_argument("-d", "--dictionary", help="Dictionary file to use")
    parser.add_argument("-u", "--unique-phrases", help="Only print a series of"
                        " words once (only if using -w)", action="store_true",
                        default=False)
    return parser


def main(argv):
    parser = make_parser()
    args = parser.parse_args(argv[1:])
    if args.phrase:
        path = args.dictionary if args.dictionary else DICT_PATH
        try:
            matcher = WordMatcher(path)
        except FileNotFoundError:
            print("Error loading dictionary")
            return
        matcher.print_matches(args.phrase, args.count, args.allow_less,
                              args.words_only, args.unique_phrases)
        return
    while True:
        matcher = WordMatcher()
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
