
"""
    For efficiency, this will probably have to be written in C and scaled with hadoop for practical use

    Disclaimer: this is a prototype

    Benchmarks:
        (Laptop):   1 million words:    64s
"""

import argparse
import os
import logging
import time
import hashlib

from itertools import islice

from engine.utils import generate_ngrams

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class NGramGenerator(object):

    word_list = []
    ngrams = []

    chunk_size = 500000

    filepath = None
    base_fname = 'split_data'
    base_ext = '.txt'

    destination_file = 'destination_file.txt'

    def __init__(self, filepath, chunk_size=500000):
        if not filepath or type(filepath) is not str:
            raise AttributeError("Invalid file path.")

        self.filepath = filepath
        self.chunk_size = chunk_size
        self.destination_file = '%s_ngram_%s' % (self.base_fname, self.base_ext)

    def _word_is_valid(self, word):
        word = word.strip()
        if len(word) < 1:
            return False

        if not word or type(word) is not str:
            return False

        return True

    def run(self):
        with open(self.filepath) as f:

            self.base_fname, self.base_ext = os.path.splitext(f.name)

            data_chunk = ['test', ]
            iteration = 0
            while data_chunk:
                data_chunk = list(islice(f, self.chunk_size))
                sanitized = [str(word).strip() for word in data_chunk if self._word_is_valid(word)]

                chunk_ngrams = generate_ngrams(sanitized, min_size=1)

                logger.debug('iteration: %s\tChunk-Size: %s' % (iteration, len(data_chunk)))
                iteration += 1

                self._save_chunk(chunk_ngrams)

    def _save_chunk(self, data):
        self.destination_file = '%s_ngrams_%s' % (self.base_fname, self.base_ext)
        logger.debug("Saving data... (Save File=%s)" % self.destination_file)

        with open(self.destination_file, 'a+') as f:
            for ng in data:
                f.write('%s\n' % ng)
        logger.debug("Done.")


class NGramCounter(object):

    counts = {}

    filepath = None
    chunk_size = 500000

    def __init__(self, filepath, chunk_size=500000):
        self.filepath = filepath
        self.chunk_size = chunk_size

    def count_ngrams(self):

        logger.debug('Counting ngram frequencies in chunks...')

        with open(self.filepath, 'r') as f:
            data_chunk = ['test', ]
            iteration = 0
            while data_chunk:
                data_chunk = list(islice(f, self.chunk_size))
                ngrams = [str(ngram).strip() for ngram in data_chunk]

                for ng in ngrams:
                    count = self.counts.get(ng, 0)
                    count += 1
                    self.counts[ng] = count

                logger.debug('Done chunk: %s\tChunk-Size: %s' % (iteration, len(data_chunk)))
                iteration += 1

        logger.debug('Done counting ngram frequencies.')
        return self.counts

if __name__ == "__main__":

    start_time = time.time()

    parser = argparse.ArgumentParser(description='Basic n-gram generator based on a word-list file.')
    parser.add_argument('-f', dest='filepath', type=str, default=None, help='Path to the word-list file.')
    parser.add_argument('-o', dest='outfile', type=str, default=None, help='File to save output to.')
    parser.add_argument('-p', dest='print_n', type=int, default=None, help='Print the top N ngrams to screen.')
    args = parser.parse_args()

    ngg = None
    if args and args.filepath:
        ngg = NGramGenerator(args.filepath)
    else:
        parser.print_usage()
        exit()

    ngg.run()

    counter = NGramCounter(ngg.destination_file)
    ngrams = counter.count_ngrams()
    sorted_ngrams = sorted(ngrams, key=ngrams.__getitem__, reverse=True)

    if args.print_n and args.print_n > 0:
        n = args.print_n
        top_ngrams = sorted_ngrams[:n]

        for ng in top_ngrams:
            print('%s:%s' % (ng, ngrams[ng]))

    save_file = 'RESULT_%s' % (hashlib.sha256(str(time.time()).encode('utf-8')).hexdigest()[:10])
    if args.outfile:
        save_file = args.outfile

    logger.debug('Saving sorted ngrams to \'%s\'...' % args.outfile)
    with open(args.outfile, 'w+') as f:
        for ng in sorted_ngrams:
            f.write('%s,%s\n' % (ng, ngrams[ng]))
    logger.debug('Done.')

    end_time = time.time()
    logger.debug('Runtime: %s' % (end_time - start_time, ))








