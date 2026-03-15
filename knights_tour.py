import sys
import time
import random
import pygame
 
 
KNIGHT_MOVES = [(2,1),(1,2),(-1,2),(-2,1),(-2,-1),(-1,-2),(1,-2),(2,-1)]
 
# Papan
LIGHT_SQ     = (200, 169, 110)
DARK_SQ      = (90,  62,  40)
VISITED_L    = (100, 170,  95)   # hijau terang — maju
VISITED_D    = (55,  120,  50)   # hijau gelap  — maju
BT_FLASH_L   = (210,  90,  75)   # merah terang — backtrack
BT_FLASH_D   = (155,  55,  45)   # merah gelap  — backtrack
CURRENT_CLR  = (240, 192,  60)   # kuning — posisi kuda
WARNSDORFF_H = (100, 160, 230)   # biru muda — highlight kandidat terbaik
 
# UI
BG           = (13,  13,  18)
PANEL_BG     = (20,  20,  27)
BORDER_CLR   = (48,  48,  60)
GOLD         = (240, 192,  60)
GREEN        = ( 95, 195,  85)
RED          = (220,  80,  70)
ORANGE       = (230, 145,  55)
BLUE         = (100, 165, 230)
WHITE        = (240, 240, 245)
DIM          = (115, 115, 128)
 
PANEL_W = 275
FPS     = 60
 
 

def valid(r, c, n, board):
    return 0 <= r < n and 0 <= c < n and board[r][c] == -1
 
 
def warnsdorff_degree(r, c, n, board):
    """
    Hitung jumlah gerakan valid dari (r, c).
    Nilai kecil = kotak sulit dijangkau = prioritas tinggi (Warnsdorff).
    """
    return sum(1 for dr, dc in KNIGHT_MOVES if valid(r+dr, c+dc, n, board))
 
 
def solve_hybrid(n, start_r, start_c, max_events=5_000_000):
    board    = [[-1] * n for _ in range(n)]
    events   = []
    solved   = [False]
    sol_path = []
 
    board[start_r][start_c] = 0
    events.append(('move', start_r, start_c, 0))
 
    def bt(r, c, step):
        if solved[0] or len(events) >= max_events:
            return
 
        if step == n * n:
            solved[0] = True
            # Rekonstruksi path dari board
            ordered = [None] * (n * n)
            for rr in range(n):
                for cc in range(n):
                    if board[rr][cc] >= 0:
                        ordered[board[rr][cc]] = (rr, cc)
            sol_path.extend(ordered)
            return
 
        # ── WARNSDORFF: kumpulkan + urutkan kandidat ──────────
        candidates = []
        for dr, dc in KNIGHT_MOVES:
            nr, nc = r + dr, c + dc
            if valid(nr, nc, n, board):
                deg = warnsdorff_degree(nr, nc, n, board)
                candidates.append((deg, nr, nc))
 
        # Urutkan: degree terkecil → paling diprioritaskan
        # Tie-breaking acak agar variasi solusi lebih kaya
        candidates.sort(key=lambda x: (x[0], random.random()))
 
        # ── BACKTRACKING: coba tiap kandidat dalam urutan terbaik
        for _, nr, nc in candidates:
            if solved[0] or len(events) >= max_events:
                return
 
            # Maju
            board[nr][nc] = step
            events.append(('move', nr, nc, step))
 
            bt(nr, nc, step + 1)
 
            if solved[0]:
                return
 
            # Mundur (backtrack) — Warnsdorff gagal, coba kandidat berikutnya
            board[nr][nc] = -1
            events.append(('back', nr, nc))
 
    bt(start_r, start_c, 1)
 
    return events, (sol_path if solved[0] else None)
 
 
# ══════════════════════════════════════════════════════════════
#  VISUALIZER
# ══════════════════════════════════════════════════════════════
 
class KnightTourViz:
 
    def __init__(self, n, start_r, start_c):
        self.n       = n
        self.start_r = start_r
        self.start_c = start_c
 
        self.cell   = min(72, max(46, 420 // n))
        self.brd_px = self.cell * n
        self.win_w  = self.brd_px + PANEL_W
        self.win_h  = max(self.brd_px + 60, 560)
 
        pygame.init()
        pygame.display.set_caption("Knight's Tour — Hybrid Backtracking + Warnsdorff")
        self.screen = pygame.display.set_mode((self.win_w, self.win_h))
        self.clock  = pygame.time.Clock()
 
        self.font_lg  = pygame.font.SysFont("monospace", 20, bold=True)
        self.font_md  = pygame.font.SysFont("monospace", 15, bold=True)
        self.font_sm  = pygame.font.SysFont("monospace", 12)
        self.font_xs  = pygame.font.SysFont("monospace", 10)
        self.font_num = pygame.font.SysFont("monospace",
                                            max(9, self.cell // 5), bold=True)
 
        # State
        self.events       = []
        self.solution     = None
        self.ev_idx       = 0
        self.board        = []
        self.knight_r     = start_r
        self.knight_c     = start_c
        self.paused       = False
        self.done         = False
        self.delay        = 0.04
        self.move_count   = 0
        self.back_count   = 0
        self.total_events = 0
        self.solved       = False
 
        # Riwayat backtrack (untuk flash merah)
        self.recent_backs = []   # list of (r, c, timestamp)
 
        self._compute()
 
    # ── Hitung solusi ─────────────────────────────────────────
    def _compute(self):
        self.board = [[-1]*self.n for _ in range(self.n)]
        self.board[self.start_r][self.start_c] = 0
 
        print(f"\nMenghitung hybrid backtracking+Warnsdorff "
              f"untuk papan {self.n}×{self.n}…")
 
        t0 = time.time()
        self.events, self.solution = solve_hybrid(self.n,
                                                   self.start_r,
                                                   self.start_c)
        elapsed = time.time() - t0
 
        self.total_events = len(self.events)
        self.solved       = self.solution is not None
 
        total_moves = sum(1 for e in self.events if e[0] == 'move')
        total_backs = sum(1 for e in self.events if e[0] == 'back')
 
        print(f"{'Solusi ditemukan' if self.solved else 'Tidak ada solusi'}  "
              f"| Waktu: {elapsed:.3f}s  "
              f"| Maju: {total_moves:,}  "
              f"| Mundur: {total_backs:,}  "
              f"| Total event: {self.total_events:,}")
 
        # Reset state animasi
        self.board        = [[-1]*self.n for _ in range(self.n)]
        self.board[self.start_r][self.start_c] = 0
        self.ev_idx       = 1
        self.knight_r     = self.start_r
        self.knight_c     = self.start_c
        self.move_count   = 1
        self.back_count   = 0
        self.done         = False
        self.paused       = False
        self.recent_backs = []
 
    # ── Satu langkah animasi ──────────────────────────────────
    def _step(self):
        if self.ev_idx >= len(self.events):
            self.done = True
            return
 
        ev = self.events[self.ev_idx]
        self.ev_idx += 1
 
        if ev[0] == 'move':
            _, r, c, step = ev
            self.board[r][c] = step
            self.knight_r = r
            self.knight_c = c
            self.move_count += 1
 
        else:  # 'back'
            _, r, c = ev
            self.board[r][c] = -1
            self.back_count += 1
            self.recent_backs.append((r, c, time.time()))
            # Kuda kembali ke kotak dengan nilai terbesar yang tersisa
            max_s, br, bc = -1, self.knight_r, self.knight_c
            for rr in range(self.n):
                for cc in range(self.n):
                    if self.board[rr][cc] > max_s:
                        max_s = self.board[rr][cc]
                        br, bc = rr, cc
            self.knight_r, self.knight_c = br, bc
 
    # ── Skip ke solusi final ──────────────────────────────────
    def _skip_to_final(self):
        if not self.solution:
            return
        self.board = [[-1]*self.n for _ in range(self.n)]
        for ev in self.events:
            if ev[0] == 'move':
                _, r, c, step = ev
                self.board[r][c] = step
            else:
                _, r, c = ev
                self.board[r][c] = -1
 
        lr, lc = self.solution[-1]
        self.knight_r = lr
        self.knight_c = lc
        self.ev_idx   = len(self.events)
        self.done     = True
        self.move_count = self.n * self.n
        self.back_count = sum(1 for e in self.events if e[0] == 'back')
        self.recent_backs = []
 
    # ── Render papan ─────────────────────────────────────────
    def draw_board(self):
        now = time.time()
        # Hapus flash lama (> 0.4 detik)
        self.recent_backs = [(r, c, t) for r, c, t in self.recent_backs
                             if now - t < 0.4]
        back_set = {(r, c) for r, c, _ in self.recent_backs}
 
        for r in range(self.n):
            for c in range(self.n):
                rect  = pygame.Rect(c*self.cell, r*self.cell,
                                    self.cell, self.cell)
                light = (r + c) % 2 == 0
                val   = self.board[r][c]
 
                if r == self.knight_r and c == self.knight_c:
                    col = CURRENT_CLR
                elif (r, c) in back_set:
                    # Flash merah — baru saja di-backtrack
                    age   = now - next(t for rr,cc,t in self.recent_backs
                                       if rr==r and cc==c)
                    alpha = max(0, 1 - age / 0.4)
                    base  = BT_FLASH_L if light else BT_FLASH_D
                    norm  = LIGHT_SQ   if light else DARK_SQ
                    col   = tuple(int(b*alpha + n*(1-alpha))
                                  for b, n in zip(base, norm))
                elif val >= 0:
                    col = VISITED_L if light else VISITED_D
                else:
                    col = LIGHT_SQ if light else DARK_SQ
 
                pygame.draw.rect(self.screen, col, rect)
 
                # Nomor langkah
                if val >= 0 and not (r == self.knight_r and c == self.knight_c):
                    surf = self.font_num.render(str(val), True,
                           (0,0,0) if light else (210,210,190))
                    self.screen.blit(surf,
                                     surf.get_rect(topleft=(rect.x+3, rect.y+3)))
 
                pygame.draw.rect(self.screen, (0,0,0), rect, 1)
 
    # ── Render jejak garis ────────────────────────────────────
    def draw_trail(self):
        max_step = -1
        for r in range(self.n):
            for c in range(self.n):
                if self.board[r][c] > max_step:
                    max_step = self.board[r][c]
        if max_step < 1:
            return
 
        ordered = [None] * (max_step + 1)
        for r in range(self.n):
            for c in range(self.n):
                v = self.board[r][c]
                if 0 <= v <= max_step:
                    ordered[v] = (r, c)
 
        pts = [(c*self.cell + self.cell//2, r*self.cell + self.cell//2)
               for r, c in ordered if (r, c) is not None]
        if len(pts) >= 2:
            pygame.draw.lines(self.screen, (*GOLD, 110), False, pts, 2)
 
    # ── Render ikon kuda ─────────────────────────────────────
    def draw_knight(self):
        r, c   = self.knight_r, self.knight_c
        rect   = pygame.Rect(c*self.cell, r*self.cell, self.cell, self.cell)
        cx, cy = rect.centerx, rect.centery
        pygame.draw.circle(self.screen, (25,25,30), (cx,cy), self.cell//3)
        pygame.draw.circle(self.screen, GOLD,       (cx,cy), self.cell//3, 3)
        t = self.font_lg.render("♞", True, GOLD)
        self.screen.blit(t, t.get_rect(center=(cx,cy)))
 
    # ── Render panel samping ──────────────────────────────────
    def draw_panel(self):
        px = self.brd_px
        pygame.draw.rect(self.screen, PANEL_BG, (px, 0, PANEL_W, self.win_h))
        pygame.draw.line(self.screen, BORDER_CLR, (px,0),(px,self.win_h), 2)
 
        x0, y = px + 16, 16
 
        # ── Judul ─────────────────────────────────────────────
        self.screen.blit(
            self.font_lg.render("Knight's Tour", True, GOLD), (x0, y))
        y += 24
        self.screen.blit(
            self.font_sm.render("Hybrid Backtrack + Warnsdorff", True, DIM),
            (x0, y))
        y += 22
        pygame.draw.line(self.screen, BORDER_CLR,
                         (px+8,y),(self.win_w-8,y)); y += 10
 
        # ── Info umum ─────────────────────────────────────────
        def info(label, val, vc=WHITE):
            self.screen.blit(
                self.font_xs.render(label, True, DIM), (x0, y))
            self.screen.blit(
                self.font_md.render(str(val), True, vc), (x0, y+13))
 
        info("Papan",      f"{self.n} × {self.n}"); y += 36
        info("Posisi awal",f"({self.start_r}, {self.start_c})"); y += 36
        pygame.draw.line(self.screen, BORDER_CLR,
                         (px+8,y),(self.win_w-8,y)); y += 10
 
        # ── Statistik live ────────────────────────────────────
        total_ev = max(self.total_events, 1)
        pct_ev   = self.ev_idx / total_ev * 100
 
        info("Event diputar",
             f"{self.ev_idx:,} / {self.total_events:,}", GOLD); y += 36
 
        # Progress bar event
        bw = PANEL_W - 32
        pygame.draw.rect(self.screen, BORDER_CLR, (x0,y,bw,7), border_radius=3)
        fw = int(bw * pct_ev / 100)
        if fw > 0:
            pygame.draw.rect(self.screen, GOLD, (x0,y,fw,7), border_radius=3)
        y += 16
 
        info("Langkah MAJU",   f"{self.move_count:,}", GREEN);  y += 36
        info("Langkah MUNDUR", f"{self.back_count:,}", RED);    y += 36
 
        ratio = self.back_count / max(self.move_count, 1)
        col_r = GREEN if ratio < 0.5 else (ORANGE if ratio < 5 else RED)
        info("Rasio mundur/maju", f"{ratio:.2f}×", col_r); y += 36
 
        cells = sum(1 for r in range(self.n) for c in range(self.n)
                    if self.board[r][c] >= 0)
        info("Kotak dikunjungi",
             f"{cells} / {self.n*self.n}",
             GREEN if cells == self.n*self.n else WHITE); y += 36
 
        # Progress bar kotak
        pygame.draw.rect(self.screen, BORDER_CLR, (x0,y,bw,7), border_radius=3)
        fw2 = int(bw * cells / (self.n * self.n))
        if fw2 > 0:
            pygame.draw.rect(self.screen, GREEN, (x0,y,fw2,7), border_radius=3)
        y += 16
 
        pygame.draw.line(self.screen, BORDER_CLR,
                         (px+8,y),(self.win_w-8,y)); y += 10
 
        # ── Status ───────────────────────────────────────────
        if self.done:
            st = "SOLUSI DITEMUKAN!" if self.solved else "TIDAK ADA SOLUSI"
            sc = GREEN if self.solved else RED
        elif self.paused:
            st, sc = "PAUSED", (200,180,90)
        else:
            st, sc = "BERJALAN...", (95, 175, 240)
        self.screen.blit(self.font_md.render(st, True, sc), (x0, y)); y += 26
 
        delay_ms = int(self.delay * 1000)
        self.screen.blit(
            self.font_sm.render(f"Delay: {delay_ms} ms", True, DIM), (x0,y))
        y += 20
 
        pygame.draw.line(self.screen, BORDER_CLR,
                         (px+8,y),(self.win_w-8,y)); y += 10
 
        # ── Legenda ──────────────────────────────────────────
        def legend(col, label):
            nonlocal y
            pygame.draw.rect(self.screen, col, (x0,y+2,13,11), border_radius=2)
            self.screen.blit(self.font_sm.render(label, True, DIM), (x0+18, y))
            y += 17
 
        legend(VISITED_L,   "Kotak dikunjungi (maju)")
        legend(BT_FLASH_L,  "Flash merah (backtrack)")
        legend(CURRENT_CLR, "Posisi kuda sekarang")
        y += 4
 
        pygame.draw.line(self.screen, BORDER_CLR,
                         (px+8,y),(self.win_w-8,y)); y += 10
 
        # ── Kontrol ───────────────────────────────────────────
        ctrl = [
            ("SPACE", "Pause / Lanjut"),
            ("S",     "Skip ke solusi"),
            ("R",     "Reset & acak awal"),
            ("+/-",   "Kecepatan"),
            ("Q/ESC", "Keluar"),
        ]
        for key, desc in ctrl:
            self.screen.blit(self.font_sm.render(key,  True, GOLD), (x0, y))
            self.screen.blit(self.font_sm.render(desc, True, DIM),  (x0+50, y))
            y += 16
 
    # ── Status bar bawah papan ────────────────────────────────
    def draw_statusbar(self):
        bar_h = self.win_h - self.brd_px
        pygame.draw.rect(self.screen, PANEL_BG,
                         (0, self.brd_px, self.brd_px, bar_h))
 
        if 0 < self.ev_idx <= len(self.events):
            ev = self.events[self.ev_idx - 1]
            if ev[0] == 'move':
                msg = f"MAJU    langkah {ev[3]:3d} → ({ev[1]},{ev[2]})"
                col = GREEN
            else:
                msg = f"MUNDUR  hapus kotak ({ev[1]},{ev[2]})"
                col = RED
        elif self.done:
            msg = ("Selesai — Solusi ditemukan!"
                   if self.solved else "Selesai — Tidak ada solusi")
            col = GREEN if self.solved else RED
        else:
            msg, col = "Siap.", DIM
 
        self.screen.blit(self.font_sm.render(msg, True, col),
                         (8, self.brd_px + 10))
 
        # Mini info kanan
        mini = (f"Maju: {self.move_count:,}   "
                f"Mundur: {self.back_count:,}   "
                f"Rasio: {self.back_count/max(self.move_count,1):.2f}×")
        surf = self.font_xs.render(mini, True, DIM)
        self.screen.blit(surf,
                         (self.brd_px - surf.get_width() - 8,
                          self.brd_px + 10))
 
    # ── Loop utama ────────────────────────────────────────────
    def run(self):
        last_step = time.time()
 
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
 
                if event.type == pygame.KEYDOWN:
                    k = event.key
 
                    if k in (pygame.K_q, pygame.K_ESCAPE):
                        pygame.quit(); sys.exit()
 
                    elif k == pygame.K_SPACE:
                        self.paused = not self.paused
 
                    elif k == pygame.K_s:
                        self._skip_to_final()
 
                    elif k == pygame.K_r:
                        self.start_r = random.randint(0, self.n - 1)
                        self.start_c = random.randint(0, self.n - 1)
                        self._compute()
 
                    elif k in (pygame.K_PLUS, pygame.K_EQUALS,
                                pygame.K_KP_PLUS):
                        self.delay = max(0.003, self.delay - 0.015)
 
                    elif k in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        self.delay = min(2.0, self.delay + 0.015)
 
            # Auto-advance — beberapa step per frame saat delay sangat kecil
            now = time.time()
            if not self.paused and not self.done:
                if now - last_step >= self.delay:
                    steps = max(1, int(0.016 / max(self.delay, 0.001)))
                    for _ in range(steps):
                        if not self.done:
                            self._step()
                    last_step = now
 
            # Render
            self.screen.fill(BG)
            self.draw_board()
            self.draw_trail()
            self.draw_knight()
            self.draw_panel()
            self.draw_statusbar()
            pygame.display.flip()
            self.clock.tick(FPS)
 
 
# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
 
def main():
    args = sys.argv[1:]
 
    n       = int(args[0]) if len(args) >= 1 else 8
    start_r = int(args[1]) if len(args) >= 2 else 0
    start_c = int(args[2]) if len(args) >= 3 else 0
 
    if not (4 <= n <= 10):
        print("Ukuran papan harus antara 4–10.")
        sys.exit(1)
 
    if not (0 <= start_r < n and 0 <= start_c < n):
        print(f"Posisi awal harus dalam rentang 0–{n-1}.")
        sys.exit(1)
 
    
 
    viz = KnightTourViz(n, start_r, start_c)
    viz.run()
 
 
if __name__ == "__main__":
    main()