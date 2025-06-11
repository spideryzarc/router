"""
Gerenciamento de planejamentos: cadastro, edição, lista e detalhes.
"""
from nicegui import ui
from backend.controler import (
    get_plannings,
    add_planning,
    update_planning,
    get_depots,
)
from backend.model import PlanningStatus
from datetime import datetime

_planning_list_container = None # type: ignore

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
        ui.label("Adicionar Novo Planejamento").classes("text-h6")

        active_depots = get_depots(active_only=True)
        depot_options = {d.id: d.name for d in active_depots}
        if not depot_options:
            ui.label("Nenhum depósito ativo encontrado. Crie e ative um depósito primeiro.")
            with ui.card_actions().classes("w-full justify-end"):
                 ui.button("Fechar", on_click=dialog.close, color="negative")
            dialog.open()
            return

        depot_in = ui.select(label="Depósito", options=depot_options)
        
        ui.label("Deadline (Opcional)")
        with ui.row():
            deadline_date_in = ui.date(value=None).props('clearable')
            deadline_time_in = ui.time(value=None).props('clearable')

        def save():
            if not depot_in.value:
                ui.notify("Depósito é obrigatório.", color="negative"); return

            deadline_dt = parse_datetime_from_input(deadline_date_in.value, deadline_time_in.value)

            add_planning(depot_id=depot_in.value, deadline=deadline_dt)
            refresh("Planejamento adicionado!")
            dialog.close()

        with ui.card_actions().classes("w-full justify-end"):
            ui.button("Salvar", on_click=save, color="primary", icon="save")
            ui.button("Cancelar", on_click=dialog.close, color="negative", icon="close")
    dialog.open()

def edit_planning_dialog(planning_obj):
    with ui.dialog() as dialog, ui.card():
        ui.label("Editar Planejamento").classes("text-h6")

        all_depots = get_depots(active_only=False) # Mostrar todos para contexto, incluindo o atual se inativo
        depot_options = {d.id: d.name for d in all_depots}
        depot_in = ui.select(label="Depósito", options=depot_options, value=planning_obj.depot_id)

        ui.label("Deadline (Opcional)")
        initial_date_str, initial_time_str = format_datetime_for_input(planning_obj.deadline)
        with ui.row(): # ui.date espera YYYY-MM-DD ou None
            deadline_date_in = ui.date(value=initial_date_str).props('clearable')
            deadline_time_in = ui.time(value=initial_time_str).props('clearable')
        
        status_options = {s.name: s.value for s in PlanningStatus}
        status_in = ui.select(label="Status", options=status_options, value=planning_obj.status.name)

        def save():
            if not (depot_in.value and status_in.value):
                ui.notify("Depósito e Status são obrigatórios.", color="negative"); return
            
            deadline_dt = parse_datetime_from_input(deadline_date_in.value, deadline_time_in.value)

            update_planning(
                planning_id=planning_obj.id,
                depot_id=depot_in.value,
                deadline=deadline_dt,
                status_str=status_in.value
            )
            refresh("Planejamento atualizado!")
            dialog.close()

        with ui.card_actions().classes("w-full justify-end"):
            ui.button("Salvar", on_click=save, color="primary", icon="save")
            ui.button("Cancelar", on_click=dialog.close, color="negative", icon="close")
    dialog.open()

def planning_list_ui():
    _planning_list_container.clear()
    with _planning_list_container, ui.card().classes("w-full h-full overflow-auto"):
        with ui.row().classes("items-center justify-between w-full"):
            ui.label("Planejamentos").classes("text-h5")
            ui.icon("event_note").classes("text-h4")
        ui.button("Adicionar Planejamento", on_click=add_planning_dialog,
                    color="primary", icon="add").classes("mb-4")

        plannings = get_plannings(active_only=False) # Mostrar todos para gerenciamento
        if plannings:
            ui.separator()
            for p in plannings:
                header_text = f"ID: {p.id} - Depósito: {p.depot.name if p.depot else 'N/A'} - Status: {p.status.value}"
                with ui.expansion(header_text, icon="event").classes('w-full mb-2'):
                    with ui.card_section():
                        ui.label(f"Deadline: {p.deadline.strftime('%d/%m/%Y %H:%M') if p.deadline else 'Não definida'}").classes("text-sm")
                        ui.label(f"Criado em: {p.created_at.strftime('%d/%m/%Y %H:%M') if p.created_at else 'N/A'}").classes("text-sm")
                        ui.label(f"Pedidos Associados: {len(p.orders)}").classes("text-sm")
                        ui.label(f"Rotas Geradas: {len(p.routes)}").classes("text-sm")
                    ui.button(icon="edit", on_click=lambda pl_obj=p: edit_planning_dialog(pl_obj), color="primary").props("flat dense").tooltip("Editar Planejamento")
        else:
            ui.label("Nenhum planejamento encontrado.")

def planning_page(container):
    global _planning_list_container
    container.clear()
    with container:
        _planning_list_container = ui.column().classes("w-full h-full p-4")
        planning_list_ui()

def refresh(msg: str = "", color: str = "positive"):
    planning_list_ui()
    if msg:
        ui.notify(msg, color=color)