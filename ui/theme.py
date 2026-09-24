"""
Tema visual unificado del Sistema de Gestión de Ventas y Control de Stock.

Centraliza colores, fuentes y helpers de estilo para que TODAS las
pantallas (frames) usen exactamente la misma paleta e interacciones
(hover, focus, disabled, éxito/error). Basado en la paleta que ya
existía en el proyecto (slate + sky) para no romper la identidad visual,
solo formalizarla y aplicarla en todos lados por igual.
"""

import customtkinter as ctk

# ---------------------------------------------------------------------------
# PALETA DE COLORES (Tailwind slate / sky / semánticos)
# ---------------------------------------------------------------------------
class Color:
    # Fondos
    BG_APP = "#FFFFFF"          # fondo general de la app (contenido principal)
    BG_BASE = "#F4F6F9"         # fondo de paneles/secciones
    BG_CARD = "#F9FAFB"         # tarjetas / contenedores
    BG_CARD_ALT = "#F1F3F6"     # variante levemente distinta para anidar
    BG_INPUT = "#F4F6F9"        # fondo de inputs
    BORDER = "#D6DBE3"

    # Texto
    TEXT_PRIMARY = "#1A2233"
    TEXT_SECONDARY = "#6B7280"
    TEXT_MUTED = "#8B93A3"
    TEXT_WHITE = "#FFFFFF"

    # Acento principal (azul corporativo)
    ACCENT = "#1D4ED8"
    ACCENT_HOVER = "#2563EB"
    ACCENT_STRONG = "#2563EB"

    # Sidebar
    SIDEBAR_BG = "#F4F6F9"
    SIDEBAR_ITEM_HOVER = "#E4E8EF"
    SIDEBAR_ITEM_ACTIVE = "#2563EB"
    SIDEBAR_ITEM_ACTIVE_TEXT = "#FFFFFF"

    # Semánticos
    SUCCESS = "#15803D"
    SUCCESS_HOVER = "#166534"
    WARNING = "#C2410C"
    WARNING_HOVER = "#9A3412"
    DANGER = "#DC2626"
    DANGER_HOVER = "#B91C1C"
    INFO = "#2563EB"
    INFO_HOVER = "#1D4ED8"
    VIOLET = "#7C3AED"
    VIOLET_HOVER = "#6D28D9"
    NEUTRAL = "#64748B"
    NEUTRAL_HOVER = "#475569"


# ---------------------------------------------------------------------------
# TIPOGRAFÍA
# ---------------------------------------------------------------------------
class Font:
    FAMILY = "Roboto"

    H1 = (FAMILY, 28, "bold")     # título de pantalla
    H2 = (FAMILY, 20, "bold")     # subtítulo de sección
    H3 = (FAMILY, 16, "bold")     # encabezado de card
    BODY = (FAMILY, 14)
    BODY_BOLD = (FAMILY, 14, "bold")
    SMALL = (FAMILY, 12)
    BUTTON = (FAMILY, 14, "bold")
    KPI = (FAMILY, 26, "bold")


# ---------------------------------------------------------------------------
# RADIOS / ESPACIADO
# ---------------------------------------------------------------------------
class Radius:
    SM = 8
    MD = 12
    LG = 16


class Spacing:
    XS = 5
    SM = 10
    MD = 20
    LG = 30


# ---------------------------------------------------------------------------
# CONFIGURACIÓN GLOBAL DE CUSTOMTKINTER
# ---------------------------------------------------------------------------
def aplicar_tema_global():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")


# ---------------------------------------------------------------------------
# HELPERS DE WIDGETS ESTILIZADOS (para no repetir fg_color/hover en cada vista)
# ---------------------------------------------------------------------------
def boton_primario(master, text, command=None, **kw):
    defaults = dict(
        font=Font.BUTTON, height=40, corner_radius=Radius.MD,
        fg_color=Color.ACCENT_STRONG, hover_color=Color.ACCENT_HOVER,
        text_color=Color.TEXT_WHITE,
    )
    defaults.update(kw)
    return ctk.CTkButton(master, text=text, command=command, **defaults, border_width=1, border_color="#CBD2DC")


def boton_secundario(master, text, command=None, **kw):
    defaults = dict(
        font=Font.BUTTON, height=36, corner_radius=Radius.MD,
        fg_color=Color.NEUTRAL, hover_color=Color.NEUTRAL_HOVER,
        text_color=Color.TEXT_WHITE,
    )
    defaults.update(kw)
    return ctk.CTkButton(master, text=text, command=command, **defaults, border_width=1, border_color="#CBD2DC")


def boton_exito(master, text, command=None, **kw):
    defaults = dict(
        font=Font.BUTTON, height=40, corner_radius=Radius.MD,
        fg_color=Color.SUCCESS, hover_color=Color.SUCCESS_HOVER,
        text_color=Color.TEXT_WHITE,
    )
    defaults.update(kw)
    return ctk.CTkButton(master, text=text, command=command, **defaults, border_width=1, border_color="#CBD2DC")


def boton_peligro(master, text, command=None, **kw):
    defaults = dict(
        font=Font.BUTTON, height=40, corner_radius=Radius.MD,
        fg_color=Color.DANGER, hover_color=Color.DANGER_HOVER,
        text_color=Color.TEXT_WHITE,
    )
    defaults.update(kw)
    return ctk.CTkButton(master, text=text, command=command, **defaults, border_width=1, border_color="#CBD2DC")


def boton_volver(master, command=None, **kw):
    defaults = dict(
        text="← Volver", font=Font.BODY_BOLD, height=35, width=110,
        corner_radius=Radius.MD, fg_color=Color.NEUTRAL,
        hover_color=Color.NEUTRAL_HOVER, text_color=Color.TEXT_WHITE,
    )
    defaults.update(kw)
    return ctk.CTkButton(master, command=command, **defaults, border_width=1, border_color="#CBD2DC")


def card(master, **kw):
    defaults = dict(fg_color=Color.BG_CARD, corner_radius=Radius.LG)
    defaults.update(kw)
    return ctk.CTkFrame(master, **defaults)


def titulo(master, text, **kw):
    defaults = dict(font=Font.H1, text_color=Color.ACCENT)
    defaults.update(kw)
    return ctk.CTkLabel(master, text=text, **defaults)


def subtitulo(master, text, **kw):
    defaults = dict(font=Font.H3, text_color=Color.ACCENT)
    defaults.update(kw)
    return ctk.CTkLabel(master, text=text, **defaults)


def etiqueta(master, text, **kw):
    defaults = dict(font=Font.BODY, text_color=Color.TEXT_SECONDARY)
    defaults.update(kw)
    return ctk.CTkLabel(master, text=text, **defaults)


def entry(master, **kw):
    defaults = dict(
        font=Font.BODY, height=38, corner_radius=Radius.SM,
        fg_color=Color.BG_INPUT, border_color=Color.BORDER,
        text_color=Color.TEXT_PRIMARY,
    )
    defaults.update(kw)
    return ctk.CTkEntry(master, **defaults)
