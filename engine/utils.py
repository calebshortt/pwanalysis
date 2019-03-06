
def generate_ngrams(word_list, min_size=2, max_size=None, logger=None, max_wordlen=128):
    ngrams = []
    for word in word_list:
        if len(word) > max_wordlen:
            if logger:
                logger.debug('Skipping words of length greater than %s' % max_wordlen)
                logger.debug('Skipped word: %s' % word)
            continue

        for start_pos in range(len(word)):
            for end_pos in range(start_pos+min_size, len(word)+1):

                if max_size and end_pos - start_pos > max_size:
                    break

                try:
                    ngrams.append(word[start_pos:end_pos])
                except MemoryError:
                    if logger:
                        logger.debug('Excepting word length: %s' % len(word))
                        logger.debug('Excepting word: %s' % word)
                    raise

    return ngrams


