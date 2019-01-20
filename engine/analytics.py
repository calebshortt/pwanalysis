
import argparse
import logging
import time
import sys
import pickle

from numpy.random import choice

from itertools import islice

from engine.utils import generate_ngrams

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class NGramAnalyzer(object):
    """
    Take a list of known password ngrams, then take  word. Break the word into ngrams and see if it could be a password.

    Simple comparison before throwing some algs at it (ANNs, naive bayes, SVMs, etc)
    """

    pw_ng_filepath = None
    chunk_size = 500000

    def __init__(self, pw_ng_filepath, chunk_size=500000):
        self.pw_ng_filepath = pw_ng_filepath
        self.chunk_size = chunk_size

    def compare(self, word):
        logger.debug('Generating n-grams for %s' % word)
        word_ngrams = generate_ngrams([word])

        similar_ngrams = []
        total_ngrams_checked = 0

        logger.debug('Comparing to common password n-grams...')

        with open(self.pw_ng_filepath) as f:

            data_chunk = ['test', ]
            iteration = 0
            while data_chunk:
                data_chunk = list(islice(f, self.chunk_size))
                sanitized = [str(ng).strip() for ng in data_chunk]
                total_ngrams_checked += len(sanitized)

                for ng in word_ngrams:
                    similar_ngrams = similar_ngrams + [x for x in sanitized if str(ng) == str(x)]

                logger.debug('Completed iteration %s (chunk-size=%s)' % (iteration, self.chunk_size))
                iteration += 1

        return word_ngrams, similar_ngrams, total_ngrams_checked

    def generate_markov_matrix(self, save=True):

        logger.debug('Generating Markov Matrix from n-grams...')
        mm = {}
        char_freqs = {}

        with open(self.pw_ng_filepath) as f:

            data_chunk = ['test', ]
            iteration = 0
            while data_chunk:
                data_chunk = list(islice(f, self.chunk_size))
                sanitized = [str(ng).strip().split(',') for ng in data_chunk if len(str(ng)) > 0]

                for ng, ng_count in sanitized:
                    if len(ng) < 2:
                        if len(ng) == 1:
                            char_freqs[ng] = int(ng_count)
                        # Don't want to consider ngrams that have a length less than 2
                        continue

                    ng_ngrams = generate_ngrams([ng], max_size=2)
                    for ch1, ch2 in ng_ngrams:
                        ng_matrix = mm.get(ch1, {})
                        curr_ng_count = ng_matrix.get(ch2, 0)
                        ng_matrix[ch2] = int(ng_count) + curr_ng_count
                        mm[ch1] = ng_matrix

                logger.debug('Completed iteration %s (chunk-size=%s) (Markov Matrix Side (bytes)=%s)' %
                             (iteration, self.chunk_size, sys.getsizeof(mm)))
                iteration += 1

        p_mm = self._calculate_markov_probabilities(mm)

        if save:
            self.save_obj((char_freqs, p_mm), '../results/markov_matrix.pkl')

        return char_freqs, p_mm

    def _calculate_markov_probabilities(self, mm):
        """"
        Assumption: mm is a dict of dicts: {'<char:char>': {'<char:char>': <count:int>, ... }, ... }
        """

        p_mm = {}

        for ch1, ch1_matrix in mm.items():
            total = sum(ch1_matrix.values())
            temp_matrix = {}
            for ch2, ch2_count in ch1_matrix.items():
                temp_matrix[ch2] = float(ch2_count)/total

            p_mm[ch1] = temp_matrix

        return p_mm

    def save_obj(self, obj, filepath ):
        with open(filepath, 'wb') as f:
            pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

    def load_obj(self, filepath):
        with open(filepath, 'rb') as f:
            return pickle.load(f)

    def generate_pw_from_mm(self, pw_length, prune=False, threshold=0.1):

        char_freqs, mm = self.load_obj(self.pw_ng_filepath)

        # Special select of first character based on derived password frequency distribution (comes with markov model)
        char_freqs_total = sum(char_freqs.values())
        freq_probs = []
        chars = []
        for ch, count in char_freqs.items():
            chars.append(ch)
            freq_probs.append(float(count)/char_freqs_total)

        first_char = choice(chars, p=freq_probs)

        generated_password = str(first_char)
        prev_char = first_char

        for i in range(pw_length-1):
            next_char = self._get_next_char_from_mm(prev_char, mm, prune=prune, threshold=threshold)
            generated_password += str(next_char)

        return generated_password

    def _get_next_char_from_mm(self, current_char, mm, prune=False, threshold=0.1):

        curr_ch_matrix = mm.get(current_char, {})
        char_freqs_total = sum(curr_ch_matrix.values())

        freq_probs = []
        chars = []

        if prune:
            # Do a first-pass to remove all items below the threshold and then recalculate the freq total, and reconstruct dict
            ch_values = []
            for ch, count in curr_ch_matrix.items():
                ch_prob = float(count)/char_freqs_total
                if ch_prob < threshold:
                    continue
                chars.append(ch)
                ch_values.append(count)

            char_freqs_total = sum(ch_values)
            curr_ch_matrix = dict(zip(chars, ch_values))
            chars = []

        for ch, count in curr_ch_matrix.items():
            ch_prob = float(count)/char_freqs_total
            chars.append(ch)
            freq_probs.append(ch_prob)

        # print('%s avg=%s ' % (current_char, float(sum(freq_probs)) / len(freq_probs)))

        if len(chars) > 0 and len(freq_probs) > 0:
            selection = choice(chars, p=freq_probs)
        else:
            selection = ''
        return selection







if __name__ == '__main__':
    start_time = time.time()

    parser = argparse.ArgumentParser(description='Basic n-gram generator based on a word-list file')
    parser.add_argument('-f', dest='filepath', type=str, default=None, help='Path to the required file for the intended purpose (use flag)')
    parser.add_argument('-w', dest='word', type=str, default=None, help='Word to analyze')
    parser.add_argument('-m', dest='markov', action='store_true', help='Generate Markov Matrix from counted ngram list')
    parser.add_argument('-g', dest='genpw', type=int, default=None, help='Generate a password form the given markov model file with given length')
    args = parser.parse_args()

    nga = None
    if args.filepath:
        nga = NGramAnalyzer(args.filepath)
    else:
        parser.print_usage()
        exit()

    if args.word and nga:
        word_ngrams, similar_ngrams, total_ngrams_checked = nga.compare(args.word)

        similarity = float(len(similar_ngrams))/len(word_ngrams)
        logger.debug('Similarity: (# similar n-grams)/(# ngrams from word) = %s' % similarity)

    elif args.markov and nga:
        char_freqs, mm = nga.generate_markov_matrix()

        for ch, freq in char_freqs.items():
            print('(%s=%s)' % (ch, freq), end=' ')

        print('\n')

        for ch, ch_matrix in mm.items():
            print(ch, end=' ')
            for ch2, p_ch2 in ch_matrix.items():
                print('(%s:%.4f) ' % (ch2, p_ch2), end=' ')
            print()

    elif args.genpw and nga:

        for i in range(100):
            pw = nga.generate_pw_from_mm(args.genpw, prune=True, threshold=0.07)
            print('Generated Password: %s' % pw)

    end_time = time.time()
    logger.debug('Runtime: %s' % (end_time-start_time, ))









