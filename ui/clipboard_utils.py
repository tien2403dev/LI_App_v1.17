from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction, QApplication, QAbstractItemView


def copy_selected_table_cells(table, copy_all=False):
    """Copy TSV kèm tiêu đề cột và tiêu đề hàng đang được sử dụng."""
    model = table.model()
    if model is None or model.columnCount() == 0:
        return
    selected = {(i.row(), i.column()) for i in table.selectedIndexes()}
    if copy_all:
        rows = range(model.rowCount())
        columns = range(model.columnCount())
    elif selected:
        rows = range(min(r for r, _ in selected), max(r for r, _ in selected) + 1)
        columns = range(min(c for _, c in selected), max(c for _, c in selected) + 1)
    else:
        return

    def text(value):
        return '' if value is None else str(value)

    # isHidden kiểm tra header bị ẩn chủ động, kể cả tab chưa được mở.
    row_headers = not table.verticalHeader().isHidden()
    headers = [text(model.headerData(c, Qt.Horizontal, Qt.DisplayRole)) for c in columns]
    if row_headers:
        headers.insert(0, text(table.property('copy_corner_label')))
    lines = ['\t'.join(headers)]
    for row in rows:
        values = ([text(model.headerData(row, Qt.Vertical, Qt.DisplayRole))]
                  if row_headers else [])
        for column in columns:
            value = (model.index(row, column).data(Qt.DisplayRole)
                     if copy_all or (row, column) in selected else '')
            values.append(text(value))
        lines.append('\t'.join(values))

    QApplication.clipboard().setText('\n'.join(lines))


def enable_table_copy(table):
    """Cho phép chọn ô, Ctrl+C và menu chuột phải trên QTableView/QTableWidget."""
    table.setSelectionMode(QAbstractItemView.ExtendedSelection)
    table.setSelectionBehavior(QAbstractItemView.SelectItems)

    copy_action = QAction('Copy selection with headers', table)
    copy_action.setShortcut(QKeySequence.Copy)
    copy_action.setShortcutContext(Qt.WidgetShortcut)
    copy_action.triggered.connect(lambda: copy_selected_table_cells(table))
    table.addAction(copy_action)

    copy_all_action = QAction('Copy entire table with headers', table)
    copy_all_action.setShortcut(QKeySequence('Ctrl+Shift+C'))
    copy_all_action.setShortcutContext(Qt.WidgetShortcut)
    copy_all_action.triggered.connect(lambda: copy_selected_table_cells(table, copy_all=True))
    table.addAction(copy_all_action)

    select_all_action = QAction('Select all', table)
    select_all_action.setShortcut(QKeySequence.SelectAll)
    select_all_action.setShortcutContext(Qt.WidgetShortcut)
    select_all_action.triggered.connect(table.selectAll)
    table.addAction(select_all_action)

    table.setContextMenuPolicy(Qt.ActionsContextMenu)


def enable_chart_copy(chart):
    """Cho phép click chọn canvas rồi Ctrl+C hoặc chuột phải để copy ảnh."""
    chart.setFocusPolicy(Qt.StrongFocus)

    copy_action = QAction('Copy chart as image', chart)
    copy_action.setShortcut(QKeySequence.Copy)
    copy_action.setShortcutContext(Qt.WidgetShortcut)
    copy_action.triggered.connect(
        lambda: QApplication.clipboard().setPixmap(chart.grab())
    )
    chart.addAction(copy_action)
    chart.setContextMenuPolicy(Qt.ActionsContextMenu)
    chart.setToolTip('Bấm vào biểu đồ rồi nhấn Ctrl+C để sao chép ảnh.')
