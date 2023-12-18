r"""
Counting the number of homomorphisms from a graph G to a graph H.

This module defines functions to compute the number of homomorphisms between
two graphs.

AUTHORS:

- Jing Guo (2023): initial version

REFERENCES:

- [CDM2017]

"""

from sage.graphs.graph import Graph

from local_tree_decomp import *

from collections import deque
from itertools import combinations, product


def count_homomorphisms(graph, target_graph):
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
        sage: from sage.graphs.hom_count import count_homomorphisms
        sage: count_homomorphisms(graph, target_graph)
        324
    """
    if not isinstance(graph, Graph):
        raise ValueError("the first argument must be a sage Graph")
    if not isinstance(target_graph, Graph):
        raise ValueError("the second argument must be a sage Graph")

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
    # print("node changes", node_changes_dict)

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

        match node_type:
            case 'intro':
                _add_intro_node(DP_table, node, dir_labelled_TD, graph, target_graph, node_changes_dict)
            case 'forget':
                _add_forget_node(DP_table, node, dir_labelled_TD, graph, target_graph, node_changes_dict)
            case 'join':
                _add_join_node(DP_table, node, dir_labelled_TD, graph, target_graph)

            case _: 
                _add_leaf_node(DP_table, node)

    # print(DP_table)

    return next(iter(DP_table[0].values()))


### Functions possible for the Graph class


def is_homomorphism(G, H, mapping):
    for edge in G.edges(labels=False):
        # print("edge", edge)
        # print("pair", mapping[edge[0]], mapping[edge[1]])
        if not H.has_edge(mapping[edge[0]], mapping[edge[1]]):
            return False
    return True

def enumerate_homomorphisms(graph, target_graph, as_tuples=False):
    graph_vertices = graph.vertices()
    target_vertices = target_graph.vertices()

    homomorphisms = []

    for mapping_tuple in product(target_vertices, repeat=len(graph_vertices)):
        mapping = dict(zip(graph_vertices, mapping_tuple))

        if is_homomorphism(graph, target_graph, mapping):
            homomorphisms.append(mapping)

    if as_tuples:
        return [tuple((k, v) for k, v in hom.items())
                    for hom in homomorphisms]
    return homomorphisms


### For tree decomp file


def node_changes(labelled_TD):
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
    node_changes_dict = {}

    for node in sorted(labelled_TD):
        node_index, node_vertex_set = node

        node_type = labelled_TD.get_vertex(node)
        match node_type:
            case 'intro':
                child_vertex_set = labelled_TD.neighbors_out(node)[0][1]
                # Get one element from the one-element set
                (extra_vertex,) = node_vertex_set.symmetric_difference(child_vertex_set)
                node_changes_dict[node_index] = extra_vertex
            case 'forget':
                child_vertex_set = labelled_TD.neighbors_out(node)[0][1]
                # Get one element from the one-element set
                (extra_vertex,) = node_vertex_set.symmetric_difference(child_vertex_set)
                node_changes_dict[node_index] = extra_vertex

    return node_changes_dict


### Private helper functions

def get_node_index(node):
    return node[0]

def get_node_content(node):
    return node[1]

def _add_leaf_node(DP_table, node):
    """
    Process the leaf node `node` and update the homomorphism count in the dynamic programming table accordingly.
    """
    node_index = node[0]
    DP_table[node_index] = {(): 1}

def _add_intro_node(DP_table, node, graph_TD, graph, target_graph, node_changes_dict):
    """
    Process the introduce node `node` and update the homomorphism count in the dynamic programming table accordingly.
    """
    node_index, node_vertices = node

    enum_homs = enumerate_homomorphisms(graph.subgraph(node_vertices),
                                       target_graph,
                                       as_tuples=True)

    # print("intro enum", enum_homs)

    for hom in enum_homs:
        child_hom = tuple((k, v) for k, v in hom if k != node_changes_dict[node_index])

        # I_{v} (h) = I_{w} (h'), `w` is child of `v`
        child_node_index = graph_TD.neighbors_out(node)[0][0]

        # print("child node index: {}, child hom: {}".format(child_node_index, child_hom))

        DP_table[node_index][hom] = DP_table[child_node_index][child_hom]
    # print("DP_table at this node", DP_table[node_index])

def _add_forget_node(DP_table, node, graph_TD, graph, target_graph, node_changes_dict):
    """
    Process the forget node `node` and update the homomorphism count in the dynamic programming table accordingly.
    """
    node_index, node_vertices = node
    forgotten_vtx = node_changes_dict[node_index]

    enum_homs = enumerate_homomorphisms(graph.subgraph(node_vertices),
                                       target_graph,
                                       as_tuples=True)
    
    # print("forget enum", enum_homs)

    for hom in enum_homs:
        sum = 0

        for target_vtx in target_graph:
            extended_hom = tuple(sorted(hom + ((forgotten_vtx, target_vtx),),
                                                key=lambda x: x[0]))
            # print("ext hom", extended_hom)
#             ext_hom_dict = dict(extended_hom)
#             print("ext hom", ext_hom_dict)
            if is_valid_mapping(graph, target_graph, extended_hom):
                # print("yay")
                child_node_index = graph_TD.neighbors_out(node)[0][0]
                # print("DP_table at child", DP_table[child_node_index])
                sum += DP_table[child_node_index][extended_hom]

        DP_table[node_index][hom] = sum
        # print("DP_table at this node", DP_table[node_index])

def _add_join_node(DP_table, node, graph_TD, graph, target_graph):
    """
    Process the join node `node` and update the homomorphism count in the dynamic programming table accordingly.
    """
    node_index, node_vertices = node
    left_child, right_child  = [vtx for vtx in graph_TD.neighbors_out(node)
                                    if get_node_content(vtx) == node_vertices]
    left_child_index = get_node_index(left_child)
    right_child_index = get_node_index(right_child)

    enum_homs = enumerate_homomorphisms(graph.subgraph(node_vertices),
                                       target_graph,
                                       as_tuples=True)

    for hom in enum_homs:
        DP_table[node_index][hom] = DP_table[left_child_index][hom] * DP_table[right_child_index][hom]


def is_valid_mapping(G, H, mapping):
    for (G_fst_vtx, H_fst_vtx), (G_snd_vtx, H_snd_vtx) in combinations(mapping, 2):
        if G.has_edge(G_fst_vtx, G_snd_vtx) and (not H.has_edge(H_fst_vtx, H_snd_vtx)):
            return False
    return True

### Bounded-degree homomorphism count

def count_homomorphisms_bounded_degree(graph, target_graph):
    pass
