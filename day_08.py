
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

# Transform the input string into a list of ints.

def process_input_data(input_data):
    return list(int(x) for x in input_data.split())


########################################################################
#
# Transform the input list into a flattened list of tree nodes.
#
# Each node is a 2-ple: the first item in the tuple is the list of child
# node numbers (0-indexed into the node list), and the second item in
# the tuple is the list of metadata: `( [children], [metadata] )`
#
# This is done using a reduction (of course):
#
#   The reduction state is a 2-ple, with the first item being the full
#   list of nodes (some in progress, some being built), and the second
#   item being the stack of node numbers in the process of being built,
#   with the innermost node number at the end.
#
#   Each node being built looks like a "real" node except that it has
#   the number of child nodes left to be added in the first position of
#   the child node list and the number of metadata items left to be
#   added in the first position of the metadata list - or an empty
#   metadata list if the number of metadata items is not yet known.
#   Any node that is complete has the child/metadata remaining counts
#   removed.
#
#   In the sample data, just after starting node 3 (called `D` in the
#   sample data), the node list would look like this:
#   ```
#       [
#           ( [1, 1], [3] ),
#           ( [], [10, 11, 12] ),
#           ( [1], [1] ),
#           ( [0], [] ),
#       ]
#   ```
#   And the stack would be:
#   ```
#       [ 0, 2, 3 ]
#   ```
#
#   Node 0 expected 2 children; one has already been processed and one
#   more is expected.  Node 0 expects 3 metadata items.
#
#   Node 1 has already been processed and is referenced by node 0's
#   children list.
#
#   Node 2 is expecting 1 child and 1 metadata item.
#
#   Node 3 is expecting 0 children, but the number of metadata items
#   is not yet known.
#
#   The nodes being worked on are, in order, node 0, node 2, and node 3.
#   When node 3 is complete, it will be added to node 2; when node 2 is
#   complete, it will be added to node 0.
#
########################################################################
#
#   1.  The reduction is initialized with a tuple holding entries for a
#       fake outer node:  A node list with a single node expecting one
#       child and no metadata entries, and a nodestack with a single
#       index of 0 for that node.
#       ```
#       (
#           [ ( [1], [0] ) ]
#           ,
#           [ 0 ]
#       )
#       ```
#
#   2.  The reduction runs over the input list of numbers.
#
#   3.  At each step of the reduction:
#
#       4.  Generate an interim state based on the input state and the
#           next number.  During this phase and while processing the
#           interim stack, the "last node" is the node that is indexed
#           by the last item in the node stack.
#
#           5.  If the metadata list of the last node is empty, return
#               an interim state with the next number placed in the last
#               node's metadata list.
#
#           6.  If the number of children expected in the last node
#               is greater than 0, return an interim state with a new
#               node added to the node list and the new node's index
#               (which is the length of the node list before it
#               included the new node) added to the node stack.  The new
#               node has the next number as the number of expected
#               children, and an empty metadata list.
#
#           7.  Otherwise, return an interim state with the last node's
#               expected metadata count decremented by 1 and the next
#               number added to its metadata list.
#
#       8.  If the interim state's last node's metadata count is 0,
#           return a new state.
#
#           The parent node is the second-to-last node index in the
#           node stack.
#
#           The child node is the last node index in the node stack.
#
#           Return the new node list, modifying the parent node to
#           include the index of the child node (minus 1, to account
#           for the removal of the first "fake" node from the node
#           list at the end of the reduction) and to decrement the
#           parent node's expected children count by 1, and modifying
#           the child node to remove the expected children count and
#           expected metadata count from its lists.
#
#           Return the new node stack with the last stack item popped
#           off the stack.
#
#       9.  Otherwise, just return the interim state.
#
#   10. At the end of the reduction, return the nodes in the node list
#       after the first, mapping the children node numbers to all be
#       decremented by 1.
#
########################################################################

build_flat_tree = lambda input_data: (

            reduce(

#   3.  At each step of the reduction:

                lambda (nodelist, nodestack), number:

                    # use the generator trick to allow me to reference
                    # the interim step through a variable name.
                    (

#   3.  At each step of the reduction:

#       8.  If the interim state's last node's metadata count is 0,
#           return a new state.
#
#           The parent node is the second-to-last node index in the
#           node stack.
#
#           The child node is the last node index in the node stack.
#
#           Return the new node list, modifying the parent node to
#           include the index of the child node (minus 1, to account
#           for the removal of the first "fake" node from the node
#           list at the end of the reduction) and to decrement the
#           parent node's expected children count by 1, and modifying
#           the child node to remove the expected children count and
#           expected metadata count from its lists.
#
#           Return the new node stack with the last stack item popped
#           off the stack.

                        (
                            interim_nodelist[:interim_nodestack[-2]]
                            + [(
                                [ interim_nodelist[interim_nodestack[-2]][0][0] - 1 ]
                                + interim_nodelist[interim_nodestack[-2]][0][1:]
                                + [interim_nodestack[-1] - 1]
                                ,
                                interim_nodelist[interim_nodestack[-2]][1]
                            )]
                            + interim_nodelist[interim_nodestack[-2]+1:interim_nodestack[-1]]
                            + [(
                                interim_nodelist[interim_nodestack[-1]][0][1:]
                                ,
                                interim_nodelist[interim_nodestack[-1]][1][1:]
                            )]
                            + interim_nodelist[interim_nodestack[-1]+1:]
                            ,
                            interim_nodestack[:-1]
                        )

                        if interim_nodelist[interim_nodestack[-1]][1]
                        and interim_nodelist[interim_nodestack[-1]][1][0] == 0

#       9.  Otherwise, just return the interim state.

                        else (interim_nodelist, interim_nodestack)

#       4.  Generate an interim state based on the input state and the
#           next number.  During this phase and while processing the
#           interim stack, the "last node" is the node that is indexed
#           by the last item in the node stack.

                        for (interim_nodelist, interim_nodestack) in [

#           5.  If the metadata list of the last node is empty, return
#               an interim state with the next number placed in the last
#               node's metadata list.

                            (
                                nodelist[:nodestack[-1]]
                                + [(
                                    nodelist[nodestack[-1]][0]
                                    ,
                                    [number]
                                )]
                                + nodelist[nodestack[-1]+1:]
                                ,
                                nodestack
                            )
                            if not nodelist[nodestack[-1]][1]

#           6.  If the number of children expected in the last node
#               is greater than 0, return an interim state with a new
#               node added to the node list and the new node's index
#               (which is the length of the node list before it
#               included the new node) added to the node stack.  The new
#               node has the next number as the number of expected
#               children, and an empty metadata list.

                            else
                            (
                                nodelist
                                + [(
                                    [number]
                                    ,
                                    []
                                )]
                                ,
                                nodestack
                                + [len(nodelist)]
                            )
                            if nodelist[nodestack[-1]][0][0] > 0

#           7.  Otherwise, return an interim state with the last node's
#               expected metadata count decremented by 1 and the next
#               number added to its metadata list.

                            else
                            (
                                nodelist[:nodestack[-1]]
                                + [(
                                    nodelist[nodestack[-1]][0]
                                    ,
                                    [ nodelist[nodestack[-1]][1][0] - 1 ]
                                    + nodelist[nodestack[-1]][1][1:]
                                    + [number]
                                )]
                                + nodelist[nodestack[-1]+1:]
                                ,
                                nodestack
                            )

                        ]
                    ).next()

                ,

#   2.  The reduction runs over the input list of numbers.

                input_data
                ,

#   1.  The reduction is initialized with a tuple holding entries for a
#       fake outer node:  A node list with a single node expecting one
#       child and no metadata entries, and a nodestack with a single
#       index of 0 for that node.
#       ```
#       (
#           [ ( [1], [0] ) ]
#           ,
#           [ 0 ]
#       )
#       ```

                ( [ ([1],[0]) ], [0] )

            )

#   10. At the end of the reduction, return the nodes in the node list
#       after the first.

        )[0][1:]


########################################################################
#
# Part 1:
#
#   Given the "flat tree" produced by `build_flat_tree`, sum the
#   contents of all the nodes' metadata lists.

part_1 = lambda input_data: (
            sum(
                sum(metadata)
                for (children, metadata) in
                    build_flat_tree(input_data)
            )
        )

########################################################################
#
# Part 2:
#
#   Given the "flat tree" produced by `build_flat_tree`, compute the
#   value of the first node.
#
#   The value of a node with no children is the sum of its metadata.
#
#   The value of a node with children is the sum of the values of the
#   nodes referenced by its metadata.  A metadata item of 1 references
#   the node's first child node (index 0), etc.  A metadata item of 0
#   or a metadata item whose value is greater than the number of child
#   nodes is not counted for the node's value.
#
#   Because of the way the "flat tree" is constructed, nodes with
#   children will always appear in the list before their children do.
#   Therefore, if we process the "flat tree" from the last node to
#   the first, we can replace each node with its value as we go, and
#   end with the total value in the entry of the tree.
#
#   Therefore, naturally, we do this with a reduction.  In this case,
#   the reduction state is the node list itself, and we are reducing
#   over the list of node indices from last to first.
#
#   1.  The initial state of the reduction is the node list.
#
#   2.  The reduction runs over the list of node indices from last
#       to first:  `xrange(len(nodelist)-1, -1, -1)`
#
#   3.  At each step of the reduction:
#
#       4.  If this node has no children, return the new state with
#           this node replaced by the sum of its metadata.
#
#       5.  Otherwise, return the new state with this node replaced
#           by a reduction of its metadata:
#
#           6.  The initial state is 0.
#
#           7.  The reduction runs over the node's metadata.
#
#           8.  At each step of the reduction:
#
#               9.  If the metadata is 0 or is greater than the
#                   number of children in the node, return the
#                   accumulated value.
#
#               10. Otherwise, return the accumulated value plus
#                   the value from the nodelist for the node indexed
#                   by the current node's child list at index
#                   (metadata - 1).
#
#   11. At the end of the reduction, return the first value in the
#       node list.

part_2 = lambda input_data: (
            # use the generator trick to allow me to reference the
            # "flat tree" node list twice:
            (

                reduce(

#   3.  At each step of the reduction:

                    lambda nodelist, index:

#       4.  If this node has no children, return the new state with
#           this node replaced by the sum of its metadata.

                    (
                        nodelist[:index]
                        + [ sum(nodelist[index][1]) ]
                        + nodelist[index+1:]
                    )
                    if not nodelist[index][0]

#       5.  Otherwise, return the new state with this node replaced
#           by a reduction of its metadata:

                    else
                    # generator trick again, this time just to put the complex
                    # reduction at the end of the expression rather
                    # than in the middle.
                    (
                        (
                            nodelist[:index]
                            + [ sum_of_children_values ]
                            + nodelist[index+1:]
                        )
                        for sum_of_children_values in [

                            reduce(

#           8.  At each step of the reduction:
                                lambda value, metadata:

#               9.  If the metadata is 0 or is greater than the
#                   number of children in the node, return the
#                   accumulated value.

                                    value
                                    if metadata < 1
                                    or metadata > len(nodelist[index][0])

#               10. Otherwise, return the accumulated value plus
#                   the value from the nodelist for the node indexed
#                   by the current node's child list at index
#                   (metadata - 1).

                                     else
                                     value
                                     + nodelist[nodelist[index][0][metadata-1]]

#           7.  The reduction runs over the node's metadata.

                                ,
                                nodelist[index][1]

#           6.  The initial state is 0.

                                ,
                                0

                            )

                        ]
                    ).next()

#   2.  The reduction runs over the list of node indices from last
#       to first:  `xrange(len(nodelist)-1, -1, -1)`

                    ,
                    xrange(len(nodelist)-1, -1, -1)

#   1.  The initial state of the reduction is the node list.

                    ,
                    nodelist

                )

                for nodelist in [
                    build_flat_tree(input_data)
                ]
            ).next()

#   11. At the end of the reduction, return the first value in the
#       node list.

        )[0]

if __name__ == '__main__':

    sample_data = process_input_data(open(__file__.rsplit('.')[0] + '.sample').read())

    print "sample data: part 1 = {}".format(part_1(sample_data))
    print "sample data: part 2 = {}".format(part_2(sample_data))

    if DEBUGGING: sys.exit(0)

    input_data = process_input_data(open(__file__.rsplit('.')[0] + '.input').read())

    print "real input: part 1 = {}".format(part_1(input_data))
    print "real input: part 2 = {}".format(part_2(input_data))
