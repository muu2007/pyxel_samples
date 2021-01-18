import random

import pyxel


class Game:
    def __init__(self, keys, randomstate, OX):
        self.keys, self.randomstate, self.OX = keys, randomstate, OX
        self.offset_x, self.offset_y = 0, 0
        self.update = self.update0  # ゲームオーバー時に一時的に別関数(ジェネレーター・コルーチン)にすげ替える
        self.mx, self.my, self.dx, self.dy, self.scroll_y, self.energy, self.isjumping = 45, pyxel.height-Game.H-Game.MH, 1, 0, 0, 0, True
        self.floors = [(x*Game.W, pyxel.height-Game.H) for x in range(5)]  # 一番下
        self.genfloors()
    W, H = 30, 5  # 土台
    MW, MH = 13, 16  # player_size
    EnergyMax = 42

    def genfloors(self):
        random.setstate(self.randomstate)
        self.floors = [it for it in self.floors if it[1] < self.scroll_y+pyxel.height+16]  # 下に消えたものを消す
        while self.floors[-1][1] > self.scroll_y-99:
            self.floors += [(random.randrange(120-self.W) + (0, pyxel.width*3, 0)[random.randrange(3)], self.floors[-1][1]-Game.H)]  # 上に足す
        self.randomstate = random.getstate()

    def update0(self):
        self.mx += self.dx
        self.dx *= -1 if self.mx <= 5 or self.mx+Game.MW >= pyxel.width//2-5 else 1
        if not self.isjumping:  # running
            if [k for k in self.keys if pyxel.btn(k)]:
                self.energy = (self.energy + 1) % (self.EnergyMax+1)
            if [k for k in self.keys if pyxel.btnr(k)]:
                self.dy, self.isjumping = (-self.energy-0) / 4.4, True
            elif not [it for it in self.floors if it[0]+0 < self.mx+Game.MW and it[0]+Game.W-0 > self.mx and self.my+Game.MH == it[1]]:  # 踏み外す
                self.dy, self.isjumping = 0, True
        else:  # jumping
            self.my += self.dy
            if self.dy < 0:  # 上昇中
                self.scroll_y = min(self.scroll_y, self.my - 40)
                self.genfloors()
            else:  # 落下中
                if s := [it for it in self.floors if it[0]+0 < self.mx+Game.MW and it[0]+Game.W-0 > self.mx and self.my+Game.MH-self.dy <= it[1] and self.my+Game.MH >= it[1]]:  # 着地
                    self.my, self.isjumping, self.energy = s[0][1]-Game.MH, False, 0
                if self.my > self.scroll_y + pyxel.height + Game.MH:  # ゲームオーバー
                    self.update = self._update().__next__
            self.dy += 0.4

    def _update(self):  # ゲームオーバー時のアニメ
        for p in ((-2, -2), (2, 2), (-2, 2), (2, -2), (-1, -1), (1, 1), (-1, 0), (-0, -1),):
            yield self.offset(*p)
        y = self.floors[0][1]+25
        self.floors = [(x*Game.W, y) for x in range(5)] + self.floors  # 一番下
        for self.scroll_y in range(int(self.scroll_y), y-pyxel.height+5, +1):
            yield
        self.update = self.update0
        self.my = y - self.MH
        yield

    def offset(self, x=0, y=0): self.offset_x, self.offset_y = x, y  # 部分的なcamera命令

    def draw(self):
        def rect(x, y, w, h, c): pyxel.rect(x+self.offset_x, y+self.offset_y, w, h, c)
        rect(self.OX, 0, pyxel.width//2, pyxel.height+5, 1)  # @pyxel.bug? heightでは下まで塗られない
        rect(self.OX, 0, 5, pyxel.height+5, 12)
        rect(pyxel.width//2-5+self.OX, 0, 5, pyxel.height+5, 12)
        [rect(x+self.OX, y-self.scroll_y, Game.W, Game.H-1, 12) for x, y in self.floors]
        rect(self.mx+self.OX, self.my-self.scroll_y, Game.MW, Game.MH, 8)  # player
        pyxel.text(70+self.OX, 0, f"{int(-self.scroll_y) // 20+1: 7} F", 7)
        pyxel.rect((pyxel.width//2-self.EnergyMax-2)//2+self.OX, pyxel.height-5, self.EnergyMax+2, 4, 0)
        pyxel.rectb((pyxel.width//2-self.EnergyMax-2)//2+self.OX, pyxel.height-5, self.EnergyMax+2, 4, 7)
        pyxel.rect((pyxel.width//2-self.EnergyMax-2)//2+1+self.OX, pyxel.height-5+1, self.energy, 4-2, 10)


pyxel.init(240, 136, caption="A Platformer Sample2")
# pyxel.load("./assets/pyxel_platform.pyxres")
randomstate = random.getstate()
games = (Game((pyxel.GAMEPAD_1_A, pyxel.KEY_1, pyxel.KEY_KP_1, pyxel.KEY_Z, pyxel.MOUSE_LEFT_BUTTON), randomstate, 0), Game((pyxel.GAMEPAD_2_A, pyxel.KEY_2, pyxel.KEY_KP_2, pyxel.KEY_X, pyxel.MOUSE_RIGHT_BUTTON), randomstate, 120))
pyxel.run(lambda: [g.update()for g in games], lambda: [g.draw() for g in games])
