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
    """Returns a list with the same length as phrase. Each element is a map
    from letters to indices where that letter can be found in phrase starting
    from the corresponding index in the list onwards.
    """
    maps = [None] * len(phrase)
    prev = {}
    for i in range(len(phrase) - 1, -1, -1):
        letter = phrase[i]
        maps[i] = copy.deepcopy(prev)
        letter = phrase[i]
        if is_letter(letter):
            if letter not in maps[i]:
                maps[i][letter] = []
            maps[i][letter].append(i)
        prev = maps[i]
    return maps

# Uncomment this and comment the other line below to use the system dictionary.
# This will probably work on Mac and most GNU/Linux distributions, although you
# may specifically have to install this file.
# DICT_PATH = "/usr/share/dict/words"


# The path to read the dictionary from the current directory.
DICT_PATH = "dict.txt"


def read_dict(path: str = DICT_PATH) -> list:
    """Reads the dictionary at path and returns a list of words in that
    dictionary in lower case.
    """
    with open(path, "r") as f:
        return [line.lower().rstrip() for line in f.readlines()]


def make_word_line(word_list: list, phrase: str) -> str:
    """Takes a list of list of indices and returns a space separated string
    taken by forming words with the letters in phrase at the corresponding
    indices.
    """
    def word_for(word):
        return "".join(map(lambda index: phrase[index], word))
    return " ".join(map(word_for, word_list))


def print_word_list(word_list: list, phrase: str):
    """Prints the words in word_list by getting indices from phrase. The
    word_list is a list of list of ints. Each element is a list of indices in
    phrase and the output is constructed by using those indices of phrase.
    """
    result = []
    for letter in phrase:
        result.append("_" if is_letter(letter.lower()) else letter)
        result.append(" ")
    for i in range(len(word_list)):
        word = word_list[i]
        for index in word:
            result[2 * index] = phrase[index]
        if i < len(word_list) - 1:
            result[2 * word[-1] + 1] = "|"
    print("{}({})".format("".join(result), make_word_line(word_list, phrase)))


class MatchResults():
    """A incremental result of finding words by covering letters of a phrase.
    Stores the original phrase as well as the lower case version and can give a
    list of word indices for words that begin at any given index of the
    phrase.
    """

    def __init__(self, phrase: str, count: int = 0, allow_less: bool = False):
        self.phrase = phrase
        self.count = count
        self.allow_less = allow_less
        self.matches = [[] for _ in range(len(phrase))]
        self.maps = make_letter_maps(phrase.lower())

    def add_match(self, indices: list):
        """Stores the given indices and does not modify them."""
        self.matches[indices[0]].append(indices.copy())

    def _iterate_matches(self, index: int, current_words: list):
        """Iterates throuh all matches that have a word starting at index and
        using any word already in current_words. Yields a list of list of
        indices of matched words.
        """
        for indices in self.matches[index]:
            current_words.append(indices)
            if (self.count < 1 or len(current_words) == self.count
                    or self.allow_less):
                yield(current_words)
                if self.count < 1 or len(current_words) < self.count:
                    # Start from one past the last value in indices.
                    for i in range(indices[-1] + 1, len(self.phrase)):
                        yield from self._iterate_matches(i, current_words)
            current_words.pop()

    def iterate_matches(self, index=0):
        """Iterates through all matches that have a word starting at index with
        the same number of words as count or any number of words if it is less
        than 1. Yields a list of list of indices of matched words.
        """
        yield from self._iterate_matches(index, [])

    def iterate_all_matches(self):
        """Iterates over all matches currently found at any index. Yields a
        list of list of indices of matched words.
        """
        for i in range(len(self.phrase)):
            yield from self.iterate_matches(i)

    def print_all_matches(self):
        for indices in self.iterate_all_matches():
            print_word_list(indices, self.phrase)


class WordMatcher():
    """An object that takes phrases and produces matches formed by covering
    letters of that phrase using a dictionary of words.
    """

    def __init__(self, path: str = DICT_PATH):
        self.set_dict(read_dict(path))

    def set_dict(self, dictionary: list):
        """Takes a list of words and stores them as the dictionary to use."""
        self._dictionary = [word.lower() for word in dictionary]

    def set_dict_file(self, path: str):
        """Loads the dictionary from the file located at path."""
        self.set_dict(read_dict(path))

    def _match_results(self, word: str, word_index: int, index: int,
                       indices: list, results: MatchResults):
        """Checks if word matches the phrase starting at start_index from
        word_index at index in the phrase assuming the indices in indices have
        already been matches using maps containing lists of dictionaries of
        letters to where they occur later in the phrase where words is a
        MatchResults object. Note, this method updates words as it goes with
        the new words it finds.
        """
        if word_index == len(word):
            results.add_match(indices)
        elif (index < len(results.phrase)
              and word[word_index] in results.maps[index]):
            for next_index in results.maps[index][word[word_index]]:
                indices.append(next_index)
                self._match_results(word, word_index + 1, next_index + 1,
                                    indices, results)
                indices.pop()

    def match_results(self, phrase: str, count: int = 0,
                      allow_less: bool = False):
        """Prints all word combinations that can be formed by taking phrase and
        covering certain letters. The combinations will have count words or
        less if allow_less is True or any number of words is count is less than
        1.
        """
        results = MatchResults(phrase, count, allow_less)
        for word in self._dictionary:
            self._match_results(word, 0, 0, [], results)
        return results


def make_parser():
    """Returns a new ArgumentParser for this program."""
    parser = argparse.ArgumentParser(description="Find new memes")
    parser.add_argument("phrase", nargs="?")
    parser.add_argument("-c", "--count", help="The number of words to print.",
                        type=int, default=0)
    parser.add_argument("-l", "--allow-less", help="Allow word combinations "
                        "with less words.", action="store_true", default=True)
    parser.add_argument("-d", "--dictionary", help="Dictionary file to use")
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
        results = matcher.match_results(args.phrase, args.count,
                                        args.allow_less)
        results.print_all_matches()
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
        allow_less = False
        if count > 1:
            allow_less_input = input(
                "Allow combinations with less words? (Y/n) ")
            if allow_less_input and allow_less_input.lower()[0] == "y":
                allow_less = True
        matcher.match_results(phrase, count, allow_less)
        results.print_all_matches()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
