
from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)


class FullRowCheckBox(QCheckBox):
    """Cho phép bấm toàn bộ chiều rộng của dòng Select All."""

    def hitButton(self, position):
        return self.rect().contains(position)


class RowCheckListWidget(QListWidget):
    """Bấm vào bất kỳ vị trí nào trên dòng để đổi checkbox."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pressed_item = None
        self._pressed_state = Qt.Unchecked

    def mousePressEvent(self, event):
        self._pressed_item = self.itemAt(event.pos())

        if self._pressed_item is not None:
            self._pressed_state = self._pressed_item.checkState()

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        released_item = self.itemAt(event.pos())
        pressed_item = self._pressed_item
        pressed_state = self._pressed_state

        super().mouseReleaseEvent(event)

        if released_item is not None and released_item is pressed_item:
            released_item.setCheckState(
                Qt.Unchecked
                if pressed_state == Qt.Checked
                else Qt.Checked
            )

        self._pressed_item = None


class FilterValueDialog(QDialog):
    """Dialog tìm kiếm và chọn nhiều Month hoặc Date."""

    selection_changed = pyqtSignal(object)

    def __init__(
        self,
        title: str,
        values: list[str],
        selected_values: set[str],
        apply_immediately: bool = False,
        compact: bool = False,
        parent=None,
    ):
        super().__init__(parent)

        self._values = list(values)
        self._updating_select_all = False
        self._apply_immediately = apply_immediately

        self.setWindowTitle(title)
        self.setModal(True)

        if compact:
            compact_height = min(
                350,
                max(245, 180 + len(self._values) * 24),
            )
            self.resize(300, compact_height)
        else:
            self.resize(330, 480)

        self._build_ui(selected_values)

    def _build_ui(
        self,
        selected_values: set[str],
    ) -> None:
        """Tạo dialog lọc tương tự giao diện trong ảnh."""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            14,
            14,
            14,
            14,
        )
        layout.setSpacing(10)

        title_label = QLabel(
            "Filter by value:"
        )

        title_label.setStyleSheet(
            "font-weight: 600; "
            "color: #0F172A;"
        )

        layout.addWidget(title_label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "Search"
        )
        self.search_edit.setFixedHeight(32)

        layout.addWidget(
            self.search_edit
        )

        checkbox_class = (
            FullRowCheckBox
            if self._apply_immediately
            else QCheckBox
        )
        self.select_all_checkbox = checkbox_class("Select All")
        self.select_all_checkbox.setTristate(
            True
        )
        if self._apply_immediately:
            self.select_all_checkbox.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed,
            )

        layout.addWidget(
            self.select_all_checkbox
        )

        list_widget_class = (
            RowCheckListWidget
            if self._apply_immediately
            else QListWidget
        )
        self.list_widget = list_widget_class()

        self.list_widget.setAlternatingRowColors(
            True
        )

        for value in self._values:
            item = QListWidgetItem(value)

            item.setFlags(
                item.flags()
                | Qt.ItemIsUserCheckable
            )

            item.setCheckState(
                Qt.Checked
                if value in selected_values
                else Qt.Unchecked
            )

            self.list_widget.addItem(item)

        layout.addWidget(
            self.list_widget,
            1,
        )

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        close_button = QPushButton(
            "Close" if self._apply_immediately else "Cancel"
        )
        close_button.setFixedHeight(32)

        if self._apply_immediately:
            close_button.setFixedWidth(100)
            button_layout.addStretch(1)
            button_layout.addWidget(close_button)
        else:
            ok_button = QPushButton("OK")
            ok_button.setFixedHeight(34)
            close_button.setFixedHeight(34)

            ok_button.setStyleSheet(
                """
                QPushButton {
                    background-color: #1976D2;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-weight: 600;
                }

                QPushButton:hover {
                    background-color: #1565C0;
                }
                """
            )

            button_layout.addWidget(ok_button, 1)
            button_layout.addWidget(close_button, 1)
            ok_button.clicked.connect(self.accept)

        layout.addLayout(button_layout)

        self.search_edit.textChanged.connect(
            self._apply_search
        )

        self.select_all_checkbox.stateChanged.connect(
            self._set_all_checked
        )

        self.list_widget.itemChanged.connect(
            self._on_item_changed
        )

        close_button.clicked.connect(
            self.reject
        )

        self._update_select_all_state()
        self.search_edit.setFocus()

    def _on_item_changed(self, _item=None) -> None:
        """Đồng bộ Select All và áp dụng ngay nếu được yêu cầu."""
        self._update_select_all_state()
        self._emit_selection_changed()

    def _emit_selection_changed(self) -> None:
        if self._apply_immediately:
            self.selection_changed.emit(
                self.selected_values()
            )

    def selected_values(self) -> set[str]:
        """Trả các giá trị đang được tích chọn."""

        return {
            self.list_widget.item(index).text()
            for index in range(
                self.list_widget.count()
            )
            if (
                self.list_widget.item(
                    index
                ).checkState()
                == Qt.Checked
            )
        }

    def _apply_search(
        self,
        search_text: str,
    ) -> None:
        """Search không làm mất trạng thái checkbox."""

        normalized_search = (
            search_text.strip().lower()
        )

        for index in range(
            self.list_widget.count()
        ):
            item = self.list_widget.item(
                index
            )

            item.setHidden(
                normalized_search
                not in item.text().lower()
            )

    def _set_all_checked(
        self,
        state: int,
    ) -> None:
        """Chọn hoặc bỏ chọn toàn bộ giá trị."""

        if self._updating_select_all:
            return

        target_state = (
            Qt.Checked
            if state != Qt.Unchecked
            else Qt.Unchecked
        )

        self.list_widget.blockSignals(True)

        try:
            for index in range(
                self.list_widget.count()
            ):
                self.list_widget.item(
                    index
                ).setCheckState(
                    target_state
                )

        finally:
            self.list_widget.blockSignals(
                False
            )

        self._update_select_all_state()
        self._emit_selection_changed()

    def _update_select_all_state(
        self,
        _item=None,
    ) -> None:
        """Đồng bộ Select All theo danh sách."""

        total_count = (
            self.list_widget.count()
        )

        checked_count = sum(
            1
            for index in range(total_count)
            if (
                self.list_widget.item(
                    index
                ).checkState()
                == Qt.Checked
            )
        )

        if checked_count == 0:
            state = Qt.Unchecked

        elif checked_count == total_count:
            state = Qt.Checked

        else:
            state = Qt.PartiallyChecked

        self._updating_select_all = True

        self.select_all_checkbox.blockSignals(
            True
        )

        try:
            self.select_all_checkbox.setCheckState(
                state
            )

        finally:
            self.select_all_checkbox.blockSignals(
                False
            )

            self._updating_select_all = False
