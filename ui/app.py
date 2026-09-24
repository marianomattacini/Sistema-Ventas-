"""
Ventana principal única de la aplicación.

Reemplaza al viejo esquema de "una ventana (CTkToplevel) por pantalla".
Ahora existe una sola ventana raíz (App) con:
  - un sidebar fijo a la izquierda (ui/sidebar.py)
  - un header fijo arriba con botón "← Volver" (ui/header.py)
  - un contenedor central donde se monta el Frame de la pantalla activa

La navegación entre pantallas se hace SIEMPRE a través de:
    self.controller.mostrar_pantalla("nombre_pantalla", **kwargs)
    self.controller.volver()
    self.controller.cerrar_sesion()
desde cualquier Frame (ver views/base_frame.py).
"""

import importlib
import customtkinter as ctk

from ui import theme
from ui.theme import Color
from ui.sidebar import Sidebar
from ui.header import Header

# Registro de pantallas: nombre -> (módulo, nombre de la clase Frame)
PANTALLAS = {
    "login": ("views.ventana_login", "FrameLogin"),
    "pos": ("views.ventana_pos", "FramePOS"),
    "administracion": ("views.ventana_administracion", "FrameAdministracion"),
    "gerente": ("views.ventana_gerente", "FrameGerente"),
    "clientes": ("views.ventana_clientes", "FrameClientes"),
    "compras": ("views.ventana_compras", "FrameCompras"),
    "configuracion": ("views.ventana_configuracion", "FrameConfiguracion"),
    "empleados": ("views.ventana_empleados", "FrameEmpleados"),
    "entidad_pago": ("views.ventana_entidad_pago", "FrameEntidadPago"),
    "presupuestos": ("views.ventana_presupuestos", "FramePresupuestos"),
    "productos": ("views.ventana_productos", "FrameProductos"),
    "proveedores": ("views.ventana_proveedores", "FrameProveedores"),
    "turnos": ("views.ventana_turnos", "FrameTurnos"),
    "usuarios": ("views.ventana_usuarios", "FrameUsuarios"),
}

# Pantallas que NO muestran sidebar/header (pantalla de login)
PANTALLAS_SIN_CHROME = {"login"}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        theme.aplicar_tema_global()

        self.title("Sistema de Gestión de Ventas y Control de Stock")
        self.geometry("1300x800")
        self.minsize(1100, 650)
        self.configure(fg_color=Color.BG_APP)
        self._centrar_ventana()

        # Estado global de sesión
        self.usuario_actual = None
        self.turno_actual = None

        # Historial de navegación: lista de (nombre_pantalla, kwargs)
        self.historial = []
        self.pantalla_actual = None
        self.frame_actual = None

        self._crear_layout()
        self.mostrar_pantalla("login")

    def report_callback_exception(self, exc, val, tb):
        """
        Handler global de excepciones para TODOS los callbacks disparados
        por la interfaz (botones, eventos, etc.). Tkinter/CustomTkinter, por
        defecto, solo imprime el error en consola y sigue funcionando, pero
        el estado de la pantalla puede quedar inconsistente y silencioso.
        Acá se registra el error en un log y se avisa al usuario con un
        mensaje claro, en vez de dejar que la app se cuelgue o se cierre
        de forma inesperada (requisito de robustez de la consigna).
        """
        import traceback
        import os
        from datetime import datetime
        from tkinter import messagebox

        mensaje_error = "".join(traceback.format_exception(exc, val, tb))
        print("❌ Error no controlado en la interfaz:\n", mensaje_error)

        try:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, "errores.log"), "a", encoding="utf-8") as f:
                f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n{mensaje_error}\n")
        except Exception:
            pass  # si ni siquiera se puede loguear, no vamos a romper la app por eso

        try:
            messagebox.showerror(
                "Ocurrió un error",
                f"Se produjo un error inesperado y fue registrado.\n"
                f"La aplicación va a continuar funcionando.\n\nDetalle: {val}"
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # ROBUSTEZ: manejo global de excepciones no capturadas
    # ------------------------------------------------------------------
    def report_callback_exception(self, exc_type, exc_value, exc_traceback):
        """
        CustomTkinter/Tkinter invoca este método cada vez que un callback
        (click de botón, evento, etc.) lanza una excepción no manejada.
        Sin esto, cualquier error de programación imprevisto puede dejar la
        UI en un estado inconsistente o, según el error, cerrar la app.
        Acá se registra el error y se avisa al usuario sin cortar la sesión.
        """
        import traceback
        import logging
        import tkinter.messagebox as messagebox

        mensaje_error = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        try:
            logging.getLogger("sistema_ventas").error(
                "Excepción no controlada en la interfaz:\n%s", mensaje_error
            )
        except Exception:
            pass

        try:
            messagebox.showerror(
                "Ocurrió un error inesperado",
                "La operación no pudo completarse debido a un error interno.\n"
                "El sistema sigue funcionando con normalidad; si el problema "
                "persiste, contacte a soporte técnico.\n\n"
                f"Detalle técnico: {exc_type.__name__}: {exc_value}"
            )
        except Exception:
            # Si ni siquiera se puede mostrar el messagebox, al menos lo dejamos en consola.
            print(mensaje_error)

    # ------------------------------------------------------------------
    # LAYOUT BASE
    # ------------------------------------------------------------------
    def _centrar_ventana(self):
        self.update_idletasks()
        ancho, alto = 1300, 800
        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    def _crear_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = Sidebar(self, self)
        # Se posiciona (grid) recién cuando hay una sesión iniciada.

        self.frame_derecha = ctk.CTkFrame(self, fg_color=Color.BG_APP, corner_radius=0)
        self.frame_derecha.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.frame_derecha.grid_rowconfigure(1, weight=1)
        self.frame_derecha.grid_columnconfigure(0, weight=1)

        self.header = Header(self.frame_derecha, self)
        # Se posiciona (grid) recién cuando hay una sesión iniciada.

        self.contenedor = ctk.CTkFrame(self.frame_derecha, fg_color=Color.BG_APP, corner_radius=0)
        self.contenedor.grid(row=1, column=0, sticky="nsew")
        self.contenedor.grid_rowconfigure(0, weight=1)
        self.contenedor.grid_columnconfigure(0, weight=1)

    def _mostrar_chrome(self, mostrar):
        """Muestra u oculta sidebar + header (se ocultan solo en la pantalla de login)."""
        if mostrar:
            self.sidebar.grid(row=0, column=0, sticky="nsew")
            self.frame_derecha.grid(row=0, column=1, columnspan=1, sticky="nsew")
            self.header.grid(row=0, column=0, sticky="new")
        else:
            self.sidebar.grid_forget()
            self.header.grid_forget()
            self.frame_derecha.grid(row=0, column=0, columnspan=2, sticky="nsew")

    # ------------------------------------------------------------------
    # NAVEGACIÓN
    # ------------------------------------------------------------------
    def mostrar_pantalla(self, nombre, agregar_historial=True, **kwargs):
        if nombre not in PANTALLAS:
            raise ValueError(f"Pantalla desconocida: {nombre}")

        modulo_nombre, clase_nombre = PANTALLAS[nombre]
        modulo = importlib.import_module(modulo_nombre)
        clase = getattr(modulo, clase_nombre)

        if self.frame_actual is not None:
            self.frame_actual.destroy()

        frame = clase(self.contenedor, self, usuario_actual=self.usuario_actual, **kwargs)
        frame.grid(row=0, column=0, sticky="nsew")

        self.frame_actual = frame
        self.pantalla_actual = nombre

        con_chrome = nombre not in PANTALLAS_SIN_CHROME
        self._mostrar_chrome(con_chrome)
        if con_chrome:
            self.sidebar.actualizar(nombre)
            self.header.actualizar(nombre)

        if agregar_historial:
            # Evita duplicar la misma pantalla consecutiva en el historial
            if not self.historial or self.historial[-1][0] != nombre:
                self.historial.append((nombre, kwargs))
            else:
                self.historial[-1] = (nombre, kwargs)

    def volver(self):
        """Vuelve a la pantalla anterior del historial."""
        if len(self.historial) <= 1:
            return
        self.historial.pop()  # descarta la pantalla actual
        nombre, kwargs = self.historial[-1]
        self.historial.pop()  # se vuelve a agregar dentro de mostrar_pantalla
        self.mostrar_pantalla(nombre, **kwargs)

    # ------------------------------------------------------------------
    # SESIÓN
    # ------------------------------------------------------------------
    def iniciar_sesion(self, usuario_obj, turno_id=None):
        self.usuario_actual = usuario_obj
        self.turno_actual = turno_id
        self.historial = []

        if usuario_obj.rol in ("Cajero", "Supervisor"):
            self.mostrar_pantalla("pos", turno_actual=turno_id)
        elif usuario_obj.rol in ("Administrador", "Gerente General"):
            self.mostrar_pantalla("administracion")
        else:
            from tkinter import messagebox
            messagebox.showerror("Error", "Rol de usuario no reconocido.")

    def cerrar_sesion(self):
        self.usuario_actual = None
        self.turno_actual = None
        self.historial = []
        self.mostrar_pantalla("login")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
