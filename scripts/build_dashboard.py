#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重建「控制面板」：7 个视图 + 一个"点开即看"的主页。
⚠️ 主页(main) 用户会自己在界面上改：默认 --apply 只写其它 6 个视图，不动主页；要连主页一起写必须加 --all。
主页 = 天气 / 温湿度 / 空调 / 灯光 / 家电状态 / 安防 / 影音窗帘
其它视图 = 客厅 · 卧室书房 · 厨房卫浴 · 家电 · 3D打印 · 安防环境
运行: python3 build_dashboard.py [--apply]
"""
import json
import sys

import ha_api as H

URL_PATH = "home-control"


def tile(entity, name=None, icon=None, color=None, cspan=None):
    c = {"type": "tile", "entity": entity}
    if name:
        c["name"] = name
    if icon:
        c["icon"] = icon
    if color:
        c["color"] = color
    if cspan:
        c["column_span"] = cspan
    return c


HOME_BANNER = "<center>🎆🎆🎆🎆回家咯🎆🎆🎆🎆</center>"
VIEW_NAV = [("main", "主页"), ("living", "客厅"), ("bedroom", "卧室"), ("utility", "厨卫"),
            ("appliance", "家电"), ("printer", "3D打印"), ("security", "安防")]


def nav_section(cur, wide=True):
    # 全屏 kiosk 模式后 HA 自带视图标签会被藏掉，这里给每个视图顶部放一条自绘导航。
    # ⚠️ 导航条已被用户手动改过：所有视图都是"整行铺满"，且底下多了「回家咯」横幅 —— 这里照抄线上，
    #    免得下次重建把它抹掉（主页那条是 columns:"full"，其它视图是 36）。
    parts = []
    for path, label in VIEW_NAV:
        if path == cur:
            parts.append("<b>%s</b>" % label)
        else:
            parts.append("<a href='/home-control/%s'>%s</a>" % (path, label))
    content = "<img src='/local/stardew/img/hud_stardrop.png'> " + "　".join(parts)
    content += (" \n\n" if cur in ("main", "living") else "\n\n") + HOME_BANNER
    md = {"type": "markdown", "content": content,
          "grid_options": {"columns": ("full" if cur == "main" else 36), "rows": "auto"}}
    sec = {"type": "grid", "cards": [md], "column_span": 3}
    return sec


def grid(cards, columns=4, square=False):
    """网格卡片。若里面全是 tile，按"名字最长几个字"自动定列数：
    ≤2 字用 3 列，否则用 2 列 —— 避免名字被截断成"客厅…"（手机/平板都受益）。"""
    if cards and all(isinstance(c, dict) and c.get("type") == "tile" for c in cards):
        mx = max(len(c.get("name") or "") for c in cards)
        columns = 3 if mx <= 2 else 2
    return {"type": "grid", "columns": columns, "square": square, "cards": cards}


DASH = {
    "title": "控制面板",
    "views": [
        # ============================ 主页 ============================
        {
            "title": "主页", "path": "main", "icon": "mdi:home-heart", "type": "sections",
            "header": {"card": {"type": "markdown", "content": "# 欢迎回家", "text_only": True}},
            "sections": [
                # 谷里今日（大时钟 + 时间/季节/天气 + 油价 + 运势 + 家里关键状态）
                {"type": "grid", "column_span": 3, "cards": [
                    {"type": "markdown", "content": "{% set m = now().month %}{% set se = 'hud_season_spring' if m in [3,4,5] else ('hud_season_summer' if m in [6,7,8] else ('hud_season_fall' if m in [9,10,11] else 'hud_season_winter')) %}{% set w = states('weather.forecast_jia') %}{% set ic = {'sunny':'hud_sun','clear-night':'hud_sun','partlycloudy':'hud_sun','cloudy':'hud_rain','rainy':'hud_rain','pouring':'hud_storm','lightning':'hud_storm','lightning-rainy':'hud_storm','snowy':'hud_snow','snowy-rainy':'hud_snow','fog':'hud_rain','hail':'hud_storm'} %}{% set zh = {'sunny':'晴天','clear-night':'晴夜','partlycloudy':'多云','cloudy':'阴天','rainy':'小雨','pouring':'大雨','lightning':'雷雨','lightning-rainy':'雷阵雨','snowy':'下雪','snowy-rainy':'雨夹雪','fog':'有雾','hail':'冰雹','windy':'大风','windy-variant':'大风','exceptional':'异常天气'} %}{% set luck = ((as_timestamp(now()) // 86400) | int) % 7 - 3 %}{% set lv = '非常幸运' if luck >= 3 else ('有点幸运' if luck >= 1 else ('平平常常' if luck == 0 else ('有点倒霉' if luck >= -2 else '非常倒霉'))) %}{% set sezh = {'hud_season_spring':'春','hud_season_summer':'夏','hud_season_fall':'秋','hud_season_winter':'冬'}[se] %}{% set wd = ['周一','周二','周三','周四','周五','周六','周日'][now().weekday()] %}{% set vsz = {'charging':'充电中','cleaning':'清扫中','docked':'已回充','idle':'待机','returning':'回程中','paused':'已暂停','error':'故障'} %}{% set psz = {'finish':'已完成','printing':'打印中','idle':'空闲','prepare':'准备中','failed':'失败','offline':'离线'} %}\n# {{ now().strftime('%H:%M') }}\n<img src='/local/stardew/img/hud_time.png'> {{ now().strftime('%m-%d') }} {{ wd }}　<img src='/local/stardew/img/{{ se }}.png?v=2'> {{ sezh }}季　<img src='/local/stardew/img/{{ ic.get(w, 'hud_sun') }}.png'> {{ zh.get(w, w) }}<br><img src='/local/stardew/img/hud_gold.png'> 95# <b>{{ states('sensor.he_bei_you_jie_95') }}</b>元　<img src='/local/stardew/img/hud_stardrop.png'> {{ lv }} {{ '★' * (luck + 3) }}<br><img src='/local/stardew/img/hud_health.png'> 门锁 {{ states('sensor.fang_dao_men_zhuang_tai') }} {{ states('sensor.loock_r2_559c_battery_level') | round | int }}% · 扫地机 {{ vsz.get(states('sensor.p20_ultra_plus_status'), states('sensor.p20_ultra_plus_status')) }} · 打印机 {{ psz.get(states('sensor.a1mini_${PRINTER_SERIAL}_print_status'), states('sensor.a1mini_${PRINTER_SERIAL}_print_status')) }}"},
                    grid([
                        tile("sensor.xiaomi_rrbr00_c147_temperature", "客厅", "mdi:thermometer", color="orange"),
                        tile("sensor.xiaomi_rrbr00_c147_relative_humidity", "客厅湿度", "mdi:water-percent", color="blue"),
                        tile("sensor.xiaomi_h09h00_90b0_temperature", "主卧", "mdi:thermometer", color="orange"),
                        tile("sensor.xiaomi_h09h00_90b0_relative_humidity", "主卧湿度", "mdi:water-percent", color="blue"),
                        tile("sensor.xiaomi_h09h00_8af7_temperature", "书房", "mdi:thermometer", color="orange"),
                        tile("sensor.xiaomi_h09h00_8af7_relative_humidity", "书房湿度", "mdi:water-percent", color="blue"),
                    ], columns=2),
                    grid([
                        tile("sensor.he_bei_you_jie_92", "92#汽油", "mdi:gas-station", color="orange"),
                        tile("sensor.he_bei_you_jie_95", "95#汽油", "mdi:gas-station", color="orange"),
                        tile("sensor.he_bei_you_jie_98", "98#汽油", "mdi:gas-station", color="orange"),
                        tile("sensor.he_bei_chai_you_0", "0#柴油", "mdi:gas-station", color="grey"),
                    ], columns=2),
                ]},
                # 天气（一周预报）
                {"type": "grid", "column_span": 2, "cards": [
                    {"type": "heading", "heading": "天气", "icon": "mdi:weather-partly-cloudy"},
                                        {"type": "weather-forecast", "entity": "weather.forecast_jia", "name": "家里",
                     "show_current": True, "show_forecast": True, "forecast_type": "daily",
                     "secondary_info_attribute": "humidity", "column_span": 2},
                    {"type": "clock", "clock_style": "analog", "clock_size": "large",
                     "show_seconds": False, "no_background": False, "face_style": "markers",
                     "grid_options": {"columns": 12, "rows": 4}, "border": False, "ticks": "hour"},
                ]},
                # 灯光（按房间分排，3 列够放名字）
                {"type": "grid", "cards": [
                    {"type": "heading", "heading": "客厅 · 餐厅 灯光", "icon": "mdi:lightbulb-group"},
                    grid([
                        tile("switch.lemesh_sw4f14_a9c4_fourth_switch_service", "客厅主灯", "mdi:ceiling-light", color="amber"),
                        tile("switch.lemesh_sw4f14_a9c4_first_switch_service", "客厅灯带", "mdi:led-strip-variant", color="amber"),
                        tile("switch.lemesh_sw4f14_a9c4_second_switch_service", "客厅壁灯", "mdi:wall-sconce-flat", color="amber"),
                        tile("switch.lemesh_sw4f14_a9c4_third_switch_service", "客厅筒灯", "mdi:light-recessed", color="amber"),
                        tile("switch.lemesh_sw4f14_a9c0_fourth_switch_service", "餐厅主灯", "mdi:ceiling-light", color="amber"),
                        tile("switch.lemesh_sw4f14_a9c0_second_switch_service", "餐厅筒灯", "mdi:light-recessed", color="amber"),
                    ], columns=3)]},
                {"type": "grid", "cards": [
                    {"type": "heading", "heading": "卧室 · 厨卫 · 其它灯光", "icon": "mdi:lightbulb-group-outline"},
                    grid([
                        tile("switch.lemesh_sw4f14_b27f_third_switch_service", "主卧主灯", "mdi:ceiling-light", color="amber"),
                        tile("switch.lemesh_sw4f14_b27f_second_switch_service", "主卧筒灯", "mdi:light-recessed", color="amber"),
                        tile("switch.lemesh_sw4f14_b27f_first_switch_service", "主卫灯", "mdi:toilet", color="amber"),
                        tile("switch.lemesh_sw2f12_985b_left_switch_service", "玄关灯", "mdi:door-open", color="amber"),
                        tile("switch.lemesh_sw2f12_985b_right_switch_service", "客卫灯", "mdi:toilet", color="amber"),
                        tile("switch.lemesh_sw4f14_a9c0_third_switch_service", "厨房灯", "mdi:stove", color="amber"),
                        tile("switch.lemesh_sw3f13_bae4_right_switch_service", "阳台灯", "mdi:balcony", color="amber"),
                        tile("switch.lemesh_sw1f11_83fe_switch", "书房主灯", "mdi:ceiling-light", color="amber"),
                        tile("switch.lemesh_sw1f11_840d_switch", "次卧灯", "mdi:ceiling-light", color="amber"),
                    ], columns=3)]},
                {"type": "grid", "cards": [
                    {"type": "heading", "heading": "其它灯", "icon": "mdi:lamp"},
                    grid([
                        tile("switch.lemesh_sw1f11_d5e9_switch", "玄关门口", "mdi:door", color="amber"),
                        tile("switch.lemesh_sw4f14_b1f8_third_switch_service", "入户灯带", "mdi:led-strip-variant", color="amber"),
                        tile("switch.lemesh_sw4f14_b1f8_fourth_switch_service", "入户筒灯", "mdi:light-recessed", color="amber"),
                        tile("switch.lemesh_sw4f14_b27f_fourth_switch_service", "门灯", "mdi:door", color="amber"),
                        tile("switch.hzsj_wy0a01_ef07_night_light_switch", "夜灯", "mdi:floor-lamp", color="amber"),
                        tile("light.yeelink_lamp27_a7f4_light", "台灯", "mdi:lamp", color="amber"),
                        tile("light.yeelink_lamp22_9d1f_light", "电脑灯", "mdi:desk-lamp", color="amber"),
                    ], columns=3)]},
                # 空调（紧凑版，点开才展开）
                {"type": "grid", "cards": [
                    {"type": "heading", "heading": "空调", "icon": "mdi:air-conditioner"},
                    grid([
                        tile("climate.xiaomi_rrbr00_c147_air_conditioner", "客厅空调", "mdi:air-conditioner", color="blue"),
                        tile("climate.xiaomi_h09h00_90b0_air_conditioner", "主卧空调", "mdi:air-conditioner", color="blue"),
                        tile("climate.xiaomi_h09h00_8af7_air_conditioner", "书房空调", "mdi:air-conditioner", color="blue"),
                    ], columns=3)]},
                # 家电关键状态
                {"type": "grid", "cards": [
                    {"type": "heading", "heading": "家电状态", "icon": "mdi:washing-machine"},
                    grid([
                        tile("sensor.mei_de_ke_ai_duo_yun_xing_zhuang_tai", "洗衣机", "mdi:washing-machine", color="teal"),
                        tile("sensor.mei_de_ke_ai_duo_sheng_yu_shi_jian", "洗完还需", "mdi:timer-sand"),
                        tile("sensor.p20_ultra_plus_status", "扫地机", "mdi:robot-vacuum", color="teal"),
                        tile("sensor.p20_ultra_plus_battery", "电量", "mdi:battery"),
                        tile("sensor.a1mini_${PRINTER_SERIAL}_print_status", "打印机", "mdi:printer-3d", color="teal"),
                        tile("sensor.a1mini_${PRINTER_SERIAL}_print_progress", "打印进度", "mdi:percent"),
                        tile("sensor.dian_re_shui_qi_dang_qian_wen_du", "热水器", "mdi:water-boiler", color="red"),
                        tile("sensor.bing_xiang_leng_cang_shi_xian_shi_wen_du_degc", "冰箱冷藏", "mdi:fridge-outline", color="blue"),
                        tile("sensor.bing_xiang_leng_dong_shi_xian_shi_wen_du_degc", "冰箱冷冻", "mdi:snowflake", color="blue"),
                        tile("sensor.jing_shui_ji_chu_shui_tds", "净水 TDS", "mdi:water-check", color="blue"),
                        tile("sensor.jing_shui_ji_rosheng_yu_bai_fen_bi", "RO 剩余", "mdi:filter"),
                        tile("binary_sensor.a1mini_${PRINTER_SERIAL}_hms_errors", "报警", "mdi:alert-circle"),
                    ], columns=3)]},
                # 安防
                {"type": "grid", "cards": [
                    {"type": "heading", "heading": "安防", "icon": "mdi:shield-home"},
                    grid([
                        tile("sensor.fang_dao_men_zhuang_tai", "防盗门", "mdi:door-closed-lock", color="red"),
                        tile("sensor.loock_r2_559c_battery_level", "门锁电量", "mdi:battery-lock"),
                        tile("switch.chuangmi_ipc019_15e7_switch_status", "摄像头", "mdi:cctv", color="grey"),
                        tile("sensor.ke_wei_you_ren", "客卫有人", "mdi:motion-sensor", color="purple"),
                        tile("sensor.zhu_wei_you_ren", "主卫有人", "mdi:motion-sensor", color="purple"),
                        tile("switch.giot_v6oodm_30f9_switch", "开机卡", "mdi:card-account-details"),
                    ], columns=3)]},
                # 窗帘 + 影音
                {"type": "grid", "cards": [
                    {"type": "heading", "heading": "窗帘 · 影音", "icon": "mdi:curtains"},
                    grid([
                        tile("cover.dooya_dt98_ab72_curtain", "窗帘", "mdi:curtains"),
                        tile("cover.dooya_dt98_5349_curtain", "纱帘", "mdi:curtains"),
                        tile("cover.dooya_dt98_6058_curtain", "布帘", "mdi:curtains"),
                        tile("media_player.xiaomi_oh2p_bf82_play_control", "客厅音箱", "mdi:speaker"),
                        tile("switch.giot_v6oodm_ae30_switch", "磁吸墙冲", "mdi:cellphone-charging"),
                    ], columns=3)]},
                # 季节皮肤：一键换整套配色
                {"type": "grid", "cards": [
                    {"type": "heading", "heading": "季节皮肤（点一下整套换色）", "icon": "mdi:palette-swatch"},
                    grid([
                        {"type": "button", "name": "春", "icon": "mdi:flower", "show_state": False,
                         "tap_action": {"action": "perform-action", "perform_action": "frontend.set_theme",
                                       "data": {"name": "stardew_spring"}}},
                        {"type": "button", "name": "夏", "icon": "mdi:white-balance-sunny", "show_state": False,
                         "tap_action": {"action": "perform-action", "perform_action": "frontend.set_theme",
                                       "data": {"name": "stardew_summer"}}},
                        {"type": "button", "name": "秋", "icon": "mdi:leaf", "show_state": False,
                         "tap_action": {"action": "perform-action", "perform_action": "frontend.set_theme",
                                       "data": {"name": "stardew_fall"}}},
                        {"type": "button", "name": "冬", "icon": "mdi:snowflake", "show_state": False,
                         "tap_action": {"action": "perform-action", "perform_action": "frontend.set_theme",
                                       "data": {"name": "stardew_winter"}}},
                        {"type": "button", "name": "夜", "icon": "mdi:weather-night", "show_state": False,
                         "tap_action": {"action": "perform-action", "perform_action": "frontend.set_theme",
                                       "data": {"name": "stardew_night"}}},
                    ], columns=3)]},
            ],
        },
        # ============================ 客厅 ============================
        {
            "title": "客厅", "path": "living", "icon": "mdi:sofa", "type": "sections",
            "sections": [
                {"type": "grid", "cards": [
                    {"type": "thermostat", "entity": "climate.xiaomi_rrbr00_c147_air_conditioner"},
                    grid([tile("switch.xiaomi_rrbr00_c147_vertical_swing", "上下摆风", "mdi:swap-vertical"),
                          tile("switch.xiaomi_rrbr00_c147_horizontal_swing", "左右扫风", "mdi:swap-horizontal"),
                          tile("switch.xiaomi_rrbr00_c147_eco", "ECO", "mdi:leaf"),
                          tile("switch.xiaomi_rrbr00_c147_sleep_mode", "睡眠", "mdi:sleep")], columns=3),
                ]},
                {"type": "grid", "cards": [grid([
                    tile("switch.lemesh_sw4f14_a9c4_fourth_switch_service", "客厅主灯", "mdi:ceiling-light", color="amber"),
                    tile("switch.lemesh_sw4f14_a9c4_first_switch_service", "客厅灯带", "mdi:led-strip-variant", color="amber"),
                    tile("switch.lemesh_sw4f14_a9c4_second_switch_service", "客厅壁灯", "mdi:wall-sconce-flat", color="amber"),
                    tile("switch.lemesh_sw4f14_a9c4_third_switch_service", "客厅筒灯", "mdi:light-recessed", color="amber"),
                ], columns=3)]},
                {"type": "grid", "cards": [grid([
                    tile("switch.hzsj_wy0a01_ef07_night_light_switch", "夜灯", "mdi:floor-lamp", color="amber"),
                    tile("switch.giot_v6oodm_ae30_switch", "磁吸墙冲", "mdi:cellphone-charging"),
                ], columns=3)]},
                {"type": "grid", "cards": [grid([
                    tile("cover.dooya_dt98_ab72_curtain", "窗帘", "mdi:curtains"),
                    tile("cover.dooya_dt98_5349_curtain", "纱帘", "mdi:curtains"),
                    tile("cover.dooya_dt98_6058_curtain", "布帘", "mdi:curtains"),
                ], columns=3)]},
                {"type": "grid", "cards": [grid([
                    tile("media_player.xiaomi_oh2p_bf82_play_control", "客厅音箱", "mdi:speaker"),
                    tile("sensor.xiaomi_rrbr00_c147_temperature", "客厅温度", "mdi:thermometer", color="orange"),
                    tile("sensor.xiaomi_rrbr00_c147_relative_humidity", "客厅湿度", "mdi:water-percent", color="blue"),
                ], columns=2)]},
            ],
        },
        # ======================== 卧室 · 书房 ========================
        {
            "title": "卧室·书房", "path": "bedroom", "icon": "mdi:bed", "type": "sections",
            "sections": [
                {"type": "grid", "cards": [
                    {"type": "thermostat", "entity": "climate.xiaomi_h09h00_90b0_air_conditioner"},
                    grid([tile("switch.xiaomi_h09h00_90b0_vertical_swing", "上下摆风", "mdi:swap-vertical"),
                          tile("switch.xiaomi_h09h00_90b0_unstraight_blowing", "防直吹", "mdi:weather-windy"),
                          tile("switch.xiaomi_h09h00_90b0_eco", "ECO", "mdi:leaf"),
                          tile("switch.xiaomi_h09h00_90b0_sleep_mode", "睡眠", "mdi:sleep")], columns=3),
                ]},
                {"type": "grid", "cards": [grid([
                    tile("switch.lemesh_sw4f14_b27f_third_switch_service", "主卧主灯", "mdi:ceiling-light", color="amber"),
                    tile("switch.lemesh_sw4f14_b27f_second_switch_service", "主卧筒灯", "mdi:light-recessed", color="amber"),
                    tile("switch.lemesh_sw4f14_b27f_first_switch_service", "主卫灯", "mdi:toilet", color="amber"),
                    tile("switch.lemesh_sw4f14_b27f_fourth_switch_service", "门灯", "mdi:door", color="amber"),
                ], columns=3)]},
                {"type": "grid", "cards": [grid([
                    tile("light.yeelink_lamp27_a7f4_light", "台灯", "mdi:lamp", color="amber"),
                    tile("light.yeelink_lamp22_9d1f_light", "电脑灯", "mdi:desk-lamp", color="amber"),
                    tile("switch.lemesh_sw1f11_83fe_switch", "书房主灯", "mdi:ceiling-light", color="amber"),
                    tile("switch.lemesh_sw1f11_840d_switch", "次卧灯", "mdi:ceiling-light", color="amber"),
                ], columns=3)]},
                {"type": "grid", "cards": [grid([
                    tile("sensor.xiaomi_h09h00_90b0_temperature", "主卧温度", "mdi:thermometer", color="orange"),
                    tile("sensor.xiaomi_h09h00_90b0_relative_humidity", "主卧湿度", "mdi:water-percent", color="blue"),
                    tile("sensor.zhu_wei_you_ren", "主卫有人", "mdi:motion-sensor", color="purple"),
                    tile("sensor.linp_hb01_e81d_illumination", "主卫光照", "mdi:brightness-5"),
                ], columns=2)]},
                {"type": "grid", "cards": [
                    {"type": "thermostat", "entity": "climate.xiaomi_h09h00_8af7_air_conditioner"},
                    grid([tile("sensor.xiaomi_h09h00_8af7_temperature", "书房温度", "mdi:thermometer", color="orange"),
                          tile("sensor.xiaomi_h09h00_8af7_relative_humidity", "书房湿度", "mdi:water-percent", color="blue")], columns=2),
                ]},
                {"type": "grid", "cards": [grid([
                    tile("media_player.xiaomi_oh2p_beb9_play_control", "书房音响", "mdi:speaker"),
                    tile("media_player.xiaomi_l06a_a14b_play_control", "小爱音箱", "mdi:speaker-wireless"),
                    tile("media_player.xiaomi_x4b_c1dc_play_control", "主卧家庭屏", "mdi:tablet"),
                ], columns=3)]},
            ],
        },
        # ======================= 厨房 · 卫浴 · 阳台 =======================
        {
            "title": "厨卫·阳台", "path": "utility", "icon": "mdi:silverware-fork-knife",
            "type": "sections",
            "sections": [
                {"type": "grid", "cards": [grid([
                    tile("switch.lemesh_sw4f14_a9c0_third_switch_service", "厨房灯", "mdi:ceiling-light", color="amber"),
                    tile("switch.lemesh_sw4f14_a9c0_fourth_switch_service", "餐厅主灯", "mdi:ceiling-light", color="amber"),
                    tile("switch.lemesh_sw4f14_a9c0_second_switch_service", "餐厅筒灯", "mdi:light-recessed", color="amber"),
                    tile("switch.lemesh_sw4f14_a9c0_first_switch_service", "餐厅灯带", "mdi:led-strip-variant", color="amber"),
                ], columns=3)]},
                {"type": "grid", "cards": [grid([
                    tile("switch.lemesh_sw2f12_985b_right_switch_service", "客卫灯", "mdi:toilet", color="amber"),
                    tile("switch.lemesh_sw2f12_985b_left_switch_service", "玄关灯", "mdi:door-open", color="amber"),
                    tile("switch.lemesh_sw1f11_d5e9_switch", "玄关门口", "mdi:door", color="amber"),
                    tile("switch.lemesh_sw3f13_bae4_right_switch_service", "阳台灯", "mdi:balcony", color="amber"),
                    tile("switch.lemesh_sw4f14_b1f8_third_switch_service", "入户灯带", "mdi:led-strip-variant", color="amber"),
                    tile("switch.lemesh_sw4f14_b1f8_fourth_switch_service", "入户筒灯", "mdi:light-recessed", color="amber"),
                ], columns=3)]},
                {"type": "grid", "cards": [grid([
                    tile("sensor.ke_wei_you_ren", "客卫有人", "mdi:motion-sensor", color="purple"),
                    tile("sensor.linp_hb01_0380_illumination", "客卫光照", "mdi:brightness-5"),
                    tile("sensor.linp_hb01_0380_no_one_duration", "客卫无人时长", "mdi:timer-outline"),
                    tile("sensor.zhu_wei_you_ren", "主卫有人", "mdi:motion-sensor", color="purple"),
                ], columns=2)]},
                {"type": "grid", "cards": [grid([
                    tile("switch.sixwgh_v8icwf_52c7_switch", "3D打印机插座", "mdi:power-socket-cn"),
                    tile("sensor.sixwgh_v8icwf_52c7_electric_power", "打印机功率", "mdi:flash"),
                    tile("switch.giot_v6oodm_30f9_switch", "开机卡", "mdi:card-account-details"),
                    tile("switch.giot_v6oodm_ae30_switch", "磁吸墙冲", "mdi:cellphone-charging"),
                ], columns=2)]},
            ],
        },
        # ============================ 家电 ============================
        {
            "title": "家电", "path": "appliance", "icon": "mdi:home-automation", "type": "sections",
            "sections": [
                # 洗衣机
                {"type": "grid", "cards": [grid([
                    tile("sensor.mei_de_ke_ai_duo_yun_xing_zhuang_tai", "运行状态", "mdi:washing-machine", color="teal"),
                    tile("sensor.mei_de_ke_ai_duo_sheng_yu_shi_jian", "剩余时间", "mdi:timer-sand"),
                    tile("switch.mei_de_ke_ai_duo_qi_ting", "启停", "mdi:play-pause"),
                    tile("binary_sensor.mei_de_ke_ai_duo_xi_yi_ji_men_zhuang_tai", "机门", "mdi:door"),
                    tile("binary_sensor.mei_de_ke_ai_duo_xi_yi_ye_cun_liang", "洗衣液", "mdi:beer"),
                ], columns=3)]},
                # 热水器
                {"type": "grid", "cards": [grid([
                    tile("sensor.dian_re_shui_qi_dang_qian_wen_du", "当前水温", "mdi:water-thermometer", color="red"),
                    tile("sensor.dian_re_shui_qi_mu_biao_wen_du", "目标水温", "mdi:thermometer-check"),
                    tile("sensor.dian_re_shui_qi_bao_wen_jia_re_gong_neng_zhuang_tai", "加热状态", "mdi:fire"),
                    tile("switch.dian_re_shui_qi_kai_guan_ji_zhuang_tai", "开关机", "mdi:power"),
                ], columns=2)]},
                # 冰箱 + 净水
                {"type": "grid", "cards": [grid([
                    tile("sensor.bing_xiang_leng_cang_shi_xian_shi_wen_du_degc", "冷藏", "mdi:fridge-outline", color="blue"),
                    tile("sensor.bing_xiang_leng_dong_shi_xian_shi_wen_du_degc", "冷冻", "mdi:snowflake", color="blue"),
                    tile("sensor.bing_xiang_bian_wen_shi_xian_shi_wen_du", "变温", "mdi:fridge-bottom", color="blue"),
                    tile("sensor.jing_shui_ji_chu_shui_tds", "净水 TDS", "mdi:water-check", color="blue"),
                    tile("sensor.jing_shui_ji_rosheng_yu_bai_fen_bi", "RO 剩余", "mdi:filter"),
                    tile("sensor.jing_shui_ji_chu_lu_sheng_yu_bai_fen_bi", "初滤剩余", "mdi:filter-outline"),
                ], columns=3)]},
                # 扫地机
                {"type": "grid", "cards": [
                    {"type": "tile", "entity": "vacuum.p20_ultra_plus", "name": "扫地机",
                     "icon": "mdi:robot-vacuum", "color": "teal", "features": [
                         {"type": "vacuum-commands", "commands": ["start_pause", "stop", "locate", "return_home"]}]},
                    grid([tile("sensor.p20_ultra_plus_battery", "电量", "mdi:battery"),
                          tile("sensor.p20_ultra_plus_current_room", "当前房间", "mdi:map-marker"),
                          tile("sensor.p20_ultra_plus_cleaning_area", "本次面积", "mdi:texture-box"),
                          tile("sensor.p20_ultra_plus_total_cleaning_count", "总次数", "mdi:counter"),
                          tile("binary_sensor.p20_ultra_plus_water_shortage", "缺水", "mdi:water-off"),
                          tile("binary_sensor.p20_ultra_plus_charging", "充电中", "mdi:battery-charging")], columns=3),
                ]},
                {"type": "grid", "cards": [
                    {"type": "picture-entity", "entity": "image.p20_ultra_plus_map_0", "name": "扫地机地图",
                     "show_name": True, "show_state": False, "camera_view": "auto"},
                ]},
            ],
        },
        # =========================== 3D 打印 ===========================
        {
            "title": "3D打印", "path": "printer", "icon": "mdi:printer-3d", "type": "sections",
            "sections": [
                {"type": "grid", "cards": [
                    {"type": "picture-entity", "entity": "camera.a1mini_${PRINTER_SERIAL}_camera",
                     "name": "打印机画面", "camera_view": "auto", "show_state": False},
                    grid([tile("sensor.a1mini_${PRINTER_SERIAL}_print_status", "状态", "mdi:printer-3d", color="teal"),
                          tile("sensor.a1mini_${PRINTER_SERIAL}_print_progress", "进度", "mdi:percent"),
                          tile("sensor.a1mini_${PRINTER_SERIAL}_remaining_time", "剩余时间", "mdi:timer-sand"),
                          tile("sensor.a1mini_${PRINTER_SERIAL}_current_layer", "当前层", "mdi:layers"),
                          tile("sensor.a1mini_${PRINTER_SERIAL}_nozzle_temperature", "喷嘴温度", "mdi:thermometer", color="red"),
                          tile("sensor.a1mini_${PRINTER_SERIAL}_bed_temperature", "热床温度", "mdi:radiator", color="orange")], columns=3),
                ]},
                {"type": "grid", "cards": [
                    {"type": "tile", "entity": "light.a1mini_${PRINTER_SERIAL}_chamber_light", "name": "仓灯",
                     "icon": "mdi:lightbulb", "color": "amber"},
                    {"type": "tile", "entity": "fan.a1mini_${PRINTER_SERIAL}_cooling_fan", "name": "冷却风扇",
                     "icon": "mdi:fan"},
                    grid([tile("sensor.a1mini_${PRINTER_SERIAL}_ams_1_tray_1", "料盘1", "mdi:palette"),
                          tile("sensor.a1mini_${PRINTER_SERIAL}_ams_1_tray_2", "料盘2", "mdi:palette"),
                          tile("sensor.a1mini_${PRINTER_SERIAL}_ams_1_tray_3", "料盘3", "mdi:palette"),
                          tile("sensor.a1mini_${PRINTER_SERIAL}_ams_1_tray_4", "料盘4", "mdi:palette")], columns=4),
                ]},
                {"type": "grid", "cards": [grid([
                    tile("sensor.a1mini_${PRINTER_SERIAL}_wi_fi_signal", "Wi-Fi", "mdi:wifi"),
                    tile("sensor.a1mini_${PRINTER_SERIAL}_current_stage", "当前阶段", "mdi:state-machine"),
                    tile("sensor.a1mini_${PRINTER_SERIAL}_speed_profile", "速度模式", "mdi:speedometer"),
                    tile("sensor.a1mini_${PRINTER_SERIAL}_print_weight", "耗材重量", "mdi:weight-gram"),
                    tile("sensor.sixwgh_v8icwf_52c7_electric_power", "插座功率", "mdi:flash"),
                    tile("switch.sixwgh_v8icwf_52c7_switch", "打印机插座", "mdi:power-socket-cn"),
                ], columns=3)]},
            ],
        },
        # ========================== 安防 · 环境 ==========================
        {
            "title": "安防·环境", "path": "security", "icon": "mdi:shield-home", "type": "sections",
            "sections": [
                {"type": "grid", "cards": [
                    {"type": "picture-entity", "entity": "camera.loock_r2_559c_video_doorbell",
                     "name": "防盗门门铃", "camera_view": "auto", "show_state": False},
                    {"type": "picture-entity", "entity": "camera.chuangmi_ipc019_15e7_camera_control",
                     "name": "天网恢恢", "camera_view": "auto", "show_state": False},
                    # 真·实时画面：NAS 上的 go2rtc 走小米 miss/P2P 本地取流 → 转 H264（见 HA 「客厅摄像头实时」实体）
                    {"type": "picture-entity", "entity": "camera.ke_ting_she_xiang_tou_shi_shi",
                     "name": "客厅实时", "camera_view": "live", "show_state": False},
                ]},
                {"type": "grid", "cards": [grid([
                    tile("sensor.fang_dao_men_zhuang_tai", "门状态", "mdi:door-closed-lock", color="red"),
                    tile("sensor.loock_r2_559c_battery_level", "门锁电量", "mdi:battery-lock"),
                    tile("binary_sensor.loock_r2_559c_armed_state", "布防", "mdi:shield-lock"),
                    tile("switch.chuangmi_ipc019_15e7_switch_status", "摄像头开关", "mdi:cctv", color="grey"),
                    tile("switch.chuangmi_ipc019_15e7_glimmer_full_color", "全彩夜视", "mdi:weather-night"),
                ], columns=3)]},
                {"type": "grid", "cards": [grid([
                    tile("sensor.ke_wei_you_ren", "客卫有人", "mdi:motion-sensor", color="purple"),
                    tile("sensor.zhu_wei_you_ren", "主卫有人", "mdi:motion-sensor", color="purple"),
                    tile("sensor.xiaomi_rrbr00_c147_temperature", "客厅温度", "mdi:thermometer", color="orange"),
                    tile("sensor.xiaomi_rrbr00_c147_relative_humidity", "客厅湿度", "mdi:water-percent", color="blue"),
                    tile("sensor.xiaomi_h09h00_90b0_temperature", "主卧温度", "mdi:thermometer", color="orange"),
                    tile("sensor.xiaomi_h09h00_8af7_temperature", "书房温度", "mdi:thermometer", color="orange"),
                ], columns=3)]},
            ],
        },
    ],
}


# ——— 其它 6 个视图的排版润色（主页保持用户自己改的样子，绝不碰 main）———
VIEW_TWEAKS = {
    "living": {
        "headings": {1: ("客厅灯光", "mdi:lightbulb-group"), 2: ("其它灯 · 充电", "mdi:lamp"),
                     3: ("窗帘", "mdi:curtains"), 4: ("影音 · 客厅环境", "mdi:speaker")},
        "cols": {3: 2}, "spans": {0: 2},
    },
    "bedroom": {
        "headings": {1: ("卧室灯光", "mdi:lightbulb-group"), 2: ("书房 · 次卧灯光", "mdi:desk-lamp"),
                     3: ("主卧环境", "mdi:home-thermometer"), 5: ("音响 · 家庭屏", "mdi:tablet")},
        "spans": {0: 2, 4: 2},
    },
    "utility": {
        "headings": {0: ("餐厅灯光", "mdi:silverware-fork-knife"), 1: ("厨卫 · 玄关 · 阳台灯光", "mdi:lightbulb-group"),
                     2: ("客卫感应 · 光照", "mdi:motion-sensor"), 3: ("插座 · 开机卡", "mdi:power-socket-cn")},
    },
    "appliance": {
        "headings": {0: ("洗衣机", "mdi:washing-machine"), 1: ("热水器", "mdi:water-boiler"),
                     2: ("冰箱 · 净水", "mdi:fridge-outline"), 3: ("扫地机", "mdi:robot-vacuum"),
                     4: ("扫地机地图", "mdi:map")},
        "spans": {3: 2, 4: 2},
    },
    "printer": {
        "headings": {1: ("仓灯 · 风扇 · 料盘", "mdi:palette"), 2: ("设备信息", "mdi:information-outline")},
        "spans": {0: 2},
    },
    "security": {
        "headings": {0: ("门铃 · 摄像头画面", "mdi:cctv"), 1: ("门锁 · 摄像头设置", "mdi:door-closed-lock"),
                     2: ("全屋环境感应", "mdi:motion-sensor")},
        "spans": {0: 3},
    },
}


def tweak_views():
    for v in DASH["views"]:
        tw = VIEW_TWEAKS.get(v.get("path"))
        if not tw:
            continue
        secs = v.get("sections", [])
        for idx, (title, icon) in (tw.get("headings") or {}).items():
            if idx < len(secs):
                secs[idx]["cards"].insert(0, {"type": "heading", "heading": title, "icon": icon})
        for idx, cols in (tw.get("cols") or {}).items():
            if idx < len(secs):
                for c in secs[idx]["cards"]:
                    if c.get("type") == "grid" and isinstance(c.get("cards"), list):
                        c["columns"] = cols
        for idx, span in (tw.get("spans") or {}).items():
            if idx < len(secs):
                secs[idx]["column_span"] = span


# ——— 全屏(kiosk)与自绘导航：放在这里统一处理，避免改每个视图的源码 ———
DASH["kiosk_mode"] = {"kiosk": True}          # 隐藏 HA 自带的侧边栏 + 顶栏（临时关闭：网址后加 ?disable_km）
tweak_views()
for _v in DASH["views"]:
    _v["sections"].insert(0, nav_section(_v["path"], wide=(_v["path"] == "main")))


def main():
    apply = "--apply" in sys.argv
    cfg = json.dumps(DASH, ensure_ascii=False)
    print(f"视图 {len(DASH['views'])} 个，配置 {len(cfg)} 字符")
    # 引用校验
    states = {s["entity_id"] for s in H.rest("GET", "/api/states")}
    bad = []
    def walk(n):
        if isinstance(n, dict):
            e = n.get("entity")
            if isinstance(e, str) and "." in e and e not in states:
                bad.append(e)
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)
    walk(DASH)
    print("失效引用:", bad or "无 ✅")
    if not apply:
        print("（干跑，加 --apply 保存）")
        return
    # ⚠️ 主页(main)是用户自己在界面上调过的，默认**不覆盖**，只更新其它视图。
    #    真要连主页一起覆盖：加 --all（慎用）
    if "--all" in sys.argv:
        out = DASH
        print("⚠️ 覆盖全部视图（含主页）")
    else:
        live = [x for x in H.ws([{"id": 1, "type": "lovelace/config", "url_path": URL_PATH}])
                if x.get("id") == 1][0]["result"]
        gen = {v["path"]: v for v in DASH["views"]}
        # ⚠️ 按 path 匹配、并**保持线上视图顺序**（用户会拖动排序；早期版本假设 main 在第 0 位，
        #    一旦顺序被拖动就会把主页覆盖掉 —— 实测踩过）
        out = dict(live)
        out["views"] = [(v if v["path"] == "main" else gen.get(v["path"], v))
                        for v in live["views"]]
        _have = {v["path"] for v in live["views"]}
        out["views"] += [v for v in DASH["views"] if v["path"] not in _have]
        print("只更新其它 %d 个视图，主页保持线上版本（顺序也保持线上）" % (len(DASH["views"]) - 1))
    H.ws([{"id": 2, "type": "lovelace/config/save", "url_path": URL_PATH, "config": out}])
    print("✅ 已保存到", URL_PATH)


if __name__ == "__main__":
    main()
