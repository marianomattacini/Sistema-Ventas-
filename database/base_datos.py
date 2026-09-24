"""
Clase de Base de Datos (capa "Modelo de datos" del patrón MVC / requisito
de la consigna del CRUD).

Toda la conexión a SQLite y la ejecución de sentencias SQL (INSERT, SELECT,
UPDATE, DELETE) del sistema pasa, en definitiva, por esta clase: es el único
lugar del proyecto que abre una conexión sqlite3 y ejecuta SQL directamente.
Las clases de Vista (views/) nunca tocan SQL ni conexiones: siempre piden
los datos a una clase de Modelo (models/), y estas usan BaseDatos para
hablar con la base.
"""

import sqlite3


class BaseDatos:
    """
    Encargada exclusivamente de:
      1) la conexión a la base de datos SQLite, y
      2) la ejecución de sentencias SQL (INSERT, SELECT, UPDATE, DELETE).

    Uso típico desde una clase de Modelo:
        bd = BaseDatos(ruta_db)
        filas = bd.consultar("SELECT * FROM productos WHERE estado = ?", ("Activo",))
        nuevo_id = bd.insertar("INSERT INTO clientes (nombre) VALUES (?)", ("Juan Pérez",))
        filas_afectadas = bd.actualizar("UPDATE productos SET stock_actual = ? WHERE codigo_barras = ?", (10, "123"))
        bd.eliminar("DELETE FROM notificaciones WHERE id = ?", (5,))
    """

    def __init__(self, ruta_db):
        self.ruta_db = ruta_db
        self._schema_migrado = False

    # ------------------------------------------------------------------
    # 1) Conexión
    # ------------------------------------------------------------------
    def conectar(self):
        """
        Abre y retorna una conexión sqlite3 a la base de datos, con
        claves foráneas activadas y un tiempo de espera razonable para
        evitar bloqueos ("database is locked") cuando dos operaciones
        intentan escribir casi al mismo tiempo.
        """
        try:
            conn = sqlite3.connect(self.ruta_db, timeout=15)
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA busy_timeout = 15000;")
            self._migrar_esquema(conn)
            return conn
        except sqlite3.Error as e:
            print(f"❌ Error al conectar a SQLite: {e}")
            return None

    def _migrar_esquema(self, conn):
        """
        Migración idempotente y liviana: agrega columnas que puedan faltar
        en bases de datos ya existentes (creadas antes de incorporar
        ciertas funcionalidades), sin tocar ni recrear ninguna tabla. Se
        ejecuta una sola vez por instancia de BaseDatos.
        """
        if self._schema_migrado:
            return
        try:
            cursor = conn.cursor()

            cursor.execute("PRAGMA table_info(ventas_pagos)")
            columnas = [c[1] for c in cursor.fetchall()]
            if columnas and 'monto_recibido' not in columnas:
                cursor.execute("ALTER TABLE ventas_pagos ADD COLUMN monto_recibido REAL DEFAULT 0")

            cursor.execute("PRAGMA table_info(ventas_cabecera)")
            columnas = [c[1] for c in cursor.fetchall()]
            if columnas and 'descuento_total' not in columnas:
                cursor.execute("ALTER TABLE ventas_cabecera ADD COLUMN descuento_total REAL DEFAULT 0")

            cursor.execute("PRAGMA table_info(ventas_detalle)")
            columnas = [c[1] for c in cursor.fetchall()]
            if columnas and 'descuento' not in columnas:
                cursor.execute("ALTER TABLE ventas_detalle ADD COLUMN descuento REAL DEFAULT 0")

            cursor.execute("PRAGMA table_info(entidades_pago)")
            columnas = [c[1] for c in cursor.fetchall()]
            if columnas:
                if 'descuento_porcentaje' not in columnas:
                    cursor.execute("ALTER TABLE entidades_pago ADD COLUMN descuento_porcentaje REAL DEFAULT 0")
                if 'cuotas_sin_interes' not in columnas:
                    cursor.execute("ALTER TABLE entidades_pago ADD COLUMN cuotas_sin_interes INTEGER DEFAULT 0")
                if 'promocion_descripcion' not in columnas:
                    cursor.execute("ALTER TABLE entidades_pago ADD COLUMN promocion_descripcion TEXT")

            conn.commit()
        except sqlite3.Error:
            pass
        self._schema_migrado = True

    # ------------------------------------------------------------------
    # 2) Ejecución de sentencias SQL
    # ------------------------------------------------------------------
    def consultar(self, query, params=()):
        """Ejecuta un SELECT y retorna la lista de filas resultantes."""
        conn = self.conectar()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"❌ Error en consulta SQL: {e}")
            return []
        finally:
            conn.close()

    def insertar(self, query, params=()):
        """Ejecuta un INSERT y retorna el id autogenerado (lastrowid), o None si falló."""
        conn = self.conectar()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"❌ Error al insertar: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def actualizar(self, query, params=()):
        """Ejecuta un UPDATE y retorna la cantidad de filas afectadas."""
        conn = self.conectar()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
        except sqlite3.Error as e:
            print(f"❌ Error al actualizar: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()

    def eliminar(self, query, params=()):
        """Ejecuta un DELETE y retorna la cantidad de filas afectadas."""
        conn = self.conectar()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
        except sqlite3.Error as e:
            print(f"❌ Error al eliminar: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()

    def ejecutar_transaccion(self, operaciones):
        """
        Ejecuta varias sentencias SQL como una única transacción atómica
        (todas se confirman juntas, o ninguna). 'operaciones' es una lista
        de tuplas (query, params). Se usa para operaciones que deben
        descontar/sumar stock junto con insertar una venta o una compra,
        evitando bloqueos por abrir varias conexiones a la vez.
        """
        conn = self.conectar()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            for query, params in operaciones:
                cursor.execute(query, params)
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"❌ Error en transacción: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
