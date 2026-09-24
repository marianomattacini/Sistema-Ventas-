import customtkinter as ctk
from tkinter import messagebox
from models.configuracion import Configuracion
from views.base_frame import BaseFrame

class FrameConfiguracion(BaseFrame):
    def __init__(self, parent, controller, usuario_actual, **kwargs):
        super().__init__(parent, controller, usuario_actual)

        self.configure(fg_color="#F4F6F9")

        self._crear_widgets()

    def _crear_widgets(self):
        frame = ctk.CTkFrame(self, fg_color="#F9FAFB", corner_radius=15, border_width=1, border_color="#B8C1CE")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="⚙️ Configuración del Sistema", 
                    font=("Roboto", 20, "bold"), text_color="#1D4ED8"
        ).pack(pady=(20, 10))

        self.entradas = {}
        configs = Configuracion.obtener_todos()
        campos = [
            ("IVA (%)", "iva"),
            ("Puntos por $100", "puntos_por_100"),
            ("Cuotas Máximas", "max_cuotas_predeterminado"),
            ("Tiempo Descanso (min)", "tiempo_descanso_min"),
        ]

        for etiqueta, clave in campos:
            ctk.CTkLabel(frame, text=f"{etiqueta}:", font=("Roboto", 13, "bold")
            ).pack(anchor="w", padx=40, pady=(10, 5))
            entrada = ctk.CTkEntry(frame, font=("Roboto", 13), height=35,
                                 fg_color="#D6DBE3", text_color="#1A2233")
            entrada.pack(fill="x", padx=40, pady=(0, 5))
            if clave in configs:
                entrada.insert(0, configs[clave])
            self.entradas[clave] = entrada

        frame_botones = ctk.CTkFrame(frame, fg_color="transparent")
        frame_botones.pack(fill="x", pady=30)

        def guardar():
            for clave, entrada in self.entradas.items():
                valor = entrada.get().strip()
                if not valor:
                    messagebox.showerror("Error", f"El campo {clave} no puede estar vacío.")
                    return
                Configuracion.guardar(clave, valor)
            messagebox.showinfo("Éxito", "✅ Configuración guardada correctamente.")
            self.controller.volver()

        btn_guardar = ctk.CTkButton(frame_botones, text="💾 Guardar", height=40,
                                  fg_color="#15803D", hover_color="#166534",
                                  corner_radius=10, command=guardar, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_guardar.pack(side="left", fill="x", expand=True, padx=5)

        btn_cancelar = ctk.CTkButton(frame_botones, text="Cancelar", height=40,
                                   fg_color="#64748B", hover_color="#D6DBE3",
                                   corner_radius=10, command=self.controller.volver, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_cancelar.pack(side="left", fill="x", expand=True, padx=5)
