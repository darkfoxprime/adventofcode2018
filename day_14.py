
import re
import sys
import itertools
import time
import operator

from blist import blist

DEBUGGING = False

if DEBUGGING:

    def reduce(func, iterable, initial=None):
        iterable = iter(iterable)
        if initial is None:
            initial = iterable.next()
        for value in iterable:
            print >> sys.stderr, ">>reduce<< state={!r} value={!r}".format(initial, value)
            initial = func(initial, value)
        print >> sys.stderr, ">>reduce<< final state={!r}".format(initial)
        return initial

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
        print >> sys.stderr, ">>accumulate<< initial state={!r}".format(total)
        yield total
        for element in it:
            print >> sys.stderr, ">>accumulate<< element={!r}".format(element)
            total = func(total, element)
            print >> sys.stderr, ">>accumulate<< state={!r}".format(total)
            yield total

else:

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

########################################################################
#
# Process input data to return the appropriate records or data format.
#
# For this puzzle, the input data is the number of recipes after which
# the 10-digit number will appear, plus the starting state: two recipes
# with scores `[3,7]` and the two elves starting positions at `0` and
# `1`.

process_input_data = lambda input_data: (
            (int(input_data), (blist([3,7]), 0, 1))
        )

########################################################################
#
# determine the new recipes to be added based on the current state.
# 
# Returns a list of one or two numbers, the scores of the new recipes
# added.
#
# If the two current recipes sum to less than 10, returns a list of a
# single number which is the sum of the two current recipes.
#
# Otherwise, returns a list of two numbers, the first of which is the
# sum of the two current recipes (integrally) divided by 10, and the
# second of which is the sum of the two recipes mod 10.

new_recipes = lambda recipes, pos1, pos2: (

# If the two current recipes sum to less than 10, returns a list of a
# single number which is the sum of the two current recipes.

            blist([ recipes[pos1] + recipes[pos2] ])
            if recipes[pos1] + recipes[pos2] < 10
            else

# Otherwise, returns a list of two numbers, the first of which is the
# sum of the two current recipes (integrally) divided by 10, and the
# second of which is the sum of the two recipes mod 10.

                blist([
                    (recipes[pos1] + recipes[pos2]) // 10 ,
                    (recipes[pos1] + recipes[pos2]) % 10
                ])
        )

########################################################################
#
# determine the next position for an elf based on the recipes list
# (including the new recipes added this time) and their current position.
#

next_position = lambda recipes, position: (
            (position + 1 + recipes[position]) % len(recipes)
        )

########################################################################
#
# Run one cooking cycle.
# 
# Generate a new recipes list from the current state.
# (including the new recipes added this time) and their current position.
#
# Accepts an extra parameter for use in the `accumulate` function.

next_cooking_cycle = lambda state, _: (
            # use the generator trick to store the new recipes
            (
                (
                    recipes,
                    next_position(recipes, state[1]),
                    next_position(recipes, state[2])
                )
                for recipes in [
                    state[0] + new_recipes(state[0], state[1], state[2])
                ]
            ).next()
        )

########################################################################
#
# Part 1:   Run `next_cooking_cycle` until the length of the recipes
#           list is at least `input_data` + 10 long.  Grab the 10 recipes
#           after `input_data`, convert them all to strings, then join
#           them together.

part_1 = lambda input_data: (
            ''.join(
                str(digit)
                for state in [
                    itertools.dropwhile(
                        lambda state: (
                            len(state[0]) < (input_data[0] + 10)
                        )
                        ,
                        accumulate(
                            itertools.chain(
                                input_data[1:2]
                                ,
                                itertools.count(1)
                            )
                            ,
                            next_cooking_cycle
                        )
                    ).next()
                ]
                for digit in state[0][input_data[0]:input_data[0]+10]
            )
        )

########################################################################
#
# Part 2:   Split `input_data` into a list of integers.
#           Run `next_cooking_cycle` until the `input_data` list appears
#           either at the end or 1 back from the end of the recipes list.
#           Return the number of recipes before the `input_data` list.

part_2 = lambda input_data: (
            # generator trick to bind values to names
            (

#           Return the number of recipes before the `input_data` list.

                len(state[0]) - len(input_data_list)
                if state[0][-len(input_data_list):] == input_data_list
                else
                    len(state[0]) - len(input_data_list) - 1

#           Split `input_data` into a list of integers.

                for input_data_list in [
                    blist(
                        int(digit)
                        for digit in str(input_data[0])
                    )
                ]
                for state in [

#                                ... until the `input_data` list appears
#           either at the end or 1 back from the end of the recipes list.

                    itertools.dropwhile(
                        lambda state: (
                            state[0][-len(input_data_list):] != input_data_list
                            and state[0][-len(input_data_list)-1:-1] != input_data_list
                        )
                        ,

#           Run `next_cooking_cycle` ...

                        accumulate(
                            itertools.chain(
                                input_data[1:2]
                                ,
                                itertools.count(1)
                            )
                            ,
                            next_cooking_cycle
                        )
                    ).next()
                ]
            ).next()
        )

########################################################################
#
# Main controller

if __name__ == '__main__':

    sample_data = process_input_data(open(__file__.rsplit('.')[0] + '.sample').read())

    t = time.time()
    result = part_1(sample_data)
    t = time.time() - t
    print "{}: sample data: part 1 = {}".format(t, result)

    sample_data = process_input_data(open(__file__.rsplit('.')[0] + '.sample.2').read())

    t = time.time()
    result = part_2(sample_data)
    t = time.time() - t
    print "{}: sample data: part 2 = {}".format(t, result)

    if DEBUGGING: sys.exit(0)

    input_data = process_input_data(open(__file__.rsplit('.')[0] + '.input').read())

    t = time.time()
    result = part_1(input_data)
    t = time.time() - t
    print "{}: input data: part 1 = {}".format(t, result)

    t = time.time()
    result = part_2(input_data)
    t = time.time() - t
    print "{}: input data: part 2 = {}".format(t, result)

