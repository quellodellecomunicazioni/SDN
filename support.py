def vicini(nodo, collegamenti):
	vicini = []
	for test in collegamenti:
		if test[0] == nodo:
			if test[1] not in vicini:
				vicini.append(test[1])
		elif test[1] == nodo:
			if test[0] not in vicini:
				vicini.append(test[0])
	return vicini

def coll_vicini(nodo, collegamenti):
	coll_vicini = []
	for test in collegamenti:
		if test[0] == nodo or test[1] == nodo:
			if test not in coll_vicini:
				coll_vicini.append(test)
	return coll_vicini

def regole_dirette(path, rules, collegamenti):
	src = path[0]
	dst = path[1]
	vicini_di_src = vicini(src, collegamenti)

	if dst in vicini_di_src:
		weight = 1
		next_hop = dst
		rules[path] = [next_hop, weight]
	
	return rules

def regole_indirette(path, rules, collegamenti):
	src = path[0]
	dst = path[1]
	vicini_di_src = vicini(src, collegamenti)

	next_hop = 0
	weight = 100
	for test in vicini_di_src:
		n_path = (test, dst)
		if n_path in rules:
			next_hop_provv = test
			weight_provv = 1 + rules[n_path][1]
			if weight_provv < weight:
				next_hop = next_hop_provv
				weight = weight_provv

	rules[path] = [next_hop, weight]

	return rules

def combinazioni(nodi, links):
	combinazioni_dir = []
	combinazioni_ind = []
	for i in range(0, len(nodi)):
		for j in range(0, len(nodi)):
			if i != j:		
				combo = (nodi[i],nodi[j])
				if nodi[j] in vicini(nodi[i], links):
					combinazioni_dir.append(combo)
				else:
					combinazioni_ind.append(combo)

	return combinazioni_dir, combinazioni_ind