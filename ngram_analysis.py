
import argparse
import logging
import time
import hashlib

from engine.base import NGramCounter, NGramGenerator
from engine.analytics import NGramAnalyzer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

"""
    Examples:
        Generate ngrams:                                    ./ngram_analysis -f passwords.txt -n -o pw_ngrams.ngram
        Generate Markov Matrix from ngrams:                 ./ngram_analysis -f pw_ngrams.ngram -m -o mm.model
        Generate 50 passwords of length 10 from M. Matrix:  ./ngram_analysis -f mm.model -g 10 -G 50

        ./ngram_analysis -f resources/10_million_password_list_top_1000000.txt -n -o results/pw_ngrams.ngram
        ./ngram_analysis -f results/pw_ngrams.ngram -m -o results/mm.model
        ./ngram_analysis -f results/mm.model -g 10 -G 50


"""

if __name__ == "__main__":

    start_time = time.time()

    parser = argparse.ArgumentParser(description='Basic n-gram generator and analyzer based on a word-list file.')
    parser.add_argument('-f', dest='filepath', type=str, default=None, help='Path to the word-list file.')
    parser.add_argument('-n', dest='genngrams', action='store_true', help='Generate ngrams from given list file.')
    parser.add_argument('-o', dest='outfile', type=str, default=None, help='File to save output to.')
    parser.add_argument('-p', dest='print_n', type=int, default=None, help='Print the top N ngrams to screen.')
    parser.add_argument('-m', dest='markov', action='store_true', help='Generate Markov Matrix from counted ngram list')
    parser.add_argument('-g', dest='genpw', type=int, default=None, help='Generate a password from the given markov model file with given length')
    parser.add_argument('-G', dest='genpws', type=int, default=None, help='Supplemental flag for -g, repeat N times.')
    args = parser.parse_args()

    ngg = None
    nga = None
    if args and args.filepath:
        ngg = NGramGenerator(args.filepath)
        nga = NGramAnalyzer(args.filepath)
    else:
        parser.print_usage()
        exit()

    # Generator functions
    if args.genngrams:
        ngg.run()

        counter = NGramCounter(ngg.destination_file)
        ngrams = counter.count_ngrams()
        sorted_ngrams = sorted(ngrams, key=ngrams.__getitem__, reverse=True)

        if args.print_n and args.print_n > 0:
            n = args.print_n
            top_ngrams = sorted_ngrams[:n]

            for ng in top_ngrams:
                print('%s:%s' % (ng, ngrams[ng]))

        save_file = 'RESULT_%s.ngram' % (hashlib.sha256(str(time.time()).encode('utf-8')).hexdigest()[:10])
        if args.outfile and args.outfile is not None:
            save_file = args.outfile

        logger.debug('Saving sorted ngrams to \'%s\'...' % save_file)
        with open(save_file, 'w+') as f:
            for ng in sorted_ngrams:
                f.write('%s,%s\n' % (ng, ngrams[ng]))
        logger.debug('Done.')


    # Analysis functions
    elif args.markov:

        save_file = 'RESULT_%s.model' % (hashlib.sha256(str(time.time()).encode('utf-8')).hexdigest()[:10])
        if args.outfile and args.outfile is not None:
            save_file = args.outfile

        char_freqs, mm = nga.generate_markov_matrix(savefile=save_file)

        for ch, freq in char_freqs.items():
            print('(%s=%s)' % (ch, freq), end=' ')

        print('\n')

        for ch, ch_matrix in mm.items():
            print(ch, end=' ')
            for ch2, p_ch2 in ch_matrix.items():
                print('(%s:%.4f) ' % (ch2, p_ch2), end=' ')
            print()

    elif args.genpw:
        num_pws = args.genpws if args.genpws else 100

        for i in range(num_pws):
            pw = nga.generate_pw_from_mm(args.genpw, prune=True, threshold=0.07)
            print('Generated Password: %s' % pw)

    end_time = time.time()
    logger.debug('Runtime: %s' % (end_time - start_time, ))

