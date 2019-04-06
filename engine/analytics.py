
import logging
import numpy as np

from itertools import islice

from engine.utils import generate_ngrams, load_obj, save_obj

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
                sanitized = [str(ng).strip('\n\r') for ng in data_chunk]
                total_ngrams_checked += len(sanitized)

                for ng in word_ngrams:
                    similar_ngrams = similar_ngrams + [x for x in sanitized if str(ng) == str(x)]

                logger.debug('Completed iteration %s (chunk-size=%s)' % (iteration, self.chunk_size))
                iteration += 1

        return word_ngrams, similar_ngrams, total_ngrams_checked

    def generate_markov_matrix(self, savefile=None, ng_filepath=None):

        logger.debug('Generating Markov Matrix from n-grams...')
        mm = {}
        char_freqs = {}
        ng_fp = ng_filepath if ng_filepath else self.pw_ng_filepath


        with open(ng_fp, encoding='utf-8') as f:

            data_chunk = ['test', ]
            iteration = 0
            while data_chunk:
                data_chunk = list(islice(f, self.chunk_size))
                sanitized = [str(ng).strip('\n\r').split('\t') for ng in data_chunk if len(str(ng)) > 0]

                for i, item in enumerate(sanitized):
                    ng, ng_count = item
                    if len(ng) < 2:
                        if len(ng) == 1:
                            # Count the frequencies of single chars
                            char_freqs[ng] = int(ng_count)
                        # Don't want to consider ngrams that have a length less than 2
                        continue

                    ng_ngrams = generate_ngrams([ng], max_size=2)
                    for ch1, ch2 in ng_ngrams:
                        ng_matrix = mm.get(ch1, {})
                        curr_ng_count = ng_matrix.get(ch2, 0)
                        ng_matrix[ch2] = int(ng_count) + curr_ng_count
                        mm[ch1] = ng_matrix

                logger.debug('Completed iteration %s (chunk-size=%s) (Markov Matrix Side' % (iteration, self.chunk_size))
                iteration += 1

        p_mm = self._calculate_markov_probabilities(mm)

        if savefile:
            save_obj((char_freqs, p_mm), savefile)

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

    def generate_pw_from_mm(self, pw_length, prune=False, threshold=0.1, mutation_rate=0.1, onlyascii=True, filepath=None):
        """

        :param pw_length:
        :param prune:
        :param threshold: the minimum probability that the char frequency must be to be included
        :param mutation_rate:
        :return:
        """
        mm_fp = filepath if filepath else self.pw_ng_filepath
        char_freqs, mm = load_obj(mm_fp)

        # Special select of first character based on derived password frequency distribution (comes with markov model)
        char_freqs_total = sum(char_freqs.values())
        freq_probs = []
        chars = []
        for ch, count in char_freqs.items():
            chars.append(ch)
            freq_probs.append(float(count)/char_freqs_total)

        first_char = np.random.choice(chars, p=freq_probs)

        generated_password = str(first_char)
        prev_char = first_char

        for i in range(pw_length-1):
            next_char = self._get_next_char_from_mm(prev_char, mm, prune=prune, threshold=threshold,
                                                    mutation_rate=mutation_rate, onlyascii=onlyascii)
            generated_password += str(next_char)

        return generated_password

    def _get_next_char_from_mm(self, current_char, mm, prune=False, threshold=0.1, mutation_rate=0.01, onlyascii=True):

        curr_ch_matrix = mm.get(current_char, {})
        char_freqs_total = sum(curr_ch_matrix.values())

        freq_probs = []
        chars = []

        if prune or onlyascii:
            # Do a first-pass to remove all items below the threshold and then recalculate the freq total, and reconstruct dict
            ch_values = []
            for ch, count in curr_ch_matrix.items():
                ch_prob = float(count)/char_freqs_total
                if prune and ch_prob < threshold:
                    continue
                if onlyascii and ord(ch) > 127:
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

        if len(chars) > 0 and len(freq_probs) > 0:
            mutate = np.random.choice([True, False], p=[mutation_rate, 1.0-mutation_rate])
            if mutate:
                selection = np.random.choice(chars)
            else:
                selection = np.random.choice(chars, p=freq_probs)
        else:
            selection = ''
        return selection










