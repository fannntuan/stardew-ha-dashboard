#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成星露谷风格的像素图标（自绘，16x16 网格放大到 64x64）+ 木箱卡片框 + 羊皮纸横幅。
配色取自游戏 UI（物品栏面板真实取色）。全部本地生成，零外网依赖。
输出：/vol2/@appdata/trim.hermes/workspace/stardew_www/img/game/
"""
import os
from PIL import Image, ImageDraw

OUT = "/vol2/@appdata/trim.hermes/workspace/stardew_www/img/game"
os.makedirs(OUT, exist_ok=True)

P = {
    "K": (63, 36, 16, 255),      # 深描边
    "B": (90, 43, 42, 255),      # 深棕
    "W": (139, 90, 43, 255),     # 木中棕
    "C": (230, 164, 97, 255),    # 浅木
    "Y": (242, 181, 58, 255),    # 金
    "L": (220, 123, 5, 255),     # 橙
    "S": (249, 236, 208, 255),   # 羊皮纸
    "R": (192, 57, 43, 255),     # 红
    "U": (74, 144, 217, 255),    # 蓝
    "N": (78, 158, 74, 255),     # 绿
    "G": (150, 156, 162, 255),   # 灰
    "H": (203, 208, 213, 255),   # 浅灰
    "P": (125, 79, 158, 255),    # 紫
    "D": (27, 27, 27, 255),      # 黑
    "T": (255, 240, 200, 255),   # 亮点
}
S = 16          # 逻辑网格
FINAL = 64      # 输出尺寸


def canvas():
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def save(im, name):
    im.resize((FINAL, FINAL), Image.NEAREST).save(os.path.join(OUT, name))
    print("  ", name)


def out(im, box, c):
    im.rectangle(box, fill=P[c])
    return None


# ---------- 灯：火把（点着 / 熄灭） ----------
def torch(lit=True):
    im, d = canvas()
    d.rectangle((6, 8, 9, 15), fill=P["W"])           # 木柄
    d.rectangle((6, 8, 9, 8), fill=P["C"])
    d.rectangle((6, 15, 9, 15), fill=P["B"])
    d.rectangle((5, 6, 10, 8), fill=P["B"])           # 火把头
    d.rectangle((6, 6, 9, 7), fill=P["W"])
    if lit:
        d.polygon([(7, 0), (10, 4), (8, 7), (5, 4)], fill=P["L"])
        d.polygon([(7, 1), (9, 4), (7, 6), (6, 4)], fill=P["Y"])
        d.point((7, 3), fill=P["T"])
    else:
        d.rectangle((6, 5, 9, 6), fill=P["D"])
    return im


# ---------- 灯带：一串小灯 ----------
def string_lights():
    im, d = canvas()
    d.line((1, 6, 14, 6), fill=P["K"], width=1)
    for x, c in ((3, "Y"), (7, "L"), (11, "Y")):
        d.rectangle((x - 1, 7, x + 1, 9), fill=P[c])
        d.rectangle((x - 1, 7, x + 1, 7), fill=P["T"])
    return im


# ---------- 台灯 / 夜灯 ----------
def lamp(lit=True):
    im, d = canvas()
    d.polygon([(4, 5), (11, 5), (9, 1), (6, 1)], fill=P["C"])
    d.polygon([(4, 5), (11, 5), (9, 1), (6, 1)], outline=P["K"])
    d.rectangle((7, 6, 8, 12), fill=P["W"])
    d.rectangle((4, 13, 11, 14), fill=P["W"])
    d.rectangle((4, 14, 11, 14), fill=P["B"])
    if lit:
        d.rectangle((6, 4, 9, 5), fill=P["Y"])
        d.rectangle((7, 3, 8, 3), fill=P["T"])
    return im


# ---------- 筒灯 / 顶灯 ----------
def ceiling():
    im, d = canvas()
    d.rectangle((3, 2, 12, 4), fill=P["W"])
    d.rectangle((3, 2, 12, 2), fill=P["C"])
    d.polygon([(4, 5), (11, 5), (13, 9), (2, 9)], fill=P["C"])
    for x in range(4, 12, 2):
        d.line((x, 10, x, 11 + (x % 3)), fill=P["Y"])
    d.rectangle((3, 9, 12, 9), fill=P["B"])
    return im


# ---------- 水滴（湿度） ----------
def drop():
    im, d = canvas()
    d.polygon([(8, 1), (13, 9), (8, 14), (3, 9)], fill=P["U"])
    d.polygon([(8, 1), (13, 9), (8, 14), (3, 9)], outline=P["K"])
    d.rectangle((6, 8, 7, 11), fill=P["H"])
    return im


# ---------- 温度计 ----------
def thermo():
    im, d = canvas()
    d.rounded_rectangle((6, 1, 10, 11), radius=2, fill=P["S"], outline=P["K"])
    d.ellipse((5, 9, 11, 15), fill=P["R"], outline=P["K"])
    d.rectangle((7, 5, 8, 10), fill=P["R"])
    for y in (3, 5, 7):
        d.line((10, y, 11, y), fill=P["G"])
    return im


# ---------- 油桶 ----------
def oil():
    im, d = canvas()
    d.rectangle((4, 4, 11, 15), fill=P["G"])
    d.rectangle((4, 4, 11, 5), fill=P["H"])
    d.rectangle((4, 15, 11, 15), fill=P["K"])
    d.rectangle((3, 6, 12, 7), fill=P["D"])
    d.rectangle((3, 12, 12, 13), fill=P["D"])
    d.polygon([(8, 6), (11, 10), (8, 13), (5, 10)], fill=P["U"])
    return im


# ---------- 洗衣机 ----------
def washer():
    im, d = canvas()
    d.rectangle((1, 2, 14, 15), fill=P["H"])
    d.rectangle((1, 2, 14, 15), outline=P["K"])
    d.rectangle((2, 3, 13, 5), fill=P["S"])
    d.ellipse((4, 6, 12, 14), fill=P["S"], outline=P["K"])
    d.ellipse((5, 7, 11, 13), fill=P["U"])
    d.arc((5, 7, 11, 13), 200, 340, fill=P["H"])
    d.point((12, 4), fill=P["R"])
    return im


# ---------- 冰箱 ----------
def fridge():
    im, d = canvas()
    d.rectangle((3, 1, 12, 15), fill=P["H"])
    d.rectangle((3, 1, 12, 15), outline=P["K"])
    d.line((3, 6, 12, 6), fill=P["K"])
    d.rectangle((10, 3, 11, 5), fill=P["G"])
    d.rectangle((10, 8, 11, 12), fill=P["G"])
    return im


# ---------- 水壶（热水器） ----------
def kettle():
    im, d = canvas()
    d.ellipse((3, 5, 12, 15), fill=P["R"], outline=P["K"])
    d.rectangle((1, 7, 3, 10), fill=P["R"])          # 壶嘴
    d.arc((11, 3, 15, 10), 270, 90, fill=P["K"])     # 把手
    d.rectangle((5, 3, 9, 5), fill=P["G"])
    d.rectangle((6, 9, 9, 11), fill=P["Y"])
    return im


# ---------- 滤芯（净水） ----------
def filter():
    im, d = canvas()
    d.rectangle((4, 2, 11, 13), fill=P["S"])
    d.rectangle((4, 2, 11, 13), outline=P["K"])
    d.rectangle((3, 13, 12, 15), fill=P["W"])
    for y in (4, 6, 8, 10):
        d.line((5, y, 10, y), fill=P["G"])
    d.rectangle((6, 2, 9, 2), fill=P["U"])
    return im


# ---------- 3D 打印机 ----------
def printer():
    im, d = canvas()
    d.rectangle((1, 3, 14, 15), fill=P["W"])
    d.rectangle((1, 3, 14, 15), outline=P["K"])
    d.rectangle((2, 4, 13, 5), fill=P["G"])
    d.line((2, 7, 13, 7), fill=P["K"])
    d.rectangle((6, 8, 9, 9), fill=P["H"])           # 打印头
    d.rectangle((7, 10, 8, 11), fill=P["L"])
    d.rectangle((5, 12, 10, 13), fill=P["C"])        # 打印件
    return im


# ---------- 扫地机 ----------
def vacuum():
    im, d = canvas()
    d.ellipse((1, 3, 14, 14), fill=P["H"], outline=P["K"])
    d.ellipse((3, 5, 12, 12), fill=P["S"])
    d.ellipse((6, 7, 9, 10), fill=P["G"])
    d.rectangle((6, 1, 9, 4), fill=P["N"])
    d.point((4, 6), fill=P["Y"])
    return im


# ---------- 电池 ----------
def battery(level=3):
    im, d = canvas()
    d.rectangle((4, 2, 11, 14), fill=P["H"])
    d.rectangle((4, 2, 11, 14), outline=P["K"])
    d.rectangle((6, 0, 9, 2), fill=P["G"])
    for i in range(level):
        y = 12 - i * 3
        d.rectangle((5, y, 10, y + 2), fill=P["N"])
    return im


# ---------- 木门 ----------
def door():
    im, d = canvas()
    d.rectangle((3, 1, 12, 15), fill=P["W"])
    d.rectangle((3, 1, 12, 15), outline=P["K"])
    d.rectangle((5, 3, 10, 6), fill=P["B"])
    d.rectangle((5, 8, 10, 13), fill=P["B"])
    d.point((11, 9), fill=P["Y"])
    return im


# ---------- 摄像头（CCTV） ----------
def camera():
    im, d = canvas()
    d.rounded_rectangle((2, 4, 10, 10), radius=2, fill=P["G"], outline=P["K"])
    d.polygon([(10, 6), (14, 4), (14, 12), (10, 10)], fill=P["H"])
    d.ellipse((4, 6, 6, 8), fill=P["U"])
    d.rectangle((5, 10, 6, 15), fill=P["G"])
    return im


# ---------- 盾牌（布防/安防） ----------
def shield():
    im, d = canvas()
    d.polygon([(8, 1), (14, 3), (14, 8), (8, 15), (2, 8), (2, 3)], fill=P["U"])
    d.polygon([(8, 1), (14, 3), (14, 8), (8, 15), (2, 8), (2, 3)], outline=P["K"])
    d.polygon([(8, 4), (11, 5), (11, 8), (8, 12), (5, 8), (5, 5)], fill=P["S"])
    return im


# ---------- 有人（感应/眼睛） ----------
def eye():
    im, d = canvas()
    d.ellipse((1, 5, 14, 11), fill=P["S"], outline=P["K"])
    d.ellipse((5, 5, 10, 11), fill=P["N"])
    d.ellipse((6, 7, 8, 9), fill=P["D"])
    return im


# ---------- 音箱 ----------
def speaker():
    im, d = canvas()
    d.rectangle((3, 2, 12, 14), fill=P["B"])
    d.rectangle((3, 2, 12, 14), outline=P["K"])
    d.ellipse((5, 4, 10, 8), fill=P["D"])
    d.ellipse((6, 5, 9, 7), fill=P["G"])
    d.rectangle((5, 10, 10, 12), fill=P["G"])
    return im


# ---------- 电视 ----------
def tv():
    im, d = canvas()
    d.rectangle((1, 3, 14, 12), fill=P["B"])
    d.rectangle((1, 3, 14, 12), outline=P["K"])
    d.rectangle((2, 4, 13, 11), fill=P["U"])
    d.rectangle((3, 8, 12, 10), fill=P["N"])
    d.rectangle((4, 5, 10, 7), fill=P["S"])
    d.rectangle((5, 13, 10, 14), fill=P["W"])
    return im


# ---------- 窗帘 ----------
def curtain():
    im, d = canvas()
    d.rectangle((1, 1, 14, 3), fill=P["W"])
    d.rectangle((1, 3, 6, 15), fill=P["R"])
    d.rectangle((9, 3, 14, 15), fill=P["R"])
    for x in (2, 4, 10, 12):
        d.line((x, 3, x, 15), fill=P["B"])
    d.rectangle((7, 3, 8, 15), fill=P["S"])
    return im


# ---------- 木箱（3D 打印件 / 通用物品） ----------
def chest():
    im, d = canvas()
    d.rectangle((1, 5, 14, 14), fill=P["C"])
    d.rectangle((1, 5, 14, 14), outline=P["K"])
    d.rectangle((1, 5, 14, 8), fill=P["W"])
    d.rectangle((6, 5, 9, 9), fill=P["G"])
    d.rectangle((7, 8, 8, 10), fill=P["Y"])
    for x in (2, 5, 10, 13):
        d.line((x, 9, x, 14), fill=P["B"])
    return im


ICONS = {
    "ic_torch_on.png": lambda: torch(True),
    "ic_torch_off.png": lambda: torch(False),
    "ic_lamp_on.png": lambda: lamp(True),
    "ic_lamp_off.png": lambda: lamp(False),
    "ic_ceiling.png": ceiling,
    "ic_string.png": string_lights,
    "ic_drop.png": drop,
    "ic_thermo.png": thermo,
    "ic_oil.png": oil,
    "ic_washer.png": washer,
    "ic_fridge.png": fridge,
    "ic_kettle.png": kettle,
    "ic_filter.png": filter,
    "ic_printer.png": printer,
    "ic_vacuum.png": vacuum,
    "ic_battery.png": battery,
    "ic_door.png": door,
    "ic_camera.png": camera,
    "ic_shield.png": shield,
    "ic_eye.png": eye,
    "ic_speaker.png": speaker,
    "ic_tv.png": tv,
    "ic_curtain.png": curtain,
    "ic_chest.png": chest,
}

print("生成图标:")
for name, fn in ICONS.items():
    save(fn(), name)

# ---------- 木箱卡片框（9 宫格，12x12，4px 切片，四角有铆钉） ----------
crate = Image.new("RGBA", (12, 12), P["C"])
d = ImageDraw.Draw(crate)
for x in range(12):
    for y in range(12):
        if x in (0, 11) or y in (0, 11):
            crate.putpixel((x, y), P["K"])
        elif x in (1, 10) or y in (1, 10):
            crate.putpixel((x, y), P["W"])
        elif x in (2, 9) or y in (2, 9):
            crate.putpixel((x, y), P["B"])
        elif x == 3 or y == 3:
            crate.putpixel((x, y), P["L"] if (x < 6 and y < 6) else P["W"])
        elif x == 8 or y == 8:
            crate.putpixel((x, y), P["B"])
# 四角铆钉
for cx, cy in ((1, 1), (10, 1), (1, 10), (10, 10)):
    crate.putpixel((cx, cy), P["H"])
crate.save(os.path.join(OUT, "frame_crate.png"))
print("   frame_crate.png", crate.size)

# ---------- 羊皮纸横幅（9 宫格，16x16，5px 切片，卷边） ----------
ban = Image.new("RGBA", (16, 16), P["S"])
d = ImageDraw.Draw(ban)
for x in range(16):
    for y in range(16):
        edge = min(x, y, 15 - x, 15 - y)
        if edge == 0:
            ban.putpixel((x, y), P["B"])
        elif edge == 1:
            ban.putpixel((x, y), P["W"])
        elif edge == 2:
            ban.putpixel((x, y), P["C"])
        elif edge == 3:
            ban.putpixel((x, y), P["S"])
        else:
            ban.putpixel((x, y), P["S"])
# 左右两端的木轴
for y in range(16):
    for x in list(range(0, 3)) + list(range(13, 16)):
        ban.putpixel((x, y), P["W"] if y % 2 == 0 else P["B"])
ban.save(os.path.join(OUT, "frame_banner.png"))
print("   frame_banner.png", ban.size)

# ---------- 木拉杆（开关 ON） ----------
lev = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
d = ImageDraw.Draw(lev)
d.rectangle((3, 4, 12, 13), fill=P["C"])
d.rectangle((3, 4, 12, 13), outline=P["K"])
d.rectangle((4, 5, 11, 6), fill=P["W"])
d.rectangle((5, 2, 10, 9), fill=P["W"])          # 拉杆
d.rectangle((6, 1, 9, 3), fill=P["Y"])
d.rectangle((5, 10, 10, 12), fill=P["B"])
lev.save(os.path.join(OUT, "lever_on.png"))
print("   lever_on.png")

# ---------- 联络表（人工核对用） ----------
names = list(ICONS.keys()) + ["frame_crate.png", "frame_banner.png", "lever_on.png"]
cols, cell = 7, 96
rows = (len(names) + cols - 1) // cols
sheet = Image.new("RGBA", (cols * cell, rows * (cell + 14)), (245, 236, 214, 255))
dd = ImageDraw.Draw(sheet)
for i, n in enumerate(names):
    im = Image.open(os.path.join(OUT, n)).convert("RGBA")
    im = im.resize((72, 72), Image.NEAREST)
    x, y = (i % cols) * cell + 12, (i // cols) * (cell + 14) + 6
    sheet.alpha_composite(im, (x, y))
    dd.text((x - 6, y + 76), n.replace("ic_", "").replace(".png", "")[:12], fill=(60, 40, 20, 255))
sheet.save("/vol2/@appdata/trim.hermes/workspace/game_sprites_sheet.png")
print("\n联络表 ->", sheet.size)
