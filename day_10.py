
import re
import sys
import itertools
import operator

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

re_input=re.compile(r'''position=< *(?P<x>-?[0-9]+) *, *(?P<y>-?[0-9]+) *> velocity=< *(?P<dx>-?[0-9]+) *, *(?P<dy>-?[0-9]+) *>''')
process_input_data = lambda input_data: list(
            dict(
                (key,int(value))
                for (key,value) in
                    m.groupdict().items()
            )
            for m in
                re_input.finditer(input_data)
        )

########################################################################
#
# Part 1:
#
# Iterate the positions until all lights are orthagonally adjacent to
# another light.

# first, a conversion from the list of lights to the display grid.

show_lights = lambda lights: (
            '\n'.join(
                ['']
                + [str(lights[0]['count'])]
                + [
                    ''.join(
                        '#'
                        if x in points
                        else '.'
                        for points in [
                            set(light['x'] for light in lightrow)
                        ]
                        for x in range(minx, maxx+1)
                    )
                    for (minx, maxx, miny, maxy) in [
                        (
                            min(light['x'] for light in lights) - 4,
                            max(light['x'] for light in lights) + 4,
                            min(light['y'] for light in lights) - 1,
                            max(light['y'] for light in lights) + 1,
                        )
                    ]
                    for y in range(miny, maxy+1)
                    for lightrow in [
                        [
                            light
                            for light in lights
                            if light['y'] == y
                        ]
                    ]
                ]
            )
        )

# identify the lights which have no neighbors.

solo_lights = lambda lights: [
            light
            for lightset in [
                set(
                    (light['x'], light['y'])
                    for light in lights
                )
            ]
            for light in lightset
            if (
                    (light[0]-1,light[1]+0) not in lightset
                and (light[0]+1,light[1]+0) not in lightset
                and (light[0]+0,light[1]-1) not in lightset
                and (light[0]+0,light[1]+1) not in lightset
                and (light[0]-1,light[1]-1) not in lightset
                and (light[0]+1,light[1]-1) not in lightset
                and (light[0]-1,light[1]+1) not in lightset
                and (light[0]+1,light[1]+1) not in lightset
            )
        ]

# process the light list continuously until there are no solo lights.
# Use `accumulate` to process the light list, running off of an iterator
# `chain` consisting of the input data as the first element, followed by
# the second count (starting at 1 and increasing infinitely).
# USe `dropwhile` to skip iterator elements until there are no solo lights.
# Then take the next iteration and process that through `show_lights`.

part_1 = lambda input_data: show_lights(
            itertools.dropwhile(
                lambda lights:
                    len(solo_lights(lights)) > 0
                ,
                accumulate(
                    itertools.chain([input_data], itertools.count(1))
                    ,
                    lambda lights, count: list(
                            {
                                'x': light['x'] + light['dx'],
                                'y': light['y'] + light['dy'],
                                'dx': light['dx'],
                                'dy': light['dy'],
                                'count': count
                            }
                            for light in lights
                        )
                )
            ).next()
        )

########################################################################
#
# Part 2:   ...

part_2 = lambda input_data: (
            None
        )

if __name__ == '__main__':

    sample_data = process_input_data(open(__file__.rsplit('.')[0] + '.sample').read())

    print "sample data: part 1 = {}".format(part_1(sample_data))
    # part 1 includes the output for part 2
    # print "sample data: part 2 = {}".format(part_2(sample_data))

    input_data = process_input_data(open(__file__.rsplit('.')[0] + '.input').read())

    print "real input: part 1 = {}".format(part_1(input_data))
    # part 1 includes the output for part 2
    # print "real input: part 2 = {}".format(part_2(input_data))
