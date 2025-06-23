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
        address = address_in.value.strip()
        if not address:
            ui.notify("Preencha o endereço primeiro.", color="negative")
            return

        # Exibe um diálogo de espera enquanto busca as coordenadas
        with ui.dialog() as wait_dialog:
            ui.label("Obtendo coordenadas...").classes("text-h6")
            wait_dialog.open()
        try:
            lat, lon = geocode(address)
            if lat is not None and lon is not None:
                lat_in.value = str(lat)
                lon_in.value = str(lon)
                ui.notify("Coordenadas obtidas com sucesso!", color="positive")
            else:
                ui.notify("Endereço inválido ou não encontrado.", color="negative")
        except Exception as e:
            ui.notify(f"Erro ao buscar coordenadas: {e}", color="negative")
        finally:
            wait_dialog.close()

    def save():
        name = name_in.value.strip()
        email = email_in.value.strip()
        address = address_in.value.strip()

        # Validação de latitude e longitude
        try:
            lat = float(lat_in.value)
            lon = float(lon_in.value)
        except ValueError:
            ui.notify("Latitude/Longitude inválidas.", color="negative")
            return

        # Validação de campos obrigatórios
        if not (name and email and address):
            ui.notify("Preencha todos os campos obrigatórios.", color="negative")
            return

        # Adiciona o cliente e atualiza a interface
        add_customer(name, email, address, lat, lon)
        refresh("Cliente adicionado com sucesso!", color="positive")
        dialog.close()

    # Criação do diálogo principal
    with ui.dialog() as dialog, ui.card():
        ui.label("Adicionar Novo Cliente").classes("text-h6")
        name_in = ui.input(label="Nome").classes("w-full")
        email_in = ui.input(label="E-mail").classes("w-full")
        with ui.row().classes("items-center w-full"):
            address_in = ui.input(label="Endereço").classes("flex-grow")
            ui.button(icon="search", on_click=get_coords).classes("ml-2")
        lat_in = ui.input(label="Latitude").classes("w-full")
        lon_in = ui.input(label="Longitude").classes("w-full")

        # Botões de ação
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
                ui.notify("Latitude/Longitude inválidas", color="negative")
                return
            if not (n and e and a):
                ui.notify("Preencha todos os campos.", color="negative")
                return
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
            ui.button("Sim", on_click=confirm, color="dark", icon="visibility_off")
            ui.button("Não", on_click=dlg.close, icon="visibility", color="positive")
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
            ui.button("Sim", on_click=confirm, color="positive", icon="visibility")
            ui.button("Não", on_click=dlg.close, icon="visibility_off", color="dark")
    dlg.open()


def customer_list():
    _cust_list.clear()
    with _cust_list:
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full items-center justify-between"):
                ui.label("Clientes Cadastrados").classes("text-h6")
                ui.icon("people").classes("text-h6 ml-auto")
            with ui.row().classes("w-full justify-between"):
                ui.button("Adicionar", on_click=add_customer_dialog,
                        color="primary", icon="add").classes("mb-4")
                sw = ui.switch("Mostrar desativados",
                            value=ui.state.show_disabled_customers,
                            on_change=lambda e: toggle_show_disabled(e.value))
        with ui.scroll_area().classes("h-[calc(100vh-250px)] overflow-y-auto"):
            if customers := get_customers():
                for customer in customers:
                    with ui.card().classes("w-full") as customer_spam, \
                            ui.row().classes("items-center justify-between w-full"):
                        with ui.row().classes("items-center gap-2"):
                            ui.button(icon="edit",
                                    on_click=lambda x=customer: edit_customer_dialog(x),
                                    color="primary").props("flat dense").tooltip("Editar")
                            if customer.active:
                                ui.button(icon="visibility_off",
                                        on_click=lambda x=customer: deactivate_customer(x),  # type: ignore
                                        color="dark").props("flat dense").tooltip("Desativar")
                            else:
                                ui.button(icon="visibility",
                                        on_click=lambda x=customer: activate_customer(x),
                                        color="positive").props("flat dense").tooltip("Ativar")
                        with ui.label(f"{customer.name}").classes("text-body1"), ui.tooltip():
                            ui.label(f"ID: {customer.id}").classes("body-text")
                            ui.label(f"Nome: {customer.name}").classes("body-text")
                            ui.label(f"Email: {customer.email}").classes("body-text")
                            ui.label(f"Endereço: {customer.address}").classes("body-text")
                            ui.label(f"Coords: ({customer.latitude}, {customer.longitude})").classes("body-text")
                        ui.badge("Ativo" if customer.active else "Inativo", 
                                 color="positive" if customer.active else "dark").classes("ml-auto")
                if not customer.active:
                    customer_spam.bind_visibility(sw, "value")
            else:
                ui.label("Nenhum cliente encontrado.")


def customer_map():
    custs = get_customers()
    if custs:
        lats = [c.latitude for c in custs if c.latitude is not None]
        lons = [c.longitude for c in custs if c.longitude is not None]
        
        if lats and lons: # Check if there are valid coordinates to calculate mean
            m = folium.Map(location=[mean(lats), mean(lons)], zoom_start=12)
            if len(lats) > 1: # Only fit bounds if there's more than one point
                m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])
        else: # Fallback if no valid coordinates found among customers
            m = folium.Map(location=[-3.7327, -38.5267], zoom_start=12) # Fortaleza
            
        for c in custs:
            if c.latitude is not None and c.longitude is not None and (c.active or ui.state.show_disabled_customers):
                folium.Marker(
                    location=[c.latitude, c.longitude],
                    popup=f"({c.id}) {c.name}<br>{c.email}",
                    icon=folium.Icon(color="blue" if c.active else "gray")
                ).add_to(m)
    #
    _cust_map.clear()
    with _cust_map:
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
