#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para convertir todas las ventanas CTkToplevel a CTkFrame
y unificar la navegación en una sola ventana.
"""

import os
import re
import shutil
from pathlib import Path

# Directorio donde están las vistas
VIEWS_DIR = Path(__file__).parent / "views"

# Clases que deben convertirse (todas las que heredan de CTkToplevel)
# Se identifican por la línea "class ...(ctk.CTkToplevel):"
# y se reemplaza por "class ...(ctk.CTkFrame):"

# También se debe modificar el constructor para que reciba (parent, controller, ...)
# y eliminar las configuraciones de ventana.

# Patrón para detectar clases CTkToplevel
CLASS_PATTERN = re.compile(r'^class\s+(\w+)\(ctk\.CTkToplevel\):', re.MULTILINE)

# Patrón para encontrar el __init__ y cambiar la firma
INIT_PATTERN = re.compile(r'def __init__\(self,\s*(.*?)\):', re.DOTALL)

# Lista de configuraciones de ventana a eliminar
WINDOW_CONFIGS = [
    r'self\.title\([^)]*\)',
    r'self\.geometry\([^)]*\)',
    r'self\.resizable\([^,]*,\s*[^)]*\)',
    r'self\.transient\([^)]*\)',
    r'self\.grab_set\(\)',
    r'self\.lift\(\)',
    r'self\.focus_force\(\)',
    r'self\.attributes\([^)]*\)',
    r'self\.after\([^)]*\)',
    r'self\._centrar_ventana\(\)',
]

# Métodos a eliminar (llamadas a _centrar_ventana)
CENTER_CALL = re.compile(r'self\._centrar_ventana\(\)')

# Patrón para el botón "Volver" que usa self.destroy
VOLVER_PATTERN = re.compile(r'command=(?:self\.destroy|self\.master\.destroy)')

# Reemplazo para el botón Volver
VOLVER_REPLACE = 'command=self.controller.volver_al_menu'

def convertir_archivo(filepath):
    """Convierte un archivo de ventana de CTkToplevel a CTkFrame."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # 1. Cambiar herencia
    content = CLASS_PATTERN.sub(r'class \1(ctk.CTkFrame):', content)

    # 2. Cambiar firma del __init__ (si existe)
    def cambiar_init(match):
        params = match.group(1).strip()
        # Si ya tiene 'parent, controller' no se modifica, pero asumimos que no
        # Reemplazar la firma actual por una que incluya parent, controller
        # Buscar si tiene 'master=None' o 'usuario_actual, master=None'
        if 'master=' in params:
            # Quitar master y agregar parent, controller
            new_params = params.replace('master=None', '').replace('master', '')
            # Limpiar comas sobrantes
            new_params = re.sub(r',\s*,', ',', new_params)
            new_params = re.sub(r'^\s*,\s*', '', new_params)
            new_params = re.sub(r'\s*,\s*$', '', new_params)
            if new_params:
                new_params = f'parent, controller, {new_params}'
            else:
                new_params = 'parent, controller'
        else:
            # Si no tiene master, agregamos parent, controller al inicio
            if params:
                new_params = f'parent, controller, {params}'
            else:
                new_params = 'parent, controller'
        return f'def __init__(self, {new_params}):'

    content = INIT_PATTERN.sub(cambiar_init, content)

    # 3. Eliminar llamadas a super().__init__(master) -> super().__init__(parent)
    content = re.sub(r'super\(\)\.__init__\(master\)', 'super().__init__(parent)', content)
    content = re.sub(r'super\(\)\.__init__\(self\.master\)', 'super().__init__(parent)', content)
    content = re.sub(r'CTkToplevel\.__init__\(self,\s*master\)', 'CTkFrame.__init__(self, parent)', content)

    # 4. Eliminar configuraciones de ventana (title, geometry, etc.)
    for pattern in WINDOW_CONFIGS:
        content = re.sub(pattern, '', content)

    # 5. Eliminar llamadas a _centrar_ventana
    content = CENTER_CALL.sub('', content)

    # 6. Reemplazar self.destroy() en botones "Volver"
    # Buscar la línea que contiene el botón Volver y reemplazar su command
    # Haremos un reemplazo más general: command=self.destroy -> command=self.controller.volver_al_menu
    content = re.sub(r'command=(?:self\.destroy|self\.master\.destroy)', 'command=self.controller.volver_al_menu', content)

    # 7. Reemplazar self.destroy() en otros lugares (ej. en permisos denegados)
    # Pero solo cuando se usa para cerrar la ventana, lo cambiaremos por controller.volver_al_menu()
    # Pero cuidado, no queremos cambiar los destroy de diálogos modales (que son CTkToplevel)
    # Para simplificar, reemplazaremos self.destroy() dentro de la clase pero no en métodos que sean diálogos.
    # Usaremos una heurística: reemplazar self.destroy() si no está dentro de un método que sea un diálogo
    # (ej. _formulario_*, _crear_*_dialog). Como es complicado, dejamos que el usuario revise.
    # Mejor haremos un reemplazo selectivo: solo en los casos de permisos denegados y en el botón volver.
    # El botón volver ya fue tratado.
    # En las verificaciones de permisos, se usa self.destroy() después de messagebox.
    # Los reemplazaremos por self.controller.volver_al_menu()
    content = re.sub(r'self\.destroy\(\)\s*return', 'self.controller.volver_al_menu(); return', content)
    # También cuando se usa self.destroy() solo, pero no en diálogos, es arriesgado.
    # Por ahora solo los casos anteriores.

    # 8. Ajustar referencias a master: self.master -> self.controller (o self)
    # Por ejemplo, en los diálogos modales se usa self.master, pero esos son CTkToplevel, no se tocan.
    # En la ventana principal, a veces se usa self.master para referirse a la ventana padre, ahora es self.controller.
    # Reemplazar self.master por self.controller (con cuidado)
    content = re.sub(r'self\.master\.', 'self.controller.', content)

    # 9. Eliminar el método _centrar_ventana si existe
    content = re.sub(r'def _centrar_ventana\(self\):.*?(?=\n    def |\nclass |\Z)', '', content, flags=re.DOTALL)

    # Guardar solo si hubo cambios
    if content != original:
        # Hacer backup
        backup = filepath.with_suffix(filepath.suffix + '.bak')
        shutil.copy(filepath, backup)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Convertido: {filepath.name}")
        return True
    else:
        print(f"⏭️ Sin cambios: {filepath.name}")
        return False

def main():
    if not VIEWS_DIR.exists():
        print(f"❌ El directorio {VIEWS_DIR} no existe.")
        return

    for filepath in VIEWS_DIR.glob("ventana_*.py"):
        if filepath.name in ["ventana_login.py", "ventana_administracion.py"]:
            # Estas ya son CTkFrame, pero podemos revisar que tengan el constructor correcto
            # Asegurar que reciban parent, controller
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'def __init__(self, parent, controller' not in content:
                # Intentar corregir
                # Para ventana_login ya está bien, para administración también.
                pass
            continue
        convertir_archivo(filepath)

    print("\n🎉 Conversión completada. Revisa los archivos y reemplaza tu main.py con el nuevo.")

if __name__ == "__main__":
    main()