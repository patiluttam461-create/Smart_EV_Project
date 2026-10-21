"""
app.py
Smart EV Battery Management System
ANFIS-Based Battery State of Health (SOH) Estimation.

Professional Dark Engineering Dashboard designed for academic
presentation and soft computing laboratory demonstration.
"""

import sys
from typing import Dict, Any, List, Optional
import flet as ft

import config
import validators
import battery_logic
import demo_data


def create_app():
    def main(page: ft.Page):
        # -------------------------------------------------------------
        # Page Configuration (Dark Engineering Dashboard)
        # -------------------------------------------------------------
        page.title = f"{config.APP_TITLE} - {config.APP_SUBTITLE}"
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = config.COLOR_BG
        page.padding = 20
        page.scroll = ft.ScrollMode.AUTO

        # -------------------------------------------------------------
        # Notifications & Status Feedback
        # -------------------------------------------------------------
        def notify(message: str, is_error: bool = False):
            sb = ft.SnackBar(
                content=ft.Text(message, color=config.COLOR_TEXT_PRIMARY, size=13, weight=ft.FontWeight.W_500),
                bgcolor=config.COLOR_CRITICAL if is_error else config.COLOR_ACCENT_BLUE,
            )
            if hasattr(page, "show_dialog"):
                page.show_dialog(sb)
            elif hasattr(page, "open"):
                page.open(sb)
            else:
                page.snack_bar = sb
                sb.open = True
                page.update()

        # -------------------------------------------------------------
        # Validation & Error Banner
        # -------------------------------------------------------------
        error_banner_text = ft.Text("", color="#FCA5A5", size=13, weight=ft.FontWeight.W_500)
        error_banner = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.WARNING_AMBER, color="#EF4444", size=20),
                    ft.Container(content=error_banner_text, expand=True),
                ],
                spacing=10,
            ),
            bgcolor="#2D1214",
            border=ft.Border.all(1.0, "#7F1D1D"),
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            border_radius=8,
            visible=False,
        )

        def show_error(message: str):
            error_banner_text.value = message
            error_banner.visible = True
            page.update()

        def clear_error():
            error_banner_text.value = ""
            error_banner.visible = False
            page.update()

        # -------------------------------------------------------------
        # Header Section
        # -------------------------------------------------------------
        header_title = ft.Text(
            config.APP_TITLE,
            size=22,
            weight=ft.FontWeight.BOLD,
            color=config.COLOR_TEXT_PRIMARY,
        )
        header_subtitle = ft.Text(
            config.APP_SUBTITLE,
            size=14,
            weight=ft.FontWeight.W_500,
            color=config.COLOR_ACCENT_CYAN,
        )

        status_badge = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CHECK_CIRCLE, size=14, color="#34D399"),
                    ft.Text(config.APP_BADGE, size=12, weight=ft.FontWeight.BOLD, color="#34D399"),
                ],
                tight=True,
                spacing=6,
            ),
            bgcolor="#064E3B",
            border=ft.Border.all(1.0, "#059669"),
            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
            border_radius=16,
        )

        header_container = ft.Container(
            content=ft.Row(
                [
                    ft.Column([header_title, header_subtitle], spacing=3),
                    status_badge,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=config.COLOR_CARD,
            border=ft.Border.all(1.0, config.COLOR_CARD_BORDER),
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=20, vertical=14),
        )

        # -------------------------------------------------------------
        # Left Panel: 7 Battery Cycle Input Parameters
        # -------------------------------------------------------------
        input_fields: Dict[str, ft.TextField] = {}

        for spec in config.PARAMETER_SPECS:
            pid = spec["id"]
            tf_border = {
                ft.ControlState.FOCUSED: ft.OutlineInputBorder(side=ft.BorderSide(1.5, config.COLOR_INPUT_FOCUS)),
                ft.ControlState.DEFAULT: ft.OutlineInputBorder(side=ft.BorderSide(1.0, config.COLOR_INPUT_BORDER)),
            }
            tf = ft.TextField(
                label=f"{spec['label']} [{spec['unit_symbol']}]",
                hint_text=spec["hint"],
                value="",
                keyboard_type=ft.KeyboardType.NUMBER,
                dense=True,
                bgcolor=config.COLOR_INPUT_BG,
                border=tf_border,
                color=config.COLOR_TEXT_PRIMARY,
                text_size=13,
            )
            input_fields[pid] = tf

        # Compact 2-column grid for the 7 inputs to maintain desktop compactness
        inputs_grid = ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(content=input_fields["tv_ch"], expand=True),
                        ft.Container(content=input_fields["tv_d"], expand=True),
                    ],
                    spacing=12,
                ),
                ft.Row(
                    [
                        ft.Container(content=input_fields["tI_ch"], expand=True),
                        ft.Container(content=input_fields["Tavg"], expand=True),
                    ],
                    spacing=12,
                ),
                ft.Row(
                    [
                        ft.Container(content=input_fields["tTpeak_ch"], expand=True),
                        ft.Container(content=input_fields["Eavg_ch"], expand=True),
                    ],
                    spacing=12,
                ),
                ft.Row(
                    [
                        ft.Container(content=input_fields["Eavg_d"], expand=True),
                        ft.Container(
                            content=ft.Text(
                                "Units: Times in seconds [s], Temp in °C, Voltages in Volts [V].",
                                size=11,
                                color=config.COLOR_TEXT_MUTED,
                                italic=True,
                            ),
                            expand=True,
                            alignment=ft.Alignment.CENTER_LEFT,
                            padding=ft.Padding.only(left=8),
                        ),
                    ],
                    spacing=12,
                ),
            ],
            spacing=10,
        )

        # Action Buttons
        predict_button = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.BOLT, size=16, color="#FFFFFF"),
                    ft.Text("PREDICT SOH", size=13, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                ],
                tight=True,
                spacing=6,
            ),
            bgcolor=config.COLOR_ACCENT_BLUE,
            on_click=lambda e: on_predict_clicked(),
        )

        clear_button = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CLEAR_ALL, size=16, color=config.COLOR_TEXT_PRIMARY),
                    ft.Text("CLEAR", size=13, weight=ft.FontWeight.BOLD, color=config.COLOR_TEXT_PRIMARY),
                ],
                tight=True,
                spacing=6,
            ),
            bgcolor="#334155",
            on_click=lambda e: on_clear_clicked(),
        )

        # Demonstration Preset Buttons
        btn_healthy = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=14, color="#34D399"),
                    ft.Text("Healthy Example", size=12, weight=ft.FontWeight.W_600, color="#34D399"),
                ],
                tight=True,
                spacing=4,
            ),
            bgcolor="#064E3B",
            on_click=lambda e: load_preset("healthy"),
        )

        btn_warning = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.WARNING_AMBER, size=14, color="#FBBF24"),
                    ft.Text("Warning Example", size=12, weight=ft.FontWeight.W_600, color="#FBBF24"),
                ],
                tight=True,
                spacing=4,
            ),
            bgcolor="#451A03",
            on_click=lambda e: load_preset("warning"),
        )

        btn_critical = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=14, color="#F87171"),
                    ft.Text("Critical Example", size=12, weight=ft.FontWeight.W_600, color="#F87171"),
                ],
                tight=True,
                spacing=4,
            ),
            bgcolor="#450A0A",
            on_click=lambda e: load_preset("critical"),
        )

        inputs_card = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.TUNE, size=18, color=config.COLOR_ACCENT_CYAN),
                            ft.Text("BATTERY CYCLE PARAMETERS", size=15, weight=ft.FontWeight.BOLD, color=config.COLOR_TEXT_PRIMARY),
                        ],
                        spacing=8,
                    ),
                    ft.Text(
                        "Enter battery charging/discharging cycle parameters used by the ANFIS model.",
                        size=12,
                        color=config.COLOR_TEXT_MUTED,
                    ),
                    ft.Divider(color=config.COLOR_CARD_BORDER, height=8),
                    inputs_grid,
                    ft.Divider(color=config.COLOR_CARD_BORDER, height=12),
                    ft.Row([predict_button, clear_button], spacing=10),
                    ft.Divider(color=config.COLOR_CARD_BORDER, height=12),
                    ft.Text(
                        "DEMONSTRATION EXAMPLES (VERIFIED DATASET RECORDS):",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=config.COLOR_TEXT_MUTED,
                    ),
                    ft.Row([btn_healthy, btn_warning, btn_critical], spacing=8, wrap=True),
                ],
                spacing=8,
            ),
            bgcolor=config.COLOR_CARD,
            border=ft.Border.all(1.0, config.COLOR_CARD_BORDER),
            border_radius=10,
            padding=16,
        )

        # -------------------------------------------------------------
        # Right Panel: ANFIS Prediction Result Card
        # -------------------------------------------------------------
        soh_display_value = ft.Text(
            "-- %",
            size=44,
            weight=ft.FontWeight.BOLD,
            color=config.COLOR_ACCENT_CYAN,
        )

        condition_badge_text = ft.Text(
            "AWAITING INPUT",
            size=12,
            weight=ft.FontWeight.BOLD,
            color="#FFFFFF",
        )
        condition_badge_container = ft.Container(
            content=condition_badge_text,
            bgcolor="#475569",
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=12, vertical=5),
        )

        soh_progress_bar = ft.ProgressBar(
            value=0.0,
            color=config.COLOR_ACCENT_CYAN,
            bgcolor=config.COLOR_INPUT_BG,
            height=12,
            border_radius=6,
        )

        status_description_text = ft.Text(
            "Enter 7 battery parameters or select an example above, then click 'PREDICT SOH' to run ANFIS inference.",
            size=12,
            color=config.COLOR_TEXT_MUTED,
        )

        range_warning_text = ft.Text(
            "",
            size=11,
            color="#FBBF24",
            visible=False,
        )

        prediction_card = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.ANALYTICS, size=18, color=config.COLOR_ACCENT_CYAN),
                                    ft.Text("ANFIS PREDICTION", size=15, weight=ft.FontWeight.BOLD, color=config.COLOR_TEXT_PRIMARY),
                                ],
                                spacing=8,
                            ),
                            condition_badge_container,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(color=config.COLOR_CARD_BORDER, height=8),
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text("Predicted State of Health (SOH):", size=12, color=config.COLOR_TEXT_MUTED),
                                    soh_display_value,
                                ],
                                spacing=2,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    soh_progress_bar,
                    range_warning_text,
                    ft.Container(
                        content=status_description_text,
                        bgcolor=config.COLOR_INPUT_BG,
                        border=ft.Border.all(1.0, config.COLOR_CARD_BORDER),
                        border_radius=8,
                        padding=12,
                    ),
                    ft.Text(
                        "Project-defined classification thresholds:  • HEALTHY: SOH ≥ 90.0%  • WARNING: 85.0% ≤ SOH < 90.0%  • CRITICAL: SOH < 85.0%",
                        size=11,
                        color=config.COLOR_TEXT_DIM,
                        italic=True,
                    ),
                ],
                spacing=10,
            ),
            bgcolor=config.COLOR_CARD,
            border=ft.Border.all(1.0, config.COLOR_CARD_BORDER),
            border_radius=10,
            padding=16,
        )

        # -------------------------------------------------------------
        # Right Panel: ANFIS Model Information Card
        # -------------------------------------------------------------
        model_meta = battery_logic.get_model_metadata()

        model_info_card = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.MEMORY, size=18, color=config.COLOR_ACCENT_CYAN),
                                    ft.Text("ANFIS MODEL INFORMATION", size=14, weight=ft.FontWeight.BOLD, color=config.COLOR_TEXT_PRIMARY),
                                ],
                                spacing=8,
                            ),
                            ft.Container(
                                content=ft.Text(f"● {model_meta['version']}: {model_meta['status']}", size=11, color="#34D399", weight=ft.FontWeight.BOLD),
                                bgcolor="#064E3B",
                                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                border_radius=8,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(color=config.COLOR_CARD_BORDER, height=6),
                    ft.ResponsiveRow(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("• Model: Adaptive Neuro-Fuzzy Inference System", size=12, color=config.COLOR_TEXT_PRIMARY),
                                        ft.Text("• Inference: Zero-Order Sugeno ANFIS", size=12, color=config.COLOR_TEXT_PRIMARY),
                                        ft.Text("• Inputs: 7 Cycle Parameters", size=12, color=config.COLOR_TEXT_PRIMARY),
                                        ft.Text("• Output: Battery SOH (%) [Regression]", size=12, color=config.COLOR_TEXT_PRIMARY),
                                    ],
                                    spacing=4,
                                ),
                                col={"sm": 12, "md": 6},
                            ),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("• Membership Functions: 2 Gaussian MFs / Input", size=12, color=config.COLOR_TEXT_PRIMARY),
                                        ft.Text("• Fuzzy Rules: 128 (2⁷ Combination Matrix)", size=12, color=config.COLOR_TEXT_PRIMARY),
                                        ft.Text("• Features: tv_ch, tv_d, tI_ch, Tavg, tTpeak_ch, Eavg_ch, Eavg_d", size=12, color=config.COLOR_TEXT_PRIMARY),
                                        ft.Text("• Pipeline: Scaler Transform → ANFIS → Scaler Inverse", size=12, color=config.COLOR_TEXT_PRIMARY),
                                    ],
                                    spacing=4,
                                ),
                                col={"sm": 12, "md": 6},
                            ),
                        ],
                        spacing=8,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=config.COLOR_CARD,
            border=ft.Border.all(1.0, config.COLOR_CARD_BORDER),
            border_radius=10,
            padding=14,
        )

        # -------------------------------------------------------------
        # Process Flow Section (Horizontal Pipeline)
        # -------------------------------------------------------------
        def create_flow_step(step_num: str, step_label: str) -> ft.Container:
            return ft.Container(
                content=ft.Column(
                    [
                        ft.Text(step_num, size=9, weight=ft.FontWeight.BOLD, color=config.COLOR_ACCENT_CYAN),
                        ft.Text(step_label, size=11, weight=ft.FontWeight.W_600, color=config.COLOR_TEXT_PRIMARY),
                    ],
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=config.COLOR_INPUT_BG,
                border=ft.Border.all(1.0, config.COLOR_CARD_BORDER),
                border_radius=8,
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            )

        def create_flow_arrow() -> ft.Text:
            return ft.Text("→", size=14, weight=ft.FontWeight.BOLD, color=config.COLOR_ACCENT_CYAN)

        process_flow_card = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.ACCOUNT_TREE, size=16, color=config.COLOR_ACCENT_CYAN),
                            ft.Text("ANFIS INFERENCE PROCESS FLOW", size=13, weight=ft.FontWeight.BOLD, color=config.COLOR_TEXT_PRIMARY),
                        ],
                        spacing=6,
                    ),
                    ft.Divider(color=config.COLOR_CARD_BORDER, height=4),
                    ft.Row(
                        [
                            create_flow_step("STEP 1", "BATTERY CYCLE DATA"),
                            create_flow_arrow(),
                            create_flow_step("STEP 2", "FEATURE INPUT (7)"),
                            create_flow_arrow(),
                            create_flow_step("STEP 3", "FUZZIFICATION"),
                            create_flow_arrow(),
                            create_flow_step("STEP 4", "128 FUZZY RULES"),
                            create_flow_arrow(),
                            create_flow_step("STEP 5", "NORMALIZATION"),
                            create_flow_arrow(),
                            create_flow_step("STEP 6", "SUGENO INFERENCE"),
                            create_flow_arrow(),
                            create_flow_step("STEP 7", "SOH PREDICTION %"),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        wrap=True,
                        spacing=6,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=config.COLOR_CARD,
            border=ft.Border.all(1.0, config.COLOR_CARD_BORDER),
            border_radius=10,
            padding=14,
        )

        # -------------------------------------------------------------
        # Footer
        # -------------------------------------------------------------
        footer = ft.Container(
            content=ft.Row(
                [
                    ft.Text(config.APP_FOOTER, size=11, color=config.COLOR_TEXT_DIM, weight=ft.FontWeight.W_500),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=10,
        )

        # -------------------------------------------------------------
        # Event Handlers & Prediction Logic
        # -------------------------------------------------------------
        def load_preset(category: str):
            clear_error()
            try:
                preset_vals = demo_data.get_demo_example(category)
                meta = demo_data.get_demo_metadata(category)
                for pid, val in preset_vals.items():
                    if pid in input_fields:
                        input_fields[pid].value = str(val)

                cycle_info = f" (Global Cycle {meta.get('cycle', '')})" if meta.get("cycle") else ""
                notify(f"Loaded {meta.get('title', category)}{cycle_info} from processed dataset.")
                page.update()
            except Exception as ex:
                show_error(f"Failed to load preset: {ex}")

        def on_clear_clicked():
            clear_error()
            for tf in input_fields.values():
                tf.value = ""

            soh_display_value.value = "-- %"
            soh_display_value.color = config.COLOR_ACCENT_CYAN
            condition_badge_text.value = "AWAITING INPUT"
            condition_badge_container.bgcolor = "#475569"
            soh_progress_bar.value = 0.0
            soh_progress_bar.color = config.COLOR_ACCENT_CYAN
            status_description_text.value = "Enter 7 battery parameters or select an example above, then click 'PREDICT SOH' to run ANFIS inference."
            range_warning_text.visible = False
            notify("All input parameters and prediction results cleared.")
            page.update()

        def on_predict_clicked():
            clear_error()
            raw_vals = {pid: tf.value for pid, tf in input_fields.items()}

            # 1. Validation
            is_valid, parsed_vals, err_msg = validators.validate_battery_inputs(raw_vals)
            if not is_valid or parsed_vals is None:
                show_error(err_msg or "Validation error: Please review input fields.")
                return

            # 2. Deterministic ANFIS Inference
            try:
                soh = battery_logic.predict_soh_anfis(parsed_vals)
                status = battery_logic.get_status(soh)
                status_color = battery_logic.get_status_color(status)
                description = battery_logic.get_status_description(soh)
                range_warnings = battery_logic.check_training_range(parsed_vals)

                # Update UI
                soh_display_value.value = f"{soh:.2f} %"
                soh_display_value.color = status_color
                condition_badge_text.value = status
                condition_badge_container.bgcolor = status_color

                soh_progress_bar.value = max(0.0, min(1.0, soh / 100.0))
                soh_progress_bar.color = status_color

                status_description_text.value = description

                if range_warnings:
                    range_warning_text.value = "Notice: Some inputs fall outside the ANFIS V5 training bounds: " + ", ".join(range_warnings[:2])
                    range_warning_text.visible = True
                else:
                    range_warning_text.visible = False

                notify(f"ANFIS SOH Prediction: {soh:.2f}% ({status})")
                page.update()

            except Exception as ex:
                show_error(f"Inference error: {ex}")

        # -------------------------------------------------------------
        # Assemble Final Page Layout
        # -------------------------------------------------------------
        left_column = ft.Column(
            [inputs_card],
            spacing=14,
        )

        right_column = ft.Column(
            [prediction_card, model_info_card],
            spacing=14,
        )

        main_dashboard_grid = ft.ResponsiveRow(
            [
                ft.Container(content=left_column, col={"sm": 12, "md": 12, "lg": 6}),
                ft.Container(content=right_column, col={"sm": 12, "md": 12, "lg": 6}),
            ],
            spacing=14,
        )

        page.add(
            header_container,
            error_banner,
            main_dashboard_grid,
            process_flow_card,
            footer,
        )

    return main


def run_app():
    """
    Entry point to launch the Flet application.
    Supports native desktop app and web browser mode.
    """
    main_func = create_app()
    view_mode = ft.AppView.WEB_BROWSER if ("--web" in sys.argv or sys.platform == "darwin") else ft.AppView.FLET_APP

    if hasattr(ft, "run"):
        ft.run(main=main_func, view=view_mode)
    elif hasattr(ft, "app"):
        ft.app(target=main_func, view=view_mode)
    else:
        raise RuntimeError("Compatible Flet runner not found.")


if __name__ == "__main__":
    run_app()
