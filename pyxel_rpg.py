import pickle
import random
import re

import pyxel


def arrowkeysp(values=(0, 1, 2, 3), poll=pyxel.btnp):  # 戻り値:押されてないときNone、押されたときvaluesのなかの一つが返る。python.spec 0はfalseと判定されることに注意して使う
    s = [v for k, v in zip((pyxel.KEY_LEFT, pyxel.KEY_UP, pyxel.KEY_RIGHT, pyxel.KEY_DOWN, pyxel.GAMEPAD_1_LEFT, pyxel.GAMEPAD_1_UP, pyxel.GAMEPAD_1_RIGHT, pyxel.GAMEPAD_1_DOWN), values+values) if poll(k)]
    return s[0] if s else None


def btnpA(): return pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.GAMEPAD_1_A)
def btnpB(): return pyxel.btnp(pyxel.KEY_X) or pyxel.btnp(pyxel.GAMEPAD_1_B)
def blinker(): return pyxel.frame_count // 16 % 2  # 右、左、右、左、の変化用
# def chip(n): return n//1024, n % 1024//32, n % 1024 % 32


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
Font1.chars[48]['glyph'][3] = 'A0'  # 0の中の点を無くす
# Font1.fx, Font1.fy = 2, 3  # 外から調整できる


def draw_text(x, y, text, col=7): [pyxel.pset(x+u, y+v, col) for u, v in Font1.points(text)]
def draw_textC(x, y, text): draw_text(x, y, text, 8 if g_player.hp <= 0 else 10 if g_player.hp < g_player.maxhp / 2 else 7)  # カラー
def draw_frameC(x, y, w, h): draw_frame(x, y, w, h, 2 if g_player.hp <= 0 else 1 if g_player.hp < g_player.maxhp / 2 else 0)  # カラー


def draw_frame(x, y, w, h, col=0):  # col 0: white 1:yellow 2:red
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
    # def draw(self): pass

    def releaseback(self, fmulti=False):  # 閉じてフォーカスを返す、を実現するためのもの
        global g_state  # global宣言忘れがちなので、できるだけここを使う
        if g_state == self:
            g_state = self.original_state
            if fmulti and SelectBox == type(self.original_state):  # サブメニューから一気に返る仕組み
                g_state = g_state.original_state


g_state = None
ToZenkaku = str.maketrans({chr(0x0021 + i): chr(0xFF01 + i) for i in range(94)})


class SelectBox(State):  # ２段に並んだものでも簡潔に表現できると思うが、128ピクセルでは縦のみになった。
    def __init__(self, ox, oy, texts, commands=None):  # コマンドを指定しないときは、あとからindexを読んで使う
        self.cursor = "●"
        if len(texts) > 0:
            self.w, self.h = Font1.box("あ")[0] * (max([len(s) for s in texts]) + 1), Font1.box("あ")[1] * len(texts)
            self.index, self.ox, self.oy, self.texts, self.commands = 0, ox if ox >= 0 else -ox-self.w, oy if oy >= 0 else -oy-self.h, texts, commands or (lambda: None,)*len(texts)
            self.state4indexes = [[None, i-1, None, i+1] for i in range(len(self.texts))]  # 各index時にどのキーを押すと、次の状態はどうなるかの表。無効にするキーにはNoneを指定。
            self.state4indexes[0][1], self.state4indexes[-1][3] = None, None  # ２つなら ((None, None, None, 1), (None, 0, None, None)) ができる。
        else:
            self.update, self.draw = self.releaseback, lambda: None  # アイテムが０個のサブメニューSelectBoxを作ったとき、ここでreleasebackすると、元のコマンド後のreleasebackでそれも閉じでしまう。ので１フレームは動作させる苦肉の策。
        self.sounds = {"OK": 1, "Cancel": 2, "Move": 0}
    YesNoParameters = (-122, -84, ("はい", "いいえ"))  # ox oy に負の値を指定したときは右下を指定したものとして左上を計算で求める

    def update(self):
        if btnpA():
            pyxel.play(3, self.sounds["OK"])
            self.commands[self.index]()  # この中でg_stateを変更しても、次行も実行されるため、typeを見て動作を変える対策をした
            self.releaseback(True)  # g_stateを変更したが、効果があるのは次フレームから
        if btnpB():  # Bは何もせずにフォーカスを返す
            self.index = -1  # index -1: Cancel
            pyxel.play(3, self.sounds["Cancel"])
            self.releaseback()
        k = arrowkeysp(self.state4indexes[self.index])  # 押したキーに対応する次のindex値が返る
        if None is not k:  # 0にしたい場合もあるので、Noneとの比較を忘れずに
            self.index = k
            pyxel.play(3, self.sounds["Move"])

    def draw(self):
        self.original_state.draw()
        draw_frameC(self.ox, self.oy, self.w, self.h)
        draw_textC(self.ox, self.oy, "".join([f"　{s}\n" for s in self.texts]))
        draw_textC(self.ox, self.oy, "\n" * self.index + self.cursor)  # "→") # misaki_gothicで▶が見つからない。文字にすると別色にもできる


class TextBox(State):
    def __init__(self,  text, text2=""):
        self.text, self.text2 = text.translate(ToZenkaku) if text else "", text2
        self.update = self._update().__next__
        self.speed, self.sounds = TextBox.Speed, {"Step": 2, "Go": 1}
        self.sy = 0
    Speed = 3
    Lines, Len = 4, 14
    OX, OY = 10, 91
    W, _H = Font1.box("あ"*Len)
    H = _H * Lines

    def _update(self):
        ret_wz_tab = "\n　　" if re.match(r"\n?.「", self.text) or "　　" == self.text2[:2] or re.match(".「", self.text2) else "\n"
        for i, c in enumerate(self.text):  # 一文字ずつ描画(スペース,\nと🔻は別な動作をさせる)
            if "　" == c:  # スペースはウエイトなし
                self.text2 += c
                continue
            if "🔻" == c:  # クリック待ち
                self.speed = TextBox.Speed
                yield TextBox.V()
                continue
            if "\n" != c and len(self.text2.split("\n")[-1]) >= TextBox.Len:  # 自動改行
                c = "\n"+c  # 指定改行とコードを共通化させるため、一時的にcを変更(改行のコードも通り、文字のコードも通る)
            if "\n" == c[0]:
                self.text2 += ret_wz_tab
                s = self.text2.split("\n")
                if len(s) > self.Lines:  # scroll up
                    for self.sy in range(0, self._H, 2):
                        if btnpA():
                            self.speed = 0  # Aボタンによるアニメスキップ(の代わりに高速動作)
                        yield
                    self.text2, self.sy = "\n".join(s[-self.Lines:]), 0
                if "\n" == c:
                    continue
                else:
                    c = c[1:]  # 一時的に変更していたcを戻し、fallthrough
            self.text2 += c  # ここからほか全ての文字の動作
            pyxel.play(3, self.sounds["Step"])
            for j in range(self.speed):  # ウエイト
                if btnpA():  # self.updateをたくさん呼べばいい？→ジェネレーター内から自身は呼べない
                    self.speed = 0  # Aボタンによるアニメスキップ(の代わりに高速動作)
                yield
        yield self.releaseback()

    def draw_just(self):
        draw_frameC(self.OX, self.OY, self.W, self.H)
        pyxel.clip(self.OX, self.OY, self.W, self.H)
        draw_textC(self.OX, self.OY-self.sy, self.text2)
        pyxel.clip()

    def draw(self):
        self.original_state.draw()
        self.draw_just()

    class V(State):  # ▼を表示してクリック待ち
        def update(self):
            if btnpA() or btnpB() or None != arrowkeysp():
                pyxel.play(3, self.original_state.sounds["Go"])
                self.releaseback()
        Cursor = "▼"

        def draw(self):
            self.original_state.draw()
            pyxel.rect(110, 120,  8, 8, 0)
            draw_textC(110, 120, TextBox.V.Cursor)


class Field(State):
    def __init__(self, x=12, y=2):
        self.mapid, self.mapleft, self.maptop, self.mapright, self.mapbottom, self.bgcolor = 0, 0, 0, 256, 256, 12
        self.x, self.y = x, y  # 主人公の位置
        self.direction = 3  # 主人公の向き
        self.sx, self.sy = 0, 0  # マスの途中のアニメに使う
        self.update = self._update().__next__
        self.idle_start = pyxel.frame_count
        self.traps = ((12, 2, lambda: Field.Blackout(lambda: Castle(22, 15))), )  # 街、階段とか # lambdaにくるんで「あとで実行」することをここで書ける(遅延評価)
        self.textbox = None
        self.original_state = None  # fieldより下はないはずなので切っておく
        pyxel.playm(self.Music, loop=True)
        for npc in self. NPCs:  # どうやって渡せばいいか？
            npc.field = self
    NPCs = []  # NPC 扉、宝箱など。２度作られないようにクラス変数にしておく
    Music = 1

    def isblocked(self, x, y):
        return self.mapleft > x or self.maptop > y or x > self.mapright or y > self.mapbottom or \
            pyxel.tilemap(self.mapid).get(x, y) in (0, 4, 33, 34, 42) or \
            [npc for npc in self.NPCs if x == npc.x and y == npc.y]  # pyxel.spec タイル範囲外アクセスで落ちる

    def _update(self):
        while True:
            [npc.update() for npc in self.NPCs]
            if btnpA() or btnpB():
                dx, dy = (-1, 0, 1, 0)[self.direction], (0, -1, 0, 1)[self.direction]
                if [npc.act() for npc in self.NPCs if self.x+dx == npc.x and self.y+dy == npc.y]:  # 話しかけるなど
                    pass
                else:  # 話す相手がいなければ、コマンドをだす
                    command = None
                    def yakusou(): nonlocal command; command = self._yakusou
                    spells = []
                    spellcommands = None
                    items = [i for i in g_player.items if i in ("やくそう")]  # フィールドで使えるものだけ
                    itemcommands = [{"やくそう": yakusou}[i]for i in items]
                    yield SelectBox(80, 8, ("じゅもん", "どうぐ"), (lambda: SelectBox(84, 4, spells, spellcommands), lambda: SelectBox(84, 4, items, itemcommands)))
                    if command:
                        for it in command():  # コルーチン(ジェネレーター)の連続呼び出し
                            self.textbox = TextBox(it, self.textbox.text2 if self.textbox else "")
                            yield
                        self.textbox = None
            # if btnpB():  # 現在は機能が割り当てられていない
            #     pass
            if pyxel.btnp(pyxel.KEY_F5):
                pyxel.load("./assets/pyxel_rpg.pyxres")
            if pyxel.btnp(pyxel.KEY_W):
                save()
            d = arrowkeysp((0, 1, 2, 3), pyxel.btn)
            if None is not d:
                self.idle_start = pyxel.frame_count
                self.direction, dx, dy = d, (-1, 0, 1, 0)[d], (0, -1, 0, 1)[d]
                if self.isblocked(self.x+dx, self.y+dy):
                    pyxel.play(3, 2)
                    dx, dy = 0, 0  # 壁などに向かおうとしたら8frame動かない(音を出す時間のため?)
                for i in range(1, 8, 1):  # マスからマスの途中はアニメ
                    self.sx, self.sy = self.sx + dx, self.sy + dy
                    yield
                self.x, self.y, self.sx, self.sy = self.x + dx, self.y + dy, 0, 0
                if dx != 0 or dy != 0:  # 動いたときだけイベント発生
                    if g_player.hp <= 0:
                        yield TextBox(f"{g_player.name}はしんでしまった！🔻")
                        yield Title()
                    elif [command() for x, y, command in self.traps if x == self.x and y == self.y]:
                        pass
                    elif m := self.encont_monster(self.x, self.y):
                        Battle(m)
            yield

    def draw(self):
        pyxel.cls(self.bgcolor)
        pyxel.bltm((self.mapleft-self.x+7.5)*8-self.sx, (self.maptop-self.y+7.5)*8-self.sy, self.mapid, self.mapleft, self.maptop, self.mapright-self.mapleft, self.mapbottom-self.maptop)  # 何も考えずに全マップ描画
        [npc.draw((-self.x+7.5)*8-self.sx, (-self.y+7.5)*8-self.sy) for npc in self.NPCs]
        pyxel.blt(64-4, 64-4-1, 0, (self.direction*2+blinker())*8, 32, 8, 8, 0)  # 中央に主人公を
        if pyxel.frame_count - self.idle_start > 45:
            draw_playerstatus()
        if self.textbox:
            self.textbox.draw_just()
        # pyxel.text(0, 0, f"{self.x: 3}: {self.y: 3}", 7)

    def encont_monster(self, x, y): return Slime() if 5 == random.randrange(15) else None

    def _yakusou(self):
        yield f"{g_player.name}はやくそうをつかった！"
        pyxel.play(3, 17)
        for _ in range(8):  # SE待ち
            yield ""
        v = 5 + random.randrange(5)
        g_player.hp = min(g_player.hp + v, g_player.maxhp)
        g_player.items.remove("やくそう")
        yield f"\n{g_player.name}のＨＰは{v}かいふくした！🔻"

    class Blackout(State):
        def __init__(self, command):
            self.command = command
            self.update = self._update().__next__
            pyxel.stop()
            pyxel.play(3, 9)

        def _update(self):
            for _ in range(20):
                yield
            yield self.command()

        def draw(self): pyxel.cls(1)


class NPC:  # ベースクラスを少年に使ってる……
    def __init__(self, x, y): self.x, self.y, self.field = x, y, None
    def update(self): pass
    def draw(self, ox, oy): pyxel.blt(ox+self.x*8, oy+self.y*8-1, 0, 32+blinker()*8, 48, 8, 8, 0)
    def act(self): TextBox(("青は藍より出でて藍より青し。🔻\n漢字も使えるよ。🔻", "あおはあいよりいでてあいよりあおし。🔻\nひらがなのほうがいいかな？🔻")[random.randrange(2)])


class RandomWalker(NPC):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.update = self._update().__next__
        self.sx, self.sy = 0, 0

    def draw(self, ox, oy): pyxel.blt(ox+self.x*8+self.sx, oy+self.y*8+self.sy-1, 0, 32+blinker()*8, 48, 8, 8, 0)

    def _update(self):
        while True:
            for _ in range(16*3):
                yield
            d = random.randrange(4+3)
            dx, dy = (-1, 0, 1, 0, 0, 0, 0)[d], (0, -1, 0, 1, 0, 0, 0)[d]  # 動かないときも入れることで全員が同じタイミングで動くようにしない
            if not (self.field.isblocked(self.x+dx, self.y+dy) or (self.x+dx == self.field.x or self.y+dy == self.field.y)):
                for i in range(0, 8, 1):
                    self.sx, self.sy = self.sx+dx, self.sy+dy
                    yield
                self.x, self.y, self.sx, self.sy = self.x+dx, self.y+dy, 0, 0


class King(NPC):
    def draw(self, ox, oy): pyxel.blt(ox+self.x*8, oy+self.y*8-1, 0, 0+blinker()*8, 48, 8, 8, 0)
    def act(self): TextBox("王「わしはおうさまじゃよ」🔻")  # シンプルなテキストだけならこれだけで行ける。


class ShopKeeperDummy(NPC):  # 机に設定する
    def draw(self, ox, oy): pass
    def act(self): Shopping()  # 途中でSelectBoxが入る複雑な会話はStateをつかって


class Chest(NPC):
    def __init__(self, x, y, item): self.x, self.y, self.item = x, y, item  # item:整数ならゴールド(お金)が入っているものとする
    def draw(self, ox, oy): pyxel.blt(ox+self.x*8, oy+self.y*8, 0, 80, 8, 8, 8, 0)

    def act(self):
        self.update = self.clearing  # テキストのあとに、動作するように
        v = f"{self.item}ゴールド" if type(self.item) is int else self.item
        TextBox(f"{g_player.name}はたからばこをあけた！🔻{v}をてにいれた！🔻")

    def clearing(self):
        if type(self.item) is int:
            g_player.gold += self.item
        else:
            g_player.items += [self.item]
        g_state.NPCs.remove(self)

# QuizBoy


class Shopping(State):
    def __init__(self):
        self.textbox = None
        self.update = self._update().__next__
        self.goods = (("やくそう", 6), ("どくばり", 11))

    def _update(self):
        self.textbox = TextBox("＊「ここはどうぐやです。なにをおもとめですか？")
        yield
        while True:
            s = SelectBox(80, 8, [it[0]for it in self.goods])
            yield  # 次の回でindexを読む
            if s.index < 0:  # Bボタンでキャンセルしたときだけ会話を終えることができる？
                break
            if self.goods[s.index][1] <= g_player.gold:
                self.textbox = TextBox(f"\n{self.goods[s.index][0]}は{self.goods[s.index][1]}ゴールドです。よろしいですか？", self.textbox.text2)  # 新しいTextBoxを作っているが、前のtext2を渡して、続いているように見せる
                yield
                yesno = SelectBox(*SelectBox.YesNoParameters)
                yield  # 次の回でindexを読む
                if yesno.index == 0:
                    g_player.items += [self.goods[s.index][0]]
                    g_player.gold -= self.goods[s.index][1]
                    self.textbox = TextBox("\nありがとうございます。", self.textbox.text2)
                    yield
            else:
                self.textbox = TextBox(f"\n{self.goods[s.index][0]}は{self.goods[s.index][1]}ゴールドです。おかねがたりないようです", self.textbox.text2)
                yield
            self.textbox = TextBox("\nほかにもなにかおもとめですか？", self.textbox.text2)
            yield
        yield TextBox("\nまたのお越しを！」🔻", self.textbox.text2)
        yield self.releaseback()

    def draw(self):
        self.original_state.draw()
        if self.textbox:
            self.textbox.draw_just()  # TextBoxからフォーカスが帰ってきても、描画し続けることで続いているように見せる。


class Battle(State):
    def __init__(self,  monster):
        self.monster, self.textbox = monster, None
        self.update = self._update().__next__
        self.offset = (0, 0)
        pyxel.playm(3, loop=True)

    def _update(self):
        yield  # opening animation
        self.textbox = TextBox(f"{self.monster.name}があらわれた！")
        yield
        while True:
            command = None
            def attack(): nonlocal command; command = self._attack
            def runaway(): nonlocal command; command = self._runaway
            def yakusou(): nonlocal command; command = self._yakusou
            spells = g_player.spells
            spellcommands = None
            items = [i for i in g_player.items if i in ("やくそう")]  # 戦闘中に使えるものだけ
            itemcommands = [{"やくそう": yakusou}[i] for i in items]
            while not command:  # 命令が得られるまでSelectBoxを出す。(Bボタンで何度キャンセルされても)
                yield SelectBox(80, 8, ("たたかう", "じゅもん", "どうぐ", "にげる"), (attack, lambda: SelectBox(84, 4, spells, spellcommands), lambda: SelectBox(84, 4, items, itemcommands), runaway))
            command2 = self.monster.choice(self._attack, self._runaway, self._yakusou)
            for it in command(g_player, self.monster):  # コルーチン(ジェネレーター)の連続呼び出し
                self.textbox = TextBox(it, self.textbox.text2)
                yield
            if self.monster.hp <= 0:
                break
            for it in command2(self.monster, g_player):  # コルーチン(ジェネレーター)の連続呼び出し
                self.textbox = TextBox(it, self.textbox.text2)
                yield
            if g_player.hp <= 0:
                yield TextBox(f"\n{g_player.name}はしんでしまった！🔻", self.textbox.text2)
                yield Title()
        self.textbox = TextBox(f"\n{self.monster.name}をたおした！🔻\n{self.monster.gold}ゴールドと、{self.monster.experience}のけいけんちをえた！🔻", self.textbox.text2)
        yield
        g_player.gold += self.monster.gold
        g_player.experience += self.monster.experience
        pyxel.playm(self.original_state.Music, loop=True)
        yield self.releaseback()

    def draw(self):
        self.original_state.draw()
        pyxel.rect(32+self.offset[0], 32+self.offset[1], 64, 64, 0)
        self.monster.draw(*self.offset)
        draw_playerstatus()  # 下になるので再度描画
        if self.textbox:
            self.textbox.draw_just()

    def _attack(self, offence, deffence):
        tab = "" if offence == g_player else "　"
        yield f"\n{tab}{offence.name}のこうげき！"
        pyxel.play(3, 16)
        for i in range(8):  # SE待ち
            if offence == g_player:
                self.offset = ((-2, -2), (-2, 2), (2, 2), (-2, 2), (1, -2), (-1, 1), (0, -1), (0, 1))[i]
            yield ""
        v = 4 + random.randrange(3)
        deffence.hp -= v
        yield f"\n{tab}{deffence.name}に{v}のダメージ！"

    def _runaway(self, offence, deffence):
        tab = "" if offence == g_player else "　"
        yield f"\n{tab}{offence.name}は逃げ出した！"
        for _ in range(8):  # 待ち
            yield ""
        self.releaseback()
        yield ""

    def _yakusou(self, offence, _):
        tab = "" if offence == g_player else "　"
        yield f"\n{tab}{offence.name}はやくそうをつかった！"
        pyxel.play(3, 17)
        for _ in range(8):  # SE待ち
            yield ""
        v = 5 + random.randrange(3)
        offence.hp = min(offence.hp + v, offence.maxhp)
        offence.items.remove("やくそう")
        yield f"\n{tab}{offence.name}のＨＰは{v}かいふくした！"


def level(exp): return 1


class Charactor:
    def __init__(self, name, maxhp, maxmp, hp, mp, spells, items, gold, experience, agility):
        self.name, self.maxhp, self.maxmp, self.hp, self.mp, self.spells, self.items, self.gold, self.experience, self.agility = name, maxhp, maxmp, hp, mp, spells, items, gold, experience, agility
        self.doku = False


g_player = Charactor("ああああ", 13, 0, 13, 0, [], [], 120, 0, 7)


def draw_playerstatus():
    doku = "どく" if g_player.doku else ""
    draw_frameC(8, 8, 48, 32)
    draw_textC(8, 8, f"{g_player.name:　<4} L{level(g_player.experience): 2}\nＨＰ {g_player.hp: 3}/{g_player.maxhp: 3}\nＭＰ {g_player.mp: 3}/{g_player.maxmp: 3}\nＧ {g_player.gold: 4} {doku}")


class Slime(Charactor):
    def __init__(self): super().__init__("スライム", 5+random.randrange(2), 0, 7, 0, [], (["やくそう"] if 3 == random.randrange(5) else []), 3+random.randrange(2), 3+random.randrange(2), 4)
    def draw(self, ox, oy): pyxel.blt(56+ox, 56+oy, 2, 0, 0, 16, 16, 15)
    def choice(self, attack, runaway, yakusou): return random.choice([attack]*self.hp+[runaway]*2+([yakusou]*2 if "やくそう" in self.items else []))
# Mimic


class Castle(Field):
    def __init__(self, x, y):
        super().__init__()
        self.mapid, self.mapleft, self.maptop, self.mapright, self.mapbottom, bgcolor = 1, 9, 0, 32, 17, 3
        self.x, self.y = x, y
        self.encont_monster = lambda x, y: None
        def field(): Field.Blackout(lambda: Field())
        self.traps = ((21, 16, field), (22, 16, field), (23, 16, field), (24, 5, lambda: Field.Blackout(lambda: Palace())), )
    NPCs = [NPC(11, 13), ShopKeeperDummy(12, 13), RandomWalker(13, 2), RandomWalker(15, 5), RandomWalker(26, 13), ]
    Music = 2


class Palace(Field):
    def __init__(self, is_opening=False):
        super().__init__()
        self.mapid, self.mapleft, self.maptop, self.mapright, self.mapbottom = 1, 0, 0, 10, 6
        self.x, self.y = 8, 4
        self.encont_monster = lambda x, y: None
        self.traps = ((8, 4, lambda: Field.Blackout(lambda: Castle(24, 5))),)
        if is_opening:
            self.x, self.y = 4, 4
            self.direction = 1
            TextBox(f"王「よくぞわが呼びかけに応えてくれた！ゆうしゃ{g_player.name}よ！🔻\n……せつめいははぶくが、ぼうけんにでてまおうをたおしてきてくれ！」🔻")
    NPCs = [RandomWalker(2, 2), King(4, 1), Chest(1, 3, "やくそう"), Chest(1, 4, 99)]
    Music = 2


class Title(State):
    def __init__(self):
        global g_player
        g_player = Charactor(g_player.name, 13, 0, 13, 0, [], [], 10, 0, 7)
        pyxel.playm(0, loop=True)

    def update(self):
        # def load(): TextBox("＊「じゅげむじゅげむごこうの\nすりきれかいじゃりすいぎょのすいぎょうまつうんらいまつふうらいまつくうねるところにすむところやぶらこうじのぶらこうじぱいぽぱいぽぱいぽのしゅーりんがんしゅーりんがんのぐーりんだいぐーりんだいのぽんぽこぴーのぽんぽこなのちょうきゅうめいのちょうすけ🔻")
        s = SelectBox(40, 76, ("はじめから", "つづきから"), (lambda: Palace(True), load))
        s.sounds = {"OK": 0, "Cancel": 0, "Move": 0}

    def draw(self):
        pyxel.cls(0)
        pyxel.blt(32, 30, 1, 0, 0, 64, 16)


def save():
    with open('xxx.dump', 'wb') as f:
        pickle.dump(Palace.NPCs, f)


def load():
    with open('xxx.dump', 'rb') as f:
        Palace.NPCs = pickle.load(f)
    Palace()


pyxel.init(128, 128, caption="An RPG Sample")
pyxel.load("./assets/pyxel_rpg.pyxres")
Title()  # pyxel.initより後ろに書く
pyxel.run(lambda: g_state.update(), lambda: g_state.draw())
