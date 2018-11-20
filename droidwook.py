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
    that letter can be found from that point on in the phrase."""
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


# The path to read the dictionary from.
DICT_PATH = "dict.txt"


def read_dict(path: str = DICT_PATH) -> list:
    """Reads the dictionary at path and returns a sorted list of the words in
    it in lower case with duplicates removed.
    """
    with open(path, "r") as f:
        return [line.lower().rstrip() for line in f.readlines()]


def make_word_line(word_list: list, phrase: str) -> str:
    """Takes a list of list of indices and returns a line formed taking those
    indices of phrase.
    """
    def word_for(word):
        return "".join(map(lambda index: phrase[index], word))
    return " ".join(map(word_for, word_list))


def print_word_list(word_list: list, phrase: str, words_only: bool = False):
    """Prints the words in word_list by getting indices from phrase. word_list
    is a list of list of int. Each element is a list of indices in phrase and
    the output is constructed by using those indices of phrase. Note, the
    indices themselves are often build with case insensitive methods and then
    the cased letters are taken from the original phrase.
    """
    if words_only:
        print(make_word_line(word_list, phrase))
        return
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


def next_index(word: list) -> int:
    """Returns one past the last index of the list of indices."""
    return word[-1] + 1


class MatchResults():
    """A incremental result of finding words by covering letters of a phrase.
    Stores the original phrase as well as the lower case version and can give a
    list of word indices for words that begin at any given index of the
    phrase.
    """

    def __init__(self, phrase: str, count: int = 0, allow_less: bool = False,
                 words_only: bool = False):
        self.phrase = phrase
        self.count = count
        self.allow_less = allow_less
        self.words_only = words_only
        self.matches = [[] for _ in range(len(phrase))]
        self.maps = make_letter_maps(phrase.lower())

    def add_match(self, indices: list):
        """Stores a match with indices at indices assuming it starts at index.
        If print_results is True, print all results that include that word and
        all combinations that include count words or less if allow_less is
        True.
        """
        self.matches[indices[0]].append(indices.copy())

    def _iterate_matches(self, index: int, current_words: list):
        """Iterates throuh all matches that have a word starting at index and
        using any word already in current_words.
        """
        for indices in self.matches[index]:
            current_words.append(indices)
            if (self.count < 1 or len(current_words) == self.count
                    or self.allow_less):
                yield(current_words)
                if self.count < 1 or len(current_words) < self.count:
                    for i in range(next_index(indices), len(self.phrase)):
                        yield from self._iterate_matches(i, current_words)
            current_words.pop()

    def iterate_matches(self, index=0):
        """Iterates through all matches that have a word starting at index with
        the same number of words as count or any number of words if it is less
        than 1.
        """
        yield from self._iterate_matches(index, [])

    def iterate_all_matches(self):
        """Iterates over all matches currently found."""
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

    def match_results(self, phrase: str, count: int = 0, allow_less: bool = False,
                      words_only: bool = False, unique_phrases: bool = False):
        """Prints all word combinations that can be formed by taking phrase and
        covering certain letters. The combinations will have count words or
        less if allow_less is True or any number of words is count is less than
        1.
        """
        results = MatchResults(phrase, count, allow_less)
        for word in self._dictionary:
            self._match_results(word, 0, 0, [], results)
        # if words_only and unique_phrases:
        #     lines = set()
        #     for line in (make_word_line(word_list, phrase) for
        #                  word_list in results.iterate_all_matches()):
        #         as_lower = line.lower()
        #         if as_lower not in lines:
        #             print(line)
        #             lines.add(as_lower)
        return results


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
        results = matcher.match_results(args.phrase, args.count,
                                        args.allow_less, args.words_only,
                                        args.unique_phrases)
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
