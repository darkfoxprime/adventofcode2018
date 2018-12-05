
import re
import sys
import itertools

def process_input_data(input_data):
    return input_data.strip()

def part_1(input_data):
    # use a reduce on the input polymer to form the output polymer.
    # At each step, if the end of the reducing polymer matches opposite polarity of the next unit, remove the end of the reducing polymer; otherwise append the next unit.
    # initialize with a '.' so as to always have a non-reacting unit
    # return the length of the resulting polymer (minus one, to account for the initial '.')
    return len(
                reduce(
                    lambda polymer, unit:
                        polymer[:-1]
                        if polymer[-1].lower() == unit.lower() and polymer[-1] != unit
                        else polymer + unit
                    ,
                    input_data
                    ,
                    '.'
                )
            )-1

def part_2(input_data):
    # use the same reduce from part (a)
    # with the exception of ignoring any unit that matches a
    # `unit_to_remove` found from the set of all lowercase units in the input data
    # return the minimum length of all polymers generated from all such `unit_to_remove`s
    return min(
                len(
                    reduce(
                        lambda polymer, unit:
                            polymer if unit.lower() == unit_to_remove
                            else
                                polymer[:-1]
                                if polymer[-1].lower() == unit.lower() and polymer[-1] != unit
                                else
                                    polymer + unit
                        ,
                        input_data
                        ,
                        '.'
                    )
                )-1
                for unit_to_remove in set(x.lower() for x in input_data)
            )

if __name__ == '__main__':

    sample_data = process_input_data(open(__file__.rsplit('.')[0] + '.sample').read())

    print "sample data: part 1 = {}".format(part_1(sample_data))
    print "sample data: part 2 = {}".format(part_2(sample_data))

    input_data = process_input_data(open(__file__.rsplit('.')[0] + '.input').read())

    print "real input: part 1 = {}".format(part_1(input_data))
    print "real input: part 2 = {}".format(part_2(input_data))
