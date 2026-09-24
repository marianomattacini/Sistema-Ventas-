"""
Frame base para todas las pantallas del sistema.

Antes cada "ventana_X.py" era una ventana independiente (ctk.CTkToplevel)
que se abría encima de las demás. Ahora todas son ctk.CTkFrame que se
montan dentro del contenedor único de la ventana principal (ui/app.py),
por lo que la app entera vive en una sola ventana con navegación por
sidebar + botón "Volver".
"""

import customtkinter as ctk
from ui.theme import Color


class BaseFrame(ctk.CTkFrame):
    """
    Clase base de la que heredan todas las pantallas (Frame*).

    Parámetros:
        parent: contenedor de la ventana principal donde se monta el frame.
        controller: instancia de App (ui/app.py) — expone navegación
                    (mostrar_pantalla, volver, cerrar_sesion) y estado
                    global (usuario_actual, turno_actual).
        usuario_actual: usuario logueado (o None en la pantalla de login).
    """

    def __init__(self, parent, controller, usuario_actual=None, **kwargs):
        super().__init__(parent, fg_color=Color.BG_APP)
        self.controller = controller
        self.usuario_actual = usuario_actual
