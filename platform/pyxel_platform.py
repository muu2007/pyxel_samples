import random

import pyxel


def btnA(): return [True for k in (pyxel.GAMEPAD_1_A, pyxel.KEY_1, pyxel.KEY_KP_1, pyxel.KEY_Z, pyxel.MOUSE_LEFT_BUTTON) if pyxel.btn(k)]
def btnrA(): return [True for k in (pyxel.GAMEPAD_1_A, pyxel.KEY_1, pyxel.KEY_KP_1, pyxel.KEY_Z, pyxel.MOUSE_LEFT_BUTTON) if pyxel.btnr(k)]
def rect(x, y, w, h, c): pyxel.rect(x-g_offset_x, y-g_offset_x, w, h, c)  # camera(offset)に対応するのはこれだけ
def camera(x=0, y=0): global g_offset_x, g_offset_y; g_offset_x, g_offset_y = x, y


g_offset_x, g_offset_y = 0, 0


class Game:
    def __init__(self): self.reset()
    W, H = 30, 5  # 土台
    MW, MH = 13, 16  # player_size
    EnergyMax = 42

    def reset(self):
        self.update = self.update0  # ゲームオーバー時に一時的に別関数(ジェネレーター・コルーチン)にすげ替える
        self.mx, self.my, self.dx, self.dy, self.scroll_y, self.energy, self.isjumping = 45, pyxel.height-Game.H-Game.MH, 1, 0, 0, 0, True
        self.floors = [(x*Game.W, pyxel.height-Game.H) for x in range(5)]  # 一番下
        self.genfloors()

    def genfloors(self):
        self.floors = [it for it in self.floors if it[1] < self.scroll_y+pyxel.height+16]  # 下に消えたものを消す
        while self.floors[-1][1] > self.scroll_y-99:
            self.floors += [(random.randrange(11)*10+3 + (0,  pyxel.width*2, 0)[random.randrange(3)], self.floors[-1][1]-Game.H)]  # 上に足す

    def update0(self):
        self.mx += self.dx
        self.dx *= -1 if self.mx <= 0 or self.mx+Game.MH >= pyxel.width else 1
        if not self.isjumping:  # running
            if btnA():
                self.energy = (self.energy + 1) % (self.EnergyMax+1)
            if btnrA():
                self.dy, self.isjumping = (-self.energy-0) / 4, True
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
            yield camera(*p)
        self.reset()
        yield

    def draw(self):
        pyxel.cls(1)
        [rect(x, y-self.scroll_y, Game.W, Game.H-1, 12) for x, y in self.floors]
        rect(self.mx, self.my-self.scroll_y, Game.MW, Game.MH, 8)  # player
        camera()
        pyxel.text(90, 0, f"{int(-self.scroll_y) // 20+1: 7} F", 7)
        pyxel.rect((pyxel.width-self.EnergyMax-2)//2, 115, self.EnergyMax+2, 4, 0)
        pyxel.rectb((pyxel.width-self.EnergyMax-2)//2, 115, self.EnergyMax+2, 4, 7)
        pyxel.rect((pyxel.width-self.EnergyMax-2)//2+1, 115+1, self.energy, 4-2, 10)


pyxel.init(136, 120, caption="A Platformer Sample")
# pyxel.load("./assets/pyxel_platform.pyxres")
game = Game()
pyxel.run(lambda: game.update(), game.draw)
