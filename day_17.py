
import re
import sys
import itertools
import time
import operator
import os.path
import collections

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
            return func(state, value)
        for value in real_accumulate(iterable, debug):
            print >> sys.stderr, ">>accumulate<< yield state={!r}".format(value)
            yield value
        print >> sys.stderr, ">>accumulate<< done".format(value)

########################################################################
#
# Parse the input data and return a list of horizontal veins.
#
# As usual, do this with a reduction, list comprehension, and a regex.
#
# The regex will capture horizontal and vertical veins in the same
# groups, with the first group indicating whether it's a horizontal
# vein (`y`) or vertical vein (`x`).
# ```
# r'([xy])=([0-9]+), [yx]=([0-9]+)\.\.([0-9]+)'
# ```
#
# In the list comprehension, the result of the split will be bound
# to `input_list`.
#
# The list comprehension will loop over the range of indices from
# `1` to the length of the list, increasing by 5, to address the
# start of each set of matches from the split expression.  These
# will be bound to the names `xy`, `static`, `first`, and `last`;
# the last three will be converted to integers.
#
# The list comprehension will produce a list of tuples spanning
# horizontally across the vein:
#
#     If the first group (xy) is `y`, the one tuple will be:
#     ```
#     [ (static, (first, last)) ]
#     ```
#
#     If the first group (xy) is `x`, the tuples will be:
#     ```
#     [
#         (first, (static, static)),
#         (first+1, (static, static)),
#         ...,
#         (last, (static, static))
#     ]
#     ```
#
# The list comprehension will be fed into the reduction, which will
# simply join the lists together.
#
# Return the sorted results of the reduction.

parse_horizontal_veins = lambda input_data: (
            sorted(
                reduce(
                    operator.add
                    ,
                    [
                        [
                            (static, (first, last))
                        ]
                        if xy == 'y'
                        else
                        [
                            (y, (static, static))
                            for y in range(first, last+1)
                        ]
                        for input_list in [
                            re.split(
                                r'([xy])=([0-9]+), [yx]=([0-9]+)\.\.([0-9]+)',
                                input_data
                            )
                        ]
                        for i      in range(1, len(input_list), 5)
                        for xy     in [input_list[i]]
                        for static in [int(input_list[i+1])]
                        for first  in [int(input_list[i+2])]
                        for last   in [int(input_list[i+3])]
                    ]
                )
            )
        )

########################################################################
#
# Parse the input data and return a list of vertical veins.
#
# As usual, do this with a reduction, list comprehension, and a regex.
#
# The regex will capture horizontal and vertical veins in the same
# groups, with the first group indicating whether it's a horizontal
# vein (`y`) or vertical vein (`x`).
# ```
# r'([xy])=([0-9]+), [yx]=([0-9]+)\.\.([0-9]+)'
# ```
#
# In the list comprehension, the result of the split will be bound
# to `input_list`.
#
# The list comprehension will loop over the range of indices from
# `1` to the length of the list, increasing by 5, to address the
# start of each set of matches from the split expression.  These
# will be bound to the names `xy`, `static`, `first`, and `last`;
# the last three will be converted to integers.
#
# The list comprehension will produce a list of tuples spanning
# horizontally across the vein:
#
#     If the first group (xy) is `x`, the one tuple will be:
#     ```
#     [ (static, (first, last)) ]
#     ```
#
#     If the first group (xy) is `y`, the tuples will be:
#     ```
#     [
#         (first, (static, static)),
#         (first+1, (static, static)),
#         ...,
#         (last, (static, static))
#     ]
#     ```
#
# The list comprehension will be fed into the reduction, which will
# simply join the lists together.
#
# Return the sorted results of the reduction.

parse_vertical_veins = lambda input_data: (
            sorted(
                reduce(
                    operator.add
                    ,
                    [
                        [
                            (static, (first, last))
                        ]
                        if xy == 'x'
                        else
                        [
                            (y, (static, static))
                            for y in range(first, last+1)
                        ]
                        for input_list in [
                            re.split(
                                r'([xy])=([0-9]+), [yx]=([0-9]+)\.\.([0-9]+)',
                                input_data
                            )
                        ]
                        for i      in range(1, len(input_list), 5)
                        for xy     in [input_list[i]]
                        for static in [int(input_list[i+1])]
                        for first  in [int(input_list[i+2])]
                        for last   in [int(input_list[i+3])]
                    ]
                )
            )
        )

########################################################################
#
# `stratify`: Transform a list of veins of clay striped in strata
# into lists of non-overlapping spans of _sand_ for each stratum
# that contains clay.
#
# The veins will be fed into a reduction, which will create sand spans
# for the areas in each stratum that do not contain clay.
#
# First, bind the minimum and maximum extents of clay to names.
# The minimum extent is found by
# ```
# min(vein[1][0] for vein in clay_veins)
# ```
# and the maximum is computed similarly from the `max` of `vein[1][1]`.
#
# Then reduce across the list of clay veins.
#
# Start the reduction with a list holding a sub-list with a single span
# guaranteed to not be on the same strata as any other vein.  This will
# be sripped out at the end.
# ```
# [ ( -1, [(min_extent,max_extent)] ) ]
# ```
#
# For each span:
#
#     If the `stratum` value is not the same as that of the last strata
#     in the list being built, then return the existing list with new
#     strata added to it.
#
#         First, add a span from `min_extent` through `max_extent` for
#         each `stratum` value between 1 higher than the last strata to
#         1 less than the new strata.
#
#         Then add the new strata consisting of the `stratum` value of
#         the clay span and a list of two sand spans, one starting at
#         `min_extent` and going through the space before the start of
#         the span, and the second starting after the end of the span
#         and going through `max_extent`.
#
#     If the end of the clay span is less than the start of the last sand
#     span of the current row, then the clay span is already accounted
#     for and will be ignored; just return the existing list.
#
#     If the _start_ of the clay span is less than or equal to the start
#     of the last sand span of the current row, then the clay span at
#     least partially overlaps the start of the sand span; return the
#     existing list with the start of the last sand span replaced by
#     one space beyond the end of the clay span.
#
#     Otherwise, return the existing list with the end of the last sand
#     span replaced by one space before the start of the clay span,
#     and a new sand span starting one space after the end of the clay
#     span and ending at `max_extent`.
#
# Filter the results of the reduction (skipping any strata before the
# first clay vein) through a list comprehension to remove any span of
# sand whose start is greater than the end.
# 
# Finally, produce the "strata" for each row - a tuple of the stratum
# index (`y` for horizontal strata or `x` for vertical strata`) and the
# list of spans of sand in that strata.

stratify = lambda clay_veins: (
            [

# Finally, produce the "strata" for each row - a tuple of the stratum
# index (`y` for horizontal strata or `x` for vertical strata`) and the
# list of spans of sand in that strata.

                (
                    row[0]
                    ,

# Filter the results of the reduction ...
#              ... through a list comprehension to remove any span of
# sand whose start is greater than the end.

                    [
                        sand_span
                        for sand_span in row[1]
                        if sand_span[0] <= sand_span[1]
                    ]
                )

# First, bind the minimum and maximum extents of clay to names.
# The minimum extent is found by
# ```
# min(vein[1][0] for vein in clay_veins)
# ```

                for min_extent in [
                    min(vein[1][0] for vein in clay_veins)
                ]

# and the maximum is computed similarly from the `max` of `vein[1][1]`.

                for max_extent in [
                    max(vein[1][1] for vein in clay_veins)
                ]

                for row in (

# Then reduce across the list of clay veins.

                    reduce(

# For each span:

                        lambda strata, (stratum,(start,end)): (

#     If the `stratum` value is not the same as that of the last strata
#     in the list being built, then return the existing list with new
#     strata added to it.
#
#         First, add a span from `min_extent` through `max_extent` for
#         each `stratum` value between 1 higher than the last strata to
#         1 less than the new strata.
#
#         Then add the new strata consisting of the `stratum` value of
#         the clay span and a list of two sand spans, one starting at
#         `min_extent` and going through the space before the start of
#         the span, and the second starting after the end of the span
#         and going through `max_extent`.

                            (
                                strata
                                + [
                                    (empty_stratum, [ (min_extent, max_extent) ])
                                    for empty_stratum in range(strata[-1][0]+1, stratum)
                                ]
                                + [
                                    (stratum, [ (min_extent, start-1), (end+1, max_extent) ])
                                ]
                            )
                            if stratum != strata[-1][0]
                            else

#     If the end of the clay span is less than the start of the last sand
#     span of the current row, then the clay span is already accounted
#     for and will be ignored; just return the existing list.

                            strata
                            # strata[-1] is the last strata in the list
                            # strata[-1][1] is the list of spans in that strata
                            # strata[-1][1][-1] is the last span in the strata.
                            # strata[-1][1][-1][0] is the start of that span.
                            if end <= strata[-1][1][-1][0]
                            else

#     If the _start_ of the clay span is less than or equal to the start
#     of the last sand span of the current row, then the clay span at
#     least partially overlaps the start of the sand span; return the
#     existing list with the start of the last sand span replaced by
#     one space beyond the end of the clay span.

                            (
                                strata[:-1]
                                + [
                                    (
                                        strata[-1][0]
                                        ,
                                        strata[-1][1][:-1]
                                        + [
                                            (
                                                end + 1,
                                                strata[-1][1][-1][1]
                                            )
                                        ]
                                    )
                                ]
                            )
                            if start <= strata[-1][1][-1][0]
                            else

#     Otherwise, return the existing list with the end of the last sand
#     span replaced by one space before the start of the clay span,
#     and a new sand span starting one space after the end of the clay
#     span and ending at `max_extent`.

                            strata[:-1]
                            + [
                                (
                                    strata[-1][0]
                                    ,
                                    strata[-1][1][:-1]
                                    + [
                                        (
                                            strata[-1][1][-1][0],
                                            start - 1,
                                        )
                                        ,
                                        (
                                            end + 1,
                                            max_extent
                                        )
                                    ]
                                )
                            ]

                        )
                        ,

# Then reduce across the list of clay veins.

                        clay_veins
                        ,

# Start the reduction with a list holding a sub-list with a single span
# guaranteed to not be on the same strata as any other vein:
# ```
# [ ( -1, [(min_extent,max_extent)] ) ]
# ```

                        [ (-1,[(min_extent,max_extent)]) ]

                    )
                )

# Filter the results of the reduction (skipping any strata before the
# first clay vein)...

                if row[0] >= clay_veins[0][0]
            ]
        )

########################################################################
#
# *bugfix* to fix scoring when water flows to the edge of the known clay
# strata.
#
# Extend the horizontal strata with an extra sand element at beginning
# and end.

extend_horizontal_strata = lambda strata: [
            (
                stratum[0]
                ,
                (
                    extended_right
                    for extended_left in [
                        [(min_x-1, min_x-1)] + stratum[1]
                        if len(stratum[1])==0 or stratum[1][0][0] != min_x
                        else
                        [(min_x-1, stratum[1][0][1])] + stratum[1][1:]
                    ]
                    for extended_right in [
                        extended_left + [(max_x+1, max_x+1)]
                        if extended_left[-1][1] != max_x
                        else
                        extended_left[:-1] + [(extended_left[-1][0], max_x+1)]
                    ]
                ).next()
            )
            for stratum in strata
            for min_x in [min(stratum[1][0][0] for stratum in strata if len(stratum[1]))]
            for max_x in [max(stratum[1][-1][1] for stratum in strata if len(stratum[1]))]
        ]

########################################################################
#
# *bugfix* to fix scoring when water flows to the edge of the known clay
# strata.
#
# Extend the vertical strata with an stratum at the beginning and end.

extend_vertical_strata = lambda strata: (
            [ (strata[0][0] - 1, [ (min_y, max_y) ]) ]
            + strata
            + [ (strata[-1][0] + 1, [ (min_y, max_y) ]) ]
            for min_y in [min(stratum[1][0][0] for stratum in strata if len(stratum[1]))]
            for max_y in [max(stratum[1][-1][1] for stratum in strata if len(stratum[1]))]
        ).next()

########################################################################
#
# Process the input data into horizontal and vertical sand strata.
# Produce a dictionary of:
#     * `horizontal_strata` - The results of calling `stratify` on
#       the output from `parse_horizontal_veins`, then extended to
#       include an extra sand element on either end.
#     * `vertical_strata` - The results of calling `stratify` on
#       the output from `parse_vertical_veins`, then extended with
#       a clear vertical sand strata at either end.
#     * `spring` - The pre-determined location of the spring, `(500,0)`

process_input_data = lambda input_data: (
            {
                'horizontal_strata':
                    extend_horizontal_strata(stratify(parse_horizontal_veins(input_data))),
                'vertical_strata':
                    extend_vertical_strata(stratify(parse_vertical_veins(input_data))),
                'spring':
                    (500,0),
            }
        )

########################################################################
#
# `render` the input data into a map of clay and sand.
#
# Used for debeaching porpoises.  er, debugging purposes.

render = lambda input_data: (
            '\n'
            + '({},{}) ... ({},{})'.format(
                input_data['vertical_strata'][0][0] ,
                input_data['horizontal_strata'][0][0] ,
                input_data['vertical_strata'][-1][0] ,
                input_data['horizontal_strata'][-1][0] ,
            )
            + '\n'
            + '\n'.join(
                reduce(
                    lambda line, (fillrow, (start,end)): (
                        line[:(start-min_x)]
                        + '~' * (end-start+1)
                        + line[(end-min_x)+1:]
                        if fillrow == row[0]
                        else line
                    )
                    ,
                    input_data['fills']
                    ,
                    reduce(
                        lambda line, (flowcol, (start,end)): (
                            line[:(flowcol-min_x)]
                            + '|'
                            + line[(flowcol-min_x)+1:]
                            if start <= row[0] <= end
                            else line
                        )
                        ,
                        input_data['flows']
                        ,
                        line
                    )
                )
                if 'fills' in input_data and 'flows' in input_data
                else line
                for min_x in [input_data['vertical_strata'][0][0]]
                for max_x in [input_data['vertical_strata'][-1][0]]
                for row in input_data['horizontal_strata']
                for line in [
                    ''.join(
                        '#' * (row[1][i][0] - (min_x if i == 0 else row[1][i-1][1] + 1))
                        + '.' * (row[1][i][1] - row[1][i][0] + 1)
                        for i in range(len(row[1]))
                    ) + '#' * (max_x - (row[1][-1][1] if len(row[1]) else (min_x - 1)))
                ]
            )
            + '\n'
        )

########################################################################
#
# Part 1:   Process the input data into a series of fills and spills.
#
# This is going to be a huge accumulator.
#
# The state will be a tuple of (fills, flows, spills, sand_columns)
#
# fills is a list of horizontal spans of water that have filled (where
# each span looks like `(y,(x0,x1))` indicating water has filled from
# `x0` to `x1` (inclusive) on row `y`.
#
# flows is a list of locations of infinitely flowing water.
#
# spills is a list of spill points.  a spill point is a place from where
# water is flowing down; the initial spill point is the spring at (500,0).
#
# Any spill point that spills to the bottom is removed from `spills` and
# its flow is added to `flows`.
#
# Any spill point that spills to a location surrounded by `flows` is
# treated similarly.
#
# sand_columns is the dictionary of vertical strata of sand from the
# input data; as the reduction proceeds, the vertical strata will be
# modified to remove areas that have been filled with water.
#
# The initial state is `([], [], [(500,0)], vertical_strata)`,
# where `[(500,0)]` is the initial spring and `vertical_strata` is
# the key from the `input_data` dictionary.
#
# Run the accumulation over an infinite counter.
#
# Each step of the accumulation consists of the following logic:
#
#     1.  Examine the last spill point in `spills`.  Identify the
#         span of the spill (from the spill point to the lowest
#         point of sand within the `vertical_strata` that contains
#         it).
#
#     2.  If the bottom of the spill is at the maximum horizontal
#         stratum, add the span of the spill to `flows` and remove
#         the spill point from `spills`.
#
#     3.  Otherwise:
#
#         4.  Identify the span in `horizontal_strata` that contains
#             the lowermost extent of the spill.
#
#         5.  Identify the rightmost flow that intersects the horizontal
#             span to the left of the spill, if any, and the leftmost
#             flow that intersects the horizontal span to the right of
#             the spill, if any.
#
#         6.  Reduce the span to not include those flows, if needed.
#
#         7.  Using `vertical_strata`, identify the right-most gap to
#             the left of the spill (if any) in the stratum underlying
#             the horizontal span.
#
#         8.  If such a gap exists, create a new spill point above
#             the gap.
#
#         9.  Using `vertical_strata`, identify the right-most gap to
#             the left of the spill (if any) in the stratum underlying
#             the horizontal span.
#
#         10. If such a gap exists, create a new spill point above
#             the gap.
#
#         11. If no gap exists and no flow was found, then the span
#             needs to be filled with water:
#
#             12. Add the span (in `(stratum,(start,end))` format) to
#                 `fills`.
#
#             12a. Remove any spill point that is within the new span.
#
#             13. Any vertical stratum in `vertical_strata` that includes
#                 a vertical span which intersects the fill span must by
#                 definition _end_ at the fill span; therefore, update
#                 `vertical_strata` such that the vertical span in each
#                 stratum within the fill span that includes the fill
#                 span now ends just above the fill span.
#
#         14. Otherwise, no gap exists but a flow was found; convert
#             both the span and the spill to flows:
#
#             15. For each vertical stratum in the span _not_ including
#                 the spill, add a flow at that vertical stratum that
#                 spans just the one row at the bottom of the spill.
#
#             16. Add the spill itself to flows, limiting the vertical
#                 span of the flow to the minimum and maximum extent
#                 of the vertical space but otherwise spanning from the
#                 spill point to the bottom of the spill.
#
#             17. Remove the spill point from spills.
#
# Run the accumulator through a `dropwhile` that drops any state which
# contains one or more spills.
#
# Take the next state from the `dropwhile`, deduplicate the resulting
# lists of spans in `fills` and `flows`, and return the sum of the
# length of all remaining spans.
#
# Note - to solve part 2, there is an extra optional argument for part
# 1: if `include_flows` is passed as False, then only the `fills` will
# be counted in the final sum.

part_1 = lambda input_data, include_flows=True: (

# Take the next state from the `dropwhile` and return the sum of the
# length of each span in `fills` and `flows`.

            sum(
                len(set(
                    (rowcol, colrow)
                    for (rowcol,(start,end)) in
                        fill_flow_span
                    for colrow in
                        range(start, end+1)
                ))
                for fill_flow_span in (
#render(dict(zip(('fills', 'flows', 'spills', 'horizontal_strata', 'vertical_strata'), (


# Run the accumulator through a `dropwhile` that drops any state which
# contains one or more spills.

                    itertools.dropwhile(
                        lambda fills_flows_spills_sand: (
                            len(fills_flows_spills_sand[2]) > 0
                        )
                        ,

# This is going to be a huge accumulator.

                        accumulate(

# The initial state is `([], [], [(500,0)], vertical_strata)`,
# where `[(500,0)]` is the initial spring and `vertical_strata` is
# the key from the `input_data` dictionary.
#
# Run the accumulation over an infinite counter.

                            itertools.chain(
                                [
                                    (
                                        # the 'fills'
                                        [],
                                        # the 'flows'
                                        [],
                                        # the 'springs'
                                        [input_data['spring']],
                                        # the horizontal sand
                                        input_data['horizontal_strata'],
                                        # the vertical sand
                                        input_data['vertical_strata'],
                                    )
                                ]
                                ,
                                itertools.count(1)
                            )
                            ,

# Each step of the accumulation consists of the following logic:

                            lambda state, _: (

#     2.  If the bottom of the spill is at the maximum horizontal
#         stratum, add the span of the spill to `flows` and remove
#         the spill point from `spills`.

                                (
                                    fills,
                                    sorted(flows + [this_spill]),
                                    spills[:-1],
                                    horizontal_strata,
                                    vertical_strata
                                )
                                if this_spill[1][-1] == max_y

#     3.  Otherwise:

                                else (

#         8.  If such a gap exists [on the left], create a new spill
#             point above the gap.
#
#         10. If such a gap exists [on the right], create a new spill
#             point above the gap.

                                    (
                                        fills
                                        ,
                                        flows
                                        ,
                                        spills + (
                                            []
                                            if left_gap is None
                                            else [
                                                (left_gap, this_spill[1][1])
                                            ]
                                        ) + (
                                            []
                                            if right_gap is None
                                            else [
                                                (right_gap, this_spill[1][1])
                                            ]
                                        )
                                        ,
                                        horizontal_strata
                                        ,
                                        vertical_strata
                                    )
                                    if left_gap is not None or right_gap is not None
                                    else

                                    (

#             12. Add the span (in `(stratum,(start,end))` format) to
#                 `fills`.

                                        fills + [(this_spill[1][1],spill_spread)]
                                        ,

# (undocumented) leave the rest of the state as is

                                        flows
                                        ,

#             12a. Remove any spill point that is within the new span.

                                        [
                                            spill
                                            for spill in spills
                                            if spill[1] != this_spill[1][1]
                                            or spill[0] < spill_spread[0]
                                            or spill[0] > spill_spread[1]
                                        ]
                                        ,
                                        horizontal_strata
                                        ,

#             13. Any vertical stratum in `vertical_strata` that includes
#                 a vertical span which intersects the fill span must by
#                 definition _end_ at the fill span; therefore, update
#                 `vertical_strata` such that the vertical span in each
#                 stratum within the fill span that includes the fill
#                 span now ends just above the fill span.

                                        [
                                            (
                                                stratum[0],
                                                stratum[1]
                                                if stratum[0] < spill_spread[0] or stratum[0] > spill_spread[1]
                                                else
                                                [
                                                    (
                                                        span[0]
                                                        ,
                                                        this_spill[1][1] - 1
                                                    )
                                                    if span[1] == this_spill[1][1]
                                                    else (
                                                        span
                                                    )
                                                    for span in stratum[1]
                                                    if span[0] < this_spill[1][1]
                                                    or span[1] > this_spill[1][1]
                                                ]
                                            )
                                            for stratum in vertical_strata
                                        ]

                                    )

#         11. If no gap exists and no flow was found, then the span
#             needs to be filled with water:

                                    if (
                                        left_flow is None
                                        and right_flow is None
                                    )
                                    else

#         14. Otherwise, no gap exists but a flow was found; convert
#             both the span and the spill to flows:

                                    (
                                        fills
                                        ,

#             15. For each vertical stratum in the span _not_ including
#                 the spill, add a flow at that vertical stratum that
#                 spans just the one row at the bottom of the spill.
#
#             16. Add the spill itself to flows, limiting the vertical
#                 span of the flow to the minimum and maximum extent
#                 of the vertical space but otherwise spanning from the
#                 spill point to the bottom of the spill.

                                        sorted(
                                            flows
                                            + [
                                                this_spill
                                                if stratum == this_spill[0]
                                                else (
                                                    stratum
                                                    ,
                                                    (
                                                        this_spill[1][1]
                                                        ,
                                                        this_spill[1][1]
                                                    )
                                                )
                                                for stratum in range(free_spread[0], free_spread[1]+1)
                                            ]
                                        )
                                        ,

#             17. Remove the spill point from spills.

                                        spills[:-1]
                                        ,

# undocumented: keep the rest of the state the same

                                        horizontal_strata
                                        ,
                                        vertical_strata
                                    )

#         4.  Identify the span in `horizontal_strata` that contains
#             the lowermost extent of the spill.

                                    for spill_spread in [
                                        sand_span
                                        for sand_spans in horizontal_strata
                                        if sand_spans[0] == this_spill[1][1]
                                        for sand_span in sand_spans[1]
                                        if sand_span[0] <= this_spill[0] <= sand_span[1]
                                    ]

#         5.  Identify the rightmost flow that intersects the horizontal
#             span to the left of the spill, if any, and the leftmost
#             flow that intersects the horizontal span to the right of
#             the spill, if any.

                                    for left_flow in [
                                        (
                                            [
                                                flow[0]
                                                for flow in reversed(flows)
                                                if spill_spread[0] <= flow[0] < this_spill[0]
                                                and flow[1][0] <= this_spill[1][1] <= flow[1][1]
                                            ] + [None]
                                        )[0]
                                    ]

                                    for right_flow in [
                                        (
                                            [
                                                flow[0]
                                                for flow in flows
                                                if this_spill[0] < flow[0] <= spill_spread[1]
                                                and flow[1][0] <= this_spill[1][1] <= flow[1][1]
                                            ] + [None]
                                        )[0]
                                    ]

#         6.  Reduce the span to not include those flows, if needed.

                                    for free_spread in [
                                        (
                                            left_flow + 1
                                            if left_flow is not None
                                            else spill_spread[0]
                                            ,
                                            right_flow - 1
                                            if right_flow is not None
                                            else spill_spread[1]
                                        )
                                    ]

#         7.  Using `vertical_strata`, identify the right-most gap to
#             the left of the spill (if any) in the stratum underlying
#             the horizontal span.

                                    for left_gap in [
                                        (
                                            [
                                                sand[0]
                                                for sand in reversed(vertical_strata)
                                                if free_spread[0] <= sand[0] < this_spill[0]
                                                for span in sand[1]
                                                if span[0] <= (this_spill[1][1]+1) <= span[1]
                                            ] + [None]
                                        )[0]
                                    ]

#         9.  Using `vertical_strata`, identify the right-most gap to
#             the left of the spill (if any) in the stratum underlying
#             the horizontal span.

                                    for right_gap in [
                                        (
                                            [
                                                sand[0]
                                                for sand in vertical_strata
                                                if this_spill[0] < sand[0] <= free_spread[1]
                                                for span in sand[1]
                                                if span[0] <= (this_spill[1][1]+1) <= span[1]
                                            ] + [None]
                                        )[0]
                                    ]

                                ).next()

# undocumented steps: bind names to the items in 'state'
                                for fills in [state[0]]
                                for flows in [state[1]]
                                for spills in [state[2]]
                                for horizontal_strata in [state[3]]
                                for vertical_strata in [state[4]]

# undocumented steps: bind names to the extrema of the countable part of the space
                                for min_x in [vertical_strata[0][0]]
                                for max_x in [vertical_strata[-1][0]]
                                for min_y in [horizontal_strata[0][0]]
                                for max_y in [horizontal_strata[-1][0]]

#     1.  Examine the last spill point in `spills`.  Identify the
#         span of the spill (from the spill point to the lowest
#         point of sand within the `vertical_strata` that contains
#         it).

                                for this_spill in [
                                    (
                                        spills[-1][0]
                                        ,
                                        (
                                            [
                                                (
                                                    max(spills[-1][1], sand_span[0])
                                                    ,
                                                    sand_span[1]
                                                )
                                                for sand_spans in vertical_strata
                                                if sand_spans[0] == spills[-1][0]
                                                for sand_span in sand_spans[1]
                                                if  sand_span[0]
# use `max()` to catch the spring (which will always be above the top level of sand).
                                                    <= max(min_y, spills[-1][1])
                                                    <= sand_span[1]
                                            ] + [None]
                                        )[0]
                                    )
                                ]
                            ).next()

                        )

                    ).next()

                )[0:(2 if include_flows else 1)]
            )

        )

########################################################################
#
# Part 2:   ...

part_2 = lambda input_data: (
            part_1(input_data, include_flows=False)
        )

########################################################################
#
# Main controller

if __name__ == '__main__':

    base_filename = __file__.rsplit('.')[0]

    input_filename = '{}.input'.format(base_filename)
    input_data = open(input_filename).read()

    for sample_num in itertools.takewhile(lambda num:os.path.exists('{}.sample.{}'.format(base_filename, num)), itertools.count(1)):
        #if DEBUGGING: break

        sample_filename = '{}.sample.{}'.format(base_filename, sample_num)
        sample_data = open(sample_filename).read()

        results_filename = '{}.sample.results.part1.{}'.format(base_filename, sample_num)
        expected = (
                    int(open(results_filename).read().strip())
                    if os.path.exists(results_filename)
                    else None
                )

        if DEBUGGING: print >> sys.stderr, render(process_input_data(sample_data))
        t = time.time()
        result = part_1(process_input_data(sample_data))
        t = time.time() - t
        print "{}: sample {}: part 1 = {}{}".format(t, sample_num, result, " (expected {})".format(expected) if result != expected else "")

        #if DEBUGGING: sys.exit(0)

    #if DEBUGGING: sys.exit(0)

    if DEBUGGING: print >> sys.stderr, render(process_input_data(input_data))

    t = time.time()
    result = part_1(process_input_data(input_data))
    t = time.time() - t
    print "{}: input data: part 1 = {}".format(t, result)

    if DEBUGGING: sys.exit(0)

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

