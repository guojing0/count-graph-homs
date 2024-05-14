from numba import jit
import numpy as np

@jit(nopython=True, parallel=True)
def process_intro_node(child_result, intro_vtx_nbhs, target_graph_size, actual_target_graph, colourful, graph_clr, target_clr):
    mappings_count = np.zeros(len(child_result), dtype=np.int32)
    for mapped in range(len(child_result)):
        mapped_intro_nbhs = [extract_bag_vertex(mapped, vtx, target_graph_size) for vtx in intro_vtx_nbhs]
        mapping = 0
        for target_vtx in actual_target_graph:
            if colourful:
                if graph_clr[intro_vertex] != target_clr[target_vtx]:
                    mapping += target_graph_size ** intro_vtx_index
                    continue
            if is_valid_mapping(target_vtx, mapped_intro_nbhs, actual_target_graph):
                mappings_count[mapping] = child_result[mapped]
            mapping += target_graph_size ** intro_vtx_index
    return mappings_count

@jit(nopython=True, parallel=True)
def process_forget_node(child_result, node_vtx_tuple, actual_target_size, forgotten_vtx_index):
    mappings_length = actual_target_size ** len(node_vtx_tuple)
    mappings_count = np.zeros(mappings_length, dtype=np.int32)
    for mapping in range(mappings_length):
        sum_results = 0
        extended_mapping = mapping
        for _ in range(actual_target_size):
            sum_results += child_result[extended_mapping]
            extended_mapping += actual_target_size ** forgotten_vtx_index
        mappings_count[mapping] = sum_results
    return mappings_count
