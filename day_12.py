
import re
import sys
import itertools
import time
import operator

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
        print >> sys.stderr, ">>accumulate<< initial state={0!r}".format(total)
        yield total
        for element in it:
            total = func(total, element)
            print >> sys.stderr, ">>accumulate<< state={0!r}".format(total)
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
# In this case:  The first line is parsed to the initial pattern, a `0`
# is inserted to indicate the pot number at which the initial pattern
# begins, and subsequent blank lines are parsed into a single compiled
# regular expression that matches all possible patterns that result in
# a full pot.
#
# The last part is accomplished by parsing each line into a `(pattern,
# result)` tuple, filtering out all tuples that do not have a result
# of `#`, convering the remaining patterns to valid regular expression
# patterns (by replacing `.` with `\.`), then joining them together with
# `|` and compiling the result into a regular expression.
#
# For example, if the input contained the following three patterns...
# ```
# .#..# => #
# #...# => .
# ##... => #
# ```
# this would get parsed into the tuples `('.#..#', '#')`, `('#...#', '.')`,
# and `('##...', '#')`; the list would get filtered to remove the `.` pattern,
# and the two remaining patterns would be converted to regular expressions and
# joined to produce `re.compile(r'\.#\.\.#|##\.\.\.')`.

re_initial = re.compile(r'''initial state: ([.#]+)''', re.I)
re_pattern = re.compile(r'''([.#]{5}) => ([.#])''')

process_input_data = lambda input_data: (
            # use the generator trick to be able to reference
            # the split of the input data in two places
            (
                re_initial.search(input_parts[0]).group(1)
                ,
                0
                ,
                re.compile(
                    '|'.join(
                        pattern.group(1).replace('.', '\\.')
                        for pattern in (
                            re_pattern.finditer(input_parts[1])
                        )
                        if pattern.group(2) == '#'
                    )
                )
            )
            for input_parts in [
                input_data.split('\n',1)
            ]
        ).next()

########################################################################
# Strip unoccupied cells (`.`) from the beginning and end of a cell
# string, and return the updated string and updated index of the first
# cell.
#
# If there are no occupied cells, return an empty string and the index `0`.

strip_unoccupied_cells = lambda (cells, index): (
            cells.strip('.')
            ,
            index + len(cells) - len(cells.lstrip('.'))
            if '#' in cells
            else 0
        )

########################################################################
#
# Process one generation of the cellular automata described by the input.
#
# The input consists of:
#     The string of the current generation of cells,
#     the index number of the first cell in the string,
#     and the replacement patterns.
#
# The output consists of:
#     The string of the next generation of cells,
#     the index number of the first cell in the new generation,
#     and the replacement patterns.
#
# Assumption:  There will never be a pattern that converts an unoccupied
# cell surrounded by unoccupied cells on both sides (i.e. `.....`) to an
# occupied cell (`#`).  Otherwise, there would be an infinite number of
# occupied cells at either end.
#
# The algorithm is:
#
#     1)  Add 4 unoccupied cells to the beginning and end of the string,
#         to ensure the cells can grow outward.
#
#     2)  Loop through each `index` from 2 up to 2 less than the length
#         of the new string.
#     
#     3)  At each index, process the string from `index - 2` through
#         (and including) `index + 2` against the patterns.  If any
#         pattern matched, return `#`; otherwise, return `.`.
#
#     4)  Join the results of the index loop above into a single string.
#
#     5)  Pass the joined string through `strip_unoccupied_cells` with
#         a starting index of the original index - 2.

process_one_generation = lambda (current_cells, current_index, patterns): (
            strip_unoccupied_cells(
                (
                    ''.join(
                        '#'
                        if patterns.match(
                            extended_cells[index-2 : index+3]
                        )
                        else '.'
                        for extended_cells in [
                            '....{}....'.format(current_cells)
                        ]
                        for index in range(2, len(current_cells) + 6)
                    )
                    ,
                    current_index - 2
                )
            )
            + (patterns,)
        )

########################################################################
#
# Part 1:   Process N (default 20) generations of the cellular automata,
#           and return the sum of the indexes which are full (`#`).

part_1 = lambda input_data, N=20: (
            sum(
                index + first_index
                for (cell_string, first_index, _) in [
                    reduce(
                        lambda current_generation, generation_number: (
                            process_one_generation(current_generation)
                        )
                        ,
                        range(N)
                        ,
                        input_data
                    )
                ]
                for index in range(len(cell_string))
                if cell_string[index] == '#'
            )
        )

########################################################################
#
# Part 2:   Process at most `N` (defaulting to 50 billion) generations
#           of input data, but stop when a subsequent generation is
#           equal to the previous generation; calculate what the final
#           generation will look like based on the that; and return the
#           sum of the location of the occupied cells.
#
# Do this through a generator expression that counts up generations and
# produces the current generation _and_ the previous generation.  Run
# that through `itertools.dropwhile` to drop the generations that are
# changing (not counting the starting index).  Then take the next
# generation, figure out what the final starting index will be for
# generation 'N' based on the next generation's generation number and
# on how next generation's index varied from the previous generation's,
# and sum the pots based on that.

part_2 = lambda input_data, N = 50000000000: (
            sum(
                index + final_index
                for (next_gen, gen_num, prev_gen) in [
                    itertools.dropwhile(
                        lambda (cur_gen, gen_num, prev_gen): (
                            gen_num < N
                            and cur_gen[0] != prev_gen[0]
                        )
                        ,
                        accumulate(
                            itertools.chain(
                                [(input_data, 0, [None])]
                                ,
                                itertools.count(1)
                            )
                            ,
                            lambda (cur_gen, gen_num, prev_gen), next_gen_num: (
                                (process_one_generation(cur_gen), next_gen_num, cur_gen)
                            )
                        )
                    ).next()
                ]
                for final_index in [
                    next_gen[1] + (next_gen[1] - prev_gen[1]) * (N - gen_num)
                ]
                for index in range(len(next_gen[0]))
                if next_gen[0][index] == '#'
            )
        )

if __name__ == '__main__':

    sample_data = process_input_data(open(__file__.rsplit('.')[0] + '.sample').read())

    t = time.time()
    result = part_1(sample_data)
    t = time.time() - t
    print "{}: sample data: part 1 = {}".format(t, result)

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

