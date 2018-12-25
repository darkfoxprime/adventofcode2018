
import re
import sys
import itertools
import time
import operator
import os.path
import pprint

run_part_1 = True
run_part_2 = False

run_samples = True
run_data = True

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

real_accumulate = accumulate
def debug_accumulate(iterable, func = operator.add):
    def debug(state, value):
        print >> sys.stderr, ">>accumulate<< element={!r}".format(value)
        return func(state, value)
    for state in real_accumulate(iterable, debug):
        print >> sys.stderr, ">>accumulate<< state={!r}".format(state)
        yield state
    print >> sys.stderr, ">>accumulate<< done"

real_reduce = reduce
def debug_reduce(func, *args):
    def debug(state, value):
        print >> sys.stderr, ">>reduce<< state={!r} value={!r}".format(state, value)
        return func(state, value)
    final = real_reduce(debug, *args)
    print >> sys.stderr, ">>reduce<< final state={0!r}".format(final)
    return final

if DEBUGGING:

    print >> sys.stderr, "Debugging version of `reduce` enabled"

    reduce = debug_reduce

if DEBUGGING:

    print >> sys.stderr, "Debugging version of `accumulate` enabled"

    accumulate = debug_accumulate

def debug_value(prefix, value):
    print >> sys.stderr, '{}{}'.format(prefix, value)
    return value

########################################################################
#
# Process input data to return the appropriate records or data format.
#
# Each non-empty line consists of 4 comma (`,`) separated integers.
# Return a list of 4-tuples.

process_input_data = lambda input_data: (
            list(
                tuple(
                    int(xyzt)
                    for xyzt in line.split(',')
                )
                for line in input_data.split()
                if line
            )
        )

########################################################################
#
# Determine the manhattan distance between two spacetime points.

distance = lambda p1,p2: (
            abs(p1[0]-p2[0])
            + abs(p1[1]-p2[1])
            + abs(p1[2]-p2[2])
            + abs(p1[3]-p2[3])
        )

########################################################################
#
# Return True if a new point is part of a constellation.
#
# A constellation is a set of spacetime points.  A new point is part of
# that constellation if it's manhattan distance to at least one of the
# existing constellation points is less than or equal to 3.

is_part_of_constellation = lambda point, constellation: (
            isinstance(
                itertools.dropwhile(
                    lambda constellation_point: (
                        constellation_point
                        and
                        distance(point, constellation_point) > 3
                    )
                    ,
                    itertools.chain(
                        constellation
                        ,
                        [False]
                    )
                ).next()
                ,
                tuple
            )
        )

########################################################################
#
# constellations
#
# Return the sets of spacetime points that make up constellations.
# a constellation is a set of points, all of which are within manhattan
# distance 3 of at least one other point in the constellation.
#
# Time to try this again.
#
# This is a reduction, checking each point to see whether it joins any
# existing constellation.  Each point starts as a constellation on its
# own.  Each existing constellation that the new point can join is
# removed from the set of constellations and unioned into the new constellation
# being formed.  At the end, the new constellation is added into the set
# of all constellations.
#
# So, a reduction that runs against the list of spacetime points with
# an initial state of an empty set.
#
# Each step of the reduction,
#
#     Filter the set of existing constellations to those to which the
#     new point can join.
#
#     Remove the set of those joinable constellations from the overall
#     set, and add in a new constellation of the union of the joinable
#     constellations with each other and the new point.
#
# Return the set of constellations.

constellations = lambda points: (
            reduce(
                lambda constellations, point: (
                    (
                        constellations
                        - set(joinable) 
                    ) | set([
                        reduce(
                            lambda c1,c2: c1 | c2
                            ,
                            joinable
                            ,
                            frozenset([point])
                        )
                    ])
                    for joinable in [
                        [
                            constellation
                            for constellation in constellations
                            if is_part_of_constellation(point, constellation)
                        ]
                    ]
                ).next()
                ,
                points
                ,
                set()
            )
        )

########################################################################
#
# Part 1:   Return the number of constellations in the input data

part_1 = lambda input_data: (
            len(constellations(input_data))
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

    if run_part_1 and run_samples:

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
            if DEBUGGING: print >> sys.stderr, "\nprocessing {} with expected results {}".format(sample_filename, expected)
            result = part_1(process_input_data(sample_data))
            if DEBUGGING: result = '\n' + pprint.pformat(result) + '\n'
            t = time.time() - t
            print "{}: sample {}: part 1 = {}{}".format(t, sample_num, result, " (expected {})".format(expected) if result != expected else "")

    if run_part_1 and run_data:

        t = time.time()
        if DEBUGGING: print >> sys.stderr, "\nprocessing {}".format(sample_filename)
        result = part_1(process_input_data(input_data))
        if DEBUGGING: result = '\n' + pprint.pformat(result) + '\n'
        t = time.time() - t
        print "{}: input data: part 1 = {}".format(t, result)

    if run_part_2 and run_samples:

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
            if DEBUGGING: print >> sys.stderr, "\nprocessing {} with expected results {}".format(sample_filename, expected)
            result = part_2(process_input_data(sample_data))
            if DEBUGGING: result = '\n' + pprint.pformat(result) + '\n'
            t = time.time() - t
            print "{}: sample {}: part 2 = {}{}".format(t, sample_num, result, " (expected {})".format(expected) if result != expected else "")

    if run_part_2 and run_data:

        t = time.time()
        if DEBUGGING: print >> sys.stderr, "\nprocessing {}".format(sample_filename)
        result = part_2(process_input_data(input_data))
        if DEBUGGING: result = '\n' + pprint.pformat(result) + '\n'
        t = time.time() - t
        print "{}: input data: part 2 = {}".format(t, result)

