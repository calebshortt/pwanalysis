# NGram Analysis: Password Generator

A password generator that takes password dumps, generates predictive models from them, then validates them against machine learning algorithms to produce strings that look like passwords but are not in the given wordlist.

# Usage

To install the framework:

    $ git clone https://github.com/calebshortt/pwanalysis.git
    $ cd pwanalysis
    $ pip install -r requirements.txt

To run the framework from start to end
NOTE: Genereates all models and then produces 100 passwords of length:

    $ python ngram_analysis -A rockyou.txt

Then you can generate as many passwords as you wish from the model by using:

    $ -f <result file.model> -G 1000 -g 8 -V resources/rockyou.txt

To run ngram analysis in its separate stages:
Note: The framework does multiple things:
   1. Generate all possible ngrams from a given password list
   2. Create a markov model from the generated ngram file
   3. Generate -G passwords of length -g and validate the passwords against an algorithm trained against -V <pw-file>

    $ python ngram_analysis -f rockyou.txt -n -o ry_ngrams.ngram
    $ python ngram_analysis -f ry_ngrams.ngram -m -o ry_mm.model
    $ python ngram_analysis -f ry_mm.model -g 10 -G 50 -V rockyou.txt




### Further Notes:

This framework does not include any password files. Users will have to use their own.