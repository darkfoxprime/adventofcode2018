
import re
import sys
import itertools
import time
import operator
import os.path
import pprint

run_part_1 = True
run_part_2 = True
run_samples = True
run_data = True

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

real_accumulate = accumulate
def debug_accumulate(iterable, func = operator.add):
    def debug(state, value):
        print >> sys.stderr, ">>accumulate<< element={!r}".format(value)
        return func(state, value)
    for state in real_accumulate(iterable, debug):
        print >> sys.stderr, ">>accumulate<< state={!r}".format(state)
        yield state
    print >> sys.stderr, ">>accumulate<< done"

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

if DEBUGGING:

    print >> sys.stderr, "Debugging version of `accumulate` enabled"

    accumulate = debug_accumulate

def debug_value(prefix, value):
    print >> sys.stderr, '{}{}'.format(prefix, value)
    return value

########################################################################
#
# Process input data to return the appropriate records or data format.
#
# The input data is in two sections; the first section begins `Immune
# System:` and the second begins `Infection:`
#
# Within each section, not counting blank lines, each line is of the
# form:
# ```
# <#> units each with <#> hit points
# (immune to <type>,<type>...; weak to <type>,<type>...)
# with an attack that does # <type> damage at initiative <#>
# ```
# Immunities and weaknesses are optional, and the entire () phrase
# will be omitted if a unit has neither immunities nor weaknesses.
#
# Process this into two lists of unit groups.
# Each unit group is represented by a tuple of:
# ```
# (#units, #hp, #damage, dmgtype, #init, {dmgtype:multiplier...})
# ```
# where `#units` is the number of units in the group,
# `#hp` is the number of hit points each unit has,
# `#damage` is the amount of damage each unit inflicts,
# `dmgtype` is the type of damage the unit inflicts,
# `#init` is the initiative of the group,
# and the dictionary maps a damage type to a multiplier,
# either `0` (for immunities) or `2` (for weaknesses).
#
# Begin by splitting the input around `Infection:`.
# Each section is then parsed by a regular expression `findall`
# for this expression (unfortunately, named groups don't have
# special meaning in findall, so they're just normal groups
# that we will have to reference by number later).
# This matches the numbers within the pattern, plus optionally
# the () phrase with either `immune to` or `weak to` parts,
# or both with a `;` between.
# ```
# r'(\d+)\s+units\s+each\s+with\s+(\d+)\s+hit\s+points\s+'
# + r'(?:\(\s*'
#     + r'(?:'
#         + r'(?:'
#             + r'(?:immune\s+to\s+(\w+(?:\s*,\s*\w+)*)\s*)'
#             + r'|'
#             + r'(?:weak\s+to\s+(\w+(?:\s*,\s*\w+)*)\s*)'
#         + r')'
#         + r';?\s*'
#     + r')+'
# + r'\)\s+)?'
# + r'with\s+an\s+attack\s+that\s+does\s+'
# + r'(\d+)\s+(\w+)\s+damage\s+'
# + r'at\s+initiative\s+(\d+)'
# ```
#
# Each match produced by that expression must be further parsed
# into a tuple of:
# ```
# (
#     int(m[0]), # number of units
#     int(m[1]), # hp per unit
#     int(m[4]), # attack value per unit
#     m[5],      # attack type
#     int(m[6]), # group initiative
#     dict(
#         [
#             (immunity.strip(), 0)
#             for immunity in m[2].split(',')
#             if immunity.strip()
#         ] + [
#             (weakness.strip(), 2)
#             for weakness in m[3].split(',')
#             if weakness.strip()
#         ]
#     )
# )
# ```
#
# The two sections of groups are then returned in a tuple.

process_input_data = lambda input_data: (
            tuple(
                list(
                    (
# [0] number of units
                        int(m[0]),
# [1] hp per unit
                        int(m[1]),
# [2] attack value per unit
                        int(m[4]),
# [3] attack type
                        m[5],
# [4] group initiative
                        int(m[6]),
# [5] effective power of the group
                        int(m[0]) * int(m[4]),
# [6] dictionary of attack modifiers
                        dict(
                            [
                                (immunity.strip(), 0)
                                for immunity in m[2].split(',')
                                if immunity.strip()
                            ] + [
                                (weakness.strip(), 2)
                                for weakness in m[3].split(',')
                                if weakness.strip()
                            ]
                        )
                    )
                    for m in re.findall(
                        r'(\d+)\s+units\s+each\s+with\s+(\d+)\s+hit\s+points\s+'
                        + r'(?:\(\s*'
                            + r'(?:'
                                + r'(?:'
                                    + r'(?:immune\s+to\s+(\w+(?:\s*,\s*\w+)*)\s*)'
                                    + r'|'
                                    + r'(?:weak\s+to\s+(\w+(?:\s*,\s*\w+)*)\s*)'
                                + r')'
                                + r';?\s*'
                            + r')+'
                        + r'\)\s+)?'
                        + r'with\s+an\s+attack\s+that\s+does\s+'
                        + r'(\d+)\s+(\w+)\s+damage\s+'
                        + r'at\s+initiative\s+(\d+)'
                        ,
                        section
                    )
                )
                for section in
                input_data.split('Infection:')
            )
        )

########################################################################
#
# Process one round of battle
#
# This is a pair of reductions across all the groups in battle.
#
# First, generate an ordered list of units in the form
# `(side, group, effective_power, initiative)`,
# where
#     * `side` is 0 or 1,
#     * `group` is the group number (starting at `0`) on that side,
#     * `effective_power` is the effective power of the group.
#     * and `initiative` is the initiative of that group.
# The list is sorted from highest effective power to lowest, and
# from highest initiative to lowest within equal effective powers.
#
# The first reduction, against the ordered list of units, identifies
# the target for each unit and builds a new list of units in the
# form `(side, group, initiative, defending_group)`.
#
# The initial state of the reduction is an empty list.
#
# Run the reduction against the ordered list of units.
#
# At each step of the reduction,
#
#     Bind `attacking_unit` to the tuple for the unit being regarded:
#         `combat_data[unit_ref[0]][unit_ref[1]]`
#
#     Sort...
#         the set of units available to be attacked
#             by the product of the attacker's effective power and the
#             defender's attack modifier vs the attacker's attack type
#             (defaulting to 1 if the defender has no modifier)
#             then by the defender's effective power
#             then by the defender's initiative
#         filtered by those units whose
#             side is not equal to the attacker's side
#             effective power is greater than 0
#             and attack modifier vs the attacker's attack type != 0
#     And bind this to `defenders`.
#
#     If no defenders are available,
#         return the unchanged list of units and targets.
#     Otherwise
#         return the list of units and targets with a new unit added,
#         using the side, group, and initiative from the unit being
#         regarded, and the defending_group from the first unit of
#         `defenders`.
#
# Bind the results of the first reduction to `attacker_targets`.
#
# Sort `attacker_targets` by initiative, from highest to lowest,
# and bind that to `attacker_order`.
#
# The second reduction, run against `attacker_order`,
# performs the actual attacks.
#
# The initial state of the reduction is the input data of groups.
#
# For each step of the reduction,
#
#     Bind `attacking_unit` to the tuple for the unit being regarded:
#         `combat_data[unit_ref[0]][unit_ref[1]]`
#
#     Bind `defending_unit` to the tuple for the defender:
#         `combat_data[1-unit_ref[0]][unit_ref[3]]`
#
#     Bind `actual_attack` to the actual attack power for the unit
#     vs the defender:
#         ```
#         attacking_unit[0]
#         * attacking_unit[2]
#         * defending_unit[6].get(attacking_unit[3], 1)
#         ```
#
#     Bind `surviving_defenders` to the number of defenders left
#     after the attack:
#         ```
#         max(
#             0,
#             defending_unit[0]
#             - (actual_attack // defending_unit[1])
#         )
#         ```
#
#     Return the new state with the modified defender.
#     The defender's side is `1-unit[0]`, and the
#     defender's group number is `unit[3]`.
#         ```
#         state[:1-unit[0]]
#         + (
#             state[1-unit[0]][:unit[3]]
#             + [
#                 (
#                     surviving_defenders
#                     ,
#                     defending_unit[1]
#                     ,
#                     defending_unit[2]
#                     ,
#                     defending_unit[3]
#                     ,
#                     defending_unit[4]
#                     ,
#                     surviving_defenders * defending_unit[2]
#                     ,
#                     defending_unit[6]
#                 )
#             ]
#             + state[1-unit[0]][unit[3]+1:]
#             , # required to make the surrounding () into a tuple
#         )
#         + state[2-unit[0]:]
#         ```

process_one_round = lambda combat_data: (
            # generator expression to bind names to values
            (

# The second reduction, run against `attacker_order`,
# performs the actual attacks.

                reduce(

# For each step of the reduction,

                    lambda combat_data, attacker: ( # generator expression

#     Return the new state with the modified defender.
#     The defender's side is `1-unit[0]`, and the
#     defender's group number is `unit[3]`.
#         ```
#         state[:1-unit[0]]
#         + (
#             state[1-unit[0]][:unit[3]]
#             + [
#                 (
#                     surviving_defenders
#                     ,
#                     defending_unit[1]
#                     ,
#                     defending_unit[2]
#                     ,
#                     defending_unit[3]
#                     ,
#                     defending_unit[4]
#                     ,
#                     surviving_defenders * defending_unit[2]
#                     ,
#                     defending_unit[6]
#                 )
#             ]
#             + state[1-unit[0]][unit[3]+1:]
#             , # required to make the surrounding () into a tuple
#         )
#         + state[2-unit[0]:]
#         ```

                        (
                            combat_data[:1-attacker[0]]
                            + (
                                combat_data[1-attacker[0]][:attacker[3]]
                                + [
                                    (
                                        surviving_defenders
                                        ,
                                        defending_unit[1]
                                        ,
                                        defending_unit[2]
                                        ,
                                        defending_unit[3]
                                        ,
                                        defending_unit[4]
                                        ,
                                        surviving_defenders * defending_unit[2]
                                        ,
                                        defending_unit[6]
                                    )
                                ]
                                + combat_data[1-attacker[0]][attacker[3]+1:]
                                , # required to make the surrounding () into a tuple
                            )
                            + combat_data[2-attacker[0]:]
                        )

#     Bind `attacking_unit` to the tuple for the unit being regarded:
#         `combat_data[unit_ref[0]][unit_ref[1]]`

                        for attacking_unit in [

                            combat_data[attacker[0]][attacker[1]]
                        ]

#     Bind `defending_unit` to the tuple for the defender:
#         `combat_data[1-unit_ref[0]][unit_ref[3]]`

                        for defending_unit in [
                            combat_data[1-attacker[0]][attacker[3]]
                        ]

#     Bind `actual_attack` to the actual attack power for the unit
#     vs the defender: The # of attacking units, multiplied by the
#     attack value, multiplied by the defender's modifier against
#     the attacker's attack type (defaulting to 1).
#         ```
#         attacking_unit[0]
#         * attacking_unit[2]
#         * defending_unit[6].get(attacking_unit[3], 1)
#         ```

                        for actual_attack in [
                            attacking_unit[0]
                            * attacking_unit[2]
                            * defending_unit[6].get(attacking_unit[3], 1)
                        ]

#     Bind `surviving_defenders` to the number of defenders left
#     after the attack:
#         ```
#         max(
#             0,
#             defending_unit[0]
#             - (actual_attack // defending_unit[1])
#         )
#         ```

                        for surviving_defenders in [
                            max(
                                0,
                                defending_unit[0]
                                - (actual_attack // defending_unit[1])
                            )
                        ]

                    ).next() # generator expression

                    ,

# The second reduction, run against `attacker_order`,

                    attacker_order
                    ,

# The initial state of the reduction is the input data of groups.

                    combat_data
                )

# First, generate an ordered list of units in the form
# `(side, group, effective_power, initiative)`,
# where
#     * `side` is 0 or 1,
#     * `group` is the group number (starting at `0`) on that side,
#     * `effective_power` is the effective power of the group.
#     * and `initiative` is the initiative of that group.
# The list is sorted from highest effective power to lowest, and
# from highest initiative to lowest within equal effective powers.

                for ordered_units in [
                    sorted(
                        (
                            (
                                side,
                                group,
                                combat_data[side][group][5] ,
                                combat_data[side][group][4]
                            )
                            for side in range(len(combat_data))
                            for group in range(len(combat_data[side]))
                        )
                        ,
                        key = lambda unit_ref: unit_ref[2:]
                        ,
                        reverse = True
                    )
                ]

# Bind the results of the first reduction to `attacker_targets`.

                for attacker_targets in [

# The first reduction, against the ordered list of units, identifies
# the target for each unit and builds a new list of units in the
# form `(side, group, initiative, defending_group)`.

                    reduce(

# At each step of the reduction,

                        lambda unit_targets, attacker: ( # generator expression

#         return the unchanged list of units and targets.

                            unit_targets

#     If no defenders are available,

                            if len(defenders) == 0

#     Otherwise

                            else

#         return the list of units and targets with a new unit added,

                            unit_targets + [
                                (

#         using the side, group, and initiative from the unit being
#         regarded, and the defending_group from the first unit of
#         `defenders`.

                                    attacker[0]
                                    ,
                                    attacker[1]
                                    ,
                                    attacker[3]
                                    ,
                                    defenders[0][1]
                                )
                            ]

#     Bind `attacking_unit` to the tuple for the unit being regarded:
#         `combat_data[unit_ref[0]][unit_ref[1]]`

                            for attacking_unit in [
                                combat_data[attacker[0]][attacker[1]]
                            ]

#     Sort...
#         the set of units available to be attacked
#             by the product of the attacker's effective power and the
#             defender's attack modifier vs the attacker's attack type
#             (defaulting to 1 if the defender has no modifier)
#             then by the defender's effective power
#             then by the defender's initiative
#         filtered by those units whose
#             side is not equal to the attacker's side
#             effective power is greater than 0
#             and attack modifier vs the attacker's attack type != 0
#     And bind this to `defenders`.

                            for defenders in [
                                sorted(
                                    (
                                        defender
                                        for defender in ordered_units
                                        if defender[0] != attacker[0]
                                        for defending_unit in [
                                            combat_data[defender[0]][defender[1]]
                                        ]
                                        if defending_unit[0] > 0
                                        and defending_unit[6].get(attacking_unit[3],1) > 0
                                        and defender[1] not in (
                                            unit[3] for unit in unit_targets
                                            if unit[0] != defender[0]
                                        )
                                    )
                                    ,
                                    key = lambda defender: (
                                        attacking_unit[5]
                                        * combat_data[defender[0]][defender[1]][6].get(attacking_unit[3],1)
                                        ,
                                        combat_data[defender[0]][defender[1]][5]
                                        ,
                                        combat_data[defender[0]][defender[1]][4]
                                    )
                                    ,
                                    reverse = True
                                )
                            ]

                        ).next() # generator expression
                        ,

# The first reduction, against the ordered list of units...

                        (
                            attacker
                            for attacker in ordered_units
                            if combat_data[attacker[0]][attacker[1]][0]
                        )
                        ,

# The initial state of the reduction is an empty list.

                        list()
                    )
                ]

# Sort `attacker_targets` by initiative, from highest to lowest,
# and bind that to `attacker_order`.

                for attacker_order in [
                    sorted(
                        attacker_targets
                        ,
                        key = lambda attacker: attacker[2]
                        ,
                        reverse = True
                    )
                ]

            ).next()
        )

########################################################################
#
# combat_results
#
# Repeatedly call `process_one_round` until the max hp on one or the
# other side is 0.
#
# Do this with an accumulator filtered through dropwhile.
#
# The dropwhile drops as long as the (a) the two sets of combat data
# are not equal, and (b) the lowest maximum-units-per-side is
# not 0.
# ```
# lambda combat_data, old_combat_data: (
#     (
#         combat_data != old_combat_data
#     ) and (
#         min(
#             max(group[0] for group in groups)
#             for groups in combat_data
#         )
#     )
# )
# ```
#
# The accumulator's state is a tuple of the current combat data and
# the previous round's combat data (so that the dropwhile can detect an
# infinite loop).
#
# The accumulator uses a chained iterator of the initial state (a tuple
# of the combat data and `None) followed by an infinite counter.
#
# Each step of the accumulator, it returns the updated combat data
# returned from `process_one_round` as well as the current combat data.
#
# When the `dropwhile` returns a value, return the sum of the unit counts
# for each side.

combat_results = lambda combat_data: (
            tuple(
                sum(
                    unit[0]
                    for unit in groups
                )
                for groups in (
                    itertools.dropwhile(
                        lambda new_and_old_combat_data: (
                            (
                                new_and_old_combat_data[0]
                                != new_and_old_combat_data[1]
                            ) and (
                                min(
                                    max(group[0] for group in groups)
                                    for groups in new_and_old_combat_data[0]
                                )
                            )
                        )
                        ,
                        accumulate(
                            itertools.chain(
                                [(combat_data, None)]
                                ,
                                itertools.count(1)
                            )
                            ,
                            lambda combat_data, _: (
                                (
                                    process_one_round(combat_data[0])
                                    ,
                                    combat_data[0]
                                )
                            )
                        )
                    ).next()
                )[0]
            )
        )

########################################################################
#
# boosted_combat_results
#
# Return combat results after boosting the immune system's attack values

boosted_combat_results = lambda combat_data, boost: (
            combat_results(
                (
                    [
                        group[0:2]
                        + (group[2] + boost,)
                        + group[3:5]
                        + ( (group[2] + boost) * group[0], )
                        + group[6:]
                        for group in combat_data[0]
                    ]
                    ,
                    combat_data[1]
                )
            )
        )

########################################################################
#
# Part 1: 
#
# Return the sum of the units returned by `combat_results`.

part_1 = lambda input_data: (
            sum(combat_results(input_data))
        )

########################################################################
#
# Part 2:   Determine the smallest value needed to add to the immune
#           system's attach values to ensure that it wins.
#
# This is an accumulation. (of course)
#
# The basic logic is to do a binary search to identify the minimal boost
# at which the immune system wins.  Because the upper bound is not known,
# an arbitrary upper bound is chosen, and the logic includes the condition
# to increase both the lower and upper bounds if the upper bound is not
# high enough.
#
# The state of the accumulation is a tuple of a lower value at which
# the immune system loses, and an upper value at which the immune system
# either wins or loses (this is the test value).
#
# The state starts out with the lower and upper values of (0,256).
#
# At each step of the accumulator,
#
#     Bind `boosted_results` to the boosted combat results from
#     feeding the combat data and the upper bound to `boosted_combat_results`.
#
#     If the combat results show the immune system winning ([0] > 0)
#     then the next state will be the same lower bound and a new upper
#     bound set at the midpoint between the lower and upper bound.
#
#     If the combat results sohw the immune system losing ([0] == 0)
#     then the next state will have the new lower bound set to the
#     upper bound, and the upper bound increased by the difference
#     between the bounds.
#
#     In both cases, also return the immune system survivors as the
#     third element in the state tuple.
#
# Filter the accumulator through a `dropwhile` that drops any state
# in which the lower bound and upper bound are not equal.
#
# When the dropwhile completes, return the immune system survivors.

part_2 = lambda input_data: (

# Filter the accumulator through a `dropwhile` that drops any state
# in which the lower bound and upper bound are not equal.

            itertools.dropwhile(
                lambda bounds: (bounds[0] != bounds[1])
                ,

# This is an accumulation. (of course)

                accumulate(

# The state of the accumulation is a tuple of a lower value at which
# the immune system loses, and an upper value at which the immune system
# either wins or loses (this is the test value).
#
# The state starts out with the lower and upper values of (0,256).

                    itertools.chain(
                        [(0,1)]
                        ,
                        itertools.count(0)
                    )
                    ,

# At each step of the accumulator,

                    lambda bounds, _: (
                        # generator expression to bind names to values
                        (
                            (

#     If the combat results show the infection dead ([1] == 0)
#     then the next state will be the same lower bound and a new upper
#     bound set at the midpoint between the lower and upper bound.

                                (bounds[0], (bounds[0] + bounds[1])//2)
                                if boosted_results[1] == 0

#     If the combat results sohw the immune system losing ([0] == 0)
#     then the next state will have the new lower bound set to the
#     upper bound, and the upper bound increased by the difference
#     between the bounds.

                                else
                                (bounds[1], 2*bounds[1] - bounds[0])

#     In both cases, also return the immune system survivors as the
#     third element in the state tuple.

                            ) + (boosted_results[0],)

#     Bind `boosted_results` to the boosted combat results from
#     feeding the combat data and the upper bound to `boosted_combat_results`.

                            for boosted_results in [
                                boosted_combat_results(
                                    input_data,
                                    bounds[1]
                                )
                            ]
                        ).next()
                    )
                )

# The minimal boost is one higher than the bounds returned by the
# next iteration of the dropwhile.

            ).next()[2]
        )

########################################################################
#
# Main controller

if __name__ == '__main__':

    base_filename = __file__.rsplit('.')[0]

    input_filename = '{}.input'.format(base_filename)
    input_data = open(input_filename).read()

    if run_part_1 and run_samples:

        for sample_num in itertools.takewhile(lambda num:os.path.exists('{}.sample.{}'.format(base_filename, num)), itertools.count(1)):

            sample_filename = '{}.sample.{}'.format(base_filename, sample_num)
            sample_data = open(sample_filename).read()

            results_filename = '{}.sample.results.part1.{}'.format(base_filename, sample_num)
            expected = (
                        int(open(results_filename).read().strip())
                        if os.path.exists(results_filename)
                        else None
                    )

            t = time.time()
            if DEBUGGING: print >> sys.stderr, "\nprocessing {} with expected results {}".format(sample_filename, expected)
            result = part_1(process_input_data(sample_data))
            if DEBUGGING: result = '\n' + pprint.pformat(result) + '\n'
            t = time.time() - t
            print "{}: sample {}: part 1 = {}{}".format(t, sample_num, result, " (expected {})".format(expected) if result != expected else "")

    if run_part_1 and run_data:

        t = time.time()
        if DEBUGGING: print >> sys.stderr, "\nprocessing {}".format(sample_filename)
        result = part_1(process_input_data(input_data))
        if DEBUGGING: result = '\n' + pprint.pformat(result) + '\n'
        t = time.time() - t
        print "{}: input data: part 1 = {}".format(t, result)

    if run_part_2 and run_samples:

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
            if DEBUGGING: print >> sys.stderr, "\nprocessing {} with expected results {}".format(sample_filename, expected)
            result = part_2(process_input_data(sample_data))
            if DEBUGGING: result = '\n' + pprint.pformat(result) + '\n'
            t = time.time() - t
            print "{}: sample {}: part 2 = {}{}".format(t, sample_num, result, " (expected {})".format(expected) if result != expected else "")

    if run_part_2 and run_data:

        t = time.time()
        if DEBUGGING: print >> sys.stderr, "\nprocessing {}".format(sample_filename)
        result = part_2(process_input_data(input_data))
        if DEBUGGING: result = '\n' + pprint.pformat(result) + '\n'
        t = time.time() - t
        print "{}: input data: part 2 = {}".format(t, result)

