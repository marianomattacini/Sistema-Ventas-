"""
poblar_datos_bancarios_demo.py

Script de siembra (seed) para PostgreSQL: crea 20 personas FICTICIAS con datos
bancarios "realistas" (nombres, DNI/CUIL, CBU, tarjetas de débito y crédito,
billetera virtual) para poder probar y hacer demos del sistema.

⚠️ TODO es inventado. Los números de tarjeta, CBU y CUIL tienen el FORMATO
   correcto (largo, dígito verificador, prefijo de entidad) para que "se vean
   reales", pero no corresponden a ninguna persona, cuenta ni tarjeta real.

QUÉ INSERTA (por cada una de las 20 personas):
  1) Una cuenta bancaria tradicional (Caja de Ahorro / Cuenta Corriente) con
     su tarjeta de débito, en `cuentas_bancarias`.
  2) Una cuenta de billetera virtual (Mercado Pago, Ualá, Personal Pay, etc.)
     también en `cuentas_bancarias` (mismo DNI, cuenta separada).
  3) Una tarjeta de crédito asociada a la cuenta bancaria tradicional, en
     `tarjetas_credito`, con:
       - `limite_un_pago` / `consumo_un_pago`   -> lo que puede pagar en 1 pago
       - `limite_cuotas`  / `consumo_cuotas`    -> lo que tiene en cuotas
       - `saldo_total_a_pagar` = consumo_un_pago + consumo_cuotas

NOTA SOBRE EL ESQUEMA:
  La tabla `cuentas_bancarias` tenía `dni_cuil` como UNIQUE, lo que impedía
  que una misma persona tuviera 2 cuentas (banco + billetera). Como pediste
  que cada persona tenga sus 3 productos a la vez, este script relaja esa
  restricción (deja de ser UNIQUE, pasa a ser un índice normal) para permitir
  varias cuentas por DNI. Si preferís mantenerlo estrictamente 1 cuenta por
  persona, avisame y hago la versión alternativa.

El script es IDEMPOTENTE: usa un rango de DNI reservado para los datos de
demo (30500001 a 30500020), y borra esos registros antes de reinsertarlos,
así se puede correr las veces que quieras sin duplicar ni chocar con datos
reales.

Uso:
    python poblar_datos_bancarios_demo.py
"""

import random
from database.config import get_postgres_connection
from database.setup_postgresql import crear_tablas_postgresql

random.seed(42)  # reproducible: siempre genera los mismos 20 "clientes"

DNI_DESDE = 30500001  # rango reservado para datos de demo
CANTIDAD_PERSONAS = 20


# =============================================================================
# ALGORITMOS DE DÍGITO VERIFICADOR (para que los números "cierren" como reales)
# =============================================================================
def _luhn_checksum(numero):
    """Checksum estándar de Luhn sobre el número completo."""
    digitos = [int(d) for d in numero]
    impares = digitos[-1::-2]        # último dígito, y de a 2 hacia la izquierda
    pares = digitos[-2::-2]          # penúltimo dígito, y de a 2 hacia la izquierda
    total = sum(impares)
    for d in pares:
        doble = d * 2
        total += doble - 9 if doble > 9 else doble
    return total % 10


def generar_numero_tarjeta(prefijo_bin):
    """Genera un número de 16 dígitos válido por Luhn, con el BIN indicado."""
    cuerpo = prefijo_bin + "".join(str(random.randint(0, 9)) for _ in range(15 - len(prefijo_bin)))
    checksum = _luhn_checksum(cuerpo + "0")
    digito_verificador = 0 if checksum == 0 else 10 - checksum
    return cuerpo + str(digito_verificador)


def _dv_bloque_cbu(bloque):
    """Dígito verificador de un bloque de CBU (algoritmo real, pesos 3,1,7,9,3,1,7...)."""
    pesos = [3, 1, 7, 9, 3, 1, 7]
    suma = sum(int(d) * pesos[i % 7] for i, d in enumerate(bloque))
    resto = suma % 10
    return 0 if resto == 0 else 10 - resto


def generar_cbu(codigo_entidad):
    """Genera un CBU/CVU de 22 dígitos con estructura y dígitos verificadores reales."""
    sucursal = f"{random.randint(0, 9999):04d}"
    bloque1 = codigo_entidad + sucursal
    dv1 = _dv_bloque_cbu(bloque1)
    cuenta = "".join(str(random.randint(0, 9)) for _ in range(13))
    dv2 = _dv_bloque_cbu(cuenta)
    return f"{bloque1}{dv1}{cuenta}{dv2}"


def generar_cuil(dni, prefijo="20"):
    """Genera un CUIL con dígito verificador real a partir de un DNI."""
    base = f"{prefijo}{dni:08d}"
    pesos = [5, 4, 3, 2, 7, 6, 5, 4, 3]
    suma = sum(int(d) * p for d, p in zip(base, pesos))
    resto = suma % 11
    dv = 11 - resto
    if dv == 11:
        dv = 0
    elif dv == 10:
        dv = 9
        prefijo = "23" if prefijo == "20" else "24"
        base = f"{prefijo}{dni:08d}"
    return f"{prefijo}-{dni:08d}-{dv}"


# =============================================================================
# DATOS "MAESTROS" (bancos, billeteras, nombres) — códigos de entidad
# aproximados con fines demostrativos, no verificados contra el BCRA.
# =============================================================================
BANCOS = [
    ("Galicia",            "007", "4507"),
    ("Banco Nación",       "011", "4529"),
    ("BBVA",               "017", "4543"),
    ("Banco Macro",        "285", "4515"),
    ("Santander Río",      "072", "4551"),
    ("Banco Provincia",    "014", "4576"),
    ("Banco Supervielle",  "027", "4589"),
    ("Banco Ciudad",       "007", "4598"),
    ("ICBC",               "730", "4602"),
    ("Banco Patagonia",    "034", "4611"),
]

BILLETERAS = [
    ("Mercado Pago",  "170"),
    ("Ualá",          "323"),
    ("Personal Pay",  "312"),
    ("Naranja X",     "281"),
    ("Cuenta DNI",    "014"),
    ("MODO",          "398"),
    ("Brubank",       "268"),
    ("Lemon Cash",    "355"),
]

TIPOS_CUENTA = ["Caja de Ahorro", "Cuenta Corriente"]

PROMOS_CREDITO = [
    "3 cuotas sin interés en supermercados",
    "6 cuotas sin interés los martes",
    "10% de reintegro en combustibles",
    "12 cuotas con interés reducido",
    "2x1 en cines los miércoles",
    "Sin promociones activas",
    "15% de reintegro en indumentaria",
    "Hasta 18 cuotas en electrodomésticos",
]

NOMBRES = [
    "Mariano", "Lucía", "Nicolás", "Valentina", "Federico", "Camila", "Ignacio",
    "Sofía", "Emiliano", "Martina", "Tomás", "Julieta", "Gonzalo", "Agustina",
    "Franco", "Micaela", "Bruno", "Florencia", "Santiago", "Rocío",
]

APELLIDOS = [
    "Gómez", "Fernández", "Rodríguez", "Pérez", "López", "Martínez", "García",
    "González", "Sosa", "Romero", "Álvarez", "Molina", "Torres", "Ramírez",
    "Flores", "Acosta", "Benítez", "Suárez", "Ortiz", "Correa",
]


def generar_personas(cantidad):
    personas = []
    for i in range(cantidad):
        dni = DNI_DESDE + i
        nombre = NOMBRES[i % len(NOMBRES)]
        apellido = APELLIDOS[(i * 3 + 1) % len(APELLIDOS)]
        prefijo_cuil = "27" if i % 2 == 0 else "20"  # variedad, sin significado real

        banco = BANCOS[i % len(BANCOS)]
        billetera = BILLETERAS[i % len(BILLETERAS)]
        tipo_cuenta = TIPOS_CUENTA[i % len(TIPOS_CUENTA)]

        saldo_banco = round(random.uniform(15000, 2_500_000), 2)
        saldo_billetera = round(random.uniform(1000, 300000), 2)

        consumo_un_pago = round(random.uniform(0, 250000), 2)
        consumo_cuotas = round(random.uniform(0, 500000), 2)

        personas.append({
            "dni": dni,
            "nombre": nombre,
            "apellido": apellido,
            "cuil": generar_cuil(dni, prefijo_cuil),
            "banco_nombre": banco[0],
            "banco_cbu_codigo": banco[1],
            "banco_bin": banco[2],
            "billetera_nombre": billetera[0],
            "billetera_cbu_codigo": billetera[1],
            "tipo_cuenta": tipo_cuenta,
            "saldo_banco": saldo_banco,
            "saldo_billetera": saldo_billetera,
            "consumo_un_pago": consumo_un_pago,
            "consumo_cuotas": consumo_cuotas,
        })
    return personas


def _slug(texto):
    reemplazos = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n"}
    texto = texto.lower()
    for original, nuevo in reemplazos.items():
        texto = texto.replace(original, nuevo)
    return texto.replace(" ", "")


# =============================================================================
# RELAJAR EL UNIQUE DE dni_cuil (ver nota en el docstring del módulo)
# =============================================================================
def permitir_multiples_cuentas_por_dni(cursor):
    cursor.execute('''
        SELECT conname FROM pg_constraint
        WHERE conrelid = 'cuentas_bancarias'::regclass AND contype = 'u'
    ''')
    for (nombre_constraint,) in cursor.fetchall():
        cursor.execute(f'ALTER TABLE cuentas_bancarias DROP CONSTRAINT IF EXISTS "{nombre_constraint}"')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_cuentas_bancarias_dni_cuil
        ON cuentas_bancarias (dni_cuil)
    ''')


def limpiar_datos_demo_previos(cursor):
    """Borra (si existen) los datos de demo de una corrida anterior, para poder re-ejecutar el script."""
    dnis_demo = [f"{DNI_DESDE + i:08d}" for i in range(CANTIDAD_PERSONAS)]
    placeholders = ",".join(["%s"] * len(dnis_demo))
    cursor.execute(f'''
        DELETE FROM tarjetas_credito
        WHERE cuenta_id IN (
            SELECT id FROM cuentas_bancarias WHERE dni_cuil = ANY(%s)
        )
    ''', (dnis_demo,))
    cursor.execute('DELETE FROM cuentas_bancarias WHERE dni_cuil = ANY(%s)', (dnis_demo,))


def poblar():
    conn = get_postgres_connection()
    if not conn:
        print("❌ No se pudo conectar a PostgreSQL. Revisá las credenciales en tu .env")
        return

    cursor = conn.cursor()

    permitir_multiples_cuentas_por_dni(cursor)
    limpiar_datos_demo_previos(cursor)
    conn.commit()

    personas = generar_personas(CANTIDAD_PERSONAS)
    resumen = []

    for p in personas:
        dni_str = f"{p['dni']:08d}"
        nombre_completo = f"{p['nombre']} {p['apellido']}"
        usuario_slug = f"{_slug(p['nombre'])}.{_slug(p['apellido'])}"

        # --- 1) Cuenta bancaria tradicional + tarjeta de débito ---
        numero_debito = generar_numero_tarjeta(p["banco_bin"])
        pin_debito = f"{random.randint(0, 9999):04d}"
        vencimiento_debito = f"{random.randint(1, 12):02d}/{random.randint(27, 30)}"
        cbu_banco = generar_cbu(p["banco_cbu_codigo"])
        alias_banco = f"{usuario_slug}.{_slug(p['banco_nombre'])[:4]}"
        limite_extraccion = round(random.uniform(150000, 600000), 2)

        cursor.execute('''
            INSERT INTO cuentas_bancarias
                (dni_cuil, usuario, contrasena, tipo_cuenta, saldo, cbu, alias,
                 numero_debito, pin_debito, vencimiento_debito,
                 limite_extraccion_mensual, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (dni_str, f"{usuario_slug}.banco", "Demo2026!", p["tipo_cuenta"],
              p["saldo_banco"], cbu_banco, alias_banco,
              numero_debito, pin_debito, vencimiento_debito,
              limite_extraccion, "Activo"))
        cuenta_banco_id = cursor.fetchone()[0]

        # --- 2) Cuenta de billetera virtual (mismo DNI, cuenta separada) ---
        cbu_billetera = generar_cbu(p["billetera_cbu_codigo"])
        alias_billetera = f"{usuario_slug}.{_slug(p['billetera_nombre'])[:4]}"

        cursor.execute('''
            INSERT INTO cuentas_bancarias
                (dni_cuil, usuario, contrasena, tipo_cuenta, saldo, cbu, alias,
                 limite_extraccion_mensual, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (dni_str, f"{usuario_slug}.wallet", "Demo2026!", "Billetera Virtual",
              p["saldo_billetera"], cbu_billetera, alias_billetera,
              round(p["saldo_billetera"] * 0.5, 2), "Activo"))
        cuenta_billetera_id = cursor.fetchone()[0]

        # --- 3) Tarjeta de crédito asociada a la cuenta bancaria ---
        numero_credito = generar_numero_tarjeta(p["banco_bin"][:2] + "09")
        cvv = f"{random.randint(0, 999):03d}"
        vencimiento_credito = f"{random.randint(1, 12):02d}/{random.randint(27, 30)}"
        limite_un_pago = round(random.uniform(200000, 1_500_000), 2)
        limite_cuotas = round(random.uniform(150000, 1_200_000), 2)
        limite_extraccion_cred = round(limite_un_pago * 0.2, 2)
        consumo_extraccion = round(random.uniform(0, limite_extraccion_cred), 2)
        saldo_total_a_pagar = round(p["consumo_un_pago"] + p["consumo_cuotas"], 2)
        promocion = random.choice(PROMOS_CREDITO)

        cursor.execute('''
            INSERT INTO tarjetas_credito
                (cuenta_id, banco, numero_tarjeta, cvv, vencimiento_credito,
                 limite_un_pago, consumo_un_pago, limite_cuotas, consumo_cuotas,
                 limite_extraccion, consumo_extraccion, saldo_total_a_pagar,
                 promocion, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (cuenta_banco_id, p["banco_nombre"], numero_credito, cvv, vencimiento_credito,
              limite_un_pago, p["consumo_un_pago"], limite_cuotas, p["consumo_cuotas"],
              limite_extraccion_cred, consumo_extraccion, saldo_total_a_pagar,
              promocion, "Activo"))

        resumen.append({
            "nombre": nombre_completo,
            "dni": dni_str,
            "cuil": p["cuil"],
            "banco": p["banco_nombre"],
            "saldo_banco": p["saldo_banco"],
            "billetera": p["billetera_nombre"],
            "saldo_billetera": p["saldo_billetera"],
            "credito_1_pago": p["consumo_un_pago"],
            "credito_cuotas": p["consumo_cuotas"],
        })

        print(f"✅ {nombre_completo} (DNI {dni_str}) — {p['banco_nombre']} + {p['billetera_nombre']}")

    conn.commit()
    cursor.close()
    conn.close()

    print("\n" + "=" * 100)
    print(f"{'NOMBRE':<22}{'DNI':<11}{'BANCO':<18}{'SALDO BANCO':>14}{'BILLETERA':<15}{'SALDO BILL.':>13}")
    print("=" * 100)
    for r in resumen:
        print(f"{r['nombre']:<22}{r['dni']:<11}{r['banco']:<18}${r['saldo_banco']:>12,.2f} "
              f"{r['billetera']:<15}${r['saldo_billetera']:>11,.2f}")
    print("=" * 100)
    print(f"✅ {len(resumen)} personas creadas con cuenta bancaria + billetera virtual + tarjeta de crédito.")
    print("   Contraseña de todas las cuentas de demo: Demo2026!")


if __name__ == "__main__":
    print("🏦 Poblando datos bancarios de demo (20 personas ficticias)...\n")
    poblar()
