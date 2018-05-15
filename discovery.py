import networkx as nx
import matplotlib.pyplot as plt

raw_nodes = [1, 2, 3, 4, 5, 6]
raw_edges = [(1,2), (2,3), (3,4), (4,5), (5,6), (6,2)]

rules = {}
# rules è il dizionario che tiene traccia delle regole, gli elementi sono del tipo
# RULES = {(SRC,DST): [NEXT_HOP, WEIGHT_OF_THE_LINK]}

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
    neighbors = list(set(neighbors))
    return neighbors

def shortest_path(path):
    '''
    calcola il percorso più breve tra src e dst
    esiste una regola da uno dei vicini alla dst?
    --> sì, scelgo quella con il peso minore
    --> no, ho una soluzione standard (il primo nodo collegato)
    '''
    src = path[0]
    dst = path[1]
    if path in edges:           # vuol dire che esiste il collegamento diretto
        next_hop = dst
        peso = 1
        return next_hop, peso
    else:                       # vuol dire che ho un collegamento indiretto
        next_hop = nodi_collegati(src)[0]
        # se per caso non esiste ancora una regola da un vicino alla dst, soluzione standard
        n = nodi_collegati(src)
        peso = 100
        # il peso iniziale è settato ad un valore esageratamente grande così da rendere sempre vero il primo ciclo
        for i in range(0, len(n)):
            n_path = (n[i], dst)
            if n_path in rules:
                next_hop_provv = n[i]
                peso_provv = 1 + rules[(n[i], dst)][1]
                if peso_provv < peso:   # prendo il peso più piccolo
                    next_hop = next_hop_provv
                    peso = peso_provv
        return next_hop, peso

def aggiungi_nodi_collegati(nodo):
    ciao = nodi_collegati(nodo)
    for u in range(0, len(ciao)):
        if ciao[u] not in nodes:
            nodes.append(ciao[u])
    return

def add_rule(path):
    '''
    add_rule aggiunge le regola che soddisfa il percorso (src, dst)
    '''
    next_hop, peso = shortest_path(path)
    rules[path] = [next_hop, peso]
    return

G = nx.Graph()
edges = []  # scoperta progressiva di raw_edges
nodes = []  # scoperta progressiva di raw_nodes

for root in raw_nodes:
    edges = edges + check_links(root)
    edges = list(set(edges))
    if root not in nodes:
        nodes.append(root)
    for j in range(0, len(edges)):      # aggiunge solo le regole progressive
        if edges[j] not in rules:
            add_rule(edges[j])
            mirror = (edges[j][1], edges[j][0])
            edges.append(mirror)
            add_rule(mirror)
        indirect_links = []
        for i in range(0,len(nodes)):       # calcola tutti i percorsi indiretti mancanti
            for j in range(0,len(nodes)):
                if nodes[i] != nodes[j]:
                    t = (nodes[i], nodes[j])
                    indirect_links.append(t)
        indirect_links = list(set(indirect_links) - set(edges))

        for i in range(0, len(indirect_links)):     # aggiunge tutte le regole dei percorsi indiretti
            add_rule(indirect_links[i])
            
    aggiungi_nodi_collegati(root)

    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    nx.draw(G)
    plt.show()

print(rules)
