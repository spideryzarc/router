from nicegui import ui
from backend.controler import *
import folium


def base_layout():
    with ui.header():
        with ui.button(icon='menu'):
            with ui.menu() as menu:
                ui.menu_item('Depósitos', on_click=lambda: ui.navigate.to('/depots'))
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


@ui.page("/depots")
def depots():
    base_layout()
    # Linha principal que ocupará a altura disponível e usará flexbox
    with ui.row().classes('w-full h-full no-wrap'):
        # Coluna da esquerda: Lista de depósitos, com largura fixa e scroll se necessário
        with ui.column().classes('w-[400px] p-4 overflow-auto'): # Ajuste a largura (w-[400px]) conforme necessário
            with ui.card().classes('w-full'):
                ui.label("Depósitos Cadastrados").classes("text-h5")                
                ui.button("Adicionar", on_click=open_add_depot_card, color="primary", icon="add").classes("mb-4")

                # Container para a lista de depósitos, que será atualizado dinamicamente
                def refresh_depositos():
                    deposits_container.clear()
                    depositos = get_depots()  # Função que retorna os depósitos
                    if depositos:
                        for depot in depositos:
                            if depot.active or show_disabled.value:
                                with deposits_container:
                                    with ui.row().classes('items-center justify-between w-full'):
                                        ui.label(f"({depot.id}) {depot.name}").classes("text-h6")
                                        # ui.label(f"Endereço: {depot.address}")
                                        with ui.row().classes('items-center gap-2'):
                                            ui.button("", on_click=lambda d=depot: open_edit_depot(d), color="primary", icon="edit")
                                            if depot.active:
                                                ui.button("", on_click=lambda d=depot: confirm_active_toggle(d,False), color="warning", icon="delete")
                                            else:
                                                ui.button("", on_click=lambda d=depot: confirm_active_toggle(d, True), color="success", icon="check")
                    else:
                        with deposits_container:
                            ui.label("Nenhum depósito encontrado.")
                
                # Toggle para mostrar depósitos desativados
                show_disabled = ui.checkbox("Mostrar depósitos desativados", value=False, on_change=lambda: refresh_depositos()).classes('mb-4')
                ui.separator()	
                deposits_container = ui.column().classes('w-full')

                # Atualiza a lista sempre que o checkbox for modificado
                show_disabled.on("update", lambda: refresh_depositos())
                refresh_depositos()

        # Coluna da direita: Mapa ocupando o espaço restante
        with ui.column().classes('flex-grow p-4'): # flex-grow faz a coluna ocupar o espaço restante
            with ui.card().classes('w-full h-full'): # Card ocupa todo o espaço da coluna
                #lista de depósitos para exibir no mapa
                depots = get_depots()
                coords = [ (depot.latitude, depot.longitude) for depot in depots if depot.latitude and depot.longitude]
                # Cria o mapa centralizado na média das coordenadas dos depósitos
                if coords:
                    avg_lat = sum(lat for lat, lon in coords) / len(coords)
                    avg_lon = sum(lon for lat, lon in coords) / len(coords)
                    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)
                    # Adiciona marcadores para cada depósito
                    for depot in depots:
                        if depot.latitude and depot.longitude:
                            folium.Marker(
                                location=[depot.latitude, depot.longitude],
                                popup=f"({depot.id}) {depot.name}<br>{depot.address}",
                                icon=folium.Icon(color='blue' if depot.active else 'gray')
                            ).add_to(m)
                else:
                    # Se não houver depósitos com coordenadas, centraliza em São Paulo
                    m = folium.Map(location=[-23.55052, -46.633308], zoom_start=12)
                    ui.label("Nenhum depósito com coordenadas disponíveis. Exibindo mapa de São Paulo.")
                    
                # # Cria o mapa centralizado em São Paulo
                # m = folium.Map(location=[-23.55052, -46.633308], zoom_start=12)
                # # Exemplo: adiciona um marcador
                # folium.Marker(location=[-23.55052, -46.633308], popup="Centro de São Paulo").add_to(m)
                # Obtém a representação HTML do mapa
                map_html = m._repr_html_()
                # Exibe o mapa na interface, fazendo-o ocupar todo o card
                ui.html(map_html).classes('w-full h-full')

# Modal de confirmação para desativar um depósito
def confirm_active_toggle(depot, active):
    action = "ativar" if active else "desativar"
    def confirm_disable(dialog, depot):
        toggle_depot_active(depot.id, active)  # Implemente essa função para desativar o depósito
        ui.notify("Depósito atualizado!")
        dialog.close()
        # reload a página para atualizar a lista de depósitos
        ui.navigate.to('/depots')
    with ui.dialog() as confirm_dialog, ui.card():
        ui.label(f"Deseja {action} o depósito:").classes("text-h5")
        ui.label(f"({depot.id}) {depot.name}").classes("text-h6")
        with ui.card_actions().classes('w-full justify-end'):
            ui.button("Sim", on_click=lambda: confirm_disable(confirm_dialog, depot), color="warning", icon="delete")
            ui.button("Não", on_click=confirm_dialog.close, icon="close")
    confirm_dialog.open()



# Exemplo de uso dentro de um dialog com card (para adicionar depósito):
def open_add_depot_card():
    with ui.dialog() as dialog, ui.card():
        ui.label("Adicionar Novo Depósito").classes("text-h6")
        name_input = ui.input(label="Nome")
        address_input = ui.input(label="Endereço")
        with ui.card_actions().classes('w-full justify-end'):
            ui.button("Salvar", on_click=lambda: save_and_close(dialog, name_input.value, address_input.value), color="primary", icon="save")
            ui.button("Cancelar", on_click=dialog.close, color="negative", icon="close")
    dialog.open()

def save_and_close(dialog, name, address):
    add_depot(name, address)
    ui.notify("Depósito adicionado com sucesso!")
    dialog.close()
    # reload a página para atualizar a lista de depósitos
    ui.navigate.to('/depots')

def open_edit_depot(depot):
    with ui.dialog() as edit_dialog, ui.card():
        ui.label("Editar Depósito").classes("text-h6")
        name_input = ui.input(label="Nome", value=depot.name)
        address_input = ui.input(label="Endereço", value=depot.address)
        lat_input = ui.input(label="Latitude", value=depot.latitude if depot.latitude else "")
        lon_input = ui.input(label="Longitude", value=depot.longitude if depot.longitude else "")
        with ui.card_actions().classes('w-full justify-end'):
            ui.button("Salvar", on_click=lambda: save_edit_depot(edit_dialog, depot, 
                                                                 name_input.value, 
                                                                 address_input.value,
                                                                 lat_input.value,
                                                                 lon_input.value
                                                                 ), color="primary", icon="save")
            ui.button("Cancelar", on_click=edit_dialog.close, color="negative", icon="close")
    edit_dialog.open()

def save_edit_depot(dialog, depot, new_name, new_address, new_latitude=None, new_longitude=None):
    update_depot(depot.id, new_name, new_address, new_latitude, new_longitude)
    ui.notify("Depósito atualizado com sucesso!")
    dialog.close()
    # reload a página para atualizar a lista de depósitos
    ui.navigate.to('/depots')
