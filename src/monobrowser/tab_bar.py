from PyQt6.QtCore import QEvent, QRect, QSize, Qt
from PyQt6.QtGui import (
    QColor,
    QFontMetrics,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt6.QtWidgets import QTabBar, QWidget

TABSTRIP_BG = QColor("#F1F3F4")
TAB_ACTIVE_BG = QColor("#FFFFFF")
TAB_HOVER_BG = QColor("#E7E9ED")

TEXT_ACTIVE = QColor("#202124")
TEXT_INACTIVE = QColor("#5F6368")

BORDER = QColor("#DADCE0")
CLOSE_HOVER_BG = QColor("#DADCE0")
CLOSE_GLYPH = QColor("#5F6368")


TAB_HEIGHT = 36

MIN_TAB_WIDTH = 110
MAX_TAB_WIDTH = 240

ICON_SIZE = 16
ICON_TEXT_GAP = 8

H_PAD = 10

CLOSE_DIAMETER = 22

TAB_RADIUS = 9


class ChromeTabBar(QTabBar):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setDrawBase(False)

        self.setMovable(True)
        self.setExpanding(False)

        self.setMouseTracking(True)

        self.setUsesScrollButtons(True)

        self.setTabsClosable(False)

        self._hover_tab = -1
        self._hover_close = False

        self._close_rects: dict[int, QRect] = {}

        font = self.font()
        font.setPointSize(10)
        self.setFont(font)

        self.setFixedHeight(TAB_HEIGHT + 2)

    def tabSizeHint(self, index: int) -> QSize:
        metrics = QFontMetrics(self.font())

        text_width = metrics.horizontalAdvance(self.tabText(index))

        icon_width = 0

        if not self.tabIcon(index).isNull():
            icon_width = ICON_SIZE + ICON_TEXT_GAP

        width = H_PAD + icon_width + text_width + ICON_TEXT_GAP + CLOSE_DIAMETER + H_PAD

        width = max(MIN_TAB_WIDTH, width)
        width = min(MAX_TAB_WIDTH, width)

        return QSize(width, TAB_HEIGHT)

    def minimumTabSizeHint(self, index: int) -> QSize:
        del index

        return QSize(
            MIN_TAB_WIDTH,
            TAB_HEIGHT,
        )

    def paintEvent(self, event) -> None:
        del event

        painter = QPainter(self)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        painter.fillRect(
            self.rect(),
            TABSTRIP_BG,
        )

        self._close_rects.clear()

        current = self.currentIndex()

        for i in range(self.count()):
            if i != current:
                self._paint_tab(
                    painter,
                    i,
                    active=False,
                )

        if current >= 0:
            self._paint_tab(
                painter,
                current,
                active=True,
            )

        painter.end()

    def _tab_path(
        self,
        rect: QRect,
    ) -> QPainterPath:

        x = rect.left()
        y = rect.top()

        w = rect.width()
        h = rect.height()

        radius = TAB_RADIUS

        path = QPainterPath()

        path.moveTo(
            x,
            y + h,
        )

        path.lineTo(
            x,
            y + radius,
        )

        path.quadTo(
            x,
            y,
            x + radius,
            y,
        )

        path.lineTo(
            x + w - radius,
            y,
        )

        path.quadTo(
            x + w,
            y,
            x + w,
            y + radius,
        )

        path.lineTo(
            x + w,
            y + h,
        )

        path.closeSubpath()

        return path

    def _paint_tab(
        self,
        painter: QPainter,
        index: int,
        active: bool,
    ) -> None:

        rect = self.tabRect(index)

        if rect.isEmpty():
            return

        rect = QRect(
            rect.left(),
            rect.top(),
            rect.width(),
            rect.height(),
        )

        if active:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(TAB_ACTIVE_BG)

            painter.drawPath(self._tab_path(rect))

        elif index == self._hover_tab:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(TAB_HOVER_BG)

            painter.drawPath(self._tab_path(rect))

        if active:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(
                QPen(
                    BORDER,
                    1,
                )
            )

            painter.drawPath(self._tab_path(rect))

        content_left = rect.left() + H_PAD
        content_right = rect.right() - H_PAD

        center_y = rect.center().y()

        show_close = active or index == self._hover_tab

        close_rect = QRect()

        if show_close:
            close_rect = QRect(
                content_right - CLOSE_DIAMETER,
                center_y - CLOSE_DIAMETER // 2,
                CLOSE_DIAMETER,
                CLOSE_DIAMETER,
            )

            if index == self._hover_tab and self._hover_close:
                painter.setPen(Qt.PenStyle.NoPen)

                painter.setBrush(CLOSE_HOVER_BG)

                painter.drawEllipse(close_rect)

            self._paint_close_icon(
                painter,
                close_rect,
            )

        self._close_rects[index] = close_rect

        text_right = close_rect.left() - 4 if show_close else content_right

        x = content_left

        icon = self.tabIcon(index)

        if not icon.isNull():
            pixmap = icon.pixmap(
                QSize(
                    ICON_SIZE,
                    ICON_SIZE,
                )
            )

            painter.drawPixmap(
                x,
                center_y - ICON_SIZE // 2,
                pixmap,
            )

            x += ICON_SIZE + ICON_TEXT_GAP

        available = text_right - x

        if available <= 0:
            return

        metrics = QFontMetrics(self.font())

        text = metrics.elidedText(
            self.tabText(index),
            Qt.TextElideMode.ElideRight,
            available,
        )

        painter.setPen(TEXT_ACTIVE if active else TEXT_INACTIVE)

        painter.drawText(
            QRect(
                x,
                rect.top(),
                available,
                rect.height(),
            ),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            text,
        )

    def _paint_close_icon(
        self,
        painter: QPainter,
        rect: QRect,
    ) -> None:

        painter.save()

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(
            QPen(
                CLOSE_GLYPH,
                1.5,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )

        margin = 7

        x1 = rect.left() + margin
        y1 = rect.top() + margin

        x2 = rect.right() - margin
        y2 = rect.bottom() - margin

        painter.drawLine(
            x1,
            y1,
            x2,
            y2,
        )

        painter.drawLine(
            x2,
            y1,
            x1,
            y2,
        )

        painter.restore()

    def mousePressEvent(
        self,
        event: QMouseEvent | None,
    ) -> None:

        if event is None:
            return

        pos = event.pos()

        if event.button() == Qt.MouseButton.LeftButton:
            index = self.tabAt(pos)

            if index >= 0:
                close_rect = self._close_rects.get(
                    index,
                    QRect(),
                )

                if close_rect.contains(pos):
                    self.tabCloseRequested.emit(index)

                    event.accept()
                    return

        if event.button() == Qt.MouseButton.MiddleButton:
            index = self.tabAt(pos)

            if index >= 0:
                self.tabCloseRequested.emit(index)

                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(
        self,
        event: QMouseEvent | None,
    ) -> None:

        if event is None:
            return

        pos = event.pos()

        index = self.tabAt(pos)

        close_hover = index >= 0 and self._close_rects.get(
            index,
            QRect(),
        ).contains(pos)

        new_state = (
            index,
            close_hover,
        )

        if new_state != (
            self._hover_tab,
            self._hover_close,
        ):
            self._hover_tab, self._hover_close = new_state

            if self._hover_close:
                self.setCursor(Qt.CursorShape.PointingHandCursor)

            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

            self.update()

        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QEvent | None) -> None:

        self._hover_tab = -1
        self._hover_close = False

        self.setCursor(Qt.CursorShape.ArrowCursor)

        self.update()

        super().leaveEvent(event)
