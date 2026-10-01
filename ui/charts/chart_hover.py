"""Shared Qt hover tooltips; no database queries or extra dependencies."""
from html import escape
import math
from types import SimpleNamespace

import numpy as np
from PyQt5.QtCore import QEvent, QObject, QRect
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QToolTip


def number(value, suffix=''):
    if value is None or not math.isfinite(float(value)):
        return 'N/A'
    return (f'{value:,.2f}' if suffix or float(value) % 1 else f'{value:,.0f}') + suffix


def row_text(row, context=(), scrap_code=None):
    """Use the exact aggregated row used by the chart (not rounded axis labels)."""
    fields = list(context)
    for attr, label in [('date', 'Ngày'), ('eqpid', 'EQP'), ('slot', 'Slot'), ('model', 'Model')]:
        if hasattr(row, attr):
            value = str(getattr(row, attr))
            if attr == 'date' and len(value) == 8 and value.isdigit():
                value = f'{value[6:8]}/{value[4:6]}/{value[:4]}'
            fields.append((label, value))
    if scrap_code is not None:
        fields.append(('Scrap Code', str(scrap_code)))
        if hasattr(row, 'scrap_ppm_by_code'):
            fields.append(('Scrap PPM', number(row.scrap_ppm_by_code.get(scrap_code, 0), ' PPM')))
        if hasattr(row, 'scrap_qty'):
            fields.append(('Scrap Qty', number(row.scrap_qty.get(scrap_code, 0))))
    for attr, label in [('in_qty', 'In'), ('out_qty', 'Out'), ('pass_qty', 'Pass'), ('fail_qty', 'Fail')]:
        if hasattr(row, attr):
            fields.append((label, number(getattr(row, attr))))
    ppm = getattr(row, 'fail_ppm', None)
    if not hasattr(row, 'fail_ppm') and getattr(row, 'in_qty', 0):
        ppm = row.fail_qty / row.in_qty * 1_000_000
    fields.append(('Fail PPM (tổng)', number(ppm, ' PPM')))
    fields.append(('Yield', number(getattr(row, 'yield_percent', None), '%')))
    return '<br>'.join(f'<b>{escape(str(k))}:</b> {escape(str(v))}' for k, v in fields)


class ChartHover(QObject):
    """Hit-test in display pixels across both axes, including twinx bars."""
    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.bars = []
        self.lines = []
        self._shown = False
        canvas.setMouseTracking(True)
        canvas.installEventFilter(self)
        self.connections = [
            canvas.mpl_connect('motion_notify_event', self.on_motion),
            canvas.mpl_connect('figure_leave_event', self.hide),
            canvas.mpl_connect('button_press_event', self.hide),
        ]

    def hide(self, event=None):
        if self._shown:
            QToolTip.hideText()
            self._shown = False

    def eventFilter(self, obj, event):
        if obj is self.canvas and event.type() == QEvent.ToolTip:
            # Qt sends this delayed event even after our motion tooltip is
            # visible. Consume it so QWidget cannot overwrite chart data with
            # the static copy hint installed by enable_chart_copy().
            pos = event.pos()
            ratio = self.canvas.device_pixel_ratio
            probe = SimpleNamespace(
                x=pos.x() * ratio,
                y=self.canvas.figure.bbox.height - pos.y() * ratio,
            )
            text = self.hit_text(probe)
            if text is None:
                text = self.canvas.toolTip()
            if text:
                self.show(text, event.globalPos())
            else:
                self.hide()
            event.accept()
            return True
        if event.type() in (QEvent.Leave, QEvent.Hide, QEvent.Close):
            self.hide()
        return super().eventFilter(obj, event)

    def clear(self):
        self.hide()
        self.bars.clear()
        self.lines.clear()

    def add_bars(self, bars, texts):
        self.bars.extend(zip(bars.patches, texts))

    def add_line(self, line, texts):
        self.lines.append((line, list(texts)))

    def hit_text(self, event):
        if event.x is None or event.y is None:
            return None
        # Include a small border tolerance: Matplotlib rounds mouse pixels,
        # so points at Yield 0/100 can fall just outside event.inaxes.
        margin = 8.0 * self.canvas.device_pixel_ratio
        if not any(ax.bbox.padded(margin).contains(event.x, event.y)
                   for ax in self.canvas.figure.axes):
            return None
        # Prefer the nearest actual line point; do not invent interpolated values.
        nearest, text = 8.0 * self.canvas.device_pixel_ratio, None
        for line, texts in self.lines:
            if not line.get_visible() or line.axes is None:
                continue
            points = line.get_transform().transform(line.get_xydata())
            for i, (x, y) in enumerate(points):
                if not line.axes.bbox.padded(1).contains(x, y):
                    continue
                distance = np.hypot(event.x - x, event.y - y)
                if np.isfinite(distance) and distance <= nearest and i < len(texts):
                    nearest, text = distance, texts[i]
        if text is not None:
            return text
        for patch, text in reversed(self.bars):
            if patch.axes is None or not patch.get_visible():
                continue
            if patch.get_height() > 0 and patch.contains_point((event.x, event.y)):
                return text
            # Zero-height bars can still be inspected at their baseline.
            if patch.get_height() == 0:
                box = patch.get_window_extent()
                if box.x0 <= event.x <= box.x1 and abs(event.y - box.y0) <= 5 * self.canvas.device_pixel_ratio:
                    return text
        return None

    def show(self, text, position):
        # Allow time to read all metrics when the pointer stays still.
        QToolTip.showText(position, text, self.canvas, QRect(), 60000)
        self._shown = True

    def on_motion(self, event):
        if event.button is not None:
            self.hide()
            return
        text = self.hit_text(event)
        if text is None:
            self.hide()
        else:
            self.show(text, QCursor.pos())
