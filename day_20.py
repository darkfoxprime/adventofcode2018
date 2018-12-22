
import re
import sys
import itertools
import time
import operator
import os.path
import pprint

from blist import blist

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
        print ">>accumulate<< element={!r}".format(value)
        return func(state, value)
    for state in real_accumulate(iterable, debug):
        print ">>accumulate<< state={!r}".format(state)
        yield state
    print ">>accumulate<< done"

real_reduce = reduce
def debug_reduce(func, *args):
    def debug(state, value):
        print ">>reduce<< state={!r} value={!r}".format(state, value)
        return func(state, value)
    final = real_reduce(debug, *args)
    print ">>reduce<< final state={0!r}".format(final)
    return final

def debug_dropwhile(func, *args):
    def debug(value):
        print ">>dropwhile<< value={!r}".format(value)
        ret = func(value)
        print ">>dropwhile<< ret={!r}".format(ret)
        return ret
    for state in itertools.dropwhile(debug, *args):
        print ">>dropwhile<< yielding {!r}".format(state)
        yield state
    print ">>dropwhile<< done"

if DEBUGGING:

    print "Debugging version of `reduce` enabled"

    reduce = debug_reduce

if DEBUGGING:

    print "Debugging version of `accumulate` enabled"

    accumulate = debug_accumulate

########################################################################
#
# parse_path_expr_to_nfa:
#
# A path expression is a start marker (`^`), a series of path
# components, and a finish marker (`$`).
#
# Each "path component" is either
#     *   a path sequence (a string composed of `N`, `E`, `S`, or `W`
#         letters only), or
#     *   a choice, enclosed in parentheses (`(`...`)`), with one or
#         more path component alternatives separated by `|` vertical
#         bars.
#
# This is a simple recursive-descent parser using a regex to split the
# path expression into tokens, a reduction to process the token stream
# into an NFA (non-deterministic finite automata) that represents the
# expression, and is then simplified to remove as many empty links
# (connections with no path component) between NFAs as possible.
#
# The NFA is represented as a set of nodes, with one node designated
# as the 'start' node and possibly many nodes designated as 'finish
# nodes.
# (*) how this is done is yet to be determined.
#
# Each node is represented in two ways:
#     *   Any time a node is referenced, it is represented by a "node
#         id", an integer, which is the index into the "node list" at
#         which the node can be found.
#     *   Within the node list, a node is represented by a list (or
#         tuple) of tuples.  Each inner tuple represents a link from
#         this node to another node; the link consists of the path
#         sequence (possibly empty) that associates the two nodes
#         together, and the node id of the node to which the link
#         connects.  If a node is represented by a tuple, it is
#         considered _complete_, and will not have any additional
#         links added to it.  A node represented by a list is
#         _incomplete_ and is still being processed.
#
# The NFA is built up as a series of node pairs, each representing
# one "path component" as described above.  Each time a node pair is
# created, the node IDs for both nodes are pushed onto a "node stack"
# such that the last entry in the node stack is the node ID for the
# 2nd node, with the 1st node just before it.
#     *   A path sequence is represented by a node pair with one single
#         link on the first node connecting it to the second node via
#         the path sequence.  Once linked, the first node is changed to
#         a tuple to mark it as _complete_.
#
#         For example, if the node list contained only the node pair for
#         the path sequence `'NEWS'`, it would look like this:
#         ```
#         [
#             ( ('NEWS', 1,), ),
#             [],
#         ]
#         ```
#         and the node stack would look like this:
#         ```
#         [ 0, 1, ]
#         ```
#         That is, node ID 0 is a _complete_ node that contains a single
#         link via the path sequence `'NEWS'` to node ID 1.
#         Node ID 1 is an _incomplete_ node that contains no links.
#
#         After a path sequence is created, if there is a node pair under
#         it on the node stack whose 1st node is marked as _complete_,
#         then the 2nd node of the underlying node pair is linked to
#         the first node of the new node pair, and the those two nodes
#         are removed from the node stack.
#
#         Continuing the above example, if the path sequence `'SEEN'` is
#         added to the NFA, a new node pair (node IDs 2 and 3) would be
#         created, resulting in a node stack of...
#         ```
#         [ 0, 1, 2, 3, ]
#         ```
#         and a node list of
#         ```
#         [
#             ( ('NEWS', 1,), ),
#             [],
#             ( ('SEEN', 3,), ),
#             [],
#         ]
#         ```
#         After being added, the check for a complete node underneath
#         results in the node pairs being linked...
#         ```
#         [
#             ( ('NEWS', 1,), ),
#             [ ('', 2), ],
#             ( ('SEEN', 3,), ),
#             [],
#         ]
#         ```
#         And the two newly-linked nodes being removed from the stack:
#         ```
#         [ 0, 3, ]
#         ```
#
#         Thus the node list is the complete list of all nodes, tied
#         together via the node stack, which is a list of connected
#         mini-NFAs.  This is expanded when we start dealing with
#         choices:
#
#     *   When a choice is first encountered (when the opening `(` is
#         seen), a new unlinked node pair is created and added to the
#         stack, but no links are initially added, and the new node
#         pair is not marked as complete.
#
#         Additional path sequences or choice-openings are processed
#         until either an alternate (`|`) is encountered, or the choice
#         closes (`)`).
#
#     *   When an alternate (`|`) is encountered, it's assumed that
#         the topmost node pair is complete (which is guaranteed
#         through the way the path expression is tokenized, as 
#         described below), and that the node pair below that is
#         the choice's node pair (guaranteed by the processing of
#         alternates and the closing `)`).
#
#         The alternate is processed by linking the first node of the
#         choice's node pair to the first node of the complete node
#         pair on top of the stack with an empty node sequence; linking
#         the second node of the complete node pair to the second node
#         of the choice's node pair, also with an empty node sequence;
#         and removing the top node pair from the stack.
#
#         For example, after the above node sequence was processed,
#         assume we now encounter a choice that starts with `(NEW|`.
#         First, the opening choice creates an empty, unlinked,
#         incomplete node pair...
#         ```
#         [
#             ( ('NEWS', 1,), ),
#             [ ('', 2), ],
#             ( ('SEEN', 3,), ),
#             [],
#             [],
#             [],
#         ]
#         ```
#         and pushes it onto the stack:
#         ```
#         [ 0, 3, 4, 5, ]
#         ```
#
#         Then the `NEW` path sequence is processed to create
#         a complete node pair on top of the stack.  That node
#         pair is _not_ linked because the choice node pair is
#         not complete:
#         ```
#         [
#             ( ('NEWS', 1,), ),
#             [ ('', 2), ],
#             ( ('SEEN', 3,), ),
#             [],
#             [],
#             [],
#             ( ('NEW', 7,), ),
#             [],
#         ]
#         ```
#         and a stack of
#         ```
#         [ 0, 3, 4, 5, 6, 7, ]
#         ```
#         Finally, the `|` is processed, linking the `NEW`
#         sequence into the choice node pair...
#         ```
#         [
#             ( ('NEWS', 1,), ),
#             [ ('', 2), ],
#             ( ('SEEN', 3,), ),
#             [],
#             [ ('', 6,), ],
#             [],
#             ( ('NEW', 7,), ),
#             [ ('', 5,), ],
#         ]
#         ```
#         and popping the sequence from the node stack:
#         ```
#         [ 0, 3, 4, 5, ]
#         ```
#
#     *   When the closing `)` for the choice is found, it's once again
#         assumed that the topmost node pair is complete (which is
#         guaranteed through the way the path expression is tokenized,
#         as described below), and that the node pair below that is the
#         choice's node pair (guaranteed by the processing of alternates
#         and the closing `)`).
#
#         The choice closing is processed by first linking the choice's
#         node pair to the complete node pair as described above, marking
#         the choice's node pair as complete, and finally, if the next
#         node pair down on the stack is complete, linking the choice's
#         node pair to the 2nd node of the next pair down and removing
#         the newly-connected nodes from the stack.
#         
#         Continuing the example above, assume the entire choice was
#         `(NEW|ESSEN)`.
#         We've already processed `(NEW|` above, resulting in a node
#         list of
#         ```
#         [
#             ( ('NEWS', 1,), ),
#             [ ('', 2), ],
#             ( ('SEEN', 3,), ),
#             [],
#             [ ('', 6,), ],
#             [],
#             ( ('NEW', 7,), ),
#             [ ('', 5,), ],
#         ]
#         ```
#         and node stack of:
#         ```
#         [ 0, 3, 4, 5, ]
#         ```
#
#         So now we process `ESSEN` resulting in the new path sequence
#         nodes added to the node list...
#         ```
#         [
#             ( ('NEWS', 1,), ),
#             [ ('', 2), ],
#             ( ('SEEN', 3,), ),
#             [],
#             [ ('', 6,), ],
#             [],
#             ( ('NEW', 7,), ),
#             [ ('', 5,), ],
#             ( ('ESSEN', 5,), ),
#             [],
#         ]
#         ```
#         and to the node stack:
#         ```
#         [ 0, 3, 4, 5, 8, 9, ]
#         ```
#         The choice closing would first link the `ESSEN` node pair in
#         to the choice...
#         ```
#         [
#             ( ('NEWS', 1,), ),
#             [ ('', 2), ],
#             ( ('SEEN', 3,), ),
#             [],
#             [ ('', 6,), ('', 8,), ],
#             [],
#             ( ('NEW', 7,), ),
#             [ ('', 5,), ],
#             ( ('ESSEN', 5,), ),
#             [ ('', 5,), ],
#         ]
#         ```
#         and remove it from the node stack...
#         ```
#         [ 0, 3, 4, 5, ]
#         ```
#         Then it would mark the choice node pair as complete...
#         ```
#         [
#             ( ('NEWS', 1,), ),
#             [ ('', 2), ],
#             ( ('SEEN', 3,), ),
#             [],
#             ( ('', 6,), ('', 8,), ),
#             [],
#             ( ('NEW', 7,), ),
#             [ ('', 5,), ],
#             ( ('ESSEN', 5,), ),
#             [ ('', 5,), ],
#         ]
#         ```
#         Link it to the previous complete node (as seen on the node
#         stack)...
#         ```
#         [
#             ( ('NEWS', 1,), ),
#             [ ('', 2), ],
#             ( ('SEEN', 3,), ),
#             [ ('', 4,), ],
#             ( ('', 6,), ('', 8,), ),
#             [],
#             ( ('NEW', 7,), ),
#             [ ('', 5,), ],
#             ( ('ESSEN', 5,), ),
#             [ ('', 5,), ],
#         ]
#         ```
#         And remove the newly-linked nodes from the stack:
#         ```
#         [ 0, 5, ]
#         ```
#
# At the end of this process, the node stack will be left either empty
# (if the node path was empty) or with a single pair of node ids,
# indicating the start and end nodes of all the possible paths.
#
# This process is accomplished through first tokenizing the path
# expression (minus the `^` and `$` begining and end markers) through
# a regular expression: `r'([\(\)\|])'`
#
# By splitting the path expression using that RE with the `()` parentheses
# for group matching, it's guaranteed that individual path components
# all end up separated by the punctuation marks, and it's guaranteed
# that there is at exactly one (possibly empty) path component between
# each pair of punctuation marks and at the beginning and end of the list.
#
# The initial NFA is then generated as a reduction, following the
# procedure described above.
#
# The initial state of the reduction is a tuple of two empty lists,
# the first of which is the node list and the second of which is the
# node stack.
# `( [], [], )`
#
# The reduction is run across the list of tokens generated by the
# regular expression tokenzer.
#
# At each step of the reduction...
#
#     If the next token is '(',
#
#        Return a new node list with:
#
#            Two empty nodes (empty lists) added to the node list,
#
#        and a new node stack with:
#
#            The new node IDs added to the end of the stack, in this order:
#            *   the length of the (original) node list,
#            *   and 1 plus the original length.
#
#     If the next token is '|',
#
#         Return a new node list with:
#
#             The node at index -4 on the stack replaced by a list with
#             an empty transition to the node at index -2 on the stack
#             added to it,
#
#             And the node at index -1 on the stack replaced by a list
#             with an empty transition to the node at index -3 on the
#             stack added to it,
#         
#         and a new node stack with
#
#             The last two entries removed.
#
#     If the next token is ')',
#
#         Return a new node list with:
#
#             The node at index -5 on the stack replaced by a list with
#             an empty transition added to the node at index -4 on the
#             stack added to it.  (These are guaranteed to exist because
#             of the way the string is tokenized).
#
#             The node at index -4 on the stack replaced by a *tuple* with
#             an empty transition to the node at index -2 on the stack
#             added to it,
#
#             And the node at index -1 on the stack replaced by a list
#             with an empty transition to the node at index -3 on the
#             stack added to it,
#
#        And a new node stack with
#
#            Entries `[:-5]` and the entry at `[-3]`.
#
#     Otherwise, this is a node sequence.
#
#         Return a new node list with:
#
#             The node at index -1 on the stack replaced by a list with
#             an empty transition added to the (as-yet-non-existent) node
#             with ID equal to the length of the node list, *only if* the
#             stack is at least 2 deep and the node at stack index -2 is
#             a tuple,
#
#             and with two new nodes added to the list:
#
#                 A tuple containing a tuple of the node sequence and
#                 the length of the node list + 1,
#
#                 and an empty list.
#
#         And a new node stack with:
#
#             The node stack up to `[:-1]` *only if* the node stack is
#             at least two deep and the node at node stack index -2 is a
#             tuple, otherwise the full node stack with a single element
#             added to it consisting of the length of the node list,
#
#             with one plus the length of the node list added to the stack.

parse_path_expr_to_nfa = lambda path_expr: (

# The initial NFA is then generated as a reduction, following the
# procedure described above.

            reduce(

# At each step of the reduction...

                lambda nodes, token: (

                    (

#        Return a new node list with:
#
#            Two empty nodes (empty lists) added to the node list,

                        nodes[0] + [ [], [], ]
                        ,

#        and a new node stack with:
#
#            The new node IDs added to the end of the stack, in this order:
#            *   the length of the (original) node list,
#            *   and 1 plus the original length.

                        nodes[1] + [ len(nodes[0]), 1 + len(nodes[0]), ]

                    )

#     If the next token is '(',

                    if token == '('
                    else

                    (

#         Return a new node list with:

#             The node at index -4 on the stack replaced by a list with
#             an empty transition to the node at index -2 on the stack
#             added to it,

                        nodes[0][:nodes[1][-4]]
                        + [
                            nodes[0][nodes[1][-4]] + [
                                ('', nodes[1][-2], ),
                            ]
                        ]

#             And the node at index -1 on the stack replaced by a list
#             with an empty transition to the node at index -3 on the
#             stack added to it,

                        + nodes[0][nodes[1][-3]:nodes[1][-1]]
                        + [
                            nodes[0][nodes[1][-1]] + [
                                ('', nodes[1][-3], ),
                            ]
                        ]
                        ,

#         and a new node stack with
#
#             The last two entries removed.

                        nodes[1][:-2]

                    )

#     If the next token is '|',

                    if token == '|'
                    else

                    (

#         Return a new node list with:
#
#             The node at index -5 on the stack replaced by a list with
#             an empty transition added to the node at index -4 on the
#             stack added to it.  (These are guaranteed to exist because
#             of the way the string is tokenized).

                        nodes[0][:nodes[1][-5]]
                        + [
                            nodes[0][nodes[1][-5]] + [
                                ('', nodes[1][-4], ),
                            ]
                        ]

#             The node at index -4 on the stack replaced by a *tuple* with
#             an empty transition to the node at index -2 on the stack
#             added to it,

                        + [
                            tuple(
                                nodes[0][nodes[1][-4]] + [
                                    ('', nodes[1][-2], ),
                                ]
                            )
                        ]

#             And the node at index -1 on the stack replaced by a list
#             with an empty transition to the node at index -3 on the
#             stack added to it,

                        + nodes[0][nodes[1][-3]:nodes[1][-1]]
                        + [
                            nodes[0][nodes[1][-1]] + [
                                ('', nodes[1][-3], ),
                            ]
                        ]
                        ,

#        And a new node stack with
#
#            Entries `[:-5]` and the entry at `[-3]`.

                        nodes[1][:-5] + nodes[1][-3:-2]

                    )

#     If the next token is ')',

                    if token == ')'
                    else

#     Otherwise, this is a node sequence.

                    (

#         Return a new node list with:

#             The node at index -1 on the stack replaced by a list with
#             an empty transition added to the (as-yet-non-existent) node
#             with ID equal to the length of the node list, *only if* the
#             stack is at least 2 deep and the node at stack index -2 is
#             a tuple,

                        (
                            (
                                nodes[0][:nodes[1][-1]]
                                + [
                                    nodes[0][nodes[1][-1]] + [
                                        ('', len(nodes[0]), )
                                    ]
                                ]
                                + nodes[0][nodes[1][-1]+1:]
                            )
                            if len(nodes[1]) > 1
                            and isinstance(nodes[0][nodes[1][-2]], tuple)
                            else nodes[0]
                        )

#             and with two new nodes added to the list:

                        + [

#                 A tuple containing a tuple of the node sequence and
#                 the length of the node list + 1,

                            ( ( token, len(nodes[0]) + 1, ), ),

#                 and an empty list.

                            []

                        ]
                        ,

#         And a new node stack with:
#
#             The node stack up to `[:-1]` *only if* the node stack is
#             at least two deep and the node at node stack index -2 is a
#             tuple, otherwise the full node stack with a single element
#             added to it consisting of the length of the node list,

                        (
                            nodes[1][:-1]
                            if len(nodes[1]) >= 2
                            and isinstance(nodes[0][nodes[1][-2]], tuple)
                            else nodes[1] + [ len(nodes[0]) ]
                        )

#             with one plus the length of the node list added to the stack.

                        + [ 1+len(nodes[0]) ]
                    )

                )
                ,

# This process is accomplished through first tokenizing the path
# expression (minus the `^` and `$` begining and end markers) through
# a regular expression: `r'([\(\)\|])'`

# The reduction is run across the list of tokens generated by the
# regular expression tokenzer.

                re.split(r'([\(\)\|])', path_expr)
                ,

# The initial state of the reduction is a tuple of two empty lists,
# the first of which is the node list and the second of which is the
# node stack.
# `( [], [], )`

                ( [], [], )

            )
        )

########################################################################
#
# simplify_path_expr:
#
# Simplify the NFA for a path expression by locating each node whose
# only transition is on an empty string, replacing all the transitions
# *to* that node with equivalent transitions to the node's transitions
# destination, and deleting the node.
#
# The input parameter is the `items()` form of the NFA dictionary, where
# each item is a node ID and the list or tuple that makes up that node,
# plus the two special items `^` and `$`, each mapping to a list with
# a single transition from `^` or `$`, respectively, to the start and
# final node IDs, respectively.
#
# This is done through an accumulator of a reduction, filtered through
# a `dropwhile`.
#
# The `dropwhile` drops NFA item lists from the accumulator as long as
# there is any NFA item in the list whose only transition has an
# empty string.
#
# The accumulator's iterator is a chain of the NFA items, plus an
# infinite counter.
#
# Each step of the accumulator is a reduction, ignoring the second
# argument of the iterator.
#
# The initial state of the reduction is the NFA items list from the
# accumulator.
#
# The reduction runs over the first NFA item found whose node has
# only one transition and that transition has an empty string.
#
# For that item, replace the list of dictionary items (the
# reduction state) with a filtered comprehension that...
#
#     *   Replaces any transition that targets the item's node id with
#         the same transition targeting the item's transition's target,
#
#     *   And filters out the item itself.

simplify_path_expr = lambda nfa_items: (

# This is ... filtered through a `dropwhile`.

            itertools.dropwhile(

# The `dropwhile` drops NFA item lists from the accumulator as long as
# there is any NFA item in the list whose only transition has an
# empty string.

                lambda filtered_nfa_items: (
                    # generator expression to test the contents of the list
                    max(
                        len(item[1]) == 1 and item[1][0][0] == ''
                        for item in filtered_nfa_items
                    )
                )
                ,

# This is done through an accumulator ...

                accumulate(

# The accumulator's iterator is a chain of the NFA items, plus an
# infinite counter.

                    itertools.chain(
                        [nfa_items]
                        ,
                        itertools.count(0)
                    )
                    ,

# Each step of the accumulator is a reduction, ignoring the second
# argument of the iterator.

                    lambda filtering_nfa_items, _: (

# ... of a reduction ...

                        reduce(

# For each such item, replace the list of dictionary items (the
# reduction state) with a filtered comprehension that...

                            lambda items, filtered_item: (
                                [
                                    (
                                        item[0]
                                        ,
                                        tuple(
                                            (
                                                transition[0]
                                                ,

#     *   Replaces any transition that targets the item's node id with
#         the same transition targeting the item's transition's target,

                                                filtered_item[1][0][1]
                                                if transition[1] == filtered_item[0]
                                                else transition[1]
                                            )
                                            for transition in item[1]
                                        )
                                    )
                                    for item in items

#     *   And filters out the item itself.

                                    if item != filtered_item
                                ]
                            )

                            ,

# The reduction runs over the NFA items list, filtered to find only
# those items whose node is one long and whose single node transition
# has an empty string:  `len(item[1]) == 1 and item[1][0][0] == ''`

                            [
                                (
                                    item
                                    for item in filtering_nfa_items
                                    if len(item[1]) == 1 and item[1][0][0] == ''
                                ).next()
                            ]
                            ,

# The initial state of the reduction is the NFA items list from the
# accumulator.

                            filtering_nfa_items

                        )
                    )

                )
            ).next()
        )

########################################################################
#
# convert path_nfa_to_dict_items
#
# Convert a path NFA from the node-list + node-stack format to a single
# list of items suitable for importing into a dictionary.
#
# ```
# (
#     [nodeTupleOrList, nodeTupleOrList, ...]
#     ,
#     [initialNodeID, finalNodeID]
# )
# ```
# ->
# ```
# [
#     (nodeID, nodeTupleOrList)
#     ,
#     (nodeID, nodeTupleOrList)
#     ,
#     ...
#     ,
#     ('^', [('^', initialNodeID)])
#     ,
#     ('$', [('$', finalNodeID)])
# ]
# ```

convert_path_nfa_to_dict_items = lambda path_nfa: (
            zip(
                range(len(path_nfa[0]))
                ,
                path_nfa[0]
            )
            + [
                ('^', [('^', path_nfa[1][0])]),
                ('$', [('$', path_nfa[1][1])]),
            ]
        )

########################################################################
#
# process_input_data:
#
# Parse the input data to an NFA, transform it to dictionary form
# (although not yet to an actual dictionary), simplify it by removing
# nodes that consist solely of a single empty transition, then
# convert the remaining list into an actual dictionary.

process_input_data = lambda input_data: (
            dict(
                simplify_path_expr(
                    convert_path_nfa_to_dict_items(
                        parse_path_expr_to_nfa(
                            input_data.strip(' \r\n^$')
                        )
                    )
                )
            )
        )

########################################################################
#
# `destination_of_path`:
#
# Compute the relative destination of a given path, by starting at (0,0)
# and adding (0,-1), (1,0), (0,1), or (-1,0) for each `N`, `E`, `S`, or
# `W` in the path.
#
# Do this via a simpler calculation, based on these observations:
#     * the order of the directions does not matter;
#     * therefore, directions can be combined: three (0,-1) movements
#       are equivalent to one (0,-3) movement;
#     * and the number of a given direction in the path is equal to
#       the length of the original path minus the length of the path
#       with that direction removed.

destination_of_path = lambda path: (
            (
                (len(path) - len(path.replace('E','')))
                - (len(path) - len(path.replace('W','')))
                ,
                (len(path) - len(path.replace('S','')))
                - (len(path) - len(path.replace('N','')))
            )
        )

########################################################################
#
# Part 1:
#
# Find the longest "shortest path" from the start to the end of a
# path expression.
# 
# Any given path expression will express one or more paths to one or
# more destinations.  Each destination has a shortest path that will
# reach that destination from the start.  This function needs to
# find the longest such "shortest path".
#
# The parsed input data is a dictionary containing an NFA which
# represents the path expression, starting from the `^` node of the
# dictionary.
#
# This is an accumulator that processes and re-processes a list of
# paths and following path expressions until all path expressions
# are "expressed".
#
#     The accumulator's iterator is a chain of
#
#         An iterator that returns the initial paths list - a list
#         containing a single tuple of an empty path and the parsed
#         input data.
#         And an infinite counter.
#
#     Each step of the accumulator...
#
#         Removes and examines the first path and path expression in
#         the paths list.
#
#         If the path expression is None or empty (its `$` and `^`
#         indices pointing to the same node), add the path back
#         to the end of the paths list with an expression of None.
#
#         Otherwise, extend the paths list by adding one or more new
#         path+expression tuples to the list via a list comprehension
#         against the transitions from current start node.
#
#         Each new path+expression tuple consists of the original path
#         with the transition path sequence appended to it, and a modified
#         path expression with the start node `^` now pointing to the
#         transition's destination node.
#
# The accumulator is passed through a `dropwhile` that drops the return
# values from the accumulator until all of the path expressions in the
# paths list are None (meaning the associated paths are complete).
#
# Each path then has its destination computed in a list comprehension.
#
# The destinations are grouped via `groupby`.
#
# Each destination then has its shortest path chosen.
#
# Finally, the length of the path to the destination with the longest
# "shortest path" is returned via `max` against the length of the paths
# to each destination.

part_1 = lambda input_data: (
#input_data); lambda: (

# Finally, the length ...

            len(

# Finally ... of the path to the destination with the longest "shortest
# path" is returned via `max` ...

                    max(

# Each destination then has its shortest path chosen.
                    [
                        min(pathsets, key = lambda pathset: len(pathset[0]))

# The destinations are grouped via `groupby`.

                        for (destination,pathsets) in itertools.groupby(

# Each path then has its destination computed (using the
# `destination_of_path` helper function) in a list comprehension.

                            sorted(
                                [
                                    (
                                        pathslist[0]
                                        ,
                                        destination_of_path(pathslist[0])
                                    )

# The accumulator is passed through a `dropwhile` that drops the return
# values from the accumulator until all of the path expressions in the
# paths list are None (meaning the associated paths are complete).

                                    for pathslist in itertools.dropwhile(
                                        lambda pathslist: (
                                            max(
                                                pathset[1] is not None
                                                for pathset in pathslist
                                            )
                                        )
                                        ,

# This is an accumulator that processes and re-processes a list of
# paths and following path expressions until all path expressions
# are "expressed".

                                        accumulate(

#     The accumulator's iterator is a chain of

                                            itertools.chain(

#         An iterator that returns the initial paths list - a list
#         containing a single tuple of an empty path and the parsed
#         input data.

                                                [
                                                    blist([ ( '', input_data ) ])
                                                ]
                                                ,

#         And an infinite counter.

                                                itertools.count(0)

                                            )
                                            ,

#     Each step of the accumulator...

                                            lambda pathslist, _: (

#         Removes and examines the first path and path expression in
#         the paths list.

                                                pathslist[1:] + (

#         If the path expression is None or empty (its `$` and `^`
#         indices pointing to the same node), add the path back
#         to the end of the paths list with an expression of None.

                                                    blist([(pathslist[0][0], None)])
                                                    if pathslist[0][1] is None
                                                    or pathslist[0][1]['^'][0][1]
                                                       == pathslist[0][1]['$'][0][1]
                                                    else

#         *** pathslist[0] is the pathset we're examining.
#         *** pathslist[0][0] is the path from that pathset.
#         *** pathslist[0][1] is the path expression (dictionary) from that pathset.
#         *** pathslist[0][1][x] is node 'x' (where 'x' can also be '^' or '$')
#         *** pathslist[0][1][x][y] is transition 'y' of node 'x'.
#         *** pathslist[0][1][x][y][0] is the path sequence for transition 'y'.
#         *** pathslist[0][1][x][y][1] is the destination node for transition 'y'.
#         *** For nodes '^' and '$', there is one transition with a path sequence
#         *** equal to the node id and a destination of the initial and final node
#         *** ids (respectively) of the entire path expression.

#         Otherwise, extend the paths list by adding one or more new
#         path+expression tuples to the list ...

                                                    blist(

#         Each new path+expression tuple consists of the original path
#         with the transition path sequence appended to it, and a modified
#         path expression with the start node `^` now pointing to the
#         transition's destination node.

                                                        (
                                                            pathslist[0][0] + transition[0]
                                                            ,
                                                            dict(
                                                                (
                                                                    item[0]
                                                                    ,
                                                                    (
                                                                        (
                                                                            '^'
                                                                            ,
                                                                            transition[1]
                                                                        ),
                                                                    )
                                                                )
                                                                if item[0] == '^'
                                                                else item
                                                                for item in
                                                                    pathslist[0][1].items()
                                                            )
                                                        )

#         ... via a list comprehension
#         against the transitions from current start node.

                                                        for transition in pathslist[0][1][
                                                            pathslist[0][1]['^'][0][1]
                                                        ]
                                                    )

                                                )

                                            ) # end of accumulate lambda

                                        ) # end of accumulate
                                    ).next() # end of dropwhile
                                ]
                                ,
                                key = lambda pathdest: pathdest[1]
                            )
                            ,

                            lambda pathset: pathset[1]
                        ) # end of groupby

                    ] # end of shortest-path list comprehension

                    ,

# Finally ... against the length of the paths to each destination.

                    key = lambda pathset: len(pathset[0])

# Finally, the ... destination with the longest "shortest path" is
# returned ...

                )[0] # end of max

            ) # end of len
        )


########################################################################
#
# Part 2:   ...

part_2 = lambda input_data: (
            None
        )

########################################################################
#
# Main controller

DEBUGGING = False

if __name__ == '__main__':

    base_filename = __file__.rsplit('.')[0]

    input_filename = '{}.input'.format(base_filename)
    input_data = open(input_filename).read()

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
        if DEBUGGING: print "\nprocessing {} with expected results {}".format(sample_filename, expected)
        result = part_1(process_input_data(sample_data))
        if DEBUGGING: result = '\n' + pprint.pformat(result) + '\n'
        t = time.time() - t
        print "{}: sample {}: part 1 = {}{}".format(t, sample_num, result, " (expected {})".format(expected) if result != expected else "")

    if DEBUGGING: sys.exit(0)

    t = time.time()
    if DEBUGGING: print "\nprocessing {}".format(sample_filename)
    result = part_1(process_input_data(input_data))
    if DEBUGGING: result = '\n' + pprint.pformat(result) + '\n'
    t = time.time() - t
    print "{}: input data: part 1 = {}".format(t, result)

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
        if DEBUGGING: print "\nprocessing {} with expected results {}".format(sample_filename, expected)
        result = part_2(process_input_data(sample_data))
        if DEBUGGING: result = '\n' + pprint.pformat(result) + '\n'
        t = time.time() - t
        print "{}: sample {}: part 2 = {}{}".format(t, sample_num, result, " (expected {})".format(expected) if result != expected else "")

    t = time.time()
    if DEBUGGING: print "\nprocessing {}".format(sample_filename)
    result = part_2(process_input_data(input_data))
    if DEBUGGING: result = '\n' + pprint.pformat(result) + '\n'
    t = time.time() - t
    print "{}: input data: part 2 = {}".format(t, result)

