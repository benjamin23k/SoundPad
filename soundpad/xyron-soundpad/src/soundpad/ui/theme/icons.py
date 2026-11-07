from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap, QPolygonF

ICON_NAMES = (
    "play",
    "pause",
    "stop",
    "previous",
    "next",
    "headphones",
    "microphone",
    "volume",
    "settings",
    "app",
)

_cache: dict[tuple[str, str, int], QIcon] = {}


def icon(name: str, color: str = "#d7dade", size: int = 20) -> QIcon:
    if name not in ICON_NAMES:
        raise KeyError(f"Icono desconocido: {name}")
    key = (name, color, size)
    cached = _cache.get(key)
    if cached is not None:
        return cached
    built = QIcon(_render(name, QColor(color), size))
    _cache[key] = built
    return built


def _render(name: str, color: QColor, size: int) -> QPixmap:
    scale = 4
    px = QPixmap(size * scale, size * scale)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(scale, scale)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    _DRAWERS[name](painter, float(size), color)
    painter.end()
    px.setDevicePixelRatio(1.0)
    return px.scaled(
        size * 2,
        size * 2,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def _stroke(color: QColor, width: float) -> QPen:
    pen = QPen(color, width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def _play(p: QPainter, s: float, c: QColor) -> None:
    p.drawPolygon(
        QPolygonF([QPointF(s * 0.30, s * 0.20), QPointF(s * 0.30, s * 0.80), QPointF(s * 0.80, s * 0.50)])
    )


def _pause(p: QPainter, s: float, c: QColor) -> None:
    p.drawRoundedRect(QRectF(s * 0.26, s * 0.22, s * 0.17, s * 0.56), 1, 1)
    p.drawRoundedRect(QRectF(s * 0.57, s * 0.22, s * 0.17, s * 0.56), 1, 1)


def _stop(p: QPainter, s: float, c: QColor) -> None:
    p.drawRoundedRect(QRectF(s * 0.24, s * 0.24, s * 0.52, s * 0.52), 1.5, 1.5)


def _previous(p: QPainter, s: float, c: QColor) -> None:
    p.drawRect(QRectF(s * 0.22, s * 0.22, s * 0.10, s * 0.56))
    p.drawPolygon(
        QPolygonF([QPointF(s * 0.78, s * 0.22), QPointF(s * 0.78, s * 0.78), QPointF(s * 0.36, s * 0.50)])
    )


def _next(p: QPainter, s: float, c: QColor) -> None:
    p.drawRect(QRectF(s * 0.68, s * 0.22, s * 0.10, s * 0.56))
    p.drawPolygon(
        QPolygonF([QPointF(s * 0.22, s * 0.22), QPointF(s * 0.22, s * 0.78), QPointF(s * 0.64, s * 0.50)])
    )


def _headphones(p: QPainter, s: float, c: QColor) -> None:
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(_stroke(c, s * 0.09))
    arc = QPainterPath()
    arc.moveTo(s * 0.20, s * 0.62)
    arc.arcTo(QRectF(s * 0.20, s * 0.16, s * 0.60, s * 0.60), 180, -180)
    p.drawPath(arc)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(c)
    p.drawRoundedRect(QRectF(s * 0.14, s * 0.52, s * 0.18, s * 0.30), 2, 2)
    p.drawRoundedRect(QRectF(s * 0.68, s * 0.52, s * 0.18, s * 0.30), 2, 2)


def _microphone(p: QPainter, s: float, c: QColor) -> None:
    p.drawRoundedRect(QRectF(s * 0.38, s * 0.12, s * 0.24, s * 0.44), s * 0.12, s * 0.12)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(_stroke(c, s * 0.08))
    arc = QPainterPath()
    arc.moveTo(s * 0.26, s * 0.44)
    arc.arcTo(QRectF(s * 0.26, s * 0.28, s * 0.48, s * 0.44), 180, 180)
    p.drawPath(arc)
    p.drawLine(QPointF(s * 0.50, s * 0.72), QPointF(s * 0.50, s * 0.86))
    p.drawLine(QPointF(s * 0.36, s * 0.86), QPointF(s * 0.64, s * 0.86))


def _volume(p: QPainter, s: float, c: QColor) -> None:
    p.drawPolygon(
        QPolygonF(
            [
                QPointF(s * 0.16, s * 0.40),
                QPointF(s * 0.34, s * 0.40),
                QPointF(s * 0.54, s * 0.22),
                QPointF(s * 0.54, s * 0.78),
                QPointF(s * 0.34, s * 0.60),
                QPointF(s * 0.16, s * 0.60),
            ]
        )
    )
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(_stroke(c, s * 0.07))
    first = QPainterPath()
    first.arcMoveTo(QRectF(s * 0.40, s * 0.34, s * 0.32, s * 0.32), 45)
    first.arcTo(QRectF(s * 0.40, s * 0.34, s * 0.32, s * 0.32), 45, -90)
    p.drawPath(first)
    second = QPainterPath()
    second.arcMoveTo(QRectF(s * 0.34, s * 0.22, s * 0.52, s * 0.56), 45)
    second.arcTo(QRectF(s * 0.34, s * 0.22, s * 0.52, s * 0.56), 45, -90)
    p.drawPath(second)


def _settings(p: QPainter, s: float, c: QColor) -> None:
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(_stroke(c, s * 0.08))
    for y in (0.28, 0.50, 0.72):
        p.drawLine(QPointF(s * 0.18, s * y), QPointF(s * 0.82, s * y))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(c)
    for x, y in ((0.36, 0.28), (0.64, 0.50), (0.44, 0.72)):
        p.drawEllipse(QPointF(s * x, s * y), s * 0.09, s * 0.09)


def _app(p: QPainter, s: float, c: QColor) -> None:
    accent = QColor("#3b82d6")
    p.setBrush(accent)
    p.drawRoundedRect(QRectF(s * 0.06, s * 0.06, s * 0.88, s * 0.88), s * 0.2, s * 0.2)
    p.setBrush(QColor("#ffffff"))
    for index, (x, h) in enumerate(((0.22, 0.30), (0.36, 0.50), (0.50, 0.36), (0.64, 0.58))):
        top = s * 0.5 - s * h / 2
        p.drawRoundedRect(QRectF(s * x, top, s * 0.09, s * h), 1, 1)


_DRAWERS = {
    "play": _play,
    "pause": _pause,
    "stop": _stop,
    "previous": _previous,
    "next": _next,
    "headphones": _headphones,
    "microphone": _microphone,
    "volume": _volume,
    "settings": _settings,
    "app": _app,
}
