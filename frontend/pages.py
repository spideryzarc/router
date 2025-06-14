"""
Módulo de definição das páginas principais da aplicação NiceGUI:
- Layout base (header, menu e footer)
- Rotas: página inicial ("/") e sobre ("/sobre")
"""

from nicegui import ui
from frontend.pages_depots import depot_page
from frontend.pages_costumers import customer_page
from frontend.pages_vehicles import vehicle_page
from frontend.pages_orders import order_page 
from frontend.pages_planning import planning_page # Import the new planning page function


def base_layout() -> ui.row:
    """
    Cria o layout base da aplicação:
    1. Header com botão de menu e título
    2. Container principal para renderizar o conteúdo de cada página
    3. Footer com informações de rodapé
    Retorna o container (ui.Row) onde o conteúdo específico deve ser inserido.
    """
    # Container principal que ocupa toda a área disponível
    main_container = ui.row().classes('w-full h-full no-wrap')

    # Cabeçalho
    with ui.header().classes('bg-primary text-white'):
        # Botão de menu com opções de navegação
        with ui.button(icon='menu'):
            with ui.menu() as menu:
                ui.menu_item('Depósitos', on_click=lambda: depot_page(main_container))
                ui.menu_item('Clientes',  on_click=lambda: customer_page(main_container))
                ui.menu_item('Veículos',  on_click=lambda: vehicle_page(main_container))
                ui.menu_item('Pedidos',   on_click=lambda: order_page(main_container))
                ui.menu_item('Planejamentos', on_click=lambda: planning_page(main_container)) # Add menu item for Plannings
                ui.separator()
                ui.menu_item('Sobre', on_click=lambda: about(main_container))                
        # Título da aplicação
        ui.label("Laboratório de Matemática Industrial (Roteirizador)") \
          .classes('text-h4 ml-4')

    # Footer
    with ui.footer().classes('bg-primary text-white flex items-center p-1'):
        ui.label("Lab. MI").classes('text-body2')
        ui.label("2025").classes('text-body2')
        ui.label("Desenvolvedores: Albert E. F. Muritiba").classes('ml-auto text-body2')
        ui.label("Versão 1.0").classes('ml-auto text-body2')

    return main_container


@ui.page("/")
def index():
    """
    Página inicial:
    - Monta o layout base
    - Renderiza a página de gerenciamento de depósitos dentro do container
    """
    container = base_layout()
    depot_page(container)
    # vehicle_page(container)  # Exemplo: renderiza a página de veículos


def about(container: ui.row):
    """
    Página "Sobre":
    - Limpa o container principal
    - Exibe informações sobre a aplicação
    """
    container.clear()
    with container, ui.card().classes('w-full h-full'):
        ui.label("Sobre a aplicação").classes('text-h4')
        ui.label("Esta é uma aplicação de exemplo para o Laboratório de Matemática Industrial.").classes('text-body1')
        ui.label("Desenvolvedores: Equipe de Desenvolvimento").classes('text-body2')
        ui.label("Versão 1.0").classes('text-body2')
        ui.button("Voltar", on_click=lambda: ui.navigate.to("/")).classes('mt-4')
