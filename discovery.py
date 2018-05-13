import networkx as nx
import matplotlib.pyplot as plt

raw_nodes = [1, 2, 3, 4, 5]
raw_edges = [(1,2), (1,3), (1,4), (3,5), (4,5)]

rules = {}

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
    neighbors = clearList(neighbors)
    return neighbors

def shortest_path(path):
    '''
    calcola il percorso più breve tra src e dst
    esiste una regola da uno dei vicini alla dst? Se sì, scelgo quella con il peso minore
    '''
    src = path[0]
    dst = path[1]
    if len(nodi_collegati(src)) == 1:       # con un solo collegamento non ho opzioni
        next_hop = nodi_collegati(src)[0]
        return next_hop
    if path in edges:           # vuol dire che esiste il collegamento diretto
        next_hop = dst
        return next_hop
    else:                       # vuol dire che ho un collegamento indiretto
        n = []
        n = nodi_collegati(src)
        for i in range(0, len(n)):
            n_path = (n[i], dst)
            if n_path in rules:
                next_hop = n[i]
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
            t = edges[j][0]
            r = edges[j][1]
            mirror = (r,t)
            edges.append(mirror)
            add_rule(mirror)
    #progressive_graph(nodes, edges)
    G.add_nodes_from(nodes)
    G.add_edges_from(edges, weight=1)   # weight = 1 assegna un peso al link
    # assegno weight = 1 perché i link scoperti in maniera progressiva sono link diretti
    # per accedere all`attributo di un link del tipo (src,dst) devo fare G[src][dst]['weight']
    nx.draw(G)
    plt.show()
#print(rules)

indirect_links = []
for i in range(0,len(nodes)):
    for j in range(0,len(nodes)):
        if nodes[i] != nodes[j]:
            t = (nodes[i], nodes[j])
            indirect_links.append(t)
indirect_links = list(set(indirect_links) - set(edges))

for i in range(0, len(indirect_links)):
    add_rule(indirect_links[i])
print(rules)
