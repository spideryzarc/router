from backend.model import Session, Depots
from osmnx import geocode 

def get_depots():
    """
    List all depots.
    """
    session = Session()
    depots = session.query(Depots).all()
    session.close()
    return depots

def add_depot(name, address):
    """p
    Add a new depot.
    """
    session = Session()
    depot = Depots(name=name, address=address)
    #search for latitude and longitude using OSMN
    if address:
        location = geocode(address)
        print(f"Location found for {address}: {location}")
        if location:
            depot.latitude = location[0]
            depot.longitude = location[1]
    else:
        depot.latitude = None
        depot.longitude = None


    session.add(depot)
    session.commit()
    session.close()
    return depot

def toggle_depot_active(depot_id, active):
    """
    Toggle the active status of a depot.
    """
    session = Session()
    depot = session.query(Depots).filter(Depots.id == depot_id).first()
    if depot:
        depot.active = active
        session.commit()
    session.close()
    return depot

def update_depot(depot_id, new_name, new_address, new_latitude=None, new_longitude=None):
    """
    Update an existing depot.
    """
    session = Session()
    depot = session.query(Depots).filter(Depots.id == depot_id).first()
    if depot:
        depot.name = new_name
        depot.address = new_address
        depot.latitude = new_latitude
        depot.longitude = new_longitude
        session.commit()
    session.close()
    return depot



print(get_depots())