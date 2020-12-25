# import gc
import itertools
import math
import sys

import pyxel


def arrow8(a=1, b=1):
    if (pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.GAMEPAD_1_LEFT)) and (pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.GAMEPAD_1_UP)):
        return (-b, -b)
    elif (pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.GAMEPAD_1_LEFT)) and (pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.GAMEPAD_1_DOWN)):
        return (-b, +b)
    elif (pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.GAMEPAD_1_RIGHT)) and (pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.GAMEPAD_1_UP)):
        return (+b, -b)
    elif (pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.GAMEPAD_1_RIGHT)) and (pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.GAMEPAD_1_DOWN)):
        return (+b, +b)
    elif pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.GAMEPAD_1_LEFT):
        return (-a, 0)
    elif pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.GAMEPAD_1_UP):
        return (0, -a)
    elif pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.GAMEPAD_1_RIGHT):
        return (a, 0)
    elif pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.GAMEPAD_1_DOWN):
        return (0, a)
    return (0, 0)


def btnpA(hold=0, period=0): return pyxel.btnp(pyxel.KEY_Z, hold, period) or pyxel.btnp(pyxel.GAMEPAD_1_A, hold, period)
def btnpB(hold=0, period=0): return pyxel.btnp(pyxel.KEY_X, hold, period) or pyxel.btnp(pyxel.GAMEPAD_1_B, hold, period)


g_score = 0
g_hiscore = 50000
g_life = 3
g_stage = 1

SCROLLSPEED = 0.5


def draw_score():
    global g_hiscore
    if g_score > g_hiscore:
        g_hiscore = g_score
    # pyxel.text(41, 0, f"1P:            SCORE: {g_score: 8} HI: {g_hiscore: 8} ", 5)
    pyxel.text(40, 0, f"1P:            SCORE: {g_score: 8} HI: {g_hiscore: 8} ", 1)
    [pyxel.blt(60+i*6, 0, 0, 16, 8, 5, 5, 0) for i in range(g_life)]


class State:
    def __new__(cls, *args):  # **kargs
        global g_scene
        self = object.__new__(cls)
        g_scene = self
        return self

    def update(self): pass
    # def draw(self): pass


class TitleState(State):
    def __init__(self):
        self.draw = self._draw().__next__  # coroutine.wrap

    def _draw(self):
        def part(y):
            pyxel.cls(0)
            draw_score()
            pyxel.blt(40, y, 2, 0, 0, 160, 68, 0)

        for y in range(256, 32, -6):
            part(y)
            yield
            if btnpA():  # skip animation
                break
        blink = itertools.cycle([True]*18+[False]*18).__next__
        for c in range(250):
            part(32)
            if blink():
                pyxel.text(85, 100, "Push A Button", 7)
            yield
            if btnpA():
                pyxel.play(3, 1)
                GameState()
        yield DemoState()


class ReadyState(State):
    def __init__(self, caller):
        self.caller = caller
        self.draw = self._draw().__next__  # coroutine.wrap
        # gc.enable()
        # gc.collect()

    def _draw(self):
        global g_scene
        for _ in range(45):
            pyxel.cls(0)
            draw_score()
            pyxel.text(110, 65, f"Stage {g_stage}", 7)
            # [pyxel.blt(130+i*8, 65, 0, 24, 0, 8, 8, 0) for i in range(g_life)]
            yield
        g_scene = self.caller
        # gc.disable()
        yield


class PauseState(State):
    def __init__(self, caller):
        self.caller = caller
        self.draw = self._draw().__next__  # coroutine.wrap
        # gc.enable()
        # gc.collect()

    def _draw(self):
        global g_scene
        blink = itertools.cycle([True]*18+[False]*18).__next__
        while True:
            self.caller.draw()
            if blink():
                pyxel.text(60, 100, "Pause", 7)
            if pyxel.btnp(pyxel.KEY_A):
                break
            yield
        g_scene = self.caller
        # gc.disable()
        yield


g_missiles = []  # python.spec global書かなくてもremoveはできちゃう
g_enemies = []  # and barrets powerup items particles


class Missile:
    def __new__(cls, *args):  # **kargs
        global g_missiles
        self = object.__new__(cls)
        g_missiles += [self]
        return self

    def __init__(self, x, y):
        self.x, self. y = x, y

    # def update(self): pass  # 画面外に出たとき、lifetimeがなくなったとき、配列からremoveする
    # def draw(self): pass
    # def collide(self): pass


class Enemy:
    def __new__(cls, *args):  # **kargs
        global g_enemies
        self = object.__new__(cls)
        g_enemies += [self]  # 作られたら登録する決まりとする
        return self

    def __init__(self, x, y, lifetime=sys.maxsize):
        self.x, self.y, self.lifetime = x, y, lifetime  # lifetimeはその時が来たら消えるパーティクルなどに使う

    # def update(self): pass  # 画面外に出たとき、lifetimeがなくなったとき、配列からremoveする
    def draw(self): pass
    def hit(self, missile): pass


class Bullet (Missile):  # player's bullet
    def __init__(self, x, y):
        super().__init__(x, y)
    w, h = 1, 1

    def update(self):
        self.x += 3.0
        if self.x > pyxel.width:
            g_missiles.remove(self)

    def draw(self): pyxel.pset(self.x, self.y, 7)

    # 主体を自機とミサイルとし、各敵機との当たり判定をする。→当たっていたら、自機ミサイルを削除する(Laserなら削除しない？)
    def collide(self):
        if [True for it in g_enemies if it.hit(self)]:
            g_missiles.remove(self)


class Apple(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)  # , 30*5)
    w, h = 8, 8

    def update(self):
        self.x -= SCROLLSPEED
        if self.x <= -self.w:
            g_enemies.remove(self)
        # self.lifetime -= 1
        # if self.lifetime <= 0:
        #     g_enemies.remove(self)

    def draw(self): pyxel.blt(self.x, self.y, 0, 16, 0, self.w, self.h, 0)

    def hit(self, missile):
        global g_apples
        if type(missile) is Player and self.x-missile.x > -self.w and self.x-missile.x < missile.w and self.y-missile.y > -self.h and self.y-missile.y < missile.h:  # 結局左から-敵幅、自幅、-敵高、自高
            g_enemies.remove(self)
            Score(self.x, self.y, 100)
            missile.apples += 1  # 自機を操作できる
            # return True


class GhostA(Enemy):
    def update(self):
        self.x -= 1
        if self.x < -8:
            g_enemies.remove(self)
    w, h = 8, 8

    def draw(self): pyxel.blt(self.x, self.y, 0, 32, 0, self.w, self.h, 0)

    def hit(self, missile):
        if self.x-missile.x > -self.w and self.x-missile.x < missile.w and self.y-missile.y > -self.h and self.y-missile.y < missile.h:  # 結局左から-敵幅、自幅、-敵高、自高
            # g_enemies.remove(self)
            self.update = lambda: None  # 途中で自分の動作を書き換えても大丈夫。コルーチンでも大丈夫。lambdaでも大丈夫
            self.draw = self._draw2().__next__
            self.hit = lambda missile: False
            Score(self.x, self.y, 200)
            return True

    def _draw2(self):
        for _ in range(10):
            pyxel.blt(self.x, self.y, 0, 56, 0, self.w, self.h, 0)
            yield
        g_enemies.remove(self)
        yield


# class Rock(Enemy):
#     def update(self): self.x -= 1
#     def draw(self): pyxel.blt(self.x, self.y, 0, 40, 0, 8, 8, 0)
#
#
# class EnemyBullet(Enemy):
#     def update(self): self.x -= 1
#     def draw(self): pyxel.blt(self.x, self.y, 0, 0, 8, 8, 8, 0)
#
#
# class EnemyBubble(Enemy):
#     def update(self): self.x -= 1
#     def draw(self): pyxel.blt(self.x, self.y, 0, 8, 8, 8, 8, 0)
#


class Score(Enemy):  # particle
    def __init__(self, x, y, value):
        global g_score
        super().__init__(x, y, 18)
        g_score += value
        self.value = str(value)

    def update(self):
        self.lifetime -= 1
        if self.lifetime <= 0:
            g_enemies.remove(self)
        self.y -= 1

    def draw(self): pyxel.text(self.x, self.y, self.value, 7)


class GhostMother(Enemy):
    """母艦は描画も当たり判定もない"""
    class GhostChild:
        def __init__(self, mother, x, y):
            self.mother = mother
            mother.children += [self]
            self.update = self._update().__next__
            self.x, self.y = x, y
            self.direction = 1
        w, h = 8, 8

        def _update(self):
            for i in range(70):
                self.x -= 2
                yield
            d = +1 if self.y < pyxel.height // 2 else -1
            self.direction = -1  # 描画反転
            for i in range(40):
                self.x += 2 / math.sqrt(2)
                self.y += 2 / math.sqrt(2) * d
                yield
            for i in range(50):
                self.x += 2
                yield
            self.mother.children.remove(self)
            yield

        def hit(self, missile):
            if self.x-missile.x > -self.w and self.x-missile.x < missile.w and self.y-missile.y > -self.h and self.y-missile.y < missile.h:  # 結局左から-敵幅、自幅、-敵高、自高
                self.mother.children.remove(self)
                Score(self.x, self.y, 200)
                if 0 == len(self.mother.children):
                    Apple(self.x, self.y)
                return True

        def draw(self): pyxel.blt(self.x, self.y, 0, (self.chip % 16)*8, (self.chip // 16)*8, self.w*self.direction, self.h, 0)
        chip = 4

    def __init__(self, y):
        self.y = y
        self.children = []
        self.update = self._update().__next__

    def _update(self):
        for i in range(6):
            self.GhostChild(self, 256, self.y)
            for j in range(15):
                [it.update() for it in self.children]
                yield
        while True:
            [it.update() for it in self.children]
            if 0 == len(self.children):
                g_enemies.remove(self)
            yield

    def draw(self):
        [it.draw() for it in self.children]

    def hit(self, missile):
        return [True for it in self.children if it.hit(missile)]


class ButterflyMother(Enemy):
    """母艦は描画も当たり判定もない"""
    class ButterflyChild:
        def __init__(self, mother, y):
            self.mother = mother
            mother.children += [self]
            self.update = self._update().__next__
            self.x, self.y, self.oy = 256, y, y
        w, h = 8, 8

        def _update(self):
            for i, x in enumerate(range(pyxel.width, -self.w, -2)):
                self.x = x
                self.y = self.oy - math.sin(i / 10.0) * 20  # sinの引数はラジアン
                yield
            self.mother.children.remove(self)
            yield

        def hit(self, missile):
            if self.x-missile.x > -self.w and self.x-missile.x < missile.w and self.y-missile.y > -self.h and self.y-missile.y < missile.h:  # 結局左から-敵幅、自幅、-敵高、自高
                self.mother.children.remove(self)
                Score(self.x, self.y, 200)
                if 0 == len(self.mother.children):
                    Apple(self.x, self.y)
                return True

        def draw(self): pyxel.blt(self.x, self.y, 0, (self.chip % 16)*8, (self.chip // 16)*8, self.w, self.h, 0)
        chip = 3

    def __init__(self, y):
        self.y = y
        self.children = []
        self.update = self._update().__next__

    def _update(self):
        for i in range(4):  # 出現
            self.ButterflyChild(self, self.y)
            self.ButterflyChild(self, pyxel.height - self.y)
            for j in range(30):  # 待ち
                [it.update() for it in self.children]
                yield
        while True:  # 出現終わったら、全機いなくなるまで待つ
            [it.update() for it in self.children]
            if 0 == len(self.children):
                g_enemies.remove(self)
            yield

    def draw(self):
        [it.draw() for it in self.children]

    def hit(self, missile):
        return [True for it in self.children if it.hit(missile)]


class BG(Enemy):
    def update(self):
        self.x -= SCROLLSPEED

    def draw(self):
        pyxel.bltm(self.x, self.y, 0, 0, 0, 30, 17, 0)


class Player(Missile):
    def __init__(self):
        self.x, self.y = 40, 70
        self.apples = 0
        self.speed = 0
    w, h = 16, 8
    Speeds = [1, 1.4, 2, 2.5]

    def update(self):
        dx, dy = arrow8(self.Speeds[self.speed], self.Speeds[self.speed] / math.sqrt(2))
        self.x = min(max(self.x + dx, 0), pyxel.width - self.w)
        self.y = min(max(self.y + dy, 0), pyxel.height - self.h)
        if btnpA():
            Bullet(self.x+14, self.y+4)  # 弾発生
        if btnpB():
            n = (self.apples-1) % 6
            if 0 == n:
                self.speedup()

    def draw(self):
        pyxel.blt(self.x, self.y, 0, 0, 0, 16, 8, 0)

    def _draw2(self):  # 途中で爆発アニメにすげ替える。
        global g_life
        for _ in range(50):
            pyxel.blt(self.x, self.y, 0, 56, 0, 8, 8, 0)
            yield
        g_life -= 1
        GameState()
        yield

    def draw_powerupslots(self):
        [pyxel.rectb(x*40, pyxel.height-7, 38, 7, 7) for x in range(6)]
        if self.apples > 0:
            pyxel.rectb((self.apples-1) % 6*40, pyxel.height-7, 38, 7, 10)

    def collide(self):
        if [True for it in g_enemies if it.hit(self)]:
            self.update = lambda: None
            self.draw = self._draw2().__next__
            self.collide = lambda: None

    def speedup(self):
        if self.speed >= len(self.Speeds):
            return
        self.apples = 0
        self.speed = min(self.speed+1, len(self.Speeds)-1)
        # print(self.speed, self.Speeds[self.speed])


stagedata = (
    (5, "Apple(90,65)"),
    # (10, "GhostA(256,120)"),
    # (20, "GhostA(256,100)"),
    # (40, "GhostA(256,40)"),
    # (60, "GhostA(256,65)"),
    # (80, "GhostA(256,20)"),
    # (120, "GhostA(256,60)"),
    # (150, "GhostA(256,80)"),
    (130, "BG(256,0)"),
    (30, "GhostMother(20)"),
    (120, "GhostMother(110)"),
    (210, "GhostMother(20)"),
    (300, "GhostMother(110)"),
    (400, "ButterflyMother(30)"),


)


class GameState(State):
    def __init__(self, time_offset=0):
        global g_missiles, g_enemies
        g_missiles, g_enemies = [Player(), ], []
        self.frame_count = time_offset
        ReadyState(self)  # 初期化したけど、一時的に別の状態にする

    def update(self):
        self.frame_count += 1
        [eval(it[1]) for it in stagedata if it[0] == self.frame_count]  # ステージデータの従って敵発生
        [it.update() for it in g_missiles + g_enemies]  # まず全部を動かす
        [it.collide() for it in g_missiles]
        if pyxel.btnp(pyxel.KEY_A):
            PauseState(self)  # 一時停止も、一時的な別の状態

    def draw(self):
        pyxel.cls(0)
        [it.draw() for it in g_missiles+g_enemies]
        draw_score()
        g_missiles[0].draw_powerupslots()

    def player_collide(self):
        global g_life
        if [True for it in g_enemies if it.hit(self)]:
            g_life -= 1
            GameState()


class DemoState(State):
    def __init__(self):
        self.draw = self._draw().__next__  # coroutine.wrap
        self.frame_count = 0

    def _draw(self):
        blink = itertools.cycle([True]*18+[False]*18).__next__
        for _ in range(30*6):
            pyxel.cls(0)
            draw_score()
            self.frame_count += 1
            pyxel.text(self.frame_count, self.frame_count, f"{self.frame_count}", 7)
            if blink():
                pyxel.text(60, 120, "Demo Scene", 7)
            yield
            if btnpA():
                break
        yield TitleState()


pyxel.init(240, 135, caption="Shooting Game")
pyxel.load("./assets/pyxel_shooting.pyxres")
# g_scene = TitleState()  # pyxel.initより後ろに書く
g_scene = GameState(100)  # pyxel.initより後ろに書く
pyxel.run(lambda: g_scene.update(), lambda: g_scene.draw())
