
from itertools import chain

def count_homomorphisms_bounded_degree(graph, target_graph):
    graph_traversal = list(graph.breadth_first_search(sorted(graph)[0]))
    return count_homomorphisms_helper(graph, target_graph, graph_traversal, [], {})

def count_homomorphisms_helper(graph, target_graph, graph_traversal, target_traversal, memo):
    traversal_tuple = tuple(target_traversal)
    if traversal_tuple in memo:
        return memo[traversal_tuple]

    if len(traversal_tuple) > 3:
        print(traversal_tuple)

    # If `target_traversal` is empty
    if not target_traversal:
        choices = target_graph.vertices()
    else:
        # Get the closed neighborhood of `target_traversal` in `target_graph`
        choices = set(chain.from_iterable(target_graph.neighbor_iterator(vtx, closed=True) for vtx in target_traversal))

    hom_count = 0
    for choice in choices:
        new_traversal = target_traversal + [choice]

        if len(target_traversal) == graph.order() - 1:
            if is_traversal_homomorphism(graph, target_graph, graph_traversal, new_traversal):
                hom_count += 1
        else:
            hom_count += count_homomorphisms_helper(graph, target_graph, graph_traversal, new_traversal, memo)

    memo[traversal_tuple] = hom_count
    return hom_count

def is_traversal_homomorphism(graph, target_graph, graph_traversal, target_traversal):
    mapping = dict(zip(graph_traversal, target_traversal))
    for vtx in graph:
        for vtx_nbhr in graph.neighbor_iterator(vtx):
            if not target_graph.has_edge(mapping[vtx], mapping[vtx_nbhr]):
                return False
    return True
