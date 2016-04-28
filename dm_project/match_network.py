import networkx as nx
import matplotlib.pyplot as plt


# convert file of matches into dict
# keys are ids, vals are lists of tuples of (id, %compat)
def import_matches(filename):
    f = open(filename)
    matches = {}
    for line in f:
        id_and_matches = line.split(':')
        match_weights = []
        for m in id_and_matches[1:-1]:
            m_id_and_weight = m.split(',')
            match_weights += [((int)(m_id_and_weight[0]),
                              (float)(m_id_and_weight[1]))]
        matches[(int)(id_and_matches[0])] = match_weights
        print id_and_matches[0]
    f.close()
    return matches


def gen_graph_from_dict(matches, num_matches=10):
    G = nx.Graph()
    G.add_nodes_from(matches.keys())
    for u in matches.keys():
        edges = [(u, m[0], m[1]) for m in matches[u][0:1]]
        G.add_weighted_edges_from(edges)
    return G

matches = import_matches('matches_2016.txt')
g = gen_graph_from_dict(matches)

print "num connected components:"
print nx.number_connected_components(g)
print "average clustering coefficient:"
print nx.average_clustering(g)
print "5-clique communities:"
print list(nx.k_clique_communities(g, 4))

nx.draw_circular(g)
plt.show()
# plt.savefig("path.png")

# G = nx.complete_graph(5)
# nx.draw(G)
# plt.show()
