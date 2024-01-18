#include <boost/graph/adjacency_list.hpp>
#include <vector>
#include <iostream>

typedef boost::adjacency_list<boost::vecS, boost::vecS, boost::undirectedS> Graph;
typedef boost::adjacency_list<boost::vecS, boost::vecS, boost::directedS> TreeDecompDigraph;
typedef std::pair<int, std::vector<int>> Node;
typedef std::vector<std::vector<unsigned int>> Table;


// Helper functions


/*
 * Get the index of `node`
 */
inline int get_node_index(const Node& node) {
    return node.first;
}

/*
 * Get the content/vertices of `node`
 */
inline const std::vector<int>& get_node_content(const Node& node) {
    return node.second;
}


// Core functions


/*
 * Add the leaf node to the DP table and update it accordingly.
 */
void add_leaf_node(Table& DP_table, const Node& node) {
    DP_table[get_node_index(node)] = {1};
}

/*
 *
 */
void add_join_node(Table& DP_table, const Node& node, const TreeDecompDigraph& graph_TD) {
    int node_index = node.first;
    auto edges = boost::out_edges(node_index, graph_TD);

    // We assume that a join node only has two out-edges and they have same content
    int left_child_index = target(*edges.first, graph_TD);
    int right_child_index = target(*(++edges.first), graph_TD);

    // Compute mappings_count
    std::vector<unsigned int> mappings_count;
    mappings_count.reserve(DP_table[left_child_index].size());
    for (size_t i = 0; i < DP_table[left_child_index].size(); ++i) {
        mappings_count.push_back(DP_table[left_child_index][i] * DP_table[right_child_index][i]);
    }

    DP_table[node_index] = mappings_count;
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

int main() {
    // Define the graph type
    Graph g = five_clique();

    // Iterate over the vertices and print them
    for (auto vp = vertices(g); vp.first != vp.second; ++vp.first) {
        std::cout << *vp.first << std::endl;
    }

    return 0;
}
