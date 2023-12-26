# cython: binding=True
# cython: language_level=3

### General helper functions

def get_node_index(node):
    return node[0]

def get_node_content(node):
    return node[1]

cpdef dict node_changes(labelled_TD):
    r"""
    Record introduced and forgotten nodes in a directed labelled nice tree decomposition.

    INPUT:

    - ``labelled_TD`` -- a directed labelled nice tree decomposition,
      with the root as source of the dirgraph

    OUTPUT:

    - A dictionary of recorded nodes, where the `key` is node index, and
      the `value` is the introduced/forgotten node

    EXAMPLES::

        sage: from sage.graphs.graph_decompositions.tree_decomposition import label_nice_tree_decomposition
        sage: from sage.graphs.hom_count import node_changes
        sage: bip_one_four = graphs.CompleteBipartiteGraph(1, 4)
        sage: nice_tree_decomp = bip_one_four.treewidth(certificate=True, nice=True)
        sage: root = sorted(nice_tree_decomp)[0]
        sage: dir_labelled_TD = label_nice_tree_decomposition(nice_tree_decomp, root, directed=True)
        sage: node_changes(dir_labelled_TD)
        {1: 1, 2: 1, 3: 4, 5: 4, 6: 4, 7: 3, 8: 2, 9: 0, 10: 0, 11: 3, 12: 2}
    """
    cdef dict node_changes_dict = {}
    cdef int node_index
    cdef node_vertex_set, child_vertex_set, extra_vertex
    cdef str node_type

    for node in sorted(labelled_TD):
        node_index, node_vertex_set = node

        node_type = labelled_TD.get_vertex(node)

        if node_type in ['intro', 'forget']:
            child_vertex_set = labelled_TD.neighbors_out(node)[0][1]
            extra_vertex = (node_vertex_set.symmetric_difference(child_vertex_set)).pop()
            node_changes_dict[node_index] = extra_vertex

        # match node_type:
        #     case 'intro':
        #         child_vertex_set = labelled_TD.neighbors_out(node)[0][1]
        #         # Get one element from the one-element set
        #         (extra_vertex,) = node_vertex_set.symmetric_difference(child_vertex_set)
        #         node_changes_dict[node_index] = extra_vertex
        #     case 'forget':
        #         child_vertex_set = labelled_TD.neighbors_out(node)[0][1]
        #         # Get one element from the one-element set
        #         (extra_vertex,) = node_vertex_set.symmetric_difference(child_vertex_set)
        #         node_changes_dict[node_index] = extra_vertex

    return node_changes_dict


### For integer representation

cpdef int extract_bag_vertex(int mapping, int index, int graph_size):
    r"""
    Extract the bag vertex of `index` from `mapping`
    """
    # Equivalent to taking the floor
    return mapping // int(graph_size ** index) % graph_size

cpdef int add_vertex_into_mapping(int new_vertex, int mapping, int index, int graph_size):
    r"""
    Insert `new_vertex` at `index` into `mapping`
    """
    cdef int temp = graph_size ** index
    cdef int right_digits = mapping % temp
    cdef int left_digits = mapping - right_digits

    return graph_size * left_digits + temp * new_vertex + right_digits

cpdef int remove_vertex_from_mapping(int mapping, int index, int graph_size):
    r"""
    Return a new mapping from removing vertex of `index` from `mapping`
    """
    cdef int left_digits = mapping - (mapping % int(graph_size ** (index + 1)))
    cdef int right_digits = mapping % int(graph_size ** index)

    return left_digits // graph_size + right_digits
