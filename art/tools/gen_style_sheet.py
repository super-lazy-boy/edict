# -*- coding: utf-8 -*-
"""《敕令》美术规范参考图生成器 v4。

纯俯视：建筑只有屋顶，不露墙面。瓦片 48，建筑 144/192，角色 24x32，头像 256。
"""
import os
import random
from PIL import Image, ImageDraw, ImageFont

ROOT = r"D:\Work\edict"
OUT_DIR = os.path.join(ROOT, "art", "preview")
os.makedirs(OUT_DIR, exist_ok=True)

TILE = 48

PAL = {
    "ink0": "#0E0D10", "ink1": "#17161B", "ink2": "#221F26", "ink3": "#302C33",
    "gray0": "#4A474E", "gray1": "#635F66", "gray2": "#827D83",
    "bone0": "#C4BCAE", "bone1": "#E0D8C8",
    "green0": "#232A1C", "green1": "#313A26", "green2": "#424B31",
    "green3": "#555E3D", "green4": "#6B7449", "green5": "#828B5A",
    "blue0": "#17262E", "blue1": "#22363F", "blue2": "#2F4A55", "blue3": "#40606C",
    "earth0": "#4A3E30", "earth1": "#5F5140", "sand0": "#7A6A52", "sand1": "#948266",
    "wood0": "#3A2A1E", "wood1": "#4E3828", "wood2": "#654933", "wood3": "#7E5C41",
    "red0": "#5C2620", "red1": "#7A332A",
    "purple": "#453048", "gold0": "#8F7433", "gold1": "#B89A4E",
}
ORDER = list(PAL.keys())


def C(name, a=255):
    h = PAL[name].lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def font(size, bold=False):
    cands = []
    if bold:
        cands.append(r"C:\Windows\Fonts\msyhbd.ttc")
    cands += [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"]
    for p in cands:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default(size=size)


# ================= 绘制工具 =================

def dither(d, box, c2, density=0.3, seed=0, checker=True):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    col = C(c2) if isinstance(c2, str) else c2
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if checker and (x + y) % 2:
                continue
            if rnd.random() < density:
                d.point((x, y), fill=col)


def soft_shadow(img, box, dx, dy, alpha=75, seed=0):
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    x0, y0, x1, y1 = box
    sd.rectangle([x0 + dx, y0 + dy, x1 + dx, y1 + dy], fill=(0, 0, 0, alpha))
    img.alpha_composite(sh)


def roof_tiles(d, box, base, edge_hi, edge_lo, th=7, tw=14, seed=0):
    """俯视屋瓦：横向叠瓦。每行有亮顶边、暗底边，底边上错缝短竖线表示单片瓦。
    不要画通长竖线——那是砖墙。"""
    x0, y0, x1, y1 = box
    d.rectangle([x0, y0, x1, y1], fill=C(base))
    row = 0
    y = y0
    while y <= y1:
        yb = min(y + th - 1, y1)
        d.line([(x0, y), (x1, y)], fill=C(edge_hi))
        d.line([(x0, yb), (x1, yb)], fill=C(edge_lo))
        off = 0 if row % 2 == 0 else tw // 2
        x = x0 - off
        while x <= x1:
            xa = max(x, x0)
            d.line([(xa, max(y + th - 3, y + 1)), (xa, yb)], fill=C(edge_lo))
            x += tw
        y += th
        row += 1


def planks_v(d, box, base, dark, light, pw=9, seed=0):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    d.rectangle([x0, y0, x1, y1], fill=C(base))
    x = x0
    while x <= x1:
        d.line([(x, y0), (x, y1)], fill=C(dark))
        if x + 1 <= x1:
            d.line([(x + 1, y0), (x + 1, y1)], fill=C(light))
        x += pw


def stone_courses(d, box, base, mortar, light, dark, bw=26, bh=13, seed=0):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    d.rectangle([x0, y0, x1, y1], fill=C(mortar))
    row = 0
    y = y0
    while y <= y1:
        off = 0 if row % 2 == 0 else bw // 2
        x = x0 - off
        while x <= x1:
            xa, xb = max(x + 1, x0), min(x + bw - 2, x1)
            ya, yb = max(y + 1, y0), min(y + bh - 2, y1)
            if xb > xa and yb > ya:
                col = base if rnd.random() > 0.2 else light
                d.rectangle([xa, ya, xb, yb], fill=C(col))
                d.line([(xa, ya), (xb, ya)], fill=C(light))
                d.line([(xa, yb), (xb, yb)], fill=C(dark))
            x += bw
        y += bh
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


# ================= 地形 48x48 =================

def t_grass():
    img = Image.new("RGBA", (TILE, TILE), C("green3"))
    d = ImageDraw.Draw(img)
    dither(d, (0, 0, TILE - 1, TILE - 1), "green4", 0.20, 1)
    dither(d, (0, 0, TILE - 1, TILE - 1), "green2", 0.13, 2)
    rnd = random.Random(21)
    for _ in range(24):
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
        d.ellipse([cx - r + 5, cy - r + 5, cx - 3, cy - 4], fill=C("green3"))
    return img


def t_water():
    img = Image.new("RGBA", (TILE, TILE), C("blue1"))
    d = ImageDraw.Draw(img)
    rnd = random.Random(3)
    for y in range(2, TILE, 5):
        x0 = rnd.randrange(0, 30)
        d.line([(x0, y), (x0 + 12, y)], fill=C("blue2"))
        d.line([(x0 + 2, y + 1), (x0 + 10, y + 1)], fill=C("blue0"))
    dither(d, (0, 0, TILE - 1, TILE - 1), "blue0", 0.08, 4)
    return img


def t_sand():
    img = Image.new("RGBA", (TILE, TILE), C("sand0"))
    d = ImageDraw.Draw(img)
    dither(d, (0, 0, TILE - 1, TILE - 1), "sand1", 0.28, 5)
    dither(d, (0, 0, TILE - 1, TILE - 1), "earth1", 0.10, 6)
    return img


def t_rock():
    img = Image.new("RGBA", (TILE, TILE), C("gray0"))
    d = ImageDraw.Draw(img)
    rnd = random.Random(9)
    for _ in range(9):
        x, y = rnd.randrange(1, 34), rnd.randrange(1, 34)
        w, h = rnd.randrange(7, 14), rnd.randrange(5, 10)
        d.polygon([(x, y), (x + w, y + 3), (x + w - 2, y + h), (x + 2, y + h - 2)],
                  fill=C("gray1"))
        d.line([(x, y), (x + 2, y + h - 2)], fill=C("ink2"))
        d.line([(x + 2, y + h - 2), (x + w - 2, y + h)], fill=C("ink2"))
    dither(d, (0, 0, TILE - 1, TILE - 1), "ink3", 0.06, 10)
    return img


def t_dirt():
    img = Image.new("RGBA", (TILE, TILE), C("earth1"))
    d = ImageDraw.Draw(img)
    dither(d, (0, 0, TILE - 1, TILE - 1), "earth0", 0.24, 11)
    dither(d, (0, 0, TILE - 1, TILE - 1), "sand0", 0.11, 12)
    rnd = random.Random(13)
    for _ in range(10):
        x, y = rnd.randrange(2, TILE - 4), rnd.randrange(2, TILE - 4)
        d.rectangle([x, y, x + 2, y + 1], fill=C("earth0"))
    return img


# ================= 建筑零件 48x48 =================

def p_roof_lit():
    img = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, TILE - 1, TILE - 1], fill=C("wood1"))
    roof_tiles(d, (2, 2, TILE - 3, TILE - 3), "red1", "wood3", "red0", 7, 12)
    return outline(img)


def p_roof_shadow():
    img = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, TILE - 1, TILE - 1], fill=C("wood1"))
    roof_tiles(d, (2, 2, TILE - 3, TILE - 3), "red0", "red1", "ink2", 7, 12)
    return outline(img)


def p_ridge():
    img = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 14, TILE - 1, 33], fill=C("wood1"))
    d.rectangle([0, 14, TILE - 1, 17], fill=C("wood3"))
    d.rectangle([0, 30, TILE - 1, 33], fill=C("wood0"))
    for x in range(0, TILE, 12):
        d.line([(x, 18), (x, 29)], fill=C("wood0"))
    return outline(img)


def p_wall():
    img = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    planks_v(d, (0, 4, TILE - 1, TILE - 5), "wood2", "wood1", "wood3", 9, 41)
    d.rectangle([0, 4, TILE - 1, 7], fill=C("wood3"))
    d.rectangle([0, TILE - 7, TILE - 1, TILE - 5], fill=C("wood0"))
    return outline(img)


def p_door():
    img = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([12, 2, 35, 45], fill=C("wood1"))
    planks_v(d, (14, 4, 33, 43), "wood1", "wood0", "wood2", 6, 42)
    d.rectangle([27, 20, 30, 24], fill=C("gold0"))
    d.rectangle([12, 2, 35, 3], fill=C("wood3"))
    return outline(img)


def p_window():
    img = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([8, 8, 39, 39], fill=C("wood1"))
    d.rectangle([11, 11, 36, 36], fill=C("blue1"))
    d.rectangle([11, 11, 36, 14], fill=C("blue3"))
    d.rectangle([11, 11, 15, 36], fill=C("blue2"))
    d.line([(23, 11), (23, 36)], fill=C("wood1"))
    d.line([(11, 23), (36, 23)], fill=C("wood1"))
    d.rectangle([8, 8, 39, 9], fill=C("wood3"))
    return outline(img)


def p_chimney():
    img = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    stone_courses(d, (12, 6, 35, 41), "gray1", "ink3", "gray2", "gray0", 12, 9, 51)
    d.rectangle([10, 4, 37, 10], fill=C("gray2"))
    d.rectangle([10, 4, 37, 5], fill=C("bone0"))
    d.rectangle([16, 6, 31, 9], fill=C("ink1"))
    return outline(img)


def p_fence():
    img = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for yy in (16, 30):
        d.rectangle([1, yy, TILE - 2, yy + 4], fill=C("wood2"))
        d.rectangle([1, yy, TILE - 2, yy + 1], fill=C("wood3"))
        d.rectangle([1, yy + 4, TILE - 2, yy + 4], fill=C("wood0"))
    for x in (6, 22, 38):
        d.rectangle([x, 8, x + 4, 42], fill=C("wood1"))
        d.rectangle([x, 8, x + 4, 10], fill=C("wood3"))
    return outline(img)


# ================= 完整建筑（纯俯视，只有屋顶） =================

def b_house():
    S = 144
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    soft_shadow(img, (14, 14, 130, 128), 6, 6, 75, 1)
    # 檐口（屋顶外缘）
    d.rectangle([12, 12, 132, 130], fill=C("wood1"))
    d.rectangle([12, 12, 132, 15], fill=C("wood3"))
    d.rectangle([12, 127, 132, 130], fill=C("wood0"))
    d.rectangle([12, 12, 15, 130], fill=C("wood2"))
    d.rectangle([129, 12, 132, 130], fill=C("wood0"))
    # 上坡（受光）
    roof_tiles(d, (16, 16, 128, 68), "red1", "wood3", "red0", 7, 13)
    # 下坡（背光）
    roof_tiles(d, (16, 68, 128, 126), "red0", "red1", "ink2", 7, 13)
    # 屋脊
    d.rectangle([14, 64, 130, 72], fill=C("wood1"))
    d.rectangle([14, 64, 130, 66], fill=C("wood3"))
    d.rectangle([14, 70, 130, 72], fill=C("wood0"))
    d.rectangle([16, 72, 128, 74], fill=C("ink3"))
    # 烟囱
    stone_courses(d, (100, 24, 120, 44), "gray1", "ink3", "gray2", "gray0", 10, 8, 11)
    d.rectangle([98, 22, 122, 28], fill=C("gray2"))
    d.rectangle([98, 22, 122, 23], fill=C("bone0"))
    d.rectangle([104, 24, 116, 26], fill=C("ink1"))
    # 屋顶天窗
    d.rectangle([52, 84, 82, 108], fill=C("wood1"))
    d.rectangle([55, 87, 79, 105], fill=C("blue1"))
    d.rectangle([55, 87, 79, 90], fill=C("blue3"))
    d.line([(67, 87), (67, 105)], fill=C("wood1"))
    return outline(img)


def b_farm():
    S = 192
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 田地：土壤 + 垄沟 + 成排作物
    d.rectangle([4, 44, 187, 187], fill=C("earth0"))
    dither(d, (6, 46, 185, 185), "earth1", 0.38, 21)
    for y in range(52, 184, 10):
        d.rectangle([8, y, 183, y + 2], fill=C("earth1"))
        dither(d, (8, y, 183, y + 2), "sand0", 0.30, y)
        for x in range(14, 178, 10):
            d.rectangle([x, y + 3, x + 3, y + 6], fill=C("green2"))
            d.point((x + 1, y + 3), fill=C("green4"))
            d.point((x + 2, y + 4), fill=C("green5"))
    # 田边小屋
    soft_shadow(img, (44, 6, 116, 46), 4, 4, 75, 2)
    d.rectangle([42, 4, 118, 46], fill=C("wood1"))
    roof_tiles(d, (46, 8, 114, 25), "red1", "wood3", "red0", 6, 11)
    roof_tiles(d, (46, 25, 114, 42), "red0", "red1", "ink2", 6, 11)
    d.rectangle([44, 23, 116, 27], fill=C("wood1"))
    d.rectangle([44, 23, 116, 24], fill=C("wood3"))
    # 稻草人
    d.rectangle([150, 56, 152, 78], fill=C("wood1"))
    d.rectangle([144, 60, 158, 62], fill=C("wood1"))
    d.ellipse([144, 50, 158, 64], fill=C("sand1"))
    d.rectangle([142, 62, 160, 72], fill=C("sand0"))
    return outline(img)


def b_warehouse():
    S = 192
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    soft_shadow(img, (10, 12, 182, 176), 7, 7, 75, 3)
    d.rectangle([8, 10, 184, 178], fill=C("wood1"))
    d.rectangle([8, 10, 184, 14], fill=C("wood3"))
    d.rectangle([8, 174, 184, 178], fill=C("wood0"))
    d.rectangle([8, 10, 12, 178], fill=C("wood2"))
    d.rectangle([180, 10, 184, 178], fill=C("wood0"))
    # 上坡
    roof_tiles(d, (12, 14, 180, 88), "red1", "wood3", "red0", 8, 15)
    # 下坡
    roof_tiles(d, (12, 88, 180, 174), "red0", "red1", "ink2", 8, 15)
    # 屋脊
    d.rectangle([10, 86, 182, 96], fill=C("wood1"))
    d.rectangle([10, 86, 182, 89], fill=C("wood3"))
    d.rectangle([10, 93, 182, 96], fill=C("wood0"))
    # 天窗（沿屋脊）
    for sx in (30, 78, 126):
        d.rectangle([sx, 62, sx + 34, 84], fill=C("wood1"))
        d.rectangle([sx + 3, 65, sx + 31, 81], fill=C("blue1"))
        d.rectangle([sx + 3, 65, sx + 31, 68], fill=C("blue3"))
        d.line([(sx + 17, 65), (sx + 17, 81)], fill=C("wood1"))
    # 通风口
    for vx in (26, 156):
        d.rectangle([vx, 120, vx + 14, 136], fill=C("wood1"))
        d.rectangle([vx + 2, 122, vx + 12, 134], fill=C("ink1"))
    return outline(img)


def b_barracks():
    S = 192
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    soft_shadow(img, (12, 16, 180, 176), 7, 7, 75, 4)
    # 屋顶主体（石质平顶）
    stone_courses(d, (12, 16, 180, 176), "gray0", "ink2", "gray1", "ink3", 26, 13, 5)
    dither(d, (14, 18, 178, 174), "gray1", 0.10, 6)
    # 女儿墙（四周垛口）
    d.rectangle([12, 16, 180, 30], fill=C("gray1"))
    d.rectangle([12, 162, 180, 176], fill=C("gray1"))
    d.rectangle([12, 16, 26, 176], fill=C("gray1"))
    d.rectangle([166, 16, 180, 176], fill=C("gray1"))
    for x in range(14, 180, 22):
        d.rectangle([x, 16, x + 12, 30], fill=C("gray2"))
        d.rectangle([x, 162, x + 12, 176], fill=C("gray2"))
    for yy in range(30, 162, 22):
        d.rectangle([12, yy, 26, yy + 12], fill=C("gray2"))
        d.rectangle([166, yy, 180, yy + 12], fill=C("gray2"))
    # 内院
    d.rectangle([28, 32, 164, 160], fill=C("ink3"))
    dither(d, (28, 32, 164, 160), "gray0", 0.16, 7)
    # 院内小屋（俯视）
    d.rectangle([40, 44, 92, 84], fill=C("wood1"))
    roof_tiles(d, (44, 48, 88, 64), "red1", "wood3", "red0", 6, 11)
    roof_tiles(d, (44, 64, 88, 80), "red0", "red1", "ink2", 6, 11)
    d.rectangle([42, 62, 90, 66], fill=C("wood1"))
    # 院中水井
    d.ellipse([110, 60, 138, 88], fill=C("gray1"))
    d.ellipse([114, 64, 134, 84], fill=C("ink1"))
    d.ellipse([117, 67, 131, 81], fill=C("blue1"))
    # 旗杆
    d.rectangle([154, 2, 158, 40], fill=C("wood1"))
    d.polygon([(158, 4), (186, 12), (158, 24)], fill=C("red1"))
    d.polygon([(158, 4), (186, 12), (158, 13)], fill=C("red0"))
    return outline(img)


# ================= 角色 24x32（俯视：头顶 + 肩） =================

SKIN = "sand1"


def char_sprite(body, hair="ink1", back=False):
    img = Image.new("RGBA", (24, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 肩背（俯视看到的身体）
    d.ellipse([3, 12, 20, 28], fill=C(body))
    d.ellipse([5, 14, 18, 24], fill=C(body))
    # 手臂
    d.ellipse([2, 16, 7, 25], fill=C(body))
    d.ellipse([16, 16, 21, 25], fill=C(body))
    # 头（俯视是头顶，所以是头发色）
    d.ellipse([6, 5, 17, 17], fill=C(hair))
    if back:
        d.ellipse([8, 7, 15, 15], fill=C(hair))
    else:
        # 前方露出一点面部，用于辨识朝向
        d.ellipse([9, 11, 14, 16], fill=C(SKIN))
        d.point((10, 13), fill=C("ink0"))
        d.point((13, 13), fill=C("ink0"))
    return outline(img)


# ================= 图标 24x24 =================

def i_coin():
    img = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 21, 21], fill=C("gold0"))
    d.ellipse([4, 3, 19, 18], fill=C("gold1"))
    d.ellipse([7, 6, 16, 15], fill=C("gold0"))
    d.rectangle([11, 8, 12, 13], fill=C("gold1"))
    return outline(img)


def i_wood():
    img = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([3, 7, 19, 17], fill=C("wood2"))
    d.ellipse([17, 7, 21, 17], fill=C("wood3"))
    d.ellipse([18, 9, 20, 15], fill=C("wood1"))
    for y in (9, 12, 15):
        d.line([(5, y), (17, y)], fill=C("wood1"))
    d.rectangle([3, 7, 19, 8], fill=C("wood3"))
    return outline(img)


def i_stone():
    img = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(4, 19), (7, 6), (17, 4), (20, 17)], fill=C("gray1"))
    d.polygon([(7, 6), (17, 4), (13, 12)], fill=C("gray2"))
    d.polygon([(4, 19), (7, 6), (13, 12)], fill=C("gray0"))
    return outline(img)


def i_food():
    img = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line([(12, 21), (12, 6)], fill=C("green1"))
    for y in (7, 11, 15):
        d.ellipse([3, y, 11, y + 5], fill=C("gold0"))
        d.ellipse([13, y, 21, y + 5], fill=C("gold0"))
        d.point((6, y + 1), fill=C("gold1"))
        d.point((16, y + 1), fill=C("gold1"))
    return outline(img)


def i_pop():
    img = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([8, 3, 16, 11], fill=C("sand1"))
    d.rectangle([10, 11, 14, 13], fill=C("sand0"))
    d.polygon([(5, 21), (8, 13), (16, 13), (19, 21)], fill=C("blue2"))
    d.polygon([(5, 21), (8, 13), (12, 13), (9, 21)], fill=C("blue3"))
    return outline(img)


def i_sword():
    img = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(19, 2), (21, 4), (10, 15), (8, 13)], fill=C("gray2"))
    d.polygon([(19, 2), (21, 4), (15, 8), (17, 10)], fill=C("bone0"))
    d.line([(6, 17), (11, 12)], fill=C("gold0"))
    d.line([(4, 16), (8, 20)], fill=C("wood1"))
    return outline(img)


def i_scroll():
    img = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([5, 3, 18, 20], fill=C("bone0"))
    d.rectangle([5, 3, 18, 5], fill=C("earth1"))
    d.rectangle([5, 18, 18, 20], fill=C("earth1"))
    for y in (8, 11, 14):
        d.line([(8, y), (15, y)], fill=C("earth0"))
    return outline(img)


def i_crown():
    img = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(3, 18), (3, 7), (8, 12), (12, 4), (16, 12), (21, 7), (21, 18)], fill=C("gold0"))
    d.rectangle([3, 18, 21, 21], fill=C("gold1"))
    d.point((7, 9), fill=C("gold1"))
    d.point((12, 7), fill=C("gold1"))
    d.point((17, 9), fill=C("gold1"))
    return outline(img)


# ================= 贵族头像 256x256 =================

def portrait(seed, mood):
    S = 256
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 背景
    d.rectangle([0, 0, S - 1, S - 1], fill=C("ink1"))
    for i in range(0, S, 12):
        d.rectangle([0, i, S - 1, i + 5], fill=C("ink2"))
    # 肩与衣领
    d.ellipse([14, 186, 242, 340], fill=C("purple"))
    d.ellipse([92, 206, 164, 286], fill=C("ink2"))
    d.polygon([(80, 196), (114, 168), (142, 168), (176, 196)], fill=C("ink1"))
    # 脖子
    d.rectangle([114, 148, 142, 198], fill=C("sand0"))
    d.rectangle([114, 148, 142, 162], fill=C("earth1"))
    # 脸
    d.ellipse([86, 30, 170, 172], fill=C(SKIN))
    d.ellipse([94, 108, 162, 182], fill=C(SKIN))
    d.ellipse([92, 38, 164, 108], fill=C("sand1"))
    # 颧骨与下颌阴影
    d.arc([94, 108, 162, 182], 25, 155, fill=C("sand0"), width=3)
    d.arc([90, 120, 166, 178], 200, 340, fill=C("sand0"), width=2)
    # 头发
    d.ellipse([82, 20, 174, 96], fill=C("ink1"))
    d.rectangle([82, 60, 90, 118], fill=C("ink1"))
    d.rectangle([166, 60, 174, 118], fill=C("ink1"))
    dither(d, (88, 28, 168, 88), "ink2", 0.12, seed)
    # 眉
    if mood == "greed":
        d.polygon([(96, 98), (122, 92), (122, 98), (96, 104)], fill=C("ink0"))
        d.polygon([(134, 92), (160, 98), (160, 104), (134, 98)], fill=C("ink0"))
    elif mood == "ambition":
        d.polygon([(96, 92), (122, 98), (122, 104), (96, 98)], fill=C("ink0"))
        d.polygon([(134, 98), (160, 92), (160, 98), (134, 104)], fill=C("ink0"))
    else:
        d.rectangle([96, 96, 122, 100], fill=C("ink0"))
        d.rectangle([134, 96, 160, 100], fill=C("ink0"))
    # 眼
    for ex in (98, 134):
        d.ellipse([ex, 110, ex + 24, 126], fill=C("bone0"))
        d.ellipse([ex + 7, 111, ex + 17, 125], fill=C("ink2"))
        d.ellipse([ex + 9, 113, ex + 15, 121], fill=C("ink0"))
        d.point((ex + 10, 113), fill=C("bone1"))
        d.line([(ex, 110), (ex + 24, 110)], fill=C("earth1"))
        d.line([(ex, 126), (ex + 24, 126)], fill=C("sand0"))
    # 鼻
    d.polygon([(126, 128), (134, 128), (132, 150), (128, 150)], fill=C("sand0"))
    d.rectangle([122, 150, 138, 153], fill=C("sand0"))
    d.rectangle([124, 153, 136, 155], fill=C("sand1"))
    d.point((123, 151), fill=C("earth1"))
    d.point((137, 151), fill=C("earth1"))
    # 嘴
    if mood == "greed":
        d.rectangle([114, 164, 146, 168], fill=C("wood1"))
        d.point((143, 164), fill=C("sand0"))
    elif mood == "ambition":
        d.rectangle([114, 166, 146, 169], fill=C("wood1"))
        d.point((117, 166), fill=C("sand0"))
    else:
        d.rectangle([116, 165, 144, 168], fill=C("wood1"))
    # 徽章
    d.rectangle([124, 176, 132, 214], fill=C("gold0"))
    d.ellipse([118, 208, 138, 228], fill=C("gold1"))
    d.ellipse([124, 214, 132, 222], fill=C("gold0"))
    # 边框
    d.rectangle([0, 0, S - 1, S - 1], outline=C("gold0"))
    d.rectangle([4, 4, S - 5, S - 5], outline=C("ink0"))
    return img


# ================= 拼版 =================

W, HCAP = 1800, 2900
sheet = Image.new("RGBA", (W, HCAP), C("ink0"))
d = ImageDraw.Draw(sheet)

F_TITLE = font(42, bold=True)
F_H2 = font(26, bold=True)
F_BODY = font(17)
F_SMALL = font(14)

y = 34
d.text((40, y), "《敕令》美术规范 v4.0  —  EDICT ART BIBLE", font=F_TITLE, fill=C("gold1"))
y += 54
d.text((40, y), "风格基准：Songs of Syx  ·  纯俯视（只见屋顶）  ·  瓦片 48×48  ·  32 色  ·  光源左上  ·  1px 描边  ·  静态角色",
       font=F_BODY, fill=C("bone0"))
y += 46


def section(title, note=""):
    global y
    d.line([(40, y), (W - 40, y)], fill=C("ink3"))
    y += 14
    d.text((40, y), title, font=F_H2, fill=C("bone1"))
    if note:
        tw = d.textlength(title, font=F_H2)
        d.text((40 + tw + 26, y + 9), note, font=F_SMALL, fill=C("gray1"))
    y += 44


def paste_scaled(img, x, top, scale):
    big = img.resize((int(img.width * scale), int(img.height * scale)), Image.NEAREST)
    sheet.alpha_composite(big, (x, top))
    return big


section("调色板  EDICT 32", "低饱和土色系，整体压暗。所有资源只能使用这 32 色")
cell_w, cell_h = 215, 100
for idx, name in enumerate(ORDER):
    col, row = idx % 8, idx // 8
    x = 40 + col * cell_w
    yy = y + row * cell_h
    d.rectangle([x, yy, x + 195, yy + 52], fill=C(name), outline=C("ink3"))
    d.text((x, yy + 58), name, font=F_SMALL, fill=C("bone0"))
    d.text((x, yy + 76), PAL[name].upper(), font=F_SMALL, fill=C("gray1"))
y += 4 * cell_h + 8

section("地形瓦片  TERRAIN 48×48", "无描边，无缝拼接，双色抖动做纹理")
terrain = [("草地", t_grass()), ("森林", t_forest()), ("水面", t_water()),
           ("沙地", t_sand()), ("岩石", t_rock()), ("土路", t_dirt())]
for i, (label, img) in enumerate(terrain):
    x = 40 + i * 232
    paste_scaled(img, x, y, 4)
    d.text((x, y + 200), label, font=F_SMALL, fill=C("bone0"))
y += 226

section("建筑零件  MODULAR KIT 48×48", "俯视零件：屋面、屋脊、檐口、烟囱")
parts = [("受光屋面", p_roof_lit()), ("背光屋面", p_roof_shadow()), ("屋脊", p_ridge()),
         ("墙体", p_wall()), ("门", p_door()), ("窗", p_window()),
         ("烟囱", p_chimney()), ("栅栏", p_fence())]
for i, (label, img) in enumerate(parts):
    x = 40 + i * 160
    paste_scaled(img, x, y, 3)
    d.text((x, y + 152), label, font=F_SMALL, fill=C("bone0"))
y += 182

section("完整建筑  BUILDINGS 144×144 / 192×192", "纯俯视：只看得到屋顶，不露任何墙面")
builds = [("民居 144", b_house(), 1.55), ("农田 192", b_farm(), 1.25),
          ("仓库 192", b_warehouse(), 1.25), ("兵营 192", b_barracks(), 1.25)]
for i, (label, img, sc) in enumerate(builds):
    x = 40 + i * 440
    paste_scaled(img, x, y, sc)
    d.text((x, y + 250), label, font=F_SMALL, fill=C("bone0"))
y += 280

section("角色  CHARACTERS 24×32", "俯视：头顶 + 肩背；静态无动画，靠服装色区分职业")
chars = [("农民", char_sprite("green3")), ("工匠", char_sprite("wood2")),
         ("商人", char_sprite("blue2")), ("士兵", char_sprite("gray1")),
         ("官员", char_sprite("purple")), ("贵族", char_sprite("purple", hair="gold0")),
         ("背面", char_sprite("green3", back=True))]
for i, (label, img) in enumerate(chars):
    x = 40 + i * 140
    paste_scaled(img, x, y, 4)
    d.text((x, y + 136), label, font=F_SMALL, fill=C("bone0"))
y += 168

section("界面图标  UI ICONS 24×24", "界面内按 2× 或 3× 整数放大")
icons = [("钱", i_coin()), ("木", i_wood()), ("石", i_stone()), ("粮", i_food()),
         ("人口", i_pop()), ("军事", i_sword()), ("政策", i_scroll()), ("王权", i_crown())]
for i, (label, img) in enumerate(icons):
    x = 40 + i * 130
    paste_scaled(img, x, y, 4)
    d.text((x, y + 104), label, font=F_SMALL, fill=C("bone0"))
y += 132

section("贵族头像  PORTRAITS 256×256", "唯一允许 AI 生成的资源；性格靠表情与服饰")
for i, (label, mood) in enumerate([("贪婪", "greed"), ("野心", "ambition"), ("忠诚", "loyal")]):
    x = 40 + i * 290
    paste_scaled(portrait(i + 1, mood), x, y, 1.0)
    d.text((x, y + 262), label, font=F_SMALL, fill=C("bone0"))
y += 300

d.text((40, y + 20), "生成：art/tools/gen_style_sheet.py   ·   《敕令》Edict   ·   2026-11",
       font=F_SMALL, fill=C("gray1"))

sheet = sheet.crop((0, 0, W, y + 70))
out = os.path.join(OUT_DIR, "style_sheet.png")
sheet.convert("RGB").save(out)
print("saved:", out, sheet.size)
