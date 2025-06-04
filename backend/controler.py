"""
Controlador do módulo 'depots': gerencia operações de CRUD e integração com OSMNX.
"""

# Imports de bibliotecas padrão
import logging

# Imports de terceiros
from osmnx import geocode

# Imports do projeto
from backend.model import Session, Depots, Costumers

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_depots():
    """
    Retorna a lista de todos os depósitos cadastrados no banco de dados.
    """
    session = Session()
    try:
        depots = session.query(Depots).all()
        logger.info(f"{len(depots)} depósitos recuperados com sucesso")
        return depots
    finally:
        session.close()

def add_depot(name: str, address: str):
    """
    Adiciona um novo depósito com nome e endereço.
    Se o endereço for informado, busca latitude e longitude via OSMNX.
    Retorna a instância do depósito criado.
    """
    session = Session()
    try:
        depot = Depots(name=name, address=address)
        if address:
            location = geocode(address)
            logger.info(f"Location found for '{address}': {location}")
            if location:
                depot.latitude, depot.longitude = location[0], location[1]
            else:
                depot.latitude = depot.longitude = None
        else:
            depot.latitude = depot.longitude = None

        session.add(depot)
        session.commit()
        logger.info(f"Depósito criado: id={depot.id}, name='{depot.name}'")
        return depot
    finally:
        session.close()

def toggle_depot_active(depot_id: int, active: bool):
    """
    Alterna o status 'active' de um depósito existente.
    Retorna o depósito atualizado ou None se não encontrado.
    """
    session = Session()
    try:
        depot = session.query(Depots).filter(Depots.id == depot_id).first()
        if depot:
            depot.active = active
            session.commit()
            logger.info(f"Depósito id={depot_id} set active={active}")
        else:
            logger.warning(f"Depósito id={depot_id} não encontrado para toggle")
        return depot
    finally:
        session.close()

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
    session = Session()
    try:
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
    finally:
        session.close()

def get_customers():
    """
    Retorna a lista de todos os clientes cadastrados no banco de dados.
    """
    session = Session()
    try:
        customers = session.query(Costumers).all()
        logger.info(f"{len(customers)} clientes recuperados")
        return customers
    finally:
        session.close()

def add_customer(name: str, email: str, address: str, latitude: float, longitude: float):
    """
    Adiciona um novo cliente com nome, e-mail e endereço.
    Retorna a instância do cliente criado.
    """
    session = Session()
    try:
        customer = Costumers(name=name, email=email, address=address,
                             latitude=latitude, longitude=longitude)
        session.add(customer)
        session.commit()
        logger.info(f"Cliente criado: id={customer.id}, name='{customer.name}'")
        return customer
    finally:
        session.close()

def update_customer(cust_id: int, new_name: str, new_email: str, new_address: str,
                    new_latitude: float, new_longitude: float):
    """
    Atualiza os campos de um cliente existente.
    Retorna o cliente atualizado ou None se não encontrado.
    """
    session = Session()
    try:
        cust = session.query(Costumers).filter(Costumers.id == cust_id).first()
        if cust:
            cust.name, cust.email = new_name, new_email
            cust.address, cust.latitude, cust.longitude = new_address, new_latitude, new_longitude
            session.commit()
            logger.info(f"Cliente id={cust_id} atualizado")
        else:
            logger.warning(f"Cliente id={cust_id} não encontrado para update")
        return cust
    finally:
        session.close()

def toggle_customer_active(cust_id: int, active: bool):
    """
    Alterna o status 'active' de um cliente existente.
    Retorna o cliente atualizado ou None se não encontrado.
    """
    session = Session()
    try:
        cust = session.query(Costumers).filter(Costumers.id == cust_id).first()
        if cust:
            cust.active = active
            session.commit()
            logger.info(f"Cliente id={cust_id} set active={active}")
        else:
            logger.warning(f"Cliente id={cust_id} não encontrado para toggle")
        return cust
    finally:
        session.close()

if __name__ == "__main__":
    # Exemplo de uso: lista todos os depósitos ao executar este arquivo diretamente
    todos = get_depots()
    for depot in todos:
        print(f"id={depot.id}, name={depot.name}, active={depot.active}")