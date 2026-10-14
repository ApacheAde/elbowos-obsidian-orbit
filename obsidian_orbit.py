#!/usr/bin/env python3
"""Obsidian Orbit — neon gravity-orbit arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv

if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/workspace/artifacts/OBSIDIAN_ORBIT_ElbowOS.mp4")
TITLE, HANDLE = "OBSIDIAN ORBIT", "x.com/ElbowOS"

# Neon palette
BG = (8, 4, 20)
HOLE = (20, 10, 40)
CYAN = (0, 255, 220)
MAGENTA = (255, 40, 160)
GOLD = (255, 210, 60)
WHITE = (240, 240, 255)
AMBER = (255, 160, 40)
TEAL = (0, 200, 180)

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.SysFont("monospace", 72, bold=True)
        self.font_md = pygame.font.SysFont("monospace", 42, bold=True)
        self.font_sm = pygame.font.SysFont("monospace", 32)
        self.reset()

    def reset(self):
        self.cx, self.cy = W // 2, H // 2 + 100
        self.r = 280.0
        self.theta = 0.0
        self.omega = 0.045
        self.score = 0
        self.stars = []
        self.debris = []
        self.trail = []
        self.t = 0
        self.spawn_timer = 0
        for _ in range(8):
            self.spawn_star()
        for _ in range(4):
            self.spawn_debris()

    def spawn_star(self):
        ang = random.uniform(0, math.tau)
        dist = random.uniform(180, 420)
        self.stars.append([ang, dist, random.choice([CYAN, GOLD, TEAL])])

    def spawn_debris(self):
        ang = random.uniform(0, math.tau)
        dist = random.uniform(200, 450)
        spd = random.uniform(-0.02, 0.02)
        self.debris.append([ang, dist, spd, MAGENTA])

    def update(self, thrust=0.0):
        self.t += 1
        self.omega += thrust * 0.0012
        self.omega = max(-0.12, min(0.12, self.omega))
        self.omega *= 0.998
        self.theta += self.omega
        px = self.cx + self.r * math.cos(self.theta)
        py = self.cy + self.r * math.sin(self.theta)
        self.trail.append((px, py))
        if len(self.trail) > 40:
            self.trail.pop(0)
        for s in self.stars[:]:
            s[0] += 0.008
            sx = self.cx + s[1] * math.cos(s[0])
            sy = self.cy + s[1] * math.sin(s[0])
            if math.hypot(sx - px, sy - py) < 36:
                self.score += 10
                self.stars.remove(s)
                self.spawn_star()
        for d in self.debris[:]:
            d[0] += d[2]
            dx = self.cx + d[1] * math.cos(d[0])
            dy = self.cy + d[1] * math.sin(d[0])
            if math.hypot(dx - px, dy - py) < 32:
                self.score = max(0, self.score - 5)
                self.debris.remove(d)
                self.spawn_debris()
        self.spawn_timer += 1
        if self.spawn_timer > 40 and len(self.stars) < 10:
            self.spawn_star()
            self.spawn_timer = 0
        if random.random() < 0.02 and len(self.debris) < 6:
            self.spawn_debris()

    def draw(self, surf):
        surf.fill(BG)
        pygame.draw.circle(surf, HOLE, (int(self.cx), int(self.cy)), 70)
        pygame.draw.circle(surf, MAGENTA, (int(self.cx), int(self.cy)), 70, 4)
        pygame.draw.circle(surf, (40, 20, 60), (int(self.cx), int(self.cy)), 40)
        pygame.draw.circle(surf, (30, 20, 50), (int(self.cx), int(self.cy)), int(self.r), 2)
        if len(self.trail) > 2:
            pygame.draw.lines(surf, CYAN, False, self.trail, 3)
        px = self.cx + self.r * math.cos(self.theta)
        py = self.cy + self.r * math.sin(self.theta)
        pygame.draw.circle(surf, GOLD, (int(px), int(py)), 18)
        pygame.draw.circle(surf, WHITE, (int(px), int(py)), 10)
        for s in self.stars:
            sx = self.cx + s[1] * math.cos(s[0])
            sy = self.cy + s[1] * math.sin(s[0])
            pygame.draw.circle(surf, s[2], (int(sx), int(sy)), 12)
            pygame.draw.circle(surf, WHITE, (int(sx), int(sy)), 5)
        for d in self.debris:
            dx = self.cx + d[1] * math.cos(d[0])
            dy = self.cy + d[1] * math.sin(d[0])
            pygame.draw.polygon(surf, d[3], [
                (dx, dy-14), (dx+12, dy+10), (dx-12, dy+10)
            ])
        title = self.font_lg.render(TITLE, True, GOLD)
        surf.blit(title, title.get_rect(center=(W//2, 120)))
        sc = self.font_md.render(f"SCORE {self.score}", True, CYAN)
        surf.blit(sc, sc.get_rect(center=(W//2, 200)))
        handle = self.font_sm.render(HANDLE, True, WHITE)
        surf.blit(handle, handle.get_rect(center=(W//2, H-80)))
        hint = self.font_sm.render("A/D or LEFT/RIGHT thrust", True, AMBER)
        surf.blit(hint, hint.get_rect(center=(W//2, H-140)))

    def play_interactive(self):
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
            keys = pygame.key.get_pressed()
            thrust = 0.0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                thrust = -1.0
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                thrust = 1.0
            self.update(thrust)
            self.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def record(self):
        frames = FPS * SECS
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS),
            "-i", "-", "-an", "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-movflags", "+faststart", OUT
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            for i in range(frames):
                thrust = 0.0
                if abs(self.omega) < 0.03:
                    thrust = 1.0 if self.t % 60 < 30 else -1.0
                elif self.omega > 0.08:
                    thrust = -1.0
                elif self.omega < -0.08:
                    thrust = 1.0
                self.update(thrust)
                self.draw(self.screen)
                frame = pygame.surfarray.array3d(self.screen)
                frame = frame.transpose([1, 0, 2])
                proc.stdin.write(frame.tobytes())
                if i % 30 == 0:
                    print(f"frame {i}/{frames}")
            proc.stdin.close()
            err = proc.stderr.read().decode("utf-8", "ignore")
            rc = proc.wait()
            if rc != 0:
                raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1200:]}")
            print("wrote", OUT)
        except Exception as e:
            proc.kill()
            raise e
        finally:
            pygame.quit()

def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()

if __name__ == "__main__":
    main()
