# -*- coding: utf-8 -*-
"""《敕令》美术规范参考图生成器 v2。

风格基准：Songs of Syx —— 低饱和土色、屋顶主导的顶视角、重描边、抖动纹理。
输出 art/preview/style_sheet.png
"""
import os
import random
from PIL import Image, ImageDraw, ImageFont

ROOT = r"D:\Work\edict"
OUT_DIR = os.path.join(ROOT, "art", "preview")
os.makedirs(OUT_DIR, exist_ok=True)

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


def dither(d, box, c2, density=0.3, seed=0, checker=True):
    """在已填充区域上撒第二色，做像素抖动。"""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    col = C(c2) if isinstance(c2, str) else c2
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if checker and (x + y) % 2:
                continue
            if rnd.random() < density:
                d.point((x, y), fill=col)


def outline(img, color=None):
    """透明像素上生成 1 像素外轮廓。"""
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


# ================= 地形 32x32 =================

def t_grass():
    img = Image.new("RGBA", (32, 32), C("green3"))
    d = ImageDraw.Draw(img)
    dither(d, (0, 0, 31, 31), "green4", 0.22, 1)
    dither(d, (0, 0, 31, 31), "green2", 0.14, 2)
    return img


def t_forest():
    img = t_grass().copy()
    d = ImageDraw.Draw(img)
    rnd = random.Random(7)
    for _ in range(6):
        cx, cy = rnd.randrange(6, 27), rnd.randrange(6, 27)
        r = rnd.randrange(4, 7)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=C("green1"))
        d.ellipse([cx - r + 1, cy - r + 1, cx + r - 1, cy + r], fill=C("green0"))
        d.ellipse([cx - r + 2, cy - r + 2, cx + 1, cy + 1], fill=C("green2"))
    return img


def t_water():
    img = Image.new("RGBA", (32, 32), C("blue1"))
    d = ImageDraw.Draw(img)
    rnd = random.Random(3)
    for y in range(1, 32, 3):
        x0 = rnd.randrange(0, 18)
        d.line([(x0, y), (x0 + 9, y)], fill=C("blue2"))
    dither(d, (0, 0, 31, 31), "blue0", 0.10, 4)
    return img


def t_sand():
    img = Image.new("RGBA", (32, 32), C("sand0"))
    d = ImageDraw.Draw(img)
    dither(d, (0, 0, 31, 31), "sand1", 0.30, 5)
    dither(d, (0, 0, 31, 31), "earth1", 0.12, 6)
    return img


def t_rock():
    img = Image.new("RGBA", (32, 32), C("gray0"))
    d = ImageDraw.Draw(img)
    rnd = random.Random(9)
    for _ in range(8):
        x, y = rnd.randrange(1, 25), rnd.randrange(1, 25)
        w, h = rnd.randrange(4, 9), rnd.randrange(3, 7)
        d.polygon([(x, y), (x + w, y + 2), (x + w - 1, y + h), (x + 1, y + h - 1)],
                  fill=C("gray1"))
        d.line([(x, y), (x + 1, y + h - 1)], fill=C("ink2"))
    return img


def t_dirt():
    img = Image.new("RGBA", (32, 32), C("earth1"))
    d = ImageDraw.Draw(img)
    dither(d, (0, 0, 31, 31), "earth0", 0.25, 11)
    dither(d, (0, 0, 31, 31), "sand0", 0.12, 12)
    return img


# ================= 建筑零件 32x32（顶视） =================

def p_roof_lit():
    """受光屋面。"""
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 2, 31, 29], fill=C("red1"))
    for y in range(6, 30, 4):
        d.line([(0, y), (31, y)], fill=C("red0"))
    dither(d, (0, 2, 31, 29), "red0", 0.10, 21)
    return outline(img)


def p_roof_shadow():
    """背光屋面。"""
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 2, 31, 29], fill=C("red0"))
    for y in range(6, 30, 4):
        d.line([(0, y), (31, y)], fill=C("ink3"))
    return outline(img)


def p_ridge():
    """屋脊。"""
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 10, 31, 16], fill=C("wood1"))
    d.rectangle([0, 10, 31, 12], fill=C("wood3"))
    d.rectangle([0, 15, 31, 16], fill=C("wood0"))
    return outline(img)


def p_wall():
    """墙体（可见的南侧一段）。"""
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 6, 31, 25], fill=C("wood2"))
    d.rectangle([0, 6, 31, 8], fill=C("wood3"))
    for x in range(3, 31, 5):
        d.line([(x, 9), (x, 25)], fill=C("wood1"))
    d.rectangle([0, 24, 31, 25], fill=C("wood0"))
    return outline(img)


def p_door():
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([10, 4, 21, 27], fill=C("wood0"))
    d.rectangle([12, 6, 19, 27], fill=C("wood1"))
    d.rectangle([18, 14, 19, 16], fill=C("gold0"))
    return outline(img)


def p_window():
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([8, 8, 23, 21], fill=C("wood0"))
    d.rectangle([10, 10, 21, 19], fill=C("blue1"))
    d.line([(15, 10), (15, 19)], fill=C("wood0"))
    d.line([(10, 14), (21, 14)], fill=C("wood0"))
    d.line([(10, 10), (21, 10)], fill=C("blue2"))
    return outline(img)


def p_chimney():
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([9, 4, 22, 27], fill=C("gray0"))
    d.rectangle([9, 4, 22, 7], fill=C("gray2"))
    dither(d, (9, 8, 22, 27), "gray1", 0.25, 31)
    d.line([(9, 14), (22, 14)], fill=C("ink3"))
    d.line([(9, 21), (22, 21)], fill=C("ink3"))
    return outline(img)


def p_fence():
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([1, 12, 30, 15], fill=C("wood2"))
    d.rectangle([1, 21, 30, 24], fill=C("wood2"))
    for x in (4, 15, 26):
        d.rectangle([x, 8, x + 3, 29], fill=C("wood1"))
        d.rectangle([x, 8, x + 3, 10], fill=C("wood3"))
    return outline(img)


# ================= 完整建筑 64x64（顶视） =================

def b_house():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 投影
    sh = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([10, 16, 58, 58], fill=(0, 0, 0, 70))
    img.alpha_composite(sh)
    # 墙（南侧）
    d.rectangle([8, 44, 54, 56], fill=C("wood2"))
    d.rectangle([8, 44, 54, 46], fill=C("wood3"))
    for x in range(12, 54, 6):
        d.line([(x, 47), (x, 56)], fill=C("wood1"))
    # 门与窗
    d.rectangle([28, 47, 36, 56], fill=C("wood0"))
    d.rectangle([34, 50, 35, 52], fill=C("gold0"))
    d.rectangle([13, 48, 21, 54], fill=C("blue1"))
    d.line([(17, 48), (17, 54)], fill=C("wood0"))
    # 屋面：上坡受光，下坡背光
    d.rectangle([6, 10, 56, 30], fill=C("red1"))
    d.rectangle([6, 30, 56, 45], fill=C("red0"))
    for y in range(13, 30, 4):
        d.line([(6, y), (56, y)], fill=C("red0"))
    for y in range(33, 45, 4):
        d.line([(6, y), (56, y)], fill=C("ink3"))
    dither(d, (6, 10, 56, 30), "red0", 0.08, 41)
    # 屋脊
    d.rectangle([4, 28, 58, 32], fill=C("wood1"))
    d.rectangle([4, 28, 58, 29], fill=C("wood3"))
    # 檐口
    d.rectangle([4, 43, 58, 46], fill=C("wood1"))
    # 烟囱
    d.rectangle([42, 12, 50, 22], fill=C("gray0"))
    d.rectangle([42, 12, 50, 14], fill=C("gray2"))
    return outline(img)


def b_farm():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 14, 61, 61], fill=C("earth0"))
    for y in range(18, 60, 6):
        d.rectangle([4, y, 59, y + 3], fill=C("green2"))
        dither(d, (4, y, 59, y + 3), "green3", 0.35, y)
        for x in range(6, 58, 6):
            d.point((x, y), fill=C("green4"))
            d.point((x + 1, y + 1), fill=C("green4"))
    # 田边小屋
    d.rectangle([22, 12, 42, 15], fill=C("wood2"))
    d.rectangle([22, 2, 42, 12], fill=C("red0"))
    d.rectangle([22, 2, 42, 7], fill=C("red1"))
    d.rectangle([22, 7, 42, 8], fill=C("wood1"))
    d.rectangle([30, 9, 34, 15], fill=C("wood0"))
    return outline(img)


def b_warehouse():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    sh = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([8, 18, 60, 60], fill=(0, 0, 0, 70))
    img.alpha_composite(sh)
    d.rectangle([4, 46, 58, 58], fill=C("wood2"))
    d.rectangle([4, 46, 58, 48], fill=C("wood3"))
    d.rectangle([18, 49, 44, 58], fill=C("wood0"))
    d.line([(31, 49), (31, 58)], fill=C("wood3"))
    # 大屋面
    d.rectangle([2, 8, 60, 32], fill=C("red0"))
    d.rectangle([2, 32, 60, 47], fill=C("red0"))
    for x in range(6, 60, 5):
        d.line([(x, 8), (x, 47)], fill=C("wood0"))
    d.rectangle([2, 8, 60, 11], fill=C("wood1"))
    dither(d, (2, 11, 60, 47), "ink3", 0.07, 51)
    d.rectangle([2, 44, 60, 47], fill=C("wood1"))
    # 天窗
    d.rectangle([24, 18, 38, 26], fill=C("blue1"))
    d.line([(31, 18), (31, 26)], fill=C("wood0"))
    return outline(img)


def b_barracks():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    sh = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([10, 20, 62, 60], fill=(0, 0, 0, 70))
    img.alpha_composite(sh)
    d.rectangle([4, 44, 56, 56], fill=C("gray1"))
    for x in range(4, 56, 8):
        d.rectangle([x, 44, x + 6, 56], fill=C("gray0"))
    d.rectangle([26, 46, 36, 56], fill=C("wood0"))
    # 平屋面：错缝砌块
    d.rectangle([2, 10, 58, 45], fill=C("gray0"))
    for row, yy in enumerate(range(11, 44, 6)):
        off = 0 if row % 2 == 0 else 7
        for x in range(2 + off, 58, 14):
            x2, y2 = min(x + 12, 57), min(yy + 5, 43)
            if x2 > x and y2 > yy:
                d.rectangle([x, yy, x2, y2], fill=C("gray1"))
    d.rectangle([2, 10, 58, 12], fill=C("gray2"))
    # 女儿墙垛口
    for x in range(2, 58, 8):
        d.rectangle([x, 6, x + 4, 11], fill=C("gray1"))
        d.rectangle([x, 6, x + 4, 7], fill=C("gray2"))
    d.rectangle([2, 43, 58, 46], fill=C("ink3"))
    # 旗杆
    d.rectangle([46, 0, 48, 14], fill=C("wood1"))
    d.polygon([(48, 2), (60, 6), (48, 11)], fill=C("red1"))
    return outline(img)


# ================= 角色 16x20（静态，无动画） =================

SKIN = "sand1"


def char_sprite(body, hair="ink1", back=False):
    img = Image.new("RGBA", (16, 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 腿
    d.rectangle([5, 16, 7, 19], fill=C("wood0"))
    d.rectangle([9, 16, 11, 19], fill=C("wood0"))
    # 躯干：肩宽腰窄
    d.rectangle([5, 9, 11, 16], fill=C(body))
    d.rectangle([4, 9, 12, 11], fill=C(body))
    # 手臂
    d.rectangle([3, 10, 4, 15], fill=C(body))
    d.rectangle([12, 10, 13, 15], fill=C(body))
    # 头
    d.ellipse([4, 1, 11, 8], fill=C(SKIN))
    # 头发
    if back:
        d.ellipse([4, 1, 11, 8], fill=C(hair))
    else:
        d.rectangle([4, 1, 11, 3], fill=C(hair))
        d.rectangle([4, 1, 5, 5], fill=C(hair))
        d.rectangle([10, 1, 11, 5], fill=C(hair))
        d.point((6, 5), fill=C("ink0"))
        d.point((9, 5), fill=C("ink0"))
    return outline(img)


# ================= 图标 16x16 =================

def i_coin():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 13, 13], fill=C("gold0"))
    d.ellipse([4, 3, 10, 9], fill=C("gold1"))
    return outline(img)


def i_wood():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 5, 13, 11], fill=C("wood2"))
    d.ellipse([11, 5, 13, 11], fill=C("wood3"))
    d.line([(4, 7), (11, 7)], fill=C("wood1"))
    d.line([(4, 9), (11, 9)], fill=C("wood1"))
    return outline(img)


def i_stone():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(3, 12), (5, 4), (11, 3), (13, 11)], fill=C("gray1"))
    d.polygon([(5, 4), (11, 3), (9, 8)], fill=C("gray2"))
    return outline(img)


def i_food():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line([(8, 14), (8, 4)], fill=C("green1"))
    for y in (5, 8, 11):
        d.ellipse([2, y, 7, y + 3], fill=C("gold0"))
        d.ellipse([9, y, 14, y + 3], fill=C("gold0"))
    return outline(img)


def i_pop():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([5, 2, 11, 8], fill=C("sand1"))
    d.polygon([(3, 14), (5, 9), (11, 9), (13, 14)], fill=C("blue2"))
    return outline(img)


def i_sword():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(12, 1), (14, 3), (6, 11), (4, 9)], fill=C("gray2"))
    d.line([(3, 13), (8, 8)], fill=C("gold0"))
    d.line([(2, 12), (5, 15)], fill=C("wood1"))
    return outline(img)


def i_scroll():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([3, 2, 12, 13], fill=C("bone0"))
    d.rectangle([3, 2, 12, 3], fill=C("earth1"))
    for y in (6, 8, 10):
        d.line([(5, y), (10, y)], fill=C("earth0"))
    return outline(img)


def i_crown():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(2, 12), (2, 5), (5, 8), (8, 3), (11, 8), (14, 5), (14, 12)], fill=C("gold0"))
    d.rectangle([2, 12, 14, 14], fill=C("gold1"))
    return outline(img)


# ================= 贵族头像 128x128 =================

def portrait(seed, mood):
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 背景斜纹
    d.rectangle([0, 0, 127, 127], fill=C("ink1"))
    for i in range(0, 128, 8):
        d.rectangle([0, i, 127, i + 3], fill=C("ink2"))
    # 肩部
    d.ellipse([24, 84, 104, 150], fill=C("purple"))
    d.ellipse([44, 96, 84, 140], fill=C("purple"))
    # 脖子
    d.rectangle([58, 70, 70, 88], fill=C("sand0"))
    # 脸
    d.ellipse([46, 28, 82, 74], fill=C(SKIN))
    # 头发
    d.ellipse([44, 24, 84, 50], fill=C("ink1"))
    d.rectangle([44, 36, 48, 54], fill=C("ink1"))
    d.rectangle([80, 36, 84, 54], fill=C("ink1"))
    # 五官
    d.rectangle([56, 48, 60, 53], fill=C("ink0"))
    d.rectangle([68, 48, 72, 53], fill=C("ink0"))
    if mood == "greed":
        d.line([(54, 43), (61, 41)], fill=C("ink0"))
        d.line([(67, 41), (74, 43)], fill=C("ink0"))
        d.line([(58, 64), (70, 62)], fill=C("wood1"))
    elif mood == "ambition":
        d.line([(54, 41), (61, 44)], fill=C("ink0"))
        d.line([(67, 44), (74, 41)], fill=C("ink0"))
        d.line([(58, 63), (70, 63)], fill=C("wood1"))
    else:
        d.line([(58, 63), (70, 63)], fill=C("wood1"))
    # 边框
    d.rectangle([0, 0, 127, 127], outline=C("gold0"))
    d.rectangle([3, 3, 124, 124], outline=C("ink0"))
    return img


# ================= 拼版 =================

W, H = 1600, 1980
sheet = Image.new("RGBA", (W, H), C("ink0"))
d = ImageDraw.Draw(sheet)

F_TITLE = font(40, bold=True)
F_H2 = font(24, bold=True)
F_BODY = font(16)
F_SMALL = font(13)

y = 34
d.text((40, y), "《敕令》美术规范 v2.0  —  EDICT ART BIBLE", font=F_TITLE, fill=C("gold1"))
y += 52
d.text((40, y), "风格基准：Songs of Syx  ·  32×32 瓦片  ·  32 色调色板  ·  顶视角  ·  光源左上  ·  1px 描边  ·  静态角色（无逐帧动画）",
       font=F_BODY, fill=C("bone0"))
y += 46


def section(title, note=""):
    global y
    d.line([(40, y), (W - 40, y)], fill=C("ink3"))
    y += 12
    d.text((40, y), title, font=F_H2, fill=C("bone1"))
    if note:
        tw = d.textlength(title, font=F_H2)
        d.text((40 + tw + 24, y + 8), note, font=F_SMALL, fill=C("gray1"))
    y += 40


def paste_scaled(img, x, top, scale):
    big = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    sheet.alpha_composite(big, (x, top))
    return big


# 调色板
section("调色板  EDICT 32 v2", "低饱和土色系，整体压暗。所有资源只能使用这 32 色")
cell_w, cell_h = 190, 92
for idx, name in enumerate(ORDER):
    col, row = idx % 8, idx // 8
    x = 40 + col * cell_w
    yy = y + row * cell_h
    d.rectangle([x, yy, x + 170, yy + 46], fill=C(name), outline=C("ink3"))
    d.text((x, yy + 52), name, font=F_SMALL, fill=C("bone0"))
    d.text((x, yy + 68), PAL[name].upper(), font=F_SMALL, fill=C("gray1"))
y += 4 * cell_h + 6

# 地形
section("地形瓦片  TERRAIN 32×32", "无描边，无缝拼接，双色抖动做纹理")
terrain = [("草地", t_grass()), ("森林", t_forest()), ("水面", t_water()),
           ("沙地", t_sand()), ("岩石", t_rock()), ("土路", t_dirt())]
for i, (label, img) in enumerate(terrain):
    x = 40 + i * 148
    paste_scaled(img, x, y, 4)
    d.text((x, y + 132), label, font=F_SMALL, fill=C("bone0"))
y += 156

# 零件
section("建筑零件  MODULAR KIT 32×32", "顶视角零件，建筑由零件拼装")
parts = [("受光屋面", p_roof_lit()), ("背光屋面", p_roof_shadow()), ("屋脊", p_ridge()),
         ("墙体", p_wall()), ("门", p_door()), ("窗", p_window()),
         ("烟囱", p_chimney()), ("栅栏", p_fence())]
for i, (label, img) in enumerate(parts):
    x = 40 + i * 108
    paste_scaled(img, x, y, 3)
    d.text((x, y + 100), label, font=F_SMALL, fill=C("bone0"))
y += 126

# 建筑
section("完整建筑  BUILDINGS 64×64", "屋顶主导的顶视角：看到的是屋面，不是正立面")
builds = [("民居", b_house()), ("农田", b_farm()),
          ("仓库", b_warehouse()), ("兵营", b_barracks())]
for i, (label, img) in enumerate(builds):
    x = 40 + i * 216
    paste_scaled(img, x, y, 3)
    d.text((x, y + 196), label, font=F_SMALL, fill=C("bone0"))
y += 224

# 角色
section("角色  CHARACTERS 16×20", "静态精灵，无逐帧动画；靠服装颜色区分职业")
chars = [("农民", char_sprite("green3")), ("工匠", char_sprite("wood2")),
         ("商人", char_sprite("blue2")), ("士兵", char_sprite("gray1")),
         ("官员", char_sprite("purple")), ("贵族", char_sprite("purple", hair="gold0")),
         ("背面", char_sprite("green3", back=True))]
for i, (label, img) in enumerate(chars):
    x = 40 + i * 100
    paste_scaled(img, x, y, 4)
    d.text((x, y + 86), label, font=F_SMALL, fill=C("bone0"))
y += 112

# 图标
section("界面图标  UI ICONS 16×16", "界面内按 2× 或 3× 整数放大")
icons = [("钱", i_coin()), ("木", i_wood()), ("石", i_stone()), ("粮", i_food()),
         ("人口", i_pop()), ("军事", i_sword()), ("政策", i_scroll()), ("王权", i_crown())]
for i, (label, img) in enumerate(icons):
    x = 40 + i * 96
    paste_scaled(img, x, y, 4)
    d.text((x, y + 70), label, font=F_SMALL, fill=C("bone0"))
y += 96

# 头像
section("贵族头像  PORTRAITS 128×128", "唯一允许 AI 生成的资源；性格靠表情与服饰")
for i, (label, mood) in enumerate([("贪婪", "greed"), ("野心", "ambition"), ("忠诚", "loyal")]):
    x = 40 + i * 300
    paste_scaled(portrait(i + 1, mood), x, y, 2)
    d.text((x, y + 262), label, font=F_SMALL, fill=C("bone0"))
y += 286

d.text((40, H - 32), "生成：art/tools/gen_style_sheet.py   ·   《敕令》Edict   ·   2026-11",
       font=F_SMALL, fill=C("gray1"))

out = os.path.join(OUT_DIR, "style_sheet.png")
sheet.convert("RGB").save(out)
print("saved:", out, sheet.size)
