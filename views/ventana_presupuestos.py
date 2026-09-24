import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from models.presupuesto import Presupuesto
from views.base_frame import BaseFrame

MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]
CATEGORIAS = ["Impuestos", "Seguros", "Indemnizaciones", "Alquiler", "Servicios", "Publicidad", "Otro"]

class FramePresupuestos(BaseFrame):
    def __init__(self, parent, controller, usuario_actual, presupuesto_id=None, **kwargs):
        super().__init__(parent, controller, usuario_actual)
        self.presupuesto_id = presupuesto_id
        self.presupuesto = Presupuesto.obtener_por_id(presupuesto_id) if presupuesto_id else None

        self.configure(fg_color="#F4F6F9")

        self._crear_widgets()

    def _crear_widgets(self):
        frame = ctk.CTkFrame(self, fg_color="#F9FAFB", corner_radius=15, border_width=1, border_color="#B8C1CE")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        titulo = "Editar Presupuesto" if self.presupuesto else "Nuevo Presupuesto"
        ctk.CTkLabel(frame, text=titulo, font=("Roboto", 20, "bold"), text_color="#1D4ED8"
        ).pack(pady=(20, 10))

        # --- Categoría (desplegable, corto) ---
        ctk.CTkLabel(frame, text="Categoría:", font=("Roboto", 13, "bold")
        ).pack(anchor="w", padx=40, pady=(10, 5))
        categoria_actual = getattr(self.presupuesto, 'categoria', None) if self.presupuesto else None
        combo_categoria = ctk.CTkOptionMenu(frame, values=CATEGORIAS, width=200, height=35,
                                           font=("Roboto", 13), fg_color="#D6DBE3",
                                           text_color="#1A2233", button_color="#2563EB",
                                           corner_radius=10)
        combo_categoria.pack(anchor="w", padx=40, pady=(0, 5))
        combo_categoria.set(categoria_actual if categoria_actual in CATEGORIAS else CATEGORIAS[0])

        # --- Monto planificado (único campo manual) ---
        ctk.CTkLabel(frame, text="Monto Planificado:", font=("Roboto", 13, "bold")
        ).pack(anchor="w", padx=40, pady=(10, 5))
        entry_monto = ctk.CTkEntry(frame, font=("Roboto", 13), height=35, width=200,
                                  fg_color="#D6DBE3", text_color="#1A2233",
                                  placeholder_text="Ej: 150000")
        entry_monto.pack(anchor="w", padx=40, pady=(0, 5))
        if self.presupuesto and self.presupuesto.monto_planificado:
            entry_monto.insert(0, str(self.presupuesto.monto_planificado))

        # --- Mes (desplegable, corto) ---
        ctk.CTkLabel(frame, text="Mes:", font=("Roboto", 13, "bold")
        ).pack(anchor="w", padx=40, pady=(10, 5))
        mes_actual = getattr(self.presupuesto, 'mes', None) if self.presupuesto else datetime.now().month
        combo_mes = ctk.CTkOptionMenu(frame, values=MESES, width=140, height=35,
                                     font=("Roboto", 13), fg_color="#D6DBE3",
                                     text_color="#1A2233", button_color="#2563EB",
                                     corner_radius=10)
        combo_mes.pack(anchor="w", padx=40, pady=(0, 5))
        try:
            combo_mes.set(MESES[int(mes_actual) - 1])
        except (TypeError, ValueError, IndexError):
            combo_mes.set(MESES[datetime.now().month - 1])

        # --- Año (desplegable, corto) ---
        ctk.CTkLabel(frame, text="Año:", font=("Roboto", 13, "bold")
        ).pack(anchor="w", padx=40, pady=(10, 5))
        anio_hoy = datetime.now().year
        anios_disponibles = [str(a) for a in range(anio_hoy - 1, anio_hoy + 4)]
        anio_actual = getattr(self.presupuesto, 'anio', None) if self.presupuesto else anio_hoy
        combo_anio = ctk.CTkOptionMenu(frame, values=anios_disponibles, width=100, height=35,
                                      font=("Roboto", 13), fg_color="#D6DBE3",
                                      text_color="#1A2233", button_color="#2563EB",
                                      corner_radius=10)
        combo_anio.pack(anchor="w", padx=40, pady=(0, 5))
        combo_anio.set(str(anio_actual) if str(anio_actual) in anios_disponibles else str(anio_hoy))

        frame_botones = ctk.CTkFrame(frame, fg_color="transparent")
        frame_botones.pack(fill="x", pady=20)

        def guardar():
            try:
                categoria = combo_categoria.get()
                mes = MESES.index(combo_mes.get()) + 1
                anio = int(combo_anio.get())

                monto_texto = entry_monto.get().strip()
                if not monto_texto:
                    raise ValueError("El monto planificado es obligatorio.")
                try:
                    monto = float(monto_texto)
                except ValueError:
                    raise ValueError("El monto planificado debe ser un número.")
                if monto <= 0:
                    raise ValueError("El monto planificado debe ser mayor a cero.")

                if self.presupuesto:
                    self.presupuesto.categoria = categoria
                    self.presupuesto.monto_planificado = monto
                    self.presupuesto.mes = mes
                    self.presupuesto.anio = anio
                    if self.presupuesto.guardar():
                        messagebox.showinfo("Éxito", "Presupuesto actualizado.")
                        self.controller.volver()
                    else:
                        messagebox.showerror("Error", "No se pudo actualizar.")
                else:
                    nuevo = Presupuesto(
                        categoria=categoria,
                        monto_planificado=monto,
                        mes=mes,
                        anio=anio
                    )
                    if nuevo.guardar():
                        messagebox.showinfo("Éxito", "Presupuesto creado.")
                        self.controller.volver()
                    else:
                        messagebox.showerror("Error", "No se pudo crear.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        btn_guardar = ctk.CTkButton(frame_botones, text="💾 Guardar", height=40,
                                  fg_color="#15803D", hover_color="#166534",
                                  corner_radius=10, command=guardar, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_guardar.pack(side="left", fill="x", expand=True, padx=5)

        btn_cancelar = ctk.CTkButton(frame_botones, text="Cancelar", height=40,
                                   fg_color="#64748B", hover_color="#D6DBE3",
                                   corner_radius=10, command=self.controller.volver, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_cancelar.pack(side="left", fill="x", expand=True, padx=5)