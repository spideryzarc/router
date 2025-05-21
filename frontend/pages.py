from nicegui import ui
from backend.controler import *

def base_layout():
    with ui.header():
        with ui.button(icon='menu'):
            with ui.menu() as menu:
                ui.menu_item('Depósitos', on_click=lambda: ui.navigate.to('/depots'))
                ui.menu_item('Menu item 2')
                ui.menu_item('Menu item 3 (keep open)')
                ui.separator()
                ui.menu_item('Close', menu.close)
        ui.label("Roterizador")

    with ui.footer():
        ui.label("Rodapé do sistema")
        ui.label("Versão 1.0")

@ui.page("/")
def index():
    base_layout()

@ui.page("/sobre")
def about():
    base_layout()
    ui.label("Página sobre")


@ui.page("/depots")
def depots():
    base_layout()
    ui.label("Página de depósitos")
    depots = get_depots()
    if len(depots) > 0:
        with ui.card():            
            for depot in depots:
                with ui.expansion(depot.name):
                    ui.label(f"ID: {depot.id}")
                    ui.label(f"Nome: {depot.name}")
                    ui.label(f"Endereço: {depot.address}")
    else:
        ui.label("Nenhum depósito encontrado.")
    
    with ui.card():
        ui.label("Adicionar Depósito")
        name = ui.input(label="Nome")
        address = ui.input(label="Endereço")
        def add():
            add_depot(name.value, address.value)
            ui.notify("Depósito adicionado com sucesso!")
            ui.navigate.to('/depots')
        submit = ui.button("Adicionar", on_click=add).props('primary')
