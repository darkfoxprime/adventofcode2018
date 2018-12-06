
import re
import sys
import itertools

# Transform the input string into a list of (x,y) tuples

def process_input_data(input_data):
    re_coords = re.compile(r'''([0-9]+), *([0-9]+)''')
    return list(tuple(int(coord) for coord in match.groups()) for match in re_coords.finditer(input_data))

# Given a point and a list of coordinates, return the closest
# distance between the point and any of those coordinates,
# and either the closest coordinate or None if multiple coordinates
# are at the same closest distance to the point.

def find_closest_coord(point, coords):
    return reduce(

                # reduce the list of distance+coordinate tuples to the
                # closest distance:
                #   if the current distance is greater than the previous
                #   distance, return the previous distance and coordinate;
                #   if the current distance is less than the previous
                #   distance, return the new distance and coordinate;
                #   if the current distance is equal to the previous
                #   distance, return the previous distance and None
                #   as the coordinate (to mark a duplicate).

                lambda (closest_dist, closest_coord), (dist, coord):
                    (closest_dist, closest_coord) if dist > closest_dist
                    else (dist, coord) if dist < closest_dist
                    else (closest_dist, None)
                ,

                # for each coordinate, generate the manhattan distance
                # betwen the point and that coordinate.  The generated
                # list includes both the distance and the coordinate
                # itself.

                (
                    ( abs(point[0]-coord[0]) + abs(point[1]-coord[1]), coord)
                    for coord in coords
                )
            )

# Part 1:
#
#   Return the number of points that are closest to the
#   coordinate which includes the largest _non-infinite_
#   number of "closest points".
#
#   A point is closest to a coordinate if its distance
#   to that coordinate is strictly less than its distance
#   to any other coordinate.

def part_1(input_data):

    # Calculate the bounds of the coordinates.  This both gives us
    # the range of locations which need to be considered, and gives
    # us the coordinates which will have infinite areas - those which
    # are closest to any points on the bounds.

    bounds = (tuple(min(coord) for coord in zip(*input_data)), tuple(max(coord) for coord in zip(*input_data)))

    # The main reduction is complicated by the need to use generators
    # or comprehensions in order to assign results to variables
    # so that those results can be used multiple times.  this is
    # the reason for the `for <name> in [ <expression> ]` blocks.

    # From the inside out:
    #
    # We first generate a list of the closest coordinates for each
    # location on or within the bounds, filtering out any "closest
    # coordinate" that has a coordinate of None, and assign that
    # result to `closest_coords`.
    #
    # We then generate the set of those coordinates that will
    # have infinite areas by gathering all the coordinate values
    # from the `closest_coords` whose location is on the bounds.
    #
    # We filter the infinite coordinates out of the
    # `closest_coords` list, then sort the results by coordinate.
    #
    # The sorted list is grouped by coordinate, then length
    # of each group is calculated, and the maximum length
    # is returned.

    return max(
                len(list(points))
                for (coord,points) in
                    itertools.groupby(
                        sorted(
                            (
                                closest_coord
                                for closest_coords in [
                                    [
                                        closest_coord
                                        for closest_coord in
                                            (
                                                (find_closest_coord((x,y), input_data), (x,y))
                                                for x in xrange(bounds[0][1], bounds[1][0]+1)
                                                for y in xrange(bounds[0][1], bounds[1][1]+1)
                                            )
                                        if closest_coord[0][1] is not None
                                    ]
                                ]
                                for infinite_coords in [
                                    set(
                                        closest_coord[0][1]
                                        for closest_coord in closest_coords
                                        if closest_coord[1][0] in (bounds[0][0], bounds[1][0])
                                        or closest_coord[1][1] in (bounds[0][1], bounds[1][1])
                                    )
                                ]
                                for closest_coord in closest_coords
                                if closest_coord[0][1] not in infinite_coords
                            )
                            ,
                            key = lambda ((dist, coord), point): coord
                        )
                        ,
                        key = lambda ((dist, coord), point): coord
                    )
            )

# Part 2:
#
#   Return the number of points whose total distance to
#   all coordinates in the input data is less than the
#   "safe distance".

def part_2(input_data, safe_dist):

    # We assume that all safe locations will be within the bounds
    # of all coordinates in the input data.  This might not be a
    # safe assumption.

    bounds = (tuple(min(coord) for coord in zip(*input_data)), tuple(max(coord) for coord in zip(*input_data)))

    # For each location on or within the bounds, calculate the
    # sum of the distances between that location and all coordinates.
    # Reduce the list of total-distances to the count of safe locations
    # by initializing the count to 0 and returning the count + 1 for
    # any location which is safe (distance < safe distance) or keeping
    # count the same otherwise.

    return reduce(
                lambda count, dist:
                    count + 1
                    if dist < safe_dist
                    else count
                ,
                (
                    sum(
                        abs(x-coord[0]) + abs(y-coord[1])
                        for coord in input_data
                    )
                    for x in xrange(bounds[0][1], bounds[1][0]+1)
                    for y in xrange(bounds[0][1], bounds[1][1]+1)
                )
                ,
                0
            )

if __name__ == '__main__':

    sample_data = process_input_data(open(__file__.rsplit('.')[0] + '.sample').read())

    print "sample data: part 1 = {}".format(part_1(sample_data))
    print "sample data: part 2 = {}".format(part_2(sample_data, 32))

    input_data = process_input_data(open(__file__.rsplit('.')[0] + '.input').read())

    print "real input: part 1 = {}".format(part_1(input_data))
    print "real input: part 2 = {}".format(part_2(input_data, 10000))
