
import re
import sys
import itertools

DEBUGGING=False
if DEBUGGING:
    def reduce(func, iterable, initial=None):
        iterable = iter(iterable)
        if initial is None:
            initial = iterable.next()
        for value in iterable:
            print >> sys.stderr, ">>reduce<< state={0!r} value={1!r}".format(initial, value)
            initial = func(initial, value)
        print >> sys.stderr, ">>reduce<< final state={0!r}".format(initial)
        return initial

########################################################################
#
# Process input data to return the appropriate records or data format.

process_input_data = lambda input_data: (
            input_data
        )

########################################################################
#
# Part 1:   ...

part_1 = lambda input_data: (
            None
        )

########################################################################
#
# Part 2:   ...

part_2 = lambda input_data: (
            None
        )

if __name__ == '__main__':

    sample_data = process_input_data(open(__file__.rsplit('.')[0] + '.sample').read())

    print "sample data: part 1 = {}".format(part_1(sample_data))
    print "sample data: part 2 = {}".format(part_2(sample_data))

    if DEBUGGING: sys.exit(0)

    input_data = process_input_data(open(__file__.rsplit('.')[0] + '.input').read())

    print "real input: part 1 = {}".format(part_1(input_data))
    print "real input: part 2 = {}".format(part_2(input_data))
