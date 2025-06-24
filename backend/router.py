from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def create_sample_data():
    """Stores the data for the problem."""
    data = {}
    data["distance_matrix"] = [
        # fmt: off
      [0, 548, 776, 696, 582, 274, 502, 194, 308, 194, 536, 502, 388, 354, 468, 776, 662],
      [548, 0, 684, 308, 194, 502, 730, 354, 696, 742, 1084, 594, 480, 674, 1016, 868, 1210],
      [776, 684, 0, 992, 878, 502, 274, 810, 468, 742, 400, 1278, 1164, 1130, 788, 1552, 754],
      [696, 308, 992, 0, 114, 650, 878, 502, 844, 890, 1232, 514, 628, 822, 1164, 560, 1358],
      [582, 194, 878, 114, 0, 536, 764, 388, 730, 776, 1118, 400, 514, 708, 1050, 674, 1244],
      [274, 502, 502, 650, 536, 0, 228, 308, 194, 240, 582, 776, 662, 628, 514, 1050, 708],
      [502, 730, 274, 878, 764, 228, 0, 536, 194, 468, 354, 1004, 890, 856, 514, 1278, 480],
      [194, 354, 810, 502, 388, 308, 536, 0, 342, 388, 730, 468, 354, 320, 662, 742, 856],
      [308, 696, 468, 844, 730, 194, 194, 342, 0, 274, 388, 810, 696, 662, 320, 1084, 514],
      [194, 742, 742, 890, 776, 240, 468, 388, 274, 0, 342, 536, 422, 388, 274, 810, 468],
      [536, 1084, 400, 1232, 1118, 582, 354, 730, 388, 342, 0, 878, 764, 730, 388, 1152, 354],
      [502, 594, 1278, 514, 400, 776, 1004, 468, 810, 536, 878, 0, 114, 308, 650, 274, 844],
      [388, 480, 1164, 628, 514, 662, 890, 354, 696, 422, 764, 114, 0, 194, 536, 388, 730],
      [354, 674, 1130, 822, 708, 628, 856, 320, 662, 388, 730, 308, 194, 0, 342, 422, 536],
      [468, 1016, 788, 1164, 1050, 514, 514, 662, 320, 274, 388, 650, 536, 342, 0, 764, 194],
      [776, 868, 1552, 560, 674, 1050, 1278, 742, 1084, 810, 1152, 274, 388, 422, 764, 0, 798],
      [662, 1210, 754, 1358, 1244, 708, 480, 856, 514, 468, 354, 844, 730, 536, 194, 798, 0],
        # fmt: on
    ]
    data["num_vehicles"] = 4
    data["demands"] = [0, 1, 1, 2, 4, 2, 4, 8, 8, 4, 2, 4, 2, 1, 1, 2, 4]
    data["vehicle_capacities"] = [15, 15, 15, 15]
    data["depot"] = 0
    return data



def solve_vrp(input_data: dict) -> dict:
    """
    Resolve o Problema de Roteamento de Veículos (VRP) com restrições de capacidade.

    Args:
        input_data: Um dicionário contendo os dados do problema:
            - distance_matrix: Matriz de distâncias entre todos os locais.
            - num_vehicles: Número de veículos disponíveis.
            - depot: Índice do nó que representa o depósito (ponto de partida e chegada).
            - demands: Lista de demandas para cada local (0 para o depósito).
            - vehicle_capacities: Lista de capacidades para cada veículo.

    Returns:
        Um dicionário contendo a solução encontrada:
            - objective: O custo total da solução (distância total percorrida por todos os veículos).
            - routes: Um dicionário mapeando o ID de cada veículo para sua rota e distância.
            - max_route_distance: A distância máxima percorrida por um único veículo.
        Ou um dicionário com uma chave "error" se nenhuma solução for encontrada.
    """
    # Configuração do modelo usando input_data
    data = input_data
    # 1. Gerenciador de Índices de Roteamento (Routing Index Manager):
    # Cria um mapeamento entre os índices internos do solver (0 a N-1) e os nós do problema
    # (índices da matriz de distância, 0 a M-1). Isso é necessário porque o solver
    # trabalha com uma representação interna diferente.
    # Argumentos:
    # - len(data["distance_matrix"]): Número total de locais (nós) no problema.
    # - data["num_vehicles"]: Número de veículos (rotas) a serem planejadas.
    # - data["depot"]: O índice do nó que serve como depósito inicial e final para todas as rotas.
    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]), data["num_vehicles"], data["depot"]
    )
    # 2. Modelo de Roteamento (Routing Model):
    # Cria o modelo principal do problema de roteamento, usando o gerenciador de índices.
    # Este objeto conterá todas as variáveis, restrições e o objetivo do problema.
    routing = pywrapcp.RoutingModel(manager)

    # 3. Função Callback para Distância (Custo do Arco):
    # Define como calcular o custo (distância) de viajar entre dois locais.
    # O solver chama esta função sempre que precisa avaliar o custo de um arco (trecho) na rota.
    def distance_callback(from_index, to_index):
        """Retorna a distância entre dois nós."""
        # Converte os índices internos do solver de volta para os índices dos nós originais.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        # Retorna a distância da matriz de distâncias pré-calculada.
        return data["distance_matrix"][from_node][to_node]

    # Registra a função de callback de distância no modelo.
    # O solver usará esta função para calcular os custos de transição (arcos).
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    # Define o custo de cada arco (trecho entre locais) para todos os veículos.
    # Informa ao solver para usar a 'distance_callback' para determinar o custo de viajar
    # entre quaisquer dois pontos em uma rota.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # 4. Função Callback para Demandas (Restrição de Capacidade):
    # Define como obter a demanda de um local específico.
    # O solver usa isso para rastrear a carga acumulada em cada veículo.
    def demand_callback(from_index):
        """Retorna a demanda de um nó."""
        # Converte o índice interno do solver para o índice do nó original.
        from_node = manager.IndexToNode(from_index)
        # Retorna a demanda associada a esse nó.
        return data["demands"][from_node]

    # Registra a função de callback de demanda no modelo.
    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    # Adiciona a dimensão de capacidade ao problema. Isso permite ao solver
    # rastrear a carga acumulada em cada veículo e garantir que não exceda a capacidade.
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,  # A função que retorna a demanda de cada local.
        0,                      # Slack (folga): Capacidade não utilizada permitida (0 significa sem folga).
        data["vehicle_capacities"], # Lista das capacidades máximas de cada veículo.
        True,                   # start_cumul_to_zero: Define se o acumulador (carga) começa em 0 no início da rota.
        "Capacity",             # Nome da dimensão (usado para depuração e identificação).
    )

    # 5. Configuração dos Parâmetros de Busca:
    # Define a estratégia que o solver usará para encontrar a primeira solução.
    # PATH_CHEAPEST_ARC: Uma heurística comum que constrói rotas adicionando iterativamente
    # o arco (trecho) mais barato disponível que conecta um nó não visitado a uma rota existente,
    # respeitando as restrições.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    # Outras opções de estratégia e parâmetros de busca podem ser configuradas aqui
    # para melhorar a qualidade da solução ou o tempo de execução (ex: metaheurísticas como
    # GUIDED_LOCAL_SEARCH, TABU_SEARCH, ou limites de tempo).
    # search_parameters.local_search_metaheuristic = (
    #     routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    # search_parameters.time_limit.seconds = 30

    # 6. Resolução do Problema:
    # Executa o solver com os parâmetros definidos para encontrar uma solução.
    solution = routing.SolveWithParameters(search_parameters)

    # 7. Processamento e Retorno da Solução:
    result = {}
    if solution:
        # Se uma solução foi encontrada, extrai as informações relevantes.
        # Objetivo: O valor total otimizado (neste caso, a soma das distâncias de todas as rotas).
        result["objective"] = solution.ObjectiveValue()
        routes = {}
        max_route_distance = 0
        total_distance_manual = 0 # Variável para verificar o cálculo da distância total

        # Itera sobre cada veículo para extrair sua rota e distância.
        for vehicle_id in range(data["num_vehicles"]):
            index = routing.Start(vehicle_id) # Obtém o índice do nó inicial para este veículo.
            route = []
            route_distance = 0
            # Percorre a rota do veículo nó por nó até retornar ao depósito.
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index) # Converte o índice do solver para o nó original.
                route.append(node_index)
                previous_index = index
                index = solution.Value(routing.NextVar(index)) # Obtém o próximo índice na rota do veículo.
                # Calcula a distância do arco entre o nó anterior e o nó atual usando a callback.
                arc_distance = distance_callback(previous_index, index)
                route_distance += arc_distance

            # Adiciona o último nó (depósito) à rota visual.
            node_index = manager.IndexToNode(index)
            route.append(node_index)

            # Armazena a rota e a distância calculada para este veículo.
            routes[vehicle_id] = {"route": route, "distance": route_distance}
            # Atualiza a distância máxima encontrada entre todas as rotas.
            max_route_distance = max(max_route_distance, route_distance)
            # Acumula a distância desta rota na distância total manual.
            total_distance_manual += route_distance

        # Verificação opcional: Comparar a distância total calculada manualmente com o objetivo do solver.
        # Podem existir pequenas diferenças devido a arredondamentos ou à forma como o solver calcula.
        # print(f"Objective from solver: {result['objective']}")
        # print(f"Total distance calculated manually: {total_distance_manual}")
        # Descomentar a linha abaixo pode ser útil se houver discrepâncias significativas e
        # você preferir usar o valor calculado manualmente.
        # result["objective"] = total_distance_manual

        result["routes"] = routes
        result["max_route_distance"] = max_route_distance
    else:
        # Se nenhuma solução foi encontrada, retorna uma mensagem de erro.
        result["error"] = "No solution found"
    return result


if __name__ == "__main__":
    # Exemplo de utilização da função solve_vrp
    data_model = create_sample_data()
    result = solve_vrp(data_model)
    if "error" not in result:
        print("Objective:", result["objective"])
        for vehicle, route_info in result["routes"].items():
            print(f"Veículo {vehicle}: Rota: {route_info['route']} - Distância: {route_info['distance']}m")
        print("Máxima distância percorrida:", result["max_route_distance"], "m")
    else:
        print(result["error"])
