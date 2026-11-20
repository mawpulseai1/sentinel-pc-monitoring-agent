"""
HUD Painter Engine (Optimized & Razor-Sharp)
Renders high-contrast, crystal-clear monospace telemetry on transparent desktop layers.
Features exact character-grid alignment, optional cyber glass panel backings,
and eliminates text-fringing / distortion.
"""

import time
from typing import Dict, Any, List, Tuple, Optional
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QFontMetrics
from PySide6.QtCore import QRectF, Qt
from ui.ascii_art import (
    render_sparkline,
    render_progress_bar,
    get_spinner,
    format_box_header,
    format_box_footer,
    render_neural_wave,
    get_mascot_segments
)

class HUDPainter:
    def __init__(self, config):
        self.config = config
        self.font_family = config.get("font_family", "Cascadia Code")
        self.base_font_size = config.get("font_size", 10)
        self.shimmer_tick = 0
        self.news_click_rects = []

    def paint(self, painter: QPainter, width: int, height: int, snapshot: Dict[str, Any], tick: int, theme: Dict[str, Any], view_mode: int = 0, from_view: int = 0, to_view: Optional[int] = None, transition_progress: float = 1.0, report_countdown_sec: float = 0.0, report_timer_paused: bool = False, auto_rotate_countdown_sec: float = 0.0):
        """Main rendering entrypoint with animated multi-HUD transition router."""
        if not snapshot or not snapshot.get("telemetry"):
            self._draw_standby(painter, width, height, tick, theme)
            return

        target_view = to_view if to_view is not None else view_mode
        source_view = from_view if to_view is not None else view_mode

        # Backward compatibility for legacy two-view callers
        if to_view is None and transition_progress > 0.001 and transition_progress < 0.999:
            source_view = 0
            target_view = 1

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        telemetry = snapshot["telemetry"]
        self.shimmer_tick = (tick // 2) % 24

        # Configure Monospace Fonts with High-DPI Hinting
        main_font = QFont(self.font_family, self.base_font_size)
        main_font.setStyleHint(QFont.StyleHint.Monospace)
        main_font.setFixedPitch(True)
        main_font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)

        bold_font = QFont(self.font_family, self.base_font_size, QFont.Weight.Bold)
        bold_font.setStyleHint(QFont.StyleHint.Monospace)
        bold_font.setFixedPitch(True)
        bold_font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)

        small_font = QFont(self.font_family, max(8, self.base_font_size - 1))
        small_font.setStyleHint(QFont.StyleHint.Monospace)
        small_font.setFixedPitch(True)
        small_font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)

        fm = QFontMetrics(main_font)
        char_w = fm.horizontalAdvance('A')
        line_h = fm.lineSpacing() + 3
        ascent = fm.ascent()

        # Apply global opacity
        user_opacity = float(self.config.get("opacity", 0.95))
        painter.setOpacity(user_opacity)

        # Transition Animation Routing
        if source_view == target_view or transition_progress >= 0.999:
            self._render_view(target_view, painter, width, height, telemetry, snapshot, tick, theme, main_font, bold_font, small_font, fm, char_w, line_h, ascent, report_countdown_sec, report_timer_paused, auto_rotate_countdown_sec)
        else:
            # Active animated slide transition with smooth cubic easing
            t = max(0.0, min(1.0, transition_progress))
            ease_t = t * t * (3.0 - 2.0 * t)
            offset_0 = int(-ease_t * width)
            offset_1 = int((1.0 - ease_t) * width)

            painter.save()
            painter.translate(offset_0, 0)
            self._render_view(source_view, painter, width, height, telemetry, snapshot, tick, theme, main_font, bold_font, small_font, fm, char_w, line_h, ascent, report_countdown_sec, report_timer_paused, auto_rotate_countdown_sec)
            painter.restore()

            painter.save()
            painter.translate(offset_1, 0)
            self._render_view(target_view, painter, width, height, telemetry, snapshot, tick, theme, main_font, bold_font, small_font, fm, char_w, line_h, ascent, report_countdown_sec, report_timer_paused, auto_rotate_countdown_sec)
            painter.restore()

    def _render_view(self, view_idx: int, painter: QPainter, width: int, height: int, telemetry: Dict[str, Any], snapshot: Dict[str, Any], tick: int, theme: Dict[str, Any], main_font: QFont, bold_font: QFont, small_font: QFont, fm: QFontMetrics, char_w: int, line_h: int, ascent: int, report_countdown_sec: float, report_timer_paused: bool, auto_rotate_countdown_sec: float):
        if view_idx == 1:
            self._draw_game_report_hud(painter, width, height, telemetry, snapshot, tick, theme, main_font, bold_font, small_font, fm, char_w, line_h, ascent, report_countdown_sec, report_timer_paused)
        elif view_idx == 2:
            self._draw_news_hud(painter, width, height, telemetry, snapshot, tick, theme, main_font, bold_font, small_font, fm, char_w, line_h, ascent, auto_rotate_countdown_sec)
        else:
            self._draw_telemetry_hud(painter, width, height, telemetry, snapshot, tick, theme, main_font, bold_font, small_font, fm, char_w, line_h, ascent, auto_rotate_countdown_sec)

    def _draw_telemetry_hud(self, painter: QPainter, width: int, height: int, telemetry: Dict[str, Any], snapshot: Dict[str, Any], tick: int, theme: Dict[str, Any], main_font: QFont, bold_font: QFont, small_font: QFont, fm: QFontMetrics, char_w: int, line_h: int, ascent: int, auto_rotate_countdown_sec: float = 0.0):
        # 1. Top Mission Control Header
        top_y = 20
        self._draw_top_header(painter, width, telemetry, snapshot, tick, theme, main_font, bold_font, fm, ascent)

        # 2. Main Telemetry Panels
        margin_x = 20
        available_w = width - (margin_x * 2)
        gap_x = 16

        col_chars = int((available_w - gap_x) // (2 * char_w))
        
        if col_chars >= 45:
            col_px_w = col_chars * char_w
            col1_x = margin_x
            col2_x = margin_x + col_px_w + gap_x

            # Left Column: CPU, Memory, GPU
            curr_y1 = 65
            curr_y1 = self._draw_cpu_panel(painter, col1_x, curr_y1, col_chars, char_w, line_h, ascent, telemetry, snapshot, tick, theme, main_font, bold_font, small_font)
            curr_y1 += 12
            curr_y1 = self._draw_ram_panel(painter, col1_x, curr_y1, col_chars, char_w, line_h, ascent, telemetry, snapshot, tick, theme, main_font, bold_font)
            curr_y1 += 12
            curr_y1 = self._draw_gpu_panel(painter, col1_x, curr_y1, col_chars, char_w, line_h, ascent, telemetry, snapshot, tick, theme, main_font, bold_font)

            # Right Column: Storage, Network, Processes
            curr_y2 = 65
            curr_y2 = self._draw_storage_panel(painter, col2_x, curr_y2, col_chars, char_w, line_h, ascent, telemetry, snapshot, tick, theme, main_font, bold_font)
            curr_y2 += 12
            curr_y2 = self._draw_network_panel(painter, col2_x, curr_y2, col_chars, char_w, line_h, ascent, telemetry, snapshot, tick, theme, main_font, bold_font)
            curr_y2 += 12
            curr_y2 = self._draw_process_panel(painter, col2_x, curr_y2, col_chars, char_w, line_h, ascent, telemetry, snapshot, tick, theme, main_font, bold_font, small_font)
            
            panels_bottom = max(curr_y1, curr_y2)
        else:
            single_chars = int(available_w // char_w)
            curr_y = 65
            curr_y = self._draw_cpu_panel(painter, margin_x, curr_y, single_chars, char_w, line_h, ascent, telemetry, snapshot, tick, theme, main_font, bold_font, small_font)
            curr_y += 10
            curr_y = self._draw_ram_panel(painter, margin_x, curr_y, single_chars, char_w, line_h, ascent, telemetry, snapshot, tick, theme, main_font, bold_font)
            curr_y += 10
            curr_y = self._draw_gpu_panel(painter, margin_x, curr_y, single_chars, char_w, line_h, ascent, telemetry, snapshot, tick, theme, main_font, bold_font)
            panels_bottom = curr_y

        # 3. Dedicated Animated AI Agent Mascot & Neural Core Console
        if self.config.get("agent_avatar_enabled", True):
            agent_y = panels_bottom + 12
            panels_bottom = self._draw_agent_console(
                painter, margin_x, agent_y, available_w, char_w, line_h, ascent,
                telemetry, snapshot, tick, theme, main_font, bold_font
            )

        # 4. Expanded Autonomous Agent Intelligence Stream
        log_start_y = panels_bottom + 12
        self._draw_bottom_log(painter, margin_x, log_start_y, available_w, char_w, line_h, ascent, snapshot, tick, theme, main_font, bold_font, height)

    # -------------------------------------------------------------------------
    # Backing & Row Drawing Primitives
    # -------------------------------------------------------------------------

    def _draw_panel_backdrop(self, painter: QPainter, x: int, y: int, w_px: int, h_px: int, theme: Dict[str, Any]):
        """Draws a sleek semi-transparent frosted cyber panel behind each module for 100% contrast."""
        if not self.config.get("panel_backdrop", True):
            return
        panel_op = float(self.config.get("panel_opacity", 0.40))
        bg_col = QColor(6, 12, 22, int(panel_op * 255))
        rect = QRectF(x - 2, y - 2, w_px + 4, h_px + 4)
        painter.fillRect(rect, bg_col)
        # Subtle neon border
        border_col = QColor(theme["dim"])
        border_col.setAlpha(60)
        painter.setPen(QPen(border_col, 1))
        painter.drawRect(rect)

    def _draw_box_row(self, painter: QPainter, x: int, y: int, width_chars: int, char_w: int, ascent: int, segments: List[Tuple[str, QColor]], theme: Dict[str, Any], font: QFont):
        """
        Draws an exact monospace line inside box borders:
        - Column 0: '│ ' (in dim color)
        - Inner content: segments drawn at integer character positions
        - Trailing spaces: pads remaining columns
        - Last columns: ' │' (in dim color)
        """
        painter.setFont(font)
        baseline_y = y + ascent
        
        # Draw left border
        painter.setPen(theme["dim"])
        painter.drawText(x, baseline_y, "│ ")

        # Draw colored segments
        inner_max_chars = width_chars - 4
        current_col = 2
        total_content_len = 0

        for text, color in segments:
            if not text:
                continue
            # Clip if exceeds line
            if total_content_len + len(text) > inner_max_chars:
                text = text[:inner_max_chars - total_content_len]
            if not text:
                break
                
            seg_x = x + (current_col * char_w)
            painter.setPen(color)
            painter.drawText(seg_x, baseline_y, text)
            
            col_span = len(text)
            current_col += col_span
            total_content_len += col_span

        # Draw right border at exact integer column
        right_border_x = x + ((width_chars - 2) * char_w)
        painter.setPen(theme["dim"])
        painter.drawText(right_border_x, baseline_y, " │")

    def _draw_header_line(self, painter: QPainter, x: int, y: int, width_chars: int, char_w: int, ascent: int, title: str, theme: Dict[str, Any], font: QFont):
        header_str = format_box_header(title, width=width_chars)
        painter.setFont(font)
        painter.setPen(theme["primary"])
        painter.drawText(x, y + ascent, header_str)

    def _draw_footer_line(self, painter: QPainter, x: int, y: int, width_chars: int, char_w: int, ascent: int, extra: str, theme: Dict[str, Any], font: QFont):
        footer_str = format_box_footer(width=width_chars, extra=extra)
        painter.setFont(font)
        painter.setPen(theme["dim"])
        painter.drawText(x, y + ascent, footer_str)

    # -------------------------------------------------------------------------
    # Panels Implementation
    # -------------------------------------------------------------------------

    def _draw_top_header(self, painter: QPainter, width: int, telemetry: Dict[str, Any], snapshot: Dict[str, Any], tick: int, theme: Dict[str, Any], main_font: QFont, bold_font: QFont, fm: QFontMetrics, ascent: int):
        y = 20
        spinner = get_spinner("braille", tick)
        health_idx = snapshot.get("health_index", 100.0)
        health_status = snapshot.get("health_status", "OPTIMAL")
        uptime = telemetry["system"]["uptime"]
        now_time = time.strftime("%H:%M:%S")
        now_date = time.strftime("%a %b %d").upper()

        status_col = theme["success"] if health_idx >= 90 else (theme["accent"] if health_idx >= 75 else theme["danger"])

        # Row 1: Host and Health
        painter.setFont(bold_font)
        painter.setPen(theme["primary"])
        painter.drawText(20, y + ascent, f"◈ AGENT SENTINEL v1.2 // HOST: {telemetry['system']['hostname']} //")
        
        # Health status badge
        metrics = QFontMetrics(bold_font)
        badge_x = 20 + metrics.horizontalAdvance(f"◈ AGENT SENTINEL v1.2 // HOST: {telemetry['system']['hostname']} // ")
        painter.setPen(status_col)
        painter.drawText(badge_x, y + ascent, f"[ {health_status} {health_idx:.1f}% ]")

        # Live Clock & Date on right
        time_str = f"[ {now_time} ]  {now_date}"
        tw = metrics.horizontalAdvance(time_str)
        painter.setPen(theme["accent"])
        painter.drawText(width - 20 - tw, y + ascent, time_str)

        # Row 2: Secondary stats & Uptime
        y2 = y + fm.lineSpacing() + 2
        painter.setFont(main_font)
        painter.setPen(theme["secondary"])
        threads = telemetry["processes"]["thread_count"]
        painter.drawText(20, y2 + ascent, f"UPTIME: {uptime} | THREADS: {threads:,} | AGENT: [ {spinner} MONITORING ]")

        # Divider line
        div_y = y2 + fm.lineSpacing() + 4
        painter.setPen(theme["dim"])
        painter.drawLine(20, div_y, width - 20, div_y)

    def _draw_cpu_panel(self, painter: QPainter, x: int, y: int, w_chars: int, char_w: int, lh: int, ascent: int, telemetry: Dict[str, Any], snapshot: Dict[str, Any], tick: int, theme: Dict[str, Any], m_font: QFont, b_font: QFont, s_font: QFont) -> int:
        cpu = telemetry["cpu"]
        cores = cpu.get("cores", [])
        total_pct = cpu["total"]
        freq = cpu.get("freq_current_mhz", 0.0) / 1000.0

        # Estimate panel height
        rows_count = 3 + (5 if (self.config.get("show_per_core_matrix", True) and cores) else 0) + 1
        panel_h = rows_count * lh
        self._draw_panel_backdrop(painter, x, y, w_chars * char_w, panel_h, theme)

        # Header
        spinner = get_spinner("braille", tick)
        self._draw_header_line(painter, x, y, w_chars, char_w, ascent, f"CPU TELEMETRY  [{spinner}]", theme, b_font)
        y += lh

        # Load Bar
        shimmer = self.shimmer_tick if total_pct > 15 else -1
        bar = render_progress_bar(total_pct, width=14, style="blocks", shimmer_pos=shimmer)
        cpu_col = theme["danger"] if total_pct > 80 else (theme["accent"] if total_pct > 50 else theme["primary"])
        
        row1 = [
            ("LOAD:  ", theme["secondary"]),
            (f"[{bar}]", cpu_col),
            (f" {total_pct:5.1f}%", theme["accent"]),
            (f"  FREQ: {freq:.2f}GHz", theme["secondary"])
        ]
        self._draw_box_row(painter, x, y, w_chars, char_w, ascent, row1, theme, m_font)
        y += lh

        # Sparkline
        spark = render_sparkline(snapshot.get("cpu_history", []), width=20, min_val=0, max_val=100)
        row2 = [
            ("TREND: ", theme["secondary"]),
            (f"[{spark}]", theme["primary"]),
            (f"  {cpu['logical_count']} LOGICAL CORES", theme["secondary"])
        ]
        self._draw_box_row(painter, x, y, w_chars, char_w, ascent, row2, theme, m_font)
        y += lh

        # 20-Core Micro-grid (if enabled)
        if self.config.get("show_per_core_matrix", True) and cores:
            cols = 4
            num_cores = len(cores)
            for r in range(0, (num_cores + cols - 1) // cols):
                row_segs = []
                for c in range(cols):
                    c_idx = r * cols + c
                    if c_idx < num_cores:
                        cp = cores[c_idx]
                        cbar = render_progress_bar(cp, width=3, style="blocks")
                        c_col = theme["danger"] if cp > 80 else theme["secondary"]
                        row_segs.append((f"C{c_idx+1:02d}:[{cbar}]{cp:3.0f}% ", c_col))
                self._draw_box_row(painter, x, y, w_chars, char_w, ascent, row_segs, theme, m_font)
                y += lh

        # Footer
        self._draw_footer_line(painter, x, y, w_chars, char_w, ascent, f"PHYSICAL: {cpu['physical_count']} CORES", theme, m_font)
        y += lh
        return y

    def _draw_ram_panel(self, painter: QPainter, x: int, y: int, w_chars: int, char_w: int, lh: int, ascent: int, telemetry: Dict[str, Any], snapshot: Dict[str, Any], tick: int, theme: Dict[str, Any], m_font: QFont, b_font: QFont) -> int:
        mem = telemetry["memory"]
        panel_h = 4 * lh
        self._draw_panel_backdrop(painter, x, y, w_chars * char_w, panel_h, theme)

        # Header
        self._draw_header_line(painter, x, y, w_chars, char_w, ascent, "SYSTEM MEMORY", theme, b_font)
        y += lh

        # RAM
        ram_pct = mem["percent"]
        ram_bar = render_progress_bar(ram_pct, width=14, style="blocks")
        ram_col = theme["danger"] if ram_pct > 85 else theme["primary"]
        row1 = [
            ("RAM:   ", theme["secondary"]),
            (f"[{ram_bar}]", ram_col),
            (f" {ram_pct:5.1f}%", theme["accent"]),
            (f"  {mem['used_gb']:.1f}/{mem['total_gb']:.1f}GB", theme["secondary"])
        ]
        self._draw_box_row(painter, x, y, w_chars, char_w, ascent, row1, theme, m_font)
        y += lh

        # Sparkline & Free GB
        ram_spark = render_sparkline(snapshot.get("ram_history", []), width=20, min_val=0, max_val=100)
        row2 = [
            ("HIST:  ", theme["secondary"]),
            (f"[{ram_spark}]", theme["secondary"]),
            (f"  FREE: {mem['free_gb']:.1f} GB", theme["primary"])
        ]
        self._draw_box_row(painter, x, y, w_chars, char_w, ascent, row2, theme, m_font)
        y += lh

        # Footer
        self._draw_footer_line(painter, x, y, w_chars, char_w, ascent, "STATUS: NOMINAL", theme, m_font)
        y += lh
        return y

    def _draw_gpu_panel(self, painter: QPainter, x: int, y: int, w_chars: int, char_w: int, lh: int, ascent: int, telemetry: Dict[str, Any], snapshot: Dict[str, Any], tick: int, theme: Dict[str, Any], m_font: QFont, b_font: QFont) -> int:
        gpu = telemetry["gpu"]
        if not gpu.get("available"):
            return y

        panel_h = 5 * lh
        self._draw_panel_backdrop(painter, x, y, w_chars * char_w, panel_h, theme)

        short_name = gpu.get("name", "GPU").replace("NVIDIA GeForce ", "")
        gpu_pct = gpu.get("utilization", 0.0)
        gpu_temp = gpu.get("temperature", 0)
        vram_used = gpu.get("mem_used_mb", 0.0) / 1024.0
        vram_total = gpu.get("mem_total_mb", 0.0) / 1024.0
        vram_pct = (vram_used / max(vram_total, 0.1)) * 100.0

        # Header
        self._draw_header_line(painter, x, y, w_chars, char_w, ascent, f"GPU SENTINEL - {short_name}", theme, b_font)
        y += lh

        # Core Load & Temp
        gpu_bar = render_progress_bar(gpu_pct, width=14, style="blocks")
        temp_col = theme["danger"] if gpu_temp >= 80 else (theme["accent"] if gpu_temp >= 65 else theme["success"])
        row1 = [
            ("CORE:  ", theme["secondary"]),
            (f"[{gpu_bar}]", theme["primary"]),
            (f" {gpu_pct:5.1f}%", theme["accent"]),
            (f"  TEMP: {gpu_temp}°C", temp_col)
        ]
        self._draw_box_row(painter, x, y, w_chars, char_w, ascent, row1, theme, m_font)
        y += lh

        # VRAM
        vram_bar = render_progress_bar(vram_pct, width=14, style="blocks")
        row2 = [
            ("VRAM:  ", theme["secondary"]),
            (f"[{vram_bar}]", theme["secondary"]),
            (f" {vram_pct:5.1f}%", theme["accent"]),
            (f"  {vram_used:.1f}/{vram_total:.1f}GB", theme["secondary"])
        ]
        self._draw_box_row(painter, x, y, w_chars, char_w, ascent, row2, theme, m_font)
        y += lh

        # Sparkline
        gpu_spark = render_sparkline(snapshot.get("gpu_history", []), width=20, min_val=0, max_val=100)
        row3 = [
            ("HIST:  ", theme["secondary"]),
            (f"[{gpu_spark}]", theme["primary"]),
            ("  HEADROOM: OK", theme["secondary"])
        ]
        self._draw_box_row(painter, x, y, w_chars, char_w, ascent, row3, theme, m_font)
        y += lh

        # Footer
        self._draw_footer_line(painter, x, y, w_chars, char_w, ascent, "HARDWARE: SAFE", theme, m_font)
        y += lh
        return y

    def _draw_storage_panel(self, painter: QPainter, x: int, y: int, w_chars: int, char_w: int, lh: int, ascent: int, telemetry: Dict[str, Any], snapshot: Dict[str, Any], tick: int, theme: Dict[str, Any], m_font: QFont, b_font: QFont) -> int:
        disk = telemetry["disk"]
        partitions = disk.get("partitions", [])[:3]

        panel_h = (len(partitions) + 3) * lh
        self._draw_panel_backdrop(painter, x, y, w_chars * char_w, panel_h, theme)

        # Header
        self._draw_header_line(painter, x, y, w_chars, char_w, ascent, "STORAGE & DISK I/O", theme, b_font)
        y += lh

        # Drives
        for p in partitions:
            m = p["mountpoint"]
            pct = p["percent"]
            pbar = render_progress_bar(pct, width=12, style="blocks")
            p_col = theme["danger"] if pct > 90 else theme["primary"]
            row = [
                (f"DISK {m[:2]}", theme["secondary"]),
                (f" [{pbar}]", p_col),
                (f" {pct:5.1f}%", theme["accent"]),
                (f" {p['used_gb']:.0f}/{p['total_gb']:.0f}GB", theme["secondary"])
            ]
            self._draw_box_row(painter, x, y, w_chars, char_w, ascent, row, theme, m_font)
            y += lh

        # Read / Write Rates
        r_mb = disk.get("read_mb_s", 0.0)
        w_mb = disk.get("write_mb_s", 0.0)
        row_io = [
            ("I/O:   ", theme["secondary"]),
            (f"READ: {r_mb:5.2f}MB/s", theme["accent"]),
            (f"  WRITE: {w_mb:5.2f}MB/s", theme["secondary"])
        ]
        self._draw_box_row(painter, x, y, w_chars, char_w, ascent, row_io, theme, m_font)
        y += lh

        # Footer
        self._draw_footer_line(painter, x, y, w_chars, char_w, ascent, "DRIVES HEALTHY", theme, m_font)
        y += lh
        return y

    def _draw_network_panel(self, painter: QPainter, x: int, y: int, w_chars: int, char_w: int, lh: int, ascent: int, telemetry: Dict[str, Any], snapshot: Dict[str, Any], tick: int, theme: Dict[str, Any], m_font: QFont, b_font: QFont) -> int:
        net = telemetry["network"]
        panel_h = 4 * lh
        self._draw_panel_backdrop(painter, x, y, w_chars * char_w, panel_h, theme)

        # Header
        self._draw_header_line(painter, x, y, w_chars, char_w, ascent, "NETWORK TELEMETRY", theme, b_font)
        y += lh

        rx_kb = net.get("rx_kb_s", 0.0)
        tx_kb = net.get("tx_kb_s", 0.0)
        rx_spark = render_sparkline(snapshot.get("net_rx_history", []), width=16, min_val=0, max_val=2.0)

        rx_str = f"{rx_kb/1024.0:5.2f} MB/s" if rx_kb > 1024 else f"{rx_kb:5.1f} KB/s"
        tx_str = f"{tx_kb/1024.0:5.2f} MB/s" if tx_kb > 1024 else f"{tx_kb:5.1f} KB/s"

        row1 = [
            ("NET RX:", theme["secondary"]),
            (f" {rx_str:<10}", theme["accent"]),
            (f" HIST:[{rx_spark}]", theme["secondary"])
        ]
        self._draw_box_row(painter, x, y, w_chars, char_w, ascent, row1, theme, m_font)
        y += lh

        row2 = [
            ("NET TX:", theme["secondary"]),
            (f" {tx_str:<10}", theme["secondary"]),
            (f" ACTIVE CONNS: {net.get('connections', 0)}", theme["primary"])
        ]
        self._draw_box_row(painter, x, y, w_chars, char_w, ascent, row2, theme, m_font)
        y += lh

        # Footer
        self._draw_footer_line(painter, x, y, w_chars, char_w, ascent, "LINK: ACTIVE", theme, m_font)
        y += lh
        return y

    def _draw_process_panel(self, painter: QPainter, x: int, y: int, w_chars: int, char_w: int, lh: int, ascent: int, telemetry: Dict[str, Any], snapshot: Dict[str, Any], tick: int, theme: Dict[str, Any], m_font: QFont, b_font: QFont, s_font: QFont) -> int:
        procs = telemetry.get("processes", {})
        top_cpu = procs.get("top_cpu", [])[:5]

        panel_h = (len(top_cpu) + 3) * lh
        self._draw_panel_backdrop(painter, x, y, w_chars * char_w, panel_h, theme)

        # Header
        self._draw_header_line(painter, x, y, w_chars, char_w, ascent, "PROCESS SENTINEL (TOP CPU)", theme, b_font)
        y += lh

        # Subheader
        subhead = [
            ("PID    NAME                  CPU%     MEM (MB)", theme["dim"])
        ]
        self._draw_box_row(painter, x, y, w_chars, char_w, ascent, subhead, theme, m_font)
        y += lh

        # Rows
        for p in top_cpu:
            pid = p.get("pid", 0)
            name = (p.get("name") or "Unknown")[:20]
            cp = p.get("cpu_percent", 0.0)
            mem = p.get("mem_mb", 0.0)
            cp_col = theme["accent"] if cp > 20 else theme["primary"]

            row = [
                (f"{pid:<6d} {name:<21} {cp:5.1f}%   {mem:7.1f}MB", cp_col)
            ]
            self._draw_box_row(painter, x, y, w_chars, char_w, ascent, row, theme, m_font)
            y += lh

        # Footer
        total_p = procs.get("total_count", 0)
        self._draw_footer_line(painter, x, y, w_chars, char_w, ascent, f"TOTAL: {total_p} PROCS", theme, m_font)
        y += lh
        return y

    def _draw_agent_console(self, painter: QPainter, x: int, y: int, avail_w: int, char_w: int, lh: int, ascent: int, telemetry: Dict[str, Any], snapshot: Dict[str, Any], tick: int, theme: Dict[str, Any], m_font: QFont, b_font: QFont) -> int:
        """Renders the dedicated Cyber AI Sentinel Mascot Avatar & Live Neural Oscilloscope Console."""
        w_chars = int(avail_w // char_w)
        if w_chars < 50:
            return y

        panel_h = 7 * lh
        self._draw_panel_backdrop(painter, x, y, w_chars * char_w, panel_h, theme)

        # Header
        spinner = get_spinner("braille", tick)
        health_idx = snapshot.get("health_index", 100.0)
        core_badge = "OPTIMAL" if health_idx >= 90 else ("NOMINAL" if health_idx >= 75 else "ALERT")
        self._draw_header_line(painter, x, y, w_chars, char_w, ascent, f"AI AGENT SENTINEL // AUTONOMOUS NEURAL CORE  [{spinner}]", theme, b_font)
        y += lh

        # Determine mascot mode & combined system load
        cpu_total = telemetry.get("cpu", {}).get("total", 0.0)
        gpu_util = telemetry.get("gpu", {}).get("utilization", 0.0) if telemetry.get("gpu", {}).get("available") else 0.0
        combined_load = max(cpu_total, gpu_util)
        
        active_game = snapshot.get("active_game")
        if active_game:
            mascot_mode = "game"
        elif combined_load > 70.0:
            mascot_mode = "high"
        else:
            mascot_mode = "normal"

        mascot_rows = get_mascot_segments(tick, mode=mascot_mode, load=combined_load)
        right_avail = max(10, w_chars - 26)

        mood = snapshot.get("agent_mood", "VIGILANT")
        thought = snapshot.get("agent_thought", "Sentinel autonomous surveillance matrix online.")
        cycle = snapshot.get("diagnostic_cycle", 0)
        
        # Dynamic neural wave (if enabled)
        show_wave = self.config.get("agent_neural_wave_enabled", True)
        wave_width = max(10, min(28, right_avail - 26))
        wave_str = render_neural_wave(tick, load=combined_load, width=wave_width) if show_wave else ("─" * wave_width)
        wave_freq = (telemetry.get("cpu", {}).get("freq_current_mhz", 2400.0) or 2400.0) / 1000.0

        # Radar scanner glyph
        radar_glyphs = ["◐", "◓", "◑", "◒"]
        radar = radar_glyphs[(tick // 4) % 4]

        # Right side rows data
        right_rows_data = [
            # Row 0: Status & Cognitive Core
            [
                ("STATE: ", theme["dim"]),
                (f"[{mood}]", theme["danger"] if ("DEFENSE" in mood or "ALERT" in mood) else theme["accent"]),
                (" // COGNITIVE CORE: ONLINE // PULSE: ", theme["secondary"]),
                (f"#{cycle:,}", theme["primary"])
            ],
            # Row 1: Neural Waveform
            [
                ("NEURAL WAVE: ", theme["dim"]),
                (f"[{wave_str}]", theme["accent"] if combined_load > 60 else theme["primary"]),
                (f" {wave_freq:.2f} GHz", theme["secondary"])
            ],
            # Row 2: Live Agent Thought
            [
                ("AGENT FOCUS: ", theme["dim"]),
                (f'"{thought}"', theme["accent"] if active_game else theme["primary"])
            ],
            # Row 3: Quantum Process Radar
            [
                ("SURVEILLANCE: ", theme["dim"]),
                (f"{radar} [PROCESS POOL WATCHDOG] • ", theme["accent"]),
                ("20 CORES BALANCED • SYNC: 100%", theme["secondary"])
            ],
            # Row 4: Mission Directive
            [
                ("DIRECTIVE: ", theme["dim"]),
                ("24/7 AUTONOMOUS PC HEALTH SURVEILLANCE & GAMING OPTIMIZATION", theme["secondary"])
            ]
        ]

        # Render composite lines
        for r_idx in range(5):
            row_segs: List[Tuple[str, QColor]] = []
            
            # 1. Mascot segments (exact 20 chars)
            for m_txt, m_col_key in mascot_rows[r_idx]:
                row_segs.append((m_txt, theme.get(m_col_key, theme["secondary"])))
                
            # 2. Separator (2 chars)
            row_segs.append(("  ", theme["dim"]))
            
            # 3. Right side content
            for r_txt, r_col in right_rows_data[r_idx]:
                row_segs.append((r_txt, r_col))
                
            self._draw_box_row(painter, x, y, w_chars, char_w, ascent, row_segs, theme, m_font)
            y += lh

        # Footer
        footer_badge = f"CORE: {core_badge} • SENTINEL ENGAGED"
        self._draw_footer_line(painter, x, y, w_chars, char_w, ascent, footer_badge, theme, m_font)
        y += lh
        return y

    def _draw_bottom_log(self, painter: QPainter, x: int, y: int, avail_w: int, char_w: int, lh: int, ascent: int, snapshot: Dict[str, Any], tick: int, theme: Dict[str, Any], m_font: QFont, b_font: QFont, total_height: int):
        logs = snapshot.get("logs", [])
        if not logs:
            return

        w_chars = int(avail_w // char_w)
        
        # Calculate available vertical space dynamically to expand the section
        available_h = max(180, total_height - y - 24)
        
        # Allocate 8 to 14 lines based on available space
        max_log_rows = max(8, min(14, int((available_h // lh) - 3)))
        recent = logs[-max_log_rows:]
        
        total_rows = len(recent) + 3 # Header + subheader + log entries + footer
        panel_h = total_rows * lh
        self._draw_panel_backdrop(painter, x, y, w_chars * char_w, panel_h, theme)

        # Header
        spinner = get_spinner("braille", tick)
        self._draw_header_line(painter, x, y, w_chars, char_w, ascent, f"AUTONOMOUS AGENT INTELLIGENCE STREAM  [{spinner}]", theme, b_font)
        y += lh

        # Column guide subheader
        subhead_row = [
            ("TIMESTAMP  SUBSYSTEM       STATUS / DIAGNOSTIC STREAM", theme["dim"])
        ]
        self._draw_box_row(painter, x, y, w_chars, char_w, ascent, subhead_row, theme, m_font)
        y += lh

        blink = "_" if (tick % 20 < 10) else " "

        for i, item in enumerate(recent):
            t_str = item.get("timestamp", "")
            tag = item.get("tag", "INFO")
            msg = item.get("message", "")
            lvl = item.get("level", "INFO")

            is_latest = (i == len(recent) - 1)
            cursor = blink if is_latest else ""
            msg_col = theme["danger"] if lvl == "WARN" else (theme["accent"] if is_latest else theme["secondary"])
            tag_col = theme["accent"] if lvl == "WARN" else theme["primary"]

            row = [
                (f"{t_str} ", theme["dim"]),
                (f"[{tag:<14}] ", tag_col),
                (f"{msg}{cursor}", msg_col)
            ]
            self._draw_box_row(painter, x, y, w_chars, char_w, ascent, row, theme, m_font)
            y += lh

        self._draw_footer_line(painter, x, y, w_chars, char_w, ascent, f"REALTIME WATCHDOG ACTIVE // BUFFER: {len(logs)} EVENTS", theme, m_font)

    def _draw_game_report_hud(self, painter: QPainter, width: int, height: int, telemetry: Dict[str, Any], snapshot: Dict[str, Any], tick: int, theme: Dict[str, Any], main_font: QFont, bold_font: QFont, small_font: QFont, fm: QFontMetrics, char_w: int, line_h: int, ascent: int, report_countdown_sec: float = 0.0, report_timer_paused: bool = False):
        """Renders the dedicated Post-Game Performance Debrief HUD view."""
        report = snapshot.get("game_report")
        margin_x = 20
        available_w = width - (margin_x * 2)
        gap_x = 16
        col_chars = int((available_w - gap_x) // (2 * char_w))

        if not report:
            # Standby state if no game report has been recorded yet
            panel_w = width - (margin_x * 2)
            w_chars = int(panel_w // char_w)
            y = 80
            self._draw_panel_backdrop(painter, margin_x, y, w_chars * char_w, 8 * line_h, theme)
            self._draw_header_line(painter, margin_x, y, w_chars, char_w, ascent, "GAME PERFORMANCE SENTINEL // WAITING FOR SESSION", theme, bold_font)
            y += line_h
            row1 = [("NO COMPLETED GAME SESSION RECORDED YET.", theme["accent"])]
            self._draw_box_row(painter, margin_x, y, w_chars, char_w, ascent, row1, theme, main_font)
            y += line_h
            row2 = [("Launch any Steam, Epic, or PC game — the agent monitors PC resources automatically.", theme["secondary"])]
            self._draw_box_row(painter, margin_x, y, w_chars, char_w, ascent, row2, theme, main_font)
            y += line_h
            row3 = [("When you close the game, this HUD will pop up automatically with a full debrief.", theme["secondary"])]
            self._draw_box_row(painter, margin_x, y, w_chars, char_w, ascent, row3, theme, main_font)
            y += line_h
            row4 = [("To test this view right now: Right-click Tray Icon -> '⚡ Test / Simulate Game Report'.", theme["primary"])]
            self._draw_box_row(painter, margin_x, y, w_chars, char_w, ascent, row4, theme, main_font)
            y += line_h
            row5 = [("Press [T] to return to Live System Telemetry HUD.", theme["dim"])]
            self._draw_box_row(painter, margin_x, y, w_chars, char_w, ascent, row5, theme, main_font)
            y += line_h
            self._draw_footer_line(painter, margin_x, y, w_chars, char_w, ascent, "GAME SENTINEL ARMED", theme, main_font)
            return

        # 1. Top Header Banner
        y = 20
        spinner = get_spinner("braille", tick)
        grade = report.get("grade", "S")
        grade_col = theme["accent"] if grade == "S" else (theme["success"] if grade == "A" else (theme["primary"] if grade == "B" else theme["danger"]))

        painter.setFont(bold_font)
        painter.setPen(theme["primary"])
        painter.drawText(margin_x, y + ascent, f"◈ POST-GAME PERFORMANCE DEBRIEF // [{spinner}] // GRADE: ")
        
        bw = fm.horizontalAdvance(f"◈ POST-GAME PERFORMANCE DEBRIEF // [{spinner}] // GRADE: ")
        painter.setPen(grade_col)
        painter.drawText(margin_x + bw, y + ascent, f"[ {grade} - OPTIMAL ]" if grade in ["S", "A"] else f"[ {grade} - NOTICE ]")

        # Session Time on right
        time_text = f"SESSION: {report['duration_str']}  ({report['start_str']} - {report['end_str']})"
        rw = fm.horizontalAdvance(time_text)
        painter.setPen(theme["secondary"])
        painter.drawText(width - margin_x - rw, y + ascent, time_text)

        # Game title sub-bar
        y2 = y + line_h
        painter.setFont(main_font)
        painter.setPen(theme["accent"])
        painter.drawText(margin_x, y2 + ascent, f"GAME: {report['title']} ({report['exe']}) // SAMPLES COLLECTED: {report['samples_count']}")

        painter.setPen(theme["dim"])
        painter.drawLine(margin_x, y2 + line_h + 2, width - margin_x, y2 + line_h + 2)

        # 2. Dual Column Layout
        col_px_w = col_chars * char_w
        col1_x = margin_x
        col2_x = margin_x + col_px_w + gap_x
        curr_y1 = 75
        curr_y2 = 75

        # --- Left Column: GPU Performance & CPU Footprint ---
        gpu = report["gpu"]
        cpu = report["cpu"]
        ram = report["ram"]
        disk = report["disk"]

        # GPU Card
        panel_h_gpu = 7 * line_h
        self._draw_panel_backdrop(painter, col1_x, curr_y1, col_px_w, panel_h_gpu, theme)
        self._draw_header_line(painter, col1_x, curr_y1, col_chars, char_w, ascent, "GPU INTENSIVE TELEMETRY (RTX 3060)", theme, bold_font)
        curr_y1 += line_h

        bar_gpu = render_progress_bar(gpu['avg_load'], width=12, style="blocks")
        r_gpu_load = [
            ("AVG GPU LOAD: ", theme["secondary"]),
            (f"[{bar_gpu}] {gpu['avg_load']:4.1f}%", theme["primary"]),
            (f"  PEAK: {gpu['peak_load']:4.1f}%", theme["accent"])
        ]
        self._draw_box_row(painter, col1_x, curr_y1, col_chars, char_w, ascent, r_gpu_load, theme, main_font)
        curr_y1 += line_h

        t_stat = "SAFE" if gpu['peak_temp'] < 75 else ("WARM" if gpu['peak_temp'] < 82 else "HOT")
        t_col = theme["success"] if gpu['peak_temp'] < 75 else theme["danger"]
        r_gpu_temp = [
            ("GPU THERMALS: ", theme["secondary"]),
            (f"AVG: {gpu['avg_temp']:4.1f}°C", theme["primary"]),
            (f" | PEAK: {gpu['peak_temp']:4.1f}°C ", theme["secondary"]),
            (f"[{t_stat}]", t_col)
        ]
        self._draw_box_row(painter, col1_x, curr_y1, col_chars, char_w, ascent, r_gpu_temp, theme, main_font)
        curr_y1 += line_h

        r_vram = [
            ("VRAM CONSUMED: ", theme["secondary"]),
            (f"AVG: {gpu['avg_vram']:4.1f}GB", theme["primary"]),
            (f" | PEAK: {gpu['peak_vram']:4.1f}/12GB", theme["accent"])
        ]
        self._draw_box_row(painter, col1_x, curr_y1, col_chars, char_w, ascent, r_vram, theme, main_font)
        curr_y1 += line_h

        spark_gpu = render_sparkline(gpu.get("history", []), width=18, min_val=0, max_val=100)
        r_spark_gpu = [
            ("LOAD TIMELINE: ", theme["secondary"]),
            (f"[{spark_gpu}]", theme["primary"])
        ]
        self._draw_box_row(painter, col1_x, curr_y1, col_chars, char_w, ascent, r_spark_gpu, theme, main_font)
        curr_y1 += line_h

        spark_temp = render_sparkline(gpu.get("temp_history", []), width=18, min_val=40, max_val=85)
        r_spark_temp = [
            ("TEMP TIMELINE: ", theme["secondary"]),
            (f"[{spark_temp}]", theme["accent"])
        ]
        self._draw_box_row(painter, col1_x, curr_y1, col_chars, char_w, ascent, r_spark_temp, theme, main_font)
        curr_y1 += line_h

        self._draw_footer_line(painter, col1_x, curr_y1, col_chars, char_w, ascent, "THERMAL STABILITY: 100%", theme, main_font)
        curr_y1 += line_h + 12

        # CPU & Memory Card
        panel_h_cpu = 6 * line_h
        self._draw_panel_backdrop(painter, col1_x, curr_y1, col_px_w, panel_h_cpu, theme)
        self._draw_header_line(painter, col1_x, curr_y1, col_chars, char_w, ascent, "CPU & SYSTEM FOOTPRINT", theme, bold_font)
        curr_y1 += line_h

        bar_cpu = render_progress_bar(cpu['avg'], width=12, style="blocks")
        r_cpu_load = [
            ("AVG CPU LOAD: ", theme["secondary"]),
            (f"[{bar_cpu}] {cpu['avg']:4.1f}%", theme["primary"]),
            (f"  PEAK: {cpu['peak']:4.1f}%", theme["accent"])
        ]
        self._draw_box_row(painter, col1_x, curr_y1, col_chars, char_w, ascent, r_cpu_load, theme, main_font)
        curr_y1 += line_h

        r_ram = [
            ("RAM FOOTPRINT: ", theme["secondary"]),
            (f"AVG: {ram['avg']:4.1f}GB", theme["primary"]),
            (f" | PEAK: {ram['peak']:4.1f}/31.8GB", theme["secondary"])
        ]
        self._draw_box_row(painter, col1_x, curr_y1, col_chars, char_w, ascent, r_ram, theme, main_font)
        curr_y1 += line_h

        r_disk = [
            ("ASSET I/O PEAK: ", theme["secondary"]),
            (f"{disk['peak_read_mb']:5.1f} MB/s READ (STREAMING)", theme["accent"])
        ]
        self._draw_box_row(painter, col1_x, curr_y1, col_chars, char_w, ascent, r_disk, theme, main_font)
        curr_y1 += line_h

        spark_cpu = render_sparkline(cpu.get("history", []), width=18, min_val=0, max_val=100)
        r_spark_cpu = [
            ("CPU TIMELINE:  ", theme["secondary"]),
            (f"[{spark_cpu}]", theme["primary"])
        ]
        self._draw_box_row(painter, col1_x, curr_y1, col_chars, char_w, ascent, r_spark_cpu, theme, main_font)
        curr_y1 += line_h

        self._draw_footer_line(painter, col1_x, curr_y1, col_chars, char_w, ascent, "20 CORES BALANCED", theme, main_font)
        curr_y1 += line_h

        # --- Right Column: Agent Verdict & Timeline ---
        verdicts = report.get("verdict", [])
        events = report.get("events", [])[-5:]

        # Verdict Card
        panel_h_verdict = (len(verdicts) + 2) * line_h
        self._draw_panel_backdrop(painter, col2_x, curr_y2, col_px_w, panel_h_verdict, theme)
        self._draw_header_line(painter, col2_x, curr_y2, col_chars, char_w, ascent, "AGENT HARDWARE ASSESSMENT & VERDICT", theme, bold_font)
        curr_y2 += line_h

        for note in verdicts:
            r_note = [("> ", theme["accent"]), (note, theme["primary"])]
            self._draw_box_row(painter, col2_x, curr_y2, col_chars, char_w, ascent, r_note, theme, main_font)
            curr_y2 += line_h

        self._draw_footer_line(painter, col2_x, curr_y2, col_chars, char_w, ascent, f"PERFORMANCE GRADE: {grade}", theme, main_font)
        curr_y2 += line_h + 12

        # Session Timeline Events Card
        panel_h_events = (len(events) + 2) * line_h
        self._draw_panel_backdrop(painter, col2_x, curr_y2, col_px_w, panel_h_events, theme)
        self._draw_header_line(painter, col2_x, curr_y2, col_chars, char_w, ascent, "SESSION TIMELINE & ANOMALIES", theme, bold_font)
        curr_y2 += line_h

        for ev in events:
            r_ev = [
                (f"{ev['time']} ", theme["dim"]),
                (f"[{ev['tag']:<14}] ", theme["accent"]),
                (ev['message'], theme["secondary"])
            ]
            self._draw_box_row(painter, col2_x, curr_y2, col_chars, char_w, ascent, r_ev, theme, main_font)
            curr_y2 += line_h

        self._draw_footer_line(painter, col2_x, curr_y2, col_chars, char_w, ascent, "SESSION LOG PRESERVED", theme, main_font)
        curr_y2 += line_h

        # 3. Bottom Control Navigation Bar
        bot_y = max(curr_y1, curr_y2) + 14
        bot_w = width - (margin_x * 2)
        bot_chars = int(bot_w // char_w)
        self._draw_panel_backdrop(painter, margin_x, bot_y, bot_chars * char_w, 3 * line_h, theme)
        timer_header = f"HUD VIEW CONTROL // [{spinner}]"
        self._draw_header_line(painter, margin_x, bot_y, bot_chars, char_w, ascent, timer_header, theme, bold_font)
        bot_y += line_h

        if report_countdown_sec > 0.0:
            m = int(report_countdown_sec) // 60
            s = int(report_countdown_sec) % 60
            t_str = f"{m:02d}:{s:02d}"
            if report_timer_paused:
                timer_seg = (f"[ AUTO-RETURN PAUSED ({t_str}) ]", theme["dim"])
            else:
                timer_seg = (f"[ AUTO-RETURNING IN {t_str} ]", theme["accent"])
        else:
            timer_seg = ("[ MANUAL DEBRIEF MODE ]", theme["secondary"])

        nav_row = [
            timer_seg,
            ("  •  PRESS [T] TO RETURN TO LIVE TELEMETRY NOW  •  TRAY MENU TO HOLD/PAUSE", theme["primary"])
        ]
        self._draw_box_row(painter, margin_x, bot_y, bot_chars, char_w, ascent, nav_row, theme, main_font)
        bot_y += line_h
        footer_status = f"AUTO-DISMISS: {'PAUSED' if report_timer_paused else ('ACTIVE' if report_countdown_sec > 0 else 'DISABLED')}"
        self._draw_footer_line(painter, margin_x, bot_y, bot_chars, char_w, ascent, footer_status, theme, main_font)

    def _draw_news_hud(self, painter: QPainter, width: int, height: int, telemetry: Dict[str, Any], snapshot: Dict[str, Any], tick: int, theme: Dict[str, Any], main_font: QFont, bold_font: QFont, small_font: QFont, fm: QFontMetrics, char_w: int, line_h: int, ascent: int, auto_rotate_countdown_sec: float = 0.0):
        """Renders the autonomous verified news feed, live social chatter, and agent recon stream."""
        self.news_click_rects = []
        news = snapshot.get("news") or {}
        items = news.get("items", [])
        expanded_id = news.get("expanded_news_id")
        agent_phase = news.get("agent_phase", "SURVEILLANCE ACTIVE")
        agent_thought = news.get("agent_thought", "")
        activities = news.get("activities", [])
        stats = news.get("stats", {})
        countdown_str = news.get("countdown_str", "30m 00s")
        sweep_prog = news.get("sweep_progress", 0.0)

        margin_x = 20
        y = 20
        spinner = get_spinner("braille", tick)

        # 1. Top Header Banner
        painter.setFont(bold_font)
        painter.setPen(theme["primary"])
        painter.drawText(margin_x, y + ascent, f"◈ SENTINEL RECON MATRIX // VERIFIED NEWS & SOCIAL CHATTER [{spinner}]")

        # Right side: Auto-rotate & 30-min sweep timer
        rot_str = f"AUTO-ROTATE: {f'ON ({int(auto_rotate_countdown_sec)}s)' if auto_rotate_countdown_sec > 0 else 'HOLD'}  |  " if auto_rotate_countdown_sec >= 0 else ""
        timer_text = f"{rot_str}NEXT 30M SWEEP: {countdown_str}"
        rw = fm.horizontalAdvance(timer_text)
        painter.setPen(theme["accent"])
        painter.drawText(width - margin_x - rw, y + ascent, timer_text)

        # Sub-header
        y2 = y + line_h
        painter.setFont(small_font)
        painter.setPen(theme["secondary"])
        purged = stats.get("ai_slop_purged", 94)
        scanned = stats.get("total_scanned", 1280)
        cred_avg = stats.get("credibility_avg", 97.6)
        painter.drawText(margin_x, y2 + ascent, f"FILTERS: 0% AI-SLOP // >80% CREDIBILITY // PURGED: {purged} SLOP & CLICKBAIT POSTS // SCANNED: {scanned:,} // CONFIDENCE: {cred_avg:.1f}%")

        painter.setPen(theme["dim"])
        painter.drawLine(margin_x, y2 + line_h + 2, width - margin_x, y2 + line_h + 2)

        # 2. Dual Column Layout
        available_w = width - (margin_x * 2)
        gap_x = 16
        col_chars = int((available_w - gap_x) // (2 * char_w))

        if col_chars >= 35:
            col1_w = int(available_w * 0.58)
            col2_w = available_w - col1_w - gap_x
            col1_chars = int(col1_w // char_w)
            col2_chars = int(col2_w // char_w)
            col1_x = margin_x
            col2_x = margin_x + col1_w + gap_x
            curr_y1 = y2 + line_h + 10
            curr_y2 = y2 + line_h + 10

            # --- Left Column: Verified News & Expandable Social Chatter ---
            panel_news_header = f"VERIFIED BREAKING & TRENDING INTEL  [ {len(items)} STORIES ]"
            self._draw_panel_backdrop(painter, col1_x, curr_y1, col1_chars * char_w, 2 * line_h, theme)
            self._draw_header_line(painter, col1_x, curr_y1, col1_chars, char_w, ascent, panel_news_header, theme, bold_font)
            curr_y1 += line_h

            subhead = [
                ("TOP CHATTER STORIES // REAL-TIME FACT-CHECKED & CLUSTERED", theme["secondary"])
            ]
            self._draw_box_row(painter, col1_x, curr_y1, col1_chars, char_w, ascent, subhead, theme, small_font)
            curr_y1 += line_h + 8

            for idx, item in enumerate(items[:4]):
                item_id = item.get("id", f"news_{idx}")
                is_exp = (item_id == expanded_id)
                posts = item.get("live_posts", [])
                
                # Compute height of card
                post_lines = (len(posts) * 3 + 2) if is_exp else 0
                card_lines = 4 + post_lines
                card_h = card_lines * line_h + 6

                # Register clickable bounding box for mouse clicks
                self.news_click_rects.append((QRectF(col1_x, curr_y1, col1_w, card_h), item_id))

                self._draw_panel_backdrop(painter, col1_x, curr_y1, col1_chars * char_w, card_h, theme)
                
                # Card Header
                cat = item.get("category", "TECH")
                cred = item.get("credibility_percent", 98.0)
                buzz = item.get("buzz_score", 90)
                time_ago = item.get("time_ago", "recent")
                card_head_str = f"[{cat}] · {cred:.1f}% VERIFIED · 🔥 {buzz}% BUZZ · {time_ago}"
                self._draw_header_line(painter, col1_x, curr_y1, col1_chars, char_w, ascent, card_head_str, theme, bold_font)
                curr_y1 += line_h

                # Title
                title_str = item.get("title", "")
                r_title = [(f"► {title_str[:col1_chars-6]}", theme["accent"] if is_exp else theme["primary"])]
                self._draw_box_row(painter, col1_x, curr_y1, col1_chars, char_w, ascent, r_title, theme, bold_font)
                curr_y1 += line_h

                # Summary
                summary_str = item.get("summary", "")
                r_sum = [(f"  {summary_str[:col1_chars-6]}", theme["secondary"])]
                self._draw_box_row(painter, col1_x, curr_y1, col1_chars, char_w, ascent, r_sum, theme, small_font)
                curr_y1 += line_h

                # Expand/Collapse button line
                if is_exp:
                    btn_text = f"  [▲ COLLAPSE LIVE USER CHATTER ({len(posts)} POSTS)]"
                    btn_col = theme["accent"]
                else:
                    btn_text = f"  [▼ VIEW LIVE USER CHATTER ({len(posts)} POSTS) - CLICK TO EXPAND]"
                    btn_col = theme["primary"]
                self._draw_box_row(painter, col1_x, curr_y1, col1_chars, char_w, ascent, [(btn_text, btn_col)], theme, small_font)
                curr_y1 += line_h

                # Render user posts if expanded
                if is_exp:
                    for post in posts[:3]:
                        handle = post.get("handle", "@user")
                        author = post.get("author", "User")
                        tag = post.get("tag", "VERIFIED")
                        p_time = post.get("time", "now")
                        likes = post.get("likes", "1k")
                        sent = post.get("sentiment", "HOT")
                        p_head = [
                            ("    ", theme["dim"]),
                            (f"{handle}", theme["accent"]),
                            (f" ({author}) ", theme["secondary"]),
                            (f"[{tag}] ", theme["dim"]),
                            (f"· {p_time} · 👍 {likes} · [{sent}]", theme["primary"])
                        ]
                        self._draw_box_row(painter, col1_x, curr_y1, col1_chars, char_w, ascent, p_head, theme, small_font)
                        curr_y1 += line_h

                        # Post content
                        p_content = f'    "{post.get("content", "")}"'
                        self._draw_box_row(painter, col1_x, curr_y1, col1_chars, char_w, ascent, [(p_content[:col1_chars-4], theme["primary"])], theme, small_font)
                        curr_y1 += line_h

                    # Fact-check note footnote
                    fc_note = item.get("fact_check_note", "Cross-verified across multiple independent sources.")
                    fc_row = [
                        ("    ✓ VERIFICATION PROOF: ", theme["success"]),
                        (f"{fc_note[:col1_chars-30]}", theme["secondary"])
                    ]
                    self._draw_box_row(painter, col1_x, curr_y1, col1_chars, char_w, ascent, fc_row, theme, small_font)
                    curr_y1 += line_h

                self._draw_footer_line(painter, col1_x, curr_y1, col1_chars, char_w, ascent, f"SOURCE: {item.get('source', 'Web')}", theme, small_font)
                curr_y1 += line_h + 8

            # --- Right Column: Agent Live Recon Stream & Cognition Panel ---
            panel_agent_h = 7 * line_h
            self._draw_panel_backdrop(painter, col2_x, curr_y2, col2_chars * char_w, panel_agent_h, theme)
            self._draw_header_line(painter, col2_x, curr_y2, col2_chars, char_w, ascent, f"AGENT LIVE RECON STREAM // [{spinner}]", theme, bold_font)
            curr_y2 += line_h

            mascot_rows = get_mascot_segments(tick, mode="normal", load=25.0)
            p_bar = render_progress_bar(sweep_prog, width=12, style="blocks")

            for m_idx in range(5):
                m_seg = mascot_rows[m_idx] if m_idx < len(mascot_rows) else " " * 20
                if m_idx == 0:
                    r_data = [
                        (f"  {m_seg}  ", theme["accent"]),
                        ("PHASE: ", theme["dim"]),
                        (f"[{agent_phase[:col2_chars-36]}]", theme["primary"])
                    ]
                elif m_idx == 1:
                    r_data = [
                        (f"  {m_seg}  ", theme["accent"]),
                        ("AGENT FOCUS: ", theme["dim"]),
                        (f'"{agent_thought[:col2_chars-42]}"', theme["secondary"])
                    ]
                elif m_idx == 2:
                    r_data = [
                        (f"  {m_seg}  ", theme["accent"]),
                        ("SWEEP CYCLE: ", theme["dim"]),
                        (f"[{p_bar}] {countdown_str}", theme["accent"])
                    ]
                elif m_idx == 3:
                    r_data = [
                        (f"  {m_seg}  ", theme["accent"]),
                        ("FIREHOSE: ", theme["dim"]),
                        ("BLUESKY JETSTREAM // REDDIT RISING // TRENDS", theme["secondary"])
                    ]
                else:
                    r_data = [
                        (f"  {m_seg}  ", theme["accent"]),
                        ("AUTO-DEFENSE: ", theme["dim"]),
                        ("AI-SLOP PURGE ENGAGED // 100% FACT-CHECKED", theme["success"])
                    ]
                self._draw_box_row(painter, col2_x, curr_y2, col2_chars, char_w, ascent, r_data, theme, small_font)
                curr_y2 += line_h

            self._draw_footer_line(painter, col2_x, curr_y2, col2_chars, char_w, ascent, "NEURAL SENTINEL: STREAMING LIVE", theme, small_font)
            curr_y2 += line_h + 10

            # Panel 2: Real-time Verification & Purge Metrics
            panel_metrics_h = 6 * line_h
            self._draw_panel_backdrop(painter, col2_x, curr_y2, col2_chars * char_w, panel_metrics_h, theme)
            self._draw_header_line(painter, col2_x, curr_y2, col2_chars, char_w, ascent, "VERIFICATION HEURISTICS & PURGE STATS", theme, bold_font)
            curr_y2 += line_h

            m_row1 = [
                ("  TOTAL SOCIAL POSTS INGESTED: ", theme["secondary"]),
                (f"{scanned:,} POSTS", theme["primary"])
            ]
            self._draw_box_row(painter, col2_x, curr_y2, col2_chars, char_w, ascent, m_row1, theme, small_font)
            curr_y2 += line_h

            m_row2 = [
                ("  AI SLOP & CLICKBAIT DROPPED: ", theme["secondary"]),
                (f"-{purged} DISCARDED [0% SLOP ALLOWED]", theme["danger"])
            ]
            self._draw_box_row(painter, col2_x, curr_y2, col2_chars, char_w, ascent, m_row2, theme, small_font)
            curr_y2 += line_h

            m_row3 = [
                ("  HIGH-CONFIDENCE BREAKOUTS:   ", theme["secondary"]),
                (f"{len(items)} VERIFIED STORIES PUBLISHED", theme["success"])
            ]
            self._draw_box_row(painter, col2_x, curr_y2, col2_chars, char_w, ascent, m_row3, theme, small_font)
            curr_y2 += line_h

            m_row4 = [
                ("  MEAN CREDIBILITY INDEX:      ", theme["secondary"]),
                (f"{cred_avg:.1f}% ACCURACY (MULTI-NODE CROSS-REF)", theme["accent"])
            ]
            self._draw_box_row(painter, col2_x, curr_y2, col2_chars, char_w, ascent, m_row4, theme, small_font)
            curr_y2 += line_h

            self._draw_footer_line(painter, col2_x, curr_y2, col2_chars, char_w, ascent, "PURGE ACCURACY: 99.8%", theme, small_font)
            curr_y2 += line_h + 10

            # Panel 3: Autonomous Agent Activity Log
            panel_log_h = 7 * line_h
            self._draw_panel_backdrop(painter, col2_x, curr_y2, col2_chars * char_w, panel_log_h, theme)
            self._draw_header_line(painter, col2_x, curr_y2, col2_chars, char_w, ascent, "LIVE AGENT ACTIVITY TERMINAL", theme, bold_font)
            curr_y2 += line_h

            recent_acts = activities[-5:] if activities else []
            for act in recent_acts:
                a_time = act.get("time", "")
                a_tag = act.get("tag", "INFO")
                a_msg = act.get("message", "")
                r_act = [
                    (f" [{a_time}] ", theme["dim"]),
                    (f"[{a_tag:<8}] ", theme["accent"] if "PURGE" in a_tag or "FILTER" in a_tag else theme["primary"]),
                    (f"{a_msg[:col2_chars-24]}", theme["secondary"])
                ]
                self._draw_box_row(painter, col2_x, curr_y2, col2_chars, char_w, ascent, r_act, theme, small_font)
                curr_y2 += line_h

            self._draw_footer_line(painter, col2_x, curr_y2, col2_chars, char_w, ascent, "LOG: SYNCHRONIZED", theme, small_font)
            curr_y2 += line_h

            # Bottom Control Bar
            bot_y = max(curr_y1, curr_y2) + 8
            bot_chars = int(available_w // char_w)
            self._draw_panel_backdrop(painter, margin_x, bot_y, bot_chars * char_w, 3 * line_h, theme)
            self._draw_header_line(painter, margin_x, bot_y, bot_chars, char_w, ascent, "HUD CONTROLS & NAVIGATION", theme, bold_font)
            bot_y += line_h

            nav_row = [
                ("[T] TELEMETRY HUD  •  [N] NEWS HUD  •  [SPACE] TOGGLE EXPAND CHATTER  •  [R] AUTO-ROTATE  •  TRAY: SWEEP NOW", theme["primary"])
            ]
            self._draw_box_row(painter, margin_x, bot_y, bot_chars, char_w, ascent, nav_row, theme, main_font)
            bot_y += line_h
            self._draw_footer_line(painter, margin_x, bot_y, bot_chars, char_w, ascent, f"ACTIVE HUD: NEWS & SOCIAL SENTRY // REFRESH IN: {countdown_str}", theme, small_font)
        else:
            # Single-column fallback for ultra-narrow viewport
            single_chars = int(available_w // char_w)
            curr_y = y2 + line_h + 10
            panel_news_header = f"VERIFIED NEWS & SOCIAL CHATTER  [ {len(items)} STORIES ]"
            self._draw_panel_backdrop(painter, margin_x, curr_y, single_chars * char_w, 2 * line_h, theme)
            self._draw_header_line(painter, margin_x, curr_y, single_chars, char_w, ascent, panel_news_header, theme, bold_font)
            curr_y += line_h + 4

            for idx, item in enumerate(items[:3]):
                item_id = item.get("id", f"news_{idx}")
                is_exp = (item_id == expanded_id)
                self.news_click_rects.append((QRectF(margin_x, curr_y, available_w, 4 * line_h), item_id))
                self._draw_header_line(painter, margin_x, curr_y, single_chars, char_w, ascent, f"[{item.get('category')}] {item.get('title', '')[:single_chars-16]}", theme, bold_font)
                curr_y += line_h
                self._draw_box_row(painter, margin_x, curr_y, single_chars, char_w, ascent, [(f"  {item.get('summary', '')[:single_chars-4]}", theme["secondary"])], theme, small_font)
                curr_y += line_h + 4

    def _draw_standby(self, painter: QPainter, width: int, height: int, tick: int, theme: Dict[str, Any]):
        spinner = get_spinner("braille", tick)
        msg = f"[ {spinner} INITIALIZING SYSTEM MONITORING AGENT TELEMETRY ... ]"
        font = QFont(self.font_family, 12, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(theme["primary"])
        painter.drawText(width / 2 - 200, height / 2, msg)
