from docx.shared import Inches, Pt, RGBColor

# Typography Font Families
PRIMARY_FONT = "Calibri"
SECONDARY_FONT = "Calibri Light"

# Color Palette (Corporate Blue Theme)
COLOR_PRIMARY = RGBColor(26, 82, 118)     # Navy Blue
COLOR_SECONDARY = RGBColor(93, 109, 126) # Slate Grey
COLOR_TEXT = RGBColor(43, 43, 43)         # Charcoal
COLOR_ACCENT = RGBColor(230, 126, 34)     # Warm Orange
COLOR_MUTED = RGBColor(128, 128, 128)     # Light Grey
COLOR_WARNING = RGBColor(192, 57, 43)     # Red (used for placeholders/missing info)

# Font Sizes
SIZE_TITLE = Pt(28)
SIZE_SUBTITLE = Pt(14)
SIZE_H1 = Pt(18)
SIZE_H2 = Pt(14)
SIZE_BODY = Pt(11)
SIZE_CAPTION = Pt(9)

# Spacing and Layout
SPACING_LINE = 1.15
SPACING_PARAGRAPH_AFTER = Pt(6)
MARGIN_INCHES = Inches(1.0)
