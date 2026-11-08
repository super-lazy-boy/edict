# -*- coding: utf-8 -*-
"""《敕令》美术规范参考图生成器。

输出 art/preview/style_sheet.png，用于人工验收风格。
所有图形全部由代码生成，只使用 Edict 32 调色板内的颜色。
"""
import os
import random
from PIL import Image, ImageDraw, ImageFont

ROOT = r"D:\Work\edict"
OUT_DIR = os.path.join(ROOT, "art", "preview")
os.makedirs(OUT_DIR, exist_ok=True)

PAL = {
    "ink0": "#14121A", "ink1": "#241F2B", "ink2": "#35303D", "ink3": "#4A4351",
    "gray0": "#6B6472", "gray1": "#8F8896", "gray2": "#BDB6C2", "paper": "#EDE7F0",
    "green0": "#2A3B22", "green1": "#3B5230", "green2": "#4F6B3A",
    "green3": "#668547", "green4": "#7FA055", "green5": "#9DBC6C",
    "blue0": "#1E3A5F", "blue1": "#2B5382", "blue2": "#3A70A8", "blue3": "#5A94C4",
    "earth0": "#6B5B45", "earth1": "#8A7859", "sand0": "#B5A382", "sand1": "#D6C9A8",
    "wood0": "#4A3222", "wood1": "#6B4A30", "wood2": "#8F6642", "wood3": "#B08556",
    "red0": "#7A2E24", "red1": "#A84433", "red2": "#D4693F",
    "purple": "#5A3E7A", "gold0": "#C9A227", "gold1": "#F0D060",
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


# ---------------- 地形瓦片 32x32 ----------------

def t_grass():
    img = Image.new("RGBA", (32, 32), C("green3"))
    rnd = random.Random(1)
    px = img.load()
    for _ in range(90):
        x, y = rnd.randrange(32), rnd.randrange(32)
        px[x, y] = C(rnd.choice(["green2", "green4", "green4", "green5"]))
    return img


def t_forest():
    img = t_grass().copy()
    d = ImageDraw.Draw(img)
    rnd = random.Random(7)
    for _ in range(5):
        cx, cy = rnd.randrange(7, 26), rnd.randrange(7, 26)
        r = rnd.randrange(5, 8)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=C("green1"))
        d.ellipse([cx - r + 2, cy - r + 2, cx + r - 2, cy + r - 1], fill=C("green2"))
        d.ellipse([cx - r + 3, cy - r + 3, cx + r - 4, cy + r - 3], fill=C("green0"))
    return img


def t_water():
    img = Image.new("RGBA", (32, 32), C("blue1"))
    d = ImageDraw.Draw(img)
    rnd = random.Random(3)
    for i in range(1, 32, 4):
        x0 = rnd.randrange(0, 14)
        d.line([(x0, i), (x0 + 11, i)], fill=C("blue2"))
    for i in range(3, 32, 7):
        d.line([(0, i), (7, i)], fill=C("blue0"))
    return img


def t_sand():
    img = Image.new("RGBA", (32, 32), C("sand0"))
    rnd = random.Random(5)
    px = img.load()
    for _ in range(80):
        x, y = rnd.randrange(32), rnd.randrange(32)
        px[x, y] = C(rnd.choice(["sand1", "sand1", "earth1"]))
    return img


def t_rock():
    img = Image.new("RGBA", (32, 32), C("gray0"))
    d = ImageDraw.Draw(img)
    rnd = random.Random(9)
    for _ in range(7):
        x, y = rnd.randrange(1, 25), rnd.randrange(1, 25)
        w, h = rnd.randrange(5, 10), rnd.randrange(4, 8)
        d.polygon([(x, y), (x + w, y + 2), (x + w - 1, y + h), (x + 1, y + h - 1)],
                  fill=C("gray1"))
        d.line([(x, y), (x + 1, y + h - 1)], fill=C("ink2"))
    return img


def t_dirt():
    img = Image.new("RGBA", (32, 32), C("earth1"))
    rnd = random.Random(11)
    px = img.load()
    for _ in range(70):
        x, y = rnd.randrange(32), rnd.randrange(32)
        px[x, y] = C(rnd.choice(["earth0", "sand0", "wood1"]))
    return img


# ---------------- 描边 ----------------

def outline(img, color=None, only_edge=True):
    """在透明像素上生成 1 像素外轮廓。"""
    color = color or C("ink0")
    w, h = img.size
    src = img.load()
    out = img.copy()
    dst = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y][3] != 0:
                continue
            hit = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and src[nx, ny][3] != 0:
                    hit = True
                    break
            if hit:
                dst[x, y] = color
    return out


# ---------------- 建筑零件 32x32 ----------------

def p_wall_wood():
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 4, 29, 31], fill=C("wood2"))
    d.rectangle([2, 4, 29, 6], fill=C("wood3"))
    for x in range(5, 29, 5):
        d.line([(x, 7), (x, 31)], fill=C("wood1"))
    d.rectangle([2, 29, 29, 31], fill=C("wood0"))
    return outline(img)


def p_wall_stone():
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 4, 29, 31], fill=C("gray1"))
    for row, y in enumerate(range(4, 31, 6)):
        off = 0 if row % 2 == 0 else 5
        for x in range(2 + off, 30, 10):
            d.rectangle([x, y, min(x + 8, 29), y + 5], fill=C("gray0"))
            d.line([(x, y), (min(x + 8, 29), y)], fill=C("gray2"))
    return outline(img)


def p_roof_thatch():
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(0, 30), (16, 3), (31, 30)], fill=C("sand0"))
    d.polygon([(0, 30), (16, 3), (16, 30)], fill=C("sand1"))
    for i, y in enumerate(range(8, 31, 5)):
        d.line([(2 + i * 2, y), (29 - i * 2, y)], fill=C("earth1"))
    return outline(img)


def p_roof_tile():
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(0, 30), (16, 3), (31, 30)], fill=C("red1"))
    d.polygon([(0, 30), (16, 3), (16, 30)], fill=C("red2"))
    for i, y in enumerate(range(9, 31, 5)):
        d.line([(2 + i * 2, y), (29 - i * 2, y)], fill=C("red0"))
    return outline(img)


def p_door():
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([10, 8, 21, 31], fill=C("wood0"))
    d.rectangle([12, 10, 19, 31], fill=C("wood1"))
    d.rectangle([18, 18, 19, 20], fill=C("gold0"))
    return outline(img)


def p_window():
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([8, 9, 23, 22], fill=C("wood0"))
    d.rectangle([10, 11, 21, 20], fill=C("blue2"))
    d.line([(15, 11), (15, 20)], fill=C("wood0"))
    d.line([(10, 15), (21, 15)], fill=C("wood0"))
    d.line([(10, 11), (21, 11)], fill=C("blue3"))
    return outline(img)


def p_chimney():
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([10, 6, 21, 31], fill=C("gray0"))
    d.rectangle([10, 6, 21, 9], fill=C("gray2"))
    d.line([(10, 14), (21, 14)], fill=C("ink3"))
    d.line([(10, 22), (21, 22)], fill=C("ink3"))
    return outline(img)


def p_fence():
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([1, 14, 30, 17], fill=C("wood2"))
    d.rectangle([1, 22, 30, 25], fill=C("wood2"))
    for x in (4, 15, 26):
        d.rectangle([x, 10, x + 3, 30], fill=C("wood1"))
        d.rectangle([x, 10, x + 3, 12], fill=C("wood3"))
    return outline(img)


# ---------------- 完整建筑 64x64 ----------------

def b_house():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([7, 52, 56, 58], fill=C("earth0"))
    d.rectangle([9, 28, 54, 53], fill=C("wood2"))
    for x in range(13, 54, 6):
        d.line([(x, 29), (x, 52)], fill=C("wood1"))
    d.rectangle([27, 38, 37, 53], fill=C("wood0"))
    d.rectangle([34, 44, 36, 47], fill=C("gold0"))
    d.rectangle([13, 33, 21, 41], fill=C("blue2"))
    d.line([(17, 33), (17, 41)], fill=C("wood0"))
    d.line([(13, 37), (21, 37)], fill=C("wood0"))
    d.polygon([(3, 32), (32, 5), (60, 32)], fill=C("red1"))
    d.polygon([(3, 32), (32, 5), (32, 32)], fill=C("red2"))
    for i, y in enumerate(range(11, 32, 5)):
        d.line([(3 + i * 3, y), (60 - i * 3, y)], fill=C("red0"))
    d.rectangle([44, 11, 51, 22], fill=C("gray0"))
    d.rectangle([44, 11, 51, 13], fill=C("gray2"))
    return outline(img)


def b_farm():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 18, 61, 61], fill=C("earth1"))
    for y in range(22, 60, 6):
        d.rectangle([4, y, 59, y + 3], fill=C("green4"))
        for x in range(6, 58, 7):
            d.rectangle([x, y - 1, x + 2, y + 2], fill=C("green5"))
    d.rectangle([22, 4, 42, 20], fill=C("wood2"))
    d.polygon([(19, 6), (32, -2), (45, 6)], fill=C("sand0"))
    d.rectangle([29, 10, 35, 20], fill=C("wood0"))
    return outline(img)


def b_warehouse():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([3, 50, 60, 58], fill=C("earth0"))
    d.rectangle([5, 24, 58, 52], fill=C("wood2"))
    for x in range(9, 58, 5):
        d.line([(x, 25), (x, 51)], fill=C("wood1"))
    d.rectangle([18, 30, 45, 52], fill=C("wood0"))
    d.line([(31, 30), (31, 52)], fill=C("wood3"))
    d.rectangle([3, 22, 60, 26], fill=C("wood1"))
    d.polygon([(2, 22), (31, 8), (61, 22)], fill=C("red0"))
    d.rectangle([8, 8, 14, 22], fill=C("gray0"))
    return outline(img)


def b_barracks():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 52, 61, 59], fill=C("ink2"))
    d.rectangle([4, 26, 59, 54], fill=C("gray1"))
    for row, y in enumerate(range(26, 54, 7)):
        off = 0 if row % 2 == 0 else 6
        for x in range(4 + off, 60, 13):
            d.rectangle([x, y, min(x + 11, 59), y + 6], fill=C("gray0"))
    d.rectangle([26, 36, 37, 54], fill=C("wood0"))
    d.rectangle([11, 32, 20, 41], fill=C("ink1"))
    d.rectangle([43, 32, 52, 41], fill=C("ink1"))
    d.rectangle([2, 24, 61, 27], fill=C("gray2"))
    d.rectangle([44, 2, 46, 24], fill=C("wood1"))
    d.polygon([(46, 3), (60, 8), (46, 14)], fill=C("red2"))
    return outline(img)


# ---------------- 界面图标 16x16 ----------------

def i_coin():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 13, 13], fill=C("gold0"))
    d.ellipse([4, 3, 11, 10], fill=C("gold1"))
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
    d.rectangle([3, 2, 12, 13], fill=C("sand1"))
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


# ---------------- 贵族头像 128x128 ----------------

def portrait(seed, mood):
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 127, 127], fill=C("ink1"))
    for i in range(0, 128, 8):
        d.rectangle([0, i, 127, i + 3], fill=C("ink2"))
    d.ellipse([30, 96, 98, 150], fill=C("purple"))
    d.ellipse([46, 34, 82, 76], fill=C("sand0"))
    d.rectangle([54, 72, 74, 90], fill=C("sand0"))
    rnd = random.Random(seed)
    eye = C("ink0")
    d.rectangle([56, 50, 60, 54], fill=eye)
    d.rectangle([68, 50, 72, 54], fill=eye)
    if mood == "greed":
        d.line([(54, 46), (62, 44)], fill=C("ink1"))
        d.line([(66, 44), (74, 46)], fill=C("ink1"))
    elif mood == "ambition":
        d.line([(54, 44), (62, 47)], fill=C("ink1"))
        d.line([(66, 47), (74, 44)], fill=C("ink1"))
    d.line([(58, 66), (70, 66)], fill=C("wood1"))
    d.rectangle([0, 0, 127, 127], outline=C("gold0"))
    d.rectangle([3, 3, 124, 124], outline=C("ink0"))
    return img


# ---------------- 拼版 ----------------

W, H = 1600, 1860
sheet = Image.new("RGBA", (W, H), C("ink0"))
d = ImageDraw.Draw(sheet)

F_TITLE = font(40, bold=True)
F_H2 = font(24, bold=True)
F_BODY = font(16)
F_SMALL = font(13)

y = 36
d.text((40, y), "《敕令》美术规范 v1.0  —  EDICT ART BIBLE", font=F_TITLE, fill=C("gold1"))
y += 54
d.text((40, y), "32×32 瓦片 · 32 色调色板 · 3/4 俯视 · 光源左上 · 1 像素深色描边 · 禁止抗锯齿",
       font=F_BODY, fill=C("gray2"))
y += 48


def section(title, note=""):
    global y
    d.line([(40, y), (W - 40, y)], fill=C("ink2"))
    y += 12
    d.text((40, y), title, font=F_H2, fill=C("paper"))
    if note:
        tw = d.textlength(title, font=F_H2)
        d.text((40 + tw + 24, y + 8), note, font=F_SMALL, fill=C("gray0"))
    y += 40


def paste_scaled(img, x, top, scale):
    big = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    sheet.alpha_composite(big, (x, top))
    return big


# --- 调色板 ---
section("调色板  EDICT 32", "所有资源只能使用这 32 色，禁止新增")
cell_w, cell_h = 190, 92
for idx, name in enumerate(ORDER):
    col, row = idx % 8, idx // 8
    x = 40 + col * cell_w
    yy = y + row * cell_h
    d.rectangle([x, yy, x + 170, yy + 46], fill=C(name), outline=C("ink2"))
    d.text((x, yy + 52), name, font=F_SMALL, fill=C("gray2"))
    d.text((x, yy + 68), PAL[name].upper(), font=F_SMALL, fill=C("gray0"))
y += 4 * cell_h + 10

# --- 地形 ---
section("地形瓦片  TERRAIN 32×32", "无描边，无缝拼接")
terrain = [("草地", t_grass()), ("森林", t_forest()), ("水面", t_water()),
           ("沙地", t_sand()), ("岩石", t_rock()), ("土路", t_dirt())]
for i, (label, img) in enumerate(terrain):
    x = 40 + i * 148
    paste_scaled(img, x, y, 4)
    d.text((x, y + 132), label, font=F_SMALL, fill=C("gray2"))
y += 158

# --- 零件 ---
section("建筑零件  MODULAR KIT 32×32", "建筑由零件拼装，不整栋生成")
parts = [("木墙", p_wall_wood()), ("石墙", p_wall_stone()), ("茅草顶", p_roof_thatch()),
         ("瓦片顶", p_roof_tile()), ("门", p_door()), ("窗", p_window()),
         ("烟囱", p_chimney()), ("栅栏", p_fence())]
for i, (label, img) in enumerate(parts):
    x = 40 + i * 108
    paste_scaled(img, x, y, 3)
    d.text((x, y + 100), label, font=F_SMALL, fill=C("gray2"))
y += 128

# --- 建筑 ---
section("完整建筑  BUILDINGS 64×64", "由零件拼装 + 统一描边")
builds = [("民居", b_house()), ("农田", b_farm()),
          ("仓库", b_warehouse()), ("兵营", b_barracks())]
for i, (label, img) in enumerate(builds):
    x = 40 + i * 216
    paste_scaled(img, x, y, 3)
    d.text((x, y + 196), label, font=F_SMALL, fill=C("gray2"))
y += 226

# --- 图标 ---
section("界面图标  UI ICONS 16×16", "界面内按 2× 或 3× 整数放大")
icons = [("钱", i_coin()), ("木", i_wood()), ("石", i_stone()), ("粮", i_food()),
         ("人口", i_pop()), ("军事", i_sword()), ("政策", i_scroll()), ("王权", i_crown())]
for i, (label, img) in enumerate(icons):
    x = 40 + i * 96
    paste_scaled(img, x, y, 4)
    d.text((x, y + 70), label, font=F_SMALL, fill=C("gray2"))
y += 98

# --- 头像 ---
section("贵族头像  PORTRAITS 128×128", "体现性格，AI 生成后按此规格裁切")
for i, (label, mood) in enumerate([("贪婪", "greed"), ("野心", "ambition"), ("忠诚", "loyal")]):
    x = 40 + i * 300
    paste_scaled(portrait(i + 1, mood), x, y, 2)
    d.text((x, y + 262), label, font=F_SMALL, fill=C("gray2"))
y += 290

d.text((40, H - 34), "生成：art/tools/gen_style_sheet.py   ·   《敕令》Edict   ·   2026-11",
       font=F_SMALL, fill=C("gray0"))

out = os.path.join(OUT_DIR, "style_sheet.png")
sheet.convert("RGB").save(out)
print("saved:", out, sheet.size)
