# Refactor: Ventana Única + Navegación con Sidebar

## Qué cambió

Antes, cada pantalla (`ventana_administracion.py`, `ventana_productos.py`,
`ventana_clientes.py`, etc.) era una **ventana propia** (`ctk.CTkToplevel`)
que se abría encima de las demás. Resultado: varias ventanas abiertas al
mismo tiempo, sin forma consistente de "volver atrás".

Ahora la aplicación entera vive en **una sola ventana** (`ui/app.py` → clase
`App`), con:

- **Sidebar fijo a la izquierda** (`ui/sidebar.py`): arma el menú según el
  rol/permisos del usuario logueado (usando `usuario.tiene_permiso(...)`) y
  resalta la sección activa.
- **Header fijo arriba** (`ui/header.py`): botón **← Volver**, título de la
  pantalla actual y usuario logueado.
- **Contenedor central**: ahí se monta el *Frame* de la pantalla activa.
- **Paleta unificada** (`ui/theme.py`): formalicé los colores que ya usaba el
  proyecto (slate + celeste/sky) para que se apliquen igual en todas las
  pantallas, más helpers (`boton_primario`, `card`, `entry`, etc.) para no
  repetir estilos sueltos a futuro.

## Cómo funciona la navegación

Cada pantalla vieja (`views/ventana_X.py`) pasó de ser una ventana
(`ctk.CTkToplevel`) a ser un **Frame** (`views/base_frame.py` → `BaseFrame`)
que se monta y desmonta dentro de la ventana única. La navegación entre
pantallas se hace siempre a través del `controller` (la instancia de `App`)
que cada Frame recibe:

```python
self.controller.mostrar_pantalla("productos")   # ir a una pantalla
self.controller.volver()                         # volver a la anterior
self.controller.cerrar_sesion()                   # cerrar sesión y volver al login
```

`App` mantiene un historial de navegación (pila) para que "Volver" siempre
funcione, sin importar desde qué pantalla se entró.

## Pantallas y permisos del sidebar

| Pantalla         | Permiso requerido       |
|------------------|--------------------------|
| Punto de Venta   | (según rol: Cajero/Supervisor) |
| Panel Principal  | `gestionar_usuarios`     |
| Productos        | `gestionar_productos`    |
| Clientes         | `gestionar_clientes`     |
| Proveedores      | `gestionar_proveedores`  |
| Compras          | `gestionar_compras`      |
| Turnos           | `ver_reportes_basicos`   |
| Panel del Gerente / Empleados / Presupuestos / Entidad de Pago | `ver_balances` (Gerente General) |
| Usuarios         | `gestionar_usuarios`     |
| Configuración    | `ver_balances` (Gerente General) |

Cada pantalla también mantiene su verificación de permiso interna (defensa
en profundidad): si alguien llega igual sin permiso, se muestra el error y
se vuelve atrás en vez de cerrar la aplicación entera (que era lo que pasaba
antes con `self.destroy()` en la ventana raíz).

## Qué NO cambié

- Los **diálogos modales internos** (crear/editar un producto, crear un rol,
  ver el detalle de una venta, etc.) siguen siendo `ctk.CTkToplevel` — son
  ventanitas de verdad, transitorias, no pantallas de navegación. Solo
  corregí `dialog.transient(self)` → `dialog.transient(self.winfo_toplevel())`
  en los que quedaron colgando de un Frame en vez de la ventana real, porque
  Tk exige que el argumento de `transient()` sea una ventana de nivel
  superior.
- La lógica de negocio de cada pantalla (consultas SQL, cálculos, validaciones)
  no se tocó.

## Archivos nuevos

- `ui/theme.py` — paleta y helpers de estilo.
- `ui/sidebar.py` — menú lateral.
- `ui/header.py` — barra superior con volver.
- `ui/app.py` — ventana única + controlador de navegación.
- `views/base_frame.py` — clase base de todas las pantallas.

## Archivos modificados

`main.py` y los 14 `views/ventana_*.py` (ahora exportan clases `FrameX` en
vez de `VentanaX`, aunque mantuve el nombre de archivo para no romper otras
referencias).

## Falta agregar a requirements.txt

Detecté que `bcrypt` se usa en `models/usuario.py` pero no estaba en
`requirements.txt` — lo agregué.

## Verificación hecha

- Los 20 archivos Python compilan sin errores (`py_compile`).
- Se probó el arranque de la app completa en un entorno headless (Xvfb):
  levanta la ventana única y muestra el login sin excepciones.
- **No pude probar el flujo completo de login → POS/Administración** porque
  este entorno no tiene acceso a tu base PostgreSQL ni a tu `.env`. Te
  recomiendo probarlo en tu máquina antes de compilar el `.exe` con
  PyInstaller.
