from nicegui import ui
from backend.controler import *
import folium
from frontend.pages_depots import depot_page


def base_layout():
    main_container = ui.row().classes('w-full h-full no-wrap')  # Cria um container principal que ocupará toda a tela
    with ui.header():
        with ui.button(icon='menu'):
            with ui.menu() as menu:
                ui.menu_item('Depósitos', on_click=lambda: depot_page(main_container))
                ui.menu_item('Menu item 2')
                ui.menu_item('Menu item 3 (keep open)')
                ui.separator()
                ui.menu_item('Close', menu.close)
        ui.label("Laboratório de Matemática Industrial (Roteirizador)").classes("text-h4")

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


