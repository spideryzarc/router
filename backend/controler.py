"""
Controlador do módulo 'depots': gerencia operações de CRUD e integração com OSMNX.
"""
# Imports de bibliotecas padrão
import logging
from datetime import datetime

# Imports de bibliotecas padrão
# Imports de terceiros
from osmnx import geocode

# Imports do projeto
from backend.model import Session, Depots, Costumers, Vehicles, Orders, Planning, OrderStatus, PlanningStatus
from sqlalchemy.orm import joinedload

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_depots(active_only: bool = False):
    """
    Retorna a lista de todos os depósitos cadastrados no banco de dados.
    Se active_only for True, retorna apenas os depósitos ativos.
    """
    with Session() as session:
        query = session.query(Depots)
        if active_only:
            query = query.filter(Depots.active == True)
        depots = query.all()
        logger.info(f"{len(depots)} depósitos recuperados (active_only={active_only})")
        return depots


def add_depot(name: str, address: str, latitude: float = None, longitude: float = None):
    """
    Adiciona um novo depósito com nome e endereço.
    Se latitude e longitude forem fornecidas, utiliza-as.
    Caso contrário, e se o endereço for informado, busca latitude e longitude via OSMNX.
    Retorna a instância do depósito criado.
    """
    with Session() as session:
        depot = Depots(name=name, address=address)
        if latitude is not None and longitude is not None:
            depot.latitude = latitude
            depot.longitude = longitude
            logger.info(f"Coordenadas fornecidas para '{name}': ({latitude}, {longitude})")
        elif address:
            logger.info(f"Buscando coordenadas para o endereço: '{address}'")
            try:
                lat, lon = geocode(address)
                depot.latitude, depot.longitude = lat, lon
                logger.info(f"Coordenadas encontradas para '{address}': ({lat}, {lon})")
            except Exception as e:
                logger.warning(f"Não foi possível obter coordenadas para '{address}': {e}")
                depot.latitude = depot.longitude = None
        else:
            depot.latitude = depot.longitude = None

        session.add(depot)
        session.commit()
        logger.info(f"Depósito criado: id={depot.id}, name='{depot.name}'")
        return depot

def toggle_depot_active(depot_id: int, active: bool):
    """
    Alterna o status 'active' de um depósito existente.
    Retorna o depósito atualizado ou None se não encontrado.
    """
    with Session() as session:
        depot = session.query(Depots).filter(Depots.id == depot_id).first()
        if depot:
            depot.active = active
            session.commit()
            logger.info(f"Depósito id={depot_id} set active={active}")
        else:
            logger.warning(f"Depósito id={depot_id} não encontrado para toggle")
        return depot

def update_depot(
    depot_id: int,
    new_name: str,
    new_address: str,
    new_latitude: float = None,
    new_longitude: float = None
):
    """
    Atualiza os campos de um depósito existente.
    Retorna o depósito atualizado ou None se não encontrado.
    """
    with Session() as session:
        depot = session.query(Depots).filter(Depots.id == depot_id).first()
        if depot:
            depot.name = new_name
            depot.address = new_address
            depot.latitude = new_latitude
            depot.longitude = new_longitude
            session.commit()
            logger.info(f"Depósito id={depot_id} atualizado")
        else:
            logger.warning(f"Depósito id={depot_id} não encontrado para update")
        return depot

def get_customers():
    """
    Retorna a lista de todos os clientes cadastrados no banco de dados.
    """
    with Session() as session:
        customers = session.query(Costumers).all()
        logger.info(f"{len(customers)} clientes recuperados")
        return customers

def add_customer(name: str, email: str, address: str, latitude: float, longitude: float):
    """
    Adiciona um novo cliente com nome, e-mail e endereço.
    Retorna a instância do cliente criado.
    """
    with Session() as session:
        customer = Costumers(name=name, email=email, address=address,
                             latitude=latitude, longitude=longitude)
        session.add(customer)
        session.commit()
        logger.info(f"Cliente criado: id={customer.id}, name='{customer.name}'")
        return customer

def update_customer(cust_id: int, new_name: str, new_email: str, new_address: str,
                    new_latitude: float, new_longitude: float):
    """
    Atualiza os campos de um cliente existente.
    Retorna o cliente atualizado ou None se não encontrado.
    """
    with Session() as session:
        cust = session.query(Costumers).filter(Costumers.id == cust_id).first()
        if cust:
            cust.name, cust.email = new_name, new_email
            cust.address, cust.latitude, cust.longitude = new_address, new_latitude, new_longitude
            session.commit()
            logger.info(f"Cliente id={cust_id} atualizado")
        else:
            logger.warning(f"Cliente id={cust_id} não encontrado para update")
        return cust

def toggle_customer_active(cust_id: int, active: bool):
    """
    Alterna o status 'active' de um cliente existente.
    Retorna o cliente atualizado ou None se não encontrado.
    """
    with Session() as session:
        cust = session.query(Costumers).filter(Costumers.id == cust_id).first()
        if cust:
            cust.active = active
            session.commit()
            logger.info(f"Cliente id={cust_id} set active={active}")
        else:
            logger.warning(f"Cliente id={cust_id} não encontrado para toggle")
        return cust

def get_vehicles():
    """
    Retorna a lista de todos os veículos cadastrados no banco de dados.
    """
    with Session() as session:
        vehicles = session.query(Vehicles).options(joinedload(Vehicles.depot)).all()
        logger.info(f"{len(vehicles)} veículos recuperados")
        return vehicles

def add_vehicle(model: str, plate: str, capacity: int, cost_per_km: float, depot_id: int):
    """
    Adiciona um novo veículo com modelo, placa, capacidade e custo por km.
    Retorna a instância do veículo criado.
    """
    with Session() as session:
        vehicle = Vehicles(model=model, plate=plate, capacity=capacity,
                           cost_per_km=cost_per_km, depot_id=depot_id)
        session.add(vehicle)
        session.commit()
        logger.info(f"Veículo criado: id={vehicle.id}, plate='{vehicle.plate}'")
        return vehicle

def update_vehicle(vehicle_id: int, model: str, plate: str, capacity: int, cost_per_km: float, depot_id: int):
    """
    Atualiza os campos de um veículo existente.
    Retorna o veículo atualizado ou None se não encontrado.
    """
    with Session() as session:
        v = session.query(Vehicles).filter(Vehicles.id == vehicle_id).first()
        if v:
            v.model, v.plate = model, plate
            v.capacity, v.cost_per_km, v.depot_id = capacity, cost_per_km, depot_id
            session.commit()
            logger.info(f"Veículo id={vehicle_id} atualizado")
        return v

def toggle_vehicle_active(vehicle_id: int, active: bool):
    """
    Alterna o status 'active' de um veículo existente.
    Retorna o veículo atualizado ou None se não encontrado.
    """
    with Session() as session:
        v = session.query(Vehicles).filter(Vehicles.id == vehicle_id).first()
        if v:
            v.active = active
            session.commit()
            logger.info(f"Veículo id={vehicle_id} set active={active}")
        return v

def get_plannings(active_only: bool = False, for_selection: bool = False):
    """
    Retorna a lista de planejamentos.
    Se for_selection for True, retorna apenas planejamentos com status 'pending' or 'optimizing'
    e carrega apenas o depot.
    Caso contrário, carrega depot, orders e routes.
    """
    with Session() as session:
        query = session.query(Planning).options(joinedload(Planning.depot))
        if for_selection:
            query = query.filter(Planning.status.in_([PlanningStatus.pending, PlanningStatus.optimizing]))
        else: # For management view, load related entities
            query = query.options(joinedload(Planning.orders).joinedload(Orders.customer), joinedload(Planning.routes).joinedload(Routes.vehicle))
        plannings = query.all()
        logger.info(f"{len(plannings)} planejamentos recuperados (for_selection={for_selection})")
        return plannings

def get_orders():
    """
    Retorna a lista de todos os pedidos cadastrados, com informações do cliente e planejamento.
    """
    with Session() as session:
        orders = session.query(Orders).options(
            joinedload(Orders.customer),
            joinedload(Orders.planning)
        ).all()
        logger.info(f"{len(orders)} pedidos recuperados")
        return orders

def add_order(customer_id: int, demand: int, planning_id: int | None = None):
    """
    Adiciona um novo pedido. O status inicial é 'pending'.
    Retorna a instância do pedido criado.
    """
    with Session() as session:
        order = Orders(customer_id=customer_id, demand=demand, # type: ignore
                       status=OrderStatus.pending, planning_id=planning_id)
        session.add(order)
        session.commit()
        logger.info(f"Pedido criado: id={order.id} para cliente id={customer_id}")
        return order

def update_order(order_id: int, customer_id: int, demand: int, status_str: str, planning_id: int = None):
    """ # type: ignore
    Atualiza os campos de um pedido existente.
    Retorna o pedido atualizado ou None se não encontrado.
    """
    with Session() as session:
        order = session.query(Orders).filter(Orders.id == order_id).first()
        if order:
            order.customer_id = customer_id
            order.demand = demand
            try:
                order.status = OrderStatus[status_str]
            except KeyError:
                logger.error(f"Status inválido '{status_str}' para o pedido id={order_id}")
                return None # Ou levanta uma exceção
            order.planning_id = planning_id
            session.commit()
            logger.info(f"Pedido id={order_id} atualizado")
        else:
            logger.warning(f"Pedido id={order_id} não encontrado para update")
        return order

def add_planning(depot_id: int, deadline: datetime | None = None):
    """
    Adiciona um novo planejamento. O status inicial é 'pending'.
    Retorna a instância do planejamento criado.
    """
    with Session() as session:
        planning = Planning(depot_id=depot_id, deadline=deadline, status=PlanningStatus.pending) # type: ignore
        session.add(planning)
        session.commit()
        logger.info(f"Planejamento criado: id={planning.id} para depot id={depot_id}")
        return planning

def update_planning(planning_id: int, depot_id: int, deadline: datetime | None, status_str: str):
    """
    Atualiza os campos de um planejamento existente.
    Retorna o planejamento atualizado ou None se não encontrado.
    """
    with Session() as session:
        planning = session.query(Planning).filter(Planning.id == planning_id).first()
        if planning:
            planning.depot_id = depot_id
            planning.deadline = deadline # Permite definir deadline como None
            try:
                planning.status = PlanningStatus[status_str]
            except KeyError:
                logger.error(f"Status inválido '{status_str}' para o planejamento id={planning_id}")
                return None
            session.commit()
            logger.info(f"Planejamento id={planning_id} atualizado")
        else:
            logger.warning(f"Planejamento id={planning_id} não encontrado para update")
        return planning

if __name__ == "__main__":
    # Exemplo de uso: lista todos os depósitos ao executar este arquivo diretamente
    todos = get_depots()
    for depot in todos:
        print(f"id={depot.id}, name={depot.name}, active={depot.active}")