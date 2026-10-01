"""Dashboard bars using the grid, frame, hover and copy style of LI charts."""
from html import escape

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator, PercentFormatter
from PyQt5.QtWidgets import QSizePolicy

from ui.charts.chart_hover import ChartHover
from ui.clipboard_utils import enable_chart_copy


class DashboardBarChart(FigureCanvasQTAgg):
    def __init__(self, title, percent=False, daily=False, parent=None):
        figure = Figure(figsize=(4, 4), dpi=100, facecolor='white',
                        edgecolor='#BFBFBF', linewidth=1, frameon=True)
        super().__init__(figure)
        self.setParent(parent)
        self.setMinimumSize(0, 240)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.title = title
        self.percent = percent
        self.daily = daily
        self.axes = figure.add_subplot(111)
        self.hover = ChartHover(self)
        enable_chart_copy(self)
        figure.subplots_adjust(left=.16 if daily else .20, right=.98, top=.87, bottom=.22)

    def resizeEvent(self, event):
        if self.daily:
            # Fixed pixel margins avoid growing blank space on wide/scrolling charts.
            width = max(event.size().width(), 1)
            left_px = 62 if self.percent else 52
            self.figure.subplots_adjust(left=min(.25, left_px / width),
                                        right=max(.75, 1 - 14 / width))
        super().resizeEvent(event)

    def update_chart(self, labels, values, colors=None):
        self.hover.clear()
        ax = self.axes
        ax.clear()
        count = len(labels)
        # The scroll area preserves all selected dates without squeezing labels.
        self.setMinimumWidth(max(0, count * 44 + 80) if self.daily and count > 7 else 0)
        positions = list(range(count))
        bars = ax.bar(positions, values, color=colors if colors is not None else '#4472C4', width=.5, zorder=3)
        ax.set_title(self.title, fontsize=11, fontweight='normal', color='#6B6B6B', pad=16)
        ax.set_ylabel('Tỷ lệ (%)' if self.percent else 'Số alarm', fontsize=8)
        ax.set_xticks(positions)
        ax.set_xticklabels(labels, rotation=45 if self.daily else 0,
                           ha='right' if self.daily else 'center',
                           rotation_mode='anchor', fontsize=8)
        ax.set_xticks([i - .5 for i in range(count + 1)], minor=True)
        ax.set_xlim(-.5, max(count - .5, .5))
        if self.percent:
            ax.set_ylim(0, 100)
            ax.set_yticks([0, 20, 40, 60, 80, 100])
            ax.yaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
        else:
            maximum = max(values, default=0)
            ticks = MaxNLocator(nbins=5, integer=True).tick_values(0, max(1, maximum * 1.15))
            ax.set_yticks(ticks)
            ax.set_ylim(0, ticks[-1])
        ax.set_axisbelow(True)
        ax.grid(axis='y', which='major', color='#E6E6E6', linewidth=.6)
        ax.grid(axis='x', which='minor', color='#E6E6E6', linewidth=.6)
        ax.tick_params(axis='both', which='both', length=0, labelsize=8, colors='#404040')
        for spine in ax.spines.values():
            spine.set_color('#BFBFBF')
            spine.set_linewidth(.8)
        text_values = [f'{v:.2f}%' if self.percent else str(int(v)) for v in values]
        for bar, text in zip(bars, text_values):
            # Keep labels inside the frame at 100%.
            high = self.percent and bar.get_height() >= 90
            ax.annotate(text, (bar.get_x() + bar.get_width()/2, bar.get_height()),
                        xytext=(0, -5 if high else 4), textcoords='offset points',
                        ha='center', va='top' if high else 'bottom', fontsize=8,
                        color='white' if high else '#404040')
        self.hover.add_bars(bars, [f'<b>{escape(label.replace(chr(10), " "))}</b><br>{text}'
                                   for label, text in zip(labels, text_values)])
        if not count:
            ax.text(.5, .5, 'Chưa có dữ liệu', transform=ax.transAxes,
                    ha='center', va='center', fontsize=9, color='#777777')
        self.draw_idle()
