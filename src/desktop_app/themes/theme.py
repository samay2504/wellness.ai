"""
Lightweight theme utilities for the PyQt6 desktop UI.
Applies a subtle futuristic vibe: dark-on-light text, rounded corners,
soft gradients, and an optional accent color.
"""

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import QEasingCurve, QPropertyAnimation


ACCENT = "#3b82f6"  # Tailwind blue-500
BG_GRADIENT = (
    "QWidget {"
    "background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
    " stop:0 #0f172a, stop:1 #111827);"
    "color: #e5e7eb;"
    "font-family: 'Segoe UI', 'Inter', 'Arial';"
    "}"
)

BASE_STYLE = f"""
QMainWindow {{
  background: transparent;
}}
QLabel {{
  color: #e5e7eb;
}}
QFrame {{
  background-color: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
}}
QPushButton {{
  background-color: {ACCENT};
  color: white;
  border: none;
  padding: 10px 18px;
  border-radius: 10px;
  font-weight: 600;
}}
QPushButton:hover {{
  background-color: #2563eb;
}}
QProgressBar {{
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 8px;
  text-align: center;
  background-color: rgba(255,255,255,0.06);
  color: #cbd5e1;
}}
QProgressBar::chunk {{
  background-color: {ACCENT};
  border-radius: 8px;
}}
"""


def apply_theme(root: QWidget) -> None:
    """Apply gradient background and base styles, with a soft fade-in."""
    app = QApplication.instance()
    if app:
        app.setStyleSheet(BG_GRADIENT + BASE_STYLE)

    try:
        root.setWindowOpacity(0.0)
        fade = QPropertyAnimation(root, b"windowOpacity")
        fade.setDuration(350)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.Type.InOutCubic)
        fade.start()
        # Keep ref to avoid GC if needed
        setattr(root, "_fade_anim", fade)
    except Exception:
        pass
