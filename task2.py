import math
import tkinter as tk


WIDTH, HEIGHT   = 640, 480
BACKGROUND      = (25, 25, 35) 
LINE_ALPHA      = 0.9
VIEW_W, VIEW_H  = 900, 640
MIN_ZOOM, MAX_ZOOM = 1, 8

PALETTE = [
    (255, 255, 255)
]

_HEX = ["%02x" % i for i in range(256)]


class Dot:
    def __init__(self, x, y, color=(255, 255, 255)):
        self.X = int(x)
        self.Y = int(y)
        self.C = color


class Line:
    def __init__(self, a, b):
        self.start = a
        self.end = b


class PixelCanvas:
    def __init__(self, w, h, bg=BACKGROUND):
        self.width = w
        self.height = h
        self.background = bg
        self.clear()

    def clear(self):
        r, g, b = self.background
        self.pixels = [
            [[float(r), float(g), float(b)] for _ in range(self.width)]
            for _ in range(self.height)
        ]

    def blend(self, x, y, color, alpha):
        x = int(x)
        y = int(y)
        
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return
        
        px = self.pixels[y][x]
        inv = 1.0 - alpha
        px[0] = px[0] * inv + color[0] * alpha
        px[1] = px[1] * inv + color[1] * alpha
        px[2] = px[2] * inv + color[2] * alpha

    def to_data_string(self):
        hexes = _HEX
        rows = []
        for y in range(self.height):
            src = self.pixels[y]
            row = []
            for px in src:
                r = int(px[0] + 0.5)
                g = int(px[1] + 0.5)
                b = int(px[2] + 0.5)
                
                if r < 0: 
                    r = 0
                elif r > 255: 
                    r = 255
                if g < 0:
                    g = 0
                elif g > 255:
                    g = 255
                if b < 0:
                    b = 0
                elif b > 255:
                    b = 255
                    
                row.append("#" + hexes[r] + hexes[g] + hexes[b])
            rows.append("{" + " ".join(row) + "}")
        return " ".join(rows)


class BresenhamDrawer:
    @staticmethod
    def draw(canvas, line, color, alpha):
        x0, y0 = line.start.X, line.start.Y
        x1, y1 = line.end.X,   line.end.Y
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            canvas.blend(x0, y0, color, alpha)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy


class WuDrawer:
    @staticmethod
    def _fpart(v):  return v - math.floor(v)
    @staticmethod
    def _rfpart(v): return 1.0 - WuDrawer._fpart(v)

    @classmethod
    def draw(cls, canvas, line, color, alpha):
        x0, y0 = line.start.X, line.start.Y
        x1, y1 = line.end.X,   line.end.Y
        
        if x0 == x1 and y0 == y1:
            canvas.blend(x0, y0, color, alpha)
            return
        
        steep = abs(y1 - y0) > abs(x1 - x0)
        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1
        if x0 > x1:
            x0, x1 = x1, x0
            y0, y1 = y1, y0
        
        dx = x1 - x0
        dy = y1 - y0
        gradient = 1.0 if dx == 0 else dy / dx
        
        xpxl1 = int(round(x0))
        ypxl1 = math.floor(y0)
        f = y0 - ypxl1
        if steep:
            canvas.blend(ypxl1,     xpxl1, color, alpha * (1 - f))
            canvas.blend(ypxl1 + 1, xpxl1, color, alpha * f)
        else:
            canvas.blend(xpxl1, ypxl1,     color, alpha * (1 - f))
            canvas.blend(xpxl1, ypxl1 + 1, color, alpha * f)
        
        xpxl2 = int(round(x1))
        ypxl2 = math.floor(y1)
        f = y1 - ypxl2
        if steep:
            canvas.blend(ypxl2,     xpxl2, color, alpha * (1 - f))
            canvas.blend(ypxl2 + 1, xpxl2, color, alpha * f)
        else:
            canvas.blend(xpxl2, ypxl2,     color, alpha * (1 - f))
            canvas.blend(xpxl2, ypxl2 + 1, color, alpha * f)
        
        intery = y0 + gradient
        for x in range(xpxl1 + 1, xpxl2):
            y = math.floor(intery)
            fpart = intery - y
            if steep:
                canvas.blend(y,     x, color, alpha * (1 - fpart))
                canvas.blend(y + 1, x, color, alpha * fpart)
            else:
                canvas.blend(x, y,     color, alpha * (1 - fpart))
                canvas.blend(x, y + 1, color, alpha * fpart)
            intery += gradient

class LineDrawer:
    ALGORITHMS = {"bresenham": BresenhamDrawer, "wu": WuDrawer}

    def __init__(self, canvas, algorithm="wu"):
        self.canvas = canvas
        self.algorithm = algorithm
        self.history = []

    def set_algorithm(self, name):
        if name in self.ALGORITHMS:
            self.algorithm = name

    def add_line(self, line, color, alpha=LINE_ALPHA):
        self.history.append((line, color, alpha, self.algorithm))
        self.ALGORITHMS[self.algorithm].draw(self.canvas, line, color, alpha)

    def redraw_all(self):
        self.canvas.clear()
        for line, color, alpha, algo in self.history:
            self.ALGORITHMS[algo].draw(self.canvas, line, color, alpha)

    def clear(self):
        self.history.clear()
        self.canvas.clear()


class App:
    def __init__(self):
        try:
            old = tk._default_root
            if old is not None:
                old.destroy()
        except Exception:
            pass

        self.root = tk.Tk()
        self.root.title("Отрезки: Брезенхем / Ву")
        self.root.resizable(False, False)

        self.pixel_canvas = PixelCanvas(WIDTH, HEIGHT)
        self.drawer = LineDrawer(self.pixel_canvas, algorithm="wu")

        self.base_photo = tk.PhotoImage(master=self.root, width=WIDTH, height=HEIGHT)

        self.tk_canvas = tk.Canvas(
            self.root, width=VIEW_W, height=VIEW_H,
            highlightthickness=0, bd=0, bg="#000000"
        )
        self.tk_canvas.pack()

        self.status = tk.Label(self.root, anchor="w",
                               font=("Consolas", 10), bg="#111", fg="#ddd")
        self.status.pack(fill="x")

        self.zoom = 1
        self.origin_x = (VIEW_W - WIDTH  * self.zoom) // 2
        self.origin_y = (VIEW_H - HEIGHT * self.zoom) // 2
        self._cached_zoom = None
        self.zoom_photo = None
        self.image_item = None

        # --- состояние рисования ---
        self.pending_dot = None
        self.color_index = 0
        self.mouse_img = (-1, -1)

        # --- первичный рендер ---
        self._render_base()
        self._update_view()
        self._refresh_status()

        # --- события ---
        self.tk_canvas.bind("<Button-1>",       self.on_click)
        self.tk_canvas.bind("<Motion>",         self.on_motion)
        self.tk_canvas.bind("<ButtonPress-3>",  self.on_pan_start)
        self.tk_canvas.bind("<B3-Motion>",      self.on_pan_move)
        self.tk_canvas.bind("<MouseWheel>",     self.on_wheel)     # Windows / macOS
        self.tk_canvas.bind("<Button-4>", lambda e: self.zoom_at(e.x, e.y, +1))  # Linux
        self.tk_canvas.bind("<Button-5>", lambda e: self.zoom_at(e.x, e.y, -1))

        self.root.bind("<b>",     lambda e: self.switch_algorithm("bresenham"))
        self.root.bind("<w>",     lambda e: self.switch_algorithm("wu"))
        self.root.bind("<c>",     lambda e: self.clear_all())
        self.root.bind("<Escape>",lambda e: self.root.destroy())
        self.root.bind("<plus>",  lambda e: self.zoom_at(VIEW_W//2, VIEW_H//2, +1))
        self.root.bind("<equal>", lambda e: self.zoom_at(VIEW_W//2, VIEW_H//2, +1))
        self.root.bind("<minus>", lambda e: self.zoom_at(VIEW_W//2, VIEW_H//2, -1))
        self.root.bind("<Left>",  lambda e: self.pan(-20, 0))
        self.root.bind("<Right>", lambda e: self.pan(+20, 0))
        self.root.bind("<Up>",    lambda e: self.pan(0, -20))
        self.root.bind("<Down>",  lambda e: self.pan(0, +20))
        self.root.focus_set()

        self.root.mainloop()

    
    def _render_base(self):
        """Перерисовать пиксельный буфер в base_photo (изображение 1:1)."""
        data = self.pixel_canvas.to_data_string()
        # put принимает одну строку — формат {'#.. #..'} {'#.. #..'} ...
        self.base_photo.put(data)
        self._cached_zoom = None   # кэш зум-копии устарел

    def _rebuild_zoom_photo(self):
        if self._cached_zoom == self.zoom:
            return
        if self.zoom == 1:
            self.zoom_photo = self.base_photo
        else:
            self.zoom_photo = self.base_photo.zoom(self.zoom)
        self._cached_zoom = self.zoom
        if self.image_item is not None:
            self.tk_canvas.itemconfigure(self.image_item, image=self.zoom_photo)

    def _update_view(self):
        """Пересобрать всё, что зависит от зума/сдвига."""
        self._rebuild_zoom_photo()
        if self.image_item is None:
            self.image_item = self.tk_canvas.create_image(
                self.origin_x, self.origin_y, anchor="nw", image=self.zoom_photo
            )
        else:
            self.tk_canvas.coords(self.image_item, self.origin_x, self.origin_y)

        # Слои поверх изображения
        self.tk_canvas.delete("grid")
        self.tk_canvas.delete("border")
        self.tk_canvas.delete("marker")
        self._draw_grid()
        self._draw_border()
        self._redraw_marker()

    def _draw_border(self):
        x0, y0 = self.origin_x, self.origin_y
        x1 = x0 + WIDTH  * self.zoom
        y1 = y0 + HEIGHT * self.zoom
        self.tk_canvas.create_rectangle(x0, y0, x1, y1,
                                        outline="#777", tags="border")

    def _draw_grid(self):
        if self.zoom < 4:
            return
        s = self.zoom
        x0, y0 = self.origin_x, self.origin_y
        x1 = x0 + WIDTH  * s
        y1 = y0 + HEIGHT * s
        for ix in range(WIDTH + 1):
            x = x0 + ix * s
            if x < 0 or x > VIEW_W: continue
            self.tk_canvas.create_line(x, y0, x, y1, fill="#2a2a3a", tags="grid")
        for iy in range(HEIGHT + 1):
            y = y0 + iy * s
            if y < 0 or y > VIEW_H: continue
            self.tk_canvas.create_line(x0, y, x1, y, fill="#2a2a3a", tags="grid")

    def _redraw_marker(self):
        self.tk_canvas.delete("marker")
        if self.pending_dot is None:
            return
        s = self.zoom
        x = self.origin_x + self.pending_dot.X * s
        y = self.origin_y + self.pending_dot.Y * s
        r = max(3, s)
        self.tk_canvas.create_oval(x - r, y - r, x + r, y + r,
                                   outline="#ffffff", width=2, tags="marker")

    def _canvas_to_image(self, cx, cy):
        return ((cx - self.origin_x) // self.zoom,
                (cy - self.origin_y) // self.zoom)

    def _current_color(self):
        return PALETTE[self.color_index % len(PALETTE)]

    def on_click(self, event):
        ix, iy = self._canvas_to_image(event.x, event.y)
        if not (0 <= ix < WIDTH and 0 <= iy < HEIGHT):
            return
        if self.pending_dot is None:
            self.pending_dot = Dot(ix, iy, self._current_color())
            self._redraw_marker()
        else:
            start = self.pending_dot
            end = Dot(ix, iy, start.C)
            self.drawer.add_line(Line(start, end), color=start.C)
            self.pending_dot = None
            self.color_index += 1
            self._render_base()
            self._update_view()
        self._refresh_status()

    def on_motion(self, event):
        self.mouse_img = self._canvas_to_image(event.x, event.y)
        self._refresh_status()

    def on_wheel(self, event):
        if event.delta > 0:
            self.zoom_at(event.x, event.y, +1)
        else:
            self.zoom_at(event.x, event.y, -1)

    def zoom_at(self, cx, cy, direction):
        old = self.zoom
        new = max(MIN_ZOOM, min(MAX_ZOOM, old + direction))
        if new == old:
            return
        ix = (cx - self.origin_x) / old
        iy = (cy - self.origin_y) / old
        self.zoom = new
        self.origin_x = int(round(cx - ix * new))
        self.origin_y = int(round(cy - iy * new))
        self._update_view()
        self._refresh_status()

    def pan(self, dx, dy):
        self.origin_x += dx
        self.origin_y += dy
        self._update_view()

    def on_pan_start(self, event):
        self._pan_start  = (event.x, event.y)
        self._pan_origin = (self.origin_x, self.origin_y)

    def on_pan_move(self, event):
        dx = event.x - self._pan_start[0]
        dy = event.y - self._pan_start[1]
        self.origin_x = self._pan_origin[0] + dx
        self.origin_y = self._pan_origin[1] + dy
        self._update_view()

    def switch_algorithm(self, name):
        self.drawer.set_algorithm(name)
        self.drawer.redraw_all()
        self._render_base()
        self._update_view()
        self._refresh_status()

    def clear_all(self):
        self.drawer.clear()
        self.pending_dot = None
        self.color_index = 0
        self._render_base()
        self._update_view()
        self._refresh_status()

    # ------------------------------------------------------------------
    def _refresh_status(self):
        algo = "Брезенхем" if self.drawer.algorithm == "bresenham" else "Ву"
        hint = "ЛКМ: 1-я точка" if self.pending_dot is None else "ЛКМ: 2-я точка"
        mx, my = self.mouse_img
        self.status.config(
            text=(f"[{algo}]  {hint}   pixel=({mx},{my})  zoom={self.zoom}x   "
                  f"|  колесо / +- : зум,  ПКМ-драг / стрелки: сдвиг,  "
                  f"B/W: алгоритм,  C: очистить,  Esc: выход")
        )


if __name__ == "__main__":
    App()