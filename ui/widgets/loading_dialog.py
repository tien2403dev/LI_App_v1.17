from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class LoadingSpinner(QWidget):
    """Spinner nhẹ dùng chung cho SEARCH và IMPORT."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0
        self.setFixedSize(36, 36)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.start(30)

    def _rotate(self) -> None:
        self._angle = (self._angle + 10) % 360
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(4, 4, -4, -4)

        outer_pen = QPen(QColor(170, 190, 215))
        outer_pen.setWidth(3)
        painter.setPen(outer_pen)
        painter.drawEllipse(rect)

        arc_pen = QPen(QColor(115, 150, 195))
        arc_pen.setWidth(3)
        arc_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(arc_pen)
        painter.drawArc(rect, -self._angle * 16, 120 * 16)

        inner_pen = QPen(QColor(210, 219, 229))
        inner_pen.setWidth(2)
        painter.setPen(inner_pen)
        painter.drawEllipse(rect.adjusted(7, 7, -7, -7))


class LoadingDialog(QDialog):
    """Dialog loading giống Aging, dùng cho tác vụ chạy nền."""

    def __init__(self, parent=None, text: str = "Loading ...", title: str = "Please Wait"):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setFixedSize(260, 90)

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(18, 14, 18, 14)
        root_layout.setSpacing(10)

        self.spinner = LoadingSpinner(self)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(1)

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 500;
                color: #000000;
                background: transparent;
            }
        """)

        self.loading_label = QLabel(text)
        self.loading_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.loading_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #1f1f1f;
                background: transparent;
            }
        """)

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.loading_label)
        root_layout.addWidget(self.spinner, alignment=Qt.AlignVCenter)
        root_layout.addLayout(text_layout)
        root_layout.addStretch()

    def set_text(self, text: str) -> None:
        self.loading_label.setText(text)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(241, 245, 249))

        border_pen = QPen(QColor(190, 200, 212))
        border_pen.setWidth(1)
        painter.setPen(border_pen)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
