from __future__ import annotations

from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg,
)
from matplotlib.figure import Figure
from matplotlib.ticker import (
    FuncFormatter,
    MaxNLocator,
)
from ui.clipboard_utils import enable_chart_copy
from ui.charts.chart_hover import ChartHover, row_text

class CumEqpChart(FigureCanvasQTAgg):
    """Biểu đồ Fail PPM dạng cột và Yield dạng đường."""


    def __init__(
            self,
            parent=None,
    ):
        self.figure = Figure(
            figsize=(9, 4.4),
            dpi=100,
            facecolor="white",
            edgecolor="#BFBFBF",
            linewidth=1.0,
            frameon=True,
        )

        super().__init__(self.figure)

        self.setParent(parent)
        enable_chart_copy(self)
        self.hover = ChartHover(self)
        self.setStyleSheet(
            """
            background-color: white;
            border: 1px solid #BFBFBF;
            """
        )

        self.ppm_axis = self.figure.add_subplot(111)
        self.yield_axis = self.ppm_axis.twinx()

        self.setFixedSize(
            1300,
            536, 
        )

    def show_empty_state(
        self,
        message: str,
    ) -> None:
        """Hiển thị trạng thái không có dữ liệu."""
        self.hover.clear()

        self.figure.legends.clear()
        self.ppm_axis.clear()
        self.yield_axis.clear()

        self.ppm_axis.text(
            0.5,
            0.5,
            message,
            ha="center",
            va="center",
            transform=self.ppm_axis.transAxes,
            color="#777777",
        )

        self.ppm_axis.set_xticks([])
        self.ppm_axis.set_yticks([])
        self.yield_axis.set_yticks([])

        self.draw_idle()


    def update_chart(
            self,
            rows,
    ) -> None:
        """Vẽ biểu đồ phong cách Excel: Fail PPM và Yield."""
        self.hover.clear()

        if not rows:
            self.show_empty_state(
                "Không có dữ liệu CUM "
                "trong khoảng ngày đã chọn."
            )
            return

        self.ppm_axis.clear()
        self.yield_axis.clear()

        eqpids = [
            row.eqpid
            for row in rows
        ]

        fail_ppms = [
            row.fail_ppm or 0
            for row in rows
        ]

        yields = [
            row.yield_percent or 0
            for row in rows
        ]

        positions = list(range(len(eqpids)))

        bars = self.ppm_axis.bar(
            positions,
            fail_ppms,
            color="#FFC000",
            width=0.30,
            label="Fail PPM",
            zorder=3,
        )

        yield_line = self.yield_axis.plot(
            positions,
            yields,
            color="#4472C4",
            marker="o",
            markersize=6,
            markerfacecolor="white",
            markeredgewidth=2,
            linewidth=2.4,
            label="Yield",
            zorder=4,
        )[0]

        self.ppm_axis.set_title(
            "Cum Yield LI",
            fontsize=15,
            fontweight="normal",
            color="#6B6B6B",
            pad=18,
        )

        self.ppm_axis.set_ylabel(
            "Fail PPM",
            fontsize=9,
        )

        self.yield_axis.set_ylabel(
            "Yield",
            fontsize=9,
            labelpad=10,
        )

        self.yield_axis.yaxis.set_label_position(
            "right"
        )

        self.yield_axis.yaxis.tick_right()

        self.ppm_axis.set_xticks(positions)

        self.ppm_axis.set_xticklabels(
            eqpids,
            fontsize=9,
        )
        # Đường lưới dọc nằm ở ranh giới giữa các EQP,
        # không đi xuyên qua giữa cột.
        vertical_boundaries = [
            position - 0.5
            for position in range(
                len(eqpids) + 1
            )
        ]

        self.ppm_axis.set_xticks(
            vertical_boundaries,
            minor=True,
        )

        self.ppm_axis.set_xlim(
            -0.5,
            len(eqpids) - 0.5,
        )

        # Chia đều trục Fail PPM và bảo đảm
        # đường trên cùng trùng với giới hạn biểu đồ.
        ppm_maximum = max(fail_ppms)

        if ppm_maximum <= 0:
            ppm_maximum = 1

        ppm_locator = MaxNLocator(
            nbins=5,
            steps=[
                1,
                2,
                2.5,
                5,
                10,
            ],
        )

        ppm_ticks = ppm_locator.tick_values(
            0,
            ppm_maximum * 1.08,
        )

        ppm_ticks = [
            tick
            for tick in ppm_ticks
            if tick >= 0
        ]

        self.ppm_axis.set_yticks(
            ppm_ticks
        )

        self.ppm_axis.set_ylim(
            ppm_ticks[0],
            ppm_ticks[-1],
        )

        min_yield = min(yields)
        max_yield = max(yields)

        yield_padding = 0.5

        yield_minimum = max(
            0,
            min_yield - yield_padding,
        )

        yield_maximum = min(
            100,
            max_yield + yield_padding,
        )

        if yield_maximum - yield_minimum < 1:
            yield_minimum = max(
                0,
                yield_minimum - 0.5,
            )

            yield_maximum = min(
                100,
                yield_maximum + 0.5,
            )

        self.yield_axis.set_ylim(
            yield_minimum,
            yield_maximum,
        )
        self.yield_axis.yaxis.set_major_formatter(
            FuncFormatter(
                lambda value, position: (
                    f"{value:.1f}%"
                )
            )
        )

        # Đường ngang chia đều theo giá trị Fail PPM.
        self.ppm_axis.grid(
            visible=True,
            which="major",
            axis="y",
            color="#E6E6E6",
            linestyle="-",
            linewidth=0.6,
            alpha=1.0,
            zorder=0,
        )

        # Đường dọc nằm giữa các cột.
        self.ppm_axis.grid(
            visible=True,
            which="minor",
            axis="x",
            color="#E6E6E6",
            linestyle="-",
            linewidth=0.6,
            alpha=1.0,
            zorder=0,
        )

        self.ppm_axis.set_axisbelow(True)

        # Khung vùng dữ liệu giống Excel.
        for spine_name in (
                "left",
                "bottom",
                "top",
        ):
            spine = self.ppm_axis.spines[
                spine_name
            ]

            spine.set_visible(True)
            spine.set_color("#BFBFBF")
            spine.set_linewidth(0.8)

        self.ppm_axis.spines[
            "right"
        ].set_visible(False)

        # Chỉ giữ cạnh phải của trục Yield.
        for spine_name in (
                "left",
                "bottom",
                "top",
        ):
            self.yield_axis.spines[
                spine_name
            ].set_visible(False)

        right_spine = self.yield_axis.spines[
            "right"
        ]

        right_spine.set_visible(True)
        right_spine.set_color("#BFBFBF")
        right_spine.set_linewidth(0.8)

        self.ppm_axis.tick_params(
            axis="both",
            length=0,
            labelsize=9,
            colors="#404040",
        )
        self.ppm_axis.tick_params(
            axis="x",
            which="minor",
            bottom=False,
            top=False,
            labelbottom=False,
        )

        self.yield_axis.tick_params(
            axis="y",
            length=0,
            labelsize=9,
            colors="#404040",
            labelright=True,
            labelleft=False,
        )

        # Hiển thị Data Label Yield phía trên từng điểm.
        for position, yield_value in zip(
                positions,
                yields,
        ):
            self.yield_axis.annotate(
                f"{yield_value:.2f}%",
                xy=(
                    position,
                    yield_value,
                ),
                xytext=(
                    0,
                    10,
                ),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9,
                color="#333333",
            )
        self.figure.legends.clear()
        # Chú thích nằm dưới biểu đồ.
        self.figure.legend(
            [bars, yield_line],
            ["Fail PPM", "Yield"],
            loc="lower center",
            ncol=2,
            frameon=False,
            fontsize=9,
            bbox_to_anchor=(
                0.5,
                0.01,
            ),
        )

        self.figure.subplots_adjust(
            left=0.075,
            right=0.925,
            top=0.84,
            bottom=0.20,
        )

        texts = [row_text(row) for row in rows]
        self.hover.add_bars(bars, texts)
        self.hover.add_line(yield_line, texts)
        self.draw_idle()


