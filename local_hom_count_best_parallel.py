import dask
from dask import delayed, compute

from concurrent.futures import ProcessPoolExecutor, as_completed, wait

from math import prod

from sage.graphs.graph import Graph

from local_tree_decomp import *
from help_functions import *

# In integer rep, the DP table is of the following form:
# { node_index: [1, 2, 3, 4, 5],
#   second_node_index: [10, 20, 30, 40, 50], ...}

class ParallelGraphHomomorphismCounter:
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

        # Bookkeeping for colourful mappings
        self.actual_target_graph = target_graph
        self.actual_target_size = len(self.actual_target_graph)

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


    # @delayed
    def process_node(self, node):
        node_type = self.dir_labelled_TD.get_vertex(node)
        match node_type:
            case 'intro':
                result = self._add_intro_node_parallel(node)
            case 'forget':
                result = self._add_forget_node_parallel(node)
            case 'join':
                result = self._add_join_node_parallel(node)
            case _:
                result = self._add_leaf_node_parallel(node)

        node_index = get_node_index(node)
        self.DP_table[node_index] = result # Assuming result is ready to be directly assigned
        return result

    def count_homomorphisms_parallel(self):
        # Dictionary to store all futures
        self.futures = {}
        for node in reversed(self.dir_labelled_TD.vertices()):
            # Delaying each node process and storing in futures
            self.futures[node] = self.process_node(node)

        print("Futures: ", self.futures)

        # Compute all results, respecting the inherent dependencies among them
        results = dask.compute(*self.futures.values())
        print("Results: ", [f.compute() for f in results])
        # Since the results are integrated into the DP_table in each process_node call,
        # you can simply access the final result:
        return self.DP_table[0][0]


    # def process_node(self, node):        
    #     # Ensure all child node computations are completed before processing this node
    #     # child_nodes = self.dir_labelled_TD.neighbors_out(node)
    #     # child_futures = [self.futures[child] for child in child_nodes if child in self.futures]

    #     # Wait for all child node computations to complete
    #     # if child_futures:
    #     #     done, _ = wait(child_futures, return_when='ALL_COMPLETED')

    #     node_type = self.dir_labelled_TD.get_vertex(node)
    #     match node_type:
    #         case 'intro':
    #             result = self._add_intro_node_parallel(node)
    #         case 'forget':
    #             result = self._add_forget_node_parallel(node)
    #         case 'join':
    #             result = self._add_join_node_parallel(node)
    #         case _:
    #             result = self._add_leaf_node_parallel(node)

    #     node_index = get_node_index(node)
    #     # print(f"Node {node_index} result: {result}")
    #     return node_index, result

    # def count_homomorphisms_parallel(self):
    #     # Create a dictionary of delayed computations
    #     self.futures = {}
    #     for node in reversed(self.dir_labelled_TD.vertices()):
    #         self.futures[node] = dask.delayed(self.process_node)(node)

    #     # print("Futures: ", self.futures)

    #     # Compute results as they are needed
    #     for node, future in self.futures.items():
    #         try:
    #             result = future.compute()
    #             node_index, result = result
    #             # print(f"In future: Node {node_index} result: {result}")
    #             self.DP_table[node_index] = result
    #         except Exception as e:
    #             print(f"Exception: {e}")

    #     return self.DP_table[0][0]


    ### Main adding functions

    @delayed
    def _add_leaf_node_parallel(self, node):
        r"""
        Add the leaf node to the DP table and update it accordingly.
        """
        node_index = get_node_index(node)
        return [1]

    @delayed
    def _add_intro_node_parallel(self, node):
        r"""
        Add the intro node to the DP table and update it accordingly.
        """
        # Basic setup
        node_index, node_vertices = node
        node_vtx_tuple = tuple(node_vertices)

        child_node_index, child_node_vtx = self.dir_labelled_TD.neighbors_out(node)[0]
        child_node_vtx_tuple = tuple(child_node_vtx)

        # If `colourful` is True, we can reduce the size of each DP table entry,
        # since we only need to consider colour partitions: Each vertex with some
        # colour in G should only map to its colour partition class in H.
        # if self.colourful:
        #     node_clr_counter = count_occurrences([self.graph_clr[i] for i in node_vtx_tuple])
        #     target_clr_counter = count_occurrences(self.target_clr)
        #     clr_intersection = list_intersection(node_clr_counter, self.target_clr) # relevant colours
        #     # print("Colours: ", node_clr_counter, target_clr_counter, clr_intersection)

        #     # Filter target vertices based on colour intersection and create subgraph
        #     target_vertices_to_keep = [v for v in self.target_graph.vertices() if self.target_clr[v] in clr_intersection]
        #     self.actual_target_graph = self.target_graph.subgraph(target_vertices_to_keep)
        #     # print("actual target graph: ", self.actual_target_graph.edges())

        #     self.actual_target_size = len(self.actual_target_graph)
        #     # print("actual target size: ", self.actual_target_size)

        #     mappings_length = prod(target_clr_counter[i] ** node_clr_counter[i] for i in clr_intersection)
        #     # mappings_length = len(self.target_graph) ** len(node_vtx_tuple)
        # else:
        mappings_length = self.actual_target_size ** len(node_vtx_tuple)
        # print("target size", self.actual_target_size)
        # print("mappings length: ", mappings_length)

        mappings_count = [0 for _ in range(mappings_length)]

        # Use the adjacency matrix when dense, otherwise use the graph itself
        target_density = self.actual_target_graph.density()
        target = self.actual_target_graph.adjacency_matrix() if target_density >= self.density_threshold else self.actual_target_graph

        # Intro node specifically
        intro_vertex = self.node_changes_dict[node_index]
        intro_vtx_index = node_vtx_tuple.index(intro_vertex) # Index of the intro vertex in the node/bag
        # print("intro vertex {} and its index {} in bag".format(intro_vertex, intro_vtx_index))

        if self.colourful:
            intro_vtx_clr = self.graph_clr[intro_vertex]
            # print("intro vtx clr", intro_vtx_clr)

        # Neighborhood of intro vertex in the bag
        intro_vtx_nbhs = [child_node_vtx_tuple.index(vtx) for vtx in child_node_vtx_tuple if self.graph.has_edge(intro_vertex, vtx)]
        # intro_vtx_nbhs = [self.graph.index(vtx) for vtx in child_node_vtx_tuple if self.graph.has_edge(intro_vertex, vtx)]
        # print("intro node nbhs in bag: ", intro_vtx_nbhs)

        child_DP_entry = self.DP_table[child_node_index]
        # print("INTRO child DP entry: ", child_DP_entry)
        # print("\n")

        for mapped in range(len(child_DP_entry)):
            # Neighborhood of the mapped vertices of intro vertex in the target graph
            mapped_intro_nbhs = [extract_bag_vertex(mapped, vtx, self.actual_target_size) for vtx in intro_vtx_nbhs]
            # print("mapped: ", mapped)
            # print("mapped nbhs in target: ", mapped_intro_nbhs)

            mapping = add_vertex_into_mapping(0, mapped, intro_vtx_index, self.actual_target_size)

            for target_vtx in self.actual_target_graph:
                # print("target vertex: ", target_vtx)

                # If the colours do not match, skip current iteration and
                # move on to the next vertex
                if self.colourful:
                    target_vtx_clr = self.target_clr[target_vtx]
                    # print("intro color: {}, target color: {}".format(intro_vtx_clr, target_vtx_clr))
                    if intro_vtx_clr != target_vtx_clr:
                        mapping += self.actual_target_size ** intro_vtx_index
                        continue

                # print("current mapping", mapping)
                if is_valid_mapping(target_vtx, mapped_intro_nbhs, target):
                    # print("VALID!")
                    mappings_count[mapping] = child_DP_entry[mapped]

                mapping += self.actual_target_size ** intro_vtx_index
                # print("TEMP entry: {}\n".format(mappings_count))

        return mappings_count
        # print("DP table: ", self.DP_table)

    @delayed
    def _add_forget_node_parallel(self, node):
        r"""
        Add the forget node to the DP table and update it accordingly.
        """
        # Basic setup
        node_index, node_vertices = node
        node_vtx_tuple = tuple(node_vertices)

        child_node_index, child_node_vtx = self.dir_labelled_TD.neighbors_out(node)[0]
        child_node_vtx_tuple = tuple(child_node_vtx)

        # target_graph_size = len(self.target_graph)
        mappings_length_range = range(self.actual_target_size ** len(node_vtx_tuple))
        mappings_count = [0 for _ in mappings_length_range]
        # print("FORGET DP table length: ", mappings_length_range)

        # Forget node specifically
        forgotten_vtx = self.node_changes_dict[node_index]
        forgotten_vtx_index = child_node_vtx_tuple.index(forgotten_vtx)

        child_DP_entry = self.DP_table[child_node_index]

        for mapping in mappings_length_range:
            sum = 0
            # extended_mapping = add_vertex_into_mapping(0, mapping, forgotten_vtx_index, target_graph_size)
            extended_mapping = add_vertex_into_mapping(0, mapping, forgotten_vtx_index, self.actual_target_size)

            for target_vtx in self.target_graph:
            # for target_vtx in self.actual_target_graph:
                # print("FORGET extended mapping: ", extended_mapping)
                sum += child_DP_entry[extended_mapping]
                extended_mapping += self.actual_target_size ** forgotten_vtx_index

            mappings_count[mapping] = sum

        # print("FORGET mappings count: ", mappings_count)
        return mappings_count

    @delayed
    def _add_join_node_parallel(self, node):
        r"""
        Add the join node to the DP table and update it accordingly.
        """
        node_index, node_vertices = node
        left_child, right_child  = [vtx for vtx in self.dir_labelled_TD.neighbors_out(node)
                                        if get_node_content(vtx) == node_vertices]
        left_child_index = get_node_index(left_child)
        right_child_index = get_node_index(right_child)

        mappings_count = [left_count * right_count for left_count, right_count
                            in zip(self.DP_table[left_child_index], self.DP_table[right_child_index])]

        # self.DP_table[node_index] = mappings_count
        return mappings_count
