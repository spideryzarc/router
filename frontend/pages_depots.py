from nicegui import ui
from backend.controler import (
    get_depots, add_depot, update_depot,
    toggle_depot_active
)
import folium

# estado de exibição dos depósitos 
ui.state.show_disabled_depots = False


def add_depot_dialog():
    with ui.dialog() as dialog, ui.card():
        ui.label("Adicionar Novo Depósito").classes("text-h6")
        name_input = ui.input(label="Nome")
        address_input = ui.input(label="Endereço")

        def save_and_close():
            name = name_input.value.strip()
            address = address_input.value.strip()
            if not name or not address:
                ui.notify("Por favor, preencha todos os campos.", color="negative")
                return
            add_depot(name, address)
            refresh("Depósito adicionado com sucesso!")
            dialog.close()

        with ui.card_actions().classes("w-full justify-end"):
            ui.button("Salvar", on_click=save_and_close, color="primary", icon="save")
            ui.button("Cancelar", on_click=dialog.close, color="negative", icon="close")
    dialog.open()

def edit_depot_dialog(depot):
    with ui.dialog() as edit_dialog, ui.card():
        ui.label("Editar Depósito").classes("text-h6")
        name_input = ui.input(label="Nome", value=depot.name)
        address_input = ui.input(label="Endereço", value=depot.address)
        lat_input = ui.input(label="Latitude", value=depot.latitude if depot.latitude else "")
        lon_input = ui.input(label="Longitude", value=depot.longitude if depot.longitude else "")
        def save_edit_depot():
            new_name = name_input.value.strip()
            new_address = address_input.value.strip()
            
            if not new_name or not new_address:
                ui.notify("Por favor, preencha todos os campos.", color="negative")
                return
            try:
                lat = float(lat_input.value)
                lon = float(lon_input.value)
            except ValueError:
                ui.notify("Latitude/Longitude inválidas", color="negative")
                return
            update_depot(depot.id, new_name, new_address, lat, lon)
            refresh("Depósito atualizado com sucesso!")
            edit_dialog.close()
        with ui.card_actions().classes('w-full justify-end'):
            ui.button("Salvar", on_click=save_edit_depot, color="primary", icon="save")
            ui.button("Cancelar", on_click=edit_dialog.close, color="negative", icon="close")
    edit_dialog.open()


def deactivate_depot(depot):
    with ui.dialog() as confirm_dialog, ui.card():
        ui.label("Deseja desativar o depósito:").classes("text-h5")
        ui.label(f"({depot.id}) {depot.name}").classes("text-h6")

        def confirm_disable():
            toggle_depot_active(depot.id, False)
            refresh("Depósito desativado")
            confirm_dialog.close()
        with ui.card_actions().classes("w-full justify-end"):
            ui.button(
                "Sim",
                on_click=confirm_disable,
                color="warning",
                icon="delete",
            )
            ui.button("Não", on_click=confirm_dialog.close, icon="close")
    confirm_dialog.open()

def activate_depot(depot):
    with ui.dialog() as confirm_dialog, ui.card():
        ui.label("Deseja ativar o depósito:").classes("text-h5")
        ui.label(f"({depot.id}) {depot.name}").classes("text-h6")

        def confirm_activate():
            toggle_depot_active(depot.id, True)
            refresh("Depósito ativado com sucesso!")
            confirm_dialog.close()
        with ui.card_actions().classes("w-full justify-end"):
            ui.button(
                "Sim",
                on_click=confirm_activate,
                color="success",
                icon="check",
            )
            ui.button("Não", on_click=confirm_dialog.close, icon="close")
    confirm_dialog.open()

def depot_list():
    _depots_list.clear()
    with _depots_list, ui.card().classes(
        "w-full h-full overflow-auto"
    ):  # Card ocupa todo o espaço da coluna
        ui.label("Depósitos Cadastrados").classes("text-h5")
        ui.button(
            "Adicionar", on_click=add_depot_dialog, color="primary", icon="add"
        ).classes("mb-4")
        depositos = get_depots()  # Função que retorna os depósitos
        if depositos:
            # Toggle para mostrar depósitos desativados
            def toggle_show_disabled(is_checked):
                ui.state.show_disabled_depots = is_checked
                refresh()

            ui.checkbox(
                "Mostrar depósitos desativados",
                value=ui.state.show_disabled_depots,
                on_change=lambda e: toggle_show_disabled(e.value),
            )
            ui.separator()
            for depot in depositos:
                if depot.active or ui.state.show_disabled_depots:
                    with ui.column().classes("w-full"):
                        with ui.row().classes("items-center justify-between w-full"):
                            ui.label(f"({depot.id}) {depot.name}").classes("text-h6")
                            # ui.label(f"Endereço: {depot.address}")
                            with ui.row().classes("items-center gap-2"):
                                ui.button(
                                    "",
                                    on_click=lambda d=depot: edit_depot_dialog(d),
                                    color="primary",
                                    icon="edit",
                                )
                                if depot.active:
                                    ui.button(
                                        "",
                                        on_click=lambda d=depot: deactivate_depot(d),
                                        color="warning",
                                        icon="delete",
                                    )
                                else:
                                    ui.button(
                                        "",
                                        on_click=lambda d=depot: activate_depot(d),
                                        color="success",
                                        icon="check",
                                    )
        else:
            with ui.column().classes("w-full"):
                ui.label("Nenhum depósito encontrado.")


def depot_map():
    _depots_map.clear()
    with _depots_map, ui.card().classes(
        "w-full h-full"
    ):  # Card ocupa todo o espaço da coluna
        # lista de depósitos para exibir no mapa
        depots = get_depots()
        coords = [
            (depot.latitude, depot.longitude)
            for depot in depots
            if depot.latitude and depot.longitude
        ]
        # Cria o mapa centralizado na média das coordenadas dos depósitos
        if coords:
            avg_lat = sum(lat for lat, lon in coords) / len(coords)
            avg_lon = sum(lon for lat, lon in coords) / len(coords)
            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)
            # Adiciona marcadores para cada depósito
            for depot in depots:
                if depot.active or ui.state.show_disabled_depots:
                    if depot.latitude and depot.longitude:
                        folium.Marker(
                            location=[depot.latitude, depot.longitude],
                            popup=f"({depot.id}) {depot.name}<br>{depot.address}",
                            icon=folium.Icon(color="blue" if depot.active else "gray"),
                        ).add_to(m)
        else:
            # Se não houver depósitos com coordenadas, centraliza em São Paulo
            m = folium.Map(location=[-23.55052, -46.633308], zoom_start=12)
            ui.label(
                "Nenhum depósito com coordenadas disponíveis. Exibindo mapa de São Paulo."
            )

        # # Cria o mapa centralizado em São Paulo
        # m = folium.Map(location=[-23.55052, -46.633308], zoom_start=12)
        # # Exemplo: adiciona um marcador
        # folium.Marker(location=[-23.55052, -46.633308], popup="Centro de São Paulo").add_to(m)
        # Obtém a representação HTML do mapa
        map_html = m._repr_html_()
        # Exibe o mapa na interface, fazendo-o ocupar todo o card
        ui.html(map_html).classes("w-full h-full")


def depot_page(outter):
    global _depots_list, _depots_map
    # clear the container
    outter.clear()
    with outter:
        _depots_list = ui.column().classes("w-1/3 h-full")
        depot_list()
        _depots_map = ui.column().classes("w-2/3 h-full")
        depot_map()



def refresh(message: str="", color: str = "positive"):
    depot_list()
    depot_map()
    if message:
        ui.notify(message, color=color)


