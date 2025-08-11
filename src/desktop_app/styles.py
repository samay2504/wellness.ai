"""
Simplified Qt stylesheet to avoid CSS warnings
"""

SIMPLIFIED_STYLE = """
QMainWindow {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                stop: 0 #0b1220, stop: 0.6 #0f172a, stop: 1 #1e1e3f);
}

QLabel {
    color: #e5e7eb;
    font-family: 'Segoe UI', Arial;
}

QPushButton {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                stop: 0 #4f46e5, stop: 1 #8b5cf6);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 10px;
    padding: 12px 24px;
    font-weight: bold;
    font-size: 14px;
}

QPushButton:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                stop: 0 #5c55ef, stop: 1 #9f74ff);
}

QPushButton:pressed {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                stop: 0 #3f3ce0, stop: 1 #6a5de3);
}

QTextEdit {
    background-color: rgba(255, 255, 255, 0.1);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 8px;
    font-family: 'Courier New', monospace;
}

QProgressBar {
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 5px;
    background-color: rgba(255, 255, 255, 0.1);
}

QProgressBar::chunk {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                stop: 0 #4a5cff, stop: 1 #7367f0);
    border-radius: 3px;
}

QFrame {
    background-color: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
}
"""
