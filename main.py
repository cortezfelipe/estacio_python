import PySimpleGUI as sg
from crud_generic import create_crud_window

# Layout do menu principal
layout = [
    #[sg.Text("Menu Principal")],
    [sg.Button("Usuários", key="usuarios")],
    [sg.Button("Cursos", key="cursos")],
    [sg.Button("Inscrições", key="inscricoes")],
    [sg.Button("Recursos", key="recursos")],
    [sg.Button("Avaliações", key="avaliacoes")],
    [sg.Button("Sair")]
]

window = sg.Window("Menu Principal", layout)

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == "Sair":
        break
    elif event in ["usuarios", "cursos", "inscricoes", "recursos", "avaliacoes"]:
        window.hide()
        create_crud_window(event)
        window.un_hide()

window.close()