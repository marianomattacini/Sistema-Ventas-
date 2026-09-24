"""
Header superior fijo: botón "Volver", título de la pantalla actual y
datos del usuario logueado. Se muestra en todas las pantallas menos login.
"""

import customtkinter as ctk
from ui.theme import Color, Font, Spacing, Radius, boton_volver

TITULOS = {
    "pos": ("🧾", "Punto de Venta"),
    "administracion": ("📊", "Panel Principal"),
    "productos": ("📦", "Productos"),
    "clientes": ("👥", "Clientes"),
    "proveedores": ("🏢", "Proveedores"),
    "compras": ("📥", "Compras"),
    "turnos": ("🕒", "Turnos"),
    "gerente": ("📈", "Panel del Gerente"),
    "empleados": ("🧑‍💼", "Empleados"),
    "presupuestos": ("💰", "Presupuestos"),
    "entidad_pago": ("🏦", "Entidad de Pago"),
    "usuarios": ("🔐", "Usuarios"),
    "configuracion": ("⚙️", "Configuración"),
}


class Header(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=Color.BG_BASE, corner_radius=0, height=60)
        self.app = app
        self.grid_propagate(False)

        self.btn_volver = boton_volver(self, command=self.app.volver)
        self.btn_volver.pack(side="left", padx=Spacing.MD, pady=Spacing.SM)

        self.lbl_titulo = ctk.CTkLabel(
            self, text="", font=Font.H3, text_color=Color.ACCENT,
        )
        self.lbl_titulo.pack(side="left", padx=Spacing.SM)

        self.lbl_usuario = ctk.CTkLabel(
            self, text="", font=Font.SMALL, text_color=Color.TEXT_SECONDARY,
        )
        self.lbl_usuario.pack(side="right", padx=Spacing.MD)

    def actualizar(self, nombre_pantalla):
        icono, texto = TITULOS.get(nombre_pantalla, ("", nombre_pantalla.capitalize()))
        self.lbl_titulo.configure(text=f"{icono}  {texto}")

        usuario = self.app.usuario_actual
        if usuario:
            self.lbl_usuario.configure(text=f"👤 {usuario.nombre_usuario} ({usuario.rol})")

        puede_volver = len(self.app.historial) > 1
        self.btn_volver.configure(state=("normal" if puede_volver else "disabled"))
