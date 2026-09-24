# Plan Técnico - Sistema de Gestión de Ventas y Control de Stock

## 1. Visión General
Este documento define la arquitectura técnica, el modelo de datos, la estructura del proyecto y las decisiones de implementación para el Sistema de Gestión de Ventas y Control de Stock, basado en la especificación funcional (`spec.md`).


---

## 2. Arquitectura General

### 2.1. Capas del Sistema
| Capa | Ubicación | Responsabilidad |
|------|-----------|-----------------|
| **Modelo** | `/models/` | Clases POO que representan las entidades del negocio (Producto, Venta, Usuario, etc.). Contienen la lógica de negocio y la persistencia (CRUD). |
| **Vista** | `/views/` | Ventanas y widgets construidos con CustomTkinter. Solo se encargan de la interfaz de usuario (mostrar datos, capturar entrada). No contienen lógica de negocio. |
| **Controlador** | `/controllers/` | Actúan como intermediarios entre Vista y Modelo. Reciben eventos de la interfaz, llaman a los modelos para procesar datos y actualizan las vistas con los resultados. |
| **Utilidades** | `/utils/` | Funciones auxiliares reutilizables: validaciones, hashing de PIN, generación de tickets, logs, etc. |
| **Base de Datos** | `/database/` | Scripts de configuración, creación de tablas y datos de prueba (setup_db.py, seed_data.py, config.py). |

### 2.2. Flujo de Datos
1. El usuario interactúa con la **Vista** (ej. hace clic en "Buscar Producto").
2. La Vista notifica al **Controlador** correspondiente.
3. El Controlador llama al **Modelo** (ej. `Producto.buscar_por_codigo()`).
4. El Modelo consulta la **Base de Datos** y devuelve los datos.
5. El Controlador recibe los datos y actualiza la Vista.
6. La Vista muestra la información al usuario.

Este flujo asegura que la lógica de negocio esté aislada de la interfaz, facilitando pruebas y cambios futuros.

---

## 3. Modelo de Datos

### 3.1. Esquema de Base de Datos Híbrida
- **SQLite** (`supermercado.db`): Base de datos operativa local (productos, ventas, turnos, clientes, proveedores, compras, cupones, logs).
- **PostgreSQL** (`cajero_automatico`): Base de datos financiera (cuentas bancarias, tarjetas de crédito, movimientos).

### 3.2. Tablas en SQLite (Operativa)

#### `usuarios`
| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Identificador único |
| nombre_usuario | TEXT | UNIQUE, NOT NULL | Nombre de usuario para login |
| pin_hash | TEXT | NOT NULL | Hash del PIN (seguridad) |
| rol | TEXT | NOT NULL | Cajero, Supervisor, Administrador, Gerente General |
| estado | TEXT | DEFAULT 'Activo' | Activo, Inactivo, Bloqueado |
| fecha_creacion | TEXT (ISO datetime) | DEFAULT CURRENT_TIMESTAMP | Fecha de alta |
| ultimo_login | TEXT (ISO datetime) | NULL | Última fecha de acceso |

#### `categorias`
| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Identificador único |
| nombre | TEXT | NOT NULL | Ej. "Bebidas", "Lácteos" |
| estado | TEXT | DEFAULT 'Activo' | Activo, Inactivo |

#### `productos`
| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| codigo_barras | TEXT | PRIMARY KEY, UNIQUE | Código de barras (lectura principal) |
| nombre | TEXT | NOT NULL | Nombre del producto |
| categoria_id | INTEGER | FOREIGN KEY (categorias.id) | Categoría a la que pertenece |
| precio_venta | REAL | NOT NULL | Precio de venta al público |
| stock_actual | INTEGER | DEFAULT 0 | Cantidad disponible |
| stock_minimo | INTEGER | DEFAULT 0 | Nivel para alerta de reposición |
| tipo_garantia | TEXT | DEFAULT 'comestible' | Comestible, electrónico, etc. |
| estado | TEXT | DEFAULT 'Activo' | Activo, Inactivo |
| precio_costo | REAL | NOT NULL | Precio de adquisición (para control) |

#### `clientes`
| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| dni_cuil | TEXT | PRIMARY KEY, UNIQUE | DNI o CUIL del cliente |
| nombre | TEXT | NOT NULL | Nombre completo |
| telefono | TEXT | | Teléfono de contacto |
| email | TEXT | | Correo electrónico |
| puntos_acumulados | INTEGER | DEFAULT 0 | Puntos de fidelización |
| estado | TEXT | DEFAULT 'Activo' | Activo, Inactivo |
| fecha_registro | TEXT (ISO datetime) | DEFAULT CURRENT_TIMESTAMP | Fecha de alta |

#### `proveedores`
| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| cuit | TEXT | PRIMARY KEY, UNIQUE | CUIT del proveedor |
| razon_social | TEXT | NOT NULL | Razón social o nombre |
| telefono | TEXT | NOT NULL | Teléfono de contacto |
| email | TEXT | NOT NULL | Correo electrónico |
| estado | TEXT | DEFAULT 'Activo' | Activo, Inactivo |

#### `turnos`
| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Identificador único |
| usuario_id | INTEGER | FOREIGN KEY (usuarios.id) | Cajero que abrió el turno |
| fecha_hora_apertura | TEXT (ISO datetime) | NOT NULL | Inicio del turno |
| fecha_hora_cierre | TEXT (ISO datetime) | NULL | Cierre del turno |
| fondo_inicial | REAL | NOT NULL | Declaración de caja al abrir |
| total_ventas_efectivo | REAL | DEFAULT 0 | Suma de ventas en efectivo |
| total_ventas_debito | REAL | DEFAULT 0 | Suma de ventas con débito |
| total_ventas_credito | REAL | DEFAULT 0 | Suma de ventas con crédito |
| total_ventas_transferencia | REAL | DEFAULT 0 | Suma de ventas con transferencia |
| total_sangrias | REAL | DEFAULT 0 | Suma de retiros de efectivo |
| estado | TEXT | DEFAULT 'Abierto' | Abierto, Cerrado, Forzado |

#### `ventas_cabecera`
| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| nro_ticket | TEXT | PRIMARY KEY, UNIQUE | Número de ticket único |
| turno_id | INTEGER | FOREIGN KEY (turnos.id) | Turno en que se realizó |
| dni_cliente | TEXT | FOREIGN KEY (clientes.dni_cuil), NULL | Cliente (opcional) |
| fecha_hora | TEXT (ISO datetime) | NOT NULL | Fecha y hora de la venta |
| total_facturado | REAL | NOT NULL | Suma total de la venta |
| puntos_sumados | INTEGER | DEFAULT 0 | Puntos otorgados al cliente |
| estado | TEXT | DEFAULT 'En Curso' | En Curso, Pausado, Completado, Anulado |

#### `ventas_detalle`
| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Identificador único |
| nro_ticket | TEXT | FOREIGN KEY (ventas_cabecera.nro_ticket) | Ticket al que pertenece |
| codigo_producto | TEXT | FOREIGN KEY (productos.codigo_barras) | Producto vendido |
| cantidad | INTEGER | NOT NULL | Cantidad vendida |
| subtotal | REAL | NOT NULL | Precio unitario * cantidad |

#### `ventas_pagos`
| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Identificador único |
| nro_ticket | TEXT | FOREIGN KEY (ventas_cabecera.nro_ticket) | Ticket al que pertenece |
| metodo_pago | TEXT | NOT NULL | Efectivo, Débito, Crédito, Transferencia |
| monto_abonado | REAL | NOT NULL | Monto pagado con este método |
| monto_vuelto | REAL | DEFAULT 0 | Vuelto (solo en efectivo) |
| cuotas | INTEGER | NULL | Número de cuotas (solo crédito) |
| interes_aplicado | REAL | DEFAULT 0 | Interés aplicado (si corresponde) |
| promocion_aplicada | TEXT | NULL | Descripción de promoción (si aplica) |

#### `sangrias`
| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Identificador único |
| turno_id | INTEGER | FOREIGN KEY (turnos.id) | Turno en que se realiza |
| cajero_id | INTEGER | FOREIGN KEY (usuarios.id) | Cajero que solicita |
| supervisor_id | INTEGER | FOREIGN KEY (usuarios.id) | Supervisor que autoriza |
| fecha_hora | TEXT (ISO datetime) | NOT NULL | Fecha y hora de la operación |
| monto_retirado | REAL | NOT NULL | Monto retirado |
| motivo | TEXT | NOT NULL DEFAULT 'Retiro de efectivo por máximo alcanzado' | Descripción de la sangría |

#### `compras_cabecera`
| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Identificador único |
| nro_factura | TEXT | UNIQUE, NOT NULL | Número de factura del proveedor |
| proveedor_id | TEXT | FOREIGN KEY (proveedores.cuit) | Proveedor |
| supervisor_id | INTEGER | FOREIGN KEY (usuarios.id) | Supervisor que registra la compra |
| fecha_hora | TEXT (ISO datetime) | NOT NULL | Fecha de la compra |
| total_factura | REAL | NOT NULL | Total de la factura |
| estado | TEXT | DEFAULT 'Ingresado' | Ingresado, Anulado |

#### `compras_detalle`
| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Identificador único |
| compra_id | INTEGER | FOREIGN KEY (compras_cabecera.id) | Compra a la que pertenece |
| codigo_producto | TEXT | FOREIGN KEY (productos.codigo_barras) | Producto comprado |
| cantidad_ingresada | INTEGER | NOT NULL | Cantidad ingresada |
| precio_costo | REAL | NOT NULL | Precio de compra unitario |
| subtotal | REAL | NOT NULL | Precio costo * cantidad |

#### `cupones_devolucion`
| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| codigo_alfanumerico | TEXT | PRIMARY KEY, UNIQUE | Código único del cupón |
| ticket_origen | TEXT | FOREIGN KEY (ventas_cabecera.nro_ticket) | Ticket que generó el cupón |
| dni_cliente | TEXT | FOREIGN KEY (clientes.dni_cuil) | Cliente que realiza la devolución |
| fecha_emision | TEXT (ISO datetime) | NOT NULL | Fecha de emisión |
| estado | TEXT | DEFAULT 'Pendiente' | Pendiente, Usado, Vencido |
| fecha_uso | TEXT (ISO datetime) | NULL | Fecha en que se usó (si aplica) |

#### `registro_descansos`
| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Identificador único |
| turno_id | INTEGER | FOREIGN KEY (turnos.id) | Turno en que se toma el descanso |
| fecha_hora_inicio | TEXT (ISO datetime) | NOT NULL | Inicio del descanso |
| fecha_hora_fin | TEXT (ISO datetime) | NULL | Fin del descanso (si ya terminó) |
| motivo | TEXT | NOT NULL | Descanso, Sanitario, Merienda, Reunión, Gestión, Otro |

#### `logs_auditoria`
| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Identificador único |
| usuario_id | INTEGER | FOREIGN KEY (usuarios.id) | Usuario que realizó la acción |
| fecha_hora | TEXT (ISO datetime) | DEFAULT CURRENT_TIMESTAMP | Fecha y hora del evento |
| accion | TEXT | NOT NULL | Descripción corta (ej. "Venta realizada", "Producto modificado") |
| detalle | TEXT | | Descripción extendida (JSON o texto) |
| ip_origen | TEXT | NULL | Dirección IP (opcional) |

### 3.3. Tablas en PostgreSQL (Financiera)

#### `cuentas_bancarias`
| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Identificador único |
| dni_cuil | VARCHAR(20) | UNIQUE, NOT NULL | DNI del titular |
| usuario | VARCHAR(50) | NOT NULL | Nombre de usuario bancario |
| contrasena | VARCHAR(50) | NOT NULL | Contraseña bancaria |
| tipo_cuenta | VARCHAR(30) | | Caja de Ahorro, Cuenta Corriente |
| saldo | NUMERIC(15,2) | DEFAULT 0.0 | Saldo disponible |
| cbu | VARCHAR(22) | UNIQUE | CBU de la cuenta |
| alias | VARCHAR(50) | UNIQUE | Alias de la cuenta |
| numero_debito | VARCHAR(16) | UNIQUE | Número de tarjeta de débito |
| pin_debito | VARCHAR(4) | | PIN de la tarjeta de débito |
| vencimiento_debito | VARCHAR(5) | | Fecha de vencimiento (MM/AA) |
| limite_extraccion_mensual | NUMERIC(15,2) | | Límite de extracción mensual |
| estado | VARCHAR(20) | DEFAULT 'Activo' | Activo, Inactivo, Bloqueado |

#### `tarjetas_credito`
| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Identificador único |
| cuenta_id | INTEGER | FOREIGN KEY (cuentas_bancarias.id) | Cuenta asociada |
| banco | VARCHAR(50) | | Banco emisor |
| numero_tarjeta | VARCHAR(16) | UNIQUE | Número de tarjeta |
| cvv | VARCHAR(4) | | Código de seguridad |
| vencimiento_credito | VARCHAR(5) | | Fecha de vencimiento (MM/AA) |
| limite_un_pago | NUMERIC(15,2) | | Límite en un pago |
| consumo_un_pago | NUMERIC(15,2) | DEFAULT 0.0 | Consumo acumulado en un pago |
| limite_cuotas | NUMERIC(15,2) | | Límite en cuotas |
| consumo_cuotas | NUMERIC(15,2) | DEFAULT 0.0 | Consumo acumulado en cuotas |
| limite_extraccion | NUMERIC(15,2) | | Límite para extracciones |
| consumo_extraccion | NUMERIC(15,2) | DEFAULT 0.0 | Consumo acumulado en extracciones |
| saldo_total_a_pagar | NUMERIC(15,2) | DEFAULT 0.0 | Saldo total adeudado |
| estado | VARCHAR(20) | DEFAULT 'Activo' | Activo, Inactivo, Bloqueado |

#### `movimientos`
| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Identificador único |
| cuenta_id | INTEGER | FOREIGN KEY (cuentas_bancarias.id) | Cuenta afectada |
| tipo_operacion | VARCHAR(50) | | Débito POS, Transferencia, etc. |
| monto | NUMERIC(15,2) | | Monto de la operación |
| descripcion | TEXT | | Detalle de la operación |
| fecha | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Fecha y hora de la operación |

---

## 4. Índices Recomendados (SQLite)

| Tabla | Campo(s) | Motivo |
|-------|----------|--------|
| usuarios | nombre_usuario | Login rápido |
| usuarios | pin_hash | Validación de PIN |
| productos | codigo_barras | Búsqueda por escaneo (PK, pero índice refuerza) |
| productos | nombre | Búsqueda manual por nombre |
| productos | categoria_id | Filtrado por categoría |
| ventas_cabecera | turno_id | Reportes por turno |
| ventas_cabecera | dni_cliente | Historial de compras por cliente |
| ventas_detalle | nro_ticket | Recuperar detalles de un ticket |
| ventas_detalle | codigo_producto | Consultar ventas por producto |
| turnos | usuario_id | Buscar turnos de un cajero |
| turnos | estado | Saber si hay turnos abiertos |
| compras_detalle | codigo_producto | Consultar compras por producto |
| sangrias | turno_id | Auditoría de caja por turno |

---

## 5. Configuración de Base de Datos

### 5.1. Activación de Claves Foráneas en SQLite
**IMPORTANTE:** Al establecer la conexión con SQLite, se debe ejecutar el siguiente comando para activar la integridad referencial:
```python
conexion.execute("PRAGMA foreign_keys = ON;")
