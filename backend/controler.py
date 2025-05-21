from backend.model import Session, Depots

def get_depots():
    """
    List all depots.
    """
    session = Session()
    depots = session.query(Depots).all()
    session.close()
    return depots

def add_depot(name, address):
    """
    Add a new depot.
    """
    session = Session()
    depot = Depots(name=name, address=address)
    session.add(depot)
    session.commit()
    session.close()
    return depot



print(get_depots())