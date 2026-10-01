from __future__ import annotations

from math import ceil

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


class CumDailyStackedChart(
    FigureCanvasQTAgg
):
    """
    Biểu đồ PPM mã lỗi dạng cột chồng
    và Yield dạng đường theo từng ngày.
    """

    CODE_COLORS = [
        "#1565C0",
        "#E65100",
        "#2E7D32",
        "#C62828",
        "#6A1B9A",
        "#00838F",
        "#AD1457",
        "#5D4037",
        "#EF6C00",
        "#283593",
        "#558B2F",
        "#4527A0",
        "#0277BD",
        "#D84315",
        "#00695C",
        "#9E9D24",
        "#7B1FA2",
        "#00897B",
        "#F4511E",
        "#3949AB",
        "#43A047",
        "#8E24AA",
        "#039BE5",
        "#FDD835",
        "#546E7A",
        "#00ACC1",
        "#FB8C00",
        "#7CB342",
        "#D81B60",
        "#6D4C41",
    ]

    # def __init__(
    #         self,
    #         parent=None,
    #         chart_title: str = "Cum Yield LI Daily",
    #         empty_data_message: str = (
    #                 "Không có dữ liệu CUM Daily."
    #         ),
    # ):
    def __init__(
            self,
            parent=None,
            chart_title: str = "Cum Yield LI Daily",
            empty_data_message: str = (
                    "Không có dữ liệu CUM Daily."
            ),
            x_value_attribute: str = "date",
            format_x_as_date: bool = True,
            show_eqp_in_title: bool = True,
            yield_label_suffix: str = "",
            chart_width: int = 1550,
            bar_width_pixels: int | None = None,
            legend_columns: int = 15,
            force_horizontal_x_labels: bool = False,
    ):

        self.chart_title = chart_title
        self.empty_data_message = (
            empty_data_message
        )
        self.x_value_attribute = (
            x_value_attribute
        )

        self.format_x_as_date = (
            format_x_as_date
        )

        self.show_eqp_in_title = (
            show_eqp_in_title
        )

        self.yield_label_suffix = (
            yield_label_suffix
        )
        self.chart_width = chart_width

        self.bar_width_pixels = (
            bar_width_pixels
        )

        self.legend_columns = max(
            1,
            legend_columns,
        )

        self.force_horizontal_x_labels = (
            force_horizontal_x_labels
        )

        self.figure = Figure(
            figsize=(13, 5.5),
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

        self.ppm_axis = (
            self.figure.add_subplot(111)
        )

        self.yield_axis = (
            self.ppm_axis.twinx()
        )

        self.setFixedSize(
            self.chart_width,
            550,
        )
        self._loaded_daily_result = None
        self._bar_containers = []
        self._yield_line = None

    def show_empty_state(
        self,
        message: str,
    ) -> None:
        """Hiển thị thông báo khi không có dữ liệu."""
        self.hover.clear()

        self.ppm_axis.clear()
        self.yield_axis.clear()
        self.figure.legends.clear()
        self._loaded_daily_result = None
        self._bar_containers.clear()
        self._yield_line = None

        self.ppm_axis.text(
            0.5,
            0.5,
            message,
            ha="center",
            va="center",
            transform=self.ppm_axis.transAxes,
            color="#777777",
            fontsize=11,
        )

        self.ppm_axis.set_xticks([])
        self.ppm_axis.set_yticks([])
        self.yield_axis.set_yticks([])

        self.draw_idle()

    def update_chart(
            self,
            daily_result,
            selected_scrap_codes: list[str],
    ) -> None:
        """
        Cập nhật cột Scrap Code.

        Nếu dữ liệu Daily không đổi thì giữ nguyên
        trục, đường Yield, ngày và đường lưới.
        """
        self.hover.clear()

        selected_set = set(
            selected_scrap_codes
        )

        displayed_codes = [
            code
            for code in daily_result.scrap_codes
            if code in selected_set
        ]

        if not daily_result.rows:
            self.show_empty_state(
                self.empty_data_message
            )
            return

        if not displayed_codes:
            self.show_empty_state(
                "Các Scrap Code được chọn "
                "không phát sinh dữ liệu."
            )
            return

        rows = daily_result.rows

        positions = list(
            range(len(rows))
        )

        category_values = [
            str(
                getattr(
                    row,
                    self.x_value_attribute,
                )
            )
            for row in rows
        ]

        date_labels = [
            (
                self._format_date(value)
                if self.format_x_as_date
                else value
            )
            for value in category_values
        ]

        data_changed = (
                daily_result
                is not self._loaded_daily_result
        )

        if data_changed:
            # Chỉ clear toàn bộ khi Date/EQP/Tier đổi.
            self.ppm_axis.clear()
            self.yield_axis.clear()

            self._bar_containers.clear()
            self._yield_line = None

        else:
            # Chỉ xóa các cột Scrap Code cũ.
            # Giữ nguyên đường Yield và cấu hình trục.
            for container in self._bar_containers:
                for patch in container.patches:
                    patch.remove()

            self._bar_containers.clear()

        self.figure.legends.clear()

        stacked_bottom = [
            0.0
            for _ in rows
        ]

        legend_handles = []
        legend_labels = []

        all_code_positions = {
            code: index
            for index, code in enumerate(
                daily_result.scrap_codes
            )
        }
        bar_width = self._get_bar_width(
            len(rows)
        )

        for scrap_code in displayed_codes:
            ppm_values = [
                row.scrap_ppm_by_code.get(
                    scrap_code,
                    0.0,
                )
                for row in rows
            ]

            color_index = (
                    all_code_positions[scrap_code]
                    % len(self.CODE_COLORS)
            )

            # Không tạo Rectangle cho ngày có PPM = 0.
            non_zero_positions = []
            non_zero_values = []
            non_zero_bottoms = []

            for index, value in enumerate(
                    ppm_values
            ):
                if value <= 0:
                    continue

                non_zero_positions.append(
                    positions[index]
                )

                non_zero_values.append(
                    value
                )

                non_zero_bottoms.append(
                    stacked_bottom[index]
                )

            if non_zero_values:
                bars = self.ppm_axis.bar(
                    non_zero_positions,
                    non_zero_values,
                    bottom=non_zero_bottoms,
                    # width=0.62,
                    width=bar_width,
                    color=self.CODE_COLORS[
                        color_index
                    ],
                    edgecolor="white",
                    linewidth=0.25,
                    label=scrap_code,
                    zorder=3,
                )

                self.hover.add_bars(bars, [
                    row_text(rows[i], [('EQP', daily_result.eqpid or 'Tất cả')], scrap_code)
                    for i in non_zero_positions
                ])
                self._bar_containers.append(
                    bars
                )

                legend_handles.append(
                    bars
                )

                legend_labels.append(
                    scrap_code
                )

            # Vẫn cộng trên toàn bộ ngày để giữ
            # chính xác vị trí cột chồng.
            stacked_bottom = [
                bottom + value
                for bottom, value in zip(
                    stacked_bottom,
                    ppm_values,
                )
            ]

        if data_changed:

            yield_values = [
                (
                    row.yield_percent
                    if row.yield_percent is not None
                    else 0.0
                )
                for row in rows
            ]

            self._yield_line = self.yield_axis.plot(
                positions,
                yield_values,
                color="#4472C4",
                marker="o",
                markersize=4,
                markerfacecolor="white",
                markeredgewidth=1.3,
                linewidth=1.8,
                label="Yield",
                zorder=5,
            )[0]
            # Data Label của đường Yield.
            for position, row in zip(
                    positions,
                    rows,
            ):
                yield_value = (
                    row.yield_percent
                    if row.yield_percent is not None
                    else 0.0
                )

                self.yield_axis.annotate(
                    (
                        f"{yield_value:.2f}"
                        f"{self.yield_label_suffix}"
                    ),
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
                    annotation_clip=False,
                    zorder=6,
                )

            # self.ppm_axis.set_title(
            #     f"{self.chart_title}"
            #     f" | EQP: {daily_result.eqpid}",
            #     fontsize=12,
            #     color="#5F5F5F",
            #     pad=32,
            # )
            title_text = self.chart_title

            if self.show_eqp_in_title:
                title_text += (
                    f" | EQP: "
                    f"{daily_result.eqpid}"
                )

            self.ppm_axis.set_title(
                title_text,
                fontsize=12,
                color="#5F5F5F",
                pad=32,
            )

            self.ppm_axis.set_ylabel(
                "Scrap PPM",
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

            self.ppm_axis.set_xticks(
                positions
            )

            # rotate_labels = (
            #         len(date_labels) > 15
            # )
            rotate_labels = (
                not self.force_horizontal_x_labels
                and len(date_labels) > 15
            )

            self.ppm_axis.set_xticklabels(
                date_labels,
                fontsize=8,
                rotation=(
                    45
                    if rotate_labels
                    else 0
                ),
                ha=(
                    "right"
                    if rotate_labels
                    else "center"
                ),
            )

            vertical_boundaries = [
                position - 0.5
                for position in range(
                    len(rows) + 1
                )
            ]

            self.ppm_axis.set_xticks(
                vertical_boundaries,
                minor=True,
            )

            self.ppm_axis.set_xlim(
                -0.5,
                len(rows) - 0.5,
            )

            self._configure_yield_axis(
                rows
            )

            self._configure_grid()
            self._configure_frame()

            self._loaded_daily_result = (
                daily_result
            )

        self.hover.add_line(self._yield_line, [
            row_text(row, [('EQP', daily_result.eqpid or 'Tất cả')]) for row in rows
        ])

        # Scrap selection thay đổi nên trục PPM
        # vẫn cần tính lại theo tổng cột mới.
        self._configure_ppm_axis(
            stacked_bottom
        )

        legend_handles.append(
            self._yield_line
        )

        legend_labels.append(
            "Yield"
        )

        # legend_columns = min(
        #     10,
        #     len(legend_handles),
        # )
        legend_columns = min(
            self.legend_columns,
            len(legend_handles),
        )

        legend_rows = ceil(
            len(legend_handles)
            / legend_columns
        )

        self.figure.legend(
            legend_handles,
            legend_labels,
            loc="lower center",
            ncol=legend_columns,
            frameon=False,
            fontsize=8,
            handlelength=1.8,
            columnspacing=1.2,
            bbox_to_anchor=(
                0.5,
                0.01,
            ),
        )

        bottom_margin = min(
            0.34,
            0.16
            + max(
                0,
                legend_rows - 1,
            ) * 0.045,
        )

        self.figure.subplots_adjust(
            left=0.065,
            right=0.935,
            top=0.87,
            bottom=bottom_margin,
        )

        self.draw_idle()

    def _configure_ppm_axis(
        self,
        stacked_totals: list[float],
    ) -> None:
        """
        Tự động tạo giới hạn và các vạch chia
        đều nhau cho trục Scrap PPM.
        """

        ppm_maximum = max(
            stacked_totals,
            default=0,
        )

        if ppm_maximum <= 0:
            ppm_maximum = 1

        locator = MaxNLocator(
            nbins=5,
            steps=[
                1,
                2,
                2.5,
                5,
                10,
            ],
        )

        ticks = locator.tick_values(
            0,
            ppm_maximum * 1.08,
        )

        ticks = [
            tick
            for tick in ticks
            if tick >= 0
        ]

        self.ppm_axis.set_yticks(
            ticks
        )

        self.ppm_axis.set_ylim(
            ticks[0],
            ticks[-1],
        )

        self.ppm_axis.yaxis.set_major_formatter(
            FuncFormatter(
                lambda value, position: (
                    f"{value:.0f}"
                )
            )
        )

    def _configure_yield_axis(
        self,
        rows,
    ) -> None:
        """Tự động điều chỉnh trục Yield bên phải."""

        valid_yields = [
            (
                row.yield_percent
                if row.yield_percent is not None
                else 0.0
            )
            for row in rows
        ]

        if not valid_yields:
            self.yield_axis.set_ylim(
                0,
                100,
            )
        else:
            minimum = min(valid_yields)
            maximum = max(valid_yields)

            yield_minimum = max(
                0,
                minimum - 0.5,
            )

            yield_maximum = min(
                100,
                maximum + 0.5,
            )

            if (
                yield_maximum
                - yield_minimum
                < 1
            ):
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

    def _configure_grid(
        self,
    ) -> None:
        """Tạo đường lưới nhạt và chia đều."""

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

        self.ppm_axis.set_axisbelow(
            True
        )

    def _configure_frame(
        self,
    ) -> None:
        """Tạo khung và định dạng tick giống chart Summary."""

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
            labelsize=8,
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
            labelsize=8,
            colors="#404040",
            labelright=True,
            labelleft=False,
        )

    @staticmethod
    def _format_date(
        date_value: str,
    ) -> str:
        """Chuyển yyyyMMdd thành dd/MM."""

        if len(date_value) != 8:
            return date_value

        return (
            f"{date_value[6:8]}/"
            f"{date_value[4:6]}"
        )

    def _get_bar_width(
        self,
        category_count: int,
    ) -> float:
        """
        Chuyển chiều rộng mong muốn từ pixel sang
        đơn vị tọa độ của Matplotlib.

        Giá trị width của matplotlib không phải pixel,
        mà là tỷ lệ khoảng cách giữa hai category.
        """

        if (
            self.bar_width_pixels is None
            or category_count <= 0
        ):
            return 0.62

        # Biểu đồ đang dùng:
        # left = 0.065, right = 0.935.
        plot_width_pixels = (
            self.width()
            * (0.935 - 0.065)
        )

        pixels_per_category = (
            plot_width_pixels
            / category_count
        )

        if pixels_per_category <= 0:
            return 0.62

        return min(
            0.90,
            max(
                0.05,
                self.bar_width_pixels
                / pixels_per_category,
            ),
        )
