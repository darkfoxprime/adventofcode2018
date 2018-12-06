
import re
import sys
import itertools

def process_input_data(input_data):
    return input_data

def claims(input_data):

    # input format is single multi-line string with claims of the form:
    #   <id> @ <x>,<y>: <w>x<h>

    re_id_format = re.compile(r'''#(?P<id>[0-9]+) *@ *(?P<x>[0-9]+) *, *(?P<y>[0-9]+) *: *(?P<w>[0-9]+) *x *(?P<h>[0-9]+)''')

    # return a generator that returns each rectangle as a dictionary,
    # mapping values to integers for every field except the id.

    return (
                dict(
                    (key,int(val))
                    if key != 'id'
                    else (key,val)
                    for (key,val) in match.groupdict().items()
                )
                for match in re_id_format.finditer(input_data)
            )

# Use `claims_to_occupancy_data` to transform the list of claims rectangles
# to a list of rows, each row consisting of a list of non-overlapping claimed
# spans (where each span indicates which claim _or claims_ occupy that span).

# Take each list of non-overlapping spans and convert the spans to either 0,
# if # only one claim occupies the span, or the width of the span, if more
# than one claim occupies the span; then sum each row, and sum each row-sum
# to find the total space occupied by more than one claim.

def part_1(input_data):
    occupancy_data = claims_to_occupancy_data(claims(input_data))
    return sum(sum(0 if len(occupancy[3]) == 1 else 1 + (occupancy[2] - occupancy[1]) for occupancy in row) for row in occupancy_data)

# Use `claims_to_occupancy_data` to transform the list of claims rectangles
# to a list of rows, each row consisting of a list of non-overlapping claimed
# spans (where each span indicates which claim _or claims_ occupy that span).

# reduce the list-of-lists of non-overlapping spans to a set of all claim
# ids found in spans with multiple claim ids.
# take the set of _all_ claim ids, subtract the claim ids found through the
# reduction, and return the first (should be only) claim id.

def part_2(input_data):
    all_ids = set(claim['id'] for claim in claims(input_data))
    overlapping_ids = reduce(
                set.union,
                (
                    set(occupancy[3])
                    for row in claims_to_occupancy_data(claims(input_data))
                    for occupancy in row
                    if len(occupancy[3]) > 1
                )
            )
    return (all_ids - overlapping_ids).pop()



# Given a list of claim dictionaries, transform the list of claims into
# a list of the space occupied by each claim on each row on which that
# claim exists:
# ```
#   [
#      (rowA, start1, end1, id1),
#      (rowB, start1, end1, id1),
#      ...,
#      (rowF, start1, end1, id1),
#      (rowD, start2, end2, id2),
#      (rowE, start2, end2, id2),
#      ...,
#      (rowH, start2, end2, id2),
#      ...
#   ]
# ```
#
# Sort the list by row, then group the list into sublists, one per
# unique row, containing all claim occupancies for that row.  For aid in
# further processing, put the id for each claim into a nested sublist:
# ```
# [
#   [
#     (rowA, start1, end1, [id1]),
#     (rowA, start2, end2, [id2]),
#     ...
#   ],
#   [
#     (rowB, start1, end1, [id1]),
#     (rowB, start2, end2, [id2]),
#     (rowB, start3, end3, [id3]),
#     ...
#   ],
#   ...
# ]
# ```
#
# For each row-based list, use `row_to_unique_occupancies` to split
# and re-combine each of the rows of occupancies into non-overlapping
# spans listing all claims that occupy that span, of the form:
# ```
#   [ (rowA, start1, end1, [ids1]), (rowA, start2, end2, [ids2]), ... ]
# ```
# where the start of each subsequent span is strictly greater than
# the end of the previous span.

def claims_to_occupancy_data(claims):
    return [

        # use `row_to_unique_occupances()` (below) to transform each row
        # of claim occupancies into a row of non-overlapping spans
        # occupied by one or more claims.

        list(row_to_unique_occupancies(row))

        for row in
            reduce(

                # reduce the list of spans into a list of rows-of-spans
                # by adding each span to the list of rows-of-spans if
                # the list of rows-of-spans is empty _or_ if the row
                # number in the first span of the last row is not the
                # same as the current span's row; otherwise, append
                # the span to the last row of the list of rows.

                lambda rows, (row, start, end, ids):
                    rows + [ [(row, start, end, ids)] ]
                    if not rows or rows[-1][0][0] != row
                    else rows[:-1] + [ rows[-1] + [(row, start, end, ids)] ]
                ,

                # start by transforming the list of claims into a list
                # of tuples indicating a row, a span of columns in that
                # row, and a claim id in a sublist, and sort the result
                # by row and by the start of the span.

                sorted(
                    (y, claim['x'], claim['x'] + claim['w'] - 1, [claim['id']])
                    for claim in claims
                    for y in range(claim['y'], claim['y'] + claim['h'])
                )
                ,

                # initialize the reduction with an empty list of rows.

                []
            )
    ]

# Transform a row of overlapping claim spans of the form
# `(row, start, end, id)` to a row of non-overlapping spans occupied by
# of one _or more_ claims of the form `(row, start, end, [ids])`

# I could not figure out how to do this as a generator expression, list
# comprehension, or reduction, and so I ended up having to do it as a
# generator function :(

def row_to_unique_occupancies(row):

    # `current` holds an array of occupancies.  The logic guarantees
    # that, if there are any occupancies in current, all those
    # occupancies will have the same start points.  There is *NO SUCH*
    # guarantee about the end points.

    current = []

    for next in row:

        # For as long as `current` is not empty, and the first spam in
        # `current` starts before `next` starts...
        #
        #     Define `current_split` as the minimum value of 1 space
        #     before the start of `next` and all the end spaces of the
        #     spans in `current`.  This is the point at which the next
        #     non-overlapping span will be split off.
        #
        #     Yield a single span occupying the same row as `current`,
        #     starting at the same place as the first span in `current`,
        #     ending at `current_split`, and occupied by all claim ids
        #     that occupy any of the spans in `current`.
        #
        #     Then rewrite `current` to eliminate any spans that end at
        #     `current_split` so that the start of any remaining span in
        #     `current` is equal to `current_split`.

        while current and current[0][1] < next[1]:

            current_split = min([next[1] - 1] + [occupancy[2] for occupancy in current])

            yield(current[0][0], current[0][1], current_split, reduce(list.__add__, (occupancy[3] for occupancy in current)))

            current = [(occupancy[0], current_split + 1, occupancy[2], occupancy[3]) for occupancy in current if occupancy[2] > current_split]

        # At this point, `current` is either empty, or consists of spans
        # starting at the same place as `next`.  In either case, add
        # `next` to the list of spans in `current`.

        current.append(next)

    # For as long as `current` is not empty, go through the same span-
    # splitting process as described above.

    while current:
        current_split = min([occupancy[2] for occupancy in current])
        yield(current[0][0], current[0][1], current_split, reduce(list.__add__, (occupancy[3] for occupancy in current)))
        current = [(occupancy[0], current_split + 1, occupancy[2], occupancy[3]) for occupancy in current if occupancy[2] > current_split]

if __name__ == '__main__':

    sample_data = process_input_data(open(__file__.rsplit('.')[0] + '.sample').read())

    print "sample data: part 1 = {}".format(part_1(sample_data))
    print "sample data: part 2 = {}".format(part_2(sample_data))

    input_data = process_input_data(open(__file__.rsplit('.')[0] + '.input').read())

    print "real input: part 1 = {}".format(part_1(input_data))
    print "real input: part 2 = {}".format(part_2(input_data))
