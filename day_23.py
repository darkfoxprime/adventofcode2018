
import re
import sys
import itertools
import time
import operator
import os.path
import pprint

import signal
def show_locals(sig,frame):
    pprint.pprint(frame.f_locals, stream=sys.stderr)
signal.signal(signal.SIGUSR1, show_locals)

USE_BLIST = True

if USE_BLIST:
    import blist
    list = blist.blist

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

def debug_value(label, value):
    print >> sys.stderr, '{}{!r}'.format(label, value)
    return value

########################################################################
#
# Process input data to return the appropriate records or data format.
# Return the nanobot information as a list of tuples of (x,y,z,r), all
# integers.

process_input_data = lambda input_data: (
            [
                tuple(
                    int(x)
                    for x in re.split(r'(-?[0-9]+)', line)[1::2]
                )
                for line in input_data.strip().split('\n')
            ]
        )

bot_distance = lambda bot1, bot2: (
            abs(bot1[0] - bot2[0])
            + abs(bot1[1] - bot2[1])
            + abs(bot1[2] - bot2[2])
        )

bots_in_range = lambda nanobots, coords: (
            sum(
                1
                for nanobot in nanobots
                if bot_distance(nanobot, coords) <= nanobot[3]
            )
        )

########################################################################
#
# Part 1:
#
# determine `maxbot`, the maximum powered nanobot, by running the
# nanobots list through `max` with a key of `nanobot[3]` (the radius
# field).
#
# return the length of the nanobots list, filtered to return those
# nanobots for whom the manhattan distance between their pos and
# maxbot's pos is <= maxbot's range.

part_1 = lambda input_data: (
            (
                sum(
                    1
                    for nanobot in input_data
                    if bot_distance(nanobot, maxbot) <= maxbot[3]
                )
                for maxbot in [
                    max(
                        input_data
                        ,
                        key = lambda nanobot: nanobot[3]
                    )
                ]
            ).next()
        )

########################################################################
#
# Part 2:
#
# Group the nanobots into sets of nanobots, where the nanobots within
# each set all intersect with every other nanobot in the set.
#
#     Do this with a reduction across the list of nanobots.
#     The state of the reduction is a list of lists of nanobots.
#     a nanobot and the set of other nanobots which are already known
#     to intersect with that nanobot.  The list starts out by adding
#     an empty set to each nanobot in the input data.  At each step of
#     the reduction, take the first nanobot+set out of the list and
#     example each remaining nanobot+set.  If the examined nanobot
#     contained within the examined nanobot's set, _and_ the first
#     set starts out empty.  At each step of the reduction, given one
#     nanobot and the set already accumulated for that nanobot,
#
# Filter this down to the largest set or sets.
#
# For each set, pick the smallest nanobot and find all points in that
# nanobot's range that are also in all other bot's ranges.
# 
# Choose the closest of all those points to (0,0,0).



# The first thing to do is to generate the set of the longest of all sets of nanobots which intersect with each other.
#
# For example, given a set of nanobots with these intersections:
#
#     * 1 intersects with 2 and 7
#     * 2 intersects with 1 and 6
#     * 3 intersects with 5 and 7
#     * 4 does not intersect
#     * 5 intersects with 3 and 7
#     * 6 intersects with 2
#     * 7 intersects with 1, 3 and 5
#
# The desired output is the list of the longest sets of nanobots which all intersect with each other.
#
# The complete list of sets of nanobots which all intersect with each other is:
#     * { 4 }
#     * { 1, 2 }
#     * { 1, 7 }
#     * { 2, 6 }
#     * { 3, 5, 7 }
# The desired output is then:
#     * { 3, 5, 7 }

# Start by generating the dictionary that maps each nanobot to the set of other nanobots which intersect with it.
# In the example above, this is:
# { 1: {2,7}, 2: {1,6}, 3: {5,7}, 4: {}, 5: {3,7}, 6: {2}, 7: {1,3,5} }
#
#     This is done by a dual loop through the bots.
#     The first loop loops through all the bots.
#     The second loop is filtered to include only bots which intersect with the bot from the first loop, but are not identical to it.
#     The second loop becomes the set of intersections for the first bot.
#
# The accumulation is a working list of partial intersection sets and an output list of complete intersection sets.
# Start the accumulation with the working list containing a set for each nanobot and an empty output set.
# [ {1}, {2}, {3}, {4}, {5}, {6}, {7} ], []
#
# Run the accumulation forever, but filter it through a `dropwhile` which drops any accumulation result in which the working list is not empty.  Only the first result from the `dropwhile` will be processed, and that will stop the accumulation from actually running forever.
#
# At each step of the accumulation, remove the first working set from the working list.
# Generate the list of all bots whose intersection set from the dictionary of intersections is equal to or a superset of the working set.
# For each bot in that list, add a new set to the working list consisting of the working set plus the bot, if that new set is not already in the working list.
# If no such superset is found, add the working set to the output list.
#
# For our example above, the initial state of the accumulation is:
# [ {1}, {2}, {3}, {4}, {5}, {6}, {7} ], []
#
# And the dictionary computed above is:
# { 1: {2,7}, 2: {1,6}, 3: {5,7}, 4: {}, 5: {3,7}, 6: {2}, 7: {1,3,5} }
#
# In the first step, set {1} is removed and the sets {1,2} and {1,7} are added:
# [ {2}, {3}, {4}, {5}, {6}, {7}, {1,2}, {1,7} ], []
#
# In the second step, set {2} is removed.  Set {1,2} is not added because it already exists, but set {2,6} is:
# [ {3}, {4}, {5}, {6}, {7}, {1,2}, {1,7}, {2,6} ], []
#
# The next 5 steps result in:
# [ {4}, {5}, {6}, {7}, {1,2}, {1,7}, {2,6}, {3,5}, {3,7} ], []
# [ {5}, {6}, {7}, {1,2}, {1,7}, {2,6}, {3,5}, {3,7} ], [ {4} ]
# [ {6}, {7}, {1,2}, {1,7}, {2,6}, {3,5}, {3,7}, {5,7} ], [ {4} ]
# [ {7}, {1,2}, {1,7}, {2,6}, {3,5}, {3,7}, {5,7} ], [ {4} ]
# [ {1,2}, {1,7}, {2,6}, {3,5}, {3,7}, {5,7} ], [ {4} ]
#
# Two things to note:
# * After processing set {4}, since that set is not a subset of any of the intersection values, it got added to the output.
# * After processing sets {6} and {7}, nothing was added to the working list because the discovered intersections were already there, but they were not added to the output because they _were_ found, even if it wasn't a unique intersection.
#
# Now things get interesting.  As a reminder, here is the dictionary of bots which overlap with another bot:
# { 1: {2,7}, 2: {1,6}, 3: {5,7}, 4: {}, 5: {3,7}, 6: {2}, 7: {1,3,5} }
#
# The next step is to remove {1,2} and check to see if that is a subset of any of the dictionary item sets.  It isn't, so it gets added to the output list:
# [ {1,7}, {2,6}, {3,5}, {3,7}, {5,7} ], [ {4}, {1,2} ]
#
# The same thing happens for {1,7} and {2,6}:
# [ {3,5}, {3,7}, {5,7} ], [ {4}, {1,2}, {1,7}, {2,6} ]
#
# However, {3,5} exists as a subset of bot 7, so that gets added back to the working list:
# [ {3,7}, {5,7}, {3,5,7} ], [ {4}, {1,2}, {1,7}, {2,6} ]
#
# {3,7} exists as a subset of bot 5.  Since {3,5,7} is already in the working list, nothing gets added to either list:
# [ {5,7}, {3,5,7} ], [ {4}, {1,2}, {1,7}, {2,6} ]
#
# Similarly, {5,7} exists as a subset of bot 3, but the resulting set is already in the working list:
# [ {3,5,7} ], [ {4}, {1,2}, {1,7}, {2,6} ]
#
# Finally, {3,5,7} is not a subset of any bot's intersection list, so add it to the output list:
# [], [ {4}, {1,2}, {1,7}, {2,6}, {3,5,7} ]
#
# With the working list empty, the accumulation stops, and the resulting list of all overlapping intersections is:
# [ {4}, {1,2}, {1,7}, {2,6}, {3,5,7} ]
#
# Because of the way this is built, the last set or sets in the output list are the longest, so filter the output
# list down to those sets with the same length as the last set:
# [ {3,5,7} ]
#
# This then gives us a pruned-down set of areas in which to find the intersections and calculate the closest to (0,0,0).
#
# Run `min` against a generator comprehension of coordinates, with a `min` key of the sum of the absolute values of the coordinate components.
#
# Generate each coordinate by examining the smallest bot within each intersection set,
# looping through all coordinates contained within that smallest bot,
# and filtering those coordinates to include only those which are within the radius of all bots in the intersection set.

generate_intersection_sets_v1 = lambda input_data: (
            # generator expression for binding values to names
            (

# ... filter it through a `dropwhile` which drops any accumulation result in which the working list is not empty.
                itertools.dropwhile(
                    lambda working_output: working_output[0]
                    ,

                    accumulate(
                        itertools.chain(

# Start the accumulation with the working list containing a set for each nanobot and an empty output set.
                            [
                                (
                                    list({bot} for bot in xrange(len(input_data)))
                                    ,
                                    list()
                                )
                            ]
                            ,

# Run the accumulation forever...
                            itertools.count(0)
                        )
                        ,

# At each step of the accumulation...

                        lambda working_output, _: (
                        # working_output is the tuple of (working_list, output_list)
                        # so working_output[0] is the working list
                        # and working_output[1] is the output list
                        # this is a generator expression to allow binding values to names

# For each bot in that list, add a new set to the working list consisting of the working set plus the bot, if that new set is not already in the working list.

                            (
                                working_output[0][1:]
                                + list(
                                    {bot} | working_set
                                    for bot in intersecting_bots
                                    if ({bot} | working_set) not in working_output[0][1:]
                                )
                                ,
                                working_output[1]
                            )
                            if intersecting_bots
                            else

# If no such superset is found, add the working set to the output list if the output list is empty or the last element in the outuptu list is the same length as the working set; otherwise, recreate the output list containing only the working set.

                            (
                                working_output[0][1:]
                                ,
                                (
                                    working_output[1]
                                    if not working_output[1]
                                    or len(working_set) == len(working_output[1][-1])
                                    else
                                    list()
                                ) + list([
                                    working_set
                                ])
                            )

# ... remove the first working set from the working list.

                            for working_set in [working_output[0][0]]

# Generate the list of all bots whose intersection set from the dictionary of intersections is equal to or a superset of the working set.

                            for intersecting_bots in [
                                [
                                    bot_item[0]
                                    for bot_item in intersects_with.iteritems()
                                    if bot_item[1] >= working_set
                                ]
                            ]

                        # this is a generator expression to allow binding values to names
                        ).next()
                    )

# Only the first result from the `dropwhile` will be processed, and that will stop the accumulation from actually running forever.
                ).next()[1]

# Start by generating the dictionary that maps each nanobot to the set of other nanobots which intersect with it.
#     This is done by a dual loop through the bots.

                for intersects_with in [
                    {

#     The second loop becomes the set of intersections for the first bot.

                        bot: set(
                            otherbot

#     The second loop is filtered to include only bots which intersect with the bot from the first loop, but are not identical to it.

                            for otherbot in xrange(len(input_data))
                            if bot != otherbot
                            and bot_distance(input_data[bot], input_data[otherbot]) <= input_data[bot][3] + input_data[otherbot][3]
                        )

#     The first loop loops through all the bots.

                        for bot in xrange(len(input_data))
                    }
                ]

            ).next()
        )

generate_intersection_sets = generate_intersection_sets_v1

part_2 = lambda input_data: (

            # generator expression to bind values to names
            (

# Run `min` against a generator comprehension of coordinates, with a `min` key of the sum of the absolute values of the coordinate components.
# Then return the sum of the returned coordinates.
#
# Generate each coordinate by examining the smallest bot within each intersection set,
# looping through all coordinates contained within that smallest bot,
# and filtering those coordinates to include only those which are within the radius of all bots in the intersection set.

                sum(
                    min(
                        (
                            coord
                            for intersection_set in largest_intersection_sets
                            for smallest_bot in [min(intersection_set, key=lambda bot:bot[3])]
                            for bot_size in [smallest_bot[3]]
                            for zz in xrange(- bot_size, 1 + bot_size)
                            for yy in xrange(- (bot_size - zz), 1 + (bot_size - zz))
                            for xx in xrange(- (bot_size - zz - yy), 1 + (bot_size - zz - yy))
                            for coord in [
                                (
                                    smallest_bot[0] + xx,
                                    smallest_bot[1] + yy,
                                    smallest_bot[2] + zz
                                )
                            ]
                            if min(
                                bot_distance(coord, bot) <= bot[3]
                                for bot in intersection_set
                            )
                        )
                        ,
                        key = lambda coord: sum(abs(c) for c in coord)
                    )
                )

                for intersection_sets in [generate_intersection_sets(input_data)]
                for largest_intersection_sets in [
                    [
                      intersection_set
                      for intersection_set in intersection_sets
                      if len(intersection_set) == len(intersection_sets[-1])
                    ]
                ]
            ).next()

if False else generate_intersection_sets(input_data)

); lambda: (
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
        if DEBUGGING: print >> sys.stderr, "\nprocessing {} with expected results {}".format(sample_filename, expected)
        result = part_1(process_input_data(sample_data))
        if DEBUGGING: result = '\n' + pprint.pformat(result) + '\n'
        t = time.time() - t
        print "{}: sample {}: part 1 = {}{}".format(t, sample_num, result, " (expected {})".format(expected) if result != expected else "")

    t = time.time()
    if DEBUGGING: print >> sys.stderr, "\nprocessing {}".format(sample_filename)
    result = part_1(process_input_data(input_data))
    if DEBUGGING: result = '\n' + pprint.pformat(result) + '\n'
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
        if DEBUGGING: print >> sys.stderr, "\nprocessing {} with expected results {}".format(sample_filename, expected)
        result = part_2(process_input_data(sample_data))
        if DEBUGGING: result = '\n' + pprint.pformat(result) + '\n'
        t = time.time() - t
        print "{}: sample {}: part 2 = {}{}".format(t, sample_num, result, " (expected {})".format(expected) if result != expected else "")

    t = time.time()
    if DEBUGGING: print >> sys.stderr, "\nprocessing {}".format(sample_filename)
    result = part_2(process_input_data(input_data))
    if DEBUGGING: result = '\n' + pprint.pformat(result) + '\n'
    t = time.time() - t
    print "{}: input data: part 2 = {}".format(t, result)

