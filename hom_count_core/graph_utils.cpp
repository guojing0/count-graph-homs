#include "graph_utils.h"

#include <cmath>

/*
 * Extract the bag vertex of `index` from `mapping`
 */
int extract_bag_vertex(int mapping, int index, int graph_size) {
    return (mapping / static_cast<int>(std::pow(graph_size, index))) % graph_size;
}

/*
 * Insert `new_vertex` at `index` into `mapping`
 */
int add_vertex_into_mapping(int new_vertex, int mapping, int index, int graph_size) {
    int temp = static_cast<int>(std::pow(graph_size, index));
    int right_digits = mapping % temp;
    int left_digits = mapping - right_digits;

    return graph_size * left_digits + temp * new_vertex + right_digits;
}

/*
 * Return a new mapping from removing vertex of `index` from `mapping`
 */
int remove_vertex_from_mapping(int mapping, int index, int graph_size) {
    int left_digits = mapping - (mapping % static_cast<int>(std::pow(graph_size, index + 1)));
    int right_digits = mapping % static_cast<int>(std::pow(graph_size, index));

    return left_digits / graph_size + right_digits;
}