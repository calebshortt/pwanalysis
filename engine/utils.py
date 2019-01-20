
def generate_ngrams(word_list, min_size=2, max_size=None):
    ngrams = []
    for word in word_list:
        for start_pos in range(len(word)):
            for end_pos in range(start_pos+min_size, len(word)+1):

                if max_size and end_pos - start_pos > max_size:
                    break

                ngrams.append(word[start_pos:end_pos])

    return ngrams

# if __name__ == "__main__":
#     test = ["test", ]
#     print('NGrams: ' + str(generate_ngrams(test, max_size=2)))