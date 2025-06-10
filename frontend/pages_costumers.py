"""
Gerenciamento de clientes: cadastro, edição, ativar/desativar, lista e mapa.
"""
from nicegui import ui
from backend.controler import (
    get_customers,
    add_customer,
    update_customer,
    toggle_customer_active,
)
import folium

from osmnx import geocode
from statistics import mean


ui.state.show_disabled_customers = False

def add_customer_dialog():
    def get_coords():
        if not address_in.value.strip():
            ui.notify("Preencha o endereço primeiro.", color="negative")
            return
        # show waiting dialog
        with ui.dialog() as wait_dialog:
            ui.label("Obtendo coordenadas...").classes("text-h6")
            wait_dialog.open()
        lat, lon = geocode(address_in.value)
        wait_dialog.close()  # close waiting dialog
        if lat and lon:
            lat_in.value = str(lat)
            lon_in.value = str(lon)
            ui.notify("Coordenadas obtidas com sucesso!", color="positive")
        else:
            ui.notify("Endereço inválido ou não encontrado", color="negative")

    with ui.dialog() as dialog, ui.card():
        ui.label("Adicionar Novo Cliente").classes("text-h6")
        name_in = ui.input(label="Nome")
        email_in = ui.input(label="E-mail")
        with ui.row().classes("items-center"):
            address_in = ui.input(label="Endereço")
            ui.button(icon="search", on_click=get_coords).classes("ml-2")
        lat_in = ui.input(label="Latitude")
        lon_in = ui.input(label="Longitude")
        def save():
            n, e, a = name_in.value.strip(), email_in.value.strip(), address_in.value.strip()
            try:
                lat, lon = float(lat_in.value), float(lon_in.value)
            except:
                ui.notify("Latitude/Longitude inválidas", color="negative")
                return
            if not (n and e and a):
                ui.notify("Preencha todos os campos.", color="negative"); return
            add_customer(n, e, a, lat, lon)
            refresh("Cliente adicionado!")
            dialog.close()
        with ui.card_actions().classes("w-full justify-end"):
            ui.button("Salvar", on_click=save, color="primary", icon="save")
            ui.button("Cancelar", on_click=dialog.close, color="negative", icon="close")
    dialog.open()

def edit_customer_dialog(cust):
    with ui.dialog() as dlg, ui.card():
        ui.label("Editar Cliente").classes("text-h6")
        name_in = ui.input(label="Nome", value=cust.name)
        email_in = ui.input(label="E-mail", value=cust.email)
        address_in = ui.input(label="Endereço", value=cust.address)
        lat_in = ui.input(label="Latitude", value=cust.latitude)
        lon_in = ui.input(label="Longitude", value=cust.longitude)
        def save():
            n, e, a = name_in.value.strip(), email_in.value.strip(), address_in.value.strip()
            try:
                lat, lon = float(lat_in.value), float(lon_in.value)
            except:
                ui.notify("Latitude/Longitude inválidas", color="negative"); return
            if not (n and e and a):
                ui.notify("Preencha todos os campos.", color="negative"); return
            update_customer(cust.id, n, e, a, lat, lon)
            refresh("Cliente atualizado!")
            dlg.close()
        with ui.card_actions().classes("w-full justify-end"):
            ui.button("Salvar", on_click=save, color="primary", icon="save")
            ui.button("Cancelar", on_click=dlg.close, color="negative", icon="close")
    dlg.open()

def deactivate_customer(cust):
    with ui.dialog() as dlg, ui.card():
        ui.label("Desativar cliente?").classes("text-h5")
        ui.label(f"({cust.id}) {cust.name}").classes("text-h6")
        def confirm():
            toggle_customer_active(cust.id, False)
            refresh("Cliente desativado")
            dlg.close()
        with ui.card_actions().classes("w-full justify-end"):
            ui.button("Sim", on_click=confirm, color="warning", icon="delete")
            ui.button("Não", on_click=dlg.close, icon="close")
    dlg.open()

def activate_customer(cust):
    with ui.dialog() as dlg, ui.card():
        ui.label("Ativar cliente?").classes("text-h5")
        ui.label(f"({cust.id}) {cust.name}").classes("text-h6")
        def confirm():
            toggle_customer_active(cust.id, True)
            refresh("Cliente ativado!")
            dlg.close()
        with ui.card_actions().classes("w-full justify-end"):
            ui.button("Sim", on_click=confirm, color="success", icon="check")
            ui.button("Não", on_click=dlg.close, icon="close")
    dlg.open()

def customer_list():
    _cust_list.clear()
    with _cust_list, ui.card().classes("w-full h-full overflow-auto"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Clientes Cadastrados").classes("text-h5")
            ui.icon("people").classes("text-h5 ml-auto")

        with ui.row().classes("w-full justify-between"):
            ui.button("Adicionar", on_click=add_customer_dialog,
                      color="primary", icon="add").classes("mb-4")
            sw = ui.switch("Mostrar desativados",
                           value=ui.state.show_disabled_customers,
                           on_change=lambda e: toggle_show_disabled(e.value))

        custs = get_customers()
        if custs:
            ui.separator()
            for c in custs:
                with ui.column().classes("w-full"): # Similar to depot_list for structure
                    with ui.row().classes("items-center justify-between w-full") as row_element:
                        with ui.label(f"{c.name}").classes("text-body1"), ui.tooltip():
                            ui.label(f"ID: {c.id}").classes("body-text")
                            ui.label(f"Nome: {c.name}").classes("body-text")
                            ui.label(f"Email: {c.email}").classes("body-text")
                            ui.label(f"Endereço: {c.address}").classes("body-text")
                            ui.label(f"Coords: ({c.latitude}, {c.longitude})").classes("body-text")

                        with ui.row().classes("gap-2"):
                            ui.button(icon="edit",
                                      on_click=lambda x=c: edit_customer_dialog(x),
                                      color="primary")
                            if c.active:
                                ui.button(icon="delete",
                                          on_click=lambda x=c: deactivate_customer(x), # type: ignore
                                          color="warning")
                            else:
                                ui.button(icon="check",
                                          on_click=lambda x=c: activate_customer(x),
                                          color="success")
                if not c.active:
                    row_element.bind_visibility(sw, "value")
        else:
            ui.label("Nenhum cliente encontrado.")

def customer_map():
    custs = get_customers()
    if custs:
        lats = [c.latitude for c in custs if c.latitude]
        lons = [c.longitude for c in custs if c.longitude]
        m = folium.Map(location=[mean(lats), mean(lons)], zoom_start=11.5)
        if len(custs) > 1:
            m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])
        for c in custs:
            if c.latitude and c.longitude and (c.active or ui.state.show_disabled_customers):
                folium.Marker(
                    location=[c.latitude, c.longitude],
                    popup=f"({c.id}) {c.name}<br>{c.email}",
                    icon=folium.Icon(color="blue" if c.active else "gray")
                ).add_to(m)
    else:
        # Mapa de fallback em Fortaleza CE
        m = folium.Map(location=[-3.7327, -38.5267], zoom_start=12)
    # 
    _cust_map.clear()
    with _cust_map, ui.card().classes("w-full h-full"):    
        ui.html(m._repr_html_()).classes("w-full h-full")

def toggle_show_disabled(is_checked: bool):
    ui.state.show_disabled_customers = is_checked
    customer_map()

def customer_page(container):
    global _cust_list, _cust_map
    container.clear()
    with container:
        _cust_list = ui.column().classes("w-1/3 h-full")
        customer_list()
        _cust_map = ui.column().classes("w-2/3 h-full")
        customer_map()

def refresh(msg: str = "", color: str = "positive"):
    customer_list()
    customer_map()
    if msg:
        ui.notify(msg, color=color)
