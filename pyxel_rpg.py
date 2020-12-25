# import iteritems
import random
import re

import pyxel


def arrowkeys(values=(0, 1, 2, 3)):
    s = [v for k, v in zip((pyxel.KEY_LEFT, pyxel.KEY_UP, pyxel.KEY_RIGHT, pyxel.KEY_DOWN, pyxel.GAMEPAD_1_LEFT, pyxel.GAMEPAD_1_UP, pyxel.GAMEPAD_1_RIGHT, pyxel.GAMEPAD_1_DOWN), values+values) if pyxel.btn(k)]
    return s[0] if s else None


def arrowkeysp(values=(0, 1, 2, 3)):  # 戻り値:押されてないときNone、押されたときvaluesのなかの一つが返る。python.spec 0はfalseと判定されることに注意して使う
    s = [v for k, v in zip((pyxel.KEY_LEFT, pyxel.KEY_UP, pyxel.KEY_RIGHT, pyxel.KEY_DOWN, pyxel.GAMEPAD_1_LEFT, pyxel.GAMEPAD_1_UP, pyxel.GAMEPAD_1_RIGHT, pyxel.GAMEPAD_1_DOWN), values+values) if pyxel.btnp(k)]
    return s[0] if s else None


def btnpA(): return pyxel.btnp(pyxel.KEY_Z, 0, 0) or pyxel.btnp(pyxel.GAMEPAD_1_A, 0, 0)
def btnpB(): return pyxel.btnp(pyxel.KEY_X, 0, 0) or pyxel.btnp(pyxel.GAMEPAD_1_B, 0, 0)


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


# Font1 = BDF("./assets/knj10.unicode.bdf")  # ナガ１０ 注意:多くのbdfフォントファイルはutf-8への変換が必要
Font1 = BDF("./assets/misaki_gothic_2nd.bdf")
Font1.chars[48]['glyph'][3] = 'A0'  # 0の中の点を無くす
# Font1.fx, Font1.fy = 2, 3  # @python.spec 外から調整できる


def draw_text(x, y, text, col=7): [pyxel.pset(x+u, y+v, col) for u, v in Font1.points(text)]
def draw_textC(x, y, text): draw_text(x, y, text, 10 if g_player.hp < g_player.maxhp / 2 else 8 if g_player.hp <= 0 else 7)  # カラー
def draw_frameC(x, y, w, h): draw_frame(x, y, w, h, 1 if g_player.hp < g_player.maxhp / 2 else 2 if g_player.hp <= 0 else 0)  # カラー


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


class SelectBox(State):  # ２段に並んだものでも簡潔に表現できると思うが、128ピクセルでは縦のみになった。
    def __init__(self, ox, oy,  texts, commands=None):  # コマンドを指定しないときは、あとからindexを読む
        self.cursor, self.w, self.h = "●", Font1.box("あ")[0] * (max([len(s) for s in texts]) + 1), Font1.box("あ")[1] * len(texts)
        self.index, self.ox, self.oy, self.texts, self.commands = 0, ox if ox >= 0 else -ox-self.w, oy if oy >= 0 else -oy-self.h, texts, commands or (lambda: None,)*len(texts)
        if len(texts) > 0:
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
        k = arrowkeysp(self.state4indexes[self.index])
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
        ToZenkaku = str.maketrans({chr(0x0021 + i): chr(0xFF01 + i) for i in range(94)})
        self.text, self.text2 = text.translate(ToZenkaku), text2
        self.update = self._update().__next__
        self.sounds = {"Step": 2, "Go": 1}
        self.sy = 0
    Speed = 3
    Lines, Len = 4, 14
    OX, OY = 10, 91
    W, _H = Font1.box("あ"*Len)
    H = _H * Lines

    def _update(self):
        for c in self.text:  # 一文字ずつ描画(スペース,\nと🔻は別な動作をさせる)
            self.text2 += c
            if "　" == c:  # ウエイトなし
                continue
            if "\n" == c:
                s = self.text2.split("\n")
                if len(s) > self.Lines:  # 3 # scroll up
                    for self.sy in range(0, self._H, 2):
                        if btnpA():
                            self.text2 = self.text.translate(str.maketrans({'🔻': ''}))
                            break  # 二重ループを抜ける
                        yield
                    self.text2, self.sy = '\n'.join(s[-self.Lines:]), 0
                continue
            if "🔻" == c:  # クリック待ち
                self.text2 = self.text2[:-1]
                yield TextBox.V()
                continue
            # ここからほか全ての文字の動作
            pyxel.play(3, self.sounds["Step"])
            for j in range(self.Speed):  # ウエイト
                if btnpA():
                    self.text2 = self.text.translate(str.maketrans({'🔻': ''}))
                    yield TextBox.V()  # アニメをスキップするときは必ず🔻付き？
                    break  # 二重ループを抜ける
                yield
            else:
                continue
            break
        # yield TextBox.V(self)  # クリック待ち
        self.releaseback()
        yield

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
            if btnpA():
                pyxel.play(3, self.original_state.sounds["Go"])
                self.releaseback()
        Cursor = "▼"

        def draw(self):
            self.original_state.draw()
            pyxel.rect(110, 120,  8, 8, 0)
            draw_textC(110, 120, TextBox.V.Cursor)


def fold_text(s, length=TextBox.Len, delimiter="\n"):  # TextBoxに組み込んで自動で……できてない
    return s if len(s) <= length else s[: length] + delimiter + fold_text(s[length:], length, delimiter)


def fold_text2(s, speaker="＊"):
    assert len(speaker) == 1
    return speaker + "「" + fold_text(s, TextBox.Len-2, "\n　　")


class Field(State):
    def __init__(self, x=12, y=2):
        self.mapid, self.mapleft, self.maptop, self.mapright, self.mapbottom, self.bgcolor = 0, 0, 0, 256, 256, 12
        self.x, self.y = x, y  # 主人公の位置
        self.direction = 3  # 主人公の向き
        self.sx, self.sy = 0, 0  # マスの途中のアニメに使う
        self.update = self._update().__next__
        self.idle_start = pyxel.frame_count
        self.draw_status = draw_playerstatus  # 買い物のときは切り替える
        self.traps = ((12, 2, lambda: Field.Blackout(lambda: Castle(22, 15))), )  # 街、階段とか # lambdaにくるんで「あとで実行」することをここで書ける(遅延評価)
        self.npcs = []  # NPC 扉、宝箱など

    def _update(self):
        while True:
            [npc.update() for npc in self.npcs]
            if btnpA():
                dx, dy = (-1, 0, 1, 0)[self.direction], (0, -1, 0, 1)[self.direction]
                if [npc.act() for npc in self.npcs if self.x+dx == npc.x and self.y+dy == npc.y]:  # 話しかけるなど、か
                    pass
                else:  # コマンドをだす
                    def spell(): SelectBox(84, 4, g_player.spells)
                    def item(): SelectBox(84, 4, g_player.items)
                    SelectBox(80, 8, ("じゅもん", "どうぐ"), (spell, item))
            if btnpB():  # 現在は機能が割り当てられていない
                pass
            d = arrowkeys((0, 1, 2, 3))
            if None is not d:
                self.idle_start = pyxel.frame_count
                self.direction, dx, dy = d, (-1, 0, 1, 0)[d], (0, -1, 0, 1)[d]
                if self.mapleft > self.x + dx or self.maptop > self.y + dy or self.x + dx > self.mapright or self.y + dy > self.mapbottom or pyxel.tilemap(self.mapid).get(self.x+dx, self.y+dy) in (0, 4, 33, 34, 42) or [npc for npc in self.npcs if self.x+dx == npc.x and self.y+dy == npc.y]:  # pyxel.spec タイル範囲外アクセスで落ちる
                    pyxel.play(3, 1)
                    dx, dy = 0, 0  # 壁などに向かおうとしたら8frame動かない(音を出す時間のため?)
                for i in range(1, 8, 1):  # 8x8のマスの途中はアニメ
                    self.sx, self.sy = self.sx + dx, self.sy + dy
                    yield
                else:
                    self.x, self.y, self.sx, self.sy = self.x + dx, self.y + dy, 0, 0
                    # continue
                    if dx != 0 or dy != 0:  # 動いたときだけイベント発生
                        if [command() for x, y, command in self.traps if x == self.x and y == self.y]:  # 街、階段など
                            pass
                        elif m := self.encont_monster(self.x, self.y):
                            Battle(m)
            yield

    def draw(self):
        pyxel.cls(self.bgcolor)
        pyxel.bltm((self.mapleft-self.x+7.5)*8-self.sx, (self.maptop-self.y+7.5)*8-self.sy, self.mapid, self.mapleft, self.maptop, self.mapright-self.mapleft, self.mapbottom-self.maptop)  # 全マップ描画
        [npc.draw((-self.x+7.5)*8-self.sx, (-self.y+7.5)*8-self.sy) for npc in self.npcs]
        pyxel.blt(64-4, 64-4-1, 0, self.direction*16+(pyxel.frame_count//16 % 2)*8, 32, 8, 8, 0)  # 中央に主人公を
        if pyxel.frame_count - self.idle_start > 45:
            self.draw_status()
        pyxel.text(0, 0, f"{self.x}: {self.y}", 7)

    def encont_monster(self, x, y):
        return Slime() if 5 == random.randrange(15) else None

    class Blackout(State):
        def __init__(self, command):
            self.command = command
            self.update = self._update().__next__

        def _update(self):
            pyxel.play(3, 9)
            for _ in range(15):
                yield
            self.command()
            yield

        def draw(self): pyxel.cls(1)


class NPC:  # ベースクラスをおうさまに使ってる……
    def __init__(self, x, y): self.x, self.y = x, y
    def update(self): pass
    def draw(self, ox, oy): pyxel.blt(ox+self.x*8, oy+self.y*8, 0, 0+(pyxel.frame_count//16 % 2)*8, 48, 8, 8, 0)
    def act(self): TextBox(fold_text2("わしはおうさまじゃよ」🔻", "王"))  # シンプルなテキストだけならこれだけで行ける。


class ShopKeeper(NPC):
    def draw(self, ox, oy): pyxel.blt(ox+self.x*8, oy+self.y*8, 0, 32+(pyxel.frame_count//16 % 2)*8, 48, 8, 8, 0)
    def act(self): GoodsShop()  # 複雑なものはStateをつかって


class GoodsShop(State):
    def __init__(self):
        self.textbox = None
        self.update = self._update().__next__
        self.goods = (("やくそう", 6), ("どくばり", 11))

    def _update(self):
        self.original_state.draw_status = draw_playerproperty
        self.textbox = TextBox(fold_text2("ここはどうぐやです。なにをおもとめですか？」"))
        yield
        while True:
            s = SelectBox(80, 8, [it[0]for it in self.goods])
            yield  # 次の回でindexを読む
            if s.index < 0:
                break
            self.textbox = TextBox("\n"+fold_text2(f"{self.goods[s.index][0]}は{self.goods[s.index][1]}ゴールドです。よろしいですか？」"), self.textbox.text2)
            yield
            yesno = SelectBox(*SelectBox.YesNoParameters)
            yield  # 次の回でindexを読む
            if yesno.index == 0:
                g_player.items += self.goods[s.index][0]
                g_player.gold -= self.goods[s.index][1]
                self.textbox = TextBox("\n"+fold_text2("ありがとうございます。」"), self.textbox.text2)
                yield
            self.textbox = TextBox("\n"+fold_text2("ほかにもなにかおもとめですか？」"), self.textbox.text2)
            yield
        TextBox("\n"+fold_text2("またのお越しを！」🔻"), self.textbox.text2)
        yield
        self.original_state.draw_status = draw_playerstatus
        self.releaseback()
        yield

    def draw(self):
        self.original_state.draw()
        if self.textbox:
            self.textbox.draw_just()


class Battle(State):
    def __init__(self,  monster):
        self.monster, self.textbox = monster, None
        self.update = self._update().__next__

    def _update(self):
        yield  # opening animation
        self.textbox = TextBox(fold_text(f"{self.monster.name}があらわれた！"))
        yield
        while True:
            command = None
            def attack(): nonlocal command; command = self._attack
            def spell(): SelectBox(84, 4, g_player.spells)
            def item(): SelectBox(84, 4, g_player.items)
            def runaway(): nonlocal command; command = self._runaway
            while not command:  # 命令が得られるまでSelectBoxを出す。(Bボタンで何度キャンセルされても)
                SelectBox(80, 8, ("たたかう", "じゅもん", "どうぐ", "にげる"), (attack, spell, item, runaway))
                yield
            for it in command(g_player, self.monster):  # コルーチン(ジェネレーター)の連続呼び出し
                self.textbox = TextBox(fold_text(it), self.textbox.text2)
                yield
            if self.monster.hp <= 0:
                break
            for it in command(self.monster, g_player):  # コルーチン(ジェネレーター)の連続呼び出し
                self.textbox = TextBox(fold_text(it), self.textbox.text2)
                yield
        g_player.gold += self.monster.gold
        g_player.experience += self.monster.experience
        self.textbox = TextBox(fold_text(f"\n{self.monster.name}をたおした！")+"🔻\n"+fold_text(f"{self.monster.gold}ゴールドと、{self.monster.experience}のけいけんちをえた！🔻"), self.textbox.text2)
        yield
        self.releaseback()
        yield

    def draw(self):
        self.original_state.draw()
        pyxel.rect(32, 32, 64, 64, 0)
        self.monster.draw()
        draw_playerstatus()  # 下になるので再度描画
        if self.textbox:
            self.textbox.draw_just()

    def _attack(self, offence, deffence):
        tab = "" if offence == g_player else "　"
        yield fold_text(f"\n{tab}{offence.name}のこうげき！")
        # pyxel.play(3, 1)
        for _ in range(8):  # SE待ち
            yield ""
        deffence.hp -= 5
        yield fold_text(f"\n{tab}{deffence.name}に5のダメージ！")

    def _runaway(self, offence, deffence):
        tab = "" if offence == g_player else "　"
        yield fold_text(f"\n{tab}{offence.name}は逃げ出した！")
        for _ in range(5):  # 待ち
            yield ""
        self.releaseback()
        yield ""


def level(exp): return 1


class Charactor:
    def __init__(self, name, maxhp, maxmp, hp, mp, gold, experience, agility):
        self.name, self.maxhp, self.maxmp, self.hp, self.mp, self.gold, self.experience, self.agility = name, maxhp, maxmp, hp, mp, gold, experience, agility
        self.spells, self.items, self.doku, self.noroi = [], [], False, False


g_player = Charactor("ああああ", 13, 0, 13, 0, 120, 0, 7)


def draw_playerstatus():
    doku = "どく" if g_player.doku else ""
    noroi = "呪い" if g_player.noroi else ""
    draw_frameC(8, 8, 52, 24)
    draw_textC(8, 8, f"{g_player.name:　<4} Lv{level(g_player.experience): 2}\nＨＰ {g_player.hp: 3} {doku}\nＭＰ {g_player.mp:3} {noroi}")


def draw_playerproperty():  # お買い物、宿屋などの会話のとき
    draw_frame(8, 8, 52, 16)
    draw_text(8, 8, f"{g_player.name:　<4} Lv{level(g_player.experience): 2}\nＧ  {g_player.gold: 9}")


class Slime(Charactor):
    def __init__(self): super().__init__("スライム", 7, 0, 7, 0, 3, 3, 4)
    def draw(self): pyxel.blt(56, 56, 2, 0, 0, 16, 16, 15)


class Castle(Field):
    def __init__(self, x, y):
        super().__init__()
        self.mapid, self.mapleft, self.maptop, self.mapright, self.mapbottom, bgcolor = 1, 9, 0, 32, 17, 3
        self.x, self.y = x, y
        self.encont_monster = lambda x, y: None
        def field(): Field.Blackout(lambda: Field())
        self.traps = ((21, 16, field), (22, 16, field), (23, 16, field), (24, 5, lambda: Field.Blackout(lambda: Palace())), )
        self.npcs = [ShopKeeper(13, 13)]


class Palace(Field):
    def __init__(self):
        super().__init__()
        self.mapid, self.mapleft, self.maptop, self.mapright, self.mapbottom = 1, 0, 0, 10, 6
        self.x, self.y = 8, 4
        self.encont_monster = lambda x, y: None
        self.traps = ((8, 4, lambda: Field.Blackout(lambda: Castle(24, 5))),)
        self.npcs = [NPC(4, 1)]


class PalaceOpening(Palace):
    def __init__(self):
        super().__init__()
        self.x, self.y = 4, 4
        self.direction = 1
        TextBox(fold_text2(f"よくぞわが呼びかけに応えてくれた！ゆうしゃ{g_player.name}よ！」", "王")+"🔻\n"+fold_text2("……せつめいははぶくがぼうけんにでてまおうをたおしてきてくれ！」🔻", "王"))


class Title(State):
    def __init__(self):
        # pyxel.playm(0,True)
        def load(): TextBox(fold_text2("じゅげむじゅげむごこうのすりきれかいじゃりすいぎょのすいぎょうまつうんらいまつふうらいまつくうねるところにすむところやぶらこうじのぶらこうじぱいぽぱいぽぱいぽのしゅーりんがんしゅーりんがんのぐーりんだいぐーりんだいのぽんぽこぴーのぽんぽこなのちょうきゅうめいのちょうすけ🔻"))
        s = SelectBox(40, 76, ("はじめから", "つづきから"), (lambda: PalaceOpening(), load))
        s.sounds = {"OK": 0, "Cancel": 0, "Move": 0}

    def draw(self):
        pyxel.cls(0)
        pyxel.blt(32, 30, 1, 0, 0, 64, 16)


pyxel.init(128, 128, caption="An RPG Sample")
pyxel.load("./assets/pyxel_rpg.pyxres")
Title()  # pyxel.initより後ろに書く
pyxel.run(lambda: g_state.update(), lambda: g_state.draw())
