from local_tree_decomp import *

def return_nice_TD(graph):
    tree_decomp = graph.treewidth(certificate=True)
    nice_tree_decomp = make_nice_tree_decomposition(graph, tree_decomp)
    root = sorted(nice_tree_decomp)[0]
    dir_labelled_TD = label_nice_tree_decomposition(nice_tree_decomp, root, directed=True)
    return dir_labelled_TD
