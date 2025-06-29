"""
Gerenciamento de veículos: cadastro, edição, ativar/desativar, lista.
"""
from nicegui import ui
from backend.controler import get_vehicles, get_depots, add_vehicle, update_vehicle, toggle_vehicle_active

ui.state.show_disabled_vehicles = False

def add_vehicle_dialog():
    with ui.dialog() as dialog, ui.card():
        ui.label("Adicionar Novo Veículo").classes("text-h6")
        model_in = ui.input(label="Modelo")
        plate_in = ui.input(label="Placa")
        capacity_in = ui.input(label="Capacidade").props('type=number')
        cost_in = ui.input(label="Custo por km").props('type=number')
        depot_options = {d.id: d.name for d in get_depots() if d.active}
        depot_in = ui.select(label="Depósito", options=depot_options)
        def save():
            try:
                cap = int(capacity_in.value); cost = float(cost_in.value)
            except:
                ui.notify("Capacidade/Custo inválidos", color="negative"); return
            if not (model_in.value.strip() and plate_in.value.strip() and depot_in.value):
                ui.notify("Preencha todos os campos.", color="negative"); return
            add_vehicle(model_in.value.strip(), plate_in.value.strip(), cap, cost, depot_in.value)
            refresh("Veículo adicionado!")
            dialog.close()
        with ui.card_actions().classes("w-full justify-end"):
            ui.button("Salvar", on_click=save, color="primary", icon="save")
            ui.button("Cancelar", on_click=dialog.close, color="negative", icon="close")
    dialog.open()

def edit_vehicle_dialog(v):
    with ui.dialog() as dialog, ui.card():
        ui.label("Editar Veículo").classes("text-h6")
        model_in = ui.input(label="Modelo", value=v.model)
        plate_in = ui.input(label="Placa", value=v.plate)
        capacity_in = ui.input(label="Capacidade", value=v.capacity).props('type=number')
        cost_in = ui.input(label="Custo por km", value=v.cost_per_km).props('type=number')
        depot_options = {d.id: d.name for d in get_depots()}
        depot_in = ui.select(label="Depósito", options=depot_options, value=v.depot_id)
        def save():
            try:
                cap = int(capacity_in.value); cost = float(cost_in.value)
            except:
                ui.notify("Capacidade/Custo inválidos", color="negative"); return
            if not (model_in.value.strip() and plate_in.value.strip() and depot_in.value):
                ui.notify("Preencha todos os campos.", color="negative"); return
            update_vehicle(v.id, model_in.value.strip(), plate_in.value.strip(), cap, cost, depot_in.value)
            refresh("Veículo atualizado!")
            dialog.close()
        with ui.card_actions().classes("w-full justify-end"):
            ui.button("Salvar", on_click=save, color="primary", icon="save")
            ui.button("Cancelar", on_click=dialog.close, color="negative", icon="close")
    dialog.open()

def deactivate_vehicle(v):
    with ui.dialog() as dlg, ui.card():
        ui.label("Desativar veículo?").classes("text-h5")
        ui.label(f"({v.id}) {v.plate}").classes("text-h6")
        def confirm():
            toggle_vehicle_active(v.id, False)
            refresh("Veículo desativado")
            dlg.close()
        with ui.card_actions().classes("w-full justify-end"):
            ui.button("Sim", on_click=confirm, color="dark", icon="visibility_off")
            ui.button("Não", on_click=dlg.close, icon="visibility", color="positive")
    dlg.open()

def activate_vehicle(v):
    with ui.dialog() as dlg, ui.card():
        ui.label("Ativar veículo?").classes("text-h5")
        ui.label(f"({v.id}) {v.plate}").classes("text-h6")
        def confirm():
            toggle_vehicle_active(v.id, True)
            refresh("Veículo ativado!")
            dlg.close()
        with ui.card_actions().classes("w-full justify-end"):
            ui.button("Sim", on_click=confirm, color="positive", icon="visibility")
            ui.button("Não", on_click=dlg.close, icon="visibility_off", color="dark")
    dlg.open()

def vehicle_list():
    _veh_list.clear()
    with _veh_list:
        with ui.card().classes("w-1/3"):
            with ui.row().classes("items-center justify-between"):
                ui.label("Veículos Cadastrados").classes("text-h5")
                ui.icon("local_shipping").classes("text-h4")
            with ui.row():
                ui.button("Adicionar", on_click=add_vehicle_dialog,
                        color="primary", icon="add").classes("mb-4")
                ui.switch("Mostrar desativados",
                            value=ui.state.show_disabled_vehicles,
                            on_change=lambda e: toggle_show_disabled(e.value))
        with ui.column().classes("w-2/3"), ui.scroll_area().classes("border h-[500px]"):
            # vehicles = get_vehicles()
            if vehicles:= get_vehicles():
                for v in vehicles:
                    # Card para cada veículo
                    with ui.card().classes('w-full max-w-2xl mb-4 mx-auto') as vehicle_card: # Adicionada mx-auto para centralizar
                        if not v.active:
                            vehicle_card.bind_visibility(ui.state, 'show_disabled_vehicles')

                        with ui.row().classes("items-center justify-between w-full"):
                            ui.label(f"Placa: {v.plate}").classes("text-lg font-semibold")
                            ui.badge("Ativo" if v.active else "Inativo",
                                    color="positive" if v.active else "dark").classes("ml-auto")

                        ui.label(f"Modelo: {v.model}")
                        ui.label(f"Capacidade: {v.capacity} unidades")
                        ui.label(f"Custo por km: R$ {v.cost_per_km:.2f}")
                        ui.label(f"Depósito: {v.depot.name if v.depot else 'N/A'}")
                        ui.label(f"ID: {v.id}").classes("text-xs text-gray-500")

                        with ui.card_actions().classes("w-full justify-end"):
                            ui.button(icon="edit",
                                    on_click=lambda x=v: edit_vehicle_dialog(x),
                                    color="primary").props("flat dense").tooltip("Editar Veículo")
                            if v.active:
                                ui.button(icon="visibility_off",  # Ícone mais intuitivo para desativar
                                        on_click=lambda x=v: deactivate_vehicle(x),
                                        color="dark").props("flat dense").tooltip("Desativar Veículo")
                            else:
                                ui.button(icon="visibility",  # Ícone mais intuitivo para ativar
                                        on_click=lambda x=v: activate_vehicle(x),
                                        color="positive").props("flat dense").tooltip("Ativar Veículo")
            else:
                ui.label("Nenhum veículo encontrado.")

def toggle_show_disabled(is_checked: bool):
    ui.state.show_disabled_vehicles = is_checked
    refresh()

def vehicle_page(container):
    global _veh_list
    # container.clear()
    # with container:
    #     # _veh_list = ui.row().classes("w-full h-full justify-center")
    #     vehicle_list()
    _veh_list = container
    vehicle_list()


def refresh(msg: str = "", color: str = "positive"):
    vehicle_list()
    if msg:
        ui.notify(msg, color=color)
