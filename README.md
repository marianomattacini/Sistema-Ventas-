# Sistema de Gestión de Ventas y Control de Stock

Aplicación de escritorio para la gestión integral de un supermercado: punto
de venta (POS), control de inventario, compras a proveedores, clientes,
promociones, turnos de caja y reportes gerenciales.

Desarrollado como Práctica Profesional 2 — Instituto Nuevo Cuyo.

## Arquitectura

El proyecto sigue el patrón **MVC (Modelo-Vista-Controlador)**:

```
main.py                 → punto de entrada
ui/                      → shell de la aplicación (ventana única, sidebar, header)
models/                  → Modelo: clases de negocio y persistencia (Producto, Venta,
                           Compra, Cliente, Proveedor, Usuario, Turno, Promoción, etc.)
views/                   → Vista: pantallas (CustomTkinter), solo se ocupan de dibujar
                           la interfaz y capturar la interacción del usuario
controllers/             → Controlador: coordina Vista y Modelo, contiene las reglas
                           de flujo de negocio (ej. VentaController, ProductoController,
                           CompraController)
database/                → configuración, migración y creación del esquema de base de datos.
                           database/base_datos.py contiene la clase BaseDatos, única
                           responsable de abrir conexiones SQLite y ejecutar sentencias
                           SQL (INSERT/SELECT/UPDATE/DELETE) en todo el proyecto.
utils/                   → generación de tickets y reportes en PDF
```

### Clase de Base de Datos

`database/base_datos.py` define la clase **`BaseDatos`**, encargada exclusivamente de:
1. la conexión a SQLite (`conectar()`), y
2. la ejecución de sentencias SQL: `consultar()` (SELECT), `insertar()` (INSERT),
   `actualizar()` (UPDATE) y `eliminar()` (DELETE).

```python
from database.config import get_base_datos

bd = get_base_datos()
filas = bd.consultar("SELECT * FROM productos WHERE estado = ?", ("Activo",))
nuevo_id = bd.insertar("INSERT INTO clientes (nombre) VALUES (?)", ("Juan Pérez",))
bd.actualizar("UPDATE productos SET stock_actual = ? WHERE codigo_barras = ?", (10, "123"))
bd.eliminar("DELETE FROM notificaciones WHERE id = ?", (5,))
```

Las clases de Vista (`views/`) **nunca** ejecutan SQL ni abren conexiones: siempre
piden los datos a una clase de Modelo (`models/`), y estas usan `BaseDatos` para
hablar con la base. Los modelos con operaciones simples de un solo statement
(`Rol`, `EntidadPago`, `Proveedor`, `Notificacion`, `Configuracion`, `Presupuesto`)
usan directamente `bd.consultar/insertar/actualizar/eliminar`. Los modelos con
transacciones de varios pasos (`Venta`, `Compra`, `Turno`) siguen usando la misma
conexión de `BaseDatos` pero controlan el commit/rollback manualmente, porque
necesitan que varias sentencias (por ejemplo, insertar una venta Y descontar
stock) se ejecuten como una única transacción atómica — si se hiciera con una
conexión nueva por cada sentencia, dos operaciones en simultáneo podrían chocar
y bloquear la base ("database is locked").

### Flujo de una venta exitosa (ejemplo de la lógica MVC)

```python
from controllers.venta_controller import VentaController

vc = VentaController()
vc.iniciar_venta(turno_id)                       # 1. abre la venta
vc.escanear_producto(codigo_barras, cantidad)     # 2. agrega ítems (valida stock)
vc.registrar_pago("Efectivo", monto)              # 3. registra pago(s) hasta cubrir el total
ticket = vc.confirmar_venta(usuario_autorizante)  # 4. descuenta stock, suma puntos,
                                                   #    notifica stock bajo y genera el ticket
```

Este es el mismo flujo que ejecuta `views/ventana_pos.py`: la vista nunca
manipula el Modelo directamente, siempre pasa por el Controlador.

## Requisitos técnicos cubiertos

- **POO**: todas las entidades del negocio son clases (`models/`).
- **Persistencia**: SQLite como base local (`supermercado.db`), con soporte
  opcional de PostgreSQL para datos bancarios de clientes.
- **GUI profesional**: CustomTkinter, tema claro (gris + azul corporativo), diseño responsivo.
- **Inventario (CRUD)**: alta/baja/modificación/consulta de productos,
  control de stock y precios de costo/venta, alertas de stock mínimo.
- **Facturación y ventas**: venta en tiempo real, emisión de ticket en PDF,
  descuento automático de stock al finalizar la venta.
- **Terceros**: CRUD de clientes (con historial e historial de puntos) y
  proveedores.
- **Abastecimiento**: ingreso formal de mercadería (compras), que
  incrementa el stock y registra el costo de adquisición.
- **Control de acceso**: login con roles (Gerente General, Cajero, etc.).
- **Validación y robustez**: validación de tipos de datos en formularios
  (controllers/producto_controller.py), manejo de excepciones en toda
  operación de base de datos, y un manejador global de errores
  (`App.report_callback_exception` en `ui/app.py`) que evita que un error
  inesperado cierre la aplicación: lo registra en `logs/errores.log` y
  avisa al usuario sin colgar el programa.
- **Distribución**: `SistemaVentas.spec` (PyInstaller) para generar un
  ejecutable `.exe` independiente.

## Funcionalidades adicionales (más allá de lo obligatorio)

- Promociones reales (3x2, descuento por cantidad, por producto o por
  categoría) que se calculan y descuentan del total a pagar automáticamente,
  y quedan reflejadas en el ticket.
- Pagos combinados: Efectivo (con cálculo de vuelto), Débito, Crédito (con
  cuotas e interés simulado) y QR / billetera virtual.
- Notificación automática al Gerente General cuando un producto queda con
  stock por debajo de su mínimo configurado.
- Dashboard gerencial: ingresos, egresos, ganancia bruta (margen real de
  productos vendidos) y utilidad neta por período, con exportación a PDF.
- Predicción de ventas (regresión Ridge) para el próximo trimestre.
- Sistema de turnos de caja con arqueo, sangrías y cierre.

## Cómo ejecutar

### Opción 1: doble clic (Windows, recomendado)

Doble clic en **`Iniciar Sistema de Ventas.bat`**. Abre la aplicación sin
consola visible y no requiere tener VSCode ni una terminal abierta.

> Si reinstalás Python o cambiás de versión, editá la ruta del intérprete
> dentro del `.bat` (clic derecho → Modificar).

### Opción 2: desde terminal

```bash
pip install -r requirements.txt --break-system-packages
python main.py
```

### Usuarios de prueba

Login por PIN (no usuario/contraseña tradicional):

| Usuario   | PIN    | Rol            |
|-----------|--------|----------------|
| `admin`   | `1234` | Gerente General |
| `cajero1` | `0000` | Cajero         |

Se crean automáticamente la primera vez que corre `database/setup_db.py`
(o al iniciar la app, si no existe la base). Si el login falla con una base
ya existente, corré `python actualizar_admin.py` para forzar el PIN del
usuario `admin`.

## Cómo generar el ejecutable

```bash
pyinstaller SistemaVentas.spec
```

El ejecutable queda en `dist/`.
# Sistema-Ventas-
