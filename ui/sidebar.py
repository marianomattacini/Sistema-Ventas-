"""
Sidebar fijo de navegación (izquierda).

Muestra las secciones a las que el usuario logueado tiene acceso según su
rol/permisos (usuario_actual.tiene_permiso(...)) y resalta la pantalla activa.
"""

import customtkinter as ctk
from ui.theme import Color, Font, Spacing, Radius

# ---------------------------------------------------------------------------
# Definición del menú: secciones -> items (icono, texto, pantalla, permiso)
# `permiso=None` significa "siempre visible para quien vea el sidebar".
# ---------------------------------------------------------------------------
MENU = [
    {
        "titulo": None,
        "items": [
            ("🧾", "Punto de Venta", "pos", "ver_pos"),
        ],
    },
    {
        "titulo": "GENERAL",
        "items": [
            ("📊", "Panel Principal", "administracion", "gestionar_usuarios"),
        ],
    },
    {
        "titulo": "OPERACIONES",
        "items": [
            ("📦", "Productos", "productos", "gestionar_productos"),
            ("👥", "Clientes", "clientes", "gestionar_clientes"),
            ("🏢", "Proveedores", "proveedores", "gestionar_proveedores"),
            ("📥", "Compras", "compras", "gestionar_compras"),
            ("🕒", "Turnos", "turnos", "ver_reportes_basicos"),
        ],
    },
    {
        "titulo": "GERENCIA",
        "items": [
            ("📈", "Panel del Gerente", "gerente", "ver_balances"),
            ("🧑‍💼", "Empleados", "empleados", "ver_balances"),
            ("💰", "Presupuestos", "presupuestos", "ver_balances"),
            ("🏦", "Entidad de Pago", "entidad_pago", "ver_balances"),
        ],
    },
    {
        "titulo": "SISTEMA",
        "items": [
            ("🔐", "Usuarios", "usuarios", "gestionar_usuarios"),
            ("⚙️", "Configuración", "configuracion", "ver_balances"),
        ],
    },
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=Color.SIDEBAR_BG, corner_radius=0, width=240)
        self.app = app
        self.grid_propagate(False)
        self.botones = {}  # nombre_pantalla -> CTkButton

        self._crear_encabezado()
        self._crear_menu()
        self._crear_pie()

    def _crear_encabezado(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=Spacing.MD, pady=(Spacing.LG, Spacing.MD))
        ctk.CTkLabel(
            header, text="🏪 Sistema de Ventas",
            font=Font.H3, text_color=Color.ACCENT, anchor="w",
            wraplength=200, justify="left",
        ).pack(fill="x")

    def _crear_menu(self):
        self.frame_menu = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=Color.SIDEBAR_BG,
            scrollbar_button_hover_color=Color.BORDER,
        )
        self.frame_menu.pack(fill="both", expand=True, padx=Spacing.SM)

    def _crear_pie(self):
        pie = ctk.CTkFrame(self, fg_color="transparent")
        pie.pack(fill="x", padx=Spacing.SM, pady=Spacing.MD)

        self.lbl_usuario = ctk.CTkLabel(
            pie, text="", font=Font.SMALL, text_color=Color.TEXT_SECONDARY,
            anchor="w", justify="left", wraplength=200,
        )
        self.lbl_usuario.pack(fill="x", padx=Spacing.SM, pady=(0, Spacing.SM))

        btn_salir = ctk.CTkButton(
            pie, text="🚪 Cerrar Sesión", font=Font.BODY_BOLD, height=38,
            corner_radius=Radius.MD, fg_color=Color.DANGER,
            hover_color=Color.DANGER_HOVER, command=self._cerrar_sesion,
        border_width=1, border_color="#B8C1CE", text_color="#FFFFFF")
        btn_salir.pack(fill="x")

    def _cerrar_sesion(self):
        from tkinter import messagebox
        if messagebox.askyesno("Cerrar Sesión", "¿Está seguro de que desea cerrar sesión?"):
            self.app.cerrar_sesion()

    def actualizar(self, pantalla_activa):
        """Reconstruye el menú según el usuario logueado y resalta la pantalla activa."""
        for widget in self.frame_menu.winfo_children():
            widget.destroy()
        self.botones = {}

        usuario = self.app.usuario_actual
        if usuario is None:
            return

        self.lbl_usuario.configure(text=f"👤 {usuario.nombre_usuario}\n{usuario.rol}")

        for seccion in MENU:
            items_visibles = [
                it for it in seccion["items"] if usuario.tiene_permiso(it[3])
            ]
            if not items_visibles:
                continue

            if seccion["titulo"]:
                ctk.CTkLabel(
                    self.frame_menu, text=seccion["titulo"], font=Font.SMALL,
                    text_color=Color.TEXT_MUTED, anchor="w",
                ).pack(fill="x", padx=Spacing.SM, pady=(Spacing.SM, 2))

            for icono, texto, nombre_pantalla, _permiso in items_visibles:
                self._crear_item(icono, texto, nombre_pantalla)

        self._resaltar(pantalla_activa)

    def _crear_item(self, icono, texto, nombre_pantalla):
        btn = ctk.CTkButton(
            self.frame_menu, text=f"  {icono}   {texto}", anchor="w",
            font=Font.BODY_BOLD, height=42, corner_radius=Radius.SM,
            fg_color="transparent", hover_color=Color.SIDEBAR_ITEM_HOVER,
            text_color=Color.TEXT_PRIMARY,
            command=lambda n=nombre_pantalla: self.app.mostrar_pantalla(n),
        border_width=1, border_color="#B8C1CE")
        btn.pack(fill="x", pady=2)
        self.botones[nombre_pantalla] = btn

    def _resaltar(self, pantalla_activa):
        for nombre, btn in self.botones.items():
            if nombre == pantalla_activa:
                btn.configure(fg_color=Color.SIDEBAR_ITEM_ACTIVE,
                              text_color=Color.SIDEBAR_ITEM_ACTIVE_TEXT,
                              hover_color=Color.SIDEBAR_ITEM_ACTIVE)
            else:
                btn.configure(fg_color="transparent",
                              text_color=Color.TEXT_PRIMARY,
                              hover_color=Color.SIDEBAR_ITEM_HOVER)
