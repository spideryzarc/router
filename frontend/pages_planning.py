"""
Gerenciamento de planejamentos: cadastro, edição, lista e detalhes.
"""
from statistics import mean
import folium
from nicegui import ui
from backend.controler import (
    get_plannings,
    add_planning,
    update_planning,
    get_depots,
    cancel_planning,
    restore_order,
    restore_planning,
    get_orders,
    assign_orders_to_planning,
    remove_order_from_planning
)
from backend.model import PlanningStatus
from datetime import datetime

_planning_list = None  # type: ignore
_planning_map = None  # type: ignore

# Inicializa o estado global para o filtro de status
if not hasattr(ui.state, 'planning_status_filter'):
    ui.state.planning_status_filter = 'all'  # Valor padrão

def format_datetime_for_input(dt_obj: datetime | None) -> tuple[str | None, str | None]:
    """Converte datetime para strings de data (YYYY-MM-DD) e hora (HH:MM) para inputs."""
    if dt_obj:
        return dt_obj.strftime('%Y-%m-%d'), dt_obj.strftime('%H:%M')
    return None, None

def parse_datetime_from_input(date_str: str | None, time_str: str | None) -> datetime | None:
    """Converte strings de data e hora dos inputs para um objeto datetime."""
    if date_str and time_str:
        try:
            # ui.date retorna YYYY/MM/DD, ui.time retorna HH:MM
            # Precisamos converter YYYY/MM/DD para YYYY-MM-DD para strptime
            dt_str_formatted = date_str.replace('/', '-')
            dt = datetime.strptime(f"{dt_str_formatted} {time_str}", '%Y-%m-%d %H:%M')
            return dt
        except ValueError:
            ui.notify("Formato de data ou hora inválido.", color="negative")
            return None
    elif date_str and not time_str: # Apenas data, assume meia-noite
        try:
            dt_str_formatted = date_str.replace('/', '-')
            dt = datetime.strptime(dt_str_formatted, '%Y-%m-%d')
            return dt
        except ValueError:
            ui.notify("Formato de data inválido.", color="negative")
            return None
    return None


def add_planning_dialog():
    with ui.dialog() as dialog, ui.card():
        ui.label("Adicionar Novo Planejamento").classes("text-h6 mb-2")
        
        # Seleciona apenas depósitos ativos
        active_depots = get_depots(active_only=True)
        depot_options = {d.id: d.name for d in active_depots}
        if not depot_options:
            ui.label("Nenhum depósito ativo encontrado. Crie e ative um depósito primeiro.").classes("mb-2")
            with ui.card_actions().classes("w-full justify-end"):
                ui.button("Fechar", on_click=dialog.close, color="negative", icon="close")
            dialog.open()
            return
        
        depot_in = ui.select(label="Depósito", options=depot_options).classes("w-full mb-2")
        
        # Deadline opcional usando os pickers compactos
        ui.label("Deadline (Opcional)").classes("mb-1")
        with ui.row().classes("mb-2"):
            deadline_date_in = compact_date_picker("Data", None).classes("flex-grow dense")
            deadline_time_in = compact_time_picker("Hora", None).classes("ml-2 flex-grow dense")
        
        def save():
            if not depot_in.value:
                ui.notify("Depósito é obrigatório.", color="negative")
                return
            
            deadline_dt = parse_datetime_from_input(deadline_date_in.value, deadline_time_in.value)
            add_planning(depot_id=depot_in.value, deadline=deadline_dt)
            refresh("Planejamento adicionado!")
            dialog.close()
        
        with ui.card_actions().classes("w-full justify-end"):
            ui.button("Salvar", on_click=save, color="primary", icon="save")
            ui.button("Cancelar", on_click=dialog.close, color="negative", icon="close")
    dialog.open()

# Funções auxiliares para criar pickers compactos
def compact_date_picker(label: str, value: str | None = None):
    with ui.input(label, value=value) as date_input:
        with ui.menu().props('no-parent-event') as menu:
            with ui.date().bind_value(date_input):
                with ui.row().classes('justify-end'):
                    ui.button('Close', on_click=menu.close).props('flat')
        with date_input.add_slot('append'):
            ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
    return date_input

def compact_time_picker(label: str, value: str | None = None):
    with ui.input(label, value=value) as time_input:
        with ui.menu().props('no-parent-event') as menu:
            with ui.time().bind_value(time_input):
                with ui.row().classes('justify-end'):
                    ui.button('Close', on_click=menu.close).props('flat')
        with time_input.add_slot('append'):
            ui.icon('access_time').on('click', menu.open).classes('cursor-pointer')
    return time_input

def edit_planning_dialog(planning_obj):
    with ui.dialog() as dialog, ui.card():
        # Exibe o ID do planejamento no cabeçalho
        ui.label(f"Editar Planejamento - ID: {planning_obj.id}").classes("text-h6 mb-2")
        
        # Seleção de Depósito (todos, inclusive inativos, para contexto)
        all_depots = get_depots(active_only=False)
        depot_options = {d.id: d.name for d in all_depots}
        depot_in = ui.select(label="Depósito", options=depot_options, value=planning_obj.depot_id).classes("w-full mb-2")
        
        # Exibição do Status Atual (não editável)
        ui.label(f"Status Atual: {planning_obj.status.value.capitalize()}").classes("mb-2")
        
        # Campo para Deadline (Opcional) usando os pickers compactos
        ui.label("Deadline (Opcional)").classes("mb-1")
        initial_date_str, initial_time_str = format_datetime_for_input(planning_obj.deadline)
        with ui.row().classes("mb-2"):
            deadline_date_in = compact_date_picker("Data", initial_date_str).classes("flex-grow dense")
            deadline_time_in = compact_time_picker("Hora", initial_time_str).classes("ml-2 flex-grow dense")
        
        def save():
            if not depot_in.value:
                ui.notify("Depósito é obrigatório.", color="negative")
                return
            
            # Usa o mesmo status atual, pois não pode ser editado diretamente
            current_status = planning_obj.status.name  
            deadline_dt = parse_datetime_from_input(deadline_date_in.value, deadline_time_in.value)
            update_planning(
                planning_id=planning_obj.id,
                depot_id=depot_in.value,
                deadline=deadline_dt,
                status_str=current_status
            )
            refresh("Planejamento atualizado!")
            dialog.close()
        
        with ui.card_actions().classes("w-full justify-end"):
            ui.button("Salvar", on_click=save, color="primary", icon="save")
            ui.button("Cancelar", on_click=dialog.close, color="negative", icon="close")
    dialog.open()

def select_orders_for_planning_dialog(planning_obj):
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Selecionar Pedidos para Planejamento - ID: {planning_obj.id}").classes("text-h6 mb-2")
        
        # Recupera apenas os pedidos com status 'pending' que não estão associados a nenhum planejamento
        eligible_orders = [o for o in get_orders(status_filter='pending') if o.planning_id is None]
        if not eligible_orders:
            ui.label("Nenhum pedido pendente disponível.").classes("mb-2")
        else:
            # Cria um dicionário com os pedidos elegíveis para seleção
            order_options = {o.id: f"ID: {o.id} - Cliente: {o.customer.name} - Demanda: {o.demand}" for o in eligible_orders}
            # Permite seleção múltipla
            selected_orders = ui.select(label="Pedidos Pendentes", options=order_options, multiple=True).classes("w-full mb-2")
        
        def save():
            if not eligible_orders or not selected_orders.value:
                ui.notify("Selecione pelo menos um pedido.", color="negative")
                return
            # Tenta atribuir os pedidos selecionados ao planejamento
            from backend.controler import assign_orders_to_planning  # Certifique-se de que esta função foi adicionada
            if assign_orders_to_planning(planning_obj.id, selected_orders.value):
                refresh(f"Pedidos adicionados ao Planejamento {planning_obj.id}!")
            else:
                ui.notify("Nenhum pedido foi atribuído. Verifique se os pedidos selecionados estão elegíveis.", color="negative")
            dialog.close()
        
        with ui.card_actions().classes("w-full justify-end"):
            ui.button("Salvar", on_click=save, color="primary", icon="save")
            ui.button("Cancelar", on_click=dialog.close, color="negative", icon="close")
    dialog.open()

def route_planning(planning_obj):
    """
    Atualiza o status do planejamento para 'optimizing' e
    exibe uma notificação informando que a integração com o roteirizador está pendente.
    """
    # TODO: Integrar com o roteirizador real
    update_planning(
        planning_id=planning_obj.id,
        depot_id=planning_obj.depot_id,
        deadline=planning_obj.deadline,
        status_str="optimizing"
    )
    ui.notify(f"Planejamento {planning_obj.id} roteirizado! (Roteirizador: TODO)", color="info")
    refresh(f"Planejamento {planning_obj.id} roteirizado!")

def abort_planning(planning_obj):
    """
    Aborta o planejamento que está em otimização, revertendo seu status para 'pending'.
    TODO: Integrar a chamada real ao abortar o roteirizador.
    """
    update_planning(
        planning_id=planning_obj.id,
        depot_id=planning_obj.depot_id,
        deadline=planning_obj.deadline,
        status_str="pending"
    )
    ui.notify(f"Planejamento {planning_obj.id} abortado! (Roteirizador: TODO)", color="info")
    refresh(f"Planejamento {planning_obj.id} abortado!")

def planning_list():
    _planning_list.clear()
    with _planning_list:
        with ui.card().classes("w-full"):
            with ui.row().classes("items-center justify-between w-full"):
                ui.label("Planejamentos").classes("text-h5")
                ui.icon("event_note").classes("text-h4")
            with ui.row().classes("w-full items-center justify-between"):
                ui.button("Adicionar Planejamento", on_click=add_planning_dialog,
                          color="primary", icon="add")
    
                # Filtro de status
                status_options = {'all': 'Todos'}
                status_options.update({s.name: s.value.capitalize() for s in PlanningStatus})
    
                def handle_filter_change(e):
                    ui.state.planning_status_filter = e.value
                    refresh()
    
                ui.select(label="Filtrar por Status",
                          options=status_options,
                          value=ui.state.planning_status_filter,
                          on_change=handle_filter_change).classes("w-32")
    
        with ui.scroll_area().classes("h-[calc(100vh-250px)] overflow-y-auto"):
            status_map = {
                PlanningStatus.pending: ("Pendente", "orange"),
                PlanningStatus.optimizing: ("Otimizando", "info"),
                PlanningStatus.ready: ("Pronto", "positive"),
                PlanningStatus.executed: ("Executado", "green"),
                PlanningStatus.cancelled: ("Cancelado", "negative"),
            }
            if plannings := get_plannings(status_filter=[ui.state.planning_status_filter] if ui.state.planning_status_filter != 'all' else None):
                for p in plannings:
                    with ui.card().classes("w-full mb-2"):
                        with ui.row().classes("w-full justify-between"):
                            with ui.column().classes("items-end"):
                                if p.status == PlanningStatus.optimizing:
                                    # Em otimização, não permite edição, remoção ou adição de pedidos; exibe apenas "Abortar"
                                    ui.button(
                                        icon="stop",
                                        on_click=lambda pl_obj=p: abort_planning(pl_obj),
                                        color="warning"
                                    ).tooltip("Abortar Planejamento").props("flat dense")
                                else:
                                    # Para status pendente ou pronto, permitir edição, cancelamento, adição de pedidos e roteirizar (se pendente)
                                    if p.status in [PlanningStatus.pending, PlanningStatus.ready]:
                                        ui.button(
                                            icon="edit",
                                            on_click=lambda pl_obj=p: edit_planning_dialog(pl_obj),
                                            color="primary"
                                        ).tooltip("Editar Planejamento").props("flat dense")
                                        ui.button(
                                            icon="cancel",
                                            on_click=lambda pl_obj=p: cancel_planning(pl_obj.id) and refresh(f"Planejamento {pl_obj.id} cancelado!"),
                                            color="negative"
                                        ).tooltip("Cancelar Planejamento").props("flat dense")
                                        ui.button(
                                            icon="playlist_add",
                                            on_click=lambda pl_obj=p: select_orders_for_planning_dialog(pl_obj),
                                            color="primary"
                                        ).tooltip("Selecionar Pedidos").props("flat dense")
                                        if p.status == PlanningStatus.pending:
                                            ui.button(
                                                icon="directions",
                                                on_click=lambda pl_obj=p: route_planning(pl_obj),
                                                color="info"
                                            ).tooltip("Roteirizar Planejamento").props("flat dense")
                                    elif p.status == PlanningStatus.cancelled:
                                        ui.button(
                                            icon="restore",
                                            on_click=lambda pl_obj=p: restore_planning(pl_obj.id) and refresh(f"Planejamento {pl_obj.id} restaurado!"),
                                            color="positive"
                                        ).tooltip("Restaurar Planejamento").props("flat dense")
    
                            with ui.column().classes("gap-0"):
                                ui.label(f"Depósito: {p.depot.name if p.depot else 'N/A'}").classes("font-semibold text-base")
                                with ui.row().classes("text-sm text-gray-600 items-center gap-2"):
                                    ui.label(f"ID: {p.id}")
                                    ui.separator().props("vertical")
                                    ui.label(f"Status: {p.status.value.capitalize()}")
                                    ui.separator().props("vertical")
                                    ui.label(f"Deadline: {p.deadline.strftime('%d/%m/%Y %H:%M') if p.deadline else 'Não definida'}")
                                with ui.row().classes("w-full"):
                                    ui.label(f"Criado em: {p.created_at.strftime('%d/%m/%Y %H:%M') if p.created_at else 'N/A'}").classes("text-xs text-gray-500 mt-1")
                                    status_text, status_color = status_map.get(p.status, ("Desconhecido", "grey"))
                                    ui.space().props("vertical")
                                    ui.badge(status_text, color=status_color)
                                if hasattr(p, "orders") and p.orders:
                                    ui.label("Pedidos associados:").classes("mt-2 text-sm")
                                    for order in p.orders:
                                        with ui.row().classes("items-center gap-2"):
                                            ui.label(f"ID: {order.id} - Cliente: {order.customer.name} - Demanda: {order.demand}").classes("text-xs")
                                            # Exibe o botão de remoção somente se o planejamento não estiver em otimização
                                            if p.status != PlanningStatus.optimizing:
                                                ui.button(
                                                    icon="delete", 
                                                    on_click=lambda o=order, p_id=p.id: remove_order_from_planning(o.id) and refresh(f"Pedido {o.id} removido do Planejamento {p_id}"),
                                                    color="negative"
                                                ).tooltip("Remover Pedido").props("flat dense")
            else:
                ui.label("Nenhum planejamento encontrado.")

def planning_map():
    global _planning_map
    plannings = get_plannings()
    
    # Coleta coordenadas dos depósitos e dos pedidos
    depot_coords = [(p.depot.latitude, p.depot.longitude) for p in plannings 
                    if p.depot and p.depot.latitude and p.depot.longitude]
                    
    orders_coords = []
    for p in plannings:
        if hasattr(p, 'orders') and p.orders:
            for order in p.orders:
                if order.customer and getattr(order.customer, 'latitude', None) and getattr(order.customer, 'longitude', None):
                    orders_coords.append((order.customer.latitude, order.customer.longitude))
    
    all_coords = depot_coords + orders_coords
    if all_coords:
        lats = [c[0] for c in all_coords]
        lons = [c[1] for c in all_coords]
        center = [mean(lats), mean(lons)]
        m = folium.Map(location=center, zoom_start=11)
        if len(all_coords) > 1:
            m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])
    else:
        m = folium.Map(location=[-3.7327, -38.5267], zoom_start=12)
    
    # Marcadores dos depósitos
    for p in plannings:
        if p.depot and p.depot.latitude and p.depot.longitude:
            folium.Marker(
                location=[p.depot.latitude, p.depot.longitude],
                popup=f"Planejamento {p.id}<br>Depósito: {p.depot.name}",
                icon=folium.Icon(color="blue", icon="warehouse", prefix='fa')
            ).add_to(m)
    
    # Marcadores dos pedidos (em vermelho) e linhas conectando ao depósito
    for p in plannings:
        if hasattr(p, 'orders') and p.orders and p.depot and p.depot.latitude and p.depot.longitude:
            for order in p.orders:
                if order.customer and getattr(order.customer, 'latitude', None) and getattr(order.customer, 'longitude', None):
                    folium.Marker(
                        location=[order.customer.latitude, order.customer.longitude],
                        popup=f"Pedido {order.id}<br>Cliente: {order.customer.name}",
                        icon=folium.Icon(color="red", icon="shopping-cart")
                    ).add_to(m)
                    # Linha ligando o depósito ao pedido
                    folium.PolyLine(
                        locations=[
                            [p.depot.latitude, p.depot.longitude],
                            [order.customer.latitude, order.customer.longitude]
                        ],
                        color="black",
                        weight=2,
                        dash_array="5, 5"
                    ).add_to(m)
    
    _planning_map.clear()
    with _planning_map:
        ui.html(m._repr_html_()).classes("w-full h-full")

def planning_page(container):
    global _planning_list, _planning_map
    container.clear()
    with container:
        _planning_list = ui.column().classes("w-1/3 h-full p-4")
        planning_list()
        _planning_map = ui.column().classes("w-2/3 h-full p-4")
        planning_map()

def refresh(msg: str = "", color: str = "positive"):
    planning_list()
    planning_map()
    if msg:
        ui.notify(msg, color=color)