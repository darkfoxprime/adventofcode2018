
import re
import sys
import itertools

# Transform the input string into a list of (x,y) tuples

def process_input_data(input_data):
    re_order = re.compile(r'''Step ([^ ]+) must be finished before step ([^ ]+) can begin''')
    return list(match.groups() for match in re_order.finditer(input_data))

# Use a reduction to determine the complete set of predecessors for
# each step.
#
#   1.  The initial state for the reduction is an empty dictionary.
#
#   2.  Run the reduction across the list of (predecessor, successor)
#       tuples.
#
#   3.  The state produced at each reduction step is a dictionary mapping
#       a step to the set of all the steps that must be completed before
#       it; for example, `{'B': set(['A', 'C'])}`.  This is a two phase
#       process:
#
#   4.  The first phase produces a new dictionary from the list of
#       `(successor,predecessors)` pairs from the dictionary's items
#       where each `predecessors` set that includes the current step's
#       `successor` gets the current step's `predecessor` added to it.
#
#   5.  The second phase adds one additional mapping for the current
#       step's `successor` and the set of the already-known predecessors
#       for the current step's `successor` unioned with the current
#       step's `predecessor` and all of the already-known `predecessors`
#       for the current step's `predecessor`, as well as ensuring that
#       the current step's `predecessor` has a mapping as well.
#
#   6.  Once the reduction for the predecessors dictionary is complete,
#       transform it back into a list of (predecessors, successor) tuples
#       (e.g. `(set(['A', 'C']), 'B')`).
#
# Because this is a reduction of comprehensions/generators, the code works
# from the "inside out", so the documented sections are repeated within the
# following code.

full_predecessors_list = lambda predecessor_list: (

#   6.  Once the reduction for the predecessors dictionary is complete,
#       transform it back into a list of (predecessors, successor) tuples
#       (e.g. `(set(['A', 'C']), 'B')`).

            list(
                (predecessors, successor)
                for (successor, predecessors) in
                    reduce(

#   3.  The state produced at each reduction step is a dictionary mapping
#       a step to the set of all the steps that must be completed before
#       it; for example, `{'B': set(['A', 'C'])}`.  This is a two phase
#       process:

                        lambda predecessors,(predecessor,successor):
                            # use a generator as a trick to be able to create
                            # and reference variables within the expression
                            (

#   5.  The second phase adds one additional mapping for the current
#       step's `successor` and the set of the already-known predecessors
#       for the current step's `successor` unioned with the current
#       step's `predecessor` and all of the already-known `predecessors`
#       for the current step's `predecessor`, as well as ensuring that
#       the current step's `predecessor` has a mapping as well.

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

#   4.  The first phase produces a new dictionary from the list of
#       `(successor,predecessors)` pairs from the dictionary's items
#       where each `predecessors` set that includes the current step's
#       `successor` gets the current step's `predecessor` added to it.

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

#   2.  Run the reduction across the list of (predecessor, successor)
#       tuples.

                        predecessor_list
                        ,

#   1.  The initial state for the reduction is an empty dictionary.

                        {}
                    ).iteritems()
            )
        )

# Part 1:
#
# Determine the final order for the input steps, based on the input data,
# which is a tuple of (predecessor, successor).
#
#   1.  Start by generating the full list of predecessors for each
#       successor, using the `full_predecessors_list` lambda above.
#
#   2.  Initialize the reduction state with an empty list (the ordered
#       list of steps) and the actual list of steps produced above.
#
#   3.  We know we have to run the reduction once for every step,
#       so run the reduction over the `range` of the length of the
#       predecessors list.
#
#   4.  At each reduction step, return a new state that has the first
#       step from the _sorted_ list of steps added to the ordered list
#       of steps and has the list of remaining steps mapped to filter
#       out that first selected step and to remove that selected step
#       from the predecessors set of every other step.
#
#   5.  Finally, given the ordered list of steps, join it together into
#       a single string to be returned.
#
# Because this is a reduction of comprehensions/generators, the code works
# from the "inside out", so the documented sections are repeated within the
# following code.

def part_1(input_data):

    return (

#   5.  Finally, given the ordered list of steps, join it together into
#       a single string to be returned.

                ''.join(
                    # use a generator as a trick to be able to create
                    # and reference variables within the expression
                    (
                        reduce(
                            lambda (ordered_steps, remaining_steps), _:
                                # same generator trick
                                (

#   4.  At each reduction step, return a new state that has the first
#       step from the _sorted_ list of steps added to the ordered list
#       of steps and has the list of remaining steps mapped to filter
#       out that first selected step and to remove that selected step
#       from the predecessors set of every other step.

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

#   3.  We know we have to run the reduction once for every step,
#       so run the reduction over the `range` of the length of the
#       predecessors list.

                            range(len(predecessors_list))
                            ,

#   2.  Initialize the reduction state with an empty list (the ordered
#       list of steps) and the actual list of steps produced above.

                            ([], predecessors_list)
                        )
                        for predecessors_list in [

#   1.  Start by generating the full list of predecessors for each
#       successor, using the `full_predecessors_list` lambda above.

                            full_predecessors_list(input_data)

                        ]
                    ).next()[0]
                )
            )

# Part 2:
#
#   This time, we need to actually schedule the steps to be done based on
#   having multiple workers available.  This changes the order of steps,
#   because some later steps will be available to be performed before
#   earlier steps are made visible.
#
#   1.  Start by generating the full list of predecessors for each step,
#       using the `full_predecessors_list` lambda above, then transform
#       each step letter to its ordinal value (where A is 1 and Z is 26).
#       (Because this is a map/reduce expression, the starting value is
#       at the end of the expression)
#
#   2.  Use the following reduction algorithm to generate the steps
#       taken in time sequence.
#
#   3.  The reduction state is a tuple containing the total time
#       taken to complete all steps (or None if the steps have not yet
#       been completed), a list of worker tuples, and the remaining
#       steps to be completed, initially set to the above-modified
#       full_predecessors_list.
#
#   4.  Each worker's tuple contains a step and the number of seconds
#       remaining for that worker to complete that step (where the
#       initial number of seconds is equal to 60 plus the ordinal value
#       of the step.
#
#   5.  The initial state is `(None, [(None, 0)]*workers,
#       modified_full_predecessors_list)`
#
#   6.  Run the reduction over the `range` of one plus the maximum
#       number of seconds that the process would take if only one step
#       could be performed at a time:  `xrange(1 + 60 * num_steps +
#       sum(ordinal_step_values))`.  The value of this is called the
#       `clock`.
#
#   7.  At each reduction step, return a new state as follows:
#
#       8.  If the final time is not None, return (final_time, None, [])
#
#       9.  Otherwise:
#
#           10. Generate an interim state:
#
#               11. Determine the set of steps that just completed
#                   by finding the step values for each worker whose
#                   time-to-complete is equal to 1.
#
#               12. Return the interim state consisting of the workers
#                   list with each time-to-complete value reduced by
#                   1 and each step that has been completed replaced
#                   by None, and the _sorted_ list of remaining steps
#                   with the completed steps skipped and also filtered out
#                   of the predecessor sets for each still-remaining step.
#
#           13. If the list of remaining steps in the interim state
#               is empty _and_ no workers are working, then the next
#               state is `(clock, None, [])` marking the time when the
#               process completed.
#
#           14. Otherwise, generate the next state by reducing the
#               interim state:
#
#               15. Initialize the next state with `(None, [],
#                   interim_remaining_steps)`
#
#               16. Run the reduction across the interim state's
#                   workers list:
#
#                   17. If the worker's current step is None, the interim
#                       remaining steps list is not empty, and the first
#                       interim remaining step has no predecessors,
#                       the next state's workers list is the previous
#                       state's workers list with a new worker added
#                       for the first remaining step and the time that
#                       step will take to complete, and the next state's
#                       remaining steps list is the previous state's
#                       remaining steps list with the first step removed.
#
#                   18. Otherwise, the next state's workers list is the
#                       previous state's workers list with the new worker
#                       added and the next state's remaining steps list
#                       is the same as the previous state's remaining
#                       steps list.
#
#   19. When the full reduction is complete, just return the final time
#       from the reduction state.
#
# Because this is a reduction of comprehensions/generators, the code works
# from the "inside out", so the documented sections are repeated within the
# following code.


# Define a helper lambda to convert a step letter to an ordinal value:
ordinal_value_of = (
            lambda letter:
                ord(letter) - ord('A') + 1
        )

def part_2(input_data, num_workers, step_base_time):

    return (
                # generator trick again
                (

#   2.  Use the following reduction algorithm to generate the steps
#       taken in time sequence.
#
#   3.  The reduction state is a tuple containing the total time
#       taken to complete all steps (or None if the steps have not yet
#       been completed), a list of worker tuples, and the remaining
#       steps to be completed, initially set to the above-modified
#       full_predecessors_list.
#
#   4.  Each worker's tuple contains a step and the number of seconds
#       remaining for that worker to complete that step (where the
#       initial number of seconds is equal to 60 plus the ordinal value
#       of the step.

                    reduce(

#   7.  At each reduction step, return a new state as follows:

                        lambda (final_time, workers, remaining_steps), clock:

#       8.  If the final time is not None, return (final_time, None, [])

                            (final_time, None, [])
                            if final_time is not None
                            else (

#       9.  Otherwise:

                                # generator trick again
                                (

#           13. If the list of remaining steps in the interim state
#               is empty _and_ no workers are working, then the next
#               state is `(clock, None, [])` marking the time when the
#               process completed.

                                    (clock, None, [])
                                    if
                                        not interim_steps
                                        and 0 == sum(
                                            worker_time
                                            for (worker_step, worker_time) in interim_workers
                                        )
                                    else (

#           14. Otherwise, generate the next state by reducing the
#               interim state:

                                        reduce(
                                            lambda (next_final_time, next_workers, next_steps), (worker_step, worker_time):

#                   17. If the worker's current step is None, the interim
#                       remaining steps list is not empty, and the first
#                       interim remaining step has no predecessors,
#                       the next state's workers list is the previous
#                       state's workers list with a new worker added
#                       for the first remaining step and the time that
#                       step will take to complete, and the next state's
#                       remaining steps list is the previous state's
#                       remaining steps list with the first step removed.

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

#                   18. Otherwise, the next state's workers list is the
#                       previous state's workers list with the new worker
#                       added and the next state's remaining steps list
#                       is the same as the previous state's remaining
#                       steps list.

                                                else (
                                                    next_final_time,
                                                    next_workers + [(worker_step, worker_time)],
                                                    next_steps
                                                )
                                            ,

#               16. Run the reduction across the interim state's
#                   workers list.

                                            interim_workers
                                            ,

#               15. Initialize the next state with `(None, [],
#                   interim_remaining_steps)`

                                            (None, [], interim_steps)
                                        )
                                    )

#           10. Generate an interim state:

                                    for (interim_workers, interim_steps) in [

#               12. Return the interim state consisting of the workers
#                   list with each time-to-complete value reduced by
#                   1 and each step that has been completed replaced
#                   by None, ...

                                        (
                                            [
                                                (None, 0)
                                                if worker_time <= 1
                                                else (worker_step, worker_time - 1)
                                                for (worker_step, worker_time) in workers
                                            ]
                                            ,

#                        ... and the _sorted_ list of remaining steps
#                   with the completed steps skipped and also filtered out
#                   of the predecessor sets for each still-remaining step.

                                            sorted(
                                                (predecessors - completed_steps, step)
                                                for (predecessors, step) in remaining_steps
                                                if step not in completed_steps
                                            )
                                        )

#               11. Determine the set of steps that just completed
#                   by finding the step values for each worker whose
#                   time-to-complete is equal to 1.

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

#   6.  Run the reduction over the `range` of one plus the maximum
#       number of seconds that the process would take if only one step
#       could be performed at a time:  `xrange(1 + 60 * num_steps +
#       sum(ordinal_step_values))`.  The value of this is called the
#       `clock`.

                        xrange(
                            1
                            + sum(
                                step_base_time + step[1]
                                for step in modified_step_list
                            )
                        )
                        ,

#   5.  The initial state is `(None, [(None, 0)]*workers,
#       modified_full_predecessors_list)`

                        (None, [(None, 0)] * num_workers, modified_step_list)
                    )

#   1.  Start by generating the full list of predecessors for each step,
#       using the `full_predecessors_list` lambda above, then transform
#       each step letter to its ordinal value (where A is 1 and Z is 26).
#       (Because this is a map/reduce expression, the starting value is
#       at the end of the expression)

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

#   19. When the full reduction is complete, just return the final time
#       from the reduction state.

            )[0]

if __name__ == '__main__':

    sample_data = process_input_data(open(__file__.rsplit('.')[0] + '.sample').read())

    print "sample data: part 1 = {}".format(part_1(sample_data))
    print "sample data: part 2 = {}".format(part_2(sample_data, 2, 0))

    input_data = process_input_data(open(__file__.rsplit('.')[0] + '.input').read())

    print "real input: part 1 = {}".format(part_1(input_data))
    print "real input: part 2 = {}".format(part_2(input_data, 5, 60))
