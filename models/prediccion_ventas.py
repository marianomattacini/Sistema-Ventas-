"""
Predicción de ventas del próximo trimestre mediante regresión lineal (Ridge),
incorporando:

  - Tendencia general del negocio (¿crece o decrece con el tiempo?)
  - Estacionalidad semanal   (día de la semana: sábados vs. martes, etc.)
  - Estacionalidad anual     (época del año, vía seno/coseno del día del año)
  - Variable externa         (cantidad de promociones activas ese día)

⚠️ CORRELACIÓN NO ES CAUSALIDAD
--------------------------------
Este modelo encuentra PATRONES ESTADÍSTICOS en el historial de ventas, no
relaciones de causa-efecto demostradas. Si el modelo aprende que "los
viernes se vende más", eso es una correlación observada en los datos —no
prueba que el hecho de ser viernes CAUSE el aumento (podría deberse a que
ese día cobran los clientes, hay más gente en la calle, etc.). De la misma
forma, "cambios de mercado" (nueva competencia, crisis económica, un local
que cerró en la cuadra) sólo se reflejan en la predicción si ya impactaron
el historial de ventas; el modelo no los puede anticipar por su cuenta.

Por eso el resultado se muestra siempre con:
  - El R² del modelo (qué tan bien explica el historial, no el futuro).
  - Una advertencia si hay poco historial.
  - La aclaración de que es una PROYECCIÓN estadística, no una garantía.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error

from database.config import get_sqlite_connection


class PrediccionVentas:
    """Genera una proyección de ventas para el próximo trimestre (3 meses)."""

    MIN_DIAS_HISTORIAL = 21   # menos que esto, no es serio proyectar
    DIAS_TRIMESTRE = 90

    def __init__(self):
        self.modelo = None
        self.scaler = None
        self.df = None

    # ------------------------------------------------------------------
    # CARGA DE DATOS
    # ------------------------------------------------------------------
    def _cargar_ventas_diarias(self):
        conn = get_sqlite_connection()
        df = pd.read_sql_query('''
            SELECT DATE(fecha_hora) AS fecha, SUM(total_facturado) AS total
            FROM ventas_cabecera
            WHERE estado = 'Completado'
            GROUP BY DATE(fecha_hora)
        ''', conn)
        conn.close()

        if df.empty:
            return df

        df["fecha"] = pd.to_datetime(df["fecha"])
        # Reindexar para incluir también los días SIN ventas (valen $0):
        # si no hacemos esto, el modelo "no ve" los días flojos y sesga
        # la tendencia y la estacionalidad hacia arriba.
        rango_completo = pd.date_range(df["fecha"].min(), df["fecha"].max(), freq="D")
        df = df.set_index("fecha").reindex(rango_completo, fill_value=0.0)
        df.index.name = "fecha"
        df = df.reset_index().rename(columns={"index": "fecha"})
        return df

    def _promociones_activas_por_dia(self, fechas):
        """Cuenta cuántas promociones estaban activas cada día (variable externa)."""
        conn = get_sqlite_connection()
        try:
            df_promos = pd.read_sql_query(
                "SELECT fecha_inicio, fecha_fin FROM promociones", conn
            )
        except Exception:
            df_promos = pd.DataFrame(columns=["fecha_inicio", "fecha_fin"])
        conn.close()

        fechas_valores = pd.DatetimeIndex(fechas.values)
        conteo = np.zeros(len(fechas_valores), dtype=float)

        if not df_promos.empty:
            df_promos["fecha_inicio"] = pd.to_datetime(df_promos["fecha_inicio"], errors="coerce")
            df_promos["fecha_fin"] = pd.to_datetime(df_promos["fecha_fin"], errors="coerce")
            df_promos = df_promos.dropna()

            for _, promo in df_promos.iterrows():
                mascara = (fechas_valores >= promo["fecha_inicio"]) & (fechas_valores <= promo["fecha_fin"])
                conteo[mascara] += 1

        return pd.Series(conteo, index=range(len(conteo)))

    # ------------------------------------------------------------------
    # INGENIERÍA DE FEATURES (estacionalidad vía seno/coseno: pocas
    # columnas, funciona bien aunque haya poco historial, y evita el
    # sobreajuste típico de usar un dummy por día/mes)
    # ------------------------------------------------------------------
    @staticmethod
    def _armar_features(fechas, promos_activas, t0):
        fechas = pd.DatetimeIndex(fechas)
        dias_desde_inicio = (fechas - t0).days.to_numpy().astype(float)
        dow = fechas.dayofweek.values.astype(float)          # 0=lunes..6=domingo
        doy = fechas.dayofyear.values.astype(float)

        return pd.DataFrame({
            "tendencia": dias_desde_inicio,
            "dow_sin": np.sin(2 * np.pi * dow / 7),
            "dow_cos": np.cos(2 * np.pi * dow / 7),
            "doy_sin": np.sin(2 * np.pi * doy / 365.25),
            "doy_cos": np.cos(2 * np.pi * doy / 365.25),
            "promos_activas": promos_activas.values.astype(float),
        })

    # ------------------------------------------------------------------
    # ENTRENAMIENTO + PREDICCIÓN
    # ------------------------------------------------------------------
    def generar_prediccion(self):
        """
        Retorna un dict:
          {
            "ok": bool,
            "motivo": str (si ok=False),
            "dias_historial": int,
            "r2_entrenamiento": float,
            "r2_validacion": float | None,
            "mae_validacion": float | None,
            "promedio_diario_historico": float,
            "prediccion_diaria": [(fecha, monto), ...],   # 90 días
            "prediccion_mensual": [{"etiqueta": str, "total": float}, ...],  # 3 meses
            "total_trimestre": float,
            "tendencia": "creciendo" | "estable" | "cayendo",
          }
        """
        df = self._cargar_ventas_diarias()

        if df.empty or len(df) < self.MIN_DIAS_HISTORIAL:
            dias = 0 if df.empty else len(df)
            return {
                "ok": False,
                "motivo": (
                    f"Hay solo {dias} día(s) con historial de ventas. "
                    f"Se necesitan al menos {self.MIN_DIAS_HISTORIAL} días para poder "
                    "proyectar el próximo trimestre con algo de seriedad."
                ),
                "dias_historial": dias,
            }

        promos = self._promociones_activas_por_dia(df["fecha"])
        t0 = df["fecha"].min()
        X = self._armar_features(df["fecha"], promos, t0)
        y = df["total"].values.astype(float)

        # --- Split temporal simple para validar (si hay suficiente historial) ---
        r2_val = None
        mae_val = None
        n = len(df)
        usar_validacion = n >= 45
        if usar_validacion:
            corte = n - 14  # últimos 14 días como "test"
            X_train, X_test = X.iloc[:corte], X.iloc[corte:]
            y_train, y_test = y[:corte], y[corte:]
        else:
            X_train, y_train = X, y
            X_test, y_test = None, None

        scaler = StandardScaler()
        X_train_esc = scaler.fit_transform(X_train)

        modelo = Ridge(alpha=1.0)
        modelo.fit(X_train_esc, y_train)

        r2_train = r2_score(y_train, modelo.predict(X_train_esc))

        if usar_validacion:
            X_test_esc = scaler.transform(X_test)
            pred_test = np.clip(modelo.predict(X_test_esc), 0, None)
            r2_val = r2_score(y_test, pred_test)
            mae_val = mean_absolute_error(y_test, pred_test)

        # --- Reentrenar con TODO el historial para la predicción final ---
        scaler_final = StandardScaler()
        X_esc = scaler_final.fit_transform(X)
        modelo_final = Ridge(alpha=1.0)
        modelo_final.fit(X_esc, y)

        self.modelo = modelo_final
        self.scaler = scaler_final
        self.df = df

        # --- Promedio de promociones activas recientes, como supuesto a futuro ---
        promo_futuro = float(promos.tail(30).mean()) if len(promos) else 0.0

        fechas_futuras = pd.date_range(
            df["fecha"].max() + timedelta(days=1), periods=self.DIAS_TRIMESTRE, freq="D"
        )
        promos_futuras = pd.Series(promo_futuro, index=fechas_futuras)
        X_futuro = self._armar_features(fechas_futuras, promos_futuras, t0)
        X_futuro_esc = scaler_final.transform(X_futuro)
        pred_futura = np.clip(modelo_final.predict(X_futuro_esc), 0, None)

        prediccion_diaria = list(zip(fechas_futuras, pred_futura))

        # --- Agrupar en 3 "meses" de 30 días para el trimestre ---
        prediccion_mensual = []
        meses_es = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        for bloque in range(3):
            inicio = bloque * 30
            fin = inicio + 30
            sub = pred_futura[inicio:fin]
            fecha_repr = fechas_futuras[inicio]
            etiqueta = f"{meses_es[fecha_repr.month - 1]} {fecha_repr.year}"
            prediccion_mensual.append({"etiqueta": etiqueta, "total": float(sub.sum())})

        total_trimestre = float(pred_futura.sum())

        pendiente_tendencia = modelo_final.coef_[0]  # coeficiente de "tendencia" (escalado)
        if pendiente_tendencia > 0.5:
            tendencia = "creciendo"
        elif pendiente_tendencia < -0.5:
            tendencia = "cayendo"
        else:
            tendencia = "estable"

        return {
            "ok": True,
            "dias_historial": n,
            "r2_entrenamiento": round(r2_train, 3),
            "r2_validacion": round(r2_val, 3) if r2_val is not None else None,
            "mae_validacion": round(mae_val, 2) if mae_val is not None else None,
            "promedio_diario_historico": round(float(y.mean()), 2),
            "prediccion_diaria": prediccion_diaria,
            "prediccion_mensual": prediccion_mensual,
            "total_trimestre": round(total_trimestre, 2),
            "tendencia": tendencia,
            "uso_validacion": usar_validacion,
        }
