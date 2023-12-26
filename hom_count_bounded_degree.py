
from itertools import chain

def count_homomorphisms_bounded_degree(graph, target_graph):
    graph_traversal = list(graph.breadth_first_search(sorted(graph)[0]))
    return count_homomorphisms_helper(graph, target_graph, graph_traversal)

def count_homomorphisms_helper(graph, target_graph, graph_traversal, target_traversal):
    # If `target_traversal` is empty
    if not target_traversal:
        choices = target_graph.vertices()
    else:
        # Get the closed neighborhood of `target_traversal` in `target_graph`
        choices = set(chain.from_iterable(target_graph.neighbor_iterator(vtx, closed=True) for vtx in target_traversal))

    hom_count = 0
    for choice in choices:
        new_target_traversal = target_traversal + [choice]

        # Bounding condition: if the current partial traversal cannot lead to a homomorphism, skip it
        # if not is_partial_traversal_valid(graph, target_graph, graph_traversal, new_target_traversal):
        #     continue

        if len(target_traversal) == graph.order() - 1:
            mapping = dict(zip(graph_traversal, new_target_traversal))

            if is_homomorphism(graph, target_graph, mapping):
                hom_count += 1
        else:
            hom_count += count_homomorphisms_helper(graph, target_graph, graph_traversal, new_target_traversal)

    return hom_count

def is_partial_traversal_valid(graph, target_graph, graph_traversal, target_traversal):
    induced_traversal = graph_traversal[:len(target_traversal)]
    induced_subgraph = graph.subgraph(induced_traversal)

    mapping = dict(zip(induced_traversal, target_traversal))

    return is_homomorphism(induced_subgraph, target_graph, mapping)

def is_homomorphism(G, H, mapping):
    for edge in G.edges(labels=False):
        if not H.has_edge(mapping[edge[0]], mapping[edge[1]]):
            return False
    return True
