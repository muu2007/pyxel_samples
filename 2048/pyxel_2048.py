from random import *

import pyxel  # type: ignore # from curses import *

Size = 4


class Game:
    def __init__(self):
        self._field = [[0]*Size for j in range(Size)]
        self._spawn(1024) or self._spawn(2)

    # def draw(self, screen): screen.erase() or [screen.addstr("".join("|{: ^5} ".format(n) if n > 0 else "|      " for n in row) + "|\n") for row in self._field]
    def _compare_field(self, ss): return any(s1 != s2 for s1, s2 in zip(ss, self._field))

    def _spawn(self, value=None):  # デフォルト引数では一度しか評価されないようだ。
        i, j = choice([(i, j) for i in range(Size) for j in range(Size) if self._field[i][j] == 0])
        self._field[i][j] = value if value else 2 if randrange(100) < 90 else 4
        exit() if not any(self._compare_field(self._move(i)) for i in range(4)) else None  # gameover

    def _move(self, direction):
        def left(field):
            def merge(row): return row if len(row) < 2 else [row[0]+row[1]]+merge(row[2:])+[0] if row[0] == row[1] else row[0:1]+merge(row[1:])  # 再帰
            return [merge(sorted(row, key=lambda n: n == 0)) for row in field]

        transpose, invert = lambda f: [list(row) for row in zip(*f)], lambda f: [row[::-1] for row in f]
        return [left, lambda f: transpose(left(transpose(f))), lambda f: invert(left(invert(f))), lambda f: transpose(invert(left(invert(transpose(f)))))][direction](self._field)

    def move(self, direction):
        old, self._field = self._field, self._move(direction)  # 動かなくても代入
        self._spawn() if self._compare_field(old) else None  # 動いたら一つ発生させる


# def _main(screen):
#     game = Game()
#     Keys = {KEY_LEFT: lambda: game.move(0), KEY_UP: lambda: game.move(1), gameKEY_RIGHT: lambda: game.move(2), KEY_DOWN: lambda: game.move(3)}
#     while not game.draw(screen) and not Keys.get(screen.getch(), lambda: None)(): pass


# wrapper(_main)
def arrowkeysp(values=(1, 2, 3, 4)):
    for k, v in zip((pyxel.KEY_LEFT, pyxel.KEY_UP, pyxel.KEY_RIGHT, pyxel.KEY_DOWN), values):
        if pyxel.btnp(k):
            return v
    for k, v in zip((pyxel.GAMEPAD_1_LEFT, pyxel.GAMEPAD_1_UP, pyxel.GAMEPAD_1_RIGHT, pyxel.GAMEPAD_1_DOWN), values):
        if pyxel.btnp(k):
            return v


def update():
    if d := arrowkeysp():  # 0がFalseと判定されるため1..4にして、Game.moveでは0..3に合わせる
        game.move(d-1)


def draw():
    def cell(x, y, v):
        pyxel.rect(x*20, y*20, 20, 20, {0: 0, 2: 1, 4: 2, 8: 3, 16: 4, 32: 5, 64: 6, 128: 8, 256: 9, 512: 10, 1024: 11, }.get(v, 7))
        pyxel.text(x*20+3, y*20+8, "{:^5}".format(v), 0)
    [[cell(i, j, v) for i, v in enumerate(row)] for j, row in enumerate(game._field)]


game = Game()
pyxel.init(20*Size, 20*Size, caption="2048", fps=10)
pyxel.run(update, draw)
