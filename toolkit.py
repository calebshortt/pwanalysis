
# https://pypi.org/project/python-Levenshtein/
import Levenshtein
import collections, argparse

from engine import utils


class ToolKit(object):

    def get_file(self, filepath):
        with open(filepath, 'r') as f:
            str_list = utils.get_file(f)
        return str_list

    def get_charcount(self, str_list):
        char_count = collections.Counter(''.join(str_list))
        return char_count

    def calc_similarity(self, gen_words, ref_words):
        # TODO: IDEA: Not implemented -- using ratio from Levenshtein library instead
        #   Iterate through all words in the generated list and compare each generated word to ALL of the reference words
        #   Generate a matrix for this comparison with all Levenshtein values
        #   Use the comparison matrix to make claims about each word:
        #       I.e. "This word is similar to x% of the reference material -- based on some threshold level of L. value
        #   Aggregate the individual comparisons and normalize to make a general claim about the generated dataset
        #       I.e. "This collection of words is similar to 40% of the reference material"
        #           This would require the threshold value set in such a way that that it is agnostic of word length
        #               percentage of characters similar? -- might get difficult with words of different lengths
        #               NOTE: L.value as some ratio between total characters in words: len(word1) + len(word2)
        # comp_matrix = []
        # for word in gen_words:
        #     result = [Levenshtein.distance(word, s) for s in ref_words]
        pass



if __name__ == "__main__":
    """
    Compare character counts and distributions between two list of passwords
    USAGE:  python toolkit.py <file1> <file2>
    OUTPUT: A ratio of similarity between the two wordlist files (Range of 0.0 to 1.0)
    """

    parser = argparse.ArgumentParser(description='Basic comparator for wordlists. Calculates the ratio of similarity.')
    parser.add_argument('file1', type=str)
    parser.add_argument('file2', type=str)

    args = parser.parse_args()

    generated_word_file = ""
    reference_word_file = ""
    if args.file1 and args.file2:
        generated_word_file = args.file1
        reference_word_file = args.file2
    else:
        parser.print_help()
        exit()

    tk = ToolKit()

    ref_word_list = tk.get_file(reference_word_file)
    gen_word_list = tk.get_file(generated_word_file)

    print(Levenshtein.seqratio(gen_word_list, ref_word_list))




