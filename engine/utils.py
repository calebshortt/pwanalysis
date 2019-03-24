
import pickle


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

def load_obj(filepath):
    with open(filepath, 'rb') as f:
        return pickle.load(f)

def save_obj(self, obj, filepath ):
    with open(filepath, 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def only_ascii(char_list):
    return [ch for ch in char_list if ord(ch) < 128]

def get_file(f, chunk_size=1000000):
    result = []
    for i in range(chunk_size):
        result.append(f.readline().strip('\n\r'))
    return result



