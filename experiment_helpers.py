import matplotlib.pyplot as plt

from local_tree_decomp import *

# def speed_test(graph, target_graph, naive=True):
#     basic_result = count_homomorphisms(graph, target_graph)
#     int_rep_result = count_homomorphisms_int(graph, target_graph)
#     better_int_rep_result = count_homomorphisms_int_pre(graph, target_graph)

#     results = [basic_result, int_rep_result, better_int_rep_result]

#     if naive:
#         brute_force_result = len(enumerate_homomorphisms(graph, target_graph))
#         results.append(brute_force_result)

#     if all(result == better_int_rep_result for result in results):
#         print(target_graph.order())
#         # print(better_int_rep_result)

#         if naive:
#             print('\nBrute force:')
#             %timeit len(enumerate_homomorphisms(graph, target_graph))
        
#         print('\nBasic:')
#         %timeit count_homomorphisms(graph, target_graph)
        
#         print('\nInt representation:')
#         %timeit count_homomorphisms_int(graph, target_graph)
    
#         print('\nBetter int representation:')
#         %timeit count_homomorphisms_int_pre(graph, target_graph)

def return_nice_TD(graph):
    tree_decomp = graph.treewidth(certificate=True)
    nice_tree_decomp = make_nice_tree_decomposition(graph, tree_decomp)
    root = sorted(nice_tree_decomp)[0]
    dir_labelled_TD = label_nice_tree_decomposition(nice_tree_decomp, root, directed=True)
    return dir_labelled_TD

def timeit_magic(N, graph):
    int_time_list = []
    int_dict_time_list = []

    for i in range(1, 21):
        density = 0.05 * i
        print('density = {}\n'.format(density))
    
        target_graph = graphs.RandomGNP(N, density, seed=42)
    
        int_time = %timeit -r 5 -o count_homomorphisms_int_pre(graph, target_graph)
        int_dict_time = %timeit -r 5 -o count_homomorphisms_int_dict(graph, target_graph)

        int_time_list.append(int_time.average)
        int_dict_time_list.append(int_dict_time.average)
    
    return int_time_list, int_dict_time_list

def plot_result(fst_time, snd_time, title, filename):
    densities = [
        0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 
        0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0
    ]
    
    plt.figure(figsize=(12, 6))
    plt.plot(densities, fst_time, label='Int version', marker='o')
    plt.plot(densities, snd_time, label='Int-dict version', marker='x')
    plt.title(title)
    plt.xlabel('Density')
    plt.ylabel('Time (second)')
    plt.legend()
    plt.grid(True)
    
    plt.savefig(filename, bbox_inches='tight')
    
    plt.show()

def run():
    graph = graphs.CompleteBipartiteGraph(2, 2)

    N = 50

    title = 'From 4-cycle to random graph of {} vertices\n'.format(N)

    print(title)

    int_time, int_dict_time = timeit_magic(N, graph)

    filename = 'C4-to-random.png'

    plot_result(int_time, int_dict_time, title, filename)
