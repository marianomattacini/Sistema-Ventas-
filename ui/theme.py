"""
Tema visual unificado del Sistema de Gestión de Ventas y Control de Stock.

Centraliza colores, fuentes y helpers de estilo para que TODAS las
pantallas (frames) usen exactamente la misma paleta e interacciones
(hover, focus, disabled, éxito/error). Basado en la identidad Arena Premium: neutros cálidos, café estructural,
terracota para acciones y colores semánticos accesibles. La paleta se aplica
de forma uniforme sin alterar la lógica ni el comportamiento del sistema.
"""

import customtkinter as ctk

# ---------------------------------------------------------------------------
# PALETA DE COLORES — ARENA PREMIUM
# ---------------------------------------------------------------------------
class Color:
    # Fondos
    BG_APP = "#F5EFE7"          # fondo general de la app (contenido principal)
    BG_BASE = "#EAE0D3"         # fondo de paneles/secciones
    BG_CARD = "#FBF8F3"         # tarjetas / contenedores
    BG_CARD_ALT = "#F1EAE1"     # variante levemente distinta para anidar
    BG_INPUT = "#FFFDF9"        # fondo de inputs
    BORDER = "#BFAE9A"

    # Texto
    TEXT_PRIMARY = "#2A241F"
    TEXT_SECONDARY = "#5E5144"
    TEXT_MUTED = "#786957"
    TEXT_WHITE = "#FFFFFF"

    # Identidad Arena Premium (café estructural + terracota de acción)
    ACCENT = "#7A5C45"
    ACCENT_HOVER = "#624836"
    ACCENT_STRONG = "#A24C2F"

    # Sidebar
    SIDEBAR_BG = "#EAE0D3"
    SIDEBAR_ITEM_HOVER = "#D9CCBC"
    SIDEBAR_ITEM_ACTIVE = "#7A5C45"
    SIDEBAR_ITEM_ACTIVE_TEXT = "#FFFFFF"

    # Semánticos
    SUCCESS = "#2F6B4F"
    SUCCESS_HOVER = "#24563F"
    WARNING = "#A15C00"
    WARNING_HOVER = "#824900"
    DANGER = "#B43B32"
    DANGER_HOVER = "#922F28"
    INFO = "#3F6478"
    INFO_HOVER = "#315064"
    VIOLET = "#3F6478"
    VIOLET_HOVER = "#315064"
    NEUTRAL = "#8D735D"
    NEUTRAL_HOVER = "#705B49"


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
# TAMAÑOS ESTÁNDAR (fuente única de verdad para TODAS las pantallas)
# ---------------------------------------------------------------------------
class Sizes:
    BUTTON_HEIGHT = 40   # alto único de todos los botones de acción
    BUTTON_WIDTH = 160   # ancho por defecto de los botones de acción
    INPUT_HEIGHT = 38    # alto único de todos los campos de texto
    COMPACT_HEIGHT = 25  # alto de botones compactos (filas de tabla / filtros)
    COMPACT_WIDTH = 80   # ancho de botones compactos


# ---------------------------------------------------------------------------
# CONFIGURACIÓN GLOBAL DE CUSTOMTKINTER
# ---------------------------------------------------------------------------
def aplicar_tema_global():
    ctk.set_appearance_mode("light")
    # Se carga el tema base de CustomTkinter y se reemplazan sus acentos
    # predeterminados para evitar controles azules en pantallas que no
    # especifican un color de forma explícita.
    ctk.set_default_color_theme("blue")

    try:
        tema = ctk.ThemeManager.theme
        overrides = {
            "CTkButton": {"fg_color": Color.ACCENT_STRONG, "hover_color": Color.ACCENT_HOVER},
            "CTkCheckBox": {"fg_color": Color.ACCENT_STRONG, "hover_color": Color.ACCENT_HOVER},
            "CTkRadioButton": {"fg_color": Color.ACCENT_STRONG, "hover_color": Color.ACCENT_HOVER},
            "CTkComboBox": {"button_color": Color.ACCENT, "button_hover_color": Color.ACCENT_HOVER},
            "CTkOptionMenu": {"fg_color": Color.ACCENT, "button_color": Color.ACCENT_STRONG, "button_hover_color": Color.ACCENT_HOVER},
            "CTkProgressBar": {"progress_color": Color.ACCENT_STRONG},
            "CTkSlider": {"button_color": Color.ACCENT_STRONG, "button_hover_color": Color.ACCENT_HOVER, "progress_color": Color.ACCENT},
            "CTkScrollbar": {"button_color": Color.BORDER, "button_hover_color": Color.NEUTRAL},
            "CTkSegmentedButton": {"selected_color": Color.ACCENT, "selected_hover_color": Color.ACCENT_HOVER, "unselected_hover_color": Color.BG_BASE},
        }
        for widget, valores in overrides.items():
            if widget in tema:
                tema[widget].update(valores)
    except (AttributeError, TypeError):
        # Compatibilidad con versiones de CustomTkinter sin ThemeManager público.
        pass


# ---------------------------------------------------------------------------
# HELPERS DE WIDGETS ESTILIZADOS (para no repetir fg_color/hover en cada vista)
# ---------------------------------------------------------------------------
def boton_primario(master, text, command=None, **kw):
    defaults = dict(
        font=Font.BUTTON, height=Sizes.BUTTON_HEIGHT, width=Sizes.BUTTON_WIDTH,
        corner_radius=Radius.MD,
        fg_color=Color.ACCENT_STRONG, hover_color=Color.ACCENT_HOVER,
        text_color=Color.TEXT_WHITE,
    )
    defaults.update(kw)
    return ctk.CTkButton(master, text=text, command=command, **defaults, border_width=2, border_color="#BFAE9A")


def boton_secundario(master, text, command=None, **kw):
    defaults = dict(
        font=Font.BUTTON, height=Sizes.BUTTON_HEIGHT, width=Sizes.BUTTON_WIDTH,
        corner_radius=Radius.MD,
        fg_color=Color.NEUTRAL, hover_color=Color.NEUTRAL_HOVER,
        text_color=Color.TEXT_WHITE,
    )
    defaults.update(kw)
    return ctk.CTkButton(master, text=text, command=command, **defaults, border_width=2, border_color="#BFAE9A")


def boton_exito(master, text, command=None, **kw):
    defaults = dict(
        font=Font.BUTTON, height=Sizes.BUTTON_HEIGHT, width=Sizes.BUTTON_WIDTH,
        corner_radius=Radius.MD,
        fg_color=Color.SUCCESS, hover_color=Color.SUCCESS_HOVER,
        text_color=Color.TEXT_WHITE,
    )
    defaults.update(kw)
    return ctk.CTkButton(master, text=text, command=command, **defaults, border_width=2, border_color="#BFAE9A")


def boton_peligro(master, text, command=None, **kw):
    defaults = dict(
        font=Font.BUTTON, height=Sizes.BUTTON_HEIGHT, width=Sizes.BUTTON_WIDTH,
        corner_radius=Radius.MD,
        fg_color=Color.DANGER, hover_color=Color.DANGER_HOVER,
        text_color=Color.TEXT_WHITE,
    )
    defaults.update(kw)
    return ctk.CTkButton(master, text=text, command=command, **defaults, border_width=2, border_color="#BFAE9A")


def boton_volver(master, command=None, **kw):
    defaults = dict(
        text="← Volver", font=Font.BODY_BOLD, height=Sizes.BUTTON_HEIGHT,
        width=Sizes.BUTTON_WIDTH,
        corner_radius=Radius.MD, fg_color=Color.NEUTRAL,
        hover_color=Color.NEUTRAL_HOVER, text_color=Color.TEXT_WHITE,
    )
    defaults.update(kw)
    return ctk.CTkButton(master, command=command, **defaults, border_width=2, border_color="#BFAE9A")


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
        font=Font.BODY, height=Sizes.INPUT_HEIGHT, corner_radius=Radius.SM,
        fg_color=Color.BG_INPUT, border_color=Color.BORDER,
        text_color=Color.TEXT_PRIMARY,
    )
    defaults.update(kw)
    return ctk.CTkEntry(master, **defaults)
