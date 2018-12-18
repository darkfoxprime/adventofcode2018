
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
#
# The input data is a map.
# Return the map as a list of the individual characters without newlines,
# plus the width of the one of the original lines of the map.

process_input_data = lambda input_data: (
            list(input_data.replace('\n', ''))
            ,
            input_data.index('\n')
        )

########################################################################
#
# Render the map.

render = lambda map_data: (
            '\n'.join(
                ''.join(map_data[0][i:i+map_data[1]])
                for i in range(0, len(map_data[0]), map_data[1])
            )
        )

########################################################################
#
# Process one generation of the map.
#
# This is a list comprehension across the range of indices of the map.
#
# At each step of the list comprehension:
#
#     Generate a value for the neighbors of the space.
#
#     The neighbors value is represented as an _integer_ value of:
#         number of neighboring lumberyards * 100
#         + number of neighboring trees * 10
#         + number of neighboring open spaces
#
#     If the current space is '.' and the number of neighboring trees
#     is >= 3, add '|' to the list; otherwise, add '.'.
#
#     If the current space is '|' and the number of neighboring yards
#     is >= 3, add '#' to the list; otherwise, add '|'.
#
#     Otherwise, the current space is '#'.  If the number of neighboring
#     yards is >= 1 and the number of neighboring trees is >= 1, add
#     '#' to the list; otherwise, add '.'

next_generation = lambda map_data: (

            [

                (
                    (
                        '|'
                        if neighbors%100 >= 30
                        else
                        '.'
                    )
                    if space == '.'
                    else
                    (
                        '#'
                        if neighbors%1000 >= 300
                        else
                        '|'
                    )
                    if space == '|'
                    else
                    (
                        '#'
                        if neighbors%1000 >= 100
                        and neighbors%100 >= 10
                        else
                        '.'
                    )
                )

                for map in [map_data[0]]
                for map_width in [map_data[1]]
                for map_height in [len(map)//map_width]

                for coord in [
                    (index//map_width, index%map_width)
                    for index in range(len(map))
                ]

                for space in [
                    map[coord[0] * map_width + coord[1]]
                ]

                for neighbors in [

                    sum(
                        { '.': 1, '|': 10, '#': 100 }
                        [
                            map[
                                (coord[0]+delta_y)
                                * map_width
                                + coord[1]
                                + delta_x
                            ]
                        ]
                        for delta_y in (-1,0,1)
                        if 0 
                            <= coord[0] + delta_y
                            < map_height
                        for delta_x in (-1,0,1)
                        if 0
                            <= coord[1] + delta_x
                            < map_width
                        and (
                            delta_x != 0
                            or delta_y != 0
                        )
                    )
                ]

            ]

        )

########################################################################
#
# Part 1:
#
# Run 10 generations of the input data.  This is a reduction:
#
#     The initial state is the input data.
#
#     The reduction runs 10 times.
#
#     Each step of the reduction, return the next generation of the map.
#
# After 10 generations, return the product of the number of trees ('|')
# and lumberyards ('#').

part_1 = lambda input_data: (
            # use a generator expression to bind values to names
            (
                (
                    sum(1 for tree in final_data[0] if tree == '|')
                    * sum(1 for yard in final_data[0] if yard == '#')
                )
                for final_data in [
                    reduce(
                        lambda prev_gen, _: (
                            (
                                next_generation(prev_gen)
                                ,
                                input_data[1]
                            )
                        )
                        ,
                        xrange(10)
                        ,
                        input_data
                    )
                ]
            ).next()
        )

########################################################################
#
# Part 2:
#
# Same as part 1, except iterating as much as 1000000000 generations
# (but hopefully much less than that!)
#
# As we generate each new generation, record the previous generation in
# a list.
# Stop the iterations when the new generation exists in the list.
# At that point, we can determine what generation #1000000000 will look
# like, based on the index of the where the new generation was found in
# the list.
#
# gen N = gen (index + (N - index) % (num-generations - index))

part_2 = lambda input_data: (
            # use a generator expression to bind values to names
            (
                (
                    sum(1 for tree in last_gen if tree == '|')
                    * sum(1 for yard in last_gen if yard == '#')
                )
                for final_state in [
                    itertools.dropwhile(lambda state:state[0] not in state[2],
                    accumulate(
                        itertools.chain(
                            [input_data + ([],)]
                            ,
                            xrange(1000000000)
                        )
                        ,
                        lambda prev_gen, gen: (
                            (
                                next_gen
                                ,
                                input_data[1]
                                ,
                                prev_gen[2] + [prev_gen[0]]
                            )
                            for next_gen in [next_generation(prev_gen)]
                        ).next()
                    )).next()
                ]
                for found_index in [
                    final_state[2].index(final_state[0])
                ]
                for last_gen in [
                    final_state[2][
                        found_index
                        + (
                            (1000000000 - found_index)
                            % (len(final_state[2]) - found_index)
                        )
                    ]
                ]
            ).next()
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

