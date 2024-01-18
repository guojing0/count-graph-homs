#include <iostream>

#include "graph_utils.h"

typedef boost::adjacency_list<boost::vecS, boost::vecS, boost::directedS> TreeDecompDigraph;
typedef std::vector<std::vector<unsigned int>> Table;

/*
 * Add the leaf node to the DP table and update it accordingly.
 */
void add_leaf_node(Table &DP_table, const Node &node) {
    DP_table[get_node_index(node)] = {1};
}

/*
 *
 */
void add_intro_node(Table &DP_table, const Node &node,
                    const TreeDecompDigraph &graph_TD, const Graph &graph, const Graph &target_graph,
                    const std::unordered_map<int, int> &node_changes_dict) {
    // Basic setup
    int node_index = node.first;
    const std::vector<int> &node_vertices = node.second;

    auto neighbors_out = boost::out_edges(node_index, graph_TD);
    int child_node_index = boost::target(*neighbors_out.first, graph_TD);
    // Assuming child_node_vtx is defined based on graph_TD structure

    int target_graph_size = boost::num_vertices(target_graph);
    int mappings_length = std::pow(target_graph_size, node_vertices.size());
    std::vector<int> mappings_count(mappings_length, 0);

    // Intro node specifically
    int intro_vertex = node_changes_dict.at(node_index);
    auto it = std::find(node_vertices.begin(), node_vertices.end(), intro_vertex);
    int intro_vtx_index = std::distance(node_vertices.begin(), it);

    // Neighborhood of the intro vertex in the graph
    std::vector<int> node_nbhs_in_bag;
    for (int vtx: child_node_vtx) {
        if (boost::edge(intro_vertex, vtx, graph).second) {
            auto it_child = std::find(child_node_vtx.begin(), child_node_vtx.end(), vtx);
            node_nbhs_in_bag.push_back(std::distance(child_node_vtx.begin(), it_child));
        }
    }

    const std::vector<int> &child_DP_entry = DP_table[child_node_index];

    for (int mapped = 0; mapped < child_DP_entry.size(); ++mapped) {
        std::vector<int> mapped_nbhs_in_target;
        for (int nbh: node_nbhs_in_bag) {
            mapped_nbhs_in_target.push_back(extract_bag_vertex(mapped, nbh, target_graph_size));
        }

        int mapping = add_vertex_into_mapping(0, mapped, intro_vtx_index, target_graph_size);

        for (auto target_vtx: boost::make_iterator_range(vertices(target_graph))) {
            if (is_valid_mapping(target_vtx, mapped_nbhs_in_target, target_graph)) {
                mappings_count[mapping] = child_DP_entry[mapped];
            }

            mapping += static_cast<int>(std::pow(target_graph_size, intro_vtx_index));
        }
    }

    DP_table[node_index] = mappings_count;
}

/*
 *
 */
void add_join_node(Table &DP_table, const Node &node, const TreeDecompDigraph &graph_TD) {
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
