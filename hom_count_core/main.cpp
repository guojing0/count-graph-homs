#include <iostream>

#include "graph_utils.h"

typedef boost::adjacency_list<boost::vecS, boost::vecS, boost::directedS> TreeDecompDigraph;
typedef std::vector<unsigned int> TableEntry;
typedef std::vector<TableEntry> Table;

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
    int node_index = get_node_index(node);
    const std::vector<int>& node_vertices = get_node_content(node);

    auto neighbors_out = boost::out_edges(node_index, graph_TD);
    int child_node_index = static_cast<int>(boost::target(*neighbors_out.first, graph_TD));
    const std::vector<int>& child_node_vtx = node_vertices; // TODO change

    int target_graph_size = static_cast<int>(boost::num_vertices(target_graph));
    int mappings_length = static_cast<int>(std::pow(target_graph_size, node_vertices.size()));
    TableEntry mappings_count(mappings_length, 0);

    // Intro node specifically
    int intro_vertex = node_changes_dict.at(node_index);
    auto iter = std::find(node_vertices.begin(), node_vertices.end(), intro_vertex);
    int intro_vtx_index = static_cast<int>(std::distance(node_vertices.begin(), iter));

    // Neighborhood of the intro vertex in the graph
    std::vector<int> node_nbhs_in_bag;
    for (int vtx : child_node_vtx) {
        if (boost::edge(intro_vertex, vtx, graph).second) {
            auto iter_child = std::find(child_node_vtx.begin(), child_node_vtx.end(), vtx);
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
                     const std::unordered_map<int, int>& node_changes_dict) {
    // Basic setup
    int node_index = get_node_index(node);
    const std::vector<int>& node_vertices = get_node_content(node);

    auto neighbors_out = boost::out_edges(node_index, graph_TD);
    int child_node_index = boost::target(*neighbors_out.first, graph_TD);
    const std::vector<int>& child_node_vtx = node_vertices; // TODO change

    int target_graph_size = static_cast<int>(boost::num_vertices(target_graph));
    int mappings_length = static_cast<int>(std::pow(target_graph_size, node_vertices.size()));
    TableEntry mappings_count(mappings_length, 0);

    // Forget node specifically
    int forgotten_vtx = node_changes_dict.at(node_index);
    auto iter = std::find(node_vertices.begin(), node_vertices.end(), forgotten_vtx);
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
void add_join_node(Table &DP_table, const Node &node, const TreeDecompDigraph &graph_TD) {
    int node_index = node.first;
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

unsigned int count_homomorphisms() {
    return 0;
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
