"""
Definição das páginas e componentes de gerenciamento de depósitos:
- Diálogos: adicionar, editar, ativar e desativar
- Listagem e mapa de depósitos
- Função principal depot_page para renderizar o layout
"""

from nicegui import ui
from backend.controler import (
    get_depots,
    add_depot,
    update_depot,
    toggle_depot_active,
)
import folium
from osmnx import geocode
from statistics import mean

# Estado global para controlar a exibição de depósitos desativados
ui.state.show_disabled_depots = False


def add_depot_dialog():
    """
    Exibe um diálogo para adicionar um novo depósito.
    Coleta nome e endereço, valida campos e comunica com o backend.
    """
    with ui.dialog() as dialog, ui.card():
        ui.label("Adicionar Novo Depósito").classes("text-h6")
        name_input = ui.input(label="Nome")

        with ui.row().classes("items-center w-full"):
            address_input = ui.input(label="Endereço").classes("flex-grow")
            # O botão será conectado à função get_coords definida abaixo
            geocode_button = ui.button(icon="search").classes("ml-2")

        lat_input = ui.input(label="Latitude")
        lon_input = ui.input(label="Longitude")

        def get_coords_from_address():
            address_value = address_input.value.strip()
            if not address_value:
                ui.notify("Preencha o endereço primeiro.", color="negative")
                return

            with ui.dialog() as wait_dialog, ui.card():
                ui.label("Obtendo coordenadas...").classes("text-h6")
                wait_dialog.open()
            try:
                lat, lon = geocode(address_value)
                if lat is not None and lon is not None:
                    lat_input.value = str(lat)
                    lon_input.value = str(lon)
                    ui.notify("Coordenadas obtidas com sucesso!", color="positive")
                else:
                    ui.notify("Endereço inválido ou não encontrado.", color="negative")
            except Exception:
                ui.notify("Erro ao buscar coordenadas. Verifique o endereço ou tente novamente.", color="negative")
            finally:
                wait_dialog.close()

        geocode_button.on_click(get_coords_from_address)

        def save_and_close():
            name = name_input.value.strip()
            address = address_input.value.strip()
            lat_str = lat_input.value.strip()
            lon_str = lon_input.value.strip()

            if not name or not address:
                ui.notify("Preencha nome e endereço.", color="negative")
                return

            lat, lon = None, None
            if lat_str and lon_str:
                try:
                    lat = float(lat_str)
                    lon = float(lon_str)
                except ValueError:
                    ui.notify("Latitude/Longitude inválidas.", color="negative")
                    return
            elif lat_str or lon_str: # Apenas um preenchido
                ui.notify("Se fornecer coordenadas, preencha Latitude e Longitude.", color="negative")
                return

            add_depot(name, address, latitude=lat, longitude=lon) # Assume backend.add_depot aceita lat/lon
            refresh("Depósito adicionado com sucesso!")
            dialog.close()

        with ui.card_actions().classes("w-full justify-end"):
            ui.button("Salvar", on_click=save_and_close,
                      color="primary", icon="save")
            ui.button("Cancelar", on_click=dialog.close,
                      color="negative", icon="close")

    dialog.open()


def edit_depot_dialog(depot):
    """
    Exibe um diálogo para editar um depósito existente.
    Permite alterar nome, endereço e coordenadas manualmente.
    """
    with ui.dialog() as edit_dialog, ui.card():
        ui.label("Editar Depósito").classes("text-h6")
        name_input = ui.input(label="Nome", value=depot.name)
        address_input = ui.input(label="Endereço", value=depot.address)
        lat_input = ui.input(label="Latitude",
                             value=depot.latitude or "")
        lon_input = ui.input(label="Longitude",
                             value=depot.longitude or "")

        def save_edit_depot():
            new_name = name_input.value.strip()
            new_address = address_input.value.strip()
            if not new_name or not new_address:
                ui.notify("Preencha todos os campos.", color="negative")
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

        with ui.card_actions().classes("w-full justify-end"):
            ui.button("Salvar", on_click=save_edit_depot,
                      color="primary", icon="save")
            ui.button("Cancelar", on_click=edit_dialog.close,
                      color="negative", icon="close")

    edit_dialog.open()


def deactivate_depot(depot):
    """
    Exibe confirmação para desativar um depósito.
    """
    with ui.dialog() as confirm_dialog, ui.card():
        ui.label("Deseja desativar o depósito?").classes("text-h5")
        ui.label(f"({depot.id}) {depot.name}").classes("text-h6")

        def confirm_disable():
            toggle_depot_active(depot.id, False)
            refresh("Depósito desativado")
            confirm_dialog.close()

        with ui.card_actions().classes("w-full justify-end"):
            ui.button("Sim", on_click=confirm_disable,
                      color="warning", icon="delete")
            ui.button("Não", on_click=confirm_dialog.close,
                      icon="close")

    confirm_dialog.open()


def activate_depot(depot):
    """
    Exibe confirmação para ativar um depósito.
    """
    with ui.dialog() as confirm_dialog, ui.card():
        ui.label("Deseja ativar o depósito?").classes("text-h5")
        ui.label(f"({depot.id}) {depot.name}").classes("text-h6")

        def confirm_activate():
            toggle_depot_active(depot.id, True)
            refresh("Depósito ativado com sucesso!")
            confirm_dialog.close()

        with ui.card_actions().classes("w-full justify-end"):
            ui.button("Sim", on_click=confirm_activate,
                      color="success", icon="check")
            ui.button("Não", on_click=confirm_dialog.close,
                      icon="close")

    confirm_dialog.open()


def depot_list():
    """
    Renderiza cartão com a lista de depósitos:
    - Botão para adicionar novo depósito
    - Toggle para mostrar depósitos desativados
    - Botões de editar, ativar/desativar em cada item
    """
    _depots_list.clear()
    with _depots_list, ui.card().classes("w-full h-full overflow-auto"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Depósitos Cadastrados").classes("text-h5")
            ui.icon("warehouse").classes("text-h5 ml-auto")
        with ui.row().classes("w-full justify-between"):
            ui.button("Adicionar", on_click=add_depot_dialog,
                  color="primary", icon="add").classes("mb-4")
            # Checkbox para exibir depósitos desativados
            sw = ui.switch("Mostrar desativados",
                        value=ui.state.show_disabled_depots,
                        on_change=lambda e: toggle_show_disabled(e.value))
        depositos = get_depots()
        if depositos:            
            ui.separator()                
            for depot in depositos:
                with ui.column().classes("w-full"):
                    with ui.row().classes("items-center justify-between w-full") as row:
                        with ui.label(depot.name).classes("body-text"), ui.tooltip():
                            ui.label(f"id: {depot.id} - {depot.name}").classes("body-text")
                            ui.label(f"coords: ({depot.latitude}, {depot.longitude})").classes("body-text")
                            ui.label(f"address: {depot.address}").classes("body-text")
                        with ui.row().classes("items-center gap-2"):
                            ui.button(icon="edit",
                                        on_click=lambda d=depot: edit_depot_dialog(d),
                                        color="primary")
                            if depot.active:
                                ui.button(icon="delete",
                                            on_click=lambda d=depot: deactivate_depot(d),
                                            color="warning")
                            else:
                                ui.button(icon="check",
                                            on_click=lambda d=depot: activate_depot(d),
                                            color="success")
                    if not depot.active:
                        row.bind_visibility(sw, "value")
        else:
            ui.label("Nenhum depósito encontrado.")


def toggle_show_disabled(is_checked: bool):
    """
    Atualiza estado de exibição de depósitos desativados e recarrega a lista e o mapa.
    """
    ui.state.show_disabled_depots = is_checked
    depot_map()


def depot_map():
    """
    Renderiza cartão com mapa (Folium) dos depósitos ativos ou desativados conforme o estado.
    """
    depositos = get_depots()
    if depositos:
        lats = [d.latitude for d in depositos if d.latitude]
        lons = [d.longitude for d in depositos if d.longitude]
        # Mapa centralizado na média das coordenadas
        m = folium.Map(location=[mean(lats), mean(lons)],
                        zoom_start=11.5)
        if len(depositos) > 1:
            m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])
        for d in depositos:
            if d.latitude and d.longitude and (d.active or ui.state.show_disabled_depots):
                folium.Marker(
                    location=[d.latitude, d.longitude],
                    popup=f"({d.id}) {d.name}<br>{d.address}",
                    icon=folium.Icon(color="blue" if d.active else "gray"),
                ).add_to(m)
    else:
        # Mapa de fallback em Fortaleza CE
        m = folium.Map(location=[-3.7327, -38.5267], zoom_start=12)

    # Exibe o HTML gerado pelo Folium
    _depots_map.clear()
    with _depots_map:
        ui.html(m._repr_html_()).classes("w-full h-full")


def depot_page(outter):
    """
    Monta o layout de duas colunas: lista (1/3) e mapa (2/3) de depósitos.
    Deve ser chamado dentro de um container NiceGUI existente.
    """
    global _depots_list, _depots_map

    outter.clear()
    with outter:
        _depots_list = ui.column().classes("w-1/3 h-full")
        depot_list()
        _depots_map = ui.column().classes("w-2/3 h-full")
        depot_map()


def refresh(message: str = "", color: str = "positive"):
    """
    Recarrega lista e mapa de depósitos.
    Se 'message' for fornecida, exibe notificação.
    """
    depot_list()
    depot_map()
    if message:
        ui.notify(message, color=color)
