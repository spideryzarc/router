"""
Gerenciamento de pedidos: cadastro, edição, cancelamento, lista.
"""
from nicegui import ui
from backend.controler import (
    get_orders,
    add_order,
    update_order,
    get_customers,
    get_plannings,
)
from backend.model import OrderStatus
import folium
from statistics import mean

ui.state.show_cancelled_orders = False
_order_list_container = None # type: ignore
_order_map_container = None # type: ignore

def add_order_dialog():
    with ui.dialog() as dialog, ui.card():
        ui.label("Adicionar Novo Pedido").classes("text-h6")
        
        customer_options = {c.id: c.name for c in get_customers() if c.active}
        customer_in = ui.select(label="Cliente", options=customer_options)
        
        demand_in = ui.number(label="Demanda", value=1, min=1)
        
        planning_options = {p.id: f"ID: {p.id} (Depot: {p.depot.name if p.depot else 'N/A'})" for p in get_plannings(active_only=True)}
        planning_options[None] = "Nenhum" # Allow no planning
        planning_in = ui.select(label="Planejamento (Opcional)", options=planning_options, value=None)

        def save():
            if not (customer_in.value and demand_in.value):
                ui.notify("Cliente e Demanda são obrigatórios.", color="negative"); return
            try:
                demand_val = int(demand_in.value)
                if demand_val <= 0:
                    ui.notify("Demanda deve ser um número positivo.", color="negative"); return
            except ValueError:
                ui.notify("Demanda inválida.", color="negative"); return

            add_order(customer_id=customer_in.value, demand=demand_val, planning_id=planning_in.value)
            refresh("Pedido adicionado!")
            dialog.close()

        with ui.card_actions().classes("w-full justify-end"):
            ui.button("Salvar", on_click=save, color="primary", icon="save")
            ui.button("Cancelar", on_click=dialog.close, color="negative", icon="close")
    dialog.open()

def edit_order_dialog(order_obj):
    with ui.dialog() as dialog, ui.card():
        ui.label("Editar Pedido").classes("text-h6")

        customer_options = {c.id: c.name for c in get_customers()} # Show all for editing context
        customer_in = ui.select(label="Cliente", options=customer_options, value=order_obj.customer_id)
        
        demand_in = ui.number(label="Demanda", value=order_obj.demand, min=1)
        
        # Include current planning even if not "active" for context, plus active ones
        current_planning_id = order_obj.planning_id
        planning_options = {p.id: f"ID: {p.id} (Depot: {p.depot.name if p.depot else 'N/A'})" for p in get_plannings(active_only=True)}
        if current_planning_id and current_planning_id not in planning_options:
            if order_obj.planning: # Check if planning object is loaded
                 planning_options[current_planning_id] = f"ID: {order_obj.planning.id} (Depot: {order_obj.planning.depot.name if order_obj.planning.depot else 'N/A'}) - Atual"
            else: # Fallback if planning object not loaded (should be by get_orders)
                 planning_options[current_planning_id] = f"ID: {current_planning_id} - Atual"

        planning_options[None] = "Nenhum"
        planning_in = ui.select(label="Planejamento (Opcional)", options=planning_options, value=current_planning_id)

        status_options = {s.name: s.value for s in OrderStatus}
        status_in = ui.select(label="Status", options=status_options, value=order_obj.status.name)

        def save():
            if not (customer_in.value and demand_in.value and status_in.value):
                ui.notify("Cliente, Demanda e Status são obrigatórios.", color="negative"); return
            try:
                demand_val = int(demand_in.value)
                if demand_val <= 0:
                    ui.notify("Demanda deve ser um número positivo.", color="negative"); return
            except ValueError:
                ui.notify("Demanda inválida.", color="negative"); return

            update_order(order_id=order_obj.id, customer_id=customer_in.value, demand=demand_val,
                         status_str=status_in.value, planning_id=planning_in.value)
            refresh("Pedido atualizado!")
            dialog.close()

        with ui.card_actions().classes("w-full justify-end"):
            ui.button("Salvar", on_click=save, color="primary", icon="save")
            ui.button("Cancelar", on_click=dialog.close, color="negative", icon="close")
    dialog.open()

def order_list_ui():
    _order_list_container.clear()
    with _order_list_container, ui.card().classes("w-full h-full overflow-auto"):
        with ui.row().classes("items-center justify-between w-full"):
            ui.label("Pedidos Cadastrados").classes("text-h5")
            ui.icon("shopping_cart").classes("text-h4")
        with ui.row().classes("w-full items-center"):
            ui.button("Adicionar Pedido", on_click=add_order_dialog,
                      color="primary", icon="add").classes("mb-4")
            # TODO: Add filter for cancelled/completed orders if needed
            # ui.switch("Mostrar cancelados/concluídos", ...)

        orders = get_orders()
        if orders:
            ui.separator()
            for o in orders:
                # Basic filtering example:
                # if o.status == OrderStatus.cancelled and not ui.state.show_cancelled_orders:
                #     continue
                with ui.row().classes("items-center justify-between w-full p-2 hover:bg-gray-100"):
                    with ui.column().classes("flex-grow"):
                        ui.label(f"ID: {o.id} - Cliente: {o.customer.name if o.customer else 'N/A'}").classes("font-semibold")
                        ui.label(f"Demanda: {o.demand} - Status: {o.status.value}")
                        ui.label(f"Planejamento ID: {o.planning_id if o.planning_id else 'Nenhum'}")
                        ui.label(f"Criado em: {o.created_at.strftime('%Y-%m-%d %H:%M') if o.created_at else 'N/A'}")

                    with ui.row().classes("gap-2 items-center"):
                        ui.button(icon="edit", on_click=lambda ord_obj=o: edit_order_dialog(ord_obj), color="primary").tooltip("Editar Pedido")
                        if o.status not in [OrderStatus.delivered, OrderStatus.cancelled]:
                             ui.button(icon="cancel", on_click=lambda ord_obj=o: update_order(ord_obj.id, ord_obj.customer_id, ord_obj.demand, OrderStatus.cancelled.name, ord_obj.planning_id) and refresh(f"Pedido {ord_obj.id} cancelado!"), color="negative").tooltip("Cancelar Pedido")
        else:
            ui.label("Nenhum pedido encontrado.")

def order_map_ui():
    global _order_map_container
    if not _order_map_container:
        return

    _order_map_container.clear()
    orders = get_orders()
    
    # Collect unique customers with valid coordinates from orders
    customers_on_map = {}
    for order in orders:
        if order.customer and order.customer.latitude is not None and order.customer.longitude is not None:
            if order.customer.id not in customers_on_map:
                customers_on_map[order.customer.id] = order.customer

    unique_customers = list(customers_on_map.values())

    if unique_customers:
        lats = [c.latitude for c in unique_customers if c.latitude is not None]
        lons = [c.longitude for c in unique_customers if c.longitude is not None]

        if not lats or not lons: # Fallback if no valid coordinates
            m = folium.Map(location=[-3.7327, -38.5267], zoom_start=12) # Fortaleza
        else:
            m = folium.Map(location=[mean(lats), mean(lons)], zoom_start=11)
            if len(lats) > 1 : # Avoid error with single point for fit_bounds
                 m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])

            for cust in unique_customers:
                folium.Marker(
                    location=[cust.latitude, cust.longitude],
                    popup=f"Cliente: {cust.name}<br>ID: {cust.id}",
                    icon=folium.Icon(color="blue" if cust.active else "gray")
                ).add_to(m)
    else:
        # Mapa de fallback em Fortaleza CE se não houver clientes com pedidos
        m = folium.Map(location=[-3.7327, -38.5267], zoom_start=12)

    with _order_map_container, ui.card().classes("w-full h-full"):
        ui.html(m._repr_html_()).classes("w-full h-full")

def order_page(container):
    global _order_list_container, _order_map_container
    container.clear()
    with container:
        _order_list_container = ui.column().classes("w-1/2 h-full p-2") # Adjusted width
        order_list_ui()
        _order_map_container = ui.column().classes("w-1/2 h-full p-2") # Adjusted width
        order_map_ui()

def refresh(msg: str = "", color: str = "positive"):
    order_list_ui()
    order_map_ui()
    if msg:
        ui.notify(msg, color=color)