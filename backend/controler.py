from backend.model import Session, Depots

def get_depots():
    """
    List all depots.
    """
    session = Session()
    depots = session.query(Depots).all()
    session.close()
    return [depot.to_dict() for depot in depots]



print(get_depots())