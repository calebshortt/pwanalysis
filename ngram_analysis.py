
import argparse
import logging
import time
import hashlib

import settings
from engine.base import NGramCounter, NGramGenerator
from engine.analytics import NGramAnalyzer
from engine.validation import PasswordVerifier


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.ERROR)

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
    parser.add_argument('-A', dest='all', type=str, help='Run entire framework on provied wordlist.')
    args = parser.parse_args()

    ngg = None
    nga = None
    ng_save_file = None
    mm_save_file = None
    if args and (args.filepath or args.all):
        fp = args.filepath if args.filepath else args.all
        ngg = NGramGenerator(fp)
        # nga = NGramAnalyzer(fp)
    else:
        parser.print_usage()
        exit()

    # Generator functions
    if args.genngrams or args.all:
        ngg.run()

        counter = NGramCounter(ngg.destination_file)
        counter.count_ngrams()

        ng_save_file = '%sRESULT_%s.%s' % (
            settings.RESULT_PATH,
            hashlib.sha256(str(time.time()).encode('utf-8')).hexdigest()[:10],
            settings.EXT_NG_COUNTS
        )

        if args.outfile and args.outfile is not None:
            ng_save_file = args.outfile

        logger.debug('Saving sorted ngrams to \'%s\'...' % ng_save_file)
        with open(ng_save_file, 'w+', encoding='utf-8') as f:
            printed = False
            for chunk in counter.get_next_top_db_ngrams(n=counter.chunk_size):
                if args.print_n and args.print_n > 0 and not printed:
                    top_ngrams = chunk[:min(args.print_n, counter.chunk_size)]
                    for ng, ct in top_ngrams:
                        print('%s:%s' % (ng, ct))
                    printed = True

                for ng, ct in chunk:
                    f.write('%s\t%s\n' % (ng, ct))
        logger.debug('Done.')


    # Analysis functions
    if args.markov or args.all:

        mm_save_file = '%sRESULT_%s.%s' % (
            settings.RESULT_PATH,
            hashlib.sha256(str(time.time()).encode('utf-8')).hexdigest()[:10],
            settings.EXT_MODEL
        )

        if args.outfile and args.outfile is not None:
            mm_save_file = args.outfile

        nga = NGramAnalyzer(ng_save_file if ng_save_file else ngg.filepath)
        char_freqs, mm = nga.generate_markov_matrix(savefile=mm_save_file)

    if args.genpw or args.all:
        num_pws = args.genpws if args.genpws else 100
        pw_len = args.genpw if args.genpw else 10
        if not nga:
            nga = NGramAnalyzer(args.all if args.all else args.filepath)

        if args.filepath:
            mm_save_file = args.filepath

        validator = None
        if args.validate:
            valid_fp = args.validate if args.validate else args.all
            validator = PasswordVerifier()
            validator.init_classifier(valid_fp, pw_len=pw_len)

        gen_pws = []
        logger.debug('Generating Strings... (Depending on verification values this may take a while)')
        while len(gen_pws) <= num_pws:
            # pw = nga.generate_pw_from_mm(pw_len, prune=False, threshold=0.07, filepath=mm_save_file)
            pw = nga.generate_pw_from_mm(pw_len, prune=False, threshold=0.2, filepath=mm_save_file)
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

