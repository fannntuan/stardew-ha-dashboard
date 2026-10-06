#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成星露谷风格 HA 主题（春/夏/秋/冬/夜 五套）+ 像素字体与素材注入脚本。"""
import os

OUT = "/vol2/@appdata/trim.hermes/workspace/stardew_www"
os.makedirs(OUT + "/themes", exist_ok=True)

FONT_STACK = "'Stardew Pixel', 'Fusion Pixel', 'Zpix', ui-monospace, 'Noto Sans SC', monospace"

# 以"秋"为基础模板，其它季节覆盖颜色
BASE = dict(
    bg="#dcbf8c", bg2="#e8d3ac", card="#f9ecd0", card_border="#7a4a20", wood="#8b5a2b",
    wood_dark="#5d3a17", text="#4a2f1a", text2="#7d5c38", text_on_dark="#fdf3dd",
    gold="#f2b53a", green="#6fae4a", green_dark="#4e8033", red="#c0392b", blue="#4a7ab5",
    shadow="rgba(93,58,23,.38)", disabled="#a8916f", divider="rgba(122,74,32,.30)",
    sidebar="#7a4a20", sidebar_text="#f7e7c6", sidebar_sel="rgba(242,181,58,.22)",
    input_bg="#fdf3dd", track="#e6d5ae",
)

PALETTES = {
    # 春：嫩绿 + 木框
    "stardew_spring": dict(BASE, bg="#cfe0a8", bg2="#dcebca", card="#fbf4dd",
                           wood="#8b5a2b", sidebar="#6f5424", sidebar_text="#f2ecc9",
                           green="#6fae4a", green_dark="#4e8033", gold="#f2b53a",
                           track="#e2e7c6", divider="rgba(96,110,50,.30)"),
    # 夏：浓绿 + 亮金
    "stardew_summer": dict(BASE, bg="#bcd97e", bg2="#cde595", card="#fdf6dc",
                           wood="#96601f", sidebar="#7f5a1e", sidebar_text="#fdf1c7",
                           green="#5fa832", green_dark="#427a20", gold="#f4b942",
                           track="#e4e6c0", divider="rgba(90,110,40,.30)"),
    # 秋：琥珀（当前季节，做默认）
    "stardew_fall": dict(BASE, bg="#d9a86a", bg2="#e6c089", card="#fbeed6",
                         card_border="#6f3f16", wood="#9a5a22", wood_dark="#5f3410",
                         gold="#e8a33d", green="#7d9c46", green_dark="#5c7a2e",
                         sidebar="#7e4517", sidebar_text="#ffeed0", shadow="rgba(95,52,16,.40)",
                         track="#e6d3ac"),
    # 冬：雪蓝 + 冷木
    "stardew_winter": dict(BASE, bg="#ccdce8", bg2="#dde9f2", card="#f6f8fa",
                           card_border="#5f6e7c", wood="#5b4b3a", wood_dark="#3b3128",
                           text="#2f3a44", text2="#5b6b78", disabled="#9aa8b3",
                           gold="#e5b53c", green="#5f9e78", green_dark="#3f7458",
                           blue="#4a7ab5", sidebar="#3f4a58", sidebar_text="#eaf2f8",
                           sidebar_sel="rgba(229,181,60,.22)", shadow="rgba(47,58,68,.35)",
                           input_bg="#ffffff", track="#dbe4ec", divider="rgba(95,110,124,.30)"),
    # 夜：星空 + 暗木
    "stardew_night": dict(BASE, bg="#2a2545", bg2="#332c52", card="#3f2f22",
                          card_border="#b5834f", wood="#4a2d14", wood_dark="#2b1a0c",
                          text="#f6e6c6", text2="#cdb28a", gold="#f7c744", green="#8fbf62",
                          green_dark="#5d8a3a", red="#d9544d", blue="#7fa6d9",
                          shadow="rgba(0,0,0,.55)", disabled="#8a7a63",
                          divider="rgba(181,131,79,.30)", sidebar="#2b1a0c", sidebar_text="#f2dfb6",
                          sidebar_sel="rgba(247,199,68,.20)", input_bg="#4b3826", track="#5b4630"),
}

TEMPLATE = {
    "primary-color": "{wood}",
    "accent-color": "{gold}",
    "primary-background-color": "{bg}",
    "secondary-background-color": "{bg2}",
    "card-background-color": "{card}",
    "ha-card-background": "{card}",
    "primary-text-color": "{text}",
    "secondary-text-color": "{text2}",
    "text-primary-color": "{text_on_dark}",
    "text-light-primary-color": "{text_on_dark}",
    "disabled-text-color": "{disabled}",
    "divider-color": "{divider}",
    "error-color": "{red}",
    "warning-color": "{gold}",
    "success-color": "{green}",
    "info-color": "{blue}",
    "ha-color-primary-05": "{card}", "ha-color-primary-10": "{card}",
    "ha-color-primary-20": "{track}", "ha-color-primary-30": "{wood}",
    "ha-color-primary-40": "{wood}", "ha-color-primary-50": "{wood}",
    "ha-color-primary-60": "{wood_dark}", "ha-color-primary-70": "{wood_dark}",
    "ha-color-primary-80": "{wood_dark}", "ha-color-primary-90": "{text}",
    "ha-color-primary-95": "{text}",
    "ha-card-border-radius": "2px",
    "ha-card-border-width": "3px",
    "ha-card-border-color": "{card_border}",
    "ha-card-box-shadow": "3px 3px 0 0 {shadow}",
    "ha-card-header-color": "{text}",
    "ha-card-header-font-size": "24px",
    "ha-border-radius-sm": "2px", "ha-border-radius-md": "2px",
    "ha-border-radius-lg": "3px", "ha-border-radius-pill": "3px",
    "ha-border-radius-circle": "50%", "ha-border-width-md": "2px",
    "ha-font-family-body": FONT_STACK,
    "ha-font-family-heading": FONT_STACK,
    "ha-font-family-code": FONT_STACK,
    "paper-font-common-base_-_font-family": FONT_STACK,
    "paper-font-common-code_-_font-family": FONT_STACK,
    "ha-font-size-xs": "12px", "ha-font-size-s": "12px", "ha-font-size-m": "12px",
    "ha-font-size-l": "12px", "ha-font-size-xl": "24px", "ha-font-size-2xl": "24px",
    "ha-font-size-3xl": "36px",
    "ha-font-weight-normal": "500", "ha-font-weight-medium": "700", "ha-font-weight-bold": "700",
    "ha-line-height-normal": "1.5", "ha-line-height-condensed": "1.35",
    "app-header-background-color": "{wood}",
    "app-header-text-color": "{text_on_dark}",
    "sidebar-background-color": "{sidebar}",
    "sidebar-text-color": "{sidebar_text}",
    "sidebar-icon-color": "{track}",
    "sidebar-selected-background-color": "{sidebar_sel}",
    "sidebar-selected-icon-color": "{gold}",
    "sidebar-selected-text-color": "{text_on_dark}",
    "ha-sidebar-background-color": "{sidebar}",
    "ha-sidebar-text-color": "{sidebar_text}",
    "ha-sidebar-icon-color": "{track}",
    "ha-sidebar-selected-background-color": "{sidebar_sel}",
    "ha-sidebar-selected-icon-color": "{gold}",
    "ha-sidebar-selected-text-color": "{text_on_dark}",
    "ha-sidebar-border-color": "{card_border}",
    "state-icon-color": "{wood}",
    "state-icon-active-color": "{gold}",
    "state-active-color": "{gold}",
    "state-light-active-color": "{gold}",
    "state-switch-active-color": "{green}",
    "state-climate-heat-color": "{red}",
    "state-climate-cool-color": "{blue}",
    "state-climate-fan_only-color": "{green}",
    "state-cover-open-color": "{gold}",
    "state-media_player-active-color": "{blue}",
    "state-vacuum-active-color": "{green}",
    "state-binary_sensor-active-color": "{green}",
    "state-sensor-battery-high-color": "{green}",
    "state-sensor-battery-low-color": "{red}",
    "slider-color": "{wood}", "slider-secondary-color": "{track}", "slider-bar-color": "{wood}",
    "switch-checked-color": "{green}", "switch-checked-track-color": "{green_dark}",
    "switch-unchecked-color": "{track}", "switch-unchecked-track-color": "{divider}",
    "toggle-button-background-color": "{card}", "toggle-button-text-color": "{text}",
    "toggle-button-icon-color": "{text2}",
    "input-fill-color": "{input_bg}", "input-ink-color": "{text}",
    "input-label-ink-color": "{text2}", "input-idle-line-color": "{card_border}",
    "input-dropdown-icon-color": "{text2}", "input-disabled-fill-color": "{bg2}",
    "input-disabled-ink-color": "{disabled}", "input-disabled-line-color": "{divider}",
    "input-disabled-label-ink-color": "{disabled}",
    "mdc-text-field-fill-color": "{input_bg}", "mdc-text-field-ink-color": "{text}",
    "mdc-select-fill-color": "{input_bg}", "mdc-select-ink-color": "{text}",
    "mdc-checkbox-unchecked-color": "{text2}",
    "mdc-theme-primary": "{wood}", "mdc-theme-secondary": "{gold}",
    "mdc-theme-background": "{bg}", "mdc-theme-surface": "{card}",
    "mdc-theme-on-primary": "{text_on_dark}", "mdc-theme-on-surface": "{text}",
    "paper-item-icon-color": "{wood}", "paper-item-icon-active-color": "{gold}",
    "paper-item-icon_-_color": "{wood}", "paper-slider-knob-color": "{gold}",
    "paper-slider-active-color": "{wood}", "paper-slider-container-color": "{track}",
    "label-badge-background-color": "{card}", "label-badge-text-color": "{text}",
    "label-badge-red": "{red}", "label-badge-green": "{green}", "label-badge-blue": "{blue}",
    "label-badge-yellow": "{gold}", "label-badge-grey": "{track}",
    "table-row-background-color": "{card}", "table-row-alternative-background-color": "{bg2}",
    "table-header-background-color": "{bg2}", "data-table-background-color": "{card}",
    "markdown-code-background-color": "{bg2}", "code-editor-background-color": "{bg2}",
    "clear-background-color": "{card}",
    "ha-dialog-surface-background": "{card}", "ha-dialog-sidebar-background": "{bg2}",
    "ha-dialog-header-title-color": "{text}", "ha-dialog-content-text-color": "{text}",
    "ha-dialog-scrim-background": "rgba(40,24,8,.55)",
    "ha-dialog-border-radius": "3px", "ha-dialog-border-color": "{card_border}",
    "ha-dialog-border-width": "3px", "ha-dialog-box-shadow": "4px 4px 0 0 {shadow}",
    "ha-dialog-surface-box-shadow": "4px 4px 0 0 {shadow}",
    "ha-tooltip-background-color": "{text}", "ha-tooltip-text-color": "{card}",
    "tooltip-background-color": "{text}", "tooltip-text-color": "{card}",
    "ha-assist-chip-filled-container-color": "{bg2}",
    "ha-assist-chip-label-text-color": "{text}",
    "badge-color": "{wood}", "ha-tab-active-text-color": "{text}",
    "ha-tab-inactive-text-color": "{text2}", "ha-tab-active-indicator-color": "{gold}",
}


def render(name: str, pal: dict) -> str:
    lines = ["# Stardew Valley 风格 HA 主题（自动生成，勿手改）", f"{name}:"]
    for k, v in TEMPLATE.items():
        lines.append(f'  {k}: "{v.format(**pal) if "{" in v else v}"')
    return "\n".join(lines) + "\n"


for name, pal in PALETTES.items():
    p = f"{OUT}/themes/{name}.yaml"
    open(p, "w", encoding="utf-8").write(render(name, pal))
    print("生成:", os.path.basename(p), os.path.getsize(p), "字节")
