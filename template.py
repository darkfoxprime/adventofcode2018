
import re
import sys
import itertools
import time
import operator
import os.path

DEBUGGING = False

# pull in python-native version of `accumulate` from python 3
def accumulate(iterable, func=operator.add):
    'Return running totals'
    # accumulate([1,2,3,4,5]) --> 1 3 6 10 15
    # accumulate([1,2,3,4,5], operator.mul) --> 1 2 6 24 120
    it = iter(iterable)
    try:
        total = next(it)
    except StopIteration:
        return
    yield total
    for element in it:
        total = func(total, element)
        yield total

if DEBUGGING:

    print >> sys.stderr, "Debugging version of `reduce` enabled"

    real_reduce = reduce
    def reduce(func, *args):
        def debug(state, value):
            print >> sys.stderr, ">>reduce<< state={!r} value={!r}".format(state, value)
            return func(state, value)
        final = real_reduce(debug, *args)
        print >> sys.stderr, ">>reduce<< final state={0!r}".format(final)
        return final

if DEBUGGING:

    print >> sys.stderr, "Debugging version of `accumulate` enabled"

    real_accumulate = accumulate
    def accumulate(iterable, func = operator.add):
        def debug(state, value):
            print >> sys.stderr, ">>accumulate<< element={!r}".format(value)
            return func(state, value)
        for state in real_accumulate(iterable, debug):
            print >> sys.stderr, ">>accumulate<< state={!r}".format(state)
            yield state
        print >> sys.stderr, ">>accumulate<< done"

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

########################################################################
#
# Main controller

if __name__ == '__main__':

    base_filename = __file__.rsplit('.')[0]

    input_filename = '{}.input'.format(base_filename)
    input_data = open(input_filename).read()

    for sample_num in itertools.takewhile(lambda num:os.path.exists('{}.sample.{}'.format(base_filename, num)), itertools.count(1)):

        sample_filename = '{}.sample.{}'.format(base_filename, sample_num)
        sample_data = open(sample_filename).read()

        results_filename = '{}.sample.results.part1.{}'.format(base_filename, sample_num)
        expected = (
                    int(open(results_filename).read().strip())
                    if os.path.exists(results_filename)
                    else None
                )

        t = time.time()
        result = part_1(process_input_data(sample_data))
        t = time.time() - t
        print "{}: sample {}: part 1 = {}{}".format(t, sample_num, result, " (expected {})".format(expected) if result != expected else "")

    t = time.time()
    result = part_1(process_input_data(input_data))
    t = time.time() - t
    print "{}: input data: part 1 = {}".format(t, result)

    for sample_num in itertools.takewhile(lambda num:os.path.exists('{}.sample.{}'.format(base_filename, num)), itertools.count(1)):

        sample_filename = '{}.sample.{}'.format(base_filename, sample_num)
        sample_data = open(sample_filename).read()

        results_filename = '{}.sample.results.part2.{}'.format(base_filename, sample_num)
        expected = (
                    int(open(results_filename).read().strip())
                    if os.path.exists(results_filename)
                    else None
                )

        t = time.time()
        result = part_2(process_input_data(sample_data))
        t = time.time() - t
        print "{}: sample {}: part 2 = {}{}".format(t, sample_num, result, " (expected {})".format(expected) if result != expected else "")

    t = time.time()
    result = part_2(process_input_data(input_data))
    t = time.time() - t
    print "{}: input data: part 2 = {}".format(t, result)

