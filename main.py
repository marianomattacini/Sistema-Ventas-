#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sistema de Gestión de Ventas y Control de Stock
Punto de entrada principal de la aplicación.
"""

import sys
import os

# Agregar la raíz del proyecto al path para importaciones
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import App

if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        # Red de seguridad para errores fatales ANTES de que exista la
        # ventana principal (ej. falla al inicializar la base de datos).
        # Sin esto, en un .exe compilado la app se cerraría sin dar ninguna
        # pista de qué pasó.
        import traceback
        from datetime import datetime

        detalle = traceback.format_exc()
        print("❌ Error fatal al iniciar la aplicación:\n", detalle)
        try:
            log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, "errores.log"), "a", encoding="utf-8") as f:
                f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR FATAL DE ARRANQUE\n{detalle}\n")
        except Exception:
            pass
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Error al iniciar", f"No se pudo iniciar la aplicación:\n\n{e}")
        except Exception:
            pass
        sys.exit(1)


"""
Args: 

Aca se realiza la ejecución del programa principal, creando una instancia de la clase App y ejecutando el bucle
principal de la interfaz gráfica. Se realiza la conexion con la base de datos y se inicializan los componentes de la 
interfaz de usuario, utilizando la arquitectura MVC para separar la lógica de negocio de la presentación.
La aquitectura MVC significa Modelo-Vista-Controlador, donde el Modelo representa la lógica de negocio y los datos, 
la Vista representa la interfaz de usuario y el Controlador maneja la interacción entre el Modelo y la Vista. 
Se utiliza la arquitectura MVC para organizar el código de manera más clara y mantener una separación de responsabilidades.
Los metodos y funciones utilizadas en este programa son: 
- `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))`: Agrega la raíz del proyecto al path para permitir 
importaciones de módulos desde cualquier parte del proyecto.
- `from ui.app import App`: Importa la clase App desde el módulo ui.app, que es la clase principal de la aplicación.
- `if __name__ == "__main__":`: Verifica si el script se está ejecutando directamente y no importado como módulo.
- `app = App()`: Crea una instancia de la clase App, que inicializa la interfaz gráfica y la lógica de negocio.
- `app.mainloop()`: Ejecuta el bucle principal de la interfaz gráfica.

Glosario de términos:
- **MVC (Modelo-Vista-Controlador)**: Patrón de diseño que separa la lógica de negocio (Modelo), la presentación (Vista) y 
la interacción del usuario (Controlador) en una aplicación.
- **Interfaz gráfica**: Conjunto de elementos visuales que permiten al usuario interactuar con la aplicación. Se ha utilizado 
la librería Tkinter para crear la interfaz gráfica de la aplicación.
- **Base de datos**: Sistema de almacenamiento de datos que permite guardar y recuperar información de manera estructurada. Se ha 
utilizado SQLite como base de datos para almacenar la información de ventas y stock y postgresql para la base de datos de usuarios
y roles.
- **Lógica de negocio**: Conjunto de reglas y procesos que definen cómo funciona la aplicación y cómo se manejan los datos.
- **Separación de responsabilidades**: Principio de diseño que consiste en dividir un sistema en partes que tienen
funciones específicas y no se mezclan entre sí, lo que facilita el mantenimiento y la escalabilidad del código.
- **Importación de módulos**: Proceso de incluir código de otros archivos o bibliotecas en un programa para reutilizar
funciones y clases.

`sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))`: Significa que se está agregando la ruta del directorio donde 
se encuentra el archivo principal (main.py) al inicio de la lista de rutas de búsqueda de módulos de Python. Esto permite que los 
módulos y paquetes ubicados en el mismo directorio o en subdirectorios puedan ser importados sin necesidad de especificar rutas 
relativas complicadas.

`from ui.app import App`: Significa que se esta importando la clase App desde el módulo ui.app. Esto significa que se est&aacute; 
importando la clase principal de la aplicaci&oacute;n que se encuentra en el archivo app.py en el directorio ui.

`if __name__ == "__main__":`: Significa que se est&aacute; verificando si el archivo main.py se est&aacute; ejecutando directamente 
como el archivo principal de la aplicaci&oacute;n. Si se est&aacute; ejecutando directamente, se crear&aacute; una instancia de la 
clase App y se ejecutar&aacute; el bucle principal de la interfaz gr&aacute;fica.

`app = App()`: Significa que se est&aacute; creando una instancia de la clase App. Esto significa que se est&aacute; creando una 
interfaz gr&aacute;fica de usuario y una l&oacute;gica de negocio para la aplicaci&oacute;n.

`app.mainloop()`: Significa que se est&aacute; ejecutando el bucle principal de la interfaz gr&aacute;fica. Esto significa que se 
est&aacute; mostrando la interfaz gr&aacute;fica y se est&aacute; esperando a que el usuario interact&uacute;e con ella.

En sintesis, para lograr la funcionalidad del proyecto, se utiliza la arquitectura MVC para separar la l&oacute;gica de negocio
de la presentaci&oacute;n, permitiendo que la l&oacute;gica de negocio se encargue de la l&oacute;gica de negocio y la presentaci&oacute;n
se encargue de la presentaci&oacute;n. Adem&aacute;s, se utiliza la librer&iacute;a Tkinter para crear la interfaz gr&aacute;fica de usuario.   

Para poder realizar modificaciones se deberán realizar las siguientes acciones:

1. Crear un nuevo archivo en la carpeta `controllers` con el nombre del controlador y la extensi&oacute;n `.py`.
2. Crear una nueva clase en el archivo del controlador con el nombre del controlador.
3. Definir la l&oacute;gica de negocio en la clase del controlador.
4. Importar la clase del controlador en el archivo `main.py`.
5. Crear un nuevo archivo en la carpeta `views` con el nombre de la vista y la extensi&oacute;n `.py`.
6. Crear una nueva clase en el archivo de la vista con el nombre de la vista.
7. Definir la l&oacute;gica de presentaci&oacute;n en la clase de la vista.
8. Importar la clase de la vista en el archivo `main.py`.
9. Crear un nuevo archivo en la carpeta `models` con el nombre del modelo y la extensi&oacute;n `.py`.
10. Crear una nueva clase en el archivo del modelo con el nombre del modelo.
11. Definir la l&oacute;gica de datos en la clase del modelo.
12. Importar la clase del modelo en el archivo `main.py`.

Para la realizacion de la documentacion se utilizo la libreria `Sphinx` con la version 5.3.0.

"""