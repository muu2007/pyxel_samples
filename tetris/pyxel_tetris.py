import atexit
import copy
import gc
import random
import sys
import time

import pyxel  # import curses

A = 6  # size


class Tetrimino:
    _O = (((1, 0), (2, 0), (1, 1), (2, 1)),)
    _I = (((0, 1), (1, 1), (2, 1), (3, 1)), ((2, 0), (2, 1), (2, 2), (2, 3)), ((0, 2), (1, 2), (2, 2), (3, 2)), ((1, 0), (1, 1), (1, 2), (1, 3)))
    _T = (((0, 1), (1, 1), (2, 1), (1, 0)), ((1, 0), (1, 1), (1, 2), (2, 1)), ((0, 1), (1, 1), (2, 1), (1, 2)), ((0, 1), (1, 1), (1, 0), (1, 2)))
    _L = (((0, 1), (1, 1), (2, 1), (2, 0)), ((1, 0), (1, 1), (1, 2), (2, 2)), ((0, 1), (1, 1), (2, 1), (0, 2)), ((1, 0), (1, 1), (1, 2), (0, 0)))
    _J = (((0, 0), (0, 1), (1, 1), (2, 1)), ((1, 0), (1, 1), (1, 2), (2, 0)), ((0, 1), (1, 1), (2, 1), (2, 2)), ((1, 0), (1, 1), (1, 2), (0, 2)))
    _Z = (((0, 0), (1, 0), (1, 1), (2, 1)), ((2, 0), (1, 1), (2, 1), (1, 2)), ((0, 1), (1, 1), (1, 2), (2, 2)), ((1, 0), (1, 1), (0, 1), (0, 2)))
    _S = (((1, 0), (2, 0), (0, 1), (1, 1)), ((1, 0), (1, 1), (2, 1), (2, 2)), ((1, 1), (2, 1), (0, 2), (1, 2)), ((0, 0), (0, 1), (1, 1), (1, 2)))
    # _SRS_O = ((((0, 0),),  # python.spec need comma for 1 item tuple
    #           ((0, 0),)),) 必ず最初で成功するから他ミノのデータで良い
    _SRS_I = ((((0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)),
               ((0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1))),
              (((0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)),
               ((0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2))),
              (((0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)),
               ((0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1))),
              (((0, 0), (-2, 0), (1, 0), (1, 2), (-2, -1)),
               ((0, 0), (1, 0), (-2, 0), (-2, 1), (1, -2))),)
    _SRS_T = ((((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),
               ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2))),
              (((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)),
               ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2))),
              (((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
               ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2))),
              (((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
               ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2))),)
    Blocks = (_O, _I, _T, _L, _J, _Z, _S)
    Colors = (10, 12, 2, 9, 5, 8, 11)
    SRSs = (_SRS_T, _SRS_I, _SRS_T, _SRS_T, _SRS_T, _SRS_T, _SRS_T)

    def __init__(self, shape, color, srs, x, y, rotation):
        self.shape = shape
        self.color = color
        self.srs = srs
        self.x = x
        self.y = y
        self.rotation = rotation
        self._spin_flag = False

    def is_movable(self, dx, dy, field) -> bool:
        return not any(field[y+self.y+dy][x+self.x+dx] for x, y in self.shape[self.rotation])

    def move(self, dx, dy):
        self.x += dx
        self.y += dy
        self._spin_flag = False

    def is_rotatable(self, rotate, field) -> (bool, int, int):
        new_rotation = (self.rotation + rotate) % len(self.shape)
        for ox, oy in self.srs[self.rotation][rotate//2]:  # index 1 or 3 → 0 or 1
            if not any(field[y+self.y+oy][x+self.x+ox] for x, y in self.shape[new_rotation]):
                return True, ox, oy
        return False, 0, 0

    def rotate(self, rotate, ox, oy):
        self.rotation = (self.rotation + rotate) % len(self.shape)
        self.x += ox
        self.y += oy
        self._spin_flag = True

    def is_tspin(self, field) -> int:
        Corners = ((0, 0), (2, 0), (0, 2), (2, 2))
        if self._spin_flag and self.shape is Tetrimino._T and sum(field[self.y+y][self.x+x] > 0 for x, y in Corners) >= 3:
            back_x, back_y = ((1, 2), (0, 1), (1, 0), (2, 1))[self.rotation]  # Baskside
            if field[self.y+back_y][self.x+back_x]:
                return 1  # TSpin mini
            return 2  # TSpin
        return 0  # Not TSpin

    def draw(self, ox, oy, method=pyxel.rect):
        [method((ox + x)*A, (oy + y)*A, A, A, self.color) for x, y in self.shape[self.rotation]]


class SevenBag:
    def __init__(self, fieldwidth):
        self.initial_x = fieldwidth // 2 - 2
        self.blocks = self._generate_7tetriminos()

    def _generate_7tetriminos(self):
        return random.sample([Tetrimino(shape, color, srs, self.initial_x, 0, 0) for shape, color, srs in zip(Tetrimino.Blocks, Tetrimino.Colors, Tetrimino.SRSs)], len(Tetrimino.Blocks))

    def pop(self):
        if len(self.blocks) < 7:
            self.blocks += self._generate_7tetriminos()
            gc.collect()
        return self.blocks.pop(0)

    def draw(self, ox):
        pyxel.text(ox*A, 4*A, 'NEXT:', 13)
        self.blocks[0].draw(ox, 5)
        [self.blocks[i].draw(ox+1, (i-1)*3+8) for i in range(1, 6)]


W = 13  # Wall color = wall value


class Field:
    def __init__(self, width=10, height=20):
        self.width = width + 2
        self.height = height + 2
        self.field = [[W]+[0]*width+[W] if y < (height+1) else [W]*(self.width) for y in range(self.height)]
        self.next_block = SevenBag(self.width)
        self.block = None
        self.lines = 0  # for level
        self.score = 0
        self.combo_count = 0
        self.back2back_count = 0
        self.holdblock = None
        self.hold_flag = False  # 一度holdから出すと、設置するまで取り替えられない
        self._ghostblock = None

    @property
    def level(self): return self.lines // 10 + 1

    def spawn(self):
        self.block = self.next_block.pop()
        self._create_ghost()
        if not self.block.is_movable(0, 0, self.field):
            pyxel.quit()

    def isdroppable(self): return self.block.is_movable(0, 1, self.field)

    def move(self, dx: int, dy: int) -> bool:
        if self.block.is_movable(dx, dy, self.field):
            self.block.move(dx, dy)
            self._create_ghost()
            return True
        return False

    def rotate(self, drotate: int) -> bool:
        f, ox, oy = self.block.is_rotatable(drotate, self.field)
        if f:
            self.block.rotate(drotate, ox, oy)
            self._create_ghost()
            return True
        return False

    def fix(self):
        for x, y in self.block.shape[self.block.rotation]:
            self.field[self.block.y + y][self.block.x + x] = self.block.color
        self.hold_flag = False

    def clear_lines(self):
        n = sum(all(row) for row in self.field[:-1])  # if even n == 0,fall through
        self.field = [[W]+[0]*(self.width-2)+[W] if all(row) else row for row in self.field[:-1]] + [self.field[-1]]  # 消して、
        self.field.sort(key=lambda row: any(row[1:-1]))  # 詰める。以降、得点処理
        self.lines += n
        Normal = (0, 100, 300, 500, 800)
        TSpin = (400, 800, 1200, 1600)
        TSpin_Mini = (100, 200, 400, 1600)  # 3lines = TSpin
        t = self.block.is_tspin(self.field)
        allclear = 10 if all(not any(row[1:-1]) for row in self.field[:-1]) else 1
        self.score += (Normal, TSpin_Mini, TSpin)[t][n] * self.level * (1 + 0.5 * self.back2back_count) * allclear
        self.score += 50 * self.combo_count * self.level * allclear
        self.combo_count += (-self.combo_count, 1, 1, 1, 1)[n]
        self.back2back_count += ([0]+[1 if t else -self.back2back_count]*3+[1])[n]  # 0段消しは続く

    def swap_hold(self):
        if self.hold_flag:
            return
        if not self.holdblock:
            self.holdblock = self.next_block.pop()
        self.block, self.holdblock = self.holdblock, self.block
        self.holdblock.rotation = 0
        self.block.x = self.width // 2 - 2  # self.holdblock.x
        self.block.y = 0  # self.holdblock.y
        self.hold_flag = True
        self._create_ghost()

    def rise(self):
        row = [W] * self.width
        xs = [i for i, c in enumerate(self.field[-2][1:-1], 1) if c]
        if not xs:
            xs = range(1, self.width-1)
        row[random.choice(xs)] = 0
        self.field = self.field[1:-1] + [row] + [self.field[-1]]
        self._create_ghost()

    def _create_ghost(self):
        if '--noghost' in sys.argv:
            return None
        self._ghostblock = copy.copy(self.block)
        self._ghostblock.color = W  # Tetrimino.Colors[(Tetrimino.Colors.index(self.block.color) + 1) % len(Tetrimino.Colors)]
        while self._ghostblock.is_movable(0, 1, self.field):
            self._ghostblock.move(0, 1)

    def draw(self):
        pyxel.cls(0)
        OX1, OX2 = 6, 19
        for y, row in enumerate(self.field):
            for x, c in enumerate(row):
                pyxel.rect((x+OX1)*A, y*A, A, A, c)
        pyxel.rect(OX1*A, 0, A*self.width, A, 0)
        if self._ghostblock:
            self._ghostblock.draw(self._ghostblock.x + OX1, self._ghostblock.y, pyxel.rectb)
        self.block.draw(self.block.x + OX1, self.block.y)
        pyxel.text(OX2*A, 1*A, 'Score: %3d' % self.score, W)
        pyxel.text(OX2*A, 2*A, 'Level: %3d' % self.level, W)
        self.next_block.draw(OX2)
        pyxel.text(0*A, 1*A, 'HOLD:', W)
        if self.holdblock:
            self.holdblock.draw(1, 2)
        pyxel.text(0*A, 5*A, f'CMB: {self.combo_count}', W)
        pyxel.text(0*A, 6*A, f'B2B: {self.back2back_count}', W)


def interval(level: int):
    # level:      --  01  02  03  04  05  06  07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29
    drop_rates = (60, 48, 43, 38, 33, 28, 23, 18, 13, 8, 6, 5, 5, 5, 4, 4, 4, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1)
    return drop_rates[level] if level < len(drop_rates) else 1


def update():
    global limit_time  # static変数にできそう
    Infinity_Play = 8
    if pyxel.btnp(pyxel.KEY_LEFT, 0, Infinity_Play) and game.move(-1, 0) and not game.isdroppable():
        limit_time = max(limit_time, pyxel.frame_count+Infinity_Play)
    elif pyxel.btnp(pyxel.KEY_RIGHT, 0, Infinity_Play) and game.move(1, 0) and not game.isdroppable():
        limit_time = max(limit_time, pyxel.frame_count+Infinity_Play)
    elif pyxel.btnp(pyxel.KEY_Z) and game.rotate(1) and not game.isdroppable():
        limit_time = max(limit_time, pyxel.frame_count+Infinity_Play)
    elif pyxel.btnp(pyxel.KEY_X) and game.rotate(3) and not game.isdroppable():
        limit_time = max(limit_time, pyxel.frame_count+Infinity_Play)
    elif pyxel.btnp(pyxel.KEY_DOWN, 0, 5):
        if game.move(0, 1):
            limit_time = pyxel.frame_count+interval(game.level)
            game.score += 1
        # else:
        #     limit_time = pyxel.frame_count  # ~~This means fix~~ @guideline 下ボタンでは固定しない
    elif pyxel.btnp(pyxel.KEY_UP):  # harddrop
        limit_time = pyxel.frame_count   # 最初の停止状態でのみバグ。設置後動かせる
        while game.move(0, 1):
            game.score += 2
    elif pyxel.btnp(pyxel.KEY_H):
        game.swap_hold()
    elif pyxel.btnp(pyxel.KEY_SEMICOLON):
        game.lines = (((game.lines + 10) // 10) * 10)  # level up
        game.rise()

    if limit_time <= pyxel.frame_count:  # drop or fix
        if game.move(0, 1):
            limit_time += interval(game.level)
        else:
            game.fix()
            game.clear_lines()
            game.spawn()


random.seed(time.time() if len(sys.argv) < 3 else int(sys.argv[2]))  # gameを作る前に
game = Field()
game.lines = max(0, ((1 if len(sys.argv) < 2 else int(sys.argv[1])) - 1) * 10)  # level
game.spawn()
limit_time = interval(game.level)
atexit.register(lambda: print('Score: %d\nLevel: %d' % (game.score, game.level,)))
pyxel.init(A*28, A*23, caption="Tetris(Guideline ver.)", fps=60)
pyxel.run(update, game.draw)

# [*] SevenBag
# [*] 最初止まってる
# [*] level
# [ ] ~~Pause~~
# [*] Score 1:100 2:300 3 500 4 800 x level
# [*] Score drop:1 harddrop: 2
# [*] Score Ren(Combo): 50 x series x level
# [*] Score T-spin: ? Allclear: ?
# [*] GhostBlock(落下位置表示)
# [*] infinity: 操作している間はFixしない。
# [*] Hold
# [*] SuperRotation
# 出現時に回転
# [*] T-Spin判定
# [*] Back-to-back
