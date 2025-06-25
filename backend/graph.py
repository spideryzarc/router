import networkx as nx
import osmnx as ox
import os
import numpy as np

# Default settings for Graph class
_DEFAULT_GRAPH_FILE_NAME = "fortaleza.ghml"
_DEFAULT_CITY = "Fortaleza, Ceará, Brasil"


class Graph:
    def __init__(self, graph_file_name=_DEFAULT_GRAPH_FILE_NAME):
        self.graph = nx.MultiDiGraph()
        self._graph_file_name = graph_file_name
        self._load_graph()

    def _load_graph(self):
        if os.path.exists(self._graph_file_name):
            print(f"Carregando grafo de {self._graph_file_name}...")
            self.graph = ox.load_graphml(self._graph_file_name)
        else:
            print(f"Arquivo {self._graph_file_name} não encontrado. Baixando o grafo {_DEFAULT_CITY}...")
            self.graph = ox.graph_from_place(_DEFAULT_CITY, network_type='drive')
            print(f"Salvando o grafo como {self._graph_file_name}...")
            ox.save_graphml(self.graph, self._graph_file_name)
            print("Grafo salvo localmente.")
            
    
    def distance(self, coord1, coord2):
        if not hasattr(self, '_nodes'):
            self._nodes = {} # dicionário para mapear coordenadas para nó mais próximo
        if coord1 not in self._nodes:
            self._nodes[coord1] = ox.distance.nearest_nodes(self.graph, coord1[1], coord1[0])
        if coord2 not in self._nodes:
            self._nodes[coord2] = ox.distance.nearest_nodes(self.graph, coord2[1], coord2[0])
        return nx.shortest_path_length(self.graph, source=self._nodes[coord1], target=self._nodes[coord2], weight='length')
   
   
    def distance_matrix(self, coords: list[tuple[float, float]]) -> np.ndarray:
        # Mapeia coordenadas para nós
        nodes = [ox.distance.nearest_nodes(self.graph, coord[1], coord[0]) for coord in coords]
        n = len(nodes)
        mat = np.zeros((n, n))

        # Calcula apenas as distâncias entre os pares do subconjunto
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if i != j:
                    try:
                        mat[i, j] = nx.shortest_path_length(self.graph, source=node1, target=node2, weight='length')
                    except nx.NetworkXNoPath:
                        mat[i, j] = np.inf
        return mat
    
    def route(self, coord1, coord2):
        if not hasattr(self, '_nodes'):
            self._nodes = {}
        if coord1 not in self._nodes:
            self._nodes[coord1] = ox.distance.nearest_nodes(self.graph, coord1[1], coord1[0])
        if coord2 not in self._nodes:
            self._nodes[coord2] = ox.distance.nearest_nodes(self.graph, coord2[1], coord2[0])
        nodes =  nx.shortest_path(self.graph, source=self._nodes[coord1], target=self._nodes[coord2], weight='length')
        return [(self.graph.nodes[node]['y'], self.graph.nodes[node]['x']) for node in nodes]



graph = Graph()

if __name__ == "__main__":
    print(f"Grafo carregado com {len(graph.graph.nodes)} nós e {len(graph.graph.edges)} arestas.")    
    coord1 = (-3.71722, -38.54333)  # Exemplo de coordenadas (latitude, longitude)
    coord2 = (-3.71822, -38.54533)  # Outro exemplo de coordenadas (latitude, longitude)
    distance = graph.distance(coord1, coord2)
    print(f"A distância entre {coord1} e {coord2} é {distance:.2f} metros.")
    coords = [coord1, coord2, (-3.71922, -38.54533)]  # Lista de coordenadas
    dist_matrix = graph.distance_matrix(coords)
    print("Matriz de distâncias:")
    print(dist_matrix)
    route = graph.route(coord1, coord2)
    print(f"Rota entre {coord1} e {coord2}:")
    print(route)

