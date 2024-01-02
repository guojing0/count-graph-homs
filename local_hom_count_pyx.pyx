from local_tree_decomp import *
from helper_functions cimport *

# In integer rep, the DP table is of the following form:
# { node_index: [1, 2, 3, 4, 5],
#   second_node_index: [10, 20, 30, 40, 50], ...}

cpdef int count_homomorphisms_pyx(graph, target_graph):
    r"""
    Return the number of homomorphisms from the graph `G` to the graph `H`.

    A homomorphism from a graph `G` to a graph `H` is a function
    `\varphi : V(G) \mapsto V(H)`, such that for any edge `uv \in E(G)` the
    pair `\varphi(u) \varphi(v)` is an edge of `H`.

    For more information, see the :wikipedia:`Graph_homomorphism`.

    ALGORITHM:

    This is an implementation based on the proof of Prop. 1.6 in [CDM2017]_.

    INPUT:

    - ``graph`` -- a Sage graph

    - ``target_graph`` -- the graph to which ``G`` is sent

    OUTPUT:

    - an integer, the number of homomorphisms from `graph` to `target_graph`

    EXAMPLES::

        sage: graph = graphs.CompleteBipartiteGraph(1, 4)
        sage: target_graph = graphs.CompleteGraph(4)
        sage: from sage.graphs.hom_count_pyx import count_homomorphisms_pyx
        sage: count_homomorphisms_pyx(graph, target_graph)
        324
    """
    from sage.graphs.graph import Graph

    if not isinstance(graph, Graph):
        raise ValueError("the first argument must be a sage Graph")
    if not isinstance(target_graph, Graph):
        raise ValueError("the second argument must be a sage Graph")

    cdef int root
    cdef list DP_table
    cdef dict node_changes_dict
    cdef str node_type
    cdef list tree_decomp, nice_tree_decomp
    cdef tuple node

    graph._scream_if_not_simple()
    target_graph._scream_if_not_simple()

    tree_decomp = graph.treewidth(certificate=True)
    nice_tree_decomp = make_nice_tree_decomposition(graph, tree_decomp)
    root = sorted(nice_tree_decomp)[0]

    # Make it into directed graph for better access
    # to children and parent, if needed
    #
    # Each node in a labelled nice tree decomposition
    # has the following form:
    #
    # (node_index, bag_vertices) node_type
    #
    # Example: (5, {0, 4}) intro
    dir_labelled_TD = label_nice_tree_decomposition(nice_tree_decomp, root, directed=True)

    # `node_changes_dict` is responsible for recording introduced and
    # forgotten vertices in a nice tree decomposition
    node_changes_dict = node_changes(dir_labelled_TD)

    # `DP_table` is a vector/list of dictionaries
    # Each element (dict) corresponds to the (induced) hom's of a tree node.
    # For each pair inside a dict, the key is the hom, and the value is the number of hom's:
    #
    # An example of K2 to K3, the values are arbitrary for demo purpose:
    #
    # [{((4, 0), (5, 1)): 10,
    #   ((4, 0), (5, 2)): 20,
    #   ((4, 1), (5, 0)): 30,
    #   ((4, 1), (5, 2)): 40,
    #   ((4, 2), (5, 0)): 50,
    #   ((4, 2), (5, 1)): 60}, {}, ...]
    DP_table = [{} for _ in range(len(dir_labelled_TD))]

    # Whether it's BFS or DFS, every node below join node(s) would be
    # computed first, so we can safely go bottom-up.
    for node in reversed(dir_labelled_TD.vertices()):
        node_type = dir_labelled_TD.get_vertex(node)

        if node_type == 'intro':
            _add_intro_node_pyx(DP_table, node, dir_labelled_TD, graph, target_graph, node_changes_dict)
        elif node_type == 'forget':
            _add_forget_node_pyx(DP_table, node, dir_labelled_TD, graph, target_graph, node_changes_dict)
        elif node_type == 'join':
            _add_join_node_pyx(DP_table, node, dir_labelled_TD)
        else:
            _add_leaf_node_pyx(DP_table, node)

    return DP_table[0][0]

### Main adding functions

cdef void _add_leaf_node_pyx(list DP_table, int node):
    r"""
    Add the leaf node to the DP table and update it accordingly.
    """
    cdef int node_index
    node_index = get_node_index(node)
    DP_table[node_index] = [1]

cdef void _add_intro_node_pyx(list DP_table, tuple node, graph_TD, graph, target_graph, dict node_changes_dict):
    cdef int node_index, child_node_index, intro_vtx_index, target_graph_size, mapped, mapping, target_vtx
    cdef tuple node_vtx_tuple, child_node_vtx_tuple
    cdef list node_nbhs_in_bag, mapped_nbhs_in_target, mappings_count, child_DP_entry

    # Basic setup
    node_index, node_vertices = node
    node_vtx_tuple = tuple(node_vertices)

    child_node_index, child_node_vtx = graph_TD.neighbors_out(node)[0]
    child_node_vtx_tuple = tuple(child_node_vtx)

    target_graph_size = len(target_graph)
    mappings_length_range = range(int(target_graph_size ** len(node_vtx_tuple)))
    mappings_count = [0 for _ in mappings_length_range]

    # Intro node specifically
    intro_vertex = node_changes_dict[node_index]
    intro_vtx_index = node_vtx_tuple.index(intro_vertex)

    # Neighborhood of the intro vertex in the graph
    node_nbhs_in_bag = [child_node_vtx_tuple.index(vtx) for vtx in child_node_vtx_tuple
                            if graph.has_edge(intro_vertex, vtx)]

    child_DP_entry = DP_table[child_node_index]

    for mapped in range(len(child_DP_entry)):
        # Neighborhood of the mapped vertex of intro vertex in the target graph
        mapped_nbhs_in_target = [extract_bag_vertex(mapped, nbh, target_graph_size) for nbh in node_nbhs_in_bag]

        mapping = add_vertex_into_mapping(0, mapped, intro_vtx_index, target_graph_size)

        for target_vtx in target_graph:
            if is_valid_mapping(target_vtx, mapped_nbhs_in_target, target_graph):
                mappings_count[mapping] = child_DP_entry[mapped]

            mapping += int(target_graph_size ** intro_vtx_index)

    DP_table[node_index] = mappings_count

cdef void _add_forget_node_pyx(list DP_table, tuple node, graph_TD, graph, target_graph, dict node_changes_dict):
    cdef int node_index, child_node_index, target_graph_size, forgotten_vtx_index, mapping, extended_mapping, target_vtx, sum
    cdef tuple node_vtx_tuple, child_node_vtx_tuple
    cdef list mappings_count
    cdef dict child_DP_entry

    # Basic setup
    node_index, node_vertices = node
    node_vtx_tuple = tuple(node_vertices)

    child_node_index, child_node_vtx = graph_TD.neighbors_out(node)[0]
    child_node_vtx_tuple = tuple(child_node_vtx)

    target_graph_size = len(target_graph)
    mappings_length_range = range(int(target_graph_size ** len(node_vtx_tuple)))
    mappings_count = [0 for _ in mappings_length_range]

    # Forget node specifically
    forgotten_vtx = node_changes_dict[node_index]
    forgotten_vtx_index = child_node_vtx_tuple.index(forgotten_vtx)

    child_DP_entry = DP_table[child_node_index]

    for mapping in mappings_length_range:
        sum = 0
        extended_mapping = add_vertex_into_mapping(0, mapping, forgotten_vtx_index, target_graph_size)

        for target_vtx in target_graph:
            sum += child_DP_entry[extended_mapping]
            extended_mapping += int(target_graph_size ** forgotten_vtx_index)

        mappings_count[mapping] = sum

    DP_table[node_index] = mappings_count

cdef void _add_join_node_pyx(list DP_table, tuple node, graph_TD):
    cdef int node_index, left_child_index, right_child_index
    cdef set node_vertices
    cdef list mappings_count

    node_index, node_vertices = node
    left_child, right_child = [vtx for vtx in graph_TD.neighbors_out(node)
                                   if get_node_content(vtx) == node_vertices]
    left_child_index = get_node_index(left_child)
    right_child_index = get_node_index(right_child)

    mappings_count = [left_count * right_count for left_count, right_count
                        in zip(DP_table[left_child_index], DP_table[right_child_index])]

    DP_table[node_index] = mappings_count

### Helper functions

cpdef bint is_valid_mapping(int mapped_intro_vtx, list[int] mapped_nbhrs, target_graph):
    cdef int vtx
    for vtx in mapped_nbhrs:
        if not target_graph.has_edge(mapped_intro_vtx, vtx):
            return False

    return True