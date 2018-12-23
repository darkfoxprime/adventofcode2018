
import re
import sys
import itertools
import time
import operator
import os.path
import pprint

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

def debug_value(header, value):
    print >> sys.stderr, header, value
    return value

if not DEBUGGING:
    debug_value = lambda header, value: value

########################################################################
#
# Process input data to return the appropriate records or data format.
#
# Return a tuple of (depth,width,height) based on the input.
#
# The width and height are both *one greater* than the target
# coordinates.

process_input_data = lambda input_data: (
            tuple(
                int(x)
                for x in re.split(r'([0-9]+)', input_data)[1::2]
            )
        )

########################################################################
#
# Generate an erosion level map based on the input
#
# the erosion level map is a single dimension array width*height in length
#
# generate the map with a reduction
#
# the initial state is an empty list (or blist if needed)
#
# the reduction runs over (x,y,index) tuples with y ranging 0 ->
# (height-1),
#
# At each step, calculate the erosion level and append it to the map
# being built.
#
#     if index == 0 or index == width*height-1
#
#         the geological index is 0
#     
#     if y == 0
#
#         the geological index is x * 16807
#
#     if x == 0
#
#         the geological index is y * 48271
#     
#     otherwise
#
#         the geological index is the erosion level at index `(index-1)`
#         times the erosion level at index `(index-width)`
#
#     take the geological index , add the depth, then modulo the
#     result by 20183 and record that as the erosion level for this index.

generate_erosion_map = lambda cave_depth, map_width, map_height, target_x, target_y: (

# generate the map with a reduction

            reduce(

# At each step, calculate the erosion level and append it to the map
# being built.

                lambda erosion_map, map_index: (

#                 ... and record that as the erosion level for this index.

                    erosion_map + list([
                        ((

#     if index == 0 or index == (target_y*map_width+target_x)
#
#         the geological index is 0

                            0
                            if map_index[2] == 0
                            or map_index[2] == (
                                target_y * map_width
                                + target_x
                            )
                            else

#     if y == 0
#
#         the geological index is x * 16807

                            map_index[0] * 16807
                            if map_index[1] == 0
                            else

#     if x == 0
#
#         the geological index is y * 48271

                            map_index[1] * 48271
                            if map_index[0] == 0
                            else

#     otherwise
#
#         the geological index is the erosion level at index `(index-1)`
#         times the erosion level at index `(index-width)`

                            erosion_map[map_index[2]-1]
                            * erosion_map[map_index[2]-map_width]

#     take the geological index , add the depth, then modulo the
#     result by 20183 and ...

                        ) + cave_depth) % 20183
                    ])

                )
                ,

# the reduction runs over (x,y,index) tuples with y ranging 0 ->
# (height-1),

                (
                    (x, y, y*map_width+x)
                    for y in range(map_height)
                    for x in range(map_width)
                )
                ,

# the initial state is an empty list (or blist if needed)

                list()

            )
        )

########################################################################
#
# Transform an erosion level map into a terrain type map
#
# This is a trivial generator comprehension

generate_terrain_map = lambda erosion_map: (
            erosion_level % 3
            for erosion_level in erosion_map
        )

########################################################################
#
# Render a terrain map

render = lambda input_data, terrain_map: (
            '\n' + '\n'.join(
                re.split(
                    '(' + '.'*input_data[1] + ')'
                    ,
                    ''.join(
                        '.=|'[terrain_type]
                        for terrain_type in terrain_map
                    )
                )[1::2]
            ) + '\n'
        )

########################################################################
#
# Part 1:   Return the sum of the terrain types (which is also the risk
# levels).

part_1 = lambda input_data: (
#input_data); lambda: (
#render(input_data, generate_terrain_map(generate_erosion_map(input_data[0], input_data[1]+1, input_data[2]+1, input_data[1], input_data[2])))); lambda: (
            sum(generate_terrain_map(generate_erosion_map(
                input_data[0]   # cave_depth
                ,
                input_data[1]+1 # map width
                ,
                input_data[1]+2 # map height
                ,
                input_data[1]   # target x
                ,
                input_data[2]   # target y
            )))
        )

########################################################################
#
# Part 2:   Find the shortest weighted path from (0,0) to target (x,y)
#
# The weight for moving is based on the location being moved from and
# the location being moved to.
#
# This requires a larger map, as we may need to go beyond the target
# and come back to it.
# I'll need to make an assumption about how large, since I need to
# pre-generate the map.  For now, I'll assume a double-sized map is fine.
#
# To make the tools work, the terrain types will be modified to be 2**terrain -
# in other words, rock (terrain 0) becomes 1, wet (terrain 1) becomes 2, and
# narrow (terrain 2) becomes 4.
#
# The general procedure will be to process an ever-expanding "wave-front"
# of paths.  Each path is recorded as the end of the path, the total weight of the path so far, and the
# current tool equipped.  The end of the path is the (x,y) location and the
# next direction to move along the path.  The total weight of the
# path is the weight _just before_ moving in the direction recorded,
# but including any required tool change for that movement.
#
# At each iteration of the path finding, pick the path on the wavefront
# with the least weight and follow the movement recorded on that path.
# If the movement takes us to the target index, record that last 
# location with a delta of 0 and the final path weight.
#
# Otherwise, add the new location to the wavefront up to four different
# times, one for each direction of movement, as long as the movement
# wouldn't push the path off the map or to someplace that's already been
# seen.  For each direction, check if the current tool is compatible with
# the new location: if not, record the new tool which is compatible with
# both the current and new location and add 8 to the weight of the path
# (to account for both the tool change and the movement); otherwise,
# record the same tool and add 1 to the weight of the path for the
# movement itself.
#
# In addition to the wavefront, the procedure keeps track of a set of visited indices.
# Each time we iterate a wavefront path location, we add the location its
# movement points to into the set of visited indices.  This allows the checks
# above to ensure we're not moving onto a previously-visited index.
#
# In the implementation, a path location is recorded as a map index plus a delta.
# The only time the delta will be zero is for the initial path leading to the
# starting point, or the final path after the target has been reached.
#
# A tool is recorded as the sum of the terrain types in which it works.
# Tool "torch" is 5 (rocky + narrow).
# Tool "climbing gear" is 3 (rocky + wet).
# Tool "neither" is 6 (wet + narrow).
#
# The wavefront is recorded as a list of tuples of
# `( index, delta, tool, weight )`
#
# The initial wavefront is a list of the single tuple `( 0, 0, 5, -1 )`
# (the weight of `-1` is to account for the initial movement onto the
# starting point, which has a weight of 0).
#
# The actual procedure is an accumulator that generates wavefronts,
# filtered through a dropwhile that drops wavefronts until one includes
# the target location, and returning the weight of the path that ends
# at the target location from that "until" wavefront.
#
# The dropwhile filters on the `min` value of checking each index of
# each path end in the wavefront to be not equal to the index of the
# target location.  `min` means the resulting value will be `False`
# if any intermediate value is `False`.
#     ```
#     min(path_end[0] != target_index for path_end in wavefront)
#     ```
#
# The return value is the `next()` value from the dropwhile, run
# through a generator comprehension to generate the weight of all
# paths whose index is equal to the target index, then return the
# `next()` value from the generator.
#     ```
#     (
#         path_end[3]
#         for path_end in wavefront # dropwhile(...).next()
#         if path_end[0] == target_index
#     ).next()
#     ```
#
# The accumulator's initial iterator is a chain of...
#     A list of a tuple containing the initial wavefront list and
#     a set initialized with the value `0`:
#     ```
#     [ ( [ (0, 0, 5, -1) ], set() ) ]
#     ```
#     followed by an infinite counter.
#
#     The initial wavefront list has one path element containing
#     index 0, delta 0, tool 5 (the torch), and the initial weight -1
#     (to account for the movement to the starting point).
#     The initial set is empty.
#
# Each step of the accumulator:
#
#     Bind the wavefront, sorted by path weight, to a name `wavefront_sorted`,
#     the first element of the sorted wavefront to `location`, and location's
#     index plus location's delta to `next_index`.
#
#     The new wavefront to return consists of the sorted wavefront without
#     its first element (`wavefront_sorted[1:]`) plus the expansion to
#     the next node and the possible movements from that node.
#
#          If `next_index` is in the `seen` set,
#          don't add anything new, return the stripped wavefront.
#
#          If `next_index` is the target index, add the target index
#          to the wavefront with delta 0, the (hopefully correct) tool,
#          and a weight of `location`'s weight + 1.
#
#          Otherwise, add a new wavefront location for each `new_delta`
#          of `+1`, `-1`, `+map_width`, `-map_width` that meets the
#          following conditions:
#
#          *   `next_index` plus the new delta is not in the `seen` map.
#          *   `next_index` plus the new delta is >= 0, <= the length
#              of the terrain map, and either of the following are true:
#              ```
#              (((next_index + new_delta) % map_width)
#              == (next_index % map_width))
#              ``` or ```
#              (((next_index + new_delta) // map_width)
#              == (next_index // map_width))
#              ```
#          *   either `next_index` plus the new delta is not the target
#              index, _or_ the terrain type at `next_index` is compatible
#              with a torch (`terrain_map[net_index] & 5 > 0`).
#          *   These conditions are to ensure that we don't go outside
#              the bounds of the known terrain map, and that we can
#              approach the target with a torch.
#
#          For each such location:
#
#          If `next_index + new_delta` is the target index, and the
#          current tool is not a torch _or_ the bitwise `and` of the
#          `location`'s tool and the terrain type at `next_index +
#          new_delta` is zero...
#
#          ... add a new wavefront location with `next_index`, a delta of
#          `new_delta`, a new tool (as described next), and a new weight
#          equal to `location`'s weight plus 8 (1 for the movement to
#          `next_index` and 7 for the tool change).  The new tool is
#          either a torch, tool value 5 (if `next_index + new_delta`
#          is the target index), or the one tool that is compatible
#          between the current location and the new location - the tool
#          value that is equal to the sum of the two terrain types.
#
#          Otherwise...
#
#          ... add a new wavefront location with `next_index`, a delta of
#          `new_delta`, `location`'s tool, and `location`'s weight plus 1
#
#          Finally, add `next_index` to the set of visisted locations.

# Each step of the accumulator:

process_next_path = lambda wavefront_seen, target_index, map_width, terrain_map: (
            # generator expression to allow binding values to names
            (

#     The new wavefront to return consists of the sorted wavefront without
#     its first element (`wavefront_sorted[1:]`) plus the expansion to
#     the next node and the possible movements from that node.

                (
                    wavefront_sorted[1:]
                    + (

### DEBUGGING START ###
(
    [debug_value('at edge! x,y=', (next_index%map_width, next_index//map_width))][:0]
    if (next_index >= len(terrain_map)-map_width)
    or (next_index%map_width == map_width-1)
    else []
) + (
### DEBUGGING END ###

#          If `next_index` is in the `seen` set,
#          don't add anything new, return the stripped wavefront.

                        []
                        if next_index in wavefront_seen[1]

#          If `next_index` is the target index, add the target index
#          to the wavefront with delta 0, the (hopefully correct) tool,
#          and a weight of `location`'s weight + 1.

                        else
                        [

                            (
                                target_index
                                ,
                                0
                                ,
                                location[2]
                                ,
                                1 + location[3]
                            )
                        ]
                        if next_index == target_index

                        else
                        [

#          For each such location:

                            (

#          ... add a new wavefront location with `next_index`, a delta of
#          `new_delta`, a new tool (as described next), and a new weight
#          equal to `location`'s weight plus 8 (1 for the movement to
#          `next_index` and 7 for the tool change).  The new tool is
#          either a torch, tool value 5 (if `next_index + new_delta`
#          is the target index), or the one tool that is compatible
#          between the current location and the new location - the tool
#          value that is equal to the sum of the two terrain types.

                                next_index
                                ,
                                new_delta
                                ,
                                (
                                    5
                                    if next_next_index == target_index
                                    else
                                    (
                                        terrain_map[next_index]
                                        + terrain_map[next_next_index]
                                    )
                                )
                                ,
                                8 + location[3]
                            )

#          If `next_index + new_delta` is the target index, and the
#          current tool is not a torch _or_ the bitwise `and` of the
#          `location`'s tool and the terrain type at `next_index +
#          new_delta` is zero,

                            if (
                                next_next_index == target_index
                                and location[2] != 5
                            ) or (
                                (
                                    location[2] & terrain_map[next_next_index]
                                ) == 0
                            )

#          Otherwise...

                            else

#          ... add a new wavefront location with `next_index`, a delta of
#          `new_delta`, `location`'s tool, and `location`'s weight plus 1

                            (
                                next_index
                                ,
                                new_delta
                                ,
                                location[2]
                                ,
                                1 + location[3]
                            )

#          Otherwise, add a new wavefront location for each `new_delta`
#          of `+1`, `-1`, `+map_width`, `-map_width` ...

                            for new_delta in (+1, -1, +map_width, -map_width)
                            for next_next_index in [next_index + new_delta]

#          ... that meets the following conditions:
#
#          *   `next_index` plus the new delta is not in the `seen` map.
#          *   `next_index` plus the new delta is >= 0, <= the length
#              of the terrain map, and either of the following are true:
#              ```
#              (((next_index + new_delta) % map_width)
#              == (next_index % map_width))
#              ``` or ```
#              (((next_index + new_delta) // map_width)
#              == (next_index // map_width))
#              ```
#          *   either `next_index` plus the new delta is not the target
#              index, _or_ the terrain type at `next_index` is compatible
#              with a torch (`terrain_map[net_index] & 5 > 0`).
#          *   These conditions are to ensure that we don't go outside
#              the bounds of the known terrain map, and that we can
#              approach the target with a torch.

                            if next_next_index not in wavefront_seen[1]
                            and next_next_index >= 0
                            and next_next_index <= len(terrain_map)
                            and (
                                (
                                    (next_next_index % map_width)
                                    == (next_index % map_width)
                                )
                                or
                                (
                                    (next_next_index // map_width)
                                    == (next_index // map_width)
                                )
                            )
                            and (
                                (next_next_index != target_index)
                                or
                                (terrain_map[next_index] & 5 > 0)
                            )

                        ]

### DEBUGGING START ###
)
### DEBUGGING END ###

                    )

#          Finally, add `next_index` to the set of visisted locations.

                    ,
                    wavefront_seen[1] | set([next_index])
                )

#     Bind the wavefront, sorted by path weight, to a name `wavefront_sorted`,
#     the first element of the sorted wavefront to `location`, and location's
#     index plus location's delta to `next_index`.

                for wavefront_sorted in [
                    sorted(
                        wavefront_seen[0], 
                        key = lambda path:path[3]
                    )
                ]
                for location in [wavefront_sorted[0]]
                for next_index in [location[0] + location[1]]

            ).next()

        )

part_2 = lambda input_data: (
            # generator expression to bind values to names
            (

# The return value is the `next()` value from the dropwhile, run
# through a generator comprehension to generate the weight of all
# paths whose index is equal to the target index, then return the
# `next()` value from the generator.
#
# Because the last item added to the wavefront will always be at
# the target index (based on the original input data), I can use
# that to directly find the path weight.

                final_wavefront[0][-1][3]

# This requires a larger map, as we may need to go beyond the target
# and come back to it.
# I'll need to make an assumption about how large, since I need to
# pre-generate the map.  For now, I'll assume a square map with each
# side equal to twice the largest coordinate component of the target
# coordinate.

                # double the map size of the input data
                for cave_depth in [input_data[0]]
                for map_width in [max(input_data[1:3])*2]
                for map_height in [map_width]
                for target_index in [
                    input_data[2] * map_width
                    + input_data[1]
                ]

# To make the tools work, the terrain types will be modified to be 2**terrain -
# in other words, rock (terrain 0) becomes 1, wet (terrain 1) becomes 2, and
# narrow (terrain 2) becomes 4.

                for terrain_map in [
                    list(
                        2**terrain
                        for terrain in (
                            generate_terrain_map(
                                generate_erosion_map(
                                    cave_depth
                                    ,
                                    map_width
                                    ,
                                    map_height
                                    ,
                                    input_data[1] # target x
                                    ,
                                    input_data[2] # target y
                                )
                            )
                        )
                    )
                ]

                for final_wavefront in [
#debug_value('final_wavefront',

# The dropwhile filters on the `min` value of checking each index of
# each path end in the wavefront to be not equal to the index of the
# target location.  `min` means the resulting value will be `False`
# if any intermediate value is `False`.

                    itertools.dropwhile(
                        lambda wavefront: (
                            min(
                                path_end[0] != target_index
                                for path_end in wavefront[0]
                            )
                        )
                        ,

# The actual procedure is an accumulator that generates wavefronts...

                        accumulate(

# The accumulator's initial iterator is a chain of...
#     A list of a tuple containing the initial wavefront list and
#     a set initialized with the value `0`:
#     ```
#     [ ( [ (0, 0, 5, -1) ], set() ) ]
#     ```
#     followed by an infinite counter.
#
#     The initial wavefront list has one path element containing
#     index 0, delta 0, tool 5 (the torch), and the initial weight -1
#     (to account for the movement to the starting point).
#     The initial set is empty.

                            itertools.chain(
                                [ ( list([ (0,0,5,-1) ]), set() ) ]
                                ,
                                itertools.count(0)
                            )
                            ,

# Call the `process_next_path` function for each step of the accumulator.

                            lambda wavefront_seen, _: (
                                process_next_path(
                                    wavefront_seen,
                                    target_index,
                                    map_width,
                                    terrain_map
                                )
                            )

                        )

                    ).next()

#)
                ]

#for debugging_target_wavefront in [debug_value('\nwavefront target is', final_wavefront[0][-1])]

            ).next()

        )

########################################################################
#
# Main controller

DEBUGGING = False

if __name__ == '__main__':

    base_filename = __file__.rsplit('.')[0]

    input_filename = '{}.input'.format(base_filename)
    input_data = open(input_filename).read()

#-#     for sample_num in itertools.takewhile(lambda num:os.path.exists('{}.sample.{}'.format(base_filename, num)), itertools.count(1)):
#-# 
#-#         sample_filename = '{}.sample.{}'.format(base_filename, sample_num)
#-#         sample_data = open(sample_filename).read()
#-# 
#-#         results_filename = '{}.sample.results.part1.{}'.format(base_filename, sample_num)
#-#         expected = (
#-#                     int(open(results_filename).read().strip())
#-#                     if os.path.exists(results_filename)
#-#                     else None
#-#                 )
#-# 
#-#         t = time.time()
#-#         if DEBUGGING: print >> sys.stderr, "\nprocessing {} with expected results {}".format(sample_filename, expected)
#-#         result = part_1(process_input_data(sample_data))
#-#         if DEBUGGING: result = '\n' + pprint.pformat(result) + '\n'
#-#         t = time.time() - t
#-#         print "{}: sample {}: part 1 = {}{}".format(t, sample_num, result, " (expected {})".format(expected) if result != expected else "")
#-# 
#-#     if DEBUGGING: sys.exit(0)
#-# 
#-#     t = time.time()
#-#     if DEBUGGING: print >> sys.stderr, "\nprocessing {}".format(sample_filename)
#-#     result = part_1(process_input_data(input_data))
#-#     if DEBUGGING: result = '\n' + pprint.pformat(result) + '\n'
#-#     t = time.time() - t
#-#     print "{}: input data: part 1 = {}".format(t, result)

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

    if DEBUGGING: sys.exit(0)

    t = time.time()
    if DEBUGGING: print >> sys.stderr, "\nprocessing {}".format(sample_filename)
    result = part_2(process_input_data(input_data))
    if DEBUGGING: result = '\n' + pprint.pformat(result) + '\n'
    t = time.time() - t
    print "{}: input data: part 2 = {}".format(t, result)

