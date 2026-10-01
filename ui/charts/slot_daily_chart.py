from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, MaxNLocator
from PyQt5.QtWidgets import QSizePolicy
from ui.clipboard_utils import enable_chart_copy
from ui.charts.chart_hover import ChartHover, row_text
def format_percent(value):
    text = f'{value:.2f}'
    if text.endswith('.00'):
        text = text[:-3]
    return f'{text}%'
class SlotDailyChart(FigureCanvasQTAgg):
    """Cột Prime Fail và đường Prime Yield theo ngày; không vẽ Total."""

    def __init__(self, parent=None):
        """Tạo canvas 1300 × 536 giống biểu đồ Cum Yield LI Summary."""
        self.figure = Figure(figsize=(13, 5.36), dpi=100, facecolor='white',
                             edgecolor='#BFBFBF', linewidth=1, frameon=True)
        super().__init__(self.figure)
        self.setParent(parent)
        enable_chart_copy(self)
        self.hover = ChartHover(self)
        # Biểu đồ giãn ngang theo phần diện tích còn lại bên cạnh bảng.
        self.setMinimumWidth(0)
        self.setFixedHeight(536)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet('background:white; border:1px solid #BFBFBF;')
        self.fail_axis = self.figure.add_subplot(111)
        self.yield_axis = self.fail_axis.twinx()

    def show_empty_state(self, message):
        """Xóa dữ liệu và legend cũ khi thiếu lựa chọn hoặc không có dữ liệu."""
        self.hover.clear()
        self.figure.legends.clear()
        for axis in (self.fail_axis, self.yield_axis):
            axis.clear()
            axis.set_xticks([])
            axis.set_yticks([])
        self.fail_axis.text(.5, .5, message, ha='center', va='center',
                            transform=self.fail_axis.transAxes, color='#777777')
        self.draw_idle()

    def update_chart(self, result):
        """Vẽ dữ liệu ngày; ngày không có Input hiển thị Yield 0% trên biểu đồ."""
        self.hover.clear()
        if not result.rows:
            self.show_empty_state('Không có dữ liệu PRIME trong khoảng ngày đã chọn.')
            return
        self.figure.legends.clear()
        self.fail_axis.clear()
        self.yield_axis.clear()
        rows = result.rows
        positions = list(range(len(rows)))
        fails = [r.fail_qty for r in rows]
        yields = [r.yield_percent if r.yield_percent is not None else 0.0 for r in rows]
        bars = self.fail_axis.bar(positions, fails, width=.30, color='#FF0000', zorder=3)
        line, = self.yield_axis.plot(positions, yields, color='#0070C0', marker='o',
                                    markerfacecolor='white', linewidth=2.4, zorder=4)
        texts = [row_text(row, [('EQP', result.eqp), ('Slot', result.slot)]) for row in rows]
        self.hover.add_bars(bars, texts)
        self.hover.add_line(line, texts)
        self.fail_axis.set_title(
            f'Yield slot {result.slot} | EQP: {result.eqp}',
            fontsize=15, fontweight='normal', color='#6B6B6B', pad=18
        )
        self.fail_axis.set_ylabel('Prime Fail', fontsize=9)
        self.yield_axis.set_ylabel('Prime Yield', fontsize=9)
        self.yield_axis.yaxis.set_label_position('right')
        self.yield_axis.yaxis.tick_right()
        # Giữ đủ dữ liệu ngày nhưng giảm nhãn khi khoảng ngày dài để tránh chồng chữ.
        stride = max(1, (len(rows) + 30) // 31)
        ticks = sorted(set([*range(0, len(rows), stride), len(rows) - 1]))
        self.fail_axis.set_xticks(ticks)
        self.fail_axis.set_xticklabels([f'{int(rows[i].date[6:8])}-{int(rows[i].date[4:6])}' for i in ticks])
        self.fail_axis.set_xticks([p - .5 for p in range(len(rows) + 1)], minor=True)
        self.fail_axis.set_xlim(-.5, len(rows) - .5)
        maximum = max(max(fails), 1)
        yticks = [v for v in MaxNLocator(nbins=6, integer=True).tick_values(0, maximum) if 0 <= v <= maximum]
        self.fail_axis.set_yticks(sorted(set([*yticks, maximum])))
        self.fail_axis.set_ylim(0, maximum)
        self.yield_axis.set_ylim(0, 100)
        self.yield_axis.yaxis.set_major_formatter(
            FuncFormatter(lambda value, _: format_percent(value))
        )
        self.fail_axis.set_axisbelow(True)
        self.fail_axis.grid(True, axis='y', color='#D9D9D9', linewidth=.6)
        self.fail_axis.grid(True, axis='x', which='minor', color='#D9D9D9', linewidth=.6)
        for axis in (self.fail_axis, self.yield_axis):
            axis.tick_params(axis='both', which='both', length=0, labelsize=9, colors='#404040')
            for spine in axis.spines.values():
                spine.set_color('#BFBFBF')
                spine.set_linewidth(.8)
        for i in ticks:
            value = yields[i]
            self.yield_axis.annotate(
                format_percent(value), (i, value),
                xytext=(0, 10), textcoords='offset points',
                ha='center', fontsize=9
            )
        self.figure.legend([bars, line], ['Prime Fail', 'Prime Yield'], loc='lower center',
                           ncol=2, frameon=False, bbox_to_anchor=(.5, .01), fontsize=9)
        self.figure.subplots_adjust(left=.075, right=.925, top=.84, bottom=.20)
        self.draw_idle()
