
import sys
import itertools

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

def day_02a(input_data):
    input_list = input_data.strip().split()
    return reduce(
                int.__mul__,
                [
                   sum(letter_count)
                   for letter_count in zip(
                      *[
                          (2 in counts, 3 in counts)
                          for word in input_list
                          for counts in [
                              set((2,3)).intersection(
                                  set(
                                      count_letters_in_word(word).values()
                                  )
                              )
                          ]
                      ]
                   )
               ]
           )

def identical_letters(word1, word2):
    return ''.join(letter1 for (letter1, letter2) in zip(word1, word2) if letter1 == letter2)

def day_02b(input_data):
    input_list = input_data.strip().split()
    box_id_identical_part = [
            identical_part
            for (word1, word2) in itertools.combinations(input_list, 2)
            for identical_part in [identical_letters(word1, word2)]
            if len(identical_part) + 1 == len(word1)
                and len(identical_part) + 1 == len(word2)
        ][0]
    return box_id_identical_part

input_data = open('day_02.input').read()

print "Day 02 a = {}".format(day_02a(input_data))
print "Day 02 b = {}".format(day_02b(input_data))
