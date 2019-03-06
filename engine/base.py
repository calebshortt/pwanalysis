

import os
import logging

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
        word = word.strip('\n\r')
        if len(word) < 1:
            return False

        if not word or type(word) is not str:
            return False

        return True

    def run(self):
        with open(self.filepath, encoding='utf-8') as f:

            self.base_fname, self.base_ext = os.path.splitext(f.name)

            data_chunk = ['test', ]
            iteration = 0
            while data_chunk:

                data_chunk = list(islice(f, self.chunk_size))
                data_chunk = [str(word).strip('\n\r') for word in data_chunk if self._word_is_valid(word)]

                try:
                    chunk_ngrams = generate_ngrams(data_chunk, min_size=1, logger=logger)
                    logger.debug('iteration: %s\tChunk-Size: %s' % (iteration, len(data_chunk)))
                    iteration += 1
                    self._save_chunk(chunk_ngrams)
                    chunk_ngrams = []

                except MemoryError:
                    # If memory error, the resulting chunk_ngrams list is too big -- dial it back by an order of
                    # magnitude and go through the sublists individually and save the resulting ngrams
                    # NOTE: Rough usage metrics: caps at 800MG ram per chunk -- depends on word length though (ngram generation)

                    logger.debug('---------- Ran out of memory. Dialing back chunk size to handle ngram load. ----------')
                    sub_chunk_lengths = int(len(data_chunk)/10)
                    data_chunk = [data_chunk[x:x+sub_chunk_lengths] for x in range(0, len(data_chunk), sub_chunk_lengths)]

                    for sublist in data_chunk:
                        logger.debug('SUBLIST Length = %s' % len(sublist))
                        chunk_ngrams = generate_ngrams(sublist, min_size=1, logger=logger)
                        logger.debug('iteration: %s\tChunk-Size: %s' % (iteration, len(sublist)))
                        iteration += 1
                        self._save_chunk(chunk_ngrams)
                        chunk_ngrams = []

                    logger.debug('Recovered from Memory Error. Reverting back to normal ngram chunk size.')


    def _save_chunk(self, data):
        self.destination_file = '%s_ngrams_%s' % (self.base_fname, self.base_ext)
        logger.debug("Saving data... (Save File=%s)" % self.destination_file)

        with open(self.destination_file, 'a+', encoding='utf-8') as f:
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

        with open(self.filepath, 'r', encoding='utf-8') as f:
            data_chunk = ['test', ]
            iteration = 0
            while data_chunk:
                data_chunk = list(islice(f, self.chunk_size))
                ngrams = [str(ngram).strip('\n\r') for ngram in data_chunk]

                for ng in ngrams:
                    count = self.counts.get(ng, 0)
                    count += 1
                    self.counts[ng] = count

                logger.debug('Done chunk: %s\tChunk-Size: %s' % (iteration, len(data_chunk)))
                iteration += 1

        logger.debug('Done counting ngram frequencies.')
        return self.counts









