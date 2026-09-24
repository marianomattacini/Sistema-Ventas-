# Especificación del Sistema de Gestión de Ventas y Control de Stock

## 1. Objetivo del Sistema
Desarrollar una aplicación de escritorio profesional para la automatización de procesos comerciales y control de inventario, permitiendo gestionar ventas, productos, clientes, proveedores, compras y usuarios con roles diferenciados. El sistema debe garantizar integridad de datos, seguridad y una interfaz intuitiva.

---

## 2. Actores del Sistema

| Actor | Descripción |
|-------|-------------|
| **Cajero** | Opera el punto de venta (POS). Realiza ventas, cobros, pausa de tickets y gestión de su propio turno. |
| **Supervisor** | Hereda todas las funciones del Cajero. Además, puede anular pedidos, forzar cierre de turnos, autorizar sangrías y ver reportes básicos de ventas. |
| **Administrador** | Hereda todas las funciones del Supervisor. Además, gestiona productos (CRUD), clientes, proveedores, compras (abastecimiento), usuarios del sistema y reportes avanzados. |
| **Gerente General** | Hereda todas las funciones del Administrador. Además, puede desbloquear usuarios bloqueados, gestionar configuraciones de seguridad y acceder a auditoría completa del sistema. |

---

## 3. Módulos Funcionales

### 3.1. Módulo de Autenticación y Control de Acceso
- Login con **usuario** (único) y **PIN numérico**.
- Verificación de estado del usuario (Activo, Inactivo, Bloqueado).
- Bloqueo automático tras **3 intentos fallidos** de PIN. Solo el Gerente General puede desbloquear.
- Registro de intentos fallidos en log de auditoría.

### 3.2. Módulo de Gestión de Usuarios (Solo Administrador y Gerente)
- CRUD de usuarios (altas, bajas, modificaciones, consultas).
- Asignación de roles: Cajero, Supervisor, Administrador, Gerente General.
- Cambio de estado (Activo, Inactivo, Bloqueado).
- Reseteo de PIN.

### 3.3. Módulo de Inventario (CRUD de Productos)
- Altas, bajas, modificaciones y consultas de productos.
- Campos obligatorios: código de barras (único), nombre, categoría, precio de venta, stock actual, stock mínimo, tipo de garantía (ej. comestible, electrónico).
- Control de existencias con alerta visual cuando stock_actual <= stock_minimo.
- Precio de costo para control interno.

### 3.4. Módulo de Gestión de Terceros
- **Clientes:** CRUD con DNI/CUIL (único), nombre, contacto, historial de compras, puntos acumulados.
- **Proveedores:** CRUD con CUIT (único), razón social, teléfono, email, estado.

### 3.5. Módulo de Abastecimiento (Compras)
- Registro de compras a proveedores: factura, fecha, total, productos, cantidades, precio costo.
- Incremento automático del stock de productos al confirmar la compra.
- Control de costos de adquisición.

### 3.6. Módulo de Facturación y Ventas (POS)
- **Carrito de compras:** Agregar productos por código de barras (lectura automática o manual), con verificación de stock > 0.
- **Pagos mixtos:** El cliente puede abonar con efectivo, débito, crédito o transferencia (Mercado Pago / bancaria). El sistema permite combinar métodos hasta cubrir el total.
- **Cobro con débito:** Conexión a PostgreSQL para validar fondos y estado de cuenta.
- **Cobro con crédito:** Selector de cuotas (1 a 12). El sistema debe informar si la tarjeta tiene promociones (sin interés) o si aplica interés según las cuotas elegidas.
- **Pago en efectivo:** Validación de que el monto ingresado sea >= total. Cálculo automático del vuelto.
- **Transferencia:** Se registra el pago como "pendiente de confirmación" o se solicita comprobante manual.
- **Descuento de stock en tiempo real:** Al finalizar la venta, se descuenta el stock de cada producto.
- **Generación de ticket:** Emisión de comprobante legible (pantalla y opción de impresión/PDF).
- **Pausa de ticket:** El cajero puede guardar un carrito en estado "Pausado" para atender a otro cliente, y retomarlo después.

### 3.7. Módulo de Turnos y Caja
- Apertura de turno con declaración de fondo inicial.
- Cierre de turno con cálculo automático de ventas totales por método de pago.
- **Sangrías:** Retiro de efectivo durante el turno, autorizado por Supervisor (registro de monto, responsable, motivo).
- **Cierre forzado:** Si un cajero deja un turno abierto sin cerrar, el Supervisor puede forzar el cierre con su PIN.
- **Control de descansos:** El cajero puede pausar su sesión (cortina de bloqueo) y reanudar con su PIN.

### 3.8. Módulo de Seguridad y Auditoría
- Registro de todos los movimientos críticos: ventas, anulaciones, sangrías, bloqueos, cambios de stock, modificaciones de productos y usuarios.
- Inmutabilidad de operadores: los usuarios desactivados no se eliminan físicamente; su estado cambia a "Inactivo" y permanecen visibles en los listados administrativos.
- Anulación de pedidos solo con PIN de Supervisor.
- Cortina de bloqueo al pausar sesión (oculta información financiera).

### 3.9. Módulo de Fidelización (Puntos)
- El cajero puede registrar el DNI del cliente (opcional) al inicio de la venta.
- Al finalizar la compra, el sistema calcula puntos automáticamente (ej. 1 punto por cada $100) y los acumula en el perfil del cliente.
- El cajero puede consultar los puntos acumulados de un cliente.

### 3.10. Módulo de Cupones de Devolución
- Generación de cupones alfanuméricos únicos al realizar una devolución.
- Validación de cupón al momento de aplicarlo en una venta: debe estar vigente, no vencido y con estado "Pendiente".
- Cambio de estado a "Usado" después de su aplicación.

---

## 4. Flujos Principales (Happy Path)

### 4.1. Flujo de Venta Exitosa
1. El Cajero inicia sesión con su usuario y PIN.
2. Abre su turno de caja declarando el fondo inicial.
3. El cliente presenta productos.
4. El Cajero escanea cada producto por código de barras. Si no lee, puede ingresar el código manualmente o buscar por nombre.
5. El sistema muestra el producto, cantidad y precio. Verifica stock > 0. Si stock = 0, el Cajero puede llamar al Supervisor para autorizar una carga manual excepcional (1 unidad).
6. Si el cliente tiene DNI, el Cajero lo ingresa para acumular puntos.
7. Al finalizar la carga de productos, el Cajero selecciona el método de pago:
   - **Efectivo:** Ingresa el monto recibido. El sistema calcula el vuelto.
   - **Débito:** Solicita tarjeta y PIN. El sistema valida fondos y estado en PostgreSQL.
   - **Crédito:** Solicita cantidad de cuotas (1 a 12). El sistema muestra si hay promociones (sin interés) o si aplica interés según las cuotas.
   - **Transferencia (Mercado Pago / bancaria):** Se registra el pago, se puede solicitar comprobante manual.
8. Si el pago no cubre el total, el sistema permite pagar el saldo restante con otro método (pago mixto).
9. Cuando el saldo restante es 0, el sistema:
   - Descuenta el stock de cada producto vendido.
   - Genera un ticket con el detalle de la compra.
   - Suma puntos al cliente (si se registró DNI).
10. El Cajero entrega el ticket y el vuelto (si corresponde) al cliente.
11. El carrito se vacía y queda listo para el siguiente cliente.

### 4.2. Flujo de Pausa de Ticket
1. El Cajero tiene un carrito activo.
2. Un cliente debe ausentarse temporalmente.
3. El Cajero presiona "Pausar Ticket".
4. El sistema guarda el carrito en estado "Pausado" en la base de datos.
5. El Cajero atiende al siguiente cliente.
6. Cuando el cliente regresa, el Cajero recupera el ticket pausado y continúa la venta.

---

## 5. Flujos Alternativos (Sad Path)

| Escenario | Comportamiento del Sistema |
|-----------|----------------------------|
| Producto sin stock | Alerta visual: "Stock agotado". No se agrega al carrito. El Cajero puede llamar al Supervisor para autorizar carga manual excepcional. |
| Código de barras inexistente | Mensaje: "Producto no encontrado". |
| Fondos insuficientes en débito | Rechaza el pago. Mensaje: "Fondos insuficientes o cuenta inactiva". |
| Límite de crédito excedido | Rechaza el pago. Mensaje: "Límite de crédito excedido". |
| Anulación de pedido sin Supervisor | El Cajero intenta anular, pero el sistema exige PIN de Supervisor. Si falla, la anulación se aborta. |
| Turno colgado (sin cerrar) | Al intentar abrir un nuevo turno, el sistema detecta el turno abierto de otro operador. Solicita PIN de Supervisor para forzar el cierre. |
| Pago en efectivo con monto insuficiente | Rechaza el pago. Mensaje: "El monto ingresado es menor al total. Ingrese un monto mayor o igual." |
| Cierre de turno con inconsistencia de fondos | El sistema muestra una alerta: "Diferencia de caja detectada. Verifique el arqueo." |
| Conexión a PostgreSQL caída | El sistema permite pagos en efectivo y transferencias. Los pagos con tarjeta quedan inhabilitados. Se muestra mensaje de error de conexión. |
| 3 intentos fallidos de PIN | El usuario queda "Bloqueado". Solo el Gerente General puede desbloquear. Se registra el evento en el log. |
| Carga manual de producto (por error de código) | Si el Cajero escribe mal el código o nombre, el sistema muestra "Producto no encontrado". |
| Transferencia sin confirmación | El pago se registra como "Pendiente". Se solicita comprobante manual al cliente. |

---

## 6. Requisitos No Funcionales

| Área | Requisito |
|------|-----------|
| **Seguridad** | - PINs almacenados con hash (no texto plano).<br>- Roles con permisos estrictos.<br>- Registro de intentos fallidos de login.<br>- Bloqueo tras 3 intentos fallidos (solo Gerente desbloquea). |
| **Rendimiento** | - Carga de productos por código de barras < 1 segundo.<br>- Índices en BD (código_barras, pin, nro_ticket). |
| **Usabilidad** | - Interfaz con CustomTkinter (diseño moderno).<br>- Campo de código de barras con foco automático y limpieza después de cada escaneo.<br>- Mensajes de error claros en lenguaje humano. |
| **Robustez** | - La app no se cierra por excepciones (try-except).<br>- Si PostgreSQL falla, el sistema sigue operando con SQLite para ventas en efectivo.<br>- Logs de errores para depuración. |
| **Portabilidad** | - Compilación a .exe con PyInstaller.<br>- Funciona en Windows sin Python instalado. |
| **Auditoría** | - Todos los movimientos críticos registrados con fecha, hora y usuario responsable. |

---

## 7. Tecnologías y Herramientas

| Componente | Tecnología |
|------------|------------|
| **Lenguaje** | Python 3.10+ |
| **Interfaz Gráfica** | CustomTkinter |
| **Base de Datos Operativa** | SQLite |
| **Base de Datos Financiera** | PostgreSQL |
| **ORM/Conexión** | psycopg2, sqlite3 |
| **Generación de Ejecutable** | PyInstaller |
| **Control de Versiones** | Git / GitHub |
| **Metodología** | SDD (Spec-Driven Development) |

---

## 8. Entregables Esperados

- Código fuente completo organizado en capas (MVC: models, views, controllers).
- Scripts de base de datos (setup_db.py, seed_data.py).
- Archivos de especificación (spec.md, plan.md, tasks.md) en carpeta `/specs`.
- Archivo ejecutable (.exe) del sistema.
- README.md con instrucciones de instalación y uso.
- Repositorio Git con commits vinculados a tareas atómicas.

---

**Fin del documento de especificación**