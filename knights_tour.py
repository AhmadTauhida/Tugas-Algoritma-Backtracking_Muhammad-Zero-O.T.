"""
Knight's Tour Visualizer dengan Warnsdorff's Heuristic
========================================================
Kontrol saat visualisasi berjalan:
    SPACE   -> pause / lanjut
    R       -> reset & acak posisi awal
    +/-     -> percepat / perlambat animasi
    Q / ESC -> keluar
"""
 
import sys
import time
import random
import pygame
 
# Warna
BG          = (15,  15,  20)
LIGHT_SQ    = (200, 169, 110)
DARK_SQ     = (90,  62,  40)
VISITED_L   = (100, 170,  95)
VISITED_D   = (55,  120,  50)
CURRENT_CLR = (240, 192,  60)
TRAIL_CLR   = (240, 192,  60, 80)
TEXT_CLR    = (255, 255, 255)
DIM_TEXT    = (120, 120, 130)
GOLD        = (240, 192,  60)
GREEN       = (100, 200,  90)
RED         = (220,  80,  70)
PANEL_BG    = (22,  22,  28)
BORDER_CLR  = (50,  50,  60)
 
# ─────────────────────────── Konstanta ───────────────────────
KNIGHT_MOVES = [(2,1),(1,2),(-1,2),(-2,1),(-2,-1),(-1,-2),(1,-2),(2,-1)]
CELL         = 70       
PANEL_W      = 260
FPS          = 60
 
 
# Algoritma
 
def valid(r, c, n, board):
    return 0 <= r < n and 0 <= c < n and board[r][c] == -1
 
 
def warnsdorff_degree(r, c, n, board):
    """Hitung jumlah gerakan valid dari (r, c) — digunakan sebagai heuristic."""
    return sum(1 for dr, dc in KNIGHT_MOVES if valid(r+dr, c+dc, n, board))
 
 
def solve_warnsdorff(n, start_r, start_c):
    """
    Menyelesaikan Knight's Tour dengan Warnsdorff's Heuristic.
    Mengembalikan list koordinat [(r,c), ...] urutan kunjungan,
    atau None jika gagal.
    """
    board = [[-1]*n for _ in range(n)]
    board[start_r][start_c] = 0
    path = [(start_r, start_c)]
 
    r, c = start_r, start_c
 
    for step in range(1, n*n):
        # Kumpulkan semua gerakan valid beserta derajatnya
        candidates = []
        for dr, dc in KNIGHT_MOVES:
            nr, nc = r+dr, c+dc
            if valid(nr, nc, n, board):
                deg = warnsdorff_degree(nr, nc, n, board)
                candidates.append((deg, nr, nc))
 
        if not candidates:
            return None  # buntu
 
        # Pilih gerakan dengan derajat terkecil (Warnsdorff)
        # Tie-breaking acak agar variasi solusi lebih kaya
        candidates.sort(key=lambda x: x[0])
        min_deg = candidates[0][0]
        best = [c for c in candidates if c[0] == min_deg]
        _, r, c = random.choice(best)
 
        board[r][c] = step
        path.append((r, c))
 
    return path
 
 
# visualisasi pygame
 
class KnightTourViz:
    def __init__(self, n=8, start_r=0, start_c=0):
        self.n        = n
        self.start_r  = start_r
        self.start_c  = start_c
        self.path     = []
        self.step_idx = 0
        self.paused   = False
        self.done     = False
        self.delay    = 0.18   # detik antar langkah
 
        # Hitung ukuran sel agar muat di layar
        max_board = 680
        self.cell = min(CELL, max_board // n)
 
        self.board_px = self.cell * n
        self.win_w    = self.board_px + PANEL_W
        self.win_h    = max(self.board_px + 60, 480)
 
        pygame.init()
        pygame.display.set_caption("Knight's Tour — Warnsdorff Visualizer")
        self.screen = pygame.display.set_mode((self.win_w, self.win_h))
        self.clock  = pygame.time.Clock()
 
        # Font
        self.font_lg = pygame.font.SysFont("monospace", 22, bold=True)
        self.font_md = pygame.font.SysFont("monospace", 16, bold=True)
        self.font_sm = pygame.font.SysFont("monospace", 12)
        self.font_num= pygame.font.SysFont("monospace", max(9, self.cell//5), bold=True)
 
        # Trail surface (alpha)
        self.trail_surf = pygame.Surface((self.board_px, self.board_px), pygame.SRCALPHA)
 
        self._solve()
 
    # ── Hitung solusi ──
    def _solve(self):
        self.path     = []
        self.step_idx = 0
        self.done     = False
 
        path = solve_warnsdorff(self.n, self.start_r, self.start_c)
        if path:
            self.path    = path
            self.success = True
        else:
            self.path    = []
            self.success = False
 
        self.trail_surf.fill((0,0,0,0))
 
    # ── Utilitas gambar ───────────────────────────────────────
    def cell_rect(self, r, c):
        return pygame.Rect(c*self.cell, r*self.cell, self.cell, self.cell)
 
    def draw_board(self):
        visited = set(self.path[:self.step_idx+1]) if self.path else set()
        current = self.path[self.step_idx] if self.path else None
 
        for r in range(self.n):
            for c in range(self.n):
                rect  = self.cell_rect(r, c)
                light = (r+c) % 2 == 0
 
                if (r,c) == current:
                    color = CURRENT_CLR
                elif (r,c) in visited:
                    color = VISITED_L if light else VISITED_D
                else:
                    color = LIGHT_SQ if light else DARK_SQ
 
                pygame.draw.rect(self.screen, color, rect)
 
                # Nomor langkah
                if (r,c) in visited:
                    step_n = self.path.index((r,c))
                    num_surf = self.font_num.render(str(step_n), True,
                                                    (0,0,0) if light else (220,220,200))
                    nr = num_surf.get_rect(topleft=(rect.x+4, rect.y+4))
                    self.screen.blit(num_surf, nr)
 
                # Grid border
                pygame.draw.rect(self.screen, (0,0,0), rect, 1)
 
    def draw_trail(self):
        """Gambar garis jejak kuda."""
        if self.step_idx < 1 or not self.path:
            return
        pts = [(c*self.cell + self.cell//2, r*self.cell + self.cell//2)
               for r,c in self.path[:self.step_idx+1]]
        if len(pts) >= 2:
            pygame.draw.lines(self.screen, (*GOLD, 140), False, pts, 2)
 
    def draw_knight(self):
        if not self.path:
            return
        r, c = self.path[self.step_idx]
        rect  = self.cell_rect(r, c)
        # Gambar lingkaran kuda
        cx, cy = rect.centerx, rect.centery
        pygame.draw.circle(self.screen, (30,30,30), (cx,cy), self.cell//3)
        pygame.draw.circle(self.screen, GOLD,       (cx,cy), self.cell//3, 3)
        txt = self.font_lg.render("♞", True, GOLD)
        tr  = txt.get_rect(center=(cx,cy))
        self.screen.blit(txt, tr)
 
    def draw_panel(self):
        px = self.board_px
        panel = pygame.Rect(px, 0, PANEL_W, self.win_h)
        pygame.draw.rect(self.screen, PANEL_BG, panel)
        pygame.draw.line(self.screen, BORDER_CLR, (px,0),(px,self.win_h), 2)
 
        x0 = px + 16
        y  = 20
 
        # Judul
        t = self.font_lg.render("Knight's Tour", True, GOLD)
        self.screen.blit(t, (x0, y)); y += 30
        t = self.font_sm.render("Warnsdorff's Heuristic", True, DIM_TEXT)
        self.screen.blit(t, (x0, y)); y += 30
 
        pygame.draw.line(self.screen, BORDER_CLR, (px+8,y),(self.win_w-8,y)); y += 14
 
        # Info papan
        def label(s, v, vc=TEXT_CLR):
            ls = self.font_sm.render(s, True, DIM_TEXT)
            vs = self.font_md.render(str(v), True, vc)
            self.screen.blit(ls,(x0,y))
            self.screen.blit(vs,(x0,y+14))
 
        label("Ukuran Papan", f"{self.n} × {self.n}"); y += 44
        label("Posisi Awal",  f"({self.start_r}, {self.start_c})"); y += 44
 
        # Langkah
        cur_step = self.step_idx+1 if self.path else 0
        total    = self.n*self.n
        label("Langkah", f"{cur_step} / {total}", GOLD); y += 44
 
        # Progress bar
        bar_w = PANEL_W - 32
        pygame.draw.rect(self.screen, BORDER_CLR, (x0,y,bar_w,10), border_radius=5)
        fill = int(bar_w * cur_step / total)
        if fill > 0:
            pygame.draw.rect(self.screen, GREEN, (x0,y,fill,10), border_radius=5)
        y += 22
 
        pygame.draw.line(self.screen, BORDER_CLR, (px+8,y),(self.win_w-8,y)); y += 14
 
        # Status
        if self.done:
            if self.success and len(self.path)==self.n*self.n:
                st, sc = "✓ SELESAI!", GREEN
            else:
                st, sc = "✗ GAGAL", RED
        elif self.paused:
            st, sc = "⏸ PAUSED", (200,180,100)
        else:
            st, sc = "▶ BERJALAN...", (100,180,240)
        s = self.font_md.render(st, True, sc)
        self.screen.blit(s,(x0,y)); y += 32
 
        # Delay
        t = self.font_sm.render(f"Delay: {self.delay*1000:.0f} ms", True, DIM_TEXT)
        self.screen.blit(t,(x0,y)); y += 20
 
        pygame.draw.line(self.screen, BORDER_CLR, (px+8,y),(self.win_w-8,y)); y += 14
 
        # Kontrol
        controls = [
            ("SPACE", "Pause / Lanjut"),
            ("R",     "Reset & acak awal"),
            ("+",     "Percepat"),
            ("-",     "Perlambat"),
            ("Q/ESC", "Keluar"),
        ]
        for key, desc in controls:
            ks = self.font_sm.render(key, True, GOLD)
            ds = self.font_sm.render(desc, True, DIM_TEXT)
            self.screen.blit(ks,(x0,y))
            self.screen.blit(ds,(x0+50,y))
            y += 18
 
    def draw_status_bar(self):
        """Bar bawah papan catur."""
        bar = pygame.Rect(0, self.board_px, self.board_px, self.win_h - self.board_px)
        pygame.draw.rect(self.screen, PANEL_BG, bar)
        if self.path and self.step_idx < len(self.path):
            r,c = self.path[self.step_idx]
            msg = f"Langkah {self.step_idx+1}/{self.n*self.n}  →  ({r}, {c})"
        else:
            msg = "Siap."
        t = self.font_sm.render(msg, True, DIM_TEXT)
        self.screen.blit(t,(8, self.board_px+12))
 
    # ── Loop utama ────────────────────────────────────────────
    def run(self):
        last_step_time = time.time()
 
        while True:
            # ── Event ───────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
 
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_q, pygame.K_ESCAPE):
                        pygame.quit(); sys.exit()
 
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused
 
                    elif event.key == pygame.K_r:
                        self.start_r = random.randint(0, self.n-1)
                        self.start_c = random.randint(0, self.n-1)
                        self.paused  = False
                        self._solve()
 
                    elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                        self.delay = max(0.01, self.delay - 0.03)
 
                    elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        self.delay = min(2.0, self.delay + 0.03)
 
            # ── Auto-advance ─────────────────────────────────
            now = time.time()
            if (not self.paused
                    and not self.done
                    and self.path
                    and now - last_step_time >= self.delay):
                if self.step_idx < len(self.path) - 1:
                    self.step_idx += 1
                else:
                    self.done = True
                last_step_time = now
 
            # ── Render ───────────────────────────────────────
            self.screen.fill(BG)
            self.draw_board()
            self.draw_trail()
            self.draw_knight()
            self.draw_panel()
            self.draw_status_bar()
            pygame.display.flip()
            self.clock.tick(FPS)
 
 
# Main
 
def main():
    args = sys.argv[1:]
 
    n       = int(args[0]) if len(args) >= 1 else 8
    start_r = int(args[1]) if len(args) >= 2 else 0
    start_c = int(args[2]) if len(args) >= 3 else 0
 
    if not (5 <= n <= 10):
        print("Ukuran papan harus antara 5–10.")
        sys.exit(1)
 
    if not (0 <= start_r < n and 0 <= start_c < n):
        print(f"Posisi awal harus dalam rentang 0–{n-1}.")
        sys.exit(1)
 
    print(f"Knight's Tour  |  Papan {n}×{n}  |  Start ({start_r},{start_c})")
    print("Menghitung solusi…")
 
    # Coba hingga 5 kali (karena ada tie-breaking acak)
    for attempt in range(5):
        path = solve_warnsdorff(n, start_r, start_c)
        if path:
            print(f"Solusi ditemukan (percobaan {attempt+1}). Memulai visualisasi…\n")
            print("Urutan kunjungan:")
            for i,(r,c) in enumerate(path):
                print(f"  Langkah {i+1:3d}: ({r},{c})", end="\n" if (i+1)%4==0 else "  ")
            print()
            break
    else:
        print("Solusi tidak ditemukan dari posisi ini. Coba posisi lain.")
        sys.exit(1)
 
    viz = KnightTourViz(n, start_r, start_c)
    viz.run()
 
 
if __name__ == "__main__":
    main()