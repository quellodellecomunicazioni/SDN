import networkx as nx
import matplotlib.pyplot as plt

raw_nodes = [1, 2, 3, 4, 5]
raw_edges = [(1,2), (1,3), (1,4), (3,5), (4,5)]

rules = {}

def progressive_graph(nodes, links):
    '''
    progressive_graph disegna il grafo della rete in maniera progressiva, aggiungendo di volta in volta i nodi e i collegamenti trovati
    '''
    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(links)
    nx.draw(G)
    plt.show()

def check_links(root):
    '''
    check_links restituisce una lista contenente tutti i collegamenti uscenti/entranti da root
    '''
    marius = []
    for i in range(0,len(raw_edges)):
        if raw_edges[i][0] == root or raw_edges[i][1] == root:
            marius.append(raw_edges[i])
    return marius

def nodi_collegati(node):
    '''
    nodi_collegati mi restituisce una lista di nodi collegati al nodo in ingresso
    '''
    neighbors = []
    for i in range(0, len(edges)):
        if edges[i][0] == node:
            neighbors.append(edges[i][1])
        elif edges[i][1] == node:
            neighbors.append(edges[i][0])
    return neighbors

def shortest_path(path):
    '''
    calcola il percorso più breve tra src e dst
    '''
    src = path[0]
    dst = path[1]
    if path in edges:           # vuol dire che esiste il collegamento diretto
        next_hop = dst
        return next_hop
    else:                       # vuol dire che ho un collegamento indiretto
        #jumps = 0
        # guardo tutti i links con dst
        for i in range(0,len(edges)):
            if edges[i][1] == dst:
                if edges[i][0] in nodi_collegati(src):
                    next_hop = edges[i][0]
                    return next_hop

def add_rule(path):
    '''
    add_rule aggiunge le regola che soddisfa il percorso (src, dst)
    '''
    if path not in rules:
        next_hop = shortest_path(path)
        rules[path] = next_hop
    return

def clearList(dirty):
    '''
    clearList elimina gli elementi ripetuti
    '''
    clear = list(set(dirty))
    return clear

G = nx.Graph()
edges = []
nodes = []
for root in raw_nodes:
    edges = edges + check_links(root)
    edges = clearList(edges)
    nodes.append(root)
    for j in range(0, len(edges)):      # aggiunge solo le regole progressive
        if edges[j] not in rules:
            add_rule(edges[j])
    #progressive_graph(nodes, edges)
print(rules)
