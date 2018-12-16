
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
        print >> sys.stderr, ">>reduce<< initial state={0!r}".format(initial)
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
# Convert a combat map into a single-string map, the map's width, and
# plus dictionary mapping map-index locations to
# `{'type': type, 'enemy': enemytype, 'attack': attack, 'hp': hitpoints}`.
#
# Generate the map by first splitting the input, recording the map width,
# and joining the split map back together into a single string with
# no newlines.
#
# Generate the positions list for the dictionary by using a regex of
# `([GE])` to split the single-string combat map.
#
# Then run `reduce` over the results, with the state consisting of the
# list of (map_index,{unitdict}) being built.
#
# The initial state is [(0,None)].
#
# At each reduction, if the next map part is a `G` or `E`, update the
# last tuple in the state to include the unit dictionlary containing
# the `type`, the `enemy` type, the `attack` value (currently a constant
# of `3`), and the initial `hp` (hit points,currently a constant of
# `200`); and append a new `[(map_index+1,None)]` tuple pointing to the
# _next_ `map_index` value.
# (For debugging purposes, each unit is also given an id, but it's not
# referenced anywhere)
#
# Otherwise, adjust the `map_index` value of the last tuple to skip past
# the cells in the map part.
#
# When finished, strip the last element from the reduction state.
# 
# Return the map, the map width, and the dictionary formed from the
# position list.

process_input_data = lambda input_data: (
            # generator trick to bind values to names...
            (

# Return the map, the map width, and the dictionary formed from the
# position list.
                (
                    map, map_width, dict(positions)
                )

# Generate the map by first splitting the input, ...

                for map_lines in [
                    input_data.split()
                ]

# ... recording the map width,

                for map_width in [
                    len(map_lines[0])
                ]

# and joining the split map back together into a single string with
# no newlines.

                for map in [
                    ''.join(map_lines)
                ]

# Generate the positions list for the dictionary ...

                for positions in [

# Then run `reduce` over the results, with the state consisting of the
# list of (map_index,{type,enemy,attack,hp}) being built.

                    reduce(

                        lambda state, map_part: (
                            (

# At each reduction, if the next map part is a `G` or `E`, update the
# last tuple in the state to include the unit dictionary containing
# the `type`, the `enemy` type, the `attack` value (currently a constant
# of `3`), and the initial `hp` (hit points, currently a constant of
# `200`); and append a new `[(map_index+1,None)]` tuple pointing to the
# _next_ `map_index` value.
# (For debugging purposes, each unit is also given an id, but it's not
# referenced anywhere)

                                state[:-1]
                                + [
                                    (
                                        state[-1][0],
                                        {
                                            'id': '{}{:02d}'.format(map_part, len([unit for unit in state if unit[1] is not None and unit[1]['type'] == map_part])),
                                            'type': map_part,
                                            'enemy': 'G' if map_part == 'E' else 'E',
                                            'attack': 3,
                                            'hp': 200
                                        }
                                    )
                                ] + [
                                    (
                                        state[-1][0] + 1
                                        ,
                                        None
                                    )
                                ]
                            )
                            if map_part in ('G', 'E')
                            else
                            (

# Otherwise, adjust the `map_index` value of the last tuple to skip past
# the cells in the map part.

                                state[:-1]
                                + [
                                    (
                                        state[-1][0] + len(map_part)
                                        ,
                                        None
                                    )
                                ]
                            )
                        )
                        ,

#                                            ... by using a regex of
# `([GE])` to split the single-string combat map.

                        re.split(r'([GE])', map)
                        ,

# The initial state is [(0,None)].

                        [(0,None)]

# When finished, strip the last element from the reduction state.

                    )[:-1]
                ]
            ).next()
        )

########################################################################
#
# Find the shortest route from a unit at a particular map_index to the
# closest enemy unit to that map_index.
#
# Inputs:
#     The map,
#     The map width,
#     The map_index of the unit to process,
#     And the symbol of the unit's enemy type.
#
# Output:
#     The map_index of the first step to take to reach the closest enemy,
#     or the current map_index if there is no reachable enemy or if the
#     closest enemy is adjancent.
#
# This will be an accumulator using the following state:
#     A list of the positions being worked on, with each entry in the
#     list consisting of the map_index itself and the path to take to
#     reach that position (_including_ the starting map_index);
#     And the map, which will have each position that appears in the
#     list above replaced by an 'X'.
#
# When the accumulator finds an enemy, it will replace the state with
# the map_index of the next step to take.
#
# If the accumulator runs out of locations to check, the list of
# positions being worked on will be empty.
#
# The accumulator will be controlled by a `dropwhile` that discards
#     any state that consists of a tuple whose first item is a non-empty
#     list.
#
# The state of the accumulator is a list of positions and the path taken
# to reach each position, and the map with used positions marked so as
# to not be re-used.
#
# The initial state of the accumulator is:
#     The list `[ (starting_map_index, [starting_map_index]) ]`
#     and the map.
#
# The iterable for the accumulator consists of a `chain` of:
#     A list containing the initial state,
#     and a `count` infinite counter.
#
# The accumulator processes each state as a reduction, ignoring
# the counter.
# 
# The reduction's state is the new state of the accumulator as it is
# constructed.
#
# The reduction's initial state is:
#     An empty list `[]`
#     and the map.
# 
# The reduction runs against the `product` of the list of positions
# from the current state of the accumulator, and the static list
# of map index deltas to check: `( -map_width, -1, 1, map_width )`;
# this is further processed through an `imap` to add the positions
# and delta positions together and add the new position to the
# position's path list ( generating tuples of the form `(new_index,
# [list_of_positions_including_new_index])`), and is then sorted.
#
# The reduction function takes the reduction state and next position
# entry as arguments, and does the following:
# 
#     If the reduction state is not a tuple, return the reduction state
#     unchanged.
#
#     If the map location at the new index is empty (`.`), return the
#     state with
#
#         The new index and new list of positions added to the state's
#         position list,
#
#         And the map location of the new index replaced by an `X`.
#
#     If the map location at the new index is an enemy, strip the
#     returned state down to the next step to take towards that enemy:
#
#         Take the new list of positions,
#         Remove the last item (the position of the enemy);
#         Remove all but the first two items (to leave the current
#         position and possibly the next step);
#         And return the last item remaining in the list:
#             `list_of_new_positions[:-1][:2][-1]`
#
#     Otherwise, return the input reduction state without adding any
#     new position to it.
#
# The main lambda will take one result from the accumulator's `dropwhile`
# and either:
#
#     Return it, if it's an integer, or
#     Return the initial unit position.

path_to_closest_enemy = lambda map, map_width, unit_position, enemy: (
            # generator trick to bind values to names
            (

# The main lambda will take one result from the accumulator's `dropwhile`
# and either:
#
#     Return it, if it's an integer, or
#     Return the initial unit position.

                next_position
                if isinstance(next_position, int)
                else unit_position

                for next_position in [

# The accumulator will be controlled by a `dropwhile` that discards
#     any state that consists of a tuple whose first item is a non-empty
#     list.

                    itertools.dropwhile(
                        lambda state: (
                            isinstance(state, tuple) and state[0]
                        )
                        ,

                        accumulate(

# The state of the accumulator is a list of positions and the path taken
# to reach each position, and the map with used positions marked so as
# to not be re-used.
#
# The initial state of the accumulator is:
#     The list `[ (starting_map_index, [starting_map_index]) ]`
#     and the map.
#
# The iterable for the accumulator consists of a `chain` of:
#     A list containing the initial state,
#     and a `count` infinite counter.

                            itertools.chain(
                                # the initial state, inside a list
                                [
                                  ( [ (unit_position, [unit_position]) ], map )
                                ]
                                ,
                                itertools.count(1)
                            )
                            ,

# The accumulator processes each state as a reduction, ignoring
# the counter value.

                            lambda current_state, _: (
                                reduce(

# The reduction function takes the reduction state and next position
# entry as arguments, and does the following:

                                    lambda working_state, next_position: (

#     If the reduction state is not a tuple, return the reduction state
#     unchanged.

                                        working_state
                                        if not isinstance(working_state, tuple)
                                        else

#     return the state with

                                        (

#         The new position and new list of positions added to the state's
#         position list,

                                            working_state[0] + [next_position]
                                            ,

#         And the map location of the new position replaced by an `X`.

                                            working_state[1][:next_position[0]]
                                            + 'X'
                                            + working_state[1][next_position[0]+1:]
                                        )

#     If the map location at the next position is empty (`.`)

                                        if working_state[1][next_position[0]] == '.'
                                        else

#     strip the returned state down to the next step to take towards
#     that enemy:
#
#         Take the new list of positions,
#         Remove the last item (the position of the enemy);
#         Remove all but the first two items (to leave the current
#         position and possibly the next step);
#         And return the last item remaining in the list:
#             `list_of_new_positions[:-1][:2][-1]`

                                        next_position[1][:-1][:2][-1]

#     If the map location at the next position is an enemy,

                                        if working_state[1][next_position[0]] == enemy
                                        else

#     Otherwise, return the input reduction state without adding any
#     new position to it.

                                        working_state

                                    ) # end of reduce lambda
                                    ,

# The reduction runs against the `product` of the list of positions
# from the current state of the accumulator, and the static list
# of map index deltas to check: `( -map_width, -1, 1, map_width )`;
# this is further processed through an `imap` to add the positions
# and delta positions together and add the new position to the
# position's path list ( generating tuples of the form `(new_index,
# [list_of_positions_including_new_index])`), and is then sorted.

                                    sorted(
                                        itertools.imap(
                                            lambda (position, delta): (
                                                (
                                                    position[0] + delta
                                                    ,
                                                    position[1]
                                                    + [ position[0] + delta ]
                                                )
                                            )
                                            ,
                                            itertools.product(
                                                current_state[0],
                                                ( -map_width, -1, 1, map_width )
                                            )
                                        )
                                    )
                                    ,

# The reduction's initial state is:
#     An empty list `[]`
#     and the map.

                                    ( [], current_state[1] )

                                ) # end of `reduce()`

                            ) # end of accumulator lambda

                        ) # end of accumulate

                    ).next() # end of dropwhile; return the next item

                ] # end of `for next_position in` trick
            ).next() # end of main generator trick; take the item produced
        ) # end of path_to_enemy lambda

########################################################################
#
# Process a combat round:
#
# The input to the lambda is a tuple of:
#     The map.
#     The map's width.
#     The dictionary of combatants.
#
# The return from the lambda is a tuple of:
#     The new map, or an empty string if the combat round does not happen,
#     or a string of spaces if the combat round ends part way through.
#     The map's width.
#     The updated dictionary of combatants, with dead combatants removed.
#
# 1.  If the map does not contain any goblins or does not contain any
#     elves, return an empty string for the map.
#
# 2.  Otherwise, process the round using a reduction that returns
#     the next accumulator state.
#
# 3.  The initial reduction state is the tuple of inputs to the round:
#     `(map, map_width, combatants)`
#
# 4.  The reduction runs across the combatants' positions and status,
#     sorted by their `y` and `x` coordinates.
#
# 5.  If the current combatant's location on the map is is not the
#     combatant's type, return the current state unchanged.
#     This covers both the case where a combatant dies (in which case
#     the combatant's map location will be a `.`), and where combat ends
#     mid-round (in which case the combatant's map location will be a
#     space).
#
# 6.  If the current state's map contains no enemies for the combatant,
#     return the current state with the map replaced by all spaces, to
#     indicate the round is a partial combat round.
#
# 7.  Otherwise, use `path_to_closest_enemy` to find the next step
#     to take for this combatant.
#
# 8.  Generate an interim state consisting of the combatant's movement towards
#     the closest enemy.
#
#     9.  If combatant's next step is the same as its current position, return
#         the current reduction state as the interim state.
#
#     10. Otherwise, return a new interim state after moving the combatant to
#         the next step:
#
#         11. Generate a new map with the combatant's position replaced
#             with a '.' and the next step position replaced with the
#             combatant's type.
#
#         12. Replace the position dictionary with a new dictionary that
#             excludes the combatant's position and includes the `step`
#             position with the combatant's information.
#
# 13. Generate the return state based on any combat happening:
#
#     14. Determine which adjacent locations to the next step contain
#         an enemy, using a list comprehension over the delta indices
#         in "reading" order: `( -map_width, -1, 1, map_width )`.
#         Return the first one, or `None`.
#
#     15. If there is an adjacent enemy, process combat with the first
#         adjacent enemy found:
#
#         16. If the enemy has hit points less than or equal to the
#             combatant's attack value...
#
#             17. Replace the enemy's position on the map with a `.`
#
#             18. Remove the enemy's position from the positions
#                 dictionary.
#
#         19. Otherwise...
#
#             20. Replace the enemy's information in the positions
#                 dictionary with their hit points minus the combatant's
#                 attack value.
#
#     21. If there are no adjacent enemies, return the interim state
#         unchanged.

process_combat_round = lambda (map, map_width, combatants): (

# 1.  If the map does not contain any goblins or does not contain any
#     elves, return an empty string for the map.

            ('', map_width, combatants)
            if 'G' not in map and 'E' not in map
            else

# 2.  Otherwise, process the round using a reduction that returns
#     the next accumulator state.

            reduce(
                lambda state, combatant: (

# 5.  If the current combatant's location on the map is is not the
#     combatant's type, return the current state unchanged.
#     This covers both the case where a combatant dies (in which case
#     the combatant's map location will be a `.`), and where combat ends
#     mid-round (in which case the combatant's map location will be a
#     space).

                    state
                    if state[0][combatant[0]] != combatant[1]['type']
                    else

# 6.  If the current state's map contains no enemies for the combatant,
#     return the current state with the map replaced by all spaces, to
#     indicate the round is a partial combat round.

                    (
                        ' ' * len(state[0])
                        ,
                        state[1]
                        ,
                        state[2]
                    )
                    if combatant[1]['enemy'] not in state[0]
                    else

# 13. Generate the return state based on any combat happening:

                    # generator trick la la la
                    (

                        ( # start of step 15 'If there is an adjacent...'
                            ( # start of step 16 'If the enemy has...'

#             17. Replace the enemy's position on the map with a `.`

                                interim_state[0][:adjacent_enemy]
                                + '.'
                                + interim_state[0][adjacent_enemy+1:]
                                ,

# (undocumented step) keep the map width unchanged

                                interim_state[1]
                                ,

#             18. Remove the enemy's position from the positions
#                 dictionary.

                                dict(
                                    item
                                    for item in interim_state[2].iteritems()
                                    if item[0] != adjacent_enemy
                                )

#         16. If the enemy has hit points less than or equal to the
#             combatant's attack value...

                            )
                            if (
                                interim_state[2][adjacent_enemy]['hp']
                                <= interim_combatant[1]['attack']
                            )

#         19. Otherwise...

                            else

#             20. Replace the enemy's information in the positions
#                 dictionary with their hit points minus the combatant's
#                 attack value.

                            (
                                interim_state[0]
                                ,
                                interim_state[1]
                                ,
                                dict(
                                    item
                                    if item[0] != adjacent_enemy
                                    else
                                    (
                                        item[0],
                                        dict(
                                            attr
                                            if attr[0] != 'hp'
                                            else (
                                                attr[0]
                                                ,
                                                attr[1]
                                                - interim_combatant[1]['attack']
                                            )
                                            for attr in item[1].items()
                                        )
                                    )
                                    for item in interim_state[2].iteritems()
                                )

                            ) # end of step 20 'Replace the enemy...'

#     15. If there is an adjacent enemy, process combat with the first
#         adjacent enemy found:

                        )
                        if adjacent_enemy

#     21. If there are no adjacent enemies, return the interim state
#         unchanged.

                        else interim_state

# 7.  Otherwise, use `path_to_closest_enemy` to find the next step
#     to take for this combatant.

                        for next_step in [
                            path_to_closest_enemy(
                                state[0],
                                state[1],
                                combatant[0],
                                combatant[1]['enemy']
                            )
                        ]

# 8.  Generate an interim state consisting of the combatant's movement towards
#     the closest enemy.

                        for interim_state_and_combatant in [

#     9.  If combatant's next step is the same as its current position, return
#         the current reduction state as the interim state.

                            (state, combatant)
                            if next_step == combatant[0]

#     10. Otherwise, return a new interim state after moving the combatant to
#         the next step:

                            else
                            (

                                ( # start of tuple containing steps 11 and 12

#         11. Generate a new map with the combatant's position replaced
#             with a '.' and the next step position replaced with the
#             combatant's type.

# (this is complicated by needing to do the slicing in the correct order
# based on whether `next_step` is before or after the combatant's current
# position)

                                    (
                                        state[0][:combatant[0]]
                                        + '.'
                                        + state[0][combatant[0]+1:next_step]
                                        + combatant[1]['type']
                                        + state[0][next_step+1:]
                                    ) if combatant[0] < next_step
                                    else (
                                        state[0][:next_step]
                                        + combatant[1]['type']
                                        + state[0][next_step+1:combatant[0]]
                                        + '.'
                                        + state[0][combatant[0]+1:]
                                    )
                                    ,

# (keep the map width unchanged)

                                    state[1]
                                    ,

#         12. Replace the position dictionary with a new dictionary that
#             excludes the combatant's position and includes the `step`
#             position with the combatant's information.

                                    dict(
                                        (
                                            item[0]
                                            if item[0] != combatant[0]
                                            else next_step
                                            ,
                                            item[1]
                                        )
                                        for item in state[2].iteritems()
                                    )

                                ) # end of tuple containing steps 11 and 12
                                ,

# (undocumented step) - update the combatant information with the
# new position.

                                (
                                    next_step,
                                    combatant[1]
                                )

                            ) # end of step '10. Otherwise...'
                        ] # end of step '8. Generate an interim step...'

# (undocumented step) to split the interim_state and combatants into two
# name bindings

                        for interim_state in [
                            interim_state_and_combatant[0]
                        ]
                        for interim_combatant in [
                            interim_state_and_combatant[1]
                        ]

#     14. Determine which adjacent locations to the next step contain
#         an enemy, using a list comprehension over the delta indices
#         in "reading" order: `( -map_width, -1, 1, map_width )`.
#         Return the first one, or `None`.

                        for adjacent_enemy in [
                            (
                                sorted([
                                        adjacent_index
                                        for adjacent_index in (
                                            interim_combatant[0] + delta
                                            for delta in (
                                                -map_width,
                                                -1,
                                                1,
                                                map_width
                                            )
                                        )
                                        if interim_state[0][adjacent_index] == interim_combatant[1]['enemy']
                                    ]
                                    ,
                                    key = lambda index:interim_state[2][index]['hp']
                                )
                                + [None]
                            )[0]
                        ]

                    ).next() # end of step 13 'Generate the return state...'

                ) # end of the reduction lambda for step 2
                ,

# 4.  The reduction runs across the combatants' positions and status,
#     sorted by their `y` and `x` coordinates.

                sorted(combatants.items())
                ,

# 3.  The initial reduction state is the tuple of inputs to the round:
#     `(map, map_width, combatants)`

                (map, map_width, combatants)

            ) # end of step 2

        ) # end of `process_combat_round`

########################################################################
#
# Part 1:
#
# 1.  Run an `accumulate` over the input data and a round counter
#     processing each round as described below.
#
# 2.  If any combatant finds no enemies during a round of combat, the
#     map will be replaced by all spaces, to mark the round as an
#     incomplete combat round.  At the beginning of any combat round,
#     if there are no goblins _or_ no elves, the map will be replaced
#     by an empty string, to mark the end of combat.
#     Therefore, filter the accumulator through a `takewhile` that
#     stops when it finds the empty string.
#
# 3.  At the end, return the product of the number of rounds (filtered
#     to remove a possible last round whose map is all spaces) and the
#     sum of the hitpoints in the last round.
#
# 3a. To support Part 2, if the optional `return_combatants` parameter
#     is passed as True, the return value is a tuple of the result as
#     described above and the final combatants list.
#
# Process each round using the `process_combat_round` helper.
# (ignoring the round counter).

part_1 = lambda input_data, return_combatants = False: (
            # generator expression cheating la la la
            (

# 3.  At the end, return the product of the number of rounds (filtered
#     to remove a possible last round whose map is all spaces) and the
#     sum of the hitpoints in the last round.

                (len([round for round in combat_rounds if round[0][0] != ' ']) - 1)
                * sum(
                    unit_stats['hp']
                    for unit_stats in
                    combat_rounds[-1][2].itervalues()
                )

# 3a. To support Part 2, if the optional `return_combatants` parameter
#     is passed as True, the return value is a tuple of the result as
#     described above, plus the final combatants list.

                if not return_combatants
                else
                (
                    (len([round for round in combat_rounds if round[0][0] != ' ']) - 1)
                    * sum(
                        unit_stats['hp']
                        for unit_stats in
                        combat_rounds[-1][2].itervalues()
                    )
                    ,
                    combat_rounds[-1][2]
                )

# (undocumented sub-steps) bind the input data to names

                for map in [input_data[0]]
                for map_width in [input_data[1]]
                for position_dict in [input_data[2]]

# (undocumented sub-step) bind the list of combat rounds to a name
                for combat_rounds in [ list(

# 2.  If any combatant finds no enemies during a round of combat, the
#     map will be replaced by all spaces, to mark the round as an
#     incomplete combat round.  At the beginning of any combat round,
#     if there are no goblins _or_ no elves, the map will be replaced
#     by an empty string, to mark the end of combat.
#     Therefore, filter the accumulator through a `takewhile` that
#     stops when it finds the empty string.

                    itertools.takewhile(
                        lambda map_data: (
                            map_data[0]
                        )
                        ,

# 1.  Run an `accumulate` over the input data and a round counter
#     processing each round as described below.

                        accumulate(
                            itertools.chain(
                                [ input_data ],
                                itertools.count(1)
                            )
                            ,

# Process each round using the `process_combat_round` helper.
# (ignoring the round counter).

                            lambda current_state, _: (
                                process_combat_round(current_state)
                            )

                        ) # end of step '1.  Run an `accumulate`...'
                    ) # end of step '2.  ... filter the `accumulate` through a `takewhile` ...'
                )]# end of 'bind the list of combat rounds to a name'.

            ).next()
        )

########################################################################
#
# Part 2:
#
# This section will use the Part 1 lambda repeatedly to determine at
# what attack value the elves can win without losing a single elf.
#
# This is an accumulator that runs with increasing attack values until
# the proper condition is met.
#
# 1.  The accumulator's iterator is a `chain` consisting of an initial
#     false "everyone dies" state (`(0, {})`) followed by a `count`
#     starting at 4.  The initial false state is required due to
#     `accumulate`'s automatic return of the first value of the iterator
#     before processing anything through its accumulation function.
#
# 2.  At each step of the iterator...
#
#     3.  Create a new set of input data by replacing the combatants
#         dictionary with a new dictionary containing the same
#         combatants, except that each elf's `attack` value is replaced
#         by the new attack value.
#
#     4.  Return the results of part 1 (with `return_combatants` set to
#         True).
#
# 5.  The accumulator is filtered by a `dropwhile` that drops all result
#     states in which the count of elves in the returned results is less
#     than the count of elves in the input data.
#
# 6.  Return the first element (`[0]`) of the `next()` result of the
#     accumulator.

part_2 = lambda input_data: (

# 5.  The accumulator is filtered by a `dropwhile` that drops all result
#     states in which the count of elves in the returned results is less
#     than the count of elves in the input data.

            itertools.dropwhile(
                lambda results: (
                    len([elf for elf in results[1] if results[1][elf]['type'] == 'E'])
                    !=
                    len([elf for elf in input_data[2] if input_data[2][elf]['type'] == 'E'])
                )
                ,

# This is an accumulator that runs with increasing attack values until
# the proper condition is met.

                accumulate(

# 1.  The accumulator's iterator is a `chain` consisting of an initial
#     false "everyone dies" state (`(0, {})`) followed by a `count`
#     starting at 4.  The initial false state is required due to
#     `accumulate`'s automatic return of the first value of the iterator
#     before processing anything through its accumulation function.

                    itertools.chain(
                        [ (0,{},[]) ]
                        ,
                        itertools.count(4)
                    )
                    ,

# 2.  At each step of the iterator...

                    lambda state, new_attack: (

                        # use the generator trick...
                        (

#     4.  Return the results of part 1 (with `return_combatants` set to
#         True).

                            results + (state[-1] + [(new_attack,results)],)

#     3.  Create a new set of input data by replacing the combatants
#         dictionary with a new dictionary containing the same
#         combatants, except that each elf's `attack` value is replaced
#         by the new attack value.

                            for new_input_data in [
                                input_data[:2]
                                + (
                                    {
                                        index: {
                                            key: (
                                                input_data[2][index][key]
                                                if key != 'attack' or input_data[2][index]['type'] != 'E'
                                                else new_attack
                                            )
                                            for key in input_data[2][index]
                                        }
                                        for index in input_data[2]
                                    },
                                )
                                + input_data[3:]
                            ]

#     4.  Return the results of part 1 (with `return_combatants` set to
#         True).

                            for results in [ part_1(new_input_data, return_combatants=True) ]

                        ).next()
                    )

# 6.  Return the first element (`[0]`) of the `next()` result of the
#     accumulator.

                )
            ).next()[0]
        )

########################################################################
#
# Main controller

if __name__ == '__main__':

    input_data = process_input_data(open(__file__.rsplit('.')[0] + '.input').read())

    file_base = __file__.rsplit('.')[0]
    for sample_num in itertools.takewhile(lambda num:os.path.exists('{}.sample.{}'.format(file_base, num)), itertools.count(1)):

        sample_data = process_input_data(open('{}.sample.{}'.format(__file__.rsplit('.')[0], sample_num)).read())

        expected = int(open('{}.sample.results.part1.{}'.format(__file__.rsplit('.')[0], sample_num)).read().strip())

        t = time.time()
        result = part_1(sample_data)
        t = time.time() - t
        print "{}: sample {}: part 1 = {}{}".format(t, sample_num, result, " (expected {})".format(expected) if result != expected else "")

        if DEBUGGING: sys.exit(0)

    t = time.time()
    result = part_1(input_data)
    t = time.time() - t
    print "{}: input data: part 1 = {}".format(t, result)

    for sample_num in itertools.takewhile(lambda num:os.path.exists('{}.sample.{}'.format(file_base, num)), itertools.count(1)):

        sample_data = process_input_data(open('{}.sample.{}'.format(__file__.rsplit('.')[0], sample_num)).read())

        expected = int(open('{}.sample.results.part2.{}'.format(__file__.rsplit('.')[0], sample_num)).read().strip())

        t = time.time()
        result = part_2(sample_data)
        t = time.time() - t
        print "{}: sample {}: part 2 = {}{}".format(t, sample_num, result, " (expected {})".format(expected) if result != expected else "")

        if DEBUGGING: sys.exit(0)

    t = time.time()
    result = part_2(input_data)
    t = time.time() - t
    print "{}: input data: part 2 = {}".format(t, result)

