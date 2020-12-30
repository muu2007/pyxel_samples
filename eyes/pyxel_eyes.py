import pyxel


def draw():
    def part(ox, oy, r, r2):
        pyxel.circ(ox, oy, r, 7)
        pyxel.circb(ox, oy, r, 0)
        dx, dy, r = pyxel.mouse_x - ox, pyxel.mouse_y - oy, r - r2
        l = (dx * dx + dy * dy) ** 0.5  # math.sqrt
        pyxel.circ(*((pyxel.mouse_x, pyxel.mouse_y) if l < r else (ox+dx*r//l, oy+dy*r//l)), r2, 0)
    pyxel.cls(3)
    [part(ox, 10, 10, 3) for ox in (10, 30)]


pyxel.init(41, 21, scale=2, caption="め", fps=10)
pyxel.mouse(True)
pyxel.run(lambda: None, draw)
