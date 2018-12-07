
import re
import sys
import itertools

# Transform the input string into a list of (x,y) tuples

def process_input_data(input_data):
    re_order = re.compile(r'''Step ([^ ]+) must be finished before step ([^ ]+) can begin''')
    return list(match.groups() for match in re_order.finditer(input_data))

# Determine the complete set of predecessors for each step.
#
#   Do this with a huge reduction.
#
#   The initial state for the reduction is an empty dictionary.
#
#   The state produced at each reduction step is a dictionary
#   mapping a step to the set of all the steps that must be completed
#   before it; for example, `{'B': set(['A', 'C'])}`
#
#   On each step, produce a new dictionary from the list of
#   successor,predecessors pairs from the dictionary's items where
#   each predecessors set that includes the successor gets the new
#   predecessor added to it.
#
#   After producing this new dictionary, add one additional mapping
#   for the current step's successor and the set of the already-known
#   predecessors for the current step's successor unioned with the
#   current step's predecessor and all of the already-known predecessors
#   for the current step's predecessor.  Also add the current step's
#   predecessor if needed.
#
#   Once the reduction for the predecessors dictionary is complete,
#   transform it back into a list of (predecessors, successor) tuples
#   (e.g. `(set(['A', 'C']), 'B')`).

full_predecessors_list = lambda predecessor_list: (
            list(
                (predecessors, successor)
                for (successor, predecessors) in
                    reduce(
                        lambda predecessors,(predecessor,successor):
                            # use a generator as a trick to be able to create
                            # and reference variables within the expression
                            (
                                dict(
                                    new_predecessors.items()
                                    + [
                                        (
                                            successor,
                                            new_predecessors.get(successor, set())
                                            | new_predecessors.get(predecessor, set())
                                            | {predecessor}
                                        )
                                        ,
                                        (
                                            predecessor,
                                            new_predecessors.get(predecessor, set())
                                        )
                                    ]
                                )
                                # trick to be able to reference the new dictionary
                                for new_predecessors in [
                                    dict(
                                        (
                                            known_successor,
                                            (
                                                known_predecessors | {predecessor}
                                                if successor in known_predecessors
                                                else known_predecessors
                                            )
                                        )
                                        for (known_successor, known_predecessors) in
                                        predecessors.items()
                                    )
                                ]
                            ).next()
                        ,
                        predecessor_list
                        ,
                        {}
                    ).iteritems()
            )
        )

# Part 1:
#
#   Determine the final order for the input steps, based on the input
#   data, which is a tuple of (predecessor, successor).
#
#   Start by generating the full list of predecessors for each successor,
#   using the `full_predecessors_list` lambda above.
#   Use the following reduction algorithm to order the steps:
#
#   Initialize the reduction state with an empty list (the ordered
#   list of steps) and the actual list of steps produced above.
#
#   Run the reduction over the `range` of the number of steps.
#
#   At each reduction step, return a new state that has the first
#   step from the _sorted_ list of steps added to the ordered list
#   of steps and has list of remaining steps mapped to filter out
#   that first selected step and to remove that selected step from
#   the predecessors set of every other step.
#
#   Finally, given the ordered list of steps, join it together into
#   a single string to be returned.

def part_1(input_data):

    return (
                ''.join(
                    # use a generator as a trick to be able to create
                    # and reference variables within the expression
                    (
                        reduce(
                            lambda (ordered_steps, remaining_steps), _:
                                # same generator trick
                                (
                                    (
                                        ordered_steps + [new_step]
                                        ,
                                        [
                                            (predecessors - {new_step}, successor)
                                            for (predecessors, successor) in remaining_steps
                                            if successor != new_step
                                        ]
                                    )
                                    for new_step in [
                                        sorted(remaining_steps)[0][1]
                                    ]
                                ).next()
                            ,
                            range(len(predecessors_list))
                            ,
                            ([], predecessors_list)
                        )
                        for predecessors_list in [
                            full_predecessors_list(input_data)
                        ]
                    ).next()[0]
                )
            )

# Part 2:
#
#   This time, we need to actually schedule the steps to be done
#   based on having multiple workers available.  This changes the
#   order of steps, because some later steps will be available to
#   be performed before earlier steps are made visible.
#
#   Start by generating the full list of predecessors for each step,
#   using the `full_predecessors_list` lambda above, then transform each
#   step letter to its ordinal value (where A is 1 and Z is 26).
#   (Because this is a map/reduce expression, the starting value is at
#   the end of the expression)
#
#   Use the following reduction algorithm to generate the steps taken in
#   time sequence.
#
#   The reduction state is a tuple containing the total time taken to
#   complete all steps (or None if the steps have not yet been completed),
#   a list of worker tuples, and the remaining steps to be completed,
#   initially set to the above-modified full_predecessors_list.
#
#   Each worker's tuple contains a step and the number of seconds
#   remaining for that worker to complete that step (where the initial
#   number of seconds is equal to 60 plus the ordinal value of the step.
#
#   The initial state is `(None, [(None, 0)]*workers, modified_full_predecessors_list)`
#
#   Run the reduction over the `range` of one plus the maximum number of seconds
#   that the process would take if only one step could be performed at a
#   time:  `xrange(1 + 60 * num_steps + sum(ordinal_step_values))`.  The value of
#   this is called the `clock`.
#
#   At each reduction step, return a new state as follows:
#
#   *   If the final time is not None, return (final_time, None, [])
#   *   Otherwise:
#       *   Generate an interim state:
#           *   Determine the steps that just completed by finding the
#               step values for each worker whose time-to-complete is
#               equal to 1.
#           *   Return the interim state consisting of the workers list
#               with each time-to-complete value reduced by 1 and each
#               step that has been completed replaced by None, and the
#               list of remaining steps with the completed steps skipped
#               and also filtered out of the predecessor sets for each
#               still-remaining step.
#       *   If the list of remaining steps in the interim state is empty
#           _and_ no workers are working, then the next state is `(clock,
#           None, [])` marking the time when the process completed.
#       *   Otherwise, generate the next state by reducing the interim state:
#           *   Initialize the next state with `(None, [], interim_remaining_steps)`
#           *   Run the reduction across the interim state's workers list:
#               *   If the worker's current step is None, the interim
#                   remaining steps list is not empty, and the first
#                   interim remaining step has no predecessors, the next
#                   state's workers list is the previous state's workers
#                   list with a new worker added for the first remaining
#                   step and the time that step will take to complete,
#                   and the next state's remaining steps list is the
#                   previous state's remaining steps list with the first
#                   step removed.
#               *   Otherwise, the next state's workers list is the
#                   previous state's workers list with the new worker
#                   added and the next state's remaining steps list is
#                   the same as the previous state's remaining steps list.
#
#   When the full reduction is complete, just return the final time from
#   the reduction state.

# a lambda to convert a step letter to an ordinal value:
ordinal_value_of = (
            lambda letter:
                ord(letter) - ord('A') + 1
        )

def part_2(input_data, num_workers, step_base_time):

    return (
                # generator trick again
                (
                    reduce(

#   The reduction state is a tuple containing the total time taken to
#   complete all steps (or None if the steps have not yet been completed),
#   a list of worker tuples, and the remaining steps to be completed,
#   initially set to the above-modified full_predecessors_list.
#
#   Each worker's tuple contains a step and the number of seconds
#   remaining for that worker to complete that step (where the initial
#   number of seconds is equal to 60 plus the ordinal value of the step.

                        lambda (final_time, workers, remaining_steps), clock:

#   *   If the final time is not None, return (final_time, None, [])

                            (final_time, None, [])
                            if final_time is not None
                            else (

#   *   Otherwise:

                                # generator trick again
                                (

#       *   If the list of remaining steps in the interim state is empty
#           _and_ no workers are working, then the next state is `(clock,
#           None, [])` marking the time when the process completed.

                                    (clock, None, [])
                                    if
                                        not interim_steps
                                        and 0 == sum(
                                            worker_time
                                            for (worker_step, worker_time) in interim_workers
                                        )
                                    else (

#       *   Otherwise, generate the next state by reducing the interim workers list to a final state:

                                        reduce(
                                            lambda (next_final_time, next_workers, next_steps), (worker_step, worker_time):

#               *   If the worker's current step is None, the interim
#                   remaining steps list is not empty, and the first
#                   interim remaining step has no predecessors, the next
#                   state's workers list is the previous state's workers
#                   list with a new worker added for the first remaining
#                   step and the time that step will take to complete,
#                   and the next state's remaining steps list is the
#                   previous state's remaining steps list with the first
#                   step removed.

                                                (
                                                    next_final_time,
                                                    next_workers + [
                                                        (
                                                            next_steps[0][1],
                                                            step_base_time + next_steps[0][1]
                                                        )
                                                    ],
                                                    next_steps[1:]
                                                )
                                                if
                                                    worker_step is None
                                                    and len(next_steps) > 0
                                                    and len(next_steps[0][0]) == 0

#               *   Otherwise, the next state's workers list is the
#                   previous state's workers list with the new worker
#                   added and the next state's remaining steps list is
#                   the same as the previous state's remaining steps list.

                                                else (
                                                    next_final_time,
                                                    next_workers + [(worker_step, worker_time)],
                                                    next_steps
                                                )
                                            ,

#           *   Run the reduction across the interim state's workers list:

                                            interim_workers
                                            ,

#           *   Initialize the next state with `(None, [], interim_remaining_steps)`

                                            (None, [], interim_steps)
                                        )
                                    )

#       *   Generate an interim state:

                                    for (interim_workers, interim_steps) in [

#           *   Return the interim state consisting of the workers list
#               with each time-to-complete value reduced by 1 and each
#               step that has been completed replaced by None, and the
#               list of remaining steps with the completed steps skipped
#               and also filtered out of the predecessor sets for each
#               still-remaining step.

                                        (
                                            [
                                                (None, 0)
                                                if worker_time <= 1
                                                else (worker_step, worker_time - 1)
                                                for (worker_step, worker_time) in workers
                                            ]
                                            ,
                                            sorted(
                                                (predecessors - completed_steps, step)
                                                for (predecessors, step) in remaining_steps
                                                if step not in completed_steps
                                            )
                                        )

#           *   Determine the steps that just completed by finding the
#               step values for each worker whose time-to-complete is
#               equal to 1.

                                        for completed_steps in [
                                            set(
                                                worker_step
                                                for (worker_step, worker_time)
                                                in workers
                                                if worker_time == 1
                                            )
                                        ]
                                    ]
                                ).next()
                            )
                        ,

#   Run the reduction over the `range` of one plus the maximum number of seconds
#   that the process would take if only one step could be performed at a
#   time:  `xrange(1 + 60 * num_steps + sum(ordinal_step_values))`.  The value of
#   this is called the `clock`.

                        xrange(
                            1
                            + sum(
                                step_base_time + step[1]
                                for step in modified_step_list
                            )
                        )
                        ,

#   The initial state is `(None, [(None, 0)]*workers, modified_full_predecessors_list)`

                        (None, [(None, 0)] * num_workers, modified_step_list)
                    )

#   Start by generating the full list of predecessors for each step,
#   using the `full_predecessors_list` lambda above, then transform each
#   step letter to its ordinal value (where A is 1 and Z is 26).

                    for modified_step_list in [
                        [
                            (
                                set(
                                    ordinal_value_of(predecessor)
                                    for predecessor in predecessors
                                )
                                ,
                                ordinal_value_of(step_letter)
                            )
                            for (predecessors, step_letter) in
                                full_predecessors_list(input_data)
                        ]
                    ]

                ).next()

#   When the full reduction is complete, just return the final time from
#   the reduction state.

            )[0]

if __name__ == '__main__':

    sample_data = process_input_data(open(__file__.rsplit('.')[0] + '.sample').read())

    print "sample data: part 1 = {}".format(part_1(sample_data))
    print "sample data: part 2 = {}".format(part_2(sample_data, 2, 0))

    input_data = process_input_data(open(__file__.rsplit('.')[0] + '.input').read())

    print "real input: part 1 = {}".format(part_1(input_data))
    print "real input: part 2 = {}".format(part_2(input_data, 5, 60))
