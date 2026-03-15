
import sys
import time
import random
import pygame

# ─── Warna ─────────────────────────────────────────────────────
BG           = (15,  15,  20)
LIGHT_SQ     = (200, 169, 110)
DARK_SQ      = (90,  62,  40)
VISIT_L      = (100, 170,  95)   # hijau terang — kotak dikunjungi
VISIT_D      = (55,  120,  50)   # hijau gelap
BACKTRACK_L  = (200,  80,  70)   # merah terang — sedang di-backtrack
BACKTRACK_D  = (150,  50,  40)   # merah gelap
CURRENT_CLR  = (240, 192,  60)   # kuning — posisi kuda sekarang
GOLD         = (240, 192,  60)
GREEN        = (100, 200,  90)
RED          = (220,  80,  70)
ORANGE       = (230, 140,  50)
PANEL_BG     = (22,  22,  28)
BORDER_CLR   = (50,  50,  60)
DIM_TEXT     = (120, 120, 130)
WHITE        = (255, 255, 255)

# ─── Konstanta ─────────────────────────────────────────────────
KNIGHT_MOVES = [(2,1),(1,2),(-1,2),(-2,1),(-2,-1),(-1,-2),(1,-2),(2,-1)]
PANEL_W      = 270
FPS          = 60


# ═══════════════════════════════════════════════════════════════
#  BACKTRACKING — menghasilkan daftar "event" untuk diputar ulang
# ═══════════════════════════════════════════════════════════════

# Setiap event: ('move', r, c, step)  — kuda maju ke (r,c) sebagai langkah ke-step
#               ('back', r, c)        — kuda mundur, (r,c) dihapus dari papan

def solve_backtrack(n, start_r, start_c, max_events=2_000_000):
    """
    Jalankan backtracking murni dan rekam setiap langkah maju/mundur.
    Kembalikan (events, solution_path) atau (events, None) jika tidak ada solusi.
    max_events membatasi rekaman agar tidak kehabisan memori.
    """
    board  = [[-1] * n for _ in range(n)]
    events = []
    solved = [False]
    sol_path = []

    def valid(r, c):
        return 0 <= r < n and 0 <= c < n and board[r][c] == -1

    def bt(r, c, step):
        if solved[0]:
            return
        if len(events) >= max_events:
            return

        if step == n * n:
            solved[0] = True
            sol_path.extend(
                [(r2, c2) for r2 in range(n) for c2 in range(n)
                 if board[r2][c2] >= 0]
            )
            return

        for dr, dc in KNIGHT_MOVES:
            if solved[0]:
                return
            nr, nc = r + dr, c + dc
            if valid(nr, nc):
                board[nr][nc] = step
                events.append(('move', nr, nc, step))
                bt(nr, nc, step + 1)
                if solved[0]:
                    return
                board[nr][nc] = -1
                events.append(('back', nr, nc))

    board[start_r][start_c] = 0
    events.append(('move', start_r, start_c, 0))
    bt(start_r, start_c, 1)

    return events, (sol_path if solved[0] else None)


# ═══════════════════════════════════════════════════════════════
#  VISUALIZER
# ═══════════════════════════════════════════════════════════════

class KnightTourViz:
    def __init__(self, n, start_r, start_c):
        self.n       = n
        self.start_r = start_r
        self.start_c = start_c

        self.cell    = min(68, max(44, 400 // n))
        self.board_w = self.cell * n
        self.win_w   = self.board_w + PANEL_W
        self.win_h   = max(self.board_w + 64, 520)

        pygame.init()
        pygame.display.set_caption("Knight's Tour — Pure Backtracking")
        self.screen = pygame.display.set_mode((self.win_w, self.win_h))
        self.clock  = pygame.time.Clock()

        self.font_lg  = pygame.font.SysFont("monospace", 20, bold=True)
        self.font_md  = pygame.font.SysFont("monospace", 15, bold=True)
        self.font_sm  = pygame.font.SysFont("monospace", 12)
        self.font_num = pygame.font.SysFont("monospace", max(9, self.cell // 5), bold=True)

        # State animasi
        self.events       = []
        self.solution     = None
        self.ev_idx       = 0          # index event yang sedang diputar
        self.board        = []         # board saat ini (nilai langkah atau -1)
        self.knight_r     = start_r
        self.knight_c     = start_c
        self.paused       = False
        self.done         = False
        self.show_final   = False      # True = tampilkan solusi akhir saja
        self.delay        = 0.05       # detik antar event
        self.move_count   = 0
        self.back_count   = 0
        self.total_events = 0
        self.solved       = False

        self._compute()

    # ── Hitung semua event ────────────────────────────────────
    def _compute(self):
        self.board = [[-1] * self.n for _ in range(self.n)]
        self.board[self.start_r][self.start_c] = 0

        print(f"Menghitung backtracking untuk papan {self.n}×{self.n}…")
        print("(Ini bisa memakan waktu beberapa detik untuk papan 6×6+)")

        t0 = time.time()
        self.events, self.solution = solve_backtrack(
            self.n, self.start_r, self.start_c
        )
        elapsed = time.time() - t0

        self.total_events = len(self.events)
        self.solved = self.solution is not None

        if self.solved:
            print(f"Solusi ditemukan! Total event: {self.total_events:,}  "
                  f"| Waktu hitung: {elapsed:.2f}s")
        else:
            print(f"Tidak ada solusi dari posisi ini.  "
                  f"Total event: {self.total_events:,}  "
                  f"| Waktu hitung: {elapsed:.2f}s")

        # Reset state animasi
        self.board        = [[-1] * self.n for _ in range(self.n)]
        self.board[self.start_r][self.start_c] = 0
        self.ev_idx       = 1          # event[0] adalah langkah awal, sudah di-apply
        self.knight_r     = self.start_r
        self.knight_c     = self.start_c
        self.move_count   = 1
        self.back_count   = 0
        self.done         = False
        self.show_final   = False
        self.paused       = False

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
        else:
            _, r, c = ev
            self.board[r][c] = -1
            self.back_count += 1
            # Kuda kembali ke posisi sebelum (r,c)
            # Cari posisi terakhir yang masih ada di board
            max_step = -1
            for rr in range(self.n):
                for cc in range(self.n):
                    if self.board[rr][cc] > max_step:
                        max_step = self.board[rr][cc]
                        self.knight_r = rr
                        self.knight_c = cc

    # ── Tampilkan solusi final langsung ──────────────────────
    def _apply_final(self):
        if self.solution is None:
            return
        self.board = [[-1] * self.n for _ in range(self.n)]
        # Terapkan semua event maju saja hingga akhir
        for ev in self.events:
            if ev[0] == 'move':
                _, r, c, step = ev
                self.board[r][c] = step
            else:
                _, r, c = ev
                self.board[r][c] = -1
        lr, lc = 0, 0
        for rr in range(self.n):
            for cc in range(self.n):
                if self.board[rr][cc] == self.n * self.n - 1:
                    lr, lc = rr, cc
        self.knight_r = lr
        self.knight_c = lc
        self.ev_idx   = len(self.events)
        self.done     = True
        self.show_final = True
        self.move_count = self.n * self.n
        self.back_count = sum(1 for e in self.events if e[0] == 'back')

    # ── Gambar papan ─────────────────────────────────────────
    def draw_board(self):
        for r in range(self.n):
            for c in range(self.n):
                rect  = pygame.Rect(c*self.cell, r*self.cell, self.cell, self.cell)
                light = (r + c) % 2 == 0
                val   = self.board[r][c]

                if r == self.knight_r and c == self.knight_c:
                    color = CURRENT_CLR
                elif val >= 0:
                    # Kotak dikunjungi — cek apakah ini langkah terakhir rantai
                    # (ada nilai lebih besar? artinya sudah "lama" dikunjungi)
                    color = VISIT_L if light else VISIT_D
                else:
                    color = LIGHT_SQ if light else DARK_SQ

                pygame.draw.rect(self.screen, color, rect)

                # Nomor langkah
                if val >= 0 and not (r == self.knight_r and c == self.knight_c):
                    surf = self.font_num.render(str(val), True,
                           (0,0,0) if light else (220,220,200))
                    self.screen.blit(surf, surf.get_rect(topleft=(rect.x+3, rect.y+3)))

                pygame.draw.rect(self.screen, (0,0,0), rect, 1)

    # ── Gambar jejak backtrack (kotak merah sementara) ───────
    def draw_backtrack_flash(self):
        """Sorot kotak yang baru saja di-backtrack (merah sekilas)."""
        if self.ev_idx == 0 or self.ev_idx > len(self.events):
            return
        # Lihat beberapa event terakhir
        look_back = min(4, self.ev_idx)
        for i in range(self.ev_idx - look_back, self.ev_idx):
            ev = self.events[i]
            if ev[0] == 'back':
                _, r, c = ev
                light = (r + c) % 2 == 0
                rect  = pygame.Rect(c*self.cell, r*self.cell, self.cell, self.cell)
                surf  = pygame.Surface((self.cell, self.cell), pygame.SRCALPHA)
                surf.fill((*BACKTRACK_L, 160) if light else (*BACKTRACK_D, 160))
                self.screen.blit(surf, rect)

    # ── Gambar jejak garis kuda ───────────────────────────────
    def draw_trail(self):
        pts = []
        max_step = -1
        for r in range(self.n):
            for c in range(self.n):
                if self.board[r][c] >= 0:
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
               for (r, c) in ordered if (r,c) is not None]
        if len(pts) >= 2:
            pygame.draw.lines(self.screen, (*GOLD, 100), False, pts, 2)

    # ── Gambar kuda ──────────────────────────────────────────
    def draw_knight(self):
        r, c  = self.knight_r, self.knight_c
        rect  = pygame.Rect(c*self.cell, r*self.cell, self.cell, self.cell)
        cx, cy = rect.centerx, rect.centery
        pygame.draw.circle(self.screen, (30,30,30), (cx,cy), self.cell//3)
        pygame.draw.circle(self.screen, GOLD,       (cx,cy), self.cell//3, 3)
        t = self.font_lg.render("♞", True, GOLD)
        self.screen.blit(t, t.get_rect(center=(cx,cy)))

    # ── Gambar panel samping ──────────────────────────────────
    def draw_panel(self):
        px = self.board_w
        pygame.draw.rect(self.screen, PANEL_BG, (px,0,PANEL_W,self.win_h))
        pygame.draw.line(self.screen, BORDER_CLR, (px,0),(px,self.win_h), 2)

        x0, y = px + 16, 18

        # Judul
        t = self.font_lg.render("Knight's Tour", True, GOLD)
        self.screen.blit(t, (x0, y)); y += 26
        t = self.font_sm.render("Pure Backtracking", True, DIM_TEXT)
        self.screen.blit(t, (x0, y)); y += 24
        pygame.draw.line(self.screen, BORDER_CLR, (px+8,y),(self.win_w-8,y)); y += 12

        # Info
        def row(label, val, vc=WHITE):
            ls = self.font_sm.render(label, True, DIM_TEXT)
            vs = self.font_md.render(str(val), True, vc)
            self.screen.blit(ls, (x0, y))
            self.screen.blit(vs, (x0, y+14))

        row("Papan", f"{self.n} × {self.n}"); y += 40
        row("Posisi awal", f"({self.start_r}, {self.start_c})"); y += 40

        pygame.draw.line(self.screen, BORDER_CLR, (px+8,y),(self.win_w-8,y)); y += 12

        # Statistik
        pct = self.ev_idx / max(self.total_events, 1) * 100
        row("Event diputar",
            f"{self.ev_idx:,} / {self.total_events:,}",
            GOLD); y += 40

        # Progress bar event
        bw = PANEL_W - 32
        pygame.draw.rect(self.screen, BORDER_CLR, (x0,y,bw,8), border_radius=4)
        fill = int(bw * pct / 100)
        if fill > 0:
            pygame.draw.rect(self.screen, GOLD, (x0,y,fill,8), border_radius=4)
        y += 18

        row("Langkah maju",   f"{self.move_count:,}", GREEN); y += 40
        row("Langkah mundur", f"{self.back_count:,}", RED);   y += 40

        # Rasio backtrack
        ratio = self.back_count / max(self.move_count, 1)
        row("Rasio mundur/maju", f"{ratio:.1f}x", ORANGE); y += 40

        # Progress solusi
        cells_visited = sum(1 for r in range(self.n)
                            for c in range(self.n) if self.board[r][c] >= 0)
        row("Kotak dikunjungi",
            f"{cells_visited} / {self.n*self.n}",
            GREEN if cells_visited == self.n*self.n else WHITE); y += 40

        # Progress bar kotak
        pygame.draw.rect(self.screen, BORDER_CLR, (x0,y,bw,8), border_radius=4)
        fill2 = int(bw * cells_visited / (self.n * self.n))
        if fill2 > 0:
            pygame.draw.rect(self.screen, GREEN, (x0,y,fill2,8), border_radius=4)
        y += 18

        pygame.draw.line(self.screen, BORDER_CLR, (px+8,y),(self.win_w-8,y)); y += 12

        # Status
        if self.done:
            if self.solved:
                st, sc = "SOLUSI DITEMUKAN!", GREEN
            else:
                st, sc = "TIDAK ADA SOLUSI", RED
        elif self.paused:
            st, sc = "PAUSED", (200,180,100)
        else:
            st, sc = "BERJALAN...", (100,180,240)
        s = self.font_md.render(st, True, sc)
        self.screen.blit(s, (x0, y)); y += 28

        # Kecepatan
        t = self.font_sm.render(f"Delay: {self.delay*1000:.0f} ms", True, DIM_TEXT)
        self.screen.blit(t, (x0, y)); y += 20

        pygame.draw.line(self.screen, BORDER_CLR, (px+8,y),(self.win_w-8,y)); y += 12

        # Legenda warna
        def legend(color, label):
            nonlocal y
            pygame.draw.rect(self.screen, color, (x0,y+2,14,12), border_radius=2)
            t = self.font_sm.render(label, True, DIM_TEXT)
            self.screen.blit(t, (x0+20, y)); y += 18

        legend(VISIT_L,     "Kotak dikunjungi")
        legend(BACKTRACK_L, "Langkah mundur")
        legend(CURRENT_CLR, "Posisi kuda"); y += 6

        pygame.draw.line(self.screen, BORDER_CLR, (px+8,y),(self.win_w-8,y)); y += 10

        # Kontrol
        controls = [
            ("SPACE", "Pause / Lanjut"),
            ("S",     "Skip ke solusi"),
            ("R",     "Reset acak"),
            ("+/-",   "Kecepatan"),
            ("Q/ESC", "Keluar"),
        ]
        for key, desc in controls:
            ks = self.font_sm.render(key, True, GOLD)
            ds = self.font_sm.render(desc, True, DIM_TEXT)
            self.screen.blit(ks, (x0, y))
            self.screen.blit(ds, (x0+52, y))
            y += 17

    # ── Status bar bawah papan ────────────────────────────────
    def draw_statusbar(self):
        bar = pygame.Rect(0, self.board_w, self.board_w,
                          self.win_h - self.board_w)
        pygame.draw.rect(self.screen, PANEL_BG, bar)

        if self.ev_idx < len(self.events):
            ev = self.events[self.ev_idx - 1] if self.ev_idx > 0 else None
            if ev:
                if ev[0] == 'move':
                    msg = f"MAJU  ke ({ev[1]},{ev[2]})  langkah {ev[3]}"
                    color = GREEN
                else:
                    msg = f"MUNDUR dari ({ev[1]},{ev[2]})"
                    color = RED
            else:
                msg, color = "Mulai...", DIM_TEXT
        else:
            msg   = f"Selesai — {'Solusi ditemukan!' if self.solved else 'Tidak ada solusi'}"
            color = GREEN if self.solved else RED

        t = self.font_sm.render(msg, True, color)
        self.screen.blit(t, (8, self.board_w + 10))

    # ── Loop utama ────────────────────────────────────────────
    def run(self):
        last_step = time.time()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_q, pygame.K_ESCAPE):
                        pygame.quit(); sys.exit()

                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused

                    elif event.key == pygame.K_s:
                        # Skip langsung ke solusi final
                        self._apply_final()

                    elif event.key == pygame.K_r:
                        self.start_r = random.randint(0, self.n-1)
                        self.start_c = random.randint(0, self.n-1)
                        self._compute()

                    elif event.key in (pygame.K_PLUS, pygame.K_EQUALS,
                                       pygame.K_KP_PLUS):
                        self.delay = max(0.005, self.delay - 0.02)

                    elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        self.delay = min(2.0, self.delay + 0.02)

            # Auto-advance
            now = time.time()
            steps_per_frame = max(1, int(1 / max(self.delay, 0.001) / FPS))
            if not self.paused and not self.done:
                if now - last_step >= self.delay:
                    for _ in range(steps_per_frame):
                        if not self.done:
                            self._step()
                    last_step = now

            # Render
            self.screen.fill(BG)
            self.draw_board()
            self.draw_backtrack_flash()
            self.draw_trail()
            self.draw_knight()
            self.draw_panel()
            self.draw_statusbar()
            pygame.display.flip()
            self.clock.tick(FPS)


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]

    n       = int(args[0]) if len(args) >= 1 else 5
    start_r = int(args[1]) if len(args) >= 2 else 0
    start_c = int(args[2]) if len(args) >= 3 else 0

    if not (3 <= n <= 8):
        print("Ukuran papan harus antara 3–8.")
        print("(Backtracking murni sangat lambat untuk papan > 6×6)")
        sys.exit(1)

    if not (0 <= start_r < n and 0 <= start_c < n):
        print(f"Posisi awal harus dalam rentang 0–{n-1}.")
        sys.exit(1)

    if n >= 7:
        print(f"\n[PERINGATAN] Papan {n}×{n} dengan backtracking murni bisa memakan")
        print("waktu sangat lama (menit hingga jam). Lanjutkan? [y/N] ", end="")
        ans = input().strip().lower()
        if ans != 'y':
            sys.exit(0)

   
    viz = KnightTourViz(n, start_r, start_c)
    viz.run()


if __name__ == "__main__":
    main()