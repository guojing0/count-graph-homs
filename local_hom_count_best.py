from math import prod

from sage.graphs.graph import Graph

from local_tree_decomp import *
from help_functions import *

# In integer rep, the DP table is of the following form:
# { node_index: [1, 2, 3, 4, 5],
#   second_node_index: [10, 20, 30, 40, 50], ...}

class GraphHomomorphismCounter:
    def __init__(self, graph, target_graph, density_threshold=0.5, graph_clr=None, target_clr=None, colourful=False):
        r"""
        INPUT:

        - ``graph`` -- a Sage graph

        - ``target_graph`` -- the graph to which ``graph`` is sent

        - ``density_threshold`` (default: 0.5) -- the desnity threshold for `target_graph` representation

        - ``graph_clr`` (default: None) -- a list of integers representing the colours of the vertices of `graph`

        - ``target_clr`` (default: None) -- a list of integers representing the colours of the vertices of `target_graph`

        - ``colourful`` (default: False) -- whether the graph homomorphism is colour-preserving
        """
        self.graph = graph
        self.target_graph = target_graph
        self.density_threshold = density_threshold
        self.graph_clr = graph_clr
        self.target_clr = target_clr
        self.colourful = colourful

        if not isinstance(graph, Graph):
            raise ValueError("first argument must be a sage Graph")
        if not isinstance(target_graph, Graph):
            raise ValueError("second argument must be a sage Graph")

        if colourful and (graph_clr is None or target_clr is None):
            raise ValueError("Both graph_clr and target_clr must be provided when colourful is True")

        self.graph._scream_if_not_simple()
        self.target_graph._scream_if_not_simple()

        self.tree_decomp = graph.treewidth(certificate=True)
        self.nice_tree_decomp = make_nice_tree_decomposition(graph, self.tree_decomp)
        self.root = sorted(self.nice_tree_decomp)[0]

        # Make it into directed graph for better access
        # to children and parent, if needed
        #
        # Each node in a labelled nice tree decomposition
        # has the following form:
        #
        # (node_index, bag_vertices) node_type
        #
        # Example: (5, {0, 4}) intro
        self.dir_labelled_TD = label_nice_tree_decomposition(self.nice_tree_decomp, self.root, directed=True)

        # `node_changes_dict` is responsible for recording introduced and
        # forgotten vertices in a nice tree decomposition
        self.node_changes_dict = node_changes(self.dir_labelled_TD)

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
        self.DP_table = [{} for _ in range(len(self.dir_labelled_TD))]


    def count_homomorphisms_best(self):
        r"""
        Return the number of homomorphisms from the graph `G` to the graph `H`.

        A homomorphism from a graph `G` to a graph `H` is a function
        `\varphi : V(G) \mapsto V(H)`, such that for any edge `uv \in E(G)` the
        pair `\varphi(u) \varphi(v)` is an edge of `H`.

        For more information, see the :wikipedia:`Graph_homomorphism`.

        ALGORITHM:

        This is an implementation based on the proof of Prop. 1.6 in [CDM2017]_.

        OUTPUT:

        - an integer, the number of homomorphisms from `graph` to `target_graph`

        EXAMPLES::

            sage: graph = graphs.CompleteBipartiteGraph(1, 4)
            sage: target_graph = graphs.CompleteGraph(4)
            sage: from sage.graphs.hom_count_best import count_homomorphisms_best
            sage: count_homomorphisms_best(graph, target_graph)
            324
        """
        # Whether it's BFS or DFS, every node below join node(s) would be
        # computed first, so we can safely go bottom-up.
        for node in reversed(self.dir_labelled_TD.vertices()):
            node_type = self.dir_labelled_TD.get_vertex(node)
            print("\nNode: ", node, node_type)

            match node_type:
                case 'intro':
                    self._add_intro_node_best(node)
                case 'forget':
                    self._add_forget_node_best(node)
                case 'join':
                    self._add_join_node_best(node)

                case _: 
                    self._add_leaf_node_best(node)

        return self.DP_table[0][0]

    ### Main adding functions

    def _add_leaf_node_best(self, node):
        r"""
        Add the leaf node to the DP table and update it accordingly.
        """
        node_index = get_node_index(node)
        self.DP_table[node_index] = [1]

    def _add_intro_node_best(self, node):
        r"""
        Add the intro node to the DP table and update it accordingly.
        """
        # Basic setup
        node_index, node_vertices = node
        node_vtx_tuple = tuple(node_vertices)

        child_node_index, child_node_vtx = self.dir_labelled_TD.neighbors_out(node)[0]
        child_node_vtx_tuple = tuple(child_node_vtx)

        target_graph_size = len(self.target_graph)

        # If `colourful` is True, we can reduce the size of each DP table entry,
        # since we only need to consider colour partitions: Each vertex with some
        # colour in G should only map to its colour partition class in H.
        if self.colourful:
            node_clr_counter = count_occurrences([self.graph_clr[i] for i in node_vtx_tuple])
            target_clr_counter = count_occurrences(self.target_clr)
            clr_intersection = list_intersection(node_clr_counter, self.target_clr) # relevant colours
            print(node_clr_counter, target_clr_counter, clr_intersection)

            mappings_length = prod(target_clr_counter[i] ** node_clr_counter[i] for i in clr_intersection)
            print("Mappings length: ", mappings_length)
        else:
            mappings_length = target_graph_size ** len(node_vtx_tuple)

        mappings_length_range = range(mappings_length)
        mappings_count = [0 for _ in mappings_length_range]

        target_density = self.target_graph.density()
        target_is_dense = target_density >= self.density_threshold

        if target_is_dense:
            target_adj_mat = self.target_graph.adjacency_matrix()

        # For use in `is_valid_mapping` only
        target = target_adj_mat if target_is_dense else self.target_graph

        # Intro node specifically
        intro_vertex = self.node_changes_dict[node_index]
        intro_vtx_index = node_vtx_tuple.index(intro_vertex)

        # Neighborhood of the intro vertex in the graph
        node_nbhs_in_bag = [child_node_vtx_tuple.index(vtx) for vtx in child_node_vtx_tuple
                                if self.graph.has_edge(intro_vertex, vtx)]

        child_DP_entry = self.DP_table[child_node_index]

        # Colourful processing
        if self.colourful:
            graph_clr_base = max(self.graph_clr) + 1
            graph_clr_int = encode_clr_list(self.graph_clr, graph_clr_base)
            intro_vtx_clr = decode_clr_int(graph_clr_int, graph_clr_base, intro_vertex)

            target_clr_base = max(self.target_clr) + 1
            target_clr_int = encode_clr_list(self.target_clr, target_clr_base)

        for mapped in range(len(child_DP_entry)):
            # Neighborhood of the mapped vertex of intro vertex in the target graph
            mapped_nbhs_in_target = [extract_bag_vertex(mapped, nbh, target_graph_size) for nbh in node_nbhs_in_bag]
            print("Mapped: ", mapped)
            print("Mapped nbhs in target: ", mapped_nbhs_in_target)

            mapping = add_vertex_into_mapping(0, mapped, intro_vtx_index, target_graph_size)

            for target_vtx in self.target_graph:
                if self.colourful:
                    target_vtx_index = tuple(self.target_graph).index(target_vtx)
                    # If the colours do not match, skip current iteration and
                    # move on to the next vertex.
                    # if self.graph_clr[intro_vertex] != self.target_clr[target_vtx_index]:
                    target_vtx_clr = decode_clr_int(target_clr_int, target_clr_base, target_vtx_index)
                    if intro_vtx_clr != target_vtx_clr:
                        continue

                print("target vertex: ", target_vtx)

                if is_valid_mapping(target_vtx, mapped_nbhs_in_target, target):
                    print("mapping: ", mapping)
                    mappings_count[mapping] = child_DP_entry[mapped]

                if self.colourful:
                    max_colour_size = max(max(node_clr_counter[i], target_clr_counter[i]) for i in clr_intersection)
                    mapping += target_graph_size ** max_colour_size
                    ## |induced subgraph of target graph| ** intro vtx index
                else:
                    mapping += target_graph_size ** intro_vtx_index
                print("DP table entry: {}\n".format(mappings_count))

        self.DP_table[node_index] = mappings_count

    def _add_forget_node_best(self, node):
        r"""
        Add the forget node to the DP table and update it accordingly.
        """
        # Basic setup
        node_index, node_vertices = node
        node_vtx_tuple = tuple(node_vertices)

        child_node_index, child_node_vtx = self.dir_labelled_TD.neighbors_out(node)[0]
        child_node_vtx_tuple = tuple(child_node_vtx)

        target_graph_size = len(self.target_graph)
        mappings_length_range = range(target_graph_size ** len(node_vtx_tuple))
        mappings_count = [0 for _ in mappings_length_range]

        # Forget node specifically
        forgotten_vtx = self.node_changes_dict[node_index]
        forgotten_vtx_index = child_node_vtx_tuple.index(forgotten_vtx)

        child_DP_entry = self.DP_table[child_node_index]

        for mapping in mappings_length_range:
            sum = 0
            extended_mapping = add_vertex_into_mapping(0, mapping, forgotten_vtx_index, target_graph_size)

            for target_vtx in self.target_graph:
                sum += child_DP_entry[extended_mapping]
                extended_mapping += target_graph_size ** forgotten_vtx_index

            mappings_count[mapping] = sum

        self.DP_table[node_index] = mappings_count

    def _add_join_node_best(self, node):
        r"""
        Add the join node to the DP table and update it accordingly.
        """
        node_index, node_vertices = node
        left_child, right_child  = [vtx for vtx in dir_labelled_TD.neighbors_out(node)
                                        if get_node_content(vtx) == node_vertices]
        left_child_index = get_node_index(left_child)
        right_child_index = get_node_index(right_child)

        mappings_count = [left_count * right_count for left_count, right_count
                            in zip(self.DP_table[left_child_index], self.DP_table[right_child_index])]

        self.DP_table[node_index] = mappings_count
