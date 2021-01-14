import random

import pyxel


def btnA(): return [True for k in (pyxel.GAMEPAD_1_A, pyxel.KEY_1, pyxel.KEY_KP_1, pyxel.KEY_Z) if pyxel.btn(k)]
def btnrA(): return [True for k in (pyxel.GAMEPAD_1_A, pyxel.KEY_1, pyxel.KEY_KP_1, pyxel.KEY_Z) if pyxel.btnr(k)]


class Game:
    def __init__(self): self.reset()

    def reset(self):
        self.mx, self.my, self.dx, self.dy, self.sy, self.energy, self.isjumping = 45, 99, 1, 0, 0, 0, True
        self.floors = [(x*5*6, pyxel.height-5) for x in range(5)]  # 一番下
        self.genfloors()

    def genfloors(self):
        self.floors = [it for it in self.floors if it[1] < self.sy+pyxel.height+16]
        while self.floors[-1][1] > self.sy-99:
            self.floors += [(random.randrange(23)*5 + (0, 0, pyxel.width)[random.randrange(3)], self.floors[-1][1]-5)]

    def update(self):
        self.mx += self.dx
        self.dx *= -1 if self.mx <= 0 or self.mx+13 >= pyxel.width else 1
        if not self.isjumping:  # running
            if btnA():
                self.energy = (self.energy + 1) % 40
            if btnrA():
                self.dy, self.isjumping = (-self.energy-2) / 4, True
            elif not [it for it in self.floors if it[0]+0 < self.mx+13 and it[0]+5*6-0 > self.mx and self.my+16 == it[1]]:  # 踏み外す
                self.dy, self.isjumping = 0, True
        else:  # jumping
            self.my += self.dy
            if self.dy < 0:  # 上昇中
                self.sy = min(self.sy, self.my - 40)
                self.genfloors()
            else:  # 落下中
                if s := [it for it in self.floors if it[0]+0 < self.mx+13 and it[0]+5*6-0 > self.mx and self.my+16-self.dy <= it[1] and self.my+16 >= it[1]]:  # 着地
                    self.my, self.isjumping, self.energy = s[0][1]-16, False, 0
                if self.my > self.sy + pyxel.height + 16:  # ゲームオーバー
                    self.reset()
            self.dy += 0.4

    def draw(self):
        pyxel.cls(1)
        [pyxel.rect(x, y-self.sy, 5*6, 4, 12) for x, y in self.floors]
        pyxel.rect(self.mx, self.my-self.sy, 13, 16, 8)  # player
        pyxel.text(90, 0, f"{int(-self.sy) // 10: 7} F", 7)
        pyxel.rect((pyxel.width-44)//2, 115, 44, 4, 0)
        pyxel.rectb((pyxel.width-44)//2, 115, 44, 4, 7)
        pyxel.rect((pyxel.width-44)//2+1, 115+1, self.energy, 4-2, 10)


pyxel.init(136, 120, caption="A Platformer Sample")
# pyxel.load("./assets/pyxel_platform.pyxres")
game = Game()
pyxel.run(game.update, game.draw)
