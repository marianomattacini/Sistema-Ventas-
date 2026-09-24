import customtkinter as ctk
from tkinter import messagebox
from models.entidad_pago import EntidadPago
from views.base_frame import BaseFrame

# ~25 entidades ficticias de pago, agrupadas por tipo (ninguna es una marca real)
ENTIDADES_POR_TIPO = {
    "Banco": [
        "Banco Cuyo Sur", "Banco Andes Plata", "Banco Mendocino", "Banco del Oeste",
        "Banco Nueva Era", "Banco Vendimia", "Banco Confianza", "Banco Río Claro",
        "Banco Cordillera", "Banco Sol Naciente",
    ],
    "Entidad Financiera": [
        "Credicuyo Financiera", "Financiera El Sol", "Financiera Vendimia Plus",
        "Credimax Financiera", "Financiera Andina", "Financiera Confía",
        "Financiera Rápida Cash",
    ],
    "Billetera Virtual": [
        "PagoYa", "WalletCuyo", "QRPay Argentina", "MonedaDigital",
        "PagoFácil Virtual", "CyberPay", "BilleteraAndes", "InstantPay",
    ],
}
TIPOS = list(ENTIDADES_POR_TIPO.keys())


class FrameEntidadPago(BaseFrame):
    def __init__(self, parent, controller, usuario_actual, entidad_id=None, **kwargs):
        super().__init__(parent, controller, usuario_actual)
        self.entidad_id = entidad_id
        self.entidad = EntidadPago.obtener_por_id(entidad_id) if entidad_id else None

        self.configure(fg_color="#F4F6F9")

        self._crear_widgets()

    def _crear_widgets(self):
        # Frame con scroll
        frame_scroll = ctk.CTkScrollableFrame(self, fg_color="#F9FAFB", corner_radius=15)
        frame_scroll.pack(fill="both", expand=True, padx=20, pady=20)

        titulo = "Editar Entidad" if self.entidad else "Nueva Entidad"
        ctk.CTkLabel(frame_scroll, text=titulo, font=("Roboto", 20, "bold"), text_color="#1D4ED8"
        ).pack(pady=(20, 10))

        # --- Tipo (desplegable corto) ---
        ctk.CTkLabel(frame_scroll, text="Tipo:", font=("Roboto", 13, "bold")
        ).pack(anchor="w", padx=40, pady=(10, 5))
        tipo_inicial = self.entidad.tipo if self.entidad and self.entidad.tipo in TIPOS else TIPOS[0]
        self.combo_tipo = ctk.CTkOptionMenu(frame_scroll, values=TIPOS, width=200, height=35,
                                          font=("Roboto", 13), fg_color="#D6DBE3",
                                          text_color="#1A2233", button_color="#2563EB",
                                          corner_radius=10, command=self._on_cambio_tipo)
        self.combo_tipo.pack(anchor="w", padx=40, pady=(0, 10))
        self.combo_tipo.set(tipo_inicial)

        # --- Nombre (desplegable corto con las ~25 entidades ficticias) ---
        ctk.CTkLabel(frame_scroll, text="Entidad:", font=("Roboto", 13, "bold")
        ).pack(anchor="w", padx=40, pady=(10, 5))
        opciones_nombre = ENTIDADES_POR_TIPO[tipo_inicial]
        self.combo_nombre = ctk.CTkOptionMenu(frame_scroll, values=opciones_nombre, width=220, height=35,
                                            font=("Roboto", 13), fg_color="#D6DBE3",
                                            text_color="#1A2233", button_color="#2563EB",
                                            corner_radius=10)
        self.combo_nombre.pack(anchor="w", padx=40, pady=(0, 10))
        if self.entidad and self.entidad.nombre in opciones_nombre:
            self.combo_nombre.set(self.entidad.nombre)
        else:
            self.combo_nombre.set(opciones_nombre[0])

        # Checkbox: Acepta cuotas
        self.check_cuotas = ctk.CTkCheckBox(frame_scroll, text="Acepta cuotas", font=("Roboto", 13),
                                          fg_color="#15803D", hover_color="#166534", text_color="#1A2233")
        self.check_cuotas.pack(anchor="w", padx=40, pady=10)
        if self.entidad and self.entidad.cuotas_maximas > 0:
            self.check_cuotas.select()

        # Campo: Cuotas Máximas (se muestra solo si el checkbox está activado)
        self.frame_cuotas = ctk.CTkFrame(frame_scroll, fg_color="transparent")
        self.frame_cuotas.pack(fill="x", padx=40, pady=(0, 10))
        ctk.CTkLabel(self.frame_cuotas, text="Cuotas Máximas:", font=("Roboto", 13, "bold")
        ).pack(anchor="w", pady=(10, 5))
        self.entry_cuotas = ctk.CTkEntry(self.frame_cuotas, font=("Roboto", 13), height=35, width=100,
                                       fg_color="#D6DBE3", text_color="#1A2233")
        self.entry_cuotas.pack(anchor="w", pady=(0, 5))
        if self.entidad:
            self.entry_cuotas.insert(0, str(self.entidad.cuotas_maximas))
        else:
            self.entry_cuotas.insert(0, "12")

        ctk.CTkLabel(self.frame_cuotas, text="Cuotas sin interés:", font=("Roboto", 13, "bold")
        ).pack(anchor="w", pady=(10, 5))
        self.entry_cuotas_si = ctk.CTkEntry(self.frame_cuotas, font=("Roboto", 13), height=35, width=100,
                                          fg_color="#D6DBE3", text_color="#1A2233")
        self.entry_cuotas_si.pack(anchor="w", pady=(0, 5))
        self.entry_cuotas_si.insert(0, str(getattr(self.entidad, 'cuotas_sin_interes', 0) if self.entidad else 3))

        def toggle_cuotas():
            if self.check_cuotas.get():
                self.frame_cuotas.pack(fill="x", padx=40, pady=(0, 10))
            else:
                self.frame_cuotas.pack_forget()

        self.check_cuotas.configure(command=toggle_cuotas)
        if not self.check_cuotas.get():
            self.frame_cuotas.pack_forget()

        # --- Promoción: descuento % y descripción libre ---
        ctk.CTkLabel(frame_scroll, text="Descuento (%):", font=("Roboto", 13, "bold")
        ).pack(anchor="w", padx=40, pady=(10, 5))
        self.entry_descuento = ctk.CTkEntry(frame_scroll, font=("Roboto", 13), height=35, width=100,
                                          fg_color="#D6DBE3", text_color="#1A2233",
                                          placeholder_text="Ej: 10")
        self.entry_descuento.pack(anchor="w", padx=40, pady=(0, 10))
        if self.entidad and self.entidad.descuento_porcentaje:
            self.entry_descuento.insert(0, str(self.entidad.descuento_porcentaje))

        ctk.CTkLabel(frame_scroll, text="Descripción de la promoción (opcional):", font=("Roboto", 13, "bold")
        ).pack(anchor="w", padx=40, pady=(10, 5))
        self.entry_promo = ctk.CTkEntry(frame_scroll, font=("Roboto", 13), height=35,
                                      fg_color="#D6DBE3", text_color="#1A2233",
                                      placeholder_text="Ej: 10% los martes / 6 cuotas sin interés todos los días")
        self.entry_promo.pack(fill="x", padx=40, pady=(0, 10))
        if self.entidad and getattr(self.entidad, 'promocion_descripcion', ''):
            self.entry_promo.insert(0, self.entidad.promocion_descripcion)

        # Checkbox: Activa
        self.check_activa = ctk.CTkCheckBox(frame_scroll, text="Activa", font=("Roboto", 13),
                                          fg_color="#15803D", hover_color="#166534", text_color="#1A2233")
        self.check_activa.pack(anchor="w", padx=40, pady=10)
        if self.entidad and self.entidad.activa:
            self.check_activa.select()
        else:
            self.check_activa.select()  # Por defecto activa

        # Botones
        frame_botones = ctk.CTkFrame(frame_scroll, fg_color="transparent")
        frame_botones.pack(fill="x", pady=20)

        def guardar():
            try:
                tipo = self.combo_tipo.get()
                nombre = self.combo_nombre.get()

                cuotas_maximas = 0
                cuotas_sin_interes = 0
                if self.check_cuotas.get():
                    try:
                        cuotas_maximas = int(self.entry_cuotas.get().strip())
                        if cuotas_maximas < 1:
                            raise ValueError
                    except (TypeError, ValueError):
                        raise ValueError("Ingrese un número entero positivo para las cuotas máximas.")
                    try:
                        cuotas_sin_interes = int(self.entry_cuotas_si.get().strip() or 0)
                        if cuotas_sin_interes < 0 or cuotas_sin_interes > cuotas_maximas:
                            raise ValueError
                    except (TypeError, ValueError):
                        raise ValueError("Las cuotas sin interés deben ser un número entre 0 y las cuotas máximas.")

                descuento_texto = self.entry_descuento.get().strip()
                descuento = 0.0
                if descuento_texto:
                    try:
                        descuento = float(descuento_texto)
                        if descuento < 0 or descuento > 100:
                            raise ValueError
                    except (TypeError, ValueError):
                        raise ValueError("El descuento debe ser un número entre 0 y 100.")

                promocion_desc = self.entry_promo.get().strip()
                activa = self.check_activa.get()

                if self.entidad:
                    self.entidad.tipo = tipo
                    self.entidad.nombre = nombre
                    self.entidad.cuotas_maximas = cuotas_maximas
                    self.entidad.cuotas_sin_interes = cuotas_sin_interes
                    self.entidad.descuento_porcentaje = descuento
                    self.entidad.promocion_descripcion = promocion_desc
                    self.entidad.activa = activa
                    if self.entidad.guardar():
                        messagebox.showinfo("Éxito", "Entidad actualizada.")
                        self.controller.volver()
                    else:
                        messagebox.showerror("Error", "No se pudo actualizar.")
                else:
                    nueva = EntidadPago(
                        nombre=nombre,
                        tipo=tipo,
                        cuotas_maximas=cuotas_maximas,
                        activa=activa,
                        descuento_porcentaje=descuento,
                        cuotas_sin_interes=cuotas_sin_interes,
                        promocion_descripcion=promocion_desc
                    )
                    if nueva.guardar():
                        messagebox.showinfo("Éxito", "Entidad creada.")
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

    def _on_cambio_tipo(self, tipo):
        opciones = ENTIDADES_POR_TIPO.get(tipo, [])
        self.combo_nombre.configure(values=opciones)
        if opciones:
            self.combo_nombre.set(opciones[0])
