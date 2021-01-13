import json
import random
import re

import pyxel


def arrowkeysp(values=(0, 1, 2, 3), method=pyxel.btnp):  # 戻り値:押されてないときNone、押されたときvaluesのなかの一つが返る。python.spec 0はfalseと判定されることに注意して使う
    s = [v for k, v in zip((pyxel.KEY_LEFT, pyxel.KEY_UP, pyxel.KEY_RIGHT, pyxel.KEY_DOWN, pyxel.GAMEPAD_1_LEFT, pyxel.GAMEPAD_1_UP, pyxel.GAMEPAD_1_RIGHT, pyxel.GAMEPAD_1_DOWN), values+values) if method(k)]
    return s[0] if s else None


def arrowkeys(values=(0, 1, 2, 3)): return arrowkeysp(values, pyxel.btn)
def btnpA(): return pyxel.btnp(pyxel.GAMEPAD_1_A) or pyxel.btnp(pyxel.KEY_1) or pyxel.btnp(pyxel.KEY_KP_1) or pyxel.btnp(pyxel.KEY_Z)
def btnpB(): return pyxel.btnp(pyxel.GAMEPAD_1_B) or pyxel.btnp(pyxel.KEY_2) or pyxel.btnp(pyxel.KEY_KP_2) or pyxel.btnp(pyxel.KEY_X)
def blinker(): return pyxel.frame_count // 16 % 2  # 右、左、右、左、の変化用
def chip(n): return n//1024, (n % 1024 % 32)*8, (n % 1024 // 32)*8


class BDF:
    def __init__(self, fn):  # if fn is list -> combine 2bdf fonts
        def read(fn):
            with open(fn) as f:
                bdf = f.read()
            if m := re.search(r'FONTBOUNDINGBOX\s(-?\d+)\s(-?\d+)\s(-?\d+)\s(-?\d+)', bdf):  # linefeed
                self.bbox = [int(v) for v in m.groups()]
            for m in re.finditer(r'ENCODING\s(\d+)\nSWIDTH.*?\nDWIDTH\s(\d+)\s(\d+)\nBBX\s(\d+)\s(\d+)\s(-?\d+)\s(-?\d+)\nBITMAP\n([0-9a-fA-F\n]*?)\n?ENDCHAR\n', bdf, re.MULTILINE):
                self.chars[int(m.group(1))] = {'dwidth': (int(m.group(2)), int(m.group(3))), 'bbx': (int(m.group(4)), int(m.group(5)), int(m.group(6)), int(m.group(7))), 'glyph': m.group(8).split()}
            # print(len(self.chars))
        self.chars = {10: {'dwidth': (0, 0), 'bbx': (0, 0, 0, 0), 'glyph': []}}
        self.fx, self.fy = 0, 0  # 追加の文字間隔、行間
        read(fn) if type(fn) is str else [read(s) for s in fn]
    Bits = {'0': [], '1': [3], '2': [2], '3': [2, 3], '4': [1], '5': [1, 3], '6': [1, 2], '7': [1, 2, 3], '8': [0], '9': [0, 3], 'A': [0, 2], 'B': [0, 2, 3], 'C': [0, 1], 'D': [0, 1, 3], 'E': [0, 1, 2], 'F': [0, 1, 2, 3], 'a': [0, 2], 'b': [0, 2, 3], 'c': [0, 1], 'd': [0, 1, 3], 'e': [0, 1, 2], 'f': [0, 1, 2, 3]}

    def points(self, s, x=0, y=0):  # 点群を返す。注意:再帰呼出し以外からはx,yを指定しないで下さい
        def letter(dwidth, bbx, glyph):  # dwidth使ってないが、引数展開で呼び出すので省略や_にできない
            sx, sy = x + bbx[2], y + self.bbox[1] + self.bbox[3] - bbx[1] - bbx[3]
            return sum([sum([[(sx+i*4+bit, sy+j) for bit in BDF.Bits[c]] for i, c in enumerate(row)], []) for j, row in enumerate(glyph)], [])  # sum = flatten
        s = [u for u in s if ord(u) in self.chars.keys()]
        return [] if not s else letter(**self.chars[ord(s[0])]) + self.points(s[1:], 0 if s[0] == '\n' else x+self.chars[ord(s[0])]['dwidth'][0]+self.fx, y if s[0] != '\n' else y+self.bbox[1]+self.fy)

    def box(self, s):  # 入るサイズを返す。次の文字、次の行の手前まで。注意:改行未対応
        s = [u for u in s if ord(u) in self.chars.keys()]
        return (sum([self.chars[ord(c)]["dwidth"][0] for c in s]) + self.fx*len(s), self.bbox[1]+self.fy)  # fyも足してみた


Font1 = BDF("./assets/misaki_gothic_2nd.bdf")  # 注意:ほかの多くのbdfフォントファイルはutf-8への変換が必要だった
Font1.chars[48]['glyph'][3] = 'A'  # 0の中の点を無くす
# Font1.fx, Font1.fy = 2, 3  # 外から調整できる


def draw_text(x, y, text, col=7): [pyxel.pset(x+u, y+v, col) for u, v in Font1.points(text)]
def draw_textC(x, y, text): draw_text(x, y, text, 8 if g_player.hp <= 0 else 10 if g_player.hp < g_player.maxhp / 2 else 7)  # カラー
def draw_frameC(x, y, w, h): draw_frame(x, y, w, h, 2 if g_player.hp <= 0 else 1 if g_player.hp < g_player.maxhp / 2 else 0)  # カラー


def draw_frame(x, y, w, h, col=0):  # col 0: white 1:yellow 2:red x,yは枠の左上ではない。中のテキストの左上
    A, B, C = 5, -2, -1  # (x,y)からA:左上に、B:右、C:下の調節
    pyxel.blt(x-A, y-A, 0, col*8, 16, A, A, 15)
    pyxel.blt(x+w+B, y-A, 0, col*8, 16, -A, A, 15)
    pyxel.blt(x-A, y+h+C, 0, col*8, 16, A, -A, 15)
    pyxel.blt(x+w+B, y+h+C, 0, col*8, 16, -A, -A, 15)
    [pyxel.blt(x+i, y-A, 0, col*8+7, 16, 1, A, 15) for i in range(w+B)]
    [pyxel.blt(x+i, y+h+C, 0, col*8+7, 16, 1, -A, 15) for i in range(w+B)]
    [pyxel.blt(x-A, y+j, 0, col*8, 16+7, A, 1, 15) for j in range(h+C)]
    [pyxel.blt(x+w+B, y+j, 0, col*8, 16+7, -A, 1, 15) for j in range(h+C)]
    pyxel.rect(x, y, w+B, h+C, 0)


class State:  # 重ねてウィンドウを表示、フォーカスを移動させる仕組み。TextBox()としても、次のフレームからというのが、関数呼び出しと違ってこんがらがる
    def __new__(cls, *args):  # **kargs
        global g_state
        self = object.__new__(cls)
        self.original_state = g_state
        g_state = self
        return self

    def update(self): pass
    def draw(self): pass

    def releaseback(self, fmulti=False):  # 閉じてフォーカスを返す、を実現するためのもの
        global g_state  # global宣言忘れがちなので、できるだけここを使う
        if g_state == self:
            g_state = self.original_state
            if fmulti and SelectBox == type(self.original_state):  # サブメニューから一気に返る仕組み
                g_state = g_state.original_state


g_state = None
ToZenkaku = str.maketrans({chr(0x0021 + i): chr(0xFF01 + i) for i in range(94)})


class SelectBox(State):  # ２段に並んだものでも簡潔に表現できると思うが、128ピクセルでは縦のみになった。
    def __init__(self, ox, oy, texts, commands=None):  # コマンドを指定しないときは、あとからindexやselectedItemを読んで使う
        if len(texts) > 0:
            self.w, self.h = Font1.box("あ")[0] * (max([len(s) for s in texts]) + 1), Font1.box("あ")[1] * len(texts)
            self.index, self.ox, self.oy, self.texts, self.commands = 0, ox if ox >= 0 else -ox-self.w, oy if oy >= 0 else -oy-self.h, texts, commands or (lambda: None,)*len(texts)
            self.state4indexes = [[None, i-1, None, i+1] for i in range(len(self.texts))]  # 各index時にどのキーを押すと、次の状態はどうなるかの表。無効にするキーにはNoneを指定。
            self.state4indexes[0][1], self.state4indexes[-1][3] = None, None  # ２つなら ((None, None, None, 1), (None, 0, None, None)) ができる。
        else:
            self.update, self.draw = self.releaseback, lambda: None  # アイテムが０個のサブメニューSelectBoxを作ったとき、ここでreleasebackすると、元のコマンド後のreleasebackでそれも閉じでしまう。ので１フレームは動作させる苦肉の策。
        self.cursor = "●"  # "→"
        self.sounds = {"OK": 1, "Cancel": 2, "Move": 0}
    selectedItem = None  # サブメニューでも項目名を(後で)取れるように
    YesNoParameters = (-122, -84, ("はい", "いいえ"))  # ox oy に負の値を指定したときは右下を指定したものとして必要文字分の左上を計算で求める

    def update(self):
        if btnpA():
            pyxel.play(3, self.sounds["OK"])
            SelectBox.selectedItem = self.texts[self.index]
            self.commands[self.index]()  # この中でg_stateを変更しても、次行も実行されるため、typeを見て動作を変える対策をした
            self.releaseback(True)  # g_stateを変更したが、効果があるのは次フレームから
        if btnpB():  # B:Cancel は何もせずにフォーカスを返す
            self.index = -1  # index -1: Cancel
            pyxel.play(3, self.sounds["Cancel"])
            self.releaseback()
        k = arrowkeysp(self.state4indexes[self.index])  # 押したキーに対応する次のindex値が返る
        if None is not k:  # 0にしたい場合もあるので、Noneとの比較を忘れずに
            self.index = k
            pyxel.play(3, self.sounds["Move"])

    def draw(self):
        self.original_state.draw()  # 背景を描画
        draw_frameC(self.ox, self.oy, self.w, self.h)
        draw_textC(self.ox, self.oy, "".join([f"　{s}\n" for s in self.texts]))
        draw_textC(self.ox, self.oy, "\n" * self.index + self.cursor)  # "→") # misaki_gothicで▶が見つからない。文字にすると別色にもできる


class TextBox(State):
    def __init__(self,  text, text0=""):
        self.text, self.text0 = text.translate(ToZenkaku) if type(text) is str else "", text0
        self.update = self._update().__next__
        self.speed, self.sounds = TextBox.Speed, {"Step": 2, "Go": 1}
        self.sy = 0
    Speed = 3
    Lines, Len = 4, 14
    OX, OY = 10, 91
    W, _H = Font1.box("あ"*Len)
    H = _H * Lines

    def _update(self):
        tab = "　　" if re.match(r"\n?.「", self.text) or re.match("　　", self.text0) or re.match(".「", self.text0) else ""
        for i, c in enumerate(self.text):  # 一文字ずつ描画(スペース,\nと🔻は別な動作をさせる)
            if "　" == c:  # スペースは待たない
                self.text0 += c
                continue
            if "🔻" == c:  # クリック待ち
                self.speed = TextBox.Speed
                yield TextBox.V()
                continue
            if "\n" != c and len(self.text0.split("\n")[-1]) >= TextBox.Len:  # 自動改行
                c = "\n"+c  # 指定改行とコードを共通化させるため、一時的にcを変更(改行のコードも通り、文字のコードも通る)
            if "\n" == c[0] or "\r" == c:  # \rをタブなし改行とした
                self.text0 += "\n" + (tab if "\r" != c else "")
                s = self.text0.split("\n")
                if len(s) > TextBox.Lines:  # scroll up
                    for self.sy in range(0, TextBox._H, 2):
                        if btnpA():
                            self.speed = 0  # Aボタンによるアニメスキップ(の代わりに高速動作)🔻で戻す
                        yield
                    self.text0, self.sy = "\n".join(s[-TextBox.Lines:]), 0
                if "\n" == c:
                    continue
                else:
                    c = c[1:]  # 一時的に変更していたcを戻し、fallthrough
            self.text0 += c  # ここからほか全ての文字の動作
            pyxel.play(3, self.sounds["Step"])
            for j in range(self.speed):  # ウエイト
                if btnpA():  # self.updateをたくさん呼べばいい？→ジェネレーター内から自身は呼べない
                    self.speed = 0  # Aボタンによるアニメスキップ(の代わりに高速動作)🔻で戻す
                yield
        yield self.releaseback()

    def draw_just(self):
        draw_frameC(TextBox.OX, TextBox.OY, TextBox.W, TextBox.H)
        pyxel.clip(TextBox.OX, TextBox.OY, TextBox.W, TextBox.H)
        draw_textC(TextBox.OX, TextBox.OY-self.sy, self.text0)
        pyxel.clip()

    def draw(self):
        self.original_state.draw()
        self.draw_just()

    class V(State):  # ▼を表示してクリック待ち
        def update(self):
            if btnpA() or btnpB() or arrowkeysp() is not None:
                pyxel.play(3, self.original_state.sounds["Go"])
                self.releaseback()
        Cursor = "▼"

        def draw(self):
            self.original_state.draw()
            pyxel.rect(110, 120,  8, 8, 0)
            draw_textC(110, 120, TextBox.V.Cursor)


class Field(State):
    def __init__(self, x=12, y=2):
        self.x, self.y, self.direction = x, y, 3  # 主人公の位置、主人公の向き
        self.sx, self.sy = 0, 0  # マスの途中のアニメに使う
        self.update = self._update().__next__
        self.idle_start = pyxel.frame_count
        self.textbox = None
        self.fdraw_poison = False
        self.original_state = None  # fieldより下はないはずなので切っておく
        pyxel.playm(self.Music, loop=True)
        self.traps = ((12, 2, lambda: Blackout(lambda: Castle(22, 15))),  # 街、階段とか # lambdaで「あとで実行」をここで書ける # Battleを書く場合があるかもしれないのでクラス変数にしない
                      (13, 27, lambda: Blackout(lambda: Villege(None, None, self.direction))),
                      (4, 29, lambda: Blackout(lambda: Dungeon(11, 26))), )
    MapID, MapLeft, MapTop, MapRight, MapBottom, BGColor = 0, 0, 0, 256, 256, 12
    NPCs = []  # NPC 扉、宝箱など。２度作られないようにクラス変数にしておく
    Music = 1  # 戦闘シーンから戻るときに音楽を戻す
    HotKeys = {pyxel.KEY_W: lambda: save(), pyxel.KEY_F5: lambda: load()}  # python.spec lambdaに包むと、まだ作られていない関数を書ける？

    def isblocked(self, x, y):
        return self.MapLeft > x or self.MapTop > y or x > self.MapRight or y > self.MapBottom or \
            pyxel.tilemap(self.MapID).get(x, y) in (0, 4, 33, 34, 35, 42, 43) or \
            [npc for npc in self.NPCs if x == npc.x and y == npc.y]  # pyxel.spec タイル範囲外アクセスで落ちる

    def _update(self):
        dx, dy = (-1, 0, 1, 0)[self.direction], (0, -1, 0, 1)[self.direction]
        while True:
            [npc.update() for npc in self.NPCs]
            [v() for k, v in self.HotKeys.items() if pyxel.btnp(k)]  # ホットキー(開発中のみ？)
            if btnpA() or btnpB():
                if s := [npc for npc in self.NPCs if self.x+dx == npc.x and self.y+dy == npc.y]:  # NPCに話しかける、宝箱を開けるなど
                    for it in s[0]._react():  # 会話コルーチンの連続呼び出し
                        self.textbox = TextBox(it, self.textbox.text0 if self.textbox else "")
                        yield
                    self.textbox = None
                else:  # 話す相手(NPC)がいなければ、コマンドメニューをだす
                    command = None
                    def other(): nonlocal command; command = True
                    spells = [i for i in [_ for _ in g_player.spells if Spells[_] <= g_player.mp] if i in ("ヒール")]  # MPが足りて、フィールドで使えるものだけ
                    items = [i for i in g_player.items if i in ("やくそう", "もどりふだ", "どうのけん")]  # フィールドで使えるものだけ
                    yield SelectBox(-120, 8, ("じゅもん", "どうぐ"), (lambda: SelectBox(-124, 4, spells, [other]*len(spells)), lambda: SelectBox(-124, 4, items, [other]*len(items))))
                    if command:
                        command = {"ヒール": self._heal, "やくそう": self._yakusou, "もどりふだ": self._return_ticket, "どうのけん": self._soards}[SelectBox.selectedItem]
                        for it in command():  # コルーチン(ジェネレーター)の連続呼び出し
                            self.textbox = TextBox(it, self.textbox.text0 if self.textbox else "")
                            yield
                        self.textbox = None
            # if btnpB(): pass # Aボタンと同じ動作をするようにした
            d = arrowkeys((0, 1, 2, 3))
            if None is not d:
                self.idle_start = pyxel.frame_count
                self.direction, dx, dy = d, (-1, 0, 1, 0)[d], (0, -1, 0, 1)[d]
                if not self.isblocked(self.x+dx, self.y+dy):  # 進める
                    for i in range(1, 8, 1):  # マスからマスの途中はアニメ
                        self.sx, self.sy = self.sx + dx, self.sy + dy
                        yield
                    self.x, self.y, self.sx, self.sy = self.x + dx, self.y + dy, 0, 0
                    if pyxel.tilemap(self.MapID).get(self.x, self.y) == 6:  # 毒沼
                        g_player.hp -= 1
                        self.fdraw_poison = True
                    if g_player.hp <= 0:
                        yield TextBox(f"{g_player.name}はしんでしまった！🔻")
                        yield Title()
                    elif [command() for x, y, command in self.traps if x == self.x and y == self.y]:  # 階段など
                        pass
                    elif m := self.encont_monster(self.x, self.y):
                        yield Battle(m)
                else:  # 進めない
                    pyxel.play(3, 2)
                    while pyxel.play_pos(3) != -1:
                        yield
            yield

    def draw(self):
        pyxel.cls(self.BGColor)
        pyxel.bltm((self.MapLeft-self.x+7.5)*8-self.sx, (self.MapTop-self.y+7.5)*8-self.sy, self.MapID, self.MapLeft, self.MapTop, self.MapRight-self.MapLeft, self.MapBottom-self.MapTop)  # 何も考えずに全マップ描画
        [npc.draw((-self.x+7.5)*8-self.sx, (-self.y+7.5)*8-self.sy) for npc in self.NPCs]
        pyxel.blt(64-4, 64-4-1, 0, (self.direction*2+blinker())*8, 32, 8, 8, 0)  # 中央に主人公を
        if pyxel.frame_count - self.idle_start > 45:
            draw_playerstatus()
        if self.textbox:
            self.textbox.draw_just()
        if self.fdraw_poison:
            pyxel.rectb(0, 0, pyxel.width, pyxel.height, 8)
            self.fdraw_poison = False
        # pyxel.text(0, 0, f"{self.x: 3}: {self.y: 3}", 7)

    def encont_monster(self, x, y): return (Slime, Slime, Rabbit, Pi, Theta, Root)[random.randrange(6)]() if 5 == random.randrange(15) else None

    def _heal(self):  # 以下、コマンドへの対応、最初の\nがあるのでBattleとの共有化はできない
        yield f"{g_player.name}はヒールをとなえた！"
        pyxel.play(3, 17)
        while pyxel.play_pos(3) != -1:
            yield ""
        v = 6 + random.randrange(5)
        g_player.hp = min(g_player.hp + v, g_player.maxhp)
        g_player.mp -= 2
        yield f"\n{g_player.name}のＨＰは{v}かいふくした！🔻"

    def _yakusou(self):
        yield f"{g_player.name}はやくそうをつかった！"
        pyxel.play(3, 17)
        while pyxel.play_pos(3) != -1:
            yield ""
        v = 6 + random.randrange(5)
        g_player.hp = min(g_player.hp + v, g_player.maxhp)
        g_player.items.remove("やくそう")
        yield f"\n{g_player.name}のＨＰは{v}かいふくした！🔻"

    def _return_ticket(self):
        yield "もどりふだはさいしょのしろのばしょにもどります。\nつかいますか？"
        yesno = SelectBox(*SelectBox.YesNoParameters)
        yield ""
        if yesno.index == 0:
            yield f"\n{g_player.name}はもどりふだをつかった！"
            g_player.items.remove("もどりふだ")
            pyxel.play(3, 17)
            while pyxel.play_pos(3) != -1:
                yield ""
            yield Field(12, 3)  # 音の変更
        else:
            yield ""

    def _soards(self): yield "けんなどはじどうでいちばんつよいものがつかわれる。🔻"


class Blackout(State):
    def __init__(self, command):
        self.command = command
        self.update = self._update().__next__
        self.sound = 9

    def _update(self):
        pyxel.stop()  # BGM停止
        pyxel.play(3, self.sound)
        while pyxel.play_pos(3) != -1:
            yield
        yield self.command()
        yield self.releaseback()

    def draw(self): pyxel.cls(1)


class NPC:  # 宝箱などにも使うのでしゃべるをベースにできない
    def __init__(self, x, y, chip, text_or_callable): self.x, self.y, self.chip, self.text_or_callable = x, y, chip, text_or_callable
    def update(self): pass
    def draw(self, ox, oy): pyxel.blt(ox+self.x*8, oy+self.y*8-1, *chip(self.chip+blinker()), 8, 8, 0)  # 人物はy-1して少し重ねる
    def _react(self): yield self.text_or_callable if not callable(self.text_or_callable) else self.text_or_callable()  # シンプルなテキストだけなら文字列を、複雑なものは_reactを更新(例:Shop)


class RandomWalker(NPC):  # 人物のベース
    def __init__(self, x, y, chip, text):
        super().__init__(x, y, chip, text)
        self.update = self._update().__next__
        self.sx, self.sy = 0, 0

    def _update(self):
        while True:
            for _ in range(16*2):
                yield
            d = random.randrange(4+3)
            dx, dy = (-1, 0, 1, 0, 0, 0, 0)[d], (0, -1, 0, 1, 0, 0, 0)[d]  # 動かないときも入れることで全員が同じタイミングで動かないよう
            if not (g_state.isblocked(self.x+dx, self.y+dy) or (self.x+dx == g_state.x or self.y+dy == g_state.y)):  # npc.updateが呼ばれるときg_stateはFieldです
                for i in range(0, 8, 1):
                    self.sx, self.sy = self.sx+dx, self.sy+dy
                    yield
                self.x, self.y, self.sx, self.sy = self.x+dx, self.y+dy, 0, 0

    def draw(self, ox, oy): super().draw(ox+self.sx, oy+self.sy)


class Chest(NPC):
    def __init__(self, x, y, item):
        super().__init__(x, y, 42, "")
        self.item = item  # item:整数ならゴールド(お金)が入っているものとする

    def draw(self, ox, oy): pyxel.blt(ox+self.x*8, oy+self.y*8, *chip(self.chip), 8, 8, 0)  # y-1なし、blinkなし

    def _react(self):
        v = f"{self.item}ゴールド" if type(self.item) is int else self.item
        yield f"{g_player.name}はたからばこをあけた！🔻{v}をてにいれた！🔻"
        if type(self.item) is int:
            g_player.gold += self.item
        else:
            g_player.items += [self.item]
        yield g_state.NPCs.remove(self)


class Door(NPC):
    def __init__(self, x, y):
        super().__init__(x, y, 43, "")

    def draw(self, ox, oy): pyxel.blt(ox+self.x*8, oy+self.y*8, *chip(self.chip), 8, 8, 0)  # y-1なし、blinkなし

    def _react(self):
        if not "かぎ" in g_player.items:
            yield "ドアをあけるにはかぎがひつようだ。🔻"
        else:
            yield f"{g_player.name}はドアをあけた。🔻"
            g_player.items.remove("かぎ")
            yield g_state.NPCs.remove(self)


class InnDummy(NPC):  # 机に設定する
    def __init__(self, x, y, price):
        super().__init__(x, y, 1022, "")  # 1022 1023は何も表示しない
        self.price = price

    def _react(self):
        yield f"＊「ここはやどやです。ひとばん{self.price}ゴールドです。よろしいですか？"
        yesno = SelectBox(*SelectBox.YesNoParameters)
        yield ""
        if yesno.index == 0:
            yield "\nごゆっくりお休みください。」"
            s = Blackout(lambda: None)  # 音の変更
            s.sound = 14
            g_player.hp, g_player.mp, g_player.doku = g_player.maxhp, g_player.maxmp, False
            g_player.gold -= self.price
            yield ""
            pyxel.playm(g_state.Music, loop=True)
            save()
            yield "\r＊「おはようございます。いってらっしゃいませ。」🔻"  # \rでタグなし改行
        else:
            yield "\nまたのお越しを！」🔻"


class ShopDummy(NPC):  # 机に設定する
    def __init__(self, x, y, goods, shopname="どうぐや"):  # (("やくそう", 6), ("どくばり", 11)), "どうぐや"
        super().__init__(x, y, 1022, "")
        self.goods, self.shopname = goods, shopname

    def _react(self):
        yield f"＊「ここは{self.shopname}です。なにをおもとめですか？"
        while True:
            s = SelectBox(-120, 8, [it[0]for it in self.goods])
            yield  # 次の回でindexを読む
            if s.index < 0:  # Bボタンでキャンセルしたときだけ会話を終えることができる？
                break
            if self.goods[s.index][1] <= g_player.gold:
                yield f"\n{self.goods[s.index][0]}は{self.goods[s.index][1]}ゴールドです。よろしいですか？"
                yesno = SelectBox(*SelectBox.YesNoParameters)
                yield  # 次の回でindexを読む
                if yesno.index == 0:
                    g_player.items += [self.goods[s.index][0]]
                    g_player.gold -= self.goods[s.index][1]
                    yield "\nありがとうございます。"
            else:
                yield f"\n{self.goods[s.index][0]}は{self.goods[s.index][1]}ゴールドです。おかねがたりないようです。"
            yield "\nほかにもなにかおもとめですか？"
        yield "\nまたのお越しを！」🔻"


class Battle(State):
    def __init__(self,  monster):
        self.monster, self.textbox = monster, None
        self.update = self._update().__next__
        self.offset = (0, 0)
        pyxel.playm(3, loop=True)

    def releaseback(self):
        super().releaseback()
        pyxel.playm(self.original_state.Music, loop=True)  # @spec これがあるので、Fieldの上すぐにBattleが来ないとならない

    def _update(self):
        # yield  # opening animation
        self.textbox = TextBox(f"{self.monster.name}があらわれた！")
        yield
        while True:
            command = None
            def other(): nonlocal command; command = True  # 一時的にTrueとし、後でSelectBox.selectedItemをみて設定し直す
            spells = [i for i in [_ for _ in g_player.spells if Spells[_] <= g_player.mp] if i in ("ヒール", "ファイア")]  # 戦闘中に使えるものだけ
            items = [i for i in g_player.items if i in ("やくそう")]  # 戦闘中に使えるものだけ
            while not command:  # 命令が得られるまでSelectBoxを出す。(Bボタンで何度キャンセルされても)
                yield SelectBox(-120, 8, ("たたかう", "じゅもん", "どうぐ", "にげる"), (other, lambda: SelectBox(-124, 4, spells, [other]*len(spells)), lambda: SelectBox(-124, 4, items, [other]*len(items)), other))
            Commands = {"たたかう": self._attack, "にげる": self._runaway, "ヒール": self._heal, "ファイア": self._fire, "やくそう": self._yakusou}
            command = Commands[SelectBox.selectedItem](g_player, self.monster)  # 一時的なTrueから、対応するコルーチンへ置き換え
            command2 = Commands[self.monster.choice()](self.monster, g_player)  # 同じタイミングで決断する
            for cmd in [command, command2] if g_player.agility+random.randrange(5) >= self.monster.agility+random.randrange(5) else [command2, command]:
                for it in cmd:  # コルーチン(ジェネレーター)の連続呼び出し
                    self.textbox = TextBox(it.replace("\n", "\n" if cmd is command else "\n　") if it else "", self.textbox.text0)
                    yield
                if self.monster.hp <= 0:
                    break  # ２重ループを抜ける
                if g_player.hp <= 0:
                    yield TextBox(f"\n{g_player.name}はしんでしまった！🔻", self.textbox.text0)
                    yield Title()
            else:
                continue
            break
        drops = "、".join(self.monster.items)+"、" if self.monster.items else ""
        self.textbox = TextBox(f"\n{self.monster.name}をたおした！🔻\n{self.monster.gold}ゴールドと、{drops}{self.monster.experience}のけいけんちをえた！🔻", self.textbox.text0)
        yield
        g_player.items += self.monster.items
        g_player.gold += self.monster.gold
        g_player.experience += self.monster.experience
        if level(g_player.experience - self.monster.experience) < level(g_player.experience):
            self.textbox = TextBox(f"\n{g_player.name}はレベルがあがった！🔻", self.textbox.text0)
            yield
            g_player.maxhp, g_player.maxmp, spells, g_player.agility = Statuses[level(g_player.experience)-1]
            g_player.spells += spells
        yield self.releaseback()

    def draw(self):
        self.original_state.draw()
        pyxel.rect(32+self.offset[0], 32+self.offset[1], 64, 64, 0)  # 背景
        pyxel.rectb(32+self.offset[0], 32+self.offset[1], 64, 64, 7)  # 背景
        draw_playerstatus()  # 下になるので再度描画
        if self.textbox:
            self.textbox.draw_just()
        if self.monster.hp > 0:
            self.monster.draw(*self.offset)  # モンスターが一番上

    def _attack(self, offence, deffence):
        yield f"\n{offence.name}のこうげき！"
        Shake = ((-2, -2), (-2, 2), (2, 2), (-2, 2), (1, -2), (-1, 1), (0, -1), (0, 1), (0, 0))
        pyxel.play(3, 16)
        if offence == g_player:
            for self.offset in Shake:
                yield ""
        else:
            for self.original_state.fdraw_poison in (True, False, True, False, True, False, True, False, True, False, ):
                yield ""
        while pyxel.play_pos(3) != -1:
            yield ""
        a = max([v for k, v in (("どうのけん", 3), ("はがねのけん", 7)) if k in offence.items] + [0])
        v = 2 + random.randrange(3) + a
        deffence.hp = max(deffence.hp-v, 0)
        yield f"\n{deffence.name}に{v}のダメージ！"

    def _runaway(self, offence, deffence):
        yield f"\n{offence.name}は逃げ出した！"
        pyxel.play(3, 9)
        while pyxel.play_pos(3) != -1:
            yield ""
        self.releaseback()
        yield ""

    def _yakusou(self, offence, _):
        yield f"\n{offence.name}はやくそうをつかった！"
        pyxel.play(3, 17)
        while pyxel.play_pos(3) != -1:
            yield ""
        v = 6 + random.randrange(3)
        offence.hp = min(offence.hp + v, offence.maxhp)
        offence.items.remove("やくそう")
        yield f"\n{offence.name}のＨＰは{v}かいふくした！"

    def _heal(self, offence, _):
        yield f"\n{offence.name}はヒールをとなえた！"
        pyxel.play(3, 17)
        while pyxel.play_pos(3) != -1:
            yield ""
        v = 6 + random.randrange(3)
        offence.hp = min(offence.hp + v, offence.maxhp)
        offence.mp -= 2
        yield f"\n{offence.name}のＨＰは{v}かいふくした！"

    def _fire(self, offence, deffence):
        yield f"\n{offence.name}はファイアをとなえた！"
        Shake = ((-2, -2), (-2, 2), (2, 2), (-2, 2), (1, -2), (-1, 1), (0, -1), (0, 1), (0, 0))
        pyxel.play(3, 16)
        if offence == g_player:
            for self.offset in Shake:
                yield ""
        else:
            for self.original_state.fdraw_poison in (True, False, True, False, True, False, True, False, True, False, ):
                yield ""
        while pyxel.play_pos(3) != -1:
            yield ""
        v = 5 + random.randrange(3)
        deffence.hp = max(deffence.hp-v, 0)
        yield f"\n{deffence.name}に{v}のダメージ！"


#           maxhp, maxmp, spells, agility,
Statuses = ((13,  0, [], 7,),
            (16,  5, ["ヒール"], 10,),
            (19,  9, ["ファイア"], 13,),
            (22,  14, [], 14,),
            (25,  21, [], 17,),
            (28,  26, [], 21,),)
Spells = {"ヒール": 2, "ファイア": 3}
Levels = (0, 18, 39, 85, 143, 195, 999)


def level(exp): return len([i for i in Levels if i <= exp])


class Charactor:
    def __init__(self, name, maxhp, maxmp, hp, mp, spells, items, gold, experience, agility):
        self.name, self.maxhp, self.maxmp, self.hp, self.mp, self.spells, self.items, self.gold, self.experience, self.agility = name, maxhp, maxmp, hp, mp, spells, items, gold, experience, agility
        self.doku = False


g_player = Charactor("ああああ", 13, 2, 13, 2, [], [], 120, 0, 7)


def draw_playerstatus():
    doku = "どく" if g_player.doku else ""
    draw_frameC(8, 8, 48, 32)
    draw_textC(8, 8, f"{g_player.name:　<4} L{level(g_player.experience): 2}\nＨＰ {g_player.hp: 3}/{g_player.maxhp: 3}\nＭＰ {g_player.mp: 3}/{g_player.maxmp: 3}\nＧ {g_player.gold: 5}{doku}")


class Slime(Charactor):
    def __init__(self): super().__init__("スライム", 5+random.randrange(2), 0, 7, 0, [], (["やくそう"] if 3 == random.randrange(7) else []), 3+random.randrange(2), 3+random.randrange(2), 4)
    def draw(self, ox, oy): pyxel.blt(56+ox, 56+oy, 2, 0, 0, 16, 16, 15)
    def choice(self): return random.choice(["たたかう"]*self.hp+["にげる"]*1+(["やくそう"]*2 if "やくそう" in self.items else []))  # コマンドメニューと同じ文字列を返す


class Rabbit(Charactor):
    def __init__(self): super().__init__("うさぎ", 7+random.randrange(4), 0, 7, 0, [], (["やくそう"] if 3 == random.randrange(6) else []), 3+random.randrange(2), 3+random.randrange(2), 14)
    def draw(self, ox, oy): pyxel.blt(56+ox, 56+oy, 2, 16, 0, 16, 16, 15)
    def choice(self): return random.choice(["たたかう"]*self.hp+["にげる"]*2+(["やくそう"]*1 if "やくそう" in self.items else []))


class Mimic(Charactor):
    def __init__(self): super().__init__("ミミック", 11+random.randrange(4), 9, 15, 9, ["ヒール", "ファイア"], (["やくそう"] if 3 == random.randrange(4) else []), 30+random.randrange(9), 13+random.randrange(3), 9)
    def draw(self, ox, oy): pyxel.blt(56+ox, 56+oy, 2, 32, 0, 16, 16, 15)
    def choice(self): return random.choice(["たたかう"]*self.hp+(["ヒール"]*2 if self.mp > 2 else [])+(["ファイア"]*1 if self.mp > 3 else [])+(["やくそう"]*2 if "やくそう" in self.items else []))


class Pi(Charactor):
    def __init__(self): super().__init__("パイ", 8+random.randrange(4), 9, 12, 9, ["ヒール", "ファイア"], (["やくそう"] if 3 == random.randrange(9) else []), 3+random.randrange(2), 3+random.randrange(2), 8)
    def draw(self, ox, oy): pyxel.blt(56+ox, 56+oy, 2, 48, 0, 16, 16, 13)
    def choice(self): return random.choice(["たたかう"]*self.hp+(["ヒール"]*2 if self.mp > 2 else [])+(["ファイア"]*1 if self.mp > 3 else [])+(["やくそう"]*2 if "やくそう" in self.items else []))


class Theta(Charactor):
    def __init__(self): super().__init__("シータ", 9+random.randrange(4), 9, 13, 9, ["ヒール", "ファイア"], (["やくそう"] if 3 == random.randrange(9) else []), 3+random.randrange(2), 3+random.randrange(2), 8)
    def draw(self, ox, oy): pyxel.blt(56+ox, 56+oy, 2, 64, 0, 16, 16, 15)
    def choice(self): return random.choice(["たたかう"]*self.hp+(["ヒール"]*2 if self.mp > 2 else [])+(["ファイア"]*1 if self.mp > 3 else [])+(["やくそう"]*2 if "やくそう" in self.items else []))


class Root(Charactor):
    def __init__(self): super().__init__("ルート", 10+random.randrange(4), 9, 14, 9, ["ヒール", "ファイア"], (["やくそう"] if 3 == random.randrange(9) else []), 3+random.randrange(2), 3+random.randrange(2), 10)
    def draw(self, ox, oy): pyxel.blt(56+ox, 56+oy, 2, 80, 0, 16, 16, 5)
    def choice(self): return random.choice(["たたかう"]*self.hp+(["ヒール"]*2 if self.mp > 2 else [])+(["ファイア"]*1 if self.mp > 3 else [])+(["やくそう"]*2 if "やくそう" in self.items else []))


class Castle(Field):
    def __init__(self, x, y):
        super().__init__()
        self.x, self.y = x, y
        self.encont_monster = lambda x, y: None
        def field(): Blackout(lambda: Field())
        self.traps = ((21, 16, field), (22, 16, field), (23, 16, field), (24, 5, lambda: Blackout(lambda: Palace())), )
    MapID, MapLeft, MapTop, MapRight, MapBottom, BGColor = 1, 9, 0, 32, 17, 3
    NPCs = [NPC(11, 13, 196, ""),  # 男性
            ShopDummy(12, 13, (("やくそう", 6), ("どうのけん", 30))),
            NPC(29, 14, 198, ""),  # 女性
            InnDummy(28, 14, 7),
            Door(30, 5),
            RandomWalker(13, 2, 198, "みなみにゆけば、まちとダンジョンがある。"),
            RandomWalker(15, 5, 196, "青は藍より出でて藍より青し。🔻\n漢字も使えるよ。🔻"),
            RandomWalker(26, 13, 200, "そこのたからばこにはさわってはいけない。ちゅうこくしたぞ🔻"),
            NPC(30, 11, 1022, lambda: Battle(Mimic())), ]
    Music = 2


class Palace(Field):
    def __init__(self, x=8, y=4, is_opening=False):
        super().__init__()
        self.x, self.y = x, y
        self.encont_monster = lambda x, y: None
        self.traps = ((8, 4, lambda: Blackout(lambda: Castle(24, 5))),)
        if is_opening:
            self.x, self.y = 4, 4
            self.direction = 1
            TextBox(f"王「よくぞわが呼びかけに応えてくれた！ゆうしゃ{g_player.name}よ！🔻\n……せつめいははぶくが、ぼうけんにでてまおうをたおしてきてくれ！」🔻")
    MapID, MapLeft, MapTop, MapRight, MapBottom = 1, 0, 0, 10, 6
    NPCs = [NPC(4, 1, 192, "王「わしはおうさまじゃよ」🔻"),
            RandomWalker(2, 2, 196, "＊「たからばこのなかみをおとりください。🔻\nきっとやくにたつものです。」🔻"),
            Chest(1, 3, "もどりふだ"),
            Chest(1, 4, 99)]
    Music = 2


class Villege(Field):
    def __init__(self, x=None, y=None, direction=3):
        super().__init__()
        self.x = x or (62, 47, 33, 47)[direction]
        self.y = y or (15, 30, 15, 1)[direction]
        self.direction = direction
        self.encont_monster = lambda x, y: None
        def field(): Blackout(lambda: Field(13, 27))
        self.traps = ((32, 15, field), (32, 16, field), (47, 0, field), (48, 0, field), (63, 15, field), (63, 16, field), (47, 31, field), (48, 31, field),)
    MapID, MapLeft, MapTop, MapRight, MapBottom, BGColor = 1, 32, 0, 64, 32, 3
    NPCs = [NPC(58, 21, 196, ""),  # 男性
            ShopDummy(58, 20, (("やくそう", 6), ("はがねのけん", 55))),
            NPC(36, 19, 198, ""),  # 女性
            InnDummy(37, 19, 10),
            RandomWalker(33, 2, 198, "あおはあいよりいでてあいよりあおし。🔻\nひらがなのほうがいいかな？🔻"),
            RandomWalker(35, 5, 196, "青は藍より出でて藍より青し。🔻\n漢字も使えるよ。🔻"),
            RandomWalker(36, 13, 200, "ここはぼうけんしゃのまち。\nちかくのダンジョンにちょうせんするひとびとがあつまる。🔻"),
            ]
    Music = 2


class Dungeon(Field):
    def __init__(self, x, y):
        super().__init__()
        self.x, self.y = x, y
        self.traps = ((11, 26, lambda: Blackout(lambda: Field(4, 29))),)
    MapID, MapLeft, MapTop, MapRight, MapBottom, BGColor = 1, 0, 24, 32, 56, 0
    NPCs = [
        NPC(7, 54, 1022, lambda: Battle(Mimic())), ]
    Music = 2


class Title(State):
    def __init__(self):
        global g_player
        g_player = Charactor(g_player.name, 13, 2, 13, 2, [], [], 10, 0, 7)
        g_player.maxhp, g_player.maxmp, g_player.spells, g_player.agility = Statuses[0]
        g_player.hp, g_player.mp = g_player.maxhp, g_player.maxmp
        pyxel.playm(0, loop=True)

    def update(self):
        s = SelectBox(40, 76, ("はじめから", "つづきから"), (lambda: Palace(None, None, True), load))
        s.sounds = {"OK": 0, "Cancel": 0, "Move": 0}

    def draw(self):
        pyxel.cls(0)
        pyxel.blt(32, 30, 1, 0, 0, 64, 16)


SaveFilename = "pyxel_rpg.json"


def save():
    data = {
        "player": {"name": g_player.name, "hp": g_player.hp, "maxhp": g_player.maxhp, "mp": g_player.mp, "maxmp": g_player.maxmp, "spells": g_player.spells, "items": g_player.items, "gold": g_player.gold, "experience": g_player.experience},
        "field": {"classname": g_state.__class__.__name__, "x": g_state.x, "y": g_state.y, },
        # "Palace": {"chests": [{"x": i.x, "y": i.y} for i in Palace.NPCs if i.__class__ is Chest]},
    }  # 宝箱は復活しちゃうけど
    with open(SaveFilename, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def load():
    pyxel.load("./assets/pyxel_rpg.pyxres")
    with open(SaveFilename, 'r') as f:
        data = json.load(f)
        g_player.name = data["player"]["name"]
        g_player.hp = data["player"]["hp"]
        g_player.maxhp = data["player"]["maxhp"]
        g_player.mp = data["player"]["mp"]
        g_player.maxmp = data["player"]["maxmp"]
        g_player.spells = data["player"]["spells"]
        g_player.items = data["player"]["items"]
        g_player.gold = data["player"]["gold"]
        g_player.experience = data["player"]["experience"]
        cls = data["field"]["classname"]
        globals()[cls](data["field"]["x"], data["field"]["y"])  # Field派生物の__init__を揃える必要がある。


pyxel.init(128, 128, caption="An RPG Sample")
pyxel.load("./assets/pyxel_rpg.pyxres")
Title()  # pyxel.initより後ろに書く
pyxel.run(lambda: g_state.update(), lambda: g_state.draw())
