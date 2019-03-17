

import os
import logging
import sqlite3
import time

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

    filepath = None
    chunk_size = 500000
    conn = None

    # NGram Count cursor for database -- to get all counts from database -- to be used in generator
    ngc_cursor = None

    def __init__(self, filepath, chunk_size=500000):
        self.filepath = filepath
        self.chunk_size = chunk_size
        self.init_db()

    def init_db(self, db_name='ng_counts.db'):
        if not self.conn:
            self.conn = sqlite3.connect(db_name)
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS ng_counts (id INTEGER PRIMARY KEY, ngram TEXT, ng_count INTEGER)''')
        self.conn.commit()

    def get_db_ngrams(self, counts):
        """
        Get the count values for the ngrams in 'counts' from the database and add them.
        :param counts:
        :return:
        """
        db_ngrams = {}
        cursor = self.conn.cursor()
        cursor.execute('''SELECT ngram, ng_count FROM ng_counts''')

        logger.debug('Fetching count values from DB...')
        start = time.time()
        results = 1
        while results:
            results = cursor.fetchmany(int(self.chunk_size))
            for result in results:
                if result[0] in counts.keys():
                    # db_ngrams[str(result[0])] = int(result[1])
                    counts[str(result[0])] += int(result[1])
        logger.debug('Fetch Duration: %s s' % (time.time()-start, ))
        return counts

    def save_db_ngrams(self, db_ngrams):
        cursor = self.conn.cursor()
        count = 0
        for ng, ng_count in db_ngrams.items():
            cursor.execute('''INSERT OR REPLACE INTO ng_counts (ngram, ng_count) VALUES (?, ?)''', (ng, ng_count))
            count += 1
            if count % 100000 == 0:
                self.conn.commit()

    def get_top_ngrams(self, ng_counts=None, n=100):
        logger.debug('Sorting and counting top ngrams...')
        if ng_counts:
            sorted_ngrams = sorted(ng_counts, key=ng_counts.__getitem__, reverse=True)
            return sorted_ngrams[:n]

        logger.debug('Reverting to database. This may take a few minutes...')
        cursor = self.conn.cursor()
        cursor.execute('''SELECT ngram, SUM(ng_count) AS ngc FROM ng_counts GROUP BY ngram ORDER BY ngc DESC''')
        results = cursor.fetchmany(n)
        return [k for k, v in list(results)]

    def get_next_top_db_ngrams(self, n=100, reset=False):
        if not self.ngc_cursor or reset:
            logger.debug('Querying database. This may take a few minutes...')
            self.ngc_cursor = self.conn.cursor()
            self.ngc_cursor.execute('''SELECT ngram, SUM(ng_count) AS ngc FROM ng_counts GROUP BY ngram ORDER BY ngc DESC''')

        while True:
            result = self.ngc_cursor.fetchmany(n)
            if not result:
                break
            yield result

    def count_ngrams(self):

        logger.debug('Counting ngram frequencies in chunks...')
        counts = {}
        used_db = False

        with open(self.filepath, 'r', encoding='utf-8') as f:
            data_chunk = ['test', ]
            iteration = 0
            while data_chunk:
                data_chunk = list(islice(f, self.chunk_size))
                data_chunk = [str(ngram).strip('\n\r') for ngram in data_chunk]

                logger.debug('Counting chunk %s' % iteration)

                for ng in data_chunk:
                    try:
                        counts[ng] = counts.get(ng, 0) + 1
                    except MemoryError:
                        logger.debug('\tMemory Error. Reverting to DB. NOTE: This is slow.')
                        logger.debug('\tChecking DB for data values')

                        used_db = True
                        db_ngrams = self.get_db_ngrams(counts)

                        # Dump data chunk to free some memory
                        data_chunk = ['test', ]
                        for ng, ng_count in counts.items():
                            counts[ng] = ng_count + db_ngrams.get(ng, 0)

                        logger.debug('\tAdding data to DB')
                        self.save_db_ngrams(counts)
                        counts = {}

                logger.debug('\tDone chunk: %s\tChunk-Size: %s' % (iteration, len(data_chunk)))
                iteration += 1

        # Save any left-over counts to the DB
        logger.debug('Saving final counts...')
        self.save_db_ngrams(counts)
        logger.debug('Done counting ngram frequencies.')
        return counts, used_db









