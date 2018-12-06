
import sys
import itertools

# process the input data into a list of words (box ids)

def process_input_data(input_data):
    return input_data.strip().split()

# return a dictionary counting how many times each letter occurs in a word.

def count_letters_in_word(word):
    return reduce(
                lambda lettercounts, letter:
                    dict(
                        lettercounts.items()
                        + [ (letter, lettercounts.get(letter, 0) + 1) ]
                    ),
                word,
                {}
            )

# For each word in the input data, count the number of times letters
# appear (disregarding the letters themselves) and record whether or
# not any letter appeared exactly twice and whether or not any letter
# appeared exactly three times.
#
# zip the results into a list of the letter-appeared-twice values and
# the letter-appeared-thrice values.
#
# Sum each such list (since False sums to 0 and True sums to 1),
# then multiple the sums of the two lists together.

def part_1(input_data):
    return reduce(
                int.__mul__,
                [
                   sum(letter_count)
                   for letter_count in zip(
                      *[
                          (2 in counts, 3 in counts)
                          for word in input_data
                          for counts in [
                              set(
                                  count_letters_in_word(word).values()
                              )
                          ]
                      ]
                   )
               ]
           )

# return the string of letters which are identical (the same letter in
# the same position) between two words.

def identical_letters(word1, word2):
    return ''.join(letter1 for (letter1, letter2) in zip(word1, word2) if letter1 == letter2)

def part_2(input_data):
    box_id_identical_part = [
            identical_part
            for (word1, word2) in itertools.combinations(input_data, 2)
            for identical_part in [identical_letters(word1, word2)]
            if len(identical_part) + 1 == len(word1)
                and len(identical_part) + 1 == len(word2)
        ][0]
    return box_id_identical_part

if __name__ == '__main__':

    sample_data = process_input_data(open(__file__.rsplit('.')[0] + '.sample').read())
    sample_data_2 = process_input_data(open(__file__.rsplit('.')[0] + '.sample.2').read())

    print "sample data: part 1 = {}".format(part_1(sample_data))
    print "sample data: part 2 = {}".format(part_2(sample_data_2))

    input_data = process_input_data(open(__file__.rsplit('.')[0] + '.input').read())

    print "real input: part 1 = {}".format(part_1(input_data))
    print "real input: part 2 = {}".format(part_2(input_data))
