#include <iostream>

#include "graph_utils.h"

/*
 * Define a `Node` in a tree decomposition:
 *
 * index - index of the node in the tree decomposition graph
 * content - the content in the bag of this node
 * type - each node can have four types:
 *
 * 0 - Leaf node (usually not labelled)
 * 1 - Introduce node
 * 2 - Forget node
 * 3 - Join node
 */
struct Node {
    int index, type;
    std::set<int> content;

    // Constructor to initialize fields
    Node() : index(0), type(0) {}

    // Constructor with parameters
    Node(int idx, int tp, const std::set<int>& cnt)
            : index(idx), type(tp), content(cnt) {}
};

typedef boost::adjacency_list<boost::vecS, boost::vecS, boost::directedS, Node> TreeDecompDigraph;
typedef std::vector<unsigned long> TableEntry;
typedef std::vector<TableEntry> Table;
typedef std::unordered_map<int, int> NodeChanges;

typedef boost::graph_traits<Graph>::vertex_descriptor Vertex;

struct bfs_visitor : public boost::default_bfs_visitor {
    std::vector<Vertex> vertices;
};

/*
 * Core functions for adding entries to the DP table
 */

/*
 * Add the leaf node to the DP table and update it accordingly.
 */
void add_leaf_node(Table &DP_table, const Node &node) {
    DP_table[node.index] = {1};
}

/*
 *
 */
void add_intro_node(Table &DP_table, const Node &node,
                    const TreeDecompDigraph &graph_TD, const Graph &graph, const Graph &target_graph,
                    const NodeChanges& node_changes_dict) {
    // Basic setup
    int node_index = node.index;
    const std::set<int>& node_vertices = node.content;

    auto neighbors_out = boost::out_edges(node_index, graph_TD);
    int child_node_index = static_cast<int>(boost::target(*neighbors_out.first, graph_TD));
    const std::set<int>& child_node_vtx = node_vertices; // TODO change

    int target_graph_size = static_cast<int>(boost::num_vertices(target_graph));
    int mappings_length = static_cast<int>(std::pow(target_graph_size, node_vertices.size()));
    TableEntry mappings_count(mappings_length, 0);

    // Intro node specifically
    int intro_vertex = node_changes_dict.at(node_index);
    auto iter = node_vertices.find(intro_vertex);
    int intro_vtx_index = static_cast<int>(std::distance(node_vertices.begin(), iter));

    // Neighborhood of the intro vertex in the graph
    std::vector<int> node_nbhs_in_bag;
    for (int vtx : child_node_vtx) {
        if (boost::edge(intro_vertex, vtx, graph).second) {
            auto iter_child = child_node_vtx.find(vtx);
            node_nbhs_in_bag.push_back(static_cast<int>(std::distance(child_node_vtx.begin(), iter_child)));
        }
    }

    const TableEntry& child_DP_entry = DP_table[child_node_index];

    for (int mapped = 0; mapped < child_DP_entry.size(); ++mapped) {
        std::vector<int> mapped_nbhs_in_target(node_nbhs_in_bag.size(), 0);
        for (int nbh: node_nbhs_in_bag) {
            mapped_nbhs_in_target.push_back(extract_bag_vertex(mapped, nbh, target_graph_size));
        }

        int mapping = add_vertex_into_mapping(0, mapped, intro_vtx_index, target_graph_size);

        for (auto target_vtx : boost::make_iterator_range(vertices(target_graph))) {
            if (is_valid_mapping(target_vtx, mapped_nbhs_in_target, target_graph)) {
                mappings_count[mapping] = child_DP_entry[mapped];
            }

            mapping += static_cast<int>(std::pow(target_graph_size, intro_vtx_index));
        }
    }

    DP_table[node_index] = std::move(mappings_count);
}

/*
 *
 */
void add_forget_node(Table& DP_table, const Node& node,
                     const TreeDecompDigraph& graph_TD, const Graph& graph, const Graph& target_graph,
                     const NodeChanges& node_changes_dict) {
    // Basic setup
    int node_index = node.index;
    const std::set<int>& node_vertices = node.content;

    auto neighbors_out = boost::out_edges(node_index, graph_TD);
    int child_node_index = boost::target(*neighbors_out.first, graph_TD);
    const std::set<int>& child_node_vtx = node_vertices; // TODO change

    int target_graph_size = static_cast<int>(boost::num_vertices(target_graph));
    int mappings_length = static_cast<int>(std::pow(target_graph_size, node_vertices.size()));
    TableEntry mappings_count(mappings_length, 0);

    // Forget node specifically
    int forgotten_vtx = node_changes_dict.at(node_index);
    auto iter = node_vertices.find(forgotten_vtx);
    int forgotten_vtx_index = static_cast<int>(std::distance(node_vertices.begin(), iter));

    const TableEntry& child_DP_entry = DP_table[child_node_index];

    for (int mapping = 0; mapping < mappings_length; ++mapping) {
        unsigned int sum = 0;
        int extended_mapping = add_vertex_into_mapping(0, mapping, forgotten_vtx_index, target_graph_size);

        for (auto target_vtx : boost::make_iterator_range(vertices(target_graph))) {
            sum += child_DP_entry[extended_mapping];
            extended_mapping += static_cast<int>(std::pow(target_graph_size, forgotten_vtx_index));
        }

        mappings_count[mapping] = sum;
    }

    DP_table[node_index] = std::move(mappings_count);
}

/*
 *
 */
void add_join_node(Table &DP_table, const Node& node, const TreeDecompDigraph& graph_TD) {
    int node_index = node.index;
    auto edges = boost::out_edges(node_index, graph_TD);

    // We assume that a join node only has two out-edges and they have same content
    int left_child_index = target(*edges.first, graph_TD);
    int right_child_index = target(*(++edges.first), graph_TD);

    // Compute mappings_count
    int DP_table_entry_size = DP_table[left_child_index].size();
    TableEntry mappings_count(DP_table_entry_size, 0);
    for (size_t i = 0; i < DP_table_entry_size; ++i) {
        mappings_count.push_back(DP_table[left_child_index][i] * DP_table[right_child_index][i]);
    }

    DP_table[node_index] = std::move(mappings_count);
}

unsigned long count_homomorphisms(const TreeDecompDigraph& dir_labelled_TD,
                                  const Graph& graph, const Graph& target_graph,
                                  const NodeChanges& node_changes_dict) {
    Table DP_table(boost::num_vertices(dir_labelled_TD));
    bfs_visitor visitor;

    Vertex start_vertex = *vertices(dir_labelled_TD).first;
    boost::breadth_first_search(dir_labelled_TD, start_vertex, boost::visitor(visitor));

    for (auto vi = visitor.vertices.rbegin(); vi != visitor.vertices.rend(); ++vi) {
        auto node = dir_labelled_TD[*vi];
        int node_type = node.type;

        switch (node_type) {
            case 1:
                add_intro_node(DP_table, node, dir_labelled_TD, graph, target_graph, node_changes_dict);
                break;
            case 2:
                add_forget_node(DP_table, node, dir_labelled_TD, graph, target_graph, node_changes_dict);
                break;
            case 3:
                add_join_node(DP_table, node, dir_labelled_TD);
                break;
            default:
                add_leaf_node(DP_table, node);
        }
    }

    return DP_table[0][0];
}

// Some helper functions for testing and debugging

Graph four_cycle() {
    Graph g(4);

    boost::add_edge(0, 1, g);
    boost::add_edge(1, 2, g);
    boost::add_edge(2, 3, g);
    boost::add_edge(3, 0, g);

    return g;
}

Graph five_clique() {
    Graph g(5);

    for (int i = 0; i < 4; ++i) {
        for (int j = i + 1; j < 5; ++j) {
            boost::add_edge(i, j, g);
        }
    }

    return g;
}

TreeDecompDigraph four_cycle_nice_tree_decomp() {
    TreeDecompDigraph graph;
    std::vector<TreeDecompDigraph::vertex_descriptor> vertices(9);

    std::set<int> nodeContents[] = {
            {},
            {0},
            {0, 1},
            {0, 1, 3},
            {1, 3},
            {1, 2, 3},
            {2, 3},
            {3},
            {}
    };

    for (int i = 0; i < 9; ++i) {
        Node node;
        node.index = i;
        node.content = nodeContents[i];

        vertices[i] = add_vertex(node, graph);
    }

    add_edge(vertices[0], vertices[1], graph);
    add_edge(vertices[1], vertices[2], graph);
    add_edge(vertices[2], vertices[3], graph);
    add_edge(vertices[3], vertices[4], graph);
    add_edge(vertices[4], vertices[5], graph);
    add_edge(vertices[5], vertices[6], graph);
    add_edge(vertices[6], vertices[7], graph);
    add_edge(vertices[7], vertices[8], graph);

    return graph;
}

NodeChanges four_cycle_node_changes() {
    NodeChanges map = {
            {0, 0},
            {1, 1},
            {2, 3},
            {3, 0},
            {4, 2},
            {5, 1},
            {6, 2},
            {7, 3}
    };

    return map;
}

int main() {
//    TreeDecompDigraph graph = four_cycle_nice_tree_decomp();
//    TreeDecompDigraph::vertex_iterator vi, vend;
//    for (boost::tie(vi, vend) = vertices(graph); vi != vend; ++vi) {
//        Node& n = graph[*vi];
//        std::cout << "Node " << n.index << ": {";
//        for (int c : n.content) std::cout << c << " ";
//        std::cout << "}" << std::endl;
//    }

//    TreeDecompDigraph C4_nice_tree_decomp = four_cycle_nice_tree_decomp();
//    Graph C4 = four_cycle();
//    Graph K5 = five_clique();
//    NodeChanges map = four_cycle_node_changes();
//    unsigned long count = count_homomorphisms(C4_nice_tree_decomp, C4, K5, map);

    int n = 1;

    std::cout << n << std::endl;

    return 0;
}
