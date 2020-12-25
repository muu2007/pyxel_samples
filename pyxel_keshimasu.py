import csv
import os
import re

import pyxel


class BDF:
    def __init__(self, fn):  # if fn is list -> combine 2bdf fonts
        def read(fn):
            with open(fn) as f:
                bdf = f.read()
            if m := re.search(r'FONTBOUNDINGBOX\s(-?\d+)\s(-?\d+)\s(-?\d+)\s(-?\d+)', bdf):  # linefeed
                self.bbox = [int(v) for v in m.groups()]
            for m in re.finditer(r'ENCODING\s(\d+)\nSWIDTH.*?\nDWIDTH\s(\d+)\s(\d+)\nBBX\s(\d+)\s(\d+)\s(-?\d+)\s(-?\d+)\nBITMAP\n([0-9a-fA-F\n]*?)\n?ENDCHAR\n', bdf, re.MULTILINE):
                self.chars[int(m.group(1))] = {'dwidth': (int(m.group(2)), int(m.group(3))), 'bbx': (int(m.group(4)), int(m.group(5)), int(m.group(6)), int(m.group(7))), 'glyph': m.group(8).split()}
            print(len(self.chars))
        self.chars = {10: {'dwidth': (0, 0), 'bbx': (0, 0, 0, 0), 'glyph': []}}
        self.fx, self.fy = 0, 0  # 追加の文字間隔、行間
        read(fn) if type(fn) is str else [read(s) for s in fn]

    def points(self, s, x=0, y=0):  # 注意:再帰呼出し以外からはx,yを指定しないで下さい
        def letter(dwidth, bbx, glyph):  # dwidth使ってないが、引数展開で呼び出すので省略や_にできない
            Bits = {'0': [], '1': [3], '2': [2], '3': [2, 3], '4': [1], '5': [1, 3], '6': [1, 2], '7': [1, 2, 3], '8': [0], '9': [0, 3], 'A': [0, 2], 'B': [0, 2, 3], 'C': [0, 1], 'D': [0, 1, 3], 'E': [0, 1, 2], 'F': [0, 1, 2, 3], 'a': [0, 2], 'b': [0, 2, 3], 'c': [0, 1], 'd': [0, 1, 3], 'e': [0, 1, 2], 'f': [0, 1, 2, 3]}
            sx, sy = x + bbx[2], y + self.bbox[1] + self.bbox[3] - bbx[1] - bbx[3]
            return sum([sum([[(sx+i*4+bit, sy+j) for bit in Bits[c]] for i, c in enumerate(row)], []) for j, row in enumerate(glyph)], [])  # sum = flatten
        s = [u for u in s if ord(u) in self.chars.keys()]
        return [] if not s else letter(**self.chars[ord(s[0])]) + self.points(s[1:], 0 if s[0] == '\n' else x+self.chars[ord(s[0])]['dwidth'][0]+self.fx, y if s[0] != '\n' else y+self.bbox[1]+self.fy)

    def box(self, s):  # 改行未対応
        s = [u for u in s if ord(u) in self.chars.keys()]
        return (sum([self.chars[ord(c)]["dwidth"][0] for c in s]) + self.fx*len(s), self.bbox[1])


class LineEditor:
    def __init__(self, fn):
        with open(fn, encoding='utf-8') as f:
            self.table = {row[0]: (row[1], row[2] if len(row) > 2 else "") for row in csv.reader(f, delimiter='\t')}
            del self.table["n"]
            print(self.table['a'])
            # print(pyxel.KEY_A)
        self.clear()

    def clear(self): self.text, self.state = "", ""

    def input(self, c):
        self.state += c
        if self.state in self.table:
            self.text += self.table[self.state][0]
            self.state = self.table[self.state][1]

    def bs(self):
        if len(self.state) > 0:
            self.state = self.state[:-1]
        elif len(self.text) > 0:
            self.text = self.text[:-1]

    def update(self):
        if pyxel.btnr(pyxel.KEY_MINUS):
            self.input("-")
        for k in range(pyxel.KEY_A, pyxel.KEY_Z+1):
            if pyxel.btnr(k):
                self.input(chr(k-18+97))  # _A=18 a=97
        if pyxel.btnr(pyxel.KEY_BACKSPACE):
            self.bs()
        if pyxel.btnr(pyxel.KEY_DELETE):
            self.clear()
        if pyxel.btnr(pyxel.KEY_SPACE):
            self.clear()


class Field:
    def __init__(self, fn):
        with open(fn, encoding='utf-8') as f:  # 問題
            self.field = [l.rstrip() for l in f]
            print(self.field)
        self.jisyo = []
        if os.path.isfile(fn+".skkjisyo"):  # 読み方(option)
            with open(fn+".skkjisyo") as f:
                self.jisyo += f.readlines()
        with open("./assets/SKK-JISYO.L.txt") as f:  # 読み方2
            self.jisyo += f.readlines()
        print(len(self.jisyo))
        self.selects = [[False]*4 for _ in range(4)]

    def check_selection(self):
        coords = sum([[(u, v) for u, f in enumerate(row) if f] for v, row in enumerate(self.selects)], [])
        min_x = min([x for x, _ in coords])
        max_x = max([x for x, _ in coords])
        min_y = min([y for _, y in coords])
        max_y = max([y for _, y in coords])
        # print(min_x, max_x, min_y, max_y, sum([row[min_x:max_x+1] for row in self.selects[min_y: max_y+1]], []))
        return (min_x == max_x or min_y == max_y) and all(sum([row[min_x:max_x+1] for row in self.selects[min_y: max_y+1]], []))
        # 多次元のスライスはnumpyつかうと指定できる。それ以外では内包表記を使う

    def clear(self):
        a = self.field[: -4] + [''.join([' ' if f else self.field[-4:][j][i] for i, f in enumerate(row)]) for j, row in enumerate(self.selects)]  # 消して
        self.field = [''.join(row) for row in zip(*[sorted(s, key=lambda c: c != ' ') for s in zip(*a)])]  # 落とす zip=transpose
        self.selects = [[False]*4 for _ in range(4)]

    def update(self):
        if pyxel.btnp(pyxel.MOUSE_LEFT_BUTTON):
            x, y = pyxel.mouse_x // A, pyxel.mouse_y // A
            if 0 <= x and x < 4 and 0 <= y and y < 4 and ' ' != self.field[-4:][y][x]:
                self.selects[y][x] = not self.selects[y][x]


# falseだけの行が3つ以上あるかでチェック
A = 30


def update():
    editor.update()
    field.update()
    a1 = sum(field.selects, [])  # flatten
    a2 = ''.join(field.field[-4:])  # flatten
    jukugo = ''.join([c for f, c in zip(a1, a2) if f])
    if jukugo and len(editor.text) >= 3 and field.check_selection() and any([row for row in field.jisyo if re.match(editor.text+"\s.*?/"+jukugo+";*?.*?/", row)]):
        print(jukugo, editor.text)
        field.clear()
        editor.clear()


def draw():
    pyxel.cls(7)
    [[pyxel.rect(x*A, y*A, A, A, 11 if f else 15) for x, f in enumerate(row)] for y, row in enumerate(field.selects)]
    [[[pyxel.pset(x*A+u+5, y*A+v+5, 0) for u, v in font1.points(c)] for x, c in enumerate(row)] for y, row in enumerate(field.field[-4:])]
    if len(editor.text) >= 3:
        pyxel.rect(0, pyxel.height - A, pyxel.width, pyxel.height, 8)
    [pyxel.pset(u, pyxel.height-A+v, 0) for u, v in font1.points(editor.text)]
    fx, _ = font1.box(editor.text)
    print(fx, font1.bbox)
    c1, c2 = (0, 7) if pyxel.frame_count % 50 < 25 else (7, 0)
    pyxel.rect(fx, pyxel.height-A+font1.bbox[3], *font1.box("A"), c2)
    [pyxel.pset(fx+u, pyxel.height-A+v, c1) for u, v in font1.points(editor.state)]


# font1 = BDF("./assets/misaki_gothic_2nd.bdf")
# font1 = BDF(["./assets/shnm6x12r.bdf", "./assets/shnmk12.unicode.bdf"])
# font1 = BDF(["./assets/talt14-jisx0201.bdf", "./assets/k14.unicode.bdf"])
font1 = BDF(["./assets/8x16rk.bdf", "./assets/jiskan16.unicode.bdf"])
# font1 = BDF(["./assets/12x24rk.bdf", "./assets/jiskan24.unicode.bdf"])
editor = LineEditor("./assets/romantable.txt")
field = Field("./assets/sample1.kanjikeshimasu")

pyxel.init(120, 150, caption="ケシマス")
pyxel.mouse(True)
pyxel.run(update, draw)

# 難しい漢字の読みが辞書にない
# KEY_ENTERを認識しない SPACEも
