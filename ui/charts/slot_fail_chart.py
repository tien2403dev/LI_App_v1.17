from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.ticker import AutoMinorLocator, MaxNLocator
from PyQt5.QtWidgets import QSizePolicy
from ui.clipboard_utils import enable_chart_copy
from ui.charts.chart_hover import ChartHover, row_text

class SlotFailChart(FigureCanvasQTAgg):
    def __init__(self, parent=None):
        figure = Figure(
            figsize=(16, 4),
            dpi=100,
            facecolor='white',
            edgecolor='#BFBFBF',
            linewidth=1,
            frameon=True,
        )
        super().__init__(figure)
        self.setParent(parent)
        enable_chart_copy(self)
        self.hover = ChartHover(self)

        # Giãn ngang hết layout để hai mép khung bằng hai mép bảng.
        self.setMinimumWidth(0)
        self.setFixedHeight(400)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        self.axes = figure.add_subplot(111)

        # Giữ khoảng lề bên trong khung cho nhãn trục và chú thích.
        figure.subplots_adjust(
            left=.045,
            right=.955,
            bottom=.17,
            top=.84,
        )

    def update_chart(self, rows, eqp=None):
        self.hover.clear()
        ax = self.axes
        ax.clear()
        ax.set_axis_on()
        slots = [r.slot for r in rows]
        counts = [r.fail_qty for r in rows]
        bars = ax.bar(slots, counts, color='#FF0000', width=.55, label='Prime FAIL')
        self.hover.add_bars(bars, [row_text(row, [('EQP', eqp or 'Tất cả')]) for row in rows])
        ax.bar_label(bars, padding=3, fontsize=8, clip_on=False)
        title = 'Slot Fail Prime'
        if eqp is not None and str(eqp).strip():
            title += f' | EQP: {eqp}'

        ax.set_title(
            title,
            fontsize=15,
            fontweight='normal',
            color='#6B6B6B',
            pad=18,
        )
        # ax.set_xticks(range(1, 49))
        # Nhãn slot nằm giữa mỗi ô.
        ax.set_xticks(range(1, 49))

        # Đường kẻ dọc nằm ở hai bên cột.
        ax.set_xticks([i + 0.5 for i in range(49)], minor=True)
        ax.tick_params(axis='both', which='both', length=0, labelsize=8)
        # ax.set_xlim(.4, 48.6)
        ax.set_xlim(0.5, 48.5)
        # Keep the top at the actual maximum; an all-zero chart needs a nonzero range.
        maximum = max(counts, default=0)
        ax.set_ylim(0, maximum if maximum > 0 else 1)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
        ticks = [tick for tick in ax.get_yticks() if 0 <= tick <= ax.get_ylim()[1]]
        ax.set_yticks(sorted(set([0, ax.get_ylim()[1], *ticks])))
        ax.set_axisbelow(True)
        # ax.grid(axis='both', color='#E5E5E5', linewidth=.6)
        # Đường kẻ ngang theo các mốc trục Y.
        ax.grid(axis='y', which='major', color='#E5E5E5', linewidth=.6)

        # Tắt đường dọc đi qua tâm cột; bật đường dọc giữa các slot.
        ax.grid(axis='x', which='major', visible=False)
        ax.grid(axis='x', which='minor', color='#E5E5E5', linewidth=.6)
        if maximum <= 2:
            ax.yaxis.set_minor_locator(AutoMinorLocator(5))
            ax.grid(axis='y', which='minor', color='#E5E5E5', linewidth=.6)
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color('#BFBFBF')
            spine.set_linewidth(.8)
        ax.legend(loc='upper center', bbox_to_anchor=(.5, -.09), frameon=False, fontsize=9)
        self.draw_idle()

    def show_empty_state(self, message):
        self.hover.clear()
        self.axes.clear()
        self.axes.set_axis_off()
        self.axes.text(.5, .5, message, ha='center', va='center', transform=self.axes.transAxes)
        self.draw_idle()
