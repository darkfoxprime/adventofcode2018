
import re
import sys
import itertools

def claims(input_data):
    # input format is:  <id> @ <x>,<y>: <w>x<h>
    re_id_format = re.compile(r'''#(?P<id>[0-9]+) *@ *(?P<x>[0-9]+) *, *(?P<y>[0-9]+) *: *(?P<w>[0-9]+) *x *(?P<h>[0-9]+)''')
    return itertools.imap(lambda m:dict((key,int(val)) if key != 'id' else (key,val) for (key,val) in m.groupdict().items()), re_id_format.finditer(input_data))

# Transform input to a list of claims (via `claims()` generator).
# Transform the list of claims into a list of the space occupied by each claim on each row on which that claim exists:  [ (rowA, start1, end1, id1), (rowB, start1, end1, id1), ..., (rowF, start1, end1, id1), (rowD, start2, end2, id2), (rowE, start2, end2, id2), ..., (rowH, start2, end2, id2), ... ]  (via generator expression)
# Sort the list of claim-occupancy-per-rows. (not iterable :()
# Group the list into sublists, one per unique row, containing all claim occupancies for that row.  Put each claim occupancy into its own sublist, with the id in a nested sublist: (via reduce)
# [
#   [ [(rowA, start1, end1, [id1])], [(rowB, start2, end2, [id2])] ... ],
#   [ [(rowB, start3, end3, [id3])] ... ],
#   ...
# ]
# For each row-based list, split and recombine occupancies into a new list with non-overlapping, unique occupancy ranges.
#   If both of these are on the same row,
#     ..AAAA.... = [(rowA, 2, 5, [A])]
#     ....BBB... = [(rowA, 4, 6, [B])]
#   split and recombine to form:
#     [ (rowA, 2, 3, [A]), (rowA, 4, 5, [A,B]), (rowA, 6, 6, [B]) ]
#   If one is entirely contained within another:
#     ..CCCCC... = [(rowB, 2, 6, [C])]
#     ...DD..... = [(rowB, 3, 4, [D])]
#   split and recombine to form:
#     [ (rowB, 2, 2, [C]), (rowB, 3, 4, [C,D]), (rowB, 5, 6, [C]) ]
#   (each row is a generator, not realized until enumerated)

def row_to_unique_occupancies(row):
    # current holds an array of occupancies.  it is guaranteed that,
    # if there are any occupancies in current, all those occupancies
    # will have the same start point.  there is *NO SUCH* guarantee
    # about the end point.
    current = []
    for next in row:
        # for as long as current[START] < next[START],
        #     define current_split as the minimum value of next[START]
        #     and all current[END] values.
        #     yield the portion of current between current[START] and
        #     current_split.
        #     then rewrite current so that the start value of any
        #     remaining occupancy in current is current_split.
        while current and current[0][1] < next[1]:
            current_split = min([next[1] - 1] + [occupancy[2] for occupancy in current])
            yield(current[0][0], current[0][1], current_split, reduce(list.__add__, (occupancy[3] for occupancy in current)))
            current = [(occupancy[0], current_split + 1, occupancy[2], occupancy[3]) for occupancy in current if occupancy[2] > current_split]
        # current is either empty or has a start equal to next[START].
        # in either case, append next.
        current.append(next)
    # yield the final occupancy results
    while current:
        current_split = min([occupancy[2] for occupancy in current])
        yield(current[0][0], current[0][1], current_split, reduce(list.__add__, (occupancy[3] for occupancy in current)))
        current = [(occupancy[0], current_split + 1, occupancy[2], occupancy[3]) for occupancy in current if occupancy[2] > current_split]

def claims_to_occupancy_data(claims):
    return [
        list(row_to_unique_occupancies(row))
        for row in
            reduce(
                lambda rows, (row, start, end, ids):
                    rows + [ [(row, start, end, ids)] ]
                    if not rows or rows[-1][0][0] != row
                    else rows[:-1] + [ rows[-1] + [(row, start, end, ids)] ]
                ,
                sorted(
                    (y, claim['x'], claim['x'] + claim['w'] - 1, [claim['id']])
                    for claim in claims
                    for y in range(claim['y'], claim['y'] + claim['h'])
                )
                ,
                []
            )
    ]

# once I have the coalesced occupancy ranges, map each claim to either 0
# (for a single claim) or (end-start+1) (for a range with multiple claims),
# then sum the sums of each row list.

def day_03a(input_data):
    occupancy_data = claims_to_occupancy_data(claims(input_data))
    return sum(sum(0 if len(occupancy[3]) == 1 else 1 + (occupancy[2] - occupancy[1]) for occupancy in row) for row in occupancy_data)

def day_03b(input_data):
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

if __name__ == '__main__':

    input_data = open('day_03.input').read()

    print "Day 03 a = {}".format(day_03a(input_data))
    print "Day 03 b = {}".format(day_03b(input_data))
