def make_triangle():
    return graphs.CompleteGraph(3)

def make_cycle(n):
    return graphs.CycleGraph(n)

def make_cherry():
    return graphs.CompleteBipartiteGraph(1, 2)

def make_claw():
    return graphs.CompleteBipartiteGraph(1, 3)

def make_clique(n):
    return graphs.CompleteGraph(n)

def make_random(n, p):
    return graphs.RandomGNP(n, p)

def make_petersen():
    return graphs.PetersenGraph()
