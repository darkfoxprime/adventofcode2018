
import re
import sys
import itertools
import time
import operator

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
# For this puzzle, the input data will be a 4-item tuple:
#     `(tracks, carts, next_turns, width, height)`
# - `tracks` holds the tracks of the puzzle as a single string (with the
#   first `width` characters holding the first row of the puzzle, etc).
#   Any place in the original puzzle input which held a cart is replaced
#   by the track that underlies it.
# - `carts` holds the carts from the puzzle in a string the same size as
#   `tracks`.  Each location of the original puzzle that has a cart will
#   have a track in `tracks` and a cart direction (^/v/>/<) in `carts`;
#   all other locations will have the original puzzle content in `tracks`
#   and a space in `carts`.
# - `next_turns` holds the next turn direction for each cart in `carts`,
#   with each cart starting out with a next turn of `1`.  Any location in
#   `carts` which does not hold a cart will have a space in `next_turns`.
# - `width` and `height` are the number of columns and number of rows,
#   respectively, in the input data.

process_input_data = lambda input_data: (
            input_data
                .replace('\n', '')
                .replace('<', '-')
                .replace('>', '-')
                .replace('^', '|')
                .replace('v', '|')
            ,
            input_data
                .replace('\n', '')
                .replace('-', ' ')
                .replace('|', ' ')
                .replace('+', ' ')
                .replace('\\', ' ')
                .replace('/', ' ')
            ,
            input_data
                .replace('\n', '')
                .replace('-', ' ')
                .replace('|', ' ')
                .replace('+', ' ')
                .replace('\\', ' ')
                .replace('/', ' ')
                .replace('<', '1')
                .replace('>', '1')
                .replace('^', '1')
                .replace('v', '1')
            ,
            len(input_data.split('\n')[0]),
            len(input_data.split('\n'))
        )

########################################################################
#
# Iterate the carts through one tick.
#
# Do this by looping through the length of the carts/tracks strings,
# processing each cart found (where `carts[index] in '<>^v'`).
#
# Use the generator trick to assign a dictionary to `directions` with
# the following key-value pairs:
# ```
#     {
#         '<': (    -1, 'v', '<', '^'),
#         '>': (     1, '^', '>', 'v'),
#         '^': (-width, '<', '^', '>'),
#         'v': ( width, '>', 'v', '<'),
#         collision_marker: (0,)
#         '\\': { '^': '<', 'v': '>', '>': 'v', '<': '^' },
#         '/':  { '^': '>', 'v': '<', '>': '^', '<': 'v' },
#     }
# ```
# Each cart direction contains the `(offset, left, straight, right)`
# tuple for that direction: the `offset` to add to the current index
# for the cart's next location, and the cart direction if it turns left,
# straight, or right.
# The collision marker (`X` by default) is represented by a 0 offset -
# the cart doesn't # move.
# In addition, the _track_ symbols `/` and `\\` are represented with a
# mapping of current direction to new direction,
#
# Acucmulate over each index which holds a cart:
#
#     use the generator trick to assign `cart` to `carts[index]`,
#     `next_turn` to `next_turns[index]`,
#     `cart_turn` to `directions[cart]`,
#     and `next_index` to `index + cart_turn[0]`.
#
#     Use the generator trick to assign `new_cart` and `new_next_turn`
#     based on `carts[next_index]` and `tracks[next_index]`:
#         If `cart` is the collision marker _or_ `carts[next_index]` is not a space:
#             `new_cart` is the collision marker and
#             `new_next_turn` is ` `.
#         Else if `tracks[next_index]` is a `+`:
#             `new_cart` is `cart_turn[int(next_turn)]` and
#             `new_next_turn` is `str(int(next_turn) % 3 + 1)`.
#         Else if it's in `directions:
#             `new_cart` is `directions[tracks[next_index]][cart]` and
#             `new_next_turn` is `next_turn`.
#         Otherwise (the cart isn't turning):
#             `new_cart` is `cart` and `new_next_turn` is `next_turn`.
#
#     If `next_index` is the same as `index`, return the current state
#     unchanged.
#     Otherwise, return the `carts` string with `carts[next_index]`
#     replaced by `new_cart` and `carts[index]` replaced by a space, and
#     return the `next_turns` string with `next_turns[next_index]`
#     replaced by `new_next_turn` and `next_turns[index] replaced by a
#     space.
#     (This is slightly complicated by having to do two different
#     replacement expressions based on if `next_index` comes before
#     or after `index`)

cart_tick = lambda current_state, collision_marker = 'X': (
            # use generator trick to bind `directions`
            # for the scope of the rest of the function
            (

# Acucmulate over each index which holds a cart:

                reduce(

                    lambda current_state, index: (
                        # use generator trick to bind values to names
                        # for the scope of the expression
                        (

#     If `next_index` is the same as `index`, return the current state
#     unchanged.

                            (tracks, carts, next_turns, width, height)
                            if next_index == index
                            else

#     Otherwise, return the `carts` string with `carts[next_index]`
#     replaced by `new_cart` and `carts[index]` replaced by a space, and
#     return the `next_turns` string with `next_turns[next_index]`
#     replaced by `new_next_turn` and `next_turns[index] replaced by a
#     space.
#     (This is slightly complicated by having to do two different
#     replacement expressions based on if `next_index` comes before
#     or after `index`)

                                (
                                    tracks,
                                    (
                                        carts[:next_index]
                                        + new_cart
                                        + carts[next_index + 1:index]
                                        + ' '
                                        + carts[index + 1:]
                                    )
                                    if next_index < index
                                    else (
                                        carts[:index]
                                        + ' '
                                        + carts[index + 1:next_index]
                                        + new_cart
                                        + carts[next_index + 1:]
                                    )
                                    ,
                                    (
                                        next_turns[:next_index]
                                        + new_next_turn
                                        + next_turns[next_index + 1:index]
                                        + ' '
                                        + next_turns[index + 1:]
                                    )
                                    if next_index < index
                                    else (
                                        next_turns[:index]
                                        + ' '
                                        + next_turns[index + 1:next_index]
                                        + new_next_turn
                                        + next_turns[next_index + 1:]
                                    )
                                    ,
                                    width,
                                    height
                                )

#     use the generator trick to assign `cart` to `carts[index]`,
#     `next_turn` to `next_turns[index]`,
#     `cart_turn` to `directions[cart]`,
#     and `next_index` to `index + cart_turn[0]`.

                            for (tracks, carts, next_turns, width, height) in [current_state]
                            for cart in [carts[index]]
                            for next_turn in [next_turns[index]]
                            for cart_turn in [directions[cart]]
                            for next_index in [index + cart_turn[0]]

#     Use the generator trick to assign `new_cart` and `new_next_turn`
#     based on `carts[next_index]` and `tracks[next_index]`:
#         If `cart` is the collision marker _or_ `carts[next_index]` is not a space:
#             `new_cart` is the collision marker and
#             `new_next_turn` is ` `.
#         Else if `tracks[next_index]` is a `+`:
#             `new_cart` is `cart_turn[int(next_turn)]` and
#             `new_next_turn` is `str(int(next_turn) % 3 + 1)`.
#         Else if it's in `directions:
#             `new_cart` is `directions[tracks[next_index]][cart]` and
#             `new_next_turn` is `next_turn`.
#         Otherwise (the cart isn't turning):
#             `new_cart` is `cart` and `new_next_turn` is `next_turn`.

                            for new_cart in [
                                collision_marker
                                if cart == collision_marker or carts[next_index] != ' '
                                else
                                    cart_turn[int(next_turn)]
                                    if tracks[next_index] == '+'
                                    else
                                        directions[tracks[next_index]][cart]
                                        if tracks[next_index] in directions
                                        else
                                            cart
                            ]
                            for new_next_turn in [
                                ' '
                                if cart == collision_marker or carts[next_index] != ' '
                                else
                                    str(int(next_turn) % 3 + 1)
                                    if tracks[next_index] == '+'
                                    else
                                        next_turn
                            ]

                        ).next()
                    )

                    ,

                    itertools.chain(
                        (current_state,),
                        itertools.ifilter(
                            lambda index: (
                                current_state[1][index] in '<>^v'
                            )
                            ,
                            xrange(len(current_state[0]))
                        )
                    )

                )

# Use the generator trick to assign a dictionary to `directions` with
# the following key-value pairs:

                for directions in [
                    {
                        '<': (               -1, 'v', '<', '^'),
                        '>': (                1, '^', '>', 'v'),
                        '^': (-current_state[3], '<', '^', '>'),
                        'v': ( current_state[3], '>', 'v', '<'),
                        collision_marker: (0,),
                        '\\': { '^': '<', 'v': '>', '>': 'v', '<': '^' },
                        '/':  { '^': '>', 'v': '<', '>': '^', '<': 'v' },
                    }
                ]

            ).next()
        )

########################################################################
#
# Part 1:   Run `cart_tick` until a collision occurs, and report the
#           location of the collision.

part_1 = lambda input_data: (
            (
                (collision % width, collision // width)
                for (tracks, carts, next_turns, width, height) in [
                    itertools.dropwhile(
                        lambda current_state: (
                            'X' not in current_state[1]
                        )
                        ,
                        accumulate(
                            itertools.chain(
                                (input_data,)
                                ,
                                itertools.count(1)
                            )
                            ,
                            lambda current_state, tick_number: (
                                cart_tick(current_state)
                            )
                        )
                    ).next()
                ]
                for collision in [
                    carts.index('X')
                ]
            ).next()
        )

########################################################################
#
# Part 2:   Run `cart_tick` until only one cart remains, and return the
#           location of that cart.

part_2 = lambda input_data: (
            (
                (cart_location % width, cart_location // width)
                for (tracks, carts, next_turns, width, height) in [
                    itertools.dropwhile(
                        lambda current_state: (
                            len(current_state[1].strip()) > 1
                        )
                        ,
                        accumulate(
                            itertools.chain(
                                (input_data,)
                                ,
                                itertools.count(1)
                            )
                            ,
                            lambda current_state, tick_number: (
                                cart_tick(current_state, collision_marker = ' ')
                            )
                        )
                    ).next()
                ]
                for cart_location in [
                    len(carts.rstrip()) - 1
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

