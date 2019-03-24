
import argparse
import logging
import time
import hashlib

from engine.base import NGramCounter, NGramGenerator
from engine.analytics import NGramAnalyzer
from engine.validation import PasswordVerifier

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

"""
    General format:   ./ngram_analysis.py -f <file to act on> <action flag> -o <output file>

    Examples:
        Generate ngrams:                                    ./ngram_analysis -f passwords.txt -n -o pw_ngrams.ngram
        Generate Markov Matrix from ngrams:                 ./ngram_analysis -f pw_ngrams.ngram -m -o mm.model
        Generate 50 passwords of length 10 from M. Matrix:  ./ngram_analysis -f mm.model -g 10 -G 50

        NOTE:
            Add -V <password file> to "-g" to validate generated passwords against a trained classifier
            See below example

        ./ngram_analysis -f resources/10_million_password_list_top_1000000.txt -n -o results/pw_ngrams.ngram
        ./ngram_analysis -f results/pw_ngrams.ngram -m -o results/mm.model
        ./ngram_analysis -f results/mm.model -g 10 -G 50 -V resources/rockyou.txt


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
    parser.add_argument('-V', dest='validate', type=str, help='Use this password file to validate generated passwords.')
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
        counter.count_ngrams()

        save_file = 'RESULT_%s.ngram' % (hashlib.sha256(str(time.time()).encode('utf-8')).hexdigest()[:10])
        if args.outfile and args.outfile is not None:
            save_file = args.outfile

        logger.debug('Saving sorted ngrams to \'%s\'...' % save_file)
        with open(save_file, 'w+', encoding='utf-8') as f:
            printed = False
            for chunk in counter.get_next_top_db_ngrams(n=counter.chunk_size):
                if args.print_n and args.print_n > 0 and not printed:
                    top_ngrams = chunk[:min(args.print_n, counter.chunk_size)]
                    for ng, ct in top_ngrams:
                        print('%s:%s' % (ng, ct))
                    printed = True

                for ng, ct in chunk:
                    # f.write('%s,%s\n' % (ng, ct))
                    f.write('%s\t%s\n' % (ng, ct))
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

        validator = None
        if args.validate:
            validator = PasswordVerifier()
            validator.init_classifier(args.validate)

        gen_pws = []
        while len(gen_pws) < num_pws:
            pw = nga.generate_pw_from_mm(args.genpw, prune=False, threshold=0.07, onlyascii=True)
            if validator:
                keep = validator.classify_passwords([pw])[0]
                if keep:
                    gen_pws.append(pw)
                    print(pw)
            else:
                gen_pws.append(pw)
                print(pw)

    end_time = time.time()
    logger.debug('Runtime: %s' % (end_time - start_time, ))

