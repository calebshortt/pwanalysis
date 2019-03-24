
import logging

from sklearn.svm import OneClassSVM

from engine.utils import only_ascii, get_file


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)


class PasswordVerifier(object):

    classifier = None

    def __init__(self):
        pass

    def init_classifier(self, pw_dump_filename, ascii_only=True):
        """
        Initialize the classifier and train it with a known password dump (provided)
        :param mm_filename: Markov Model file
        :param pw_dump_filename: Password dump file that will be used to train the classifier
        :return:
        """
        logger.debug('Initializing classifier...')
        self.classifier = OneClassSVM(kernel="rbf", gamma='auto')

        logger.debug('Loading password dump training file...')
        # TODO: Assumption: List of passwords can be loaded into memory to train classifier
        with open(pw_dump_filename, encoding='utf-8') as f:
            pws = get_file(f, chunk_size=10000)

        logger.debug('Formatting strings for classification...')
        if ascii_only:
            num_pws = [self.str_to_numbers(only_ascii(s)) for s in pws]
        else:
            num_pws = [self.str_to_numbers(s) for s in pws]

        logger.debug('Training classifier...')
        self.classifier.fit(num_pws)
        logger.debug('Initialization complete.')

    def classify_passwords(self, password_list):
        if not self.classifier:
            raise AttributeError('Attempted to use uninitiated classifier')
        num_pws = [self.str_to_numbers(s.strip('\n\r')) for s in password_list]
        return [x > 0 for x in self.classifier.predict(num_pws)]

    def str_to_numbers(self, string, ascii_only=True):

        # TODO: I KNOW there is a better way to do this -- figure it out
        if ascii_only:
            result = [0]*128
        else:
            # The number of unicode entries
            result = [0]*137928

        for ch in string:
            try:
                result[ord(ch)] = ord(ch)
            except:
                logger.error('ERROR: ord(%s) = %s' % (ch, ord(ch)))
                raise
        return result

