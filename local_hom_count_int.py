from sage.graphs.graph import Graph

from local_hom_count import *

from local_tree_decomp import *

# In integer rep, the DP table is of the following form:
# { node_index: [1, 2, 3, 4, 5],
#   second_node_index: [10, 20, 30, 40, 50], ...}

def count_homomorphisms_int(graph, target_graph):
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
        sage: from sage.graphs.hom_count_int import count_homomorphisms_int
        sage: count_homomorphisms_int(graph, target_graph)
        995
    """
    if not isinstance(graph, Graph):
        raise ValueError("the first argument must be a sage Graph")
    if not isinstance(target_graph, Graph):
        raise ValueError("the second argument must be a sage Graph")

    graph._scream_if_not_simple()
    target_graph._scream_if_not_simple()

    # nice_tree_decomp = graph.treewidth(certificate=True)
    # root = sorted(nice_tree_decomp)[0]

    # Make it into directed graph for better access
    # to children and parent, if needed
    #
    # Each node in a labelled nice tree decomposition
    # has the following form:
    #
    # (node_index, bag_vertices) node_type
    #
    # Example: (5, {0, 4}) intro
    tree_decomp = graph.treewidth(certificate=True)
    nice_tree_decomp = make_nice_tree_decomposition(graph, tree_decomp)
    root = sorted(nice_tree_decomp)[0]
    dir_labelled_TD = label_nice_tree_decomposition(nice_tree_decomp, root, directed=True)

    # `node_changes_dict` is responsible for recording introduced and
    # forgotten vertices in a nice tree decomposition
    # from sage.graphs.hom_count import node_changes
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
        # print(node, node_type)
        # print()

        match node_type:
            case 'intro':
                _add_intro_node_int(DP_table, node, dir_labelled_TD, graph, target_graph, node_changes_dict)
            case 'forget' | 'root':
                _add_forget_node_int(DP_table, node, dir_labelled_TD, graph, target_graph, node_changes_dict)
            case 'join':
                _add_join_node_int(DP_table, node, dir_labelled_TD)

            # If `node` is the root or a leaf node
            case _: 
                _add_leaf_node_int(DP_table, node)

    # print(DP_table)

    return DP_table[0][0]

### Helper functions

def extract_bag_vertex(mapping, index, graph_size):
    r"""
    Extract the bag vertex of `index` from `mapping`
    """
    # Equivalent to taking the floor
    return mapping // (graph_size ** index) % graph_size

def is_valid_mapping(mapping, intro_vtx, node, graph, target_graph):
    node_index, node_vertices = node
    node_vtx_tuple = tuple(node_vertices) # since its type is `set` is a node

    target_graph_size = len(target_graph)

    intro_vtx_index = node_vtx_tuple.index(intro_vtx)
    mapped_intro_vtx = extract_bag_vertex(mapping, intro_vtx_index, target_graph_size)
    # print("valid mapping: node vtx tuple", node_vtx_tuple)
    for bag_vtx in node_vtx_tuple:
        bag_vtx_index = node_vtx_tuple.index(bag_vtx)
        mapped_bag_vtx = extract_bag_vertex(mapping, bag_vtx_index, target_graph_size)
        # print("in valid mapping", mapped_intro_vtx, mapped_bag_vtx)
        if graph.has_edge(intro_vtx, bag_vtx) and (not target_graph.has_edge(mapped_intro_vtx, mapped_bag_vtx)):
            return False

    return True

def remove_vertex_from_mapping(mapping, index, graph_size):
    r"""
    Return a new mapping from removing vertex of `index` from `mapping`
    """
    left_digits = mapping - (mapping % (graph_size ** (index + 1)))
    right_digits = mapping % (graph_size ** index)

    # print("remove_vertex_from_mapping args:", mapping, index, graph_size)
    # print("left and right digits:", left_digits, right_digits)

    return left_digits // graph_size + right_digits

def add_vertex_into_mapping(new_vertex, mapping, index, graph_size):
    temp = graph_size ** index
    right_digits = mapping % temp
    left_digits = mapping - right_digits

    return graph_size * left_digits + temp * new_vertex + right_digits

### Main adding functions

def _add_leaf_node_int(DP_table, node):
    node_index = get_node_index(node)
    DP_table[node_index] = [1]
    # DP_table[node_index] = {(): [1]}

def _add_intro_node_int(DP_table, node, graph_TD, graph, target_graph, node_changes_dict):
    node_index, node_vertices = node
    node_vtx_tuple = tuple(node_vertices)
    # print("node vtx tuple", node_vtx_tuple)

    child_node_index = get_node_index(graph_TD.neighbors_out(node)[0])
    # print("child_node_index", child_node_index)

    target_graph_size = len(target_graph)
    mappings_length_range = range(target_graph_size ** len(node_vtx_tuple))
    mappings_count = [0 for _ in mappings_length_range]

    intro_vertex = node_changes_dict[node_index]
    intro_vtx_index = node_vtx_tuple.index(intro_vertex)
    # print("intro vtx index", intro_vtx_index)

    for mapping in mappings_length_range:
        if is_valid_mapping(mapping, intro_vertex, node, graph, target_graph):
            child_mapping = remove_vertex_from_mapping(mapping, intro_vtx_index, target_graph_size)
            # print("mapping", mapping)
            # print("child_mapping", child_mapping)
            # print("mappings count {}".format(mappings_count))
            # print("DP table at child node {}\n".format(DP_table[child_node_index]))
            mappings_count[mapping] = DP_table[child_node_index][child_mapping]

    DP_table[node_index] = mappings_count

def _add_forget_node_int(DP_table, node, graph_TD, graph, target_graph, node_changes_dict):
    node_index, node_vertices = node
    node_vtx_tuple = tuple(node_vertices)
    # print("node_vtx_tuple", node_vtx_tuple)

    child_node_index, child_node_vtx = graph_TD.neighbors_out(node)[0]
    child_node_vtx_tuple = tuple(child_node_vtx)
    # print("child_node", child_node_index, child_node_vtx_tuple)

    target_graph_size = len(target_graph)
    mappings_length_range = range(target_graph_size ** len(node_vtx_tuple))
    mappings_count = [0 for _ in mappings_length_range]

    forgotten_vtx = node_changes_dict[node_index]
    forgotten_vtx_index = child_node_vtx_tuple.index(forgotten_vtx)
    # print("forget vtx {} at index {}".format(forgotten_vtx, forgotten_vtx_index))

    for mapping in mappings_length_range:
        sum = 0

        for target_vtx in target_graph:
            extended_mapping = add_vertex_into_mapping(target_vtx, mapping, forgotten_vtx_index, target_graph_size)
            # print("ext mapping", extended_mapping)
            sum += DP_table[child_node_index][extended_mapping]

        mappings_count[mapping] = sum

    DP_table[node_index] = mappings_count

def _add_join_node_int(DP_table, node, graph_TD):
    node_index, node_vertices = node
    left_child, right_child  = [vtx for vtx in graph_TD.neighbors_out(node)
                                    if get_node_content(vtx) == node_vertices]
    left_child_index, left_child_content = left_child
    right_child_index, right_child_content = right_child

    mappings_count = [left_count * right_count for left_count, right_count
                        in zip(DP_table[left_child_index], DP_table[right_child_index])]

    DP_table[node_index] = mappings_count
