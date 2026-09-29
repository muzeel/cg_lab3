import pygame
import sys
import os

sys.setrecursionlimit(20000)

# Возвращает RGB пикселя или None, если координаты за пределами
def get_pixel(surface, x, y):
    if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
        c = surface.get_at((x, y))
        return (c[0], c[1], c[2])
    return None

# Сравнение двух rgb цветов с допуском
def eq(c1, c2, tol=0):
    if c1 is None or c2 is None:
        return False
    return (abs(c1[0] - c2[0]) <= tol and
            abs(c1[1] - c2[1]) <= tol and
            abs(c1[2] - c2[2]) <= tol)

# 1а) Рекурсивный алгоритм заливки на основе серий пикселов (линий) заданным цветом
def _fill_run_solid(surface, x, y, target, fill_color):
    w, h = surface.get_size()
    if not (0 <= x < w and 0 <= y < h):
        return
    if not eq(get_pixel(surface, x, y), target):
        return

    x1 = x
    while x1 >= 0 and eq(get_pixel(surface, x1, y), target):
        x1 -= 1
    x1 += 1

    x2 = x
    while x2 < w and eq(get_pixel(surface, x2, y), target):
        x2 += 1
    x2 -= 1

    for xi in range(x1, x2 + 1):
        surface.set_at((xi, y), fill_color)

    for ny in (y - 1, y + 1):
        if 0 <= ny < h:
            xi = x1
            while xi <= x2:
                if eq(get_pixel(surface, xi, ny), target):
                    start = xi
                    while xi <= x2 and eq(get_pixel(surface, xi, ny), target):
                        xi += 1
                    _fill_run_solid(surface, start, ny, target, fill_color)
                else:
                    xi += 1

# Заливка сплошным цветом
def flood_fill_solid(surface, x, y, fill_color):
    target = get_pixel(surface, x, y)
    if target is None or eq(target, fill_color):
        return
    _fill_run_solid(surface, x, y, target, fill_color)

# 1б) Рекурсивный алгоритм заливки на основе серий пикселов (линий) рисунком из графического файла
def _fill_run_pattern(surface, x, y, target, pattern, visited):
    w, h = surface.get_size()
    if not (0 <= x < w and 0 <= y < h):
        return
    if (x, y) in visited:
        return
    if not eq(get_pixel(surface, x, y), target):
        return

    x1 = x
    while x1 >= 0 and (x1, y) not in visited and eq(get_pixel(surface, x1, y), target):
        x1 -= 1
    x1 += 1
    x2 = x
    while x2 < w and (x2, y) not in visited and eq(get_pixel(surface, x2, y), target):
        x2 += 1
    x2 -= 1

    pw, ph = pattern.get_size()
    for xi in range(x1, x2 + 1):
        pc = pattern.get_at((xi % pw, y % ph))
        surface.set_at((xi, y), (pc[0], pc[1], pc[2]))
        visited.add((xi, y))

    for ny in (y - 1, y + 1):
        if 0 <= ny < h:
            xi = x1
            while xi <= x2:
                if (xi, ny) not in visited and eq(get_pixel(surface, xi, ny), target):
                    start = xi
                    while (xi <= x2 and (xi, ny) not in visited
                           and eq(get_pixel(surface, xi, ny), target)):
                        xi += 1
                    _fill_run_pattern(surface, start, ny, target, pattern, visited)
                else:
                    xi += 1

# Заливка циклическим рисунком
def flood_fill_pattern(surface, x, y, pattern):
    target = get_pixel(surface, x, y)
    if target is None:
        return
    visited = set()
    _fill_run_pattern(surface, x, y, target, pattern, visited)

# 1в) Выделение границы связной области.

# 8 соседей Мура по часовой стрелке, начиная с E
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1),
        (-1, 0), (-1, -1), (0, -1), (1, -1)]

# Поиск ближайшего пикселя границы если клик не на границе
def snap_to_boundary(surface, x, y, boundary_color, max_r=300):
    w, h = surface.get_size()
    if eq(get_pixel(surface, x, y), boundary_color):
        return (x, y)
    for r in range(1, max_r):
        for dx in range(-r, r + 1):
            for dy in (-r, r):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and \
                   eq(get_pixel(surface, nx, ny), boundary_color):
                    return (nx, ny)
        for dy in range(-r + 1, r):
            for dx in (-r, r):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and \
                   eq(get_pixel(surface, nx, ny), boundary_color):
                    return (nx, ny)
    return None

# Обход границы связной области алгоритмом Мура
def trace_boundary(surface, x, y, boundary_color):
    w, h = surface.get_size()
    start = snap_to_boundary(surface, x, y, boundary_color)
    if start is None:
        return []

    prev_dir = None
    for d in range(8):
        nx = start[0] + DIRS[d][0]
        ny = start[1] + DIRS[d][1]
        if not (0 <= nx < w and 0 <= ny < h) or \
           not eq(get_pixel(surface, nx, ny), boundary_color):
            prev_dir = d
            break
    if prev_dir is None:
        return [start]

    contour = [start]
    cur = start

    max_steps = w * h * 2
    for _ in range(max_steps):
        found = False
        for k in range(1, 9):
            d = (prev_dir + k) % 8
            nx = cur[0] + DIRS[d][0]
            ny = cur[1] + DIRS[d][1]
            if 0 <= nx < w and 0 <= ny < h and \
               eq(get_pixel(surface, nx, ny), boundary_color):
                prev_dir = (d + 4) % 8
                cur = (nx, ny)
                contour.append(cur)
                found = True
                break
        if not found:
            break
        if cur == start and len(contour) > 3:
            break

    return contour

# На случай если pattern.png отсутсвует
def make_default_pattern(size=16):
    surf = pygame.Surface((size, size))
    for py in range(size):
        for px in range(size):
            if ((px // 4) + (py // 4)) % 2 == 0:
                surf.set_at((px, py), (255, 80, 80))
            else:
                surf.set_at((px, py), (60, 60, 220))
    return surf

def main():
    pygame.init()
    W, H = 950, 620
    DRAW_W, DRAW_H = 700, 600
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Задачи 1а, 1б, 1в - заливка и обход границы")

    canvas = pygame.Surface((DRAW_W, DRAW_H))
    canvas.fill((255, 255, 255))

    # Несколько стартовых фигур, чтобы можно было сразу пробовать
    pygame.draw.rect(canvas, (0, 0, 0), (40, 40, 160, 160), 3)
    pygame.draw.circle(canvas, (0, 0, 0), (400, 140), 95, 3)
    pygame.draw.rect(canvas, (0, 0, 0), (90, 300, 220, 200), 3)
    pygame.draw.rect(canvas, (0, 0, 0), (150, 350, 100, 100), 3)
    pygame.draw.polygon(canvas, (0, 0, 0), [(500, 320), (620, 300), (660, 480), (520, 500)], 3)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    pattern_path = os.path.join(script_dir, "pattern.png")

    pattern = None
    if os.path.exists(pattern_path):
        try:
            pattern = pygame.image.load(pattern_path).convert()
            print(f"Шаблон загружен: {pattern_path}")
        except Exception as e:
            print(f"Не удалось загрузить {pattern_path}: {e}")
            pattern = None
    else:
        print(f"pattern.png не найден рядом со скриптом ({script_dir}), "
              f"использован встроенный узор.")

    if pattern is None:
        pattern = make_default_pattern(16)

    font = pygame.font.SysFont("Consolas", 14)
    mode = 'draw'
    pen_color = (0, 0, 0)
    drawing = False
    last_pos = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_c:
                    canvas.fill((255, 255, 255))
                elif event.key == pygame.K_d:
                    mode = 'draw'
                elif event.key == pygame.K_1:
                    mode = '1a'
                elif event.key == pygame.K_2:
                    mode = '1b'
                elif event.key == pygame.K_3:
                    mode = '1c'

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if mx < DRAW_W and my < DRAW_H and event.button == 1:
                    if mode == 'draw':
                        drawing = True
                        last_pos = (mx, my)
                        pygame.draw.circle(canvas, pen_color, (mx, my), 2)

                    elif mode == '1a':
                        flood_fill_solid(canvas, mx, my, (255, 0, 0))

                    elif mode == '1b':
                        flood_fill_pattern(canvas, mx, my, pattern)

                    elif mode == '1c':
                        contour = trace_boundary(canvas, mx, my, (0, 0, 0))
                        for (x, y) in contour:
                            if 0 <= x < DRAW_W and 0 <= y < DRAW_H:
                                canvas.set_at((x, y), (0, 200, 0))
                        print(f"Обойдено пикселей: {len(contour)}")

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    drawing = False
                    last_pos = None

            elif event.type == pygame.MOUSEMOTION:
                if drawing and mode == 'draw':
                    mx, my = event.pos
                    if mx < DRAW_W and my < DRAW_H:
                        if last_pos:
                            pygame.draw.line(canvas, pen_color, last_pos, (mx, my), 3)
                        last_pos = (mx, my)

        screen.fill((180, 180, 180))
        screen.blit(canvas, (0, 0))
        pygame.draw.rect(screen, (235, 235, 235), (DRAW_W, 0, W - DRAW_W, H))

        y = 10
        info = [
            f"Режим: {mode}",
            "",
            "Клавиши:",
            "  d - рисование (зажатое ЛКМ)",
            "  1 - 1а: заливка цветом",
            "  2 - 1б: заливка шаблоном",
            "  3 - 1в: обход границы",
            "  c - очистить",
            "  ESC - выход",
            "",
            "Мышь:",
            "  ЛКМ (зажатое) - рисовать",
            "  ЛКМ (клик) - выполнить действие",
            "",
            "Нарисуйте замкнутую область",
            "и кликните внутрь (1а/1б)",
            "или по границе (1в).",
        ]
        for line in info:
            surf = font.render(line, True, (0, 0, 0))
            screen.blit(surf, (DRAW_W + 10, y))
            y += 18

        screen.blit(pygame.transform.scale(pattern, (64, 64)),
                    (DRAW_W + 10, H - 80))
        screen.blit(font.render("шаблон", True, (0, 0, 0)),
                    (DRAW_W + 80, H - 55))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()