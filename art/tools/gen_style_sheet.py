# -*- coding: utf-8 -*-
"""《敕令》美术规范参考图 v6。

投影方案 C：屋顶 + 南墙（希克斯之歌式）。
调色板 40 色，瓦片 48，建筑 144/192，角色俯视 32，头像写实 256。
"""
import os
import random
from PIL import Image, ImageDraw, ImageFont

ROOT = r"D:\Work\edict"
OUT = os.path.join(ROOT, "art", "preview")
os.makedirs(OUT, exist_ok=True)

TILE = 48

PAL = {
    "ink0": "#0A090C", "ink1": "#121119", "ink2": "#1B1A23", "ink3": "#26242E",
    "gray0": "#3A3742", "gray1": "#4B4753", "gray2": "#5F5A68", "gray3": "#78727F", "gray4": "#948E99",
    "bone0": "#C2BAA9", "bone1": "#E2DACA",
    "green0": "#1C2416", "green1": "#27321E", "green2": "#344228",
    "green3": "#435433", "green4": "#55683F", "green5": "#6B7D4E",
    "blue0": "#111E26", "blue1": "#1A2C36", "blue2": "#253C48", "blue3": "#324E5C",
    "earth0": "#33291F", "earth1": "#443728", "earth2": "#574634",
    "sand0": "#6B5740", "sand1": "#836B50", "sand2": "#9C8263",
    "wood0": "#2A1E15", "wood1": "#3A2A1D", "wood2": "#4C3826", "wood3": "#5F4831", "wood4": "#765A3F",
    "red0": "#3E1A16", "red1": "#54241C", "red2": "#6B3125", "red3": "#84402F",
    "purple": "#3E2C46", "gold0": "#7A6229", "gold1": "#A2853A", "clay0": "#8E6B4E",
}
ORDER = list(PAL.keys())


def C(n, a=255):
    h = PAL[n].lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def font(size, bold=False):
    p = r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"
    try:
        return ImageFont.truetype(p, size)
    except Exception:
        return ImageFont.load_default(size=size)


def dither(d, box, c2, density=0.3, seed=0):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    col = C(c2) if isinstance(c2, str) else c2
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (x + y) % 2:
                continue
            if rnd.random() < density:
                d.point((x, y), fill=col)


def cast_shadow(img, box, dx, dy, alpha=95, spread=4):
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    x0, y0, x1, y1 = box
    sd.rectangle([x0 + dx, y0 + dy, x1 + dx, y1 + dy], fill=(0, 0, 0, alpha))
    rnd = random.Random(7)
    for i in range(spread):
        for x in range(x0 + dx - i, x1 + dx + i + 1):
            for y in (y0 + dy - i, y1 + dy + i):
                if 0 <= x < img.width and 0 <= y < img.height and rnd.random() < 0.55:
                    sd.point((x, y), fill=(0, 0, 0, alpha // 2))
    img.alpha_composite(sh)


def roof(d, box, base, hi, lo, th=8, tw=16):
    x0, y0, x1, y1 = box
    d.rectangle([x0, y0, x1, y1], fill=C(base))
    row = 0
    y = y0
    while y <= y1:
        yb = min(y + th - 1, y1)
        d.line([(x0, y), (x1, y)], fill=C(hi))
        d.line([(x0, yb), (x1, yb)], fill=C(lo))
        off = 0 if row % 2 == 0 else tw // 2
        x = x0 - off
        while x <= x1:
            xa = max(x, x0)
            d.line([(xa, max(y + th - 3, y + 1)), (xa, yb)], fill=C(lo))
            x += tw
        y += th
        row += 1


def outline(img, color=None):
    color = color or C("ink0")
    w, h = img.size
    src = img.load()
    out = img.copy()
    dst = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y][3] != 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and src[nx, ny][3] != 0:
                    dst[x, y] = color
                    break
    return out


ROOFS = {
    "tile": ("red2", "red3", "red1", "red0"),
    "thatch": ("sand1", "sand2", "sand0", "earth2"),
    "slate": ("gray3", "gray4", "gray2", "gray1"),
    "wood": ("wood3", "wood4", "wood2", "wood1"),
}


# ================= 通用建筑（C 投影） =================

def building(S, roof_kind="tile", wall="bone0", wall_shadow="sand1",
             frame="wood2", windows=2, chimney=True, flag=False,
             wall_ratio=0.27, stone_base=False):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    base, hi, lo, dark = ROOFS[roof_kind]

    m = int(S * 0.08)
    wall_h = int(S * wall_ratio)
    wall_top = S - m - wall_h
    wall_bot = S - m

    cast_shadow(img, (m, m, S - m, wall_bot), 8, 9, 95, 4)

    # ---- 南墙 ----
    d.rectangle([m, wall_top, S - m, wall_bot], fill=C(wall))
    dither(d, (m, wall_top, S - m, wall_bot), wall_shadow, 0.22, 11)
    # 墙脚阴影
    d.rectangle([m, wall_bot - 5, S - m, wall_bot], fill=C("earth0"))
    # 木构架：竖柱
    cols = [m, m + int(S * 0.19), m + int(S * 0.44), m + int(S * 0.69), S - m - 7]
    for x in cols:
        d.rectangle([x, wall_top, x + 6, wall_bot], fill=C(frame))
        d.rectangle([x, wall_top, x + 1, wall_bot], fill=C("wood4"))
    # 横梁
    d.rectangle([m, wall_top, S - m, wall_top + 6], fill=C(frame))
    d.rectangle([m, wall_top, S - m, wall_top + 1], fill=C("wood4"))
    d.rectangle([m, wall_bot - 8, S - m, wall_bot - 3], fill=C(frame))

    # ---- 门 ----
    dx0 = m + int(S * 0.30)
    dx1 = dx0 + int(S * 0.17)
    d.rectangle([dx0, wall_top + 12, dx1, wall_bot - 3], fill=C("wood1"))
    d.rectangle([dx0 + 3, wall_top + 15, dx1 - 3, wall_bot - 3], fill=C("wood2"))
    d.line([((dx0 + dx1) // 2, wall_top + 15), ((dx0 + dx1) // 2, wall_bot - 3)], fill=C("wood1"))
    d.rectangle([dx1 - 12, wall_top + 30, dx1 - 7, wall_top + 35], fill=C("gold1"))

    # ---- 窗 ----
    if windows >= 1:
        wx = m + 12
        d.rectangle([wx, wall_top + 16, wx + 22, wall_top + 36], fill=C(frame))
        d.rectangle([wx + 3, wall_top + 19, wx + 19, wall_top + 33], fill=C("blue2"))
        d.rectangle([wx + 3, wall_top + 19, wx + 19, wall_top + 21], fill=C("blue3"))
        d.line([(wx + 11, wall_top + 19), (wx + 11, wall_top + 33)], fill=C(frame))
    if windows >= 2:
        wx = S - m - 34
        d.rectangle([wx, wall_top + 16, wx + 22, wall_top + 36], fill=C(frame))
        d.rectangle([wx + 3, wall_top + 19, wx + 19, wall_top + 33], fill=C("blue2"))
        d.rectangle([wx + 3, wall_top + 19, wx + 19, wall_top + 21], fill=C("blue3"))
        d.line([(wx + 11, wall_top + 19), (wx + 11, wall_top + 33)], fill=C(frame))

    # 石基
    if stone_base:
        d.rectangle([m, wall_bot - 16, S - m, wall_bot], fill=C("gray2"))
        for x in range(m, S - m, 14):
            d.rectangle([x, wall_bot - 16, x + 12, wall_bot], fill=C("gray3"))
            d.line([(x, wall_bot - 16), (x, wall_bot)], fill=C("gray1"))

    # ---- 屋顶 ----
    r0 = m - 6
    r1 = S - m + 6
    d.rectangle([r0, m, r1, wall_top + 4], fill=C(frame))
    d.rectangle([r0, m, r1, m + 3], fill=C("wood4"))
    mid = m + int((wall_top - m) * 0.55)
    roof(d, (r0 + 4, m + 4, r1 - 4, mid), base, hi, lo, 8, 16)
    roof(d, (r0 + 4, mid, r1 - 4, wall_top), lo, base, dark, 8, 16)
    # 屋脊
    d.rectangle([r0 + 2, mid - 4, r1 - 2, mid + 5], fill=C(frame))
    d.rectangle([r0 + 2, mid - 4, r1 - 2, mid - 2], fill=C("wood4"))
    d.rectangle([r0 + 2, mid + 3, r1 - 2, mid + 5], fill=C("wood0"))
    # 檐口投在墙上的阴影
    d.rectangle([m, wall_top, S - m, wall_top + 7], fill=C("ink2"))
    dither(d, (m, wall_top + 7, S - m, wall_top + 12), wall_shadow, 0.5, 13)

    # ---- 烟囱 ----
    if chimney:
        cx = r0 + int((r1 - r0) * 0.72)
        d.rectangle([cx, m + 10, cx + 26, m + 52], fill=C("gray2"))
        d.rectangle([cx, m + 10, cx + 26, m + 13], fill=C("gray4"))
        d.rectangle([cx, m + 10, cx + 2, m + 52], fill=C("gray3"))
        d.rectangle([cx + 4, m + 16, cx + 22, m + 26], fill=C("ink1"))
        d.rectangle([cx - 2, m + 52, cx + 28, m + 55], fill=C("ink2"))

    # ---- 旗 ----
    if flag:
        d.rectangle([r1 - 18, m - 14, r1 - 15, m + 30], fill=C("wood2"))
        d.polygon([(r1 - 15, m - 12), (r1 + 10, m - 4), (r1 - 15, m + 8)], fill=C("red3"))
        d.polygon([(r1 - 15, m - 12), (r1 + 10, m - 4), (r1 - 15, m - 1)], fill=C("red2"))

    return img


def b_house():
    return building(192, "tile", "bone0", "sand1", "wood2", 2, True, False)


def b_farm():
    """农田：田地 + 田边小屋，整体俯视。"""
    S = 192
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 田地
    d.rectangle([6, 88, S - 6, S - 6], fill=C("earth0"))
    dither(d, (8, 90, S - 8, S - 8), "earth1", 0.35, 21)
    for y in range(96, S - 10, 12):
        d.rectangle([10, y, S - 10, y + 3], fill=C("earth1"))
        dither(d, (10, y, S - 10, y + 3), "sand0", 0.3, y)
        for x in range(16, S - 14, 11):
            d.rectangle([x, y + 4, x + 3, y + 8], fill=C("green2"))
            d.point((x + 1, y + 4), fill=C("green4"))
            d.point((x + 2, y + 5), fill=C("green5"))
    # 田边小屋（C 投影，缩小版）
    hut = building(104, "thatch", "sand2", "sand1", "wood2", 1, False, False, 0.32)
    img.alpha_composite(hut, (44, 0))
    # 稻草人
    d.rectangle([152, 46, 154, 68], fill=C("wood2"))
    d.rectangle([146, 50, 160, 52], fill=C("wood2"))
    d.ellipse([145, 38, 161, 54], fill=C("sand2"))
    d.rectangle([144, 52, 162, 64], fill=C("sand1"))
    d.rectangle([149, 34, 157, 39], fill=C("wood1"))
    return outline(img)


def b_warehouse():
    return building(192, "tile", "sand2", "sand1", "wood3", 0, True, False, 0.30)


def b_barracks():
    return building(192, "slate", "gray3", "gray2", "gray1", 1, True, True, 0.30, True)


def b_market():
    return building(144, "wood", "bone0", "sand1", "wood2", 0, False, False, 0.26)


def b_smithy():
    return building(144, "slate", "sand1", "earth2", "wood1", 1, True, False, 0.28, True)


# ================= 地形 48 =================

def t_grass():
    img = Image.new("RGBA", (TILE, TILE), C("green3"))
    d = ImageDraw.Draw(img)
    dither(d, (0, 0, TILE - 1, TILE - 1), "green4", 0.22, 1)
    dither(d, (0, 0, TILE - 1, TILE - 1), "green2", 0.16, 2)
    rnd = random.Random(21)
    for _ in range(22):
        x, y = rnd.randrange(2, TILE - 3), rnd.randrange(2, TILE - 3)
        d.line([(x, y), (x, y + 2)], fill=C("green5"))
    return img


def t_forest():
    img = t_grass().copy()
    d = ImageDraw.Draw(img)
    rnd = random.Random(7)
    for _ in range(5):
        cx, cy = rnd.randrange(12, 37), rnd.randrange(12, 37)
        r = rnd.randrange(9, 13)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=C("green1"))
        d.ellipse([cx - r + 2, cy - r + 2, cx + r - 2, cy + r], fill=C("green0"))
        d.ellipse([cx - r + 3, cy - r + 3, cx - 1, cy - 1], fill=C("green2"))
        d.ellipse([cx - r + 5, cy - r + 5, cx - 3, cy - 4], fill=C("green4"))
    return img


def t_water():
    img = Image.new("RGBA", (TILE, TILE), C("blue1"))
    d = ImageDraw.Draw(img)
    rnd = random.Random(3)
    for y in range(2, TILE, 5):
        x0 = rnd.randrange(0, 30)
        d.line([(x0, y), (x0 + 12, y)], fill=C("blue2"))
        d.line([(x0 + 2, y + 1), (x0 + 10, y + 1)], fill=C("blue0"))
    return img


def t_sand():
    img = Image.new("RGBA", (TILE, TILE), C("sand0"))
    d = ImageDraw.Draw(img)
    dither(d, (0, 0, TILE - 1, TILE - 1), "sand1", 0.3, 5)
    dither(d, (0, 0, TILE - 1, TILE - 1), "earth1", 0.12, 6)
    return img


def t_rock():
    img = Image.new("RGBA", (TILE, TILE), C("gray1"))
    d = ImageDraw.Draw(img)
    rnd = random.Random(9)
    for _ in range(9):
        x, y = rnd.randrange(1, 34), rnd.randrange(1, 34)
        w, h = rnd.randrange(7, 14), rnd.randrange(5, 10)
        d.polygon([(x, y), (x + w, y + 3), (x + w - 2, y + h), (x + 2, y + h - 2)],
                  fill=C("gray2"))
        d.line([(x, y), (x + 2, y + h - 2)], fill=C("ink2"))
        d.line([(x + 2, y + h - 2), (x + w - 2, y + h)], fill=C("ink2"))
    return img


def t_dirt():
    img = Image.new("RGBA", (TILE, TILE), C("earth1"))
    d = ImageDraw.Draw(img)
    dither(d, (0, 0, TILE - 1, TILE - 1), "earth0", 0.26, 11)
    dither(d, (0, 0, TILE - 1, TILE - 1), "sand0", 0.12, 12)
    return img


# ================= 角色 32（只看到头顶） =================

def char_top(hair="ink1", cloth="green3", hat=None):
    S = 32
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([6, 11, 27, 30], fill=(0, 0, 0, 110))
    img.alpha_composite(sh)
    # 肩背
    d.ellipse([5, 12, 27, 29], fill=C(cloth))
    d.ellipse([7, 14, 25, 27], fill=C(cloth))
    d.arc([6, 13, 26, 28], 190, 300, fill=C("ink3"), width=2)
    # 头顶
    d.ellipse([8, 3, 24, 21], fill=C(hair))
    d.ellipse([10, 5, 22, 19], fill=C(hair))
    d.arc([9, 4, 23, 20], 195, 295, fill=C("ink3"), width=2)
    if hat:
        d.ellipse([7, 2, 25, 20], fill=C(hat))
        d.ellipse([10, 6, 22, 17], fill=C(hat))
        d.arc([8, 3, 24, 19], 195, 295, fill=C("bone0"), width=2)
    # 前方露出一点鼻尖，提示朝向
    d.ellipse([14, 19, 18, 23], fill=C("clay0"))
    d.point((15, 21), fill=C("earth2"))
    return img


# ================= 写实头像 256 =================

def portrait(mood):
    S = 256
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], fill=C("ink1"))
    for i in range(0, S, 14):
        d.rectangle([0, i, S - 1, i + 5], fill=C("ink2"))
    d.ellipse([6, 182, 250, 340], fill=C("purple"))
    d.ellipse([70, 200, 186, 300], fill=C("ink2"))
    d.rectangle([112, 146, 146, 196], fill=C("clay0"))
    d.rectangle([112, 146, 146, 160], fill=C("earth2"))
    d.rectangle([112, 180, 146, 196], fill=C("earth2"))
    d.ellipse([84, 34, 174, 172], fill=C("clay0"))
    d.ellipse([94, 108, 164, 178], fill=C("clay0"))
    d.ellipse([94, 42, 164, 106], fill=C("sand2"))
    d.arc([84, 34, 174, 172], 200, 340, fill=C("earth2"), width=5)
    d.arc([94, 108, 164, 178], 300, 360, fill=C("earth2"), width=4)
    d.arc([96, 118, 160, 172], 30, 150, fill=C("earth2"), width=3)
    d.ellipse([80, 22, 178, 100], fill=C("ink1"))
    d.rectangle([80, 60, 92, 128], fill=C("ink1"))
    d.rectangle([166, 60, 178, 128], fill=C("ink1"))
    dither(d, (88, 30, 170, 92), "ink2", 0.16, 3)
    d.arc([86, 26, 172, 96], 200, 320, fill=C("ink3"), width=2)
    if mood == "greed":
        d.polygon([(96, 100), (124, 93), (124, 99), (96, 106)], fill=C("ink0"))
        d.polygon([(134, 93), (162, 100), (162, 106), (134, 99)], fill=C("ink0"))
    elif mood == "ambition":
        d.polygon([(96, 94), (124, 100), (124, 106), (96, 100)], fill=C("ink0"))
        d.polygon([(134, 100), (162, 94), (162, 100), (134, 106)], fill=C("ink0"))
    else:
        d.rectangle([96, 98, 124, 102], fill=C("ink0"))
        d.rectangle([134, 98, 162, 102], fill=C("ink0"))
    for ex in (96, 134):
        d.ellipse([ex - 2, 106, ex + 28, 128], fill=C("earth2"))
    for ex in (96, 134):
        d.ellipse([ex, 110, ex + 26, 124], fill=C("bone0"))
        d.ellipse([ex + 7, 110, ex + 19, 124], fill=C("sand1"))
        d.ellipse([ex + 9, 111, ex + 17, 123], fill=C("ink2"))
        d.ellipse([ex + 11, 113, ex + 15, 121], fill=C("ink0"))
        d.rectangle([ex + 11, 114, ex + 12, 116], fill=C("bone1"))
        d.line([(ex, 110), (ex + 26, 110)], fill=C("ink1"))
        d.line([(ex + 2, 124), (ex + 24, 124)], fill=C("earth2"))
    d.polygon([(126, 112), (134, 112), (133, 148), (127, 148)], fill=C("sand2"))
    d.polygon([(133, 112), (134, 112), (133, 148), (132, 148)], fill=C("earth2"))
    d.rectangle([120, 148, 140, 152], fill=C("earth2"))
    d.rectangle([122, 152, 138, 155], fill=C("clay0"))
    d.point((121, 149), fill=C("ink2"))
    d.point((139, 149), fill=C("ink2"))
    d.rectangle([116, 164, 144, 168], fill=C("ink1"))
    if mood == "greed":
        d.rectangle([116, 158, 144, 163], fill=C("earth2"))
        d.rectangle([118, 168, 142, 172], fill=C("clay0"))
    elif mood == "ambition":
        d.rectangle([116, 160, 144, 163], fill=C("earth2"))
        d.rectangle([120, 168, 140, 170], fill=C("clay0"))
    else:
        d.rectangle([116, 160, 144, 163], fill=C("earth2"))
        d.rectangle([120, 168, 140, 171], fill=C("clay0"))
    d.arc([104, 150, 154, 182], 20, 160, fill=C("earth2"), width=3)
    d.polygon([(78, 190), (114, 166), (142, 166), (178, 190)], fill=C("ink1"))
    d.polygon([(78, 190), (114, 166), (114, 186)], fill=C("ink2"))
    d.rectangle([122, 174, 134, 210], fill=C("gold0"))
    d.ellipse([116, 204, 140, 228], fill=C("gold1"))
    d.ellipse([123, 211, 133, 221], fill=C("gold0"))
    d.rectangle([0, 0, S - 1, S - 1], outline=C("gold0"))
    d.rectangle([3, 3, S - 4, S - 4], outline=C("ink0"))
    return img


# ================= 拼版 =================

W, HCAP = 1800, 2700
sheet = Image.new("RGBA", (W, HCAP), C("ink0"))
d = ImageDraw.Draw(sheet)
F_T, F_H, F_B, F_S = font(40, True), font(24, True), font(16), font(14)

y = 30
d.text((40, y), "《敕令》美术规范 v6.0  —  EDICT ART BIBLE", font=F_T, fill=C("gold1"))
y += 50
d.text((40, y), "投影 C（屋顶 + 南墙）  ·  瓦片 48  ·  40 色  ·  光源左上  ·  投影右下  ·  静态俯视角色",
       font=F_B, fill=C("bone0"))
y += 44


def sec(t, note=""):
    global y
    d.line([(40, y), (W - 40, y)], fill=C("ink3"))
    y += 12
    d.text((40, y), t, font=F_H, fill=C("bone1"))
    if note:
        d.text((40 + d.textlength(t, font=F_H) + 24, y + 8), note, font=F_S, fill=C("gray3"))
    y += 40


def put(img, x, top, sc):
    big = img.resize((int(img.width * sc), int(img.height * sc)), Image.NEAREST)
    sheet.alpha_composite(big, (x, top))


sec("完整建筑  BUILDINGS 144×144 / 192×192", "屋面 60% + 南墙 30% + 檐口阴影")
builds = [("民居 192", b_house(), 1.55), ("农田 192", b_farm(), 1.55),
          ("仓库 192", b_warehouse(), 1.55), ("兵营 192", b_barracks(), 1.55)]
for i, (label, img, sc) in enumerate(builds):
    x = 40 + i * 440
    put(img, x, y, sc)
    d.text((x, y + 320), label, font=F_S, fill=C("bone0"))
y += 350

builds2 = [("市场 144", b_market(), 1.7), ("铁匠铺 144", b_smithy(), 1.7)]
for i, (label, img, sc) in enumerate(builds2):
    x = 40 + i * 300
    put(img, x, y, sc)
    d.text((x, y + 260), label, font=F_S, fill=C("bone0"))
y += 290

sec("地形瓦片  TERRAIN 48×48", "无描边，无缝拼接，双色抖动")
terrain = [("草地", t_grass()), ("森林", t_forest()), ("水面", t_water()),
           ("沙地", t_sand()), ("岩石", t_rock()), ("土路", t_dirt())]
for i, (label, img) in enumerate(terrain):
    x = 40 + i * 232
    put(img, x, y, 4)
    d.text((x, y + 200), label, font=F_S, fill=C("bone0"))
y += 226

sec("角色  CHARACTERS 32×32", "只看到头顶：头发 + 肩背 + 前方额头；点击弹出头像")
chars = [("农民", char_top("ink1", "green3")), ("工匠", char_top("ink1", "wood2")),
         ("商人", char_top("ink1", "blue2")), ("士兵", char_top("gray1", "gray1", "gray2")),
         ("官员", char_top("ink1", "purple")), ("贵族", char_top("gold0", "purple"))]
for i, (label, img) in enumerate(chars):
    x = 40 + i * 150
    put(img, x, y, 4)
    d.text((x, y + 140), label, font=F_S, fill=C("bone0"))
y += 176

sec("写实头像 256×256", "额光 / 颧影 / 眼窝 / 鼻侧 / 唇下 —— 靠阴影分面")
for i, (label, mood) in enumerate([("贪婪", "greed"), ("野心", "ambition"), ("忠诚", "loyal")]):
    x = 40 + i * 290
    put(portrait(mood), x, y, 1.0)
    d.text((x, y + 262), label, font=F_S, fill=C("bone0"))
y += 300

sec("调色板  EDICT 40", "为写实阴影补足色阶")
cw, ch = 175, 96
for idx, name in enumerate(ORDER):
    col, row = idx % 10, idx // 10
    x = 40 + col * cw
    yy = y + row * ch
    d.rectangle([x, yy, x + 155, yy + 48], fill=C(name), outline=C("ink3"))
    d.text((x, yy + 54), name, font=F_S, fill=C("bone0"))
    d.text((x, yy + 70), PAL[name].upper(), font=F_S, fill=C("gray2"))
y += 4 * ch + 10

d.text((40, y + 10), "《敕令》Edict  ·  2026-11  ·  gen_style_sheet.py", font=F_S, fill=C("gray2"))
sheet = sheet.crop((0, 0, W, y + 60))
out = os.path.join(OUT, "style_sheet.png")
sheet.convert("RGB").save(out)
print("saved:", out, sheet.size)
