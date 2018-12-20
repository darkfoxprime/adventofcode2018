
import re
import sys
import itertools
import time
import operator
import os.path

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

real_accumulate = accumulate
def debug_accumulate(iterable, func = operator.add):
    def debug(state, value):
        print >> sys.stderr, ">>accumulate<< element={!r}".format(value)
        return func(state, value)
    for state in real_accumulate(iterable, debug):
        print >> sys.stderr, ">>accumulate<< state={!r}".format(state)
        yield state
    print >> sys.stderr, ">>accumulate<< done"

if DEBUGGING:

    print >> sys.stderr, "Debugging version of `accumulate` enabled"
    accumulate = debug_accumulate

########################################################################
#
# The dictionary of lambdas that process the instructions
#
# Each instruction lambda accepts a hash of registers and a list of 4
# integers representing the instruction.  The first instruction is the
# opcode, and is ignored; the other three are used to process the 
# instruction.  The lambda returns the new list of registers.
#
# These make use of a helper lambda called `replace_reg`, which replaces
# a register in a list of registers with a new value.
#
# A set of `directives` are also defined.  Syntactically, these are the
# same as `instructions`; semantically, they have an effect but do not
# change the instruction pointer.

replace_reg = lambda regs,reg,val: dict(regs.items() + [(reg,val)])

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

directives = {
            '#ip': lambda regs,inst: (
                    replace_reg(regs, 'ipr', inst[1])
                ),
        }

########################################################################
#
# Process input data to return the appropriate records or data format.
# In this case, simply split each line around spaces and convert all
# fields in each line but the first to integers.

process_input_data = lambda input_data: [
            [row[0]] + [int(field) for field in row[1:]]
            for line in input_data.split('\n')
            if len(line)
            for row in [line.split(' ')]
        ]

########################################################################
#
# Process directives and return the program and the initial registers.

process_program_directives = lambda init_regs, program_with_directives: (
            (
                program,
                reduce(
                    lambda regs, instr: (
                        directives[instr[0]](regs, instr)
                    )
                    ,
                    program_directives
                    ,
                    init_regs
                )
            )
            for program_directives in [
                list(
                    itertools.takewhile(
                        lambda instr: instr[0] in directives
                        ,
                        program_with_directives
                    )
                )
            ]
            for program in [
                list(
                    itertools.dropwhile(
                        lambda instr: instr[0] in directives
                        ,
                        program_with_directives
                    )
                )
            ]
        ).next()

########################################################################
#
# Process one instruction and return the new registers.
#
# Directives are processed at the beginning of the program.

process_one_instruction = lambda regs, instr: (
            regs_after_updating_ip
            for regs_after_storing_ipr in [
                replace_reg(regs, regs['ipr'], regs['ip'])
                if regs['ipr'] is not None
                else regs
            ]
            for regs_after_instruction in [
                instructions[instr[0]](regs_after_storing_ipr, instr)
            ]
            for regs_after_loading_ipr in [
                replace_reg(
                    regs_after_instruction,
                    'ip',
                    regs_after_instruction[
                        regs_after_instruction['ipr']
                    ]
                )
                if regs['ipr'] is not None
                else regs_after_instruction
            ]
            for regs_after_updating_ip in [
                replace_reg(
                    regs_after_loading_ipr,
                    'ip',
                    regs_after_loading_ipr['ip']+1
                )
            ]
        ).next()

########################################################################
#
# Part 1:   run the program until regs['ip'] is not in the program space
#
# Do this (of course) in an accumulator.
#
# Use `process_program_directives` to obtain the initial set of
# registers and the actual program.
#
# Run an accumulator to repeatedly process instructions.
#
# The iterator for the accumulator is a chain of the initial set of
# registers followed by an infinite counter.
#
# Each step of the accumulator runs `process_one_instruction` against
# the current registers and the instruction at program index
# `regs['ip']`.
#
# Run the accumulator through a `dropwhile` to drop register sets
# until `regs['ip']` is not between 0 (inclusive) and the length of
# the program (exclusive).
#
# Return the first register from the next result of the `dropwhile`.

part_1 = lambda input_data: (

            # use a generator expression to bind values to names
            (

# Run the accumulator through a `dropwhile` to drop register sets
# until `regs['ip']` is not between 0 (inclusive) and the length of
# the program (exclusive).

                itertools.dropwhile(
                    lambda regs: (
                        0 <= regs['ip'] < len(program)
                    )
                    ,

# Run an accumulator to repeatedly process instructions.

                    accumulate(

# The iterator for the accumulator is a chain of the initial set of
# registers followed by an infinite counter.

                        itertools.chain(
                            [regs]
                            ,
                            itertools.count(1)
                        )
                        ,

# Each step of the accumulator runs `process_one_instruction` against
# the current registers and the instruction at program index
# `regs['ip']`.

                        lambda regs, clock: (
                            dict(
                                process_one_instruction(
                                    regs,
                                    program[regs['ip']]
                                ).items()
                                +
                                [('clock',clock)]
                            )
                        )

                    ) # end of accumulate

# Return the first register from the next result of the `dropwhile`.

                ).next()[0]

# Use `process_program_directives` to obtain the initial set of
# registers and the actual program.

                for (program, regs) in [
                    process_program_directives(
                        dict([('ipr',None)] + [(reg,0) for reg in ['ip'] + range(6)])
                        ,
                        input_data
                    )
                ]

            ).next()

        )

########################################################################
#
# Part 2:   run the program until regs['ip'] is not in the program space
#
# Same as part 1, except the initial registers have a `1` in register `0`.

part_2 = lambda input_data: (

            # use a generator expression to bind values to names
            (

# Run the accumulator through a `dropwhile` to drop register sets
# until `regs['ip']` is not between 0 (inclusive) and the length of
# the program (exclusive).

                itertools.dropwhile(
                    lambda regs: (
                        0 <= regs['ip'] < len(program)
                    )
                    ,

# Run an accumulator to repeatedly process instructions.

                    accumulate(

# The iterator for the accumulator is a chain of the initial set of
# registers followed by an infinite counter.

                        itertools.chain(
                            [regs]
                            ,
                            itertools.count(1)
                        )
                        ,

# Each step of the accumulator runs `process_one_instruction` against
# the current registers and the instruction at program index
# `regs['ip']`.

                        lambda regs, clock: (
                            dict(
                                process_one_instruction(
                                    regs,
                                    program[regs['ip']]
                                ).items()
                                +
                                [('clock',clock)]
                            )
                        )

                    ) # end of accumulate

# Return the first register from the next result of the `dropwhile`.

                ).next()[0]

# Use `process_program_directives` to obtain the initial set of
# registers and the actual program.

                for (program, regs) in [
                    process_program_directives(
                        dict([('ipr',None)] + [(reg,0) for reg in ['ip'] + range(6)] + [(0,1)])
                        ,
                        input_data
                    )
                ]

            ).next()

        )

########################################################################
#
# Main controller

if __name__ == '__main__':

    base_filename = __file__.rsplit('.')[0]

    input_filename = '{}.input'.format(base_filename)
    input_data = open(input_filename).read()

    for sample_num in itertools.takewhile(lambda num:os.path.exists('{}.sample.{}'.format(base_filename, num)), itertools.count(1)):
        if DEBUGGING: break

        sample_filename = '{}.sample.{}'.format(base_filename, sample_num)
        sample_data = open(sample_filename).read()

        results_filename = '{}.sample.results.part1.{}'.format(base_filename, sample_num)
        expected = (
                    int(open(results_filename).read().strip())
                    if os.path.exists(results_filename)
                    else None
                )

        t = time.time()
        result = part_1(process_input_data(sample_data))
        t = time.time() - t
        print "{}: sample {}: part 1 = {}{}".format(t, sample_num, result, " (expected {})".format(expected) if result != expected else "")

    t = time.time()
    result = part_1(process_input_data(input_data))
    t = time.time() - t
    print "{}: input data: part 1 = {}".format(t, result)

    for sample_num in itertools.takewhile(lambda num:os.path.exists('{}.sample.{}'.format(base_filename, num)), itertools.count(1)):
        if DEBUGGING: break

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

