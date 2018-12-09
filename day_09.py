
import re
import sys
import itertools

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

# extract the number of players and highest numbered marble from the input data

process_input_data = lambda input_data: (
            tuple(int(x) for x in re.match('([0-9]+) players; last marble is worth ([0-9]+) points', input_data).groups())
        )

########################################################################
#
# Generate the game results using a reduction, based on the inputs
# `num_players` and `max_marble`.
#
# The reduction state is a tuple of `(scores, circle, index)`, where...
#
#   *   `scores` is a list containing the score for each player, indexed
#       from 0 to `num_players - 1`;
#
#   *   `circle` is the list containing the current marble circle, with
#       with subsequent marbles progressing clockwise around the circle;
#
#   *   and `index` is the index into `circle` which contains the
#       "current" marble.
#
#   1.  The reduction runs across the range of numbers from 1 to
#       `max_marble`.
#
#   2.  The initial state of the reduction consists of 0 scores for each
#       player (i.e.  `[0] * num_players`), the initial marble circle
#       containing only marble 0 (`[0]`), and the index of marble 0 (`0`).
#
#   3.  The next state depends on the marble number:
#
#       4.  If the marble number is a multiple of 23:
#
#           5.  The current player (which is `(marble - 1) % num_players`)
#               has their score increased by the marble number plus the
#               marble stored in the circle at location `index - 7` (which
#               will automatically wrap around with Python's indexing);
#           
#           6.  The marble at location `index - 7` is removed from the
#               circle;
#
#           7.  And the current marble is set to the location of the deletion,
#               wrapped a second time around the _reduced_ length of the circle.
#
#       8.  Otherwise...
#
#           9.  The current scores remain the same;
#
#           10. The new marble is inserted at location `index + 2`
#               (wrapping around _one more than_ the length of the
#               marble circle, to allow for insertion at the end
#               of the list);
#
#           11. And the current marble is set to location `index + 2`
#               (again, wrapping around _one more than_ the length
#               of the _original_ marble circle).

game_results = lambda (num_players, max_marble): (
            reduce(

# The reduction state is a tuple of `(scores, circle, index)`, where...

                lambda (scores, circle, index), marble:

#   3.  The next state depends on the marble number:

                    (

#           5.  The current player (which is `(marble - 1) % num_players`)
#               has their score increased by the marble number plus the
#               marble stored in the circle at location `index - 7` (which
#               will automatically wrap around with Python's indexing);

                        scores[:(marble - 1) % num_players]
                        + [
                            scores[(marble - 1) % num_players]
                            + marble
                            + circle[index - 7]
                        ]
                        + scores[((marble - 1) % num_players) + 1:]

#           6.  The marble at location `index - 7` is removed from the
#               circle;

                        ,
                        circle[:(index - 7)]
                        + circle[(index - 7):][1:]
                        # the extra [1:] is to catch the fencepost error if index == 6

#           7.  And the current marble is set to the location of the deletion,
#               wrapped a second time around the _reduced_ length of the circle.

                        ,
                        ((index + len(circle) - 7) % len(circle)) % (len(circle) - 1)

                    )

#       4.  If the marble number is a multiple of 23:

                    if marble%23 == 0

#       8.  Otherwise...

                    else
                    (

#           9.  The current scores remain the same;

                        scores

#           10. The new marble is inserted _after_ `index + 1` (wrapping
#               around the length of the marble circle) -- in other words,
#               it's inserted at position `(index + 1) % len(circle) + 1`

                        ,
                        circle[:((index + 1) % len(circle)) + 1]
                        + [marble]
                        + circle[((index + 1) % len(circle)) + 1:]

#           11. And the current marble is set to the same location
#               as the insertion.

                        ,
                        ((index + 1) % len(circle)) + 1

                    )

#   1.  The reduction runs across the range of numbers from 1 to
#       `max_marble`.

                ,
                range(1, max_marble + 1)

#   2.  The initial state of the reduction consists of 0 scores for each
#       player (i.e.  `[0] * num_players`), the initial marble circle
#       containing only marble 0 (`[0]`), and the index of marble 0 (`0`).

                ,
                (
                    [0] * num_players
                    ,
                    [0]
                    ,
                    0
                )

            )
        )

########################################################################
#
# Part 1:   Return the highest score from the game results.

part_1 = lambda input_data: (
            max(game_results(input_data)[0])
        )

########################################################################
#
# Part 2:   Return the highest score from the game results with the
#           maximum marble value multiplied by 100.

part_2 = lambda input_data: (
            max(game_results( (input_data[0], input_data[1] * 100) )[0])
        )

if __name__ == '__main__':

    for sample_data_set in open(__file__.rsplit('.')[0] + '.sample').readlines():
        sample_data = process_input_data(sample_data_set)

        print "sample data: part 1 = {}".format(part_1(sample_data))
        print "sample data: part 2 = {}".format(part_2(sample_data))

        if not DEBUGGING: break

    if DEBUGGING: sys.exit(0)

    input_data = process_input_data(open(__file__.rsplit('.')[0] + '.input').read())

    print "real input: part 1 = {}".format(part_1(input_data))
    print "real input: part 2 = {}".format(part_2(input_data))
