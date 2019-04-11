
import os
import logging

from sklearn.svm import OneClassSVM
from pathlib import Path

import settings
from engine.utils import get_file, load_obj, save_obj


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.ERROR)


class PasswordVerifier(object):

    classifier = None

    def __init__(self):
        pass

    def init_classifier(self, pw_dump_filename, chunk_size=100000, **kwargs):
        """
        Initialize the classifier and train it with a known password dump (provided).
        If a pre-trained model exists attempt to load and use it.
        """

        logger.debug('Initializing classifier...')
        self.classifier = OneClassSVM(kernel="rbf", gamma='auto')

        logger.debug('Checking for already-trained models...')
        filename, file_extension = os.path.splitext(os.path.basename(pw_dump_filename))
        model_filepath = '%s%s.%s' % (settings.VALIDATOR_PATH, filename, settings.EXT_VALIDATOR)
        model_file = Path(model_filepath)

        if model_file.is_file():
            self.load_model(model_filepath)

        else:
            logger.debug('Could not find existing model. Training new classifier.')
            self.train_model(pw_dump_filename, chunk_size=chunk_size)
            self.save_model(model_filepath)

    def save_model(self, filepath):
        logger.debug('Saving trained model to %s' % filepath)
        save_obj(self.classifier, filepath)

    def load_model(self, filepath):
        logger.debug('Loading trained model: %s' % filepath)
        self.classifier = load_obj(filepath)

    def train_model(self, pw_dump_filename, chunk_size=100000):
        # TODO: Assumption: List of passwords can be loaded into memory to train classifier
        # TODO: Limiting chunk size to prevent memory errors

        logger.debug('Loading password dump training file...')
        with open(pw_dump_filename, encoding='utf-8') as f:
            pws = get_file(f, chunk_size=chunk_size)

        logger.debug('Formatting strings for classification...')
        num_pws = [self.str_to_numbers(s) for s in pws]

        logger.debug('Training classifier...')
        self.classifier.fit(num_pws)
        logger.debug('Initialization complete.')

    def classify_passwords(self, password_list):
        if not self.classifier:
            raise AttributeError('Attempted to use uninitiated classifier')
        num_pws = [self.str_to_numbers(s.strip('\n\r')) for s in password_list]
        return [x > 0 for x in self.classifier.predict(num_pws)]

    def str_to_numbers(self, string, max_pw_length=100, **kwargs):
        result = [0]*max_pw_length
        for i, ch in enumerate(string):
            try:
                result[i] = ord(ch)
            except:
                logger.error('ERROR: i=%s; result[i] = ord(%s) = %s' % (i, ch, ord(ch)))
                raise
        return result

