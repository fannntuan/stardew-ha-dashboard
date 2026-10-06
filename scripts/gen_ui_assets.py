
import os, random
from PIL import Image
D = (74, 35, 23, 255); M = (139, 90, 43, 255); HL = (242, 201, 142, 255)
SD = (181, 118, 47, 255); F = (224, 165, 95, 255)
IMGDIR = "/vol2/@appdata/trim.hermes/workspace/stardew_www/img"

# 木质按钮 9 宫格：9x9（3px 切片）
btn = Image.new("RGBA", (9, 9), F)
px = btn.load()
for x in range(9):
    for y in range(9):
        if x in (0, 8) or y in (0, 8):
            px[x, y] = D
        elif x in (1, 7) or y in (1, 7):
            px[x, y] = M
        elif x == 2 or y == 2:
            px[x, y] = HL
        elif x == 6 or y == 6:
            px[x, y] = SD
btn.save(os.path.join(IMGDIR, "frame_button.png"))
print("frame_button.png", btn.size)

# 木牌标签（标题用）9x9
sign = Image.new("RGBA", (9, 9), (168, 108, 52, 255))
p2 = sign.load()
for x in range(9):
    for y in range(9):
        if x in (0, 8) or y in (0, 8):
            p2[x, y] = (60, 30, 16, 255)
        elif x in (1, 7) or y in (1, 7):
            p2[x, y] = (120, 74, 34, 255)
        elif x == 2 or y == 2:
            p2[x, y] = (196, 134, 70, 255)
        elif x == 6 or y == 6:
            p2[x, y] = (138, 84, 38, 255)
sign.save(os.path.join(IMGDIR, "frame_sign.png"))
print("frame_sign.png", sign.size)

# 羊皮纸/木纹噪点（很淡，8x8）
random.seed(7)
noise = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
np = noise.load()
for x in range(8):
    for y in range(8):
        r = random.random()
        if r < 0.16:
            np[x, y] = (120, 80, 40, 14)
        elif r < 0.30:
            np[x, y] = (255, 245, 220, 16)
noise.save(os.path.join(IMGDIR, "paper_noise.png"))
print("paper_noise.png", noise.size)
