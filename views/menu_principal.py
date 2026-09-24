import customtkinter as ctk
from tkinter import messagebox
from models.turno import Turno

class MenuPrincipal(ctk.CTkFrame):
    """Pantalla de menú principal con botones según el rol."""

    def __init__(self, parent, controller, usuario):
        super().__init__(parent)
        self.controller = controller
        self.usuario = usuario

        # Configurar grid para centrar el contenido
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)

        # Frame central
        frame_central = ctk.CTkFrame(self, fg_color="#F9FAFB", corner_radius=15, border_width=1, border_color="#B8C1CE")
        frame_central.grid(row=1, column=1, padx=20, pady=20, sticky="nsew")

        # Título y bienvenida
        ctk.CTkLabel(frame_central, text=f"🏪 Bienvenido, {self.usuario.nombre_usuario}",
                    font=("Roboto", 28, "bold"), text_color="#1D4ED8"
        ).pack(pady=(30, 10))

        ctk.CTkLabel(frame_central, text=f"Rol: {self.usuario.rol}",
                    font=("Roboto", 16), text_color="#6B7280"
        ).pack(pady=(0, 30))

        # Botones según rol
        self._crear_botones(frame_central)

        # Botón Cerrar Sesión
        ctk.CTkButton(frame_central, text="🚪 Cerrar Sesión", height=40,
                     fg_color="#DC2626", hover_color="#B91C1C",
                     corner_radius=10, command=self.controller.cerrar_sesion
        , border_width=1, border_color="#CBD2DC", text_color="#FFFFFF").pack(pady=(30, 20))

    def _crear_botones(self, parent):
        """Crea los botones según el rol del usuario."""
        frame_botones = ctk.CTkFrame(parent, fg_color="transparent")
        frame_botones.pack(fill="both", expand=True, padx=20, pady=10)

        # Configurar grid para 2 columnas
        for i in range(2):
            frame_botones.grid_columnconfigure(i, weight=1)

        # Función para crear botones
        def crear_boton(fila, columna, texto, comando, color="#2563EB"):
            btn = ctk.CTkButton(frame_botones, text=texto, height=60,
                              font=("Roboto", 16, "bold"), fg_color=color,
                              hover_color="#2563EB" if color == "#2563EB" else color,
                              corner_radius=12, command=comando, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
            btn.grid(row=fila, column=columna, padx=10, pady=10, sticky="nsew")
            return btn

        # Botones comunes a todos
        if self.usuario.tiene_permiso('puede_vender'):
            crear_boton(0, 0, "🛒 Punto de Venta (POS)", self._abrir_pos, "#15803D")

        if self.usuario.rol in ["Administrador", "Gerente General"]:
            crear_boton(0, 1, "⚙️ Administración", self._abrir_administracion, "#2563EB")

        if self.usuario.rol == "Gerente General":
            crear_boton(1, 0, "📊 Panel del Gerente", self._abrir_gerente, "#7C3AED")

        if self.usuario.tiene_permiso('puede_gestionar_productos'):
            crear_boton(1, 1, "📦 Productos", self._abrir_productos, "#C2410C")

        if self.usuario.tiene_permiso('puede_gestionar_clientes'):
            crear_boton(2, 0, "👥 Clientes", self._abrir_clientes, "#15803D")

        if self.usuario.tiene_permiso('puede_gestionar_proveedores'):
            crear_boton(2, 1, "🏢 Proveedores", self._abrir_proveedores, "#2563EB")

        if self.usuario.tiene_permiso('puede_gestionar_compras'):
            crear_boton(3, 0, "📥 Compras", self._abrir_compras, "#7C3AED")

        if self.usuario.tiene_permiso('puede_ver_reportes'):
            crear_boton(3, 1, "🕒 Turnos", self._abrir_turnos, "#C2410C")

        if self.usuario.tiene_permiso('puede_gestionar_usuarios'):
            crear_boton(4, 0, "🔐 Usuarios", self._abrir_usuarios, "#DC2626")

        if self.usuario.rol == "Gerente General":
            crear_boton(4, 1, "👥 Empleados", self._abrir_empleados, "#C2410C")

    def _abrir_pos(self):
        turno_abierto = Turno.obtener_turno_abierto()
        if turno_abierto and turno_abierto[1] == self.usuario.id:
            self.controller.mostrar_pos(self.usuario, turno_abierto[0])
        else:
            self.controller.mostrar_pos(self.usuario, None)

    def _abrir_administracion(self):
        self.controller.mostrar_administracion(self.usuario)

    def _abrir_gerente(self):
        self.controller.mostrar_gerente(self.usuario)

    def _abrir_productos(self):
        self.controller.mostrar_productos(self.usuario)

    def _abrir_clientes(self):
        self.controller.mostrar_clientes(self.usuario)

    def _abrir_proveedores(self):
        self.controller.mostrar_proveedores(self.usuario)

    def _abrir_compras(self):
        self.controller.mostrar_compras(self.usuario)

    def _abrir_turnos(self):
        self.controller.mostrar_turnos(self.usuario)

    def _abrir_usuarios(self):
        self.controller.mostrar_usuarios(self.usuario)

    def _abrir_empleados(self):
        self.controller.mostrar_empleados(self.usuario)