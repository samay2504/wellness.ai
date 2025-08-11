#!/usr/bin/env python3
"""
Wellness AI Desktop Icon Generator
Creates a modern, professional icon for the desktop application
"""

from PyQt6.QtGui import QPixmap, QPainter, QPen, QBrush, QColor, QFont, QRadialGradient, QPolygon
from PyQt6.QtCore import Qt, QRect, QPoint

def create_wellness_icon(size=512):
    """Create a modern wellness AI icon"""
    # Create pixmap
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Background gradient (calming blue to green)
    gradient = QRadialGradient(size/2, size/2, size/2)
    gradient.setColorAt(0, QColor(64, 224, 208))  # Turquoise
    gradient.setColorAt(0.7, QColor(72, 201, 176))  # Teal
    gradient.setColorAt(1, QColor(56, 178, 172))  # Dark teal
    
    painter.setBrush(QBrush(gradient))
    painter.setPen(QPen(QColor(255, 255, 255, 80), 4))
    painter.drawEllipse(20, 20, size-40, size-40)
    
    # Central wellness symbol (brain + heart)
    painter.setPen(QPen(Qt.GlobalColor.white, 8))
    painter.setBrush(QBrush(Qt.GlobalColor.white))
    
    # Brain outline
    brain_rect = QRect(size//2 - 60, size//2 - 80, 120, 80)
    painter.drawEllipse(brain_rect)
    
    # Brain details
    painter.setPen(QPen(QColor(64, 224, 208), 3))
    for i in range(3):
        y_offset = -30 + (i * 20)
        painter.drawLine(size//2 - 40, size//2 + y_offset, size//2 + 40, size//2 + y_offset)
    
    # Heart shape (below brain)
    painter.setPen(QPen(Qt.GlobalColor.white, 6))
    painter.setBrush(QBrush(QColor(255, 99, 132)))  # Pink heart
    
    heart_size = 40
    heart_x = size//2 - heart_size//2
    heart_y = size//2 + 20
    
    # Heart left curve
    painter.drawEllipse(heart_x - 10, heart_y, heart_size//2, heart_size//2)
    # Heart right curve  
    painter.drawEllipse(heart_x + 10, heart_y, heart_size//2, heart_size//2)
    # Heart bottom point
    points = [
        (heart_x - 10, heart_y + heart_size//4),
        (heart_x + heart_size + 10, heart_y + heart_size//4),
        (heart_x + heart_size//2, heart_y + heart_size)
    ]
    painter.drawPolygon([QPoint(x, y) for x, y in points])
    
    # AI accent dots
    painter.setBrush(QBrush(Qt.GlobalColor.yellow))
    painter.setPen(QPen(Qt.GlobalColor.transparent))
    
    # Orbiting dots around the main symbol
    import math
    for i in range(8):
        angle = (i * 45) * math.pi / 180
        x = size//2 + 100 * math.cos(angle) - 6
        y = size//2 + 100 * math.sin(angle) - 6
        painter.drawEllipse(int(x), int(y), 12, 12)
    
    # Text overlay
    painter.setPen(QPen(Qt.GlobalColor.white))
    font = QFont("Arial", max(24, size//20), QFont.Weight.Bold)
    painter.setFont(font)
    
    text_rect = QRect(0, size - 80, size, 60)
    painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "WellnessAI")
    
    painter.end()
    return pixmap

def save_icon_formats():
    """Save icon in multiple formats for different uses"""
    import os
    
    # Create assets directory
    assets_dir = os.path.dirname(__file__)
    os.makedirs(assets_dir, exist_ok=True)
    
    # Generate different sizes
    sizes = [16, 32, 48, 64, 128, 256, 512]
    
    for size in sizes:
        icon = create_wellness_icon(size)
        icon.save(os.path.join(assets_dir, f"wellness_icon_{size}.png"))
    
    # Main icon for PyInstaller
    main_icon = create_wellness_icon(512)
    main_icon.save(os.path.join(assets_dir, "wellness_icon.png"))
    main_icon.save(os.path.join(assets_dir, "wellness_icon.ico"))
    
    print(f"Icons saved to: {assets_dir}")
    return os.path.join(assets_dir, "wellness_icon.ico")

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    save_icon_formats()
    app.quit()
