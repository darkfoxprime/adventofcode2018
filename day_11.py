
import re
import sys
import itertools
import time

DEBUGGING=False
if DEBUGGING:
    def reduce(func, iterable, initial=None):
        iterable = iter(iterable)
        if initial is None:
            initial = iterable.next()
        for value in iterable:
            print >> sys.stderr, ">>reduce<< state={0!r} value={1!r}".format(initial, value)
            initial = func(initial, value)
        print >> sys.stderr, ">>reduce<< final state={0!r}".format(initial)
        return initial

########################################################################
#
# Process input data to return the appropriate records or data format.

process_input_data = lambda input_data: (
            int(input_data)
        )

power_level_of = lambda x,y,serial: (
            (
                (x * x * y + x * y * 20 + y * 100 + x * serial + 10 * serial)
                // 100
            ) % 10 - 5
        )

########################################################################
#
# Part 1:   ...

part_1 = lambda serial: (
            max(
                (
                    power_level_of(x, y, serial)
                    + power_level_of(x+1, y, serial)
                    + power_level_of(x+2, y, serial)
                    + power_level_of(x, y+1, serial)
                    + power_level_of(x+1, y+1, serial)
                    + power_level_of(x+2, y+1, serial)
                    + power_level_of(x, y+2, serial)
                    + power_level_of(x+1, y+2, serial)
                    + power_level_of(x+2, y+2, serial)
                    ,
                    x
                    ,
                    y
                )
                for x in range(1, 299)
                for y in range(1, 299)
            )
        )

########################################################################
#
# Part 2:   ...

initial_grid = lambda serial: tuple(
            tuple(
                power_level_of(x, y, serial)
                for x in range(1,301)
            )
            for y in range(1,301)
        )

part_2 = lambda serial: (
            max(
                (
                    sum(
                        sum(
                            power_grid[y+dy-1][(x-1):(x+size-1)]
                        )
                        for dy in range(size)
                    )
                    ,
                    x
                    ,
                    y
                    ,
                    size
                )
                for size in range(1,301)
                for x in range(1,302-size)
                for y in range(1,302-size)
            )
            for power_grid in [initial_grid(serial)]
        ).next()

if __name__ == '__main__':

    sample_data = process_input_data(open(__file__.rsplit('.')[0] + '.sample').read())

    t0 = time.time()
    part_1_answer = part_1(sample_data)
    print "{}: sample data: part 1 = {}".format(time.time() - t0, part_1_answer)
    t0 = time.time()
    part_2_answer = part_2(sample_data)
    print "{}: sample data: part 2 = {}".format(time.time() - t0, part_2_answer)

    if DEBUGGING: sys.exit(0)

    input_data = process_input_data(open(__file__.rsplit('.')[0] + '.input').read())

    t0 = time.time()
    part_1_answer = part_1(input_data)
    print "{}: input data: part 1 = {}".format(time.time() - t0, part_1_answer)
    t0 = time.time()
    part_2_answer = part_2(input_data)
    print "{}: input data: part 2 = {}".format(time.time() - t0, part_2_answer)
