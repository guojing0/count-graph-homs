from sage.graphs.graph_decompositions.tree_decomposition import is_valid_tree_decomposition
from sage.sets.set import Set


def make_nice_tree_decomposition(graph, tree_decomp):
    r"""
    Return a *nice* tree decomposition (TD) of the TD ``tree_decomp``.

    See page 161 of [CFKLMPPS15]_ for a description of the nice tree decomposition.

    A *nice* TD `NT` is a rooted tree with four types of nodes:

    - *Leaf* nodes have no children and bag size 1;
    - *Introduce* nodes have one child: If `v \in NT` is an introduce node and
      `w \in NT` its child, then `Bag(v) = Bag(w) \cup \{ x \}`, where `x` is the
      introduced node;
    - *Forget* nodes have one child: If `v \in NT` is a forget node and
      `w \in NT` its child, then `Bag(v) = Bag(w) \setminus \{ x \}`, where `x` is the
      forgotten node;
    - *Join* nodes have two children, both identical to the parent.

    INPUT:

    - ``graph`` -- a Sage graph
    - ``tree_decomp`` -- a tree decomposition

    OUTPUT:

    A nice tree decomposition.

    .. WARNING::

        This method assumes that the vertices of the input tree `tree_decomp`
        are hashable and have attribute ``issuperset``, e.g., ``frozenset`` or
        :class:`~sage.sets.set.Set_object_enumerated_with_category`.

    EXAMPLES::

        sage: from sage.graphs.graph_decompositions.tree_decomposition import make_nice_tree_decomposition
        sage: petersen = graphs.PetersenGraph()
        sage: petersen_TD = petersen.treewidth(certificate=True)
        sage: make_nice_tree_decomposition(petersen, petersen_TD)
        Nice tree decomposition of Tree decomposition: Graph on 28 vertices

    ::

        sage: from sage.graphs.graph_decompositions.tree_decomposition import make_nice_tree_decomposition
        sage: cherry = graphs.CompleteBipartiteGraph(1, 2)
        sage: cherry_TD = cherry.treewidth(certificate=True)
        sage: make_nice_tree_decomposition(cherry, cherry_TD)
        Nice tree decomposition of Tree decomposition: Graph on 7 vertices

    ::

        sage: from sage.graphs.graph_decompositions.tree_decomposition import make_nice_tree_decomposition
        sage: bip_one_four = graphs.CompleteBipartiteGraph(1, 4)
        sage: bip_one_four_TD = bip_one_four.treewidth(certificate=True)
        sage: make_nice_tree_decomposition(bip_one_four, bip_one_four_TD)
        Nice tree decomposition of Tree decomposition: Graph on 15 vertices

    ::

        sage: from sage.graphs.graph_decompositions.tree_decomposition import make_nice_tree_decomposition
        sage: triangle = graphs.CompleteGraph(3)
        sage: triangle_TD = triangle.treewidth(certificate=True)
        sage: make_nice_tree_decomposition(triangle, triangle_TD)
        Nice tree decomposition of Tree decomposition: Graph on 7 vertices
    """
    if not is_valid_tree_decomposition(graph, tree_decomp):
        raise ValueError("input must be a valid tree decomposition for this graph")

    name = f"Nice tree decomposition of {tree_decomp.name()}"
    from sage.graphs.graph import Graph
    if not tree_decomp:
        return Graph(name=name)

    # Step 1: Ensure the tree is directed and has a root
    # Choose a root and orient the edges from root-to-leaves direction
    #
    # Testing <= 1 for the special case when one bag containing all vertices
    leaves = [u for u in tree_decomp if tree_decomp.degree(u) <= 1]

    from sage.graphs.digraph import DiGraph
    if len(leaves) == 1:
        root = leaves[0]
        directed_tree = DiGraph(tree_decomp)
    else:
        root = leaves.pop()

        directed_tree = DiGraph(tree_decomp.breadth_first_search(start=root, edges=True),
                                format='list_of_edges')

    # Relabel the graph in range (0, |tree_decomp| - 1)
    bags_to_int = directed_tree.relabel(inplace=True, return_map=True)
    # Get the new name of the root node
    root = bags_to_int[root]
    # Force bags to be of type Set to simplify code
    bag = {ui: Set(u) for u, ui in bags_to_int.items()}

    # Step 2: Add the root node and the leaf nodes, with empty bags
    # To each leaf node of `directed_tree`, we add a child with empty bag.
    # We also add a new root with empty bag.
    root, old_root = directed_tree.add_vertex(), root
    directed_tree.add_edge(root, old_root)
    bag[root] = Set()
    for vi, u in enumerate(leaves, start=root + 1):
        directed_tree.add_edge(bags_to_int[u], vi)
        bag[vi] = Set()

    # Step 3: Ensure that each node of directed_tree has at most 2 children.
    # If a node has more than 2 children, introduce new nodes to
    # make sure each node has at most 2 children:
    #
    # If v has k > 2 children (w_1, w_2, ..., w_k), we disconnect (w_1, ..., w_{k-1})
    # from v, and introduce k - 2 new nodes (u_1, u_2, ..., u_{k-2}).
    # We then let w_i be the children of u_i for 1 <= i <= k - 2.
    # We also let w_{k-1} be the second child of u_{k-2}, and
    # u_i the second child of u_{i-1}.
    # Finally, we let u_1 the second child of u.
    # Each node u_i has the same bag as u.

    # We need to call list(...) since we modify directed_tree
    for ui in list(directed_tree):
        if directed_tree.out_degree(ui) > 2:
            children = directed_tree.neighbors_out(ui)
            children.pop() # one vertex remains a child of ui

            directed_tree.delete_edges((ui, vi) for vi in children)

            new_nodes = [directed_tree.add_vertex() for _ in range(len(children) - 1)]

            directed_tree.add_edge(ui, new_nodes[0])
            directed_tree.add_path(new_nodes)
            directed_tree.add_edges(zip(new_nodes, children))
            directed_tree.add_edge(new_nodes[-1], children[-1])

            bag.update((vi, bag[ui]) for vi in new_nodes)

    # Step 4: If current vertex v has two children w1 and w2,
    # then bag[v] == bag[w1] == bag[w2]
    for current_node in list(directed_tree):
        if directed_tree.out_degree(current_node) < 2:
            continue
        for neighbor in directed_tree.neighbor_out_iterator(current_node):
            if bag[current_node] != bag[neighbor]:
                directed_tree.delete_edge(current_node, neighbor)
                new_node = directed_tree.add_vertex()
                directed_tree.add_path([current_node, new_node, neighbor])
                bag[new_node] = bag[current_node]

    # Step 5: If the node v has only one child, then it is either an introduce
    # node or a forget node.
    def add_path_of_intro_nodes(u, v):
        """
        Replace the arc (u, v) by a path of introduce nodes.
        """
        if len(bag[u]) + 1 == len(bag[v]):
            return

        diff = list(bag[v] - bag[u])
        diff.pop()

        last_node = u
        for w in diff:
            new_node = directed_tree.add_vertex()
            bag[new_node] = bag[last_node].union(Set((w,)))
            directed_tree.add_edge(last_node, new_node)
            last_node = new_node

        directed_tree.add_edge(last_node, v)
        directed_tree.delete_edge(u, v)

    def add_path_of_forget_nodes(u, v):
        """
        Replace the arc (u, v) by a path of forget nodes.
        """
        if len(bag[v]) + 1 == len(bag[u]):
            return

        diff = list(bag[u] - bag[v])
        diff.pop()

        last_node = u
        for w in diff:
            new_node = directed_tree.add_vertex()
            bag[new_node] = bag[last_node] - {w}
            directed_tree.add_edge(last_node, new_node)
            last_node = new_node

        directed_tree.add_edge(last_node, v)
        directed_tree.delete_edge(u, v)

    for ui in list(directed_tree):
        if directed_tree.out_degree(ui) != 1:
            continue

        vi = next(directed_tree.neighbor_out_iterator(ui))
        bag_ui, bag_vi = bag[ui], bag[vi]

        # Merge the nodes if the two bags are the same
        if bag_ui == bag_vi:
            if directed_tree.in_degree(ui) == 1:
                parent = next(directed_tree.neighbor_in_iterator(ui))
                directed_tree.add_edge(parent, vi)
            else:
                root = vi
            directed_tree.delete_vertex(ui)

        # Add paths of intro / forget nodes accordingly

        elif bag_ui.issubset(bag_vi):
            add_path_of_intro_nodes(ui, vi)

        elif bag_vi.issubset(bag_ui):
            add_path_of_forget_nodes(ui, vi)

        # Handle the case when the two nodes are not related in any way above
        else:
            wi = directed_tree.add_vertex()
            bag[wi] = bag[ui] & bag[vi]
            directed_tree.add_path([ui, wi, vi])
            directed_tree.delete_edge(ui, vi)
            add_path_of_forget_nodes(ui, wi)
            add_path_of_intro_nodes(wi, vi)

    # Return the nice tree decomposition after the processing
    nice_tree_decomp = Graph(directed_tree, name=name)

    bfs_ordering = nice_tree_decomp.breadth_first_search(start=root)
    relabeling = {u: (i, bag[u]) for i, u in enumerate(bfs_ordering)}
    nice_tree_decomp.relabel(inplace=True, perm=relabeling)

    return nice_tree_decomp

def label_nice_tree_decomposition(nice_TD, root, directed=False):
    r"""
    Return a nice tree decomposition with nodes labelled accordingly.

    INPUT:

    - ``nice_TD`` -- a nice tree decomposition

    - ``root`` -- the root of the nice tree decomposition

    - ``directed`` -- boolean (default: ``False``); whether to return the directed graph

    OUTPUT:

    A nice tree decomposition with nodes labelled.

    EXAMPLES::

        sage: from sage.graphs.graph_decompositions.tree_decomposition import make_nice_tree_decomposition, label_nice_tree_decomposition
        sage: bip_one_four = graphs.CompleteBipartiteGraph(1, 4)
        sage: bip_one_four_TD = bip_one_four.treewidth(certificate=True)
        sage: nice_TD = make_nice_tree_decomposition(bip_one_four, bip_one_four_TD)
        sage: root = sorted(nice_TD.vertices())[0]
        sage: label_TD = label_nice_tree_decomposition(nice_TD, root)
        sage: for node in sorted(label_TD):
        ....:     print(node, label_TD.get_vertex(node))
        (0, {}) forget
        (1, {0}) forget
        (2, {0, 1}) intro
        (3, {0}) forget
        (4, {0, 4}) join
        (5, {0, 4}) intro
        (6, {0, 4}) intro
        (7, {0}) forget
        (8, {0}) forget
        (9, {0, 3}) intro
        (10, {0, 2}) intro
        (11, {3}) intro
        (12, {2}) intro
        (13, {}) leaf
        (14, {}) leaf
    """
    from sage.graphs.digraph import DiGraph
    from sage.graphs.graph import Graph

    directed_TD = DiGraph(nice_TD.breadth_first_search(start=root, edges=True),
                          format='list_of_edges')

    # The loop starts from the root node
    # We assume the tree decomposition is valid and nice,
    # hence saving time on checking.
    for node in directed_TD:
        in_deg = directed_TD.in_degree(node)
        out_deg = directed_TD.out_degree(node)

        if out_deg == 2:
            directed_TD.set_vertex(node, 'join')
        elif out_deg == 1:
            current_bag = node[1]
            child_bag = directed_TD.neighbors_out(node)[0][1]

            if len(current_bag) == len(child_bag) + 1:
                directed_TD.set_vertex(node, 'intro')
            else:
                directed_TD.set_vertex(node, 'forget')
        else:
            directed_TD.set_vertex(node, 'leaf')

    if directed:
        return directed_TD
    return Graph(directed_TD, name=nice_TD.name())
