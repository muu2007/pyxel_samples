import sys

import numpy  # type: ignore
import pyxel  # import curses

_SPACE, _WALL, _SLOT, _BOX, _FILLED = b' ', b'#', b'.', b'o', b'*',


def arrowkeysp(values):
    for k, v in zip((pyxel.KEY_LEFT, pyxel.KEY_UP, pyxel.KEY_RIGHT, pyxel.KEY_DOWN), values):
        if pyxel.btnp(k, 8, 7):  # at fps30
            return v
    for k, v in zip((pyxel.GAMEPAD_1_LEFT, pyxel.GAMEPAD_1_UP, pyxel.GAMEPAD_1_RIGHT, pyxel.GAMEPAD_1_DOWN), values):
        if pyxel.btnp(k, 8, 7):
            return v


class Game:
    def __init__(self, level: int):
        self._field = numpy.genfromtxt(r'./assets/sokoban_' + str(level), delimiter=[1]*64, dtype='S1', comments=';')
        self._pos0 = [i[0] for i in numpy.where(self._field == b'@')]
        self._field[self._pos0[0], self._pos0[1]] = _SPACE  # [*_pos0]では表記できなかった y,x
        self._undos = []

    def move_player(self, dy: int, dx: int):
        y1, x1, utmp = self._pos0[0] + dy, self._pos0[1] + dx, (numpy.copy(self._pos0), numpy.copy(self._field))  # deepcopy

        def box():
            y2, x2 = y1 + dy, x1 + dx
            self._field[y2, x2], f = {_SPACE: (_BOX, move), _SLOT: (_FILLED, move), _BOX: (_BOX, nomove), _FILLED: (_FILLED, nomove), _WALL: (_WALL, nomove)}[self._field[y2, x2]]
            f()

        def move():
            self._pos0 = (y1, x1)
            self._field[y1, x1] = {_SPACE: _SPACE, _SLOT: _SLOT, _BOX: _SPACE, _FILLED: _SLOT}[self._field[y1, x1]]
            self._undos.append(utmp)

        def nomove(): pass
        {_BOX: box, _FILLED: box, _SLOT: move, _SPACE: move, _WALL: nomove}[self._field[y1, x1]]()

    def undo(self):
        if self._undos:
            self._pos0, self._field = self._undos.pop()

    def is_win(self): return not any(_BOX in row for row in self._field)


class App:
    def __init__(self, level):
        self.level = level
        self.game = Game(level)
        pyxel.run(self.update, self.draw)

    def update(self):
        if d := arrowkeysp(((0, -1), (-1, 0), (0, 1), (1, 0))):
            self.game.move_player(*d)
        if pyxel.btnp(pyxel.KEY_U):
            self.game.undo()
        if self.game.is_win():
            self.level += 1
            self.game = Game(self.level)  # App(self.level+1)  # pyxel.quit() pyxel.runを２回呼ぶと終了できなくなる

    def draw(self):
        pyxel.cls(0)
        Colors = {_WALL: 1, _SPACE: 0, _BOX: 3, _SLOT: 2, _FILLED: 4, b'\n': 0, b'': 0}
        [[pyxel.blt(x*8, y*8, 0, 8*Colors[c], 8*14, 8, 8, 0) for x, c in enumerate(row)] for y, row in enumerate(self.game._field)]
        py, px = self.game._pos0
        pyxel.blt(px*8, py*8, 0, 40, 8*14, 8, 8, 0)
        pyxel.text(0, len(self.game._field)*8+8, f'level: {self.level}  step:{len(self.game._undos)}\nArrowkeys: Move u: Undo', 7)


pyxel.init(256, 256, caption="倉庫番")
pyxel.load("my_resource.pyxres")
App(0 if len(sys.argv) < 2 else int(sys.argv[1]))
# def _main(screen, level: int = 0 if len(sys.argv) < 2 else int(sys.argv[1])):
#     print('\033]2;倉庫番\007')  # Title
#     curses.curs_set(False)
#     [curses.init_pair(i, f, b) for i, f, b in ((1, curses.COLOR_RED, 0), (2, curses.COLOR_CYAN, 0), (3, curses.COLOR_YELLOW, 0), (4, curses.COLOR_YELLOW, curses.COLOR_BLUE))]
#     game = Game(level)
#     Keys = {
#         curses.KEY_UP: lambda: game.move_player(-1, 0),
#         curses.KEY_DOWN: lambda: game.move_player(1, 0),
#         curses.KEY_LEFT: lambda: game.move_player(0, -1),
#         curses.KEY_RIGHT: lambda: game.move_player(0, 1),
#         ord('u'): game.undo,
#         27: sys.exit,  # Esc
#     }  # wasd               vim
#     Keys[ord('w')] = Keys[ord('k')] = Keys[curses.KEY_UP]
#     Keys[ord('s')] = Keys[ord('j')] = Keys[curses.KEY_DOWN]
#     Keys[ord('a')] = Keys[ord('h')] = Keys[curses.KEY_LEFT]
#     Keys[ord('d')] = Keys[ord('l')] = Keys[curses.KEY_RIGHT]
#
#     def draw():
#         screen.erase()
#         Colors = {_WALL: 4, _SPACE: 0, _BOX: 2, _SLOT: 2, _FILLED: 3, b'\n': 0, b'': 0}
#         [[screen.addstr(y, x, c, curses.color_pair(Colors[c])) for x, c in enumerate(row)]for y, row in enumerate(game._field)]
#         screen.addstr(*game._pos0, '@', curses.color_pair(1))
#         screen.addstr(len(game._field), 0, f'\nLevel:{level} _step:{len(game._undos)}', curses.A_REVERSE)
#         screen.addstr(f'\n←↓↑→/wasd/hjkl: Move\nu: Undo Esc: Exit')  # screen.refresh()
#
#     while not draw():
#         Keys.get(screen.getch(), lambda: None)()
#         if game.is_win():
#             return _main(screen, level + 1)
#
#
# if __name__ == '__main__':
#     curses.wrapper(_main)
