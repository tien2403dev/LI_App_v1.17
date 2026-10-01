import math

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, MaxNLocator
from ui.charts.cum_daily_chart import CumDailyStackedChart
from ui.clipboard_utils import enable_chart_copy
from ui.charts.chart_hover import ChartHover, row_text

class CumModelChart(FigureCanvasQTAgg):
    """Cột chồng số lượng scrap theo Model và đường Yield trên trục phải."""
    COLORS = CumDailyStackedChart.CODE_COLORS

    def __init__(self, parent=None):
        """Tạo canvas khi có kết quả SEARCH, chiều rộng giống Cum Daily LI."""
        self.figure = Figure(figsize=(13, 5.36), dpi=100, facecolor='white',
                             edgecolor='#BFBFBF', linewidth=1, frameon=True)
        super().__init__(self.figure)
        self.setParent(parent)
        enable_chart_copy(self)
        self.hover = ChartHover(self) 
        self.setFixedSize(1550, 550)
        self.setStyleSheet('background:white; border:1px solid #BFBFBF;')
        self.fail_axis = self.figure.add_subplot(111)
        self.yield_axis = self.fail_axis.twinx()

    def _reset(self):
        """Xóa artist và legend cũ nhưng tái sử dụng hai trục hiện tại."""
        self.fail_axis.clear()
        self.yield_axis.clear()
        for legend in list(self.figure.legends):
            legend.remove()
        self.fail_axis.set_axis_on()
        self.yield_axis.set_axis_on()

    def show_empty_state(self, message):
        """Hiển thị trạng thái rỗng, không giữ cột hoặc Yield từ lần trước."""
        self.hover.clear()
        self._reset()
        self.fail_axis.set_axis_off()
        self.yield_axis.set_axis_off()
        self.fail_axis.text(.5, .5, message, transform=self.fail_axis.transAxes,
                            ha='center', va='center', color='#777777')
        self.draw_idle()

    def update_chart(self, result, selected_codes):
        """Vẽ số lượng thực, không PPM; Yield luôn tính từ toàn bộ In/Out."""
        self.hover.clear()
        if not result.rows:
            self.show_empty_state('Không có dữ liệu CUM theo bộ lọc đã chọn.')
            return
        if not selected_codes:
            self.show_empty_state('Chọn Scrap Code rồi bấm SEARCH để vẽ biểu đồ.')
            return
        self._reset()
        ax, right = self.fail_axis, self.yield_axis
        codes = [code for code in sorted(set(selected_codes))
                 if any(row.scrap_qty.get(code, 0) > 0 for row in result.rows)]
        if not codes:
            self.show_empty_state('Các Scrap Code được chọn không phát sinh dữ liệu.')
            return
        x = list(range(len(result.rows)))
        bottom = [0] * len(x)
        handles = []
        for code in codes:
            values = [row.scrap_qty.get(code, 0) for row in result.rows]
            # Màu giữ ổn định khi thay đổi lựa chọn trong cùng tập kết quả.
            palette_index = result.scrap_codes.index(code) if code in result.scrap_codes else 0
            positions = [i for i, value in enumerate(values) if value > 0]
            bars = ax.bar(positions, [values[i] for i in positions],
                          bottom=[bottom[i] for i in positions], width=.38, label=code,
                          color=self.COLORS[palette_index % len(self.COLORS)],
                          edgecolor='white', linewidth=.25, zorder=3)
            self.hover.add_bars(bars, [row_text(result.rows[i], scrap_code=code) for i in positions])
            handles.append(bars)
            bottom = [a + b for a, b in zip(bottom, values)]
        values = [row.yield_percent if row.yield_percent is not None else float('nan')
                  for row in result.rows]
        line, = right.plot(x, values, color='#4472C4', marker='o',
                           markerfacecolor='white', markersize=5, linewidth=1.6, label='Yield')
        self.hover.add_line(line, [row_text(row) for row in result.rows])
        for index, value in enumerate(values):
            if math.isfinite(value):
                right.annotate(f'{value:.2f}%', (index, value), xytext=(0, 9),
                               textcoords='offset points', ha='center', fontsize=8)
        valid = [v for v in values if math.isfinite(v)]
        if valid:
            padding = max(.2, (max(valid) - min(valid)) * .25)
            right.set_ylim(max(0, min(valid) - padding), max(valid) + padding)
        else:
            right.set_ylim(0, 100)
        right.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f'{value:.2f}%'))
        right.yaxis.set_major_locator(MaxNLocator(nbins=7))
        maximum = max(bottom, default=0)
        ax.set_ylim(0, maximum if maximum > 0 else 1)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=7, integer=True))
        # Tâm cột và tên Model nằm ở các vị trí 0, 1, 2, ...
        ax.set_xlim(-.5, len(x) - .5)
        ax.set_xticks(x)
        ax.set_xticklabels(
            [row.model for row in result.rows],
            rotation=45 if len(x) > 12 else 0,
            ha='right' if len(x) > 12 else 'center'
        )

        # Đường kẻ dọc ở biên mỗi ô: -0.5, 0.5, 1.5, ...
        # Mỗi cột sẽ nằm chính giữa hai đường kẻ dọc.
        boundaries = [i - .5 for i in range(len(x) + 1)]
        ax.set_xticks(boundaries, minor=True)

        ax.set_axisbelow(True)
        ax.grid(False, axis='both', which='both')

        # Giữ đường kẻ ngang theo trục số lượng.
        ax.grid(
            True, axis='y', which='major',
            color='#D9D9D9', linewidth=.6
        )

        # Chỉ vẽ đường kẻ dọc tại biên, không vẽ qua tâm cột.
        ax.grid(
            True, axis='x', which='minor',
            color='#D9D9D9', linewidth=.6
        )
        ax.tick_params(axis='x', which='minor', length=0)

        # Tắt lưới của trục Yield để tránh đường kẻ chồng lên.
        right.grid(False, axis='both', which='both')
        ax.patch.set_hatch('////////')
        ax.patch.set_edgecolor('#E5E5E5')
        ax.patch.set_linewidth(.4)
        for axis in (ax, right):
            axis.tick_params(axis='both', length=0, labelsize=8, colors='#555555')
            for spine in axis.spines.values():
                spine.set_color('#BFBFBF')
                spine.set_linewidth(.6)
        ax.set_title('Cum Yield by Model', fontsize=14, fontweight='normal', color='#777777', pad=25)
        handles.append(line)
        legend_columns = min(15, len(handles))
        legend_rows = math.ceil(len(handles) / legend_columns)
        bottom_margin = min(.34, .16 + max(0, legend_rows - 1) * .045)
        self.figure.subplots_adjust(left=.065, right=.935, top=.87, bottom=bottom_margin)
        self.figure.legend(handles, codes + ['Yield'], loc='lower center',
                           ncol=legend_columns, frameon=False, fontsize=8,
                           handlelength=1.8, columnspacing=1.2,
                           bbox_to_anchor=(.5, .01))
        self.draw_idle()
