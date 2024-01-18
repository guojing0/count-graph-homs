#ifndef HOM_COUNT_CORE_GRAPH_UTILS_H
#define HOM_COUNT_CORE_GRAPH_UTILS_H

#include <boost/graph/adjacency_list.hpp>
#include <vector>

typedef boost::adjacency_list<boost::vecS, boost::vecS, boost::undirectedS> Graph;
typedef std::pair<int, std::vector<int>> Node;

inline int get_node_index(const Node& node);
inline const std::vector<int> &get_node_content(const Node& node);

int extract_bag_vertex(int mapping, int index, int graph_size);
int add_vertex_into_mapping(int new_vertex, int mapping, int index, int graph_size);
int remove_vertex_from_mapping(int mapping, int index, int graph_size);

bool is_valid_mapping(int mapped_intro_vtx, const std::vector<int>& mapped_nbhrs, const Graph& target_graph);

#endif
