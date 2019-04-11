
import collections, operator

from engine import utils


class ToolKit(object):

    def get_charcount(self, filepath):
        with open(filepath, 'r') as f:
            str_list = utils.get_file(f)
        char_count = collections.Counter(''.join(str_list))
        return char_count


if __name__ == "__main__":
    """
    Compare character counts and distributions between two list of passwords
    """
    file1 = "resources/___unvalidated.txt"
    file2 = "resources/___validated_pwlen_fortraining.txt"

    tk = ToolKit()

    f1_count = tk.get_charcount(file1)
    f2_count = tk.get_charcount(file2)

    sorted_f1 = sorted(f1_count.items(), key=operator.itemgetter(1), reverse=True)
    sorted_f2 = sorted(f2_count.items(), key=operator.itemgetter(1), reverse=True)

    for i in range(min(100, min(len(sorted_f1), len(sorted_f2)))):
        print('%s\t%s' % (sorted_f1[i], sorted_f2[i]))



