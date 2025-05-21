from nicegui import ui

@ui.page("/")
def index():
    ui.label("Bem-vindo ao sistema")
    ui.button("Clique para testar", on_click=lambda: ui.notify("Funcionou!"))
    ui.button("Clique para ir para a página sobre", on_click=lambda: ui.navigate.to("/sobre"))
    ui.button("Clique para ir para a página de depots", on_click=lambda: ui.navigate.to("/depots"))

@ui.page("/sobre")
def about():
    ui.label("Página sobre")

@ui.page("/depots")
def depots():
    ui.label("Página de Depots")
