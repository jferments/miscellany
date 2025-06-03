#!/usr/bin/env python3
# soroban_3d_interactive.py
# ─────────────────────────────────────────────────────────────────────────────
#  INTERACTIVE 3-D SOROBAN  (flat-colour version)
#  ---------------------------------------------------------------------------
#  ✔  Flat colours – NO lighting wash-out
#  ✔  Mouse-drag = free orbit (pitch & yaw)
#  ✔  Mouse-wheel = smooth zoom in / out
#  ✔  Automatic *autoscale* – wide abacus shrinks to stay on screen
#  ✔  Two addends + result shown top-right
#
#  Colour scheme
#  -------------
#      Frame ............ tan-brown  (0.82, 0.71, 0.55)
#      Rods ............. brown      (0.63, 0.45, 0.27)
#      Upper beads ...... red        (1.00, 0.15, 0.15)
#      Lower beads ...... blue       (0.15, 0.30, 1.00)
#
#  Run
#  ----
#      pip install pygame PyOpenGL PyOpenGL_accelerate
#      python soroban_3d_interactive.py
# ---------------------------------------------------------------------------

from __future__ import annotations
import sys, time, math
from dataclasses import dataclass
from typing import List

import pygame
from pygame.locals import (
    DOUBLEBUF, OPENGL,
    QUIT, KEYDOWN, K_ESCAPE,
    MOUSEBUTTONDOWN, MOUSEMOTION
)
from OpenGL.GL  import *
from OpenGL.GLU import *

# ╭───────────────────────── 1.  GEOMETRY CONSTANTS ─────────────────────────╮
ROD_SP   = 1.40     # X-distance between rods
BEAD_R   = 0.20     # bead radius
BAR_D    = 0.25     # frame-bar thickness (depth AND beam height)

# Y layout
SEP_Y    = 0.0
UP_DN_Y  = BAR_D/2 + BEAD_R*0.8
UP_UP_Y  = UP_DN_Y + 0.80
LOWER_DN0 = -0.85
ROW_H    = 0.60

TOP_Y    = UP_UP_Y + BEAD_R + 0.35
BOT_Y    = LOWER_DN0 - 3*ROW_H - 0.35
ROD_LEN  = (TOP_Y - BAR_D/2) - (BOT_Y + BAR_D/2)

# Z-ordering: draw bars first (z=0) so they overlap rods/beads (z<0)
Z_FRAME  =  0.00
Z_INNER  = -0.01

# ╭───────────────────────── 2.  COLOURS (RGB 0-1) ──────────────────────────╮
COL_FRAME = (0.82, 0.71, 0.55)   # tan-brown
COL_ROD   = (0.63, 0.45, 0.27)
COL_UPPER = (1.00, 0.15, 0.15)
COL_LOWER = (0.15, 0.30, 1.00)

# ╭───────────────────────── 3.  WINDOW & CAMERA ────────────────────────────╮
WIN_W, WIN_H = 1000, 750
FOV          = 45         # vertical FOV (deg)
BASE_DIST    = 18         # baseline camera distance (scroll modifies)

# ╭───────────────────────── 4.  ANIMATION CONSTANTS ────────────────────────╮
DT_BEAD, PAUSE_COL, PAUSE_CR = 0.20, 0.50, 0.50
LERP_F  = 0.20
FPS     = 60

# ╭───────────────────────── 5.  QUICK PRIMITIVES (flat) ────────────────────╮
def q_sphere(r: float):
    q = gluNewQuadric(); gluSphere(q, r, 24, 16); gluDeleteQuadric(q)

def q_cyl(r: float, h: float):
    q = gluNewQuadric(); gluCylinder(q, r, r, h, 20, 4); gluDeleteQuadric(q)

def q_box(w: float, h: float, d: float):
    x,y,z = w/2, h/2, d/2
    glBegin(GL_QUADS)
    # front/back
    glVertex3f(-x,-y, z); glVertex3f( x,-y, z); glVertex3f( x, y, z); glVertex3f(-x, y, z)
    glVertex3f(-x,-y,-z); glVertex3f(-x, y,-z); glVertex3f( x, y,-z); glVertex3f( x,-y,-z)
    # sides
    glVertex3f(-x,-y,-z); glVertex3f(-x,-y, z); glVertex3f(-x, y, z); glVertex3f(-x, y,-z)
    glVertex3f( x,-y,-z); glVertex3f( x, y,-z); glVertex3f( x, y, z); glVertex3f( x,-y, z)
    # top/bottom
    glVertex3f(-x, y,-z); glVertex3f(-x, y, z); glVertex3f( x, y, z); glVertex3f( x, y,-z)
    glVertex3f(-x,-y,-z); glVertex3f( x,-y,-z); glVertex3f( x,-y, z); glVertex3f(-x,-y, z)
    glEnd()

# ╭───────────────────────── 6.  DATA MODEL ────────────────────────────────╮
@dataclass
class Bead:
    col: int
    y: float
    tgt: float

class Soroban:
    """Pure data + OpenGL draw for one abacus."""
    def __init__(self, n:int, digits:List[int]):
        self.n  = n
        self.d  = digits[:]                        # working digits
        self.beads: List[Bead] = []
        # create bead objects
        for c in range(n):
            self.beads.append(Bead(c, UP_UP_Y, UP_UP_Y))     # upper
            for i in range(4):
                y = LOWER_DN0 - i*ROW_H
                self.beads.append(Bead(c, y, y))             # lower
        self._update_targets()

    def _update_targets(self):
        for c, val in enumerate(self.d):
            base = c*5
            self.beads[base].tgt = UP_DN_Y if val>=5 else UP_UP_Y
            k = val % 5
            for i in range(4):
                dn = LOWER_DN0 - i*ROW_H
                up = dn + ROW_H
                self.beads[base+1+i].tgt = up if i<k else dn

    def inc(self,col:int)->bool:
        self.d[col]+=1
        carry=False
        if self.d[col]==10:
            self.d[col]=0; carry=True
        self._update_targets(); return carry

    def animate(self):
        for b in self.beads:
            b.y += (b.tgt - b.y)*LERP_F

    # -------- drawing (flat colour) --------------------------------------
    def draw(self):
        half = (self.n-1)*ROD_SP/2 + BAR_D

        # frame
        glColor3fv(COL_FRAME)
        glPushMatrix(); glTranslatef(0,0,Z_FRAME)
        for s in (-1,1):
            glPushMatrix(); glTranslatef(s*half,(TOP_Y+BOT_Y)/2,0)
            q_box(BAR_D, TOP_Y-BOT_Y, BAR_D); glPopMatrix()
        for y in (TOP_Y, SEP_Y, BOT_Y):
            glPushMatrix(); glTranslatef(0,y,0)
            q_box(half*2, BAR_D, BAR_D); glPopMatrix()
        glPopMatrix()

        # rods
        glColor3fv(COL_ROD)
        for c in range(self.n):
            x=-((self.n-1)*ROD_SP)/2 + c*ROD_SP
            glPushMatrix(); glTranslatef(x, TOP_Y-BAR_D/2, Z_INNER)
            glRotatef(90,1,0,0); q_cyl(0.06, ROD_LEN); glPopMatrix()

        # beads
        for idx,b in enumerate(self.beads):
            glColor3fv(COL_UPPER if idx%5==0 else COL_LOWER)
            x=-((self.n-1)*ROD_SP)/2 + b.col*ROD_SP
            glPushMatrix(); glTranslatef(x,b.y,Z_INNER)
            q_sphere(BEAD_R); glPopMatrix()

# ╭───────────────────────── 7.  OPENGL CONTEXT ────────────────────────────╮
def init_gl():
    pygame.init()
    pygame.display.set_mode((WIN_W, WIN_H), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("3-D Soroban · interactive")

    # --- PROJECTION matrix ---------------------------------------
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOV, WIN_W / WIN_H, 0.1, 100.0)

    # --- MODELVIEW matrix (everything after this is “camera”) ----
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glEnable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)          # flat-colour path

# ╭───────────────────────── 8.  CAMERA CONTROL ────────────────────────────╮
class Camera:
    """Simple orbit camera controlled by mouse."""
    def __init__(self, base_dist:float):
        self.yaw   = 25      # degrees around Y
        self.pitch = -25     # degrees around X
        self.dist  = base_dist
        self.dragging = False
        self.last_mouse: tuple[int,int] | None = None

    def apply(self):
        """Apply transforms to the MODEL-VIEW matrix."""
        glLoadIdentity()
        glTranslatef(0,0,-self.dist)
        glRotatef(self.pitch, 1,0,0)
        glRotatef(self.yaw  , 0,1,0)

    # mouse handlers -------------------------------------------------------
    def handle_event(self, ev):
        if ev.type == MOUSEBUTTONDOWN:
            if ev.button == 1:
                self.dragging = True
                self.last_mouse = ev.pos
            elif ev.button == 4:                       # wheel up → zoom in
                self.dist = max(3, self.dist*0.9)
            elif ev.button == 5:                       # wheel down → out
                self.dist = self.dist*1.1
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            self.dragging = False
        elif ev.type == MOUSEMOTION and self.dragging:
            dx,dy = ev.rel
            self.yaw   += dx * 0.5
            self.pitch += dy * 0.5
            self.pitch = max(-89, min(89, self.pitch))

# ╭───────────────────────── 9.  AUTOSCALE HELPER ──────────────────────────╮
def compute_model_scale(n_cols:int) -> float:
    """
    Dynamically shrink / grow the entire abacus so that its width fits
    inside an arbitrary margin of the view frustum.

    We pick a *target width* (units at z=0) that comfortably fits inside
    the baseline camera view.  Any abacus longer than that is uniformly
    scaled down.
    """
    width_units = (n_cols-1)*ROD_SP + 2*BAR_D
    MAX_WIDTH   = 14.0               # heuristically fits at dist≈18, FOV45
    return 1.0 if width_units <= MAX_WIDTH else MAX_WIDTH / width_units

# ╭───────────────────────── 10.  MAIN ANIMATION LOOP ──────────────────────╮
def animate_add(a:int, b:int) -> None:
    total  = a + b
    columns= len(str(total))

    # soroban model
    model = Soroban(columns, list(map(int,str(a).zfill(columns))))
    addin = list(map(int,str(b).zfill(columns)))

    # build bead-wise queue
    queue: List[int|str] = []
    for col in range(columns-1,-1,-1):
        queue.extend([col]*addin[col])
        queue.append("pause")

    # OpenGL bookkeeping
    init_gl()
    cam  = Camera(BASE_DIST)
    scale_factor = compute_model_scale(columns)

    # Pygame helpers
    font = pygame.font.SysFont("monospace", 24, True)
    clock= pygame.time.Clock()
    last = time.perf_counter() - DT_BEAD

    running=True
    while running:
        # ── input ---------------------------------------------------------
        for ev in pygame.event.get():
            if ev.type == QUIT or (ev.type==KEYDOWN and ev.key==K_ESCAPE):
                running=False
            cam.handle_event(ev)

        # ── queue processing (bead increments) ---------------------------
        now = time.perf_counter()
        if queue and now-last >= DT_BEAD:
            op = queue.pop(0)
            if op == "pause":
                last = now + PAUSE_COL - DT_BEAD
            else:
                col:int = op
                if model.inc(col):
                    if col>0:
                        queue.insert(0,"pause"); queue.insert(0,col-1)
                    last = now + PAUSE_CR - DT_BEAD
                else:
                    last = now

        # ── render -------------------------------------------------------
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        cam.apply()
        glScalef(scale_factor, scale_factor, scale_factor)
        model.animate(); model.draw()

        # overlay (top-right)
        text = f"{a} + {b} = {total}"
        surf = font.render(text, True, (255,255,255))
        # align to top-right
        pos_x = WIN_W - surf.get_width() - 10
        pos_y = 10
        glWindowPos2d(pos_x, pos_y)
        glDrawPixels(surf.get_width(), surf.get_height(), GL_RGBA,
                     GL_UNSIGNED_BYTE, pygame.image.tostring(surf,"RGBA",True))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

# ╭───────────────────────── 11.  CLI ENTRY ────────────────────────────────╮
if __name__ == "__main__":
    try:
        x = int(input("Enter first  number: "))
        y = int(input("Enter second number: "))
        if x<0 or y<0: raise ValueError
    except ValueError:
        print("Please enter non-negative integers."); sys.exit(1)

    animate_add(x, y)
