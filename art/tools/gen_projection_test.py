# -*- coding: utf-8 -*-
"""《敕令》投影方案对比图 v5。

对比三种建筑投影 + 写实阴影写法 + 俯视角色 + 写实头像。
输出 art/preview/projection_test.png
"""
import os
import random
from PIL import Image, ImageDraw, ImageFont

ROOT = r"D:\Work\edict"
OUT = os.path.join(ROOT, "art", "preview")
os.makedirs(OUT, exist_ok=True)

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
        try:
            return ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", size)
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


def cast_shadow(img, box, dx, dy, alpha=90, spread=3):
    """投影：主体实心 + 边缘抖动软化。"""
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


def ao(d, box, color, w=3):
    """内缘环境光遮蔽：四周向内压暗。"""
    x0, y0, x1, y1 = box
    for i in range(w):
        a = 1.0 - i / w
        d.rectangle([x0 + i, y0 + i, x1 - i, y0 + i], fill=C(color))
        d.rectangle([x0 + i, y1 - i, x1 - i, y1 - i], fill=C(color))


def rim(d, box, color, w=2):
    """左上边缘受光。"""
    x0, y0, x1, y1 = box
    for i in range(w):
        d.line([(x0 + i, y0 + i), (x1 - i, y0 + i)], fill=C(color))
        d.line([(x0 + i, y0 + i), (x0 + i, y1 - i)], fill=C(color))


def roof(d, box, base, hi, lo, th=8, tw=16):
    """横向叠瓦：亮顶边 + 暗底边 + 错缝短竖线。"""
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


# ================= A. 纯屋顶 =================

def house_A(S=192):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cast_shadow(img, (16, 16, 176, 176), 8, 9, 95, 4)
    # 檐口
    d.rectangle([14, 14, 178, 178], fill=C("wood2"))
    d.rectangle([14, 14, 178, 17], fill=C("wood4"))
    d.rectangle([14, 175, 178, 178], fill=C("wood0"))
    # 上坡
    roof(d, (18, 18, 174, 94), "red2", "red3", "red1", 8, 16)
    # 下坡
    roof(d, (18, 94, 174, 174), "red1", "red2", "red0", 8, 16)
    # 屋脊
    d.rectangle([16, 90, 176, 99], fill=C("wood2"))
    d.rectangle([16, 90, 176, 92], fill=C("wood4"))
    d.rectangle([16, 97, 176, 99], fill=C("wood0"))
    # 屋脊下方 AO
    d.rectangle([18, 99, 174, 103], fill=C("red0"))
    # 烟囱
    d.rectangle([128, 34, 156, 74], fill=C("gray2"))
    d.rectangle([128, 34, 156, 38], fill=C("gray4"))
    d.rectangle([128, 34, 131, 74], fill=C("gray3"))
    d.rectangle([153, 34, 156, 74], fill=C("gray1"))
    d.rectangle([133, 40, 151, 52], fill=C("ink1"))
    d.rectangle([131, 74, 158, 78], fill=C("ink2"))
    # 天窗
    d.rectangle([58, 112, 96, 142], fill=C("wood2"))
    d.rectangle([61, 115, 93, 139], fill=C("blue2"))
    d.rectangle([61, 115, 93, 119], fill=C("blue3"))
    d.line([(77, 115), (77, 139)], fill=C("wood2"))
    return img


# ================= B. 只见墙（俯视看墙体厚度 + 内部地面） =================

def house_B(S=192):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cast_shadow(img, (16, 16, 176, 176), 8, 9, 95, 4)
    # 外墙（厚 14）
    d.rectangle([14, 14, 178, 178], fill=C("gray2"))
    d.rectangle([14, 14, 178, 17], fill=C("gray4"))
    d.rectangle([14, 14, 17, 178], fill=C("gray3"))
    d.rectangle([14, 175, 178, 178], fill=C("gray0"))
    d.rectangle([175, 14, 178, 178], fill=C("gray1"))
    dither(d, (14, 14, 178, 178), "gray1", 0.18, 3)
    # 室内地面
    d.rectangle([28, 28, 164, 164], fill=C("earth1"))
    dither(d, (28, 28, 164, 164), "earth0", 0.28, 5)
    # 内缘 AO
    for i in range(6):
        d.rectangle([28 + i, 28 + i, 164 - i, 28 + i], fill=C("earth0"))
        d.rectangle([28 + i, 164 - i, 164 - i, 164 - i], fill=C("earth0"))
    # 床
    d.rectangle([40, 44, 92, 84], fill=C("wood2"))
    d.rectangle([40, 44, 92, 48], fill=C("wood4"))
    d.rectangle([44, 50, 88, 80], fill=C("bone0"))
    dither(d, (44, 50, 88, 80), "bone1", 0.3, 9)
    # 桌
    d.rectangle([108, 48, 148, 80], fill=C("wood3"))
    d.rectangle([108, 48, 148, 51], fill=C("wood4"))
    d.ellipse([118, 56, 138, 72], fill=C("gray2"))
    # 火塘
    d.ellipse([104, 108, 148, 148], fill=C("gray1"))
    d.ellipse([110, 114, 142, 142], fill=C("ink2"))
    d.ellipse([116, 120, 136, 136], fill=C("red3"))
    d.ellipse([121, 125, 131, 131], fill=C("gold1"))
    # 门洞（南墙开口）
    d.rectangle([80, 164, 112, 178], fill=C("earth1"))
    d.rectangle([80, 164, 112, 168], fill=C("earth0"))
    return img


# ================= C. 屋顶 + 南墙（斜俯视，Syx 式） =================

def house_C(S=192):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cast_shadow(img, (16, 16, 176, 178), 8, 9, 95, 4)
    # 南墙
    d.rectangle([16, 126, 176, 178], fill=C("bone0"))
    dither(d, (16, 126, 176, 178), "sand1", 0.22, 11)
    # 木构架
    for x in (16, 52, 100, 148, 172):
        d.rectangle([x, 126, x + 6, 178], fill=C("wood2"))
    d.rectangle([16, 126, 176, 132], fill=C("wood2"))
    d.rectangle([16, 126, 176, 128], fill=C("wood4"))
    # 门
    d.rectangle([74, 136, 104, 178], fill=C("wood1"))
    d.rectangle([77, 139, 101, 178], fill=C("wood2"))
    d.line([(89, 139), (89, 178)], fill=C("wood1"))
    d.rectangle([95, 154, 99, 159], fill=C("gold1"))
    # 窗
    for wx in (28, 118):
        d.rectangle([wx, 142, wx + 22, 162], fill=C("wood1"))
        d.rectangle([wx + 3, 145, wx + 19, 159], fill=C("blue2"))
        d.rectangle([wx + 3, 145, wx + 19, 147], fill=C("blue3"))
        d.line([(wx + 11, 145), (wx + 11, 159)], fill=C("wood1"))
    # 墙脚阴影
    d.rectangle([16, 174, 176, 178], fill=C("earth0"))
    # 屋顶
    d.rectangle([10, 12, 182, 130], fill=C("wood2"))
    d.rectangle([10, 12, 182, 15], fill=C("wood4"))
    roof(d, (14, 16, 178, 70), "red2", "red3", "red1", 8, 16)
    roof(d, (14, 70, 178, 124), "red1", "red2", "red0", 8, 16)
    d.rectangle([12, 66, 180, 75], fill=C("wood2"))
    d.rectangle([12, 66, 180, 68], fill=C("wood4"))
    d.rectangle([12, 73, 180, 75], fill=C("wood0"))
    # 檐口阴影落在墙上
    d.rectangle([16, 124, 176, 130], fill=C("ink2"))
    dither(d, (16, 128, 176, 132), "sand1", 0.4, 13)
    # 烟囱
    d.rectangle([132, 28, 158, 64], fill=C("gray2"))
    d.rectangle([132, 28, 158, 31], fill=C("gray4"))
    d.rectangle([132, 28, 135, 64], fill=C("gray3"))
    d.rectangle([136, 34, 154, 44], fill=C("ink1"))
    return img


# ================= 角色：只看到头顶 =================

def char_top(hair="ink1", cloth="green3", hat=None):
    S = 32
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 投影
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([7, 9, 26, 28], fill=(0, 0, 0, 110))
    img.alpha_composite(sh)
    # 肩（俯视看到的身体轮廓）
    d.ellipse([5, 12, 27, 28], fill=C(cloth))
    d.ellipse([7, 14, 25, 26], fill=C(cloth))
    # 头顶
    d.ellipse([8, 4, 24, 21], fill=C(hair))
    d.ellipse([10, 6, 22, 19], fill=C(hair))
    # 头顶高光（左上）
    d.arc([9, 5, 23, 20], 190, 300, fill=C("ink3"), width=2)
    # 前方露出一点额头
    d.arc([11, 12, 21, 22], 20, 160, fill=C("clay0"), width=3)
    return img


# ================= 写实头像 256 =================

def portrait_real(mood):
    S = 256
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], fill=C("ink1"))
    for i in range(0, S, 14):
        d.rectangle([0, i, S - 1, i + 5], fill=C("ink2"))
    # 肩
    d.ellipse([6, 182, 250, 340], fill=C("purple"))
    d.ellipse([70, 200, 186, 300], fill=C("ink2"))
    # 脖子 + 下颌阴影
    d.rectangle([112, 146, 146, 196], fill=C("clay0"))
    d.rectangle([112, 146, 146, 160], fill=C("earth2"))
    d.rectangle([112, 180, 146, 196], fill=C("earth2"))
    # 脸：底色
    d.ellipse([84, 34, 174, 172], fill=C("clay0"))
    d.ellipse([94, 108, 164, 178], fill=C("clay0"))
    # 额头受光
    d.ellipse([94, 42, 164, 106], fill=C("sand2"))
    # 侧面阴影
    d.arc([84, 34, 174, 172], 200, 340, fill=C("earth2"), width=5)
    d.arc([94, 108, 164, 178], 300, 360, fill=C("earth2"), width=4)
    # 颧骨下方阴影
    d.arc([96, 118, 160, 172], 30, 150, fill=C("earth2"), width=3)
    # 头发
    d.ellipse([80, 22, 178, 100], fill=C("ink1"))
    d.rectangle([80, 60, 92, 128], fill=C("ink1"))
    d.rectangle([166, 60, 178, 128], fill=C("ink1"))
    dither(d, (88, 30, 170, 92), "ink2", 0.16, 3)
    d.arc([86, 26, 172, 96], 200, 320, fill=C("ink3"), width=2)
    # 眉
    if mood == "greed":
        d.polygon([(96, 100), (124, 93), (124, 99), (96, 106)], fill=C("ink0"))
        d.polygon([(134, 93), (162, 100), (162, 106), (134, 99)], fill=C("ink0"))
    elif mood == "ambition":
        d.polygon([(96, 94), (124, 100), (124, 106), (96, 100)], fill=C("ink0"))
        d.polygon([(134, 100), (162, 94), (162, 100), (134, 106)], fill=C("ink0"))
    else:
        d.rectangle([96, 98, 124, 102], fill=C("ink0"))
        d.rectangle([134, 98, 162, 102], fill=C("ink0"))
    # 眼窝阴影
    for ex in (96, 134):
        d.ellipse([ex - 2, 106, ex + 28, 128], fill=C("earth2"))
    # 眼
    for ex in (96, 134):
        d.ellipse([ex, 110, ex + 26, 124], fill=C("bone0"))
        d.ellipse([ex + 7, 110, ex + 19, 124], fill=C("sand1"))
        d.ellipse([ex + 9, 111, ex + 17, 123], fill=C("ink2"))
        d.ellipse([ex + 11, 113, ex + 15, 121], fill=C("ink0"))
        d.rectangle([ex + 11, 114, ex + 12, 116], fill=C("bone1"))
        d.line([(ex, 110), (ex + 26, 110)], fill=C("ink1"))
        d.line([(ex + 2, 124), (ex + 24, 124)], fill=C("earth2"))
    # 鼻
    d.polygon([(126, 112), (134, 112), (133, 148), (127, 148)], fill=C("sand2"))
    d.polygon([(133, 112), (134, 112), (133, 148), (132, 148)], fill=C("earth2"))
    d.rectangle([120, 148, 140, 152], fill=C("earth2"))
    d.rectangle([122, 152, 138, 155], fill=C("clay0"))
    d.point((121, 149), fill=C("ink2"))
    d.point((139, 149), fill=C("ink2"))
    # 嘴
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
    # 下巴阴影
    d.arc([104, 150, 154, 182], 20, 160, fill=C("earth2"), width=3)
    # 衣领
    d.polygon([(78, 190), (114, 166), (142, 166), (178, 190)], fill=C("ink1"))
    d.polygon([(78, 190), (114, 166), (114, 186)], fill=C("ink2"))
    d.rectangle([122, 174, 134, 210], fill=C("gold0"))
    d.ellipse([116, 204, 140, 228], fill=C("gold1"))
    d.ellipse([123, 211, 133, 221], fill=C("gold0"))
    # 边框
    d.rectangle([0, 0, S - 1, S - 1], outline=C("gold0"))
    d.rectangle([3, 3, S - 4, S - 4], outline=C("ink0"))
    return img


# ================= 拼版 =================

W, HCAP = 1800, 2600
sheet = Image.new("RGBA", (W, HCAP), C("ink0"))
d = ImageDraw.Draw(sheet)
F_T = font(40, True)
F_H = font(24, True)
F_B = font(16)
F_S = font(14)

y = 30
d.text((40, y), "《敕令》投影方案对比  v5", font=F_T, fill=C("gold1"))
y += 50
d.text((40, y), "同一栋民居，三种投影。请选一个，我按它重画全部建筑。", font=F_B, fill=C("bone0"))
y += 46


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


sec("三种投影方案", "选一个：A 纯屋顶 / B 只见墙 / C 屋顶+南墙")

variants = [
    ("A  纯屋顶", house_A(), "从上往下只看到屋面。俯视最纯粹，但建筑辨识度最低。"),
    ("B  只见墙", house_B(), "看到墙的厚度和屋内地面。信息量最大，但像平面图。"),
    ("C  屋顶+南墙", house_C(), "屋面为主，南墙露出。希克斯之歌的写法，立体感最强。"),
]
for i, (label, img, desc) in enumerate(variants):
    x = 40 + i * 580
    put(img, x, y, 2.0)
    d.text((x, y + 396), label, font=F_H, fill=C("gold1"))
    d.text((x, y + 428), desc, font=F_S, fill=C("gray3"))
y += 470

sec("角色（只看到头顶）", "俯视：头发顶 + 肩背轮廓 + 前方额头")
chars = [("农民", char_top("ink1", "green3")), ("工匠", char_top("ink1", "wood2")),
         ("商人", char_top("ink1", "blue2")), ("士兵", char_top("gray1", "gray1")),
         ("官员", char_top("ink1", "purple")), ("贵族", char_top("gold0", "purple"))]
for i, (label, img) in enumerate(chars):
    x = 40 + i * 150
    put(img, x, y, 4)
    d.text((x, y + 140), label, font=F_S, fill=C("bone0"))
y += 176

sec("写实头像 256×256", "靠阴影分面：额光、颧影、眼窝、鼻侧、唇下")
for i, (label, mood) in enumerate([("贪婪", "greed"), ("野心", "ambition"), ("忠诚", "loyal")]):
    x = 40 + i * 290
    put(portrait_real(mood), x, y, 1.0)
    d.text((x, y + 262), label, font=F_S, fill=C("bone0"))
y += 300

sec("调色板  EDICT 40", "扩到 40 色，为写实阴影补足色阶")
cell_w, cell_h = 175, 96
for idx, name in enumerate(ORDER):
    col, row = idx % 10, idx // 10
    x = 40 + col * cell_w
    yy = y + row * cell_h
    d.rectangle([x, yy, x + 155, yy + 48], fill=C(name), outline=C("ink3"))
    d.text((x, yy + 54), name, font=F_S, fill=C("bone0"))
    d.text((x, yy + 70), PAL[name].upper(), font=F_S, fill=C("gray2"))
y += 4 * cell_h + 10

d.text((40, y + 10), "《敕令》Edict  ·  2026-11  ·  gen_projection_test.py", font=F_S, fill=C("gray2"))
sheet = sheet.crop((0, 0, W, y + 60))
out = os.path.join(OUT, "projection_test.png")
sheet.convert("RGB").save(out)
print("saved:", out, sheet.size)
