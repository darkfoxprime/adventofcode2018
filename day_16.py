
import re
import sys
import itertools
import time
import operator
import os.path

DEBUGGING = False

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
            print >> sys.stderr, ">>accumulate<< element={0!r}".format(element)
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
# In this case, the input data is processed into a tuple consisting of
# a list of samples and a test program.
#
# Each sample consists of a `Before` list of 4 register values,
# an instruction of 4 integers,
# and an `After` list of 4 register values.
#
# Do this using a regular expression (of course) and list comprehension
# (of course):
#
#     Split the input data using this RE:
#     (line breaks are for readability only and are not included in the
#     real RE)
#         ```
#         Before: +(\[[^]]+\])
#         \r?\n\r?
#         ([0-9]+ [0-9]+ [0-9]+ [0-9]+)
#         \r?\n\r?
#         After: +(\[[^]]+\])
#         ```
#
#     This will result in a list of...
#         ```
#         [garbage, before, instr, after, garbage, before, instr, after, ...]
#         ```
#
#     Use a generator expression to bind the split input list to `input_list`.
#
#     Then use two list comprehensions to return the tuple:
#
#         The first list comprehension, the samples, consists of:
#
#             `i` looping over the range of indices in `input_list`
#             starting at 1 and stepping by 4,
#
#             And return a tuple that evaluates the `Before` and `After`
#             strings directly into lists, and parses the instruction
#             string by splitting it around spaces and mapping the
#             resulting values through `int`.
#
#        The second list comprehension, the test program, consist of:
#
#            `instr` looping over the last item in `input_list`, split
#            by newlines (`\n`)
#
#            Returning a tuple of `instr`, stripped and split around
#            spaces, and mapped through `int`
#
#            Only if `instr` (after being stripped) is not empty.

process_input_data = lambda input_data: (
            # generator expression to bind values to names
            (
                (
                    [
                        (
                            eval(input_list[i])
                            ,
                            tuple(int(op) for op in input_list[i+1].split())
                            ,
                            eval(input_list[i+2])
                        )
                        for i in range(1, len(input_list), 4)
                    ]
                    ,
                    [
                        tuple(int(op) for op in instr.strip().split())
                        for instr in input_list[-1].split('\n')
                        if instr.strip()
                    ]
                )
                for input_list in [
                    re.split(
                        r'Before: +(\[[^]]+\])'
                        + r'\r?\n\r?'
                        + r'([0-9]+ [0-9]+ [0-9]+ [0-9]+)'
                        + r'\r?\n\r?'
                        + r'After: +(\[[^]]+\])'
                        ,
                        input_data
                    )
                ]
            ).next()
        )

########################################################################
#
# The dictionary of lambdas that process the instructions
#
# Each instruction lambda accepts a list of registers and a list of 4
# integers representing the instruction.  The first instruction is the
# opcode, and is ignored; the other three are used to process the 
# instruction.  The lambda returns the new list of registers.
#
# These make use of a helper lambda called `replace_reg`, which replaces
# a register in a list of registers with a new value.

replace_reg = lambda regs,reg,val: regs[:reg] + [val] + regs[reg+1:]

instructions = {
    'addr': lambda regs,inst: (
            replace_reg(regs, inst[3], regs[inst[1]] + regs[inst[2]])
        ),
    'addi': lambda regs,inst: (
            replace_reg(regs, inst[3], regs[inst[1]] + inst[2])
        ),
    'mulr': lambda regs,inst: (
            replace_reg(regs, inst[3], regs[inst[1]] * regs[inst[2]])
        ),
    'muli': lambda regs,inst: (
            replace_reg(regs, inst[3], regs[inst[1]] * inst[2])
        ),
    'banr': lambda regs,inst: (
            replace_reg(regs, inst[3], regs[inst[1]] & regs[inst[2]])
        ),
    'bani': lambda regs,inst: (
            replace_reg(regs, inst[3], regs[inst[1]] & inst[2])
        ),
    'borr': lambda regs,inst: (
            replace_reg(regs, inst[3], regs[inst[1]] | regs[inst[2]])
        ),
    'bori': lambda regs,inst: (
            replace_reg(regs, inst[3], regs[inst[1]] | inst[2])
        ),
    'setr': lambda regs,inst: (
            replace_reg(regs, inst[3], regs[inst[1]])
        ),
    'seti': lambda regs,inst: (
            replace_reg(regs, inst[3], inst[1])
        ),
    'gtir': lambda regs,inst: (
            replace_reg(regs, inst[3], 1 if inst[1] > regs[inst[2]] else 0)
        ),
    'gtri': lambda regs,inst: (
            replace_reg(regs, inst[3], 1 if regs[inst[1]] > inst[2] else 0)
        ),
    'gtrr': lambda regs,inst: (
            replace_reg(regs, inst[3], 1 if regs[inst[1]] > regs[inst[2]] else 0)
        ),
    'eqir': lambda regs,inst: (
            replace_reg(regs, inst[3], 1 if inst[1] == regs[inst[2]] else 0)
        ),
    'eqri': lambda regs,inst: (
            replace_reg(regs, inst[3], 1 if regs[inst[1]] == inst[2] else 0)
        ),
    'eqrr': lambda regs,inst: (
            replace_reg(regs, inst[3], 1 if regs[inst[1]] == regs[inst[2]] else 0)
        ),
}

########################################################################
#
# test_instructions:
#
# Inputs:     A sample
# Output:     The list of instruction names which produce the correct
#             results based on the sample.
#
# This is a simple list comprehension processed over the items of the
# `instructions` dictionary.
#
# Return the instruction name if the results of running the instruction
# lambda against the sample's instruction and "before" registers
# matches the samples' "after" registers.

test_instructions = lambda sample: (
            [
                name
                for (name, instr) in instructions.items()
                if instr( sample[0], sample[1] ) == sample[2]
            ]
        )

########################################################################
#
# Part 1:   Return the number of samples which behave like 3 or more
#           instructions.
#
# This is a `sum` over a simple generator run against the samples list.
#
# The generator returns `1` for each sample for which `test_instructions`
# reports 3 or more instructions that match the sample.

part_1 = lambda input_data: (
            sum(
                1
                for sample in input_data[0]
                if len(test_instructions(sample)) >= 3
            )
        )

########################################################################
#
# identify_opcodes:
#
# Inputs:     The list of samples.
# Output:     A list of instruction names in opcode order (such that
#             index 0 is the instruction name for opcode 0, etc.)
#
# Do this as a reduction using a bunch of set intersections to narrow
# down each instruction.
#
# The state of the reduction is a list (ordered/indexed by opcode) of
# sets of the possible instruction names for that opcode.
#
# The initial state of the reduction is a list of sets of _all_
# instruction names, one for each instruction.
#
# The reduction runs against each sample.
#
# For each sample, return a new list of sets, with the current opcode's
# set being the intersection of the previous set with the set of
# instruction names returned by `test_instructions`.
#
# When the reduction completes, run the result through an accumulator to
# remove each identified instruction from the possible sets of all other
# opcodes.
#
# The accumulator state is the list of instruction names -or- sets of
# possible names.
#
# The initial state is the list of instruction sets as returned from
# the reduction.
#
# The accumulator runs against an infinite counter (which is ignored).
#
# The accumulator is filtered through a `dropwhile) which filters out
# any state which contains any set of length 1.
#
# The accumulator runs a two-phase process on the list of instruction
# sets, ignoring the counter.
#
# The first phase replaces any single-item set with the contents of
# the set, ignoring multi-item sets and non-sets.
#
# The second phase generates a set containing all the non-set items
# in the list of instruction sets, then removes the contents of that set
# from each set in the list of instruction sets.
#
# Return the next list returned from the `dropwhile` iterator.

identify_opcodes = lambda sample_list: (

# The accumulator is filtered through a `dropwhile` which filters out
# any state which contains any set of length 1.

            itertools.dropwhile(
                lambda instruction_sets: (
                    max(
                        isinstance(instruction, set) and len(instruction) == 1
                        for instruction in instruction_sets
                    )
                )
                ,

# When the reduction completes, run the result through an accumulator to
# remove each identified instruction from the possible sets of all other
# opcodes.

                accumulate(

# The accumulator state is the list of instruction names -or- sets of
# possible names.
#
# The initial state is the list of instruction sets as returned from
# the reduction.

                    itertools.chain(
                        [

# Do this as a reduction using a bunch of set intersections to narrow
# down each instruction.

                            reduce(

# For each sample, return a new list of sets, with the current opcode's
# set being the intersection of the previous set with the set of
# instruction names returned by `test_instructions`.

                                lambda instruction_sets, sample: (
                                    instruction_sets[:sample[1][0]]
                                    + [
                                        instruction_sets[sample[1][0]]
                                        & set(test_instructions(sample))
                                    ]
                                    + instruction_sets[sample[1][0]+1:]
                                )
                                ,

# The reduction runs against each sample.

                                sample_list
                                ,

# The state of the reduction is a list (ordered/indexed by opcode) of
# sets of the possible instruction names for that opcode.
#
# The initial state of the reduction is a list of sets of _all_
# instruction names, one for each instruction.

                                [
                                    set(instructions.keys())
                                    for instruction in instructions.keys()
                                ]

                            )
                        ]
                        ,

# The accumulator runs against an infinite counter (which is ignored).

                        itertools.count(1)
                    )
                    ,

# The accumulator runs a two-phase process on the list of instruction
# sets, ignoring the counter.

                    lambda instruction_sets, _: (

                    # generator expression to process the two phases
                        (

#                              ... then removes the contents of that set
# from each set in the list of instruction sets.

                            [
                                (instruction_set - known_instructions)
                                if isinstance(instruction_set, set)
                                else instruction_set
                                for instruction_set in phase_1
                            ]

# The first phase replaces any single-item set with the contents of
# the set, ignoring multi-item sets and non-sets.

                            for phase_1 in [
                                [
                                    instruction_set.pop()
                                    if isinstance(instruction_set, set)
                                    and len(instruction_set) == 1
                                    else instruction_set
                                    for instruction_set in instruction_sets
                                ]
                            ]

# The second phase generates a set containing all the non-set items
# in the list of instruction sets ...

                            for known_instructions in [
                                set(
                                    instruction_set
                                    for instruction_set in phase_1
                                    if not isinstance(instruction_set, set)
                                )
                            ]

                        ).next() # end of two-phase lambda generator

                    ) # end of two-phase lambda
                ) # end of instruction accumulator
            ).next() # end of dropwhile
        ) # end of `identify_opcodes`

########################################################################
#
# Part 2:   Determine the value of register 0 after executing the
#           test program.
#
# Pass the samples into `identify_opcodes` to generate the mapping
# between opcode and instruction.
#
# Process the opcode mapping to map opcodes with instruction lambdas.
#
# Bind the opcode mapping to `opcodes` through a generator expression.
#
# Then process the test program using a reduction.
#
# The state of the reduction is the register set.
#
# The initial state of the reduction is `[0,0,0,0]`
#
# Process each instruction of the test program by calling the instruction
# lambda in the opcodes mapping for the first opcode in the instruction
# and passing in the current registers and the instruction.
#
# Return the first register of the result of the generator expression.

part_2 = lambda input_data: (

# Bind the opcode mapping to `opcodes` through a generator expression.
            (

# Then process the test program using a reduction.
# The state of the reduction is the register set.

                reduce(

# Process each instruction of the test program by calling the instruction
# lambda in the opcodes mapping for the first opcode in the instruction
# and passing in the current registers and the instruction.

                    lambda registers, instruction: (
                        opcodes[instruction[0]](registers, instruction)
                    )
                    ,

                    input_data[1]
                    ,

# The initial state of the reduction is `[0,0,0,0]`

                    [0,0,0,0]

                )

# Bind the opcode mapping to `opcodes` through a generator expression.
                for opcodes in [
                    [
                        instructions[instruction]
                        for instruction in identify_opcodes(input_data[0])
                    ]
                ]

# Return the first register of the result of the generator expression.
            ).next()[0]

        )

########################################################################
#
# Main controller

if __name__ == '__main__':

    base_filename = __file__.rsplit('.')[0]

    input_filename = '{}.input'.format(base_filename)
    input_data = process_input_data(open(input_filename).read())

    for sample_num in itertools.takewhile(lambda num:os.path.exists('{}.sample.{}'.format(base_filename, num)), itertools.count(1)):

        sample_filename = '{}.sample.{}'.format(base_filename, sample_num)
        sample_data = process_input_data(open(sample_filename).read())

        results_filename = '{}.sample.results.part1.{}'.format(base_filename, sample_num)
        expected = (
                    int(open(results_filename).read().strip())
                    if os.path.exists(results_filename)
                    else None
                )

        t = time.time()
        result = part_1(sample_data)
        t = time.time() - t
        print "{}: sample {}: part 1 = {}{}".format(t, sample_num, result, " (expected {})".format(expected) if result != expected else "")

        if DEBUGGING: sys.exit(0)

    t = time.time()
    result = part_1(input_data)
    t = time.time() - t
    print "{}: input data: part 1 = {}".format(t, result)

    for sample_num in itertools.takewhile(lambda num:os.path.exists('{}.sample.{}'.format(base_filename, num)), itertools.count(1)):

        sample_filename = '{}.sample.{}'.format(base_filename, sample_num)
        sample_data = process_input_data(open(sample_filename).read())

        results_filename = '{}.sample.results.part2.{}'.format(base_filename, sample_num)
        expected = (
                    int(open(results_filename).read().strip())
                    if os.path.exists(results_filename)
                    else None
                )

        t = time.time()
        result = part_2(sample_data)
        t = time.time() - t
        print "{}: sample {}: part 2 = {}{}".format(t, sample_num, result, " (expected {})".format(expected) if result != expected else "")

        if DEBUGGING: sys.exit(0)

    t = time.time()
    result = part_2(input_data)
    t = time.time() - t
    print "{}: input data: part 2 = {}".format(t, result)

