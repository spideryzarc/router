from sqlalchemy import Column, Integer, Unicode, UnicodeText, String, Float, Boolean, Enum, DateTime, Table, select
from sqlalchemy import create_engine, ForeignKey, insert
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
import enum
from datetime import datetime, timezone, timedelta

# Create a SQLite engine for the database (router.db)
engine = create_engine("sqlite:///router.db")
# Create a base class for declarative models
Base = declarative_base()
# Create a session factory
Session = sessionmaker(bind=engine)

# Define costumers table
class Costumers(Base):
    __tablename__ = "costumers"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True, index=True)
    address = Column(UnicodeText)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    orders = relationship("Orders", back_populates="customer")

# Define depots table
class Depots(Base):
    __tablename__ = "depots"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    address = Column(UnicodeText)
    latitude = Column(Float, default=float("nan"))
    longitude = Column(Float, default=float("nan"))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    vehicles = relationship("Vehicles", back_populates="depot")
    planning = relationship("Planning", back_populates="depot")

# Define vehicles table
class Vehicles(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True)
    model = Column(String(100))
    plate = Column(String(10), unique=True, index=True, nullable=False)
    capacity = Column(Integer, nullable=False)
    cost_per_km = Column(Float, default=1.0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    depot_id = Column(Integer, ForeignKey("depots.id"), nullable=False)
    depot = relationship("Depots", back_populates="vehicles")
    routes = relationship("Routes", back_populates="vehicle")

# Define an Enum for Order Status
class OrderStatus(enum.Enum):
    pending = "pending"
    processing = "processing"
    delivered = "delivered"
    cancelled = "cancelled"

# Define orders table
class Orders(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.pending, nullable=False)
    demand = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    customer_id = Column(Integer, ForeignKey("costumers.id"), nullable=False)
    customer = relationship("Costumers", back_populates="orders")
    planning_id = Column(Integer, ForeignKey("planning.id"))
    planning = relationship("Planning", back_populates="orders")
    route_id = Column(Integer, ForeignKey("routes.id"))  # Nova FK para rota
    sequence_position = Column(Integer)  # Posição na rota
    route = relationship("Routes", back_populates="orders")

# Define an Enum for Planning Status
class PlanningStatus(enum.Enum):
    pending = "pending"
    optimizing = "optimizing"
    ready = "ready"
    executed = "executed"
    cancelled = "cancelled"

# Define a table for planning
class Planning(Base):
    __tablename__ = "planning"
    id = Column(Integer, primary_key=True)
    deadline = Column(DateTime, nullable=True)
    status = Column(Enum(PlanningStatus), default=PlanningStatus.pending, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    orders = relationship("Orders", back_populates="planning")
    depot_id = Column(Integer, ForeignKey("depots.id"), nullable=False)
    depot = relationship("Depots", back_populates="planning")
    routes = relationship("Routes", back_populates="planning")

# Define a table for routes
class Routes(Base):
    __tablename__ = "routes"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    distance = Column(Float, nullable=False, default=0.0)
    load = Column(Float, nullable=False, default=0.0)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    vehicle = relationship("Vehicles", back_populates="routes")
    planning_id = Column(Integer, ForeignKey("planning.id"), nullable=False)
    planning = relationship("Planning", back_populates="routes")
    orders = relationship(
        "Orders",
        back_populates="route",
        order_by="Orders.sequence_position"
    )

# Create all tables in the database if they don't exist
Base.metadata.create_all(engine)

if __name__ == "__main__":
    print("--- Cleaning and Creating Database ---")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("Tables:", Base.metadata.tables.keys())

    # Use session context manager and transaction block
    with Session() as session:
        with session.begin(): # Start a transaction
            print("\n--- Creating Base Entities ---")

            # 1. Create Depot
            depot1 = Depots(name="Main Depot", address="1 Depot Lane", latitude=40.7, longitude=-74.0)
            session.add(depot1)
            # No commit needed here

            # 2. Create Vehicle (needs depot1 flushed to get ID, session.begin() handles flush)
            session.flush() # Flush to ensure depot1 has an ID assigned
            print(f"Created Depot: {depot1.name} (ID: {depot1.id})")
            vehicle1 = Vehicles(model="Electric Van", plate="EVAN01", capacity=50, cost_per_km=0.5, depot_id=depot1.id)
            session.add(vehicle1)

            # 3. Create Customers
            customer1 = Costumers(name="Alice", email="alice@example.com", address="123 Apple St", latitude=40.71, longitude=-74.01)
            customer2 = Costumers(name="Bob", email="bob@example.com", address="456 Banana Ave", latitude=40.72, longitude=-74.02)
            session.add_all([customer1, customer2])

            # 4. Create Orders (needs customers flushed)
            session.flush() # Flush to ensure customers have IDs
            print(f"Created Vehicle: {vehicle1.plate} (ID: {vehicle1.id}) at Depot ID: {vehicle1.depot_id}")
            print(f"Created Customer: {customer1.name} (ID: {customer1.id})")
            print(f"Created Customer: {customer2.name} (ID: {customer2.id})")
            order1 = Orders(customer_id=customer1.id, demand=5, status=OrderStatus.pending)
            order2 = Orders(customer_id=customer2.id, demand=8, status=OrderStatus.pending)
            order3 = Orders(customer_id=customer1.id, demand=3, status=OrderStatus.pending)
            session.add_all([order1, order2, order3])

            # 5. Create Planning (needs depot flushed)
            session.flush() # Ensure orders have IDs
            print(f"Created Order: ID {order1.id} (Demand: {order1.demand}) for Customer ID: {order1.customer_id}")
            print(f"Created Order: ID {order2.id} (Demand: {order2.demand}) for Customer ID: {order2.customer_id}")
            print(f"Created Order: ID {order3.id} (Demand: {order3.demand}) for Customer ID: {order3.customer_id}")
            print("\n--- Creating Planning and Associating Orders ---")
            # Set a deadline for 24 hours from now
            example_deadline = datetime.now(timezone.utc) + timedelta(hours=24)
            planning1 = Planning(depot_id=depot1.id, status=PlanningStatus.pending, deadline=example_deadline)
            session.add(planning1)

            # 6. Associate Orders with Planning (needs planning flushed)
            session.flush() # Ensure planning has ID
            print(f"Created Planning: ID {planning1.id} for Deadline {planning1.deadline} at Depot ID: {planning1.depot_id}")
            # Use session.get (modern equivalent of query.get)
            order_to_plan1 = session.get(Orders, order1.id)
            order_to_plan2 = session.get(Orders, order2.id)
            if order_to_plan1 and order_to_plan2:
                order_to_plan1.planning_id = planning1.id
                order_to_plan1.status = OrderStatus.processing
                order_to_plan2.planning_id = planning1.id
                order_to_plan2.status = OrderStatus.processing
                print(f"Associated Order {order_to_plan1.id} with Planning {planning1.id}, Status: {order_to_plan1.status.value}")
                print(f"Associated Order {order_to_plan2.id} with Planning {planning1.id}, Status: {order_to_plan2.status.value}")
            else:
                 print("Error: Could not fetch orders to associate with planning.")


            # 7. Create Route (needs planning and vehicle flushed)
            session.flush() # Ensure vehicle has ID
            print("\n--- Creating Route and Linking Orders in Sequence ---")
            route1 = Routes(planning_id=planning1.id, vehicle_id=vehicle1.id, distance=25.5, load=13.0)
            session.add(route1)

            # 8. Link Orders to Route
            session.flush() # Ensure route has ID
            print(f"Created Route: ID {route1.id} for Planning ID: {route1.planning_id} using Vehicle ID: {route1.vehicle_id}")
            order2.route_id = route1.id
            order2.sequence_position = 0
            order1.route_id = route1.id
            order1.sequence_position = 1
            print(f"Linked Route {route1.id} -> Order {order2.id} (Seq: 0)")
            print(f"Linked Route {route1.id} -> Order {order1.id} (Seq: 1)")

        # Transaction is automatically committed here if no exceptions occurred
        print("\n--- Transaction Committed ---")

        # --- Querying and Displaying Data (after commit) ---
        print("\n--- Querying and Displaying Data ---")
        # Use a new block or the same session (objects might be expired, refetching is safer)
        # Re-fetch objects using session.get or execute(select) for clarity
        fetched_planning = session.get(Planning, planning1.id)
        if fetched_planning:
             # Eager load relationships if needed when querying, or access them (triggers lazy load)
             print(f"\nFetched Planning ID: {fetched_planning.id}")
             print(f"  Deadline: {fetched_planning.deadline}")
             print(f"  Status: {fetched_planning.status.value}")
             # Access relationships (may trigger lazy loads if not eager loaded)
             print(f"  Depot: {fetched_planning.depot.name}")
             print(f"  Orders in Planning: {[o.id for o in fetched_planning.orders]}")
        else:
            print(f"Could not fetch Planning ID {planning1.id}")


        fetched_route = session.get(Routes, route1.id)
        if fetched_route:
            print(f"\nFetched Route ID: {fetched_route.id}")
            # Access relationships
            print(f"  Vehicle: {fetched_route.vehicle.plate} (Capacity: {fetched_route.vehicle.capacity})")
            print(f"  Distance: {fetched_route.distance} km")
            print(f"  Load: {fetched_route.load}")
            print(f"  Planning ID: {fetched_route.planning.id}")

            print("  Orders in Route (Sequence):")
            if fetched_route.orders:
                # Accessing orders triggers the relationship load, respecting order_by
                for i, order in enumerate(fetched_route.orders):
                     # Access customer within the loop (triggers lazy load if not eager loaded before)
                     print(f"    {i}: Order ID {order.id} (Customer: {order.customer.name}, Demand: {order.demand}, Status: {order.status.value})")
            else:
                print("    No orders associated with this route.")
        else:
            print(f"Could not fetch Route ID {route1.id}")


        print(f"\nRoutes for Vehicle {vehicle1.plate}:")
        # Fetch vehicle again to access its routes
        vehicle_obj = session.get(Vehicles, vehicle1.id)
        if vehicle_obj and vehicle_obj.routes:
             for r in vehicle_obj.routes:
                 # Accessing r.orders will lazy-load them if needed
                 print(f"  Route ID: {r.id}, Distance: {r.distance}, Orders: {[o.id for o in r.orders]}")
        else:
            print(f"  No routes found for Vehicle {vehicle1.plate}")


    print("\n--- Session Closed ---")
