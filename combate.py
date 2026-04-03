"""
combate.py  –  Sistema de combate por turnos.

Exporta:
    run_combat_max(screen, clock, character_name)  ← primera pelea (amañada)

Stats base de todos los personajes:
    HP: 100  |  Daño: 10-20 por golpe  |  Habilidad: se recarga al recibir 40 de daño
La primera pelea contra Max está amañada: Max se hace 100 de daño a sí mismo.
"""

import pygame
import sys
import os

# ── Rutas ─────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
IMG_DIR   = os.path.join(BASE_DIR, "img")
MUSIC_DIR = os.path.join(BASE_DIR, "music")
VIDEO_DIR = os.path.join(BASE_DIR, "video")

# ── Constantes ────────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1280, 720
FPS          = 60
TYPING_SPEED = 38

BLACK  = (  0,   0,   0)
WHITE  = (255, 255, 255)
GREEN  = ( 55, 200,  55)
YELLOW = (255, 215,   0)
RED    = (215,  45,  45)
HP_BG  = ( 18,   8,   8)

# Stats base
BASE_HP            = 100
DMG_MIN            = 10
DMG_MAX            = 20
ABILITY_CHARGE_DMG = 40    # daño recibido necesario para cargar la habilidad
_DRAIN_MS          = 300   # duración en ms del drenaje visual de HP (barra rápida)

# Vídeos por personaje (placeholders para los que aún no tienen animaciones propias)
_VIDEO_MAP = {
    "Alberto": {"idle": "AlbertoIdle.mp4",  "attack": "AlbertoAttack.mp4",  "special": "AlbertoSpecial.mp4"},
    "Angel":   {"idle": "AngelIdle.mp4",  "attack": "AngelAttack.mp4",  "special": "AngelSpecial.mp4"},
    "Abraham": {"idle": "AbrahamIdle.mp4",  "attack": "AbrahamAttack.mp4",  "special": "AbrahamSpecial.mp4"},
    "Paco":    {"idle": "PacoIdle.mp4",  "attack": "PacoAttack.mp4",  "special": "PacoSpecial.mp4"},
    "Rafa":    {"idle": "AlbertoIdle.mp4",  "attack": "AlbertoAttack.mp4",  "special": "AlbertoSpecial.mp4"},
    "Max":     {"idle": "MaxIdle.mp4",      "attack": "MaxAttack.mp4",      "special": None},
    "Zuazo":   {"idle": "ZuazoIdle.mp4",    "attack": "ZuazoAttack.mp4",     "special": "ZuazoSpecial.mp4"},
    "AbrahamSecundario":   {"idle": "AbramIdle.mp4",    "attack": None,     "special": "AbramSpecial.mp4"},
    "Gael":   {"idle": "GaelIdle.mp4",    "attack": None,     "special": "GaelSpecial.mp4"},
}


# ─── Layout del combate ───────────────────────────────────────────────────────
PANEL_W   = 540
PANEL_H   = 440
PLAYER_PX     = 40      # x-izquierda del panel del jugador (HP bar)
ENEMY_PX      = 700     # x-izquierda del panel del enemigo (HP bar)
PANEL_Y       = 56      # y del panel (debajo de las barras de HP)
PANEL_CENTER_X = (SCREEN_W - PANEL_W) // 2  # x para panel único centrado

NAME_Y    = 5      # y de la etiqueta del nombre
HP_BAR_Y  = 24     # y de la barra de HP
HP_BAR_H  = 26     # alto de la barra de HP

# ─── Caja de diálogo ─────────────────────────────────────────────────────────
DARK_BOX      = (8,  12,  20, 215)
TEXT_COLOR    = (240, 240, 245)
BLINK_COLOR   = (160, 200, 255)
BORDER_RADIUS = 10

BOX_H      = 165
BOX_MARGIN = 22
BOX_X      = BOX_MARGIN
BOX_W      = SCREEN_W - BOX_MARGIN * 2
BOX_Y      = SCREEN_H - BOX_H - BOX_MARGIN
TEXT_PAD   = 20
NM_BOX_W   = 220
NM_BOX_H   = 44
NM_BOX_X   = BOX_X
NM_BOX_Y   = BOX_Y - NM_BOX_H + 6

# Colores del hablante: (color_nombre, bg_nombre_RGBA, color_borde)
_DEFAULT_STYLE = ((100, 200, 255), (10, 30, 60, 235),  ( 80, 180, 255))
_SPEAKER_STYLES = {
    "Max":               ((255, 160,  60), (50,  20,  5, 235),  (200, 100,  40)),
    "Narrador":          ((180, 180, 255), (18,  18, 60, 235),  (130, 130, 210)),
    "Zuazo":             (( 80, 220,  90), ( 8,  40,  8, 235),  ( 50, 170,  60)),
    "AbrahamSecundario": ((255, 200,  60), (50,  30,  5, 235),  (220, 150,  40)),
    "Abraham":           ((255, 200,  60), (50,  30,  5, 235),  (220, 150,  40)),
}

# ── Diálogos de ataque y especial por personaje (usados en todos los combates) ───────────
ATK_LINES = {
    "Alberto": [
        "¡Golpe de Boxeo!",
        "¡Directo a tu panza!",
        "¡Toma ese gancho!",
    ],
    "Abraham": [
        "¡Aquí te van mis novelas japonesas de colección!",
        "¡Toma mis novelas visuales!",
        "¡Esto te lo traje directo de Japón!",
    ],
    "Paco": [
        "Paco empezó a hablar muy fuerte.",
        "Paco comenzó a confundir a su rival con tecnicismos.",
        "Paco explicó algo interminable sobre Android Studio.",
    ],
}

SPC_LINE = {
    "Alberto": ("¡Aquí te va mi moto!",   "¡Igualito a como le hice a la camioneta!"),
    "Angel":   ("¿Bueno? Sí, quiero un paquete de yakults ahora mismo...", None),
    "Abraham": ("¡Tragate estas cajas de Japón, pinche mid!",             None),
    "Paco":    ("¡Tragate mis muffins!",                                    None),
}


# ═══════════════════════════════════════════════════════════════════════════════
#   VideoPanel  –  stream de vídeo cv2 en un panel de combate
# ═══════════════════════════════════════════════════════════════════════════════

class VideoPanel:
    """
    Reproduce un archivo mp4 dentro de un área de tamaño fijo mediante opencv.
    Si cv2 no está disponible, muestra un rectángulo oscuro como fallback.
    loop=True  → vuelve al inicio al terminar.
    loop=False → se detiene en el último frame; is_done() devuelve True.
    """

    def __init__(self, path: str, width: int, height: int, loop: bool = True):
        self.width  = width
        self.height = height
        self.loop   = loop
        self._path  = path
        self._cap   = None
        self._cv2   = None
        self._surf  = None
        self._done  = False
        self._ms_per_frame = 1000.0 / 30.0
        self._last_t       = 0
        self._load(path)

    # ── Internos ──────────────────────────────────────────────────────────────

    def _load(self, path: str) -> None:
        if self._cap:
            self._cap.release()
        self._cap  = None
        self._done = False
        try:
            import cv2 as _cv2
            self._cv2 = _cv2
        except ImportError:
            return
        if not os.path.isfile(path):
            return
        self._cap = self._cv2.VideoCapture(path)
        fps = self._cap.get(self._cv2.CAP_PROP_FPS)
        if fps > 0:
            self._ms_per_frame = 1000.0 / fps
        self._read_frame()

    def _read_frame(self) -> None:
        if not self._cap or not self._cv2:
            return
        ret, frame = self._cap.read()
        if not ret:
            if self.loop:
                self._cap.set(self._cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self._cap.read()
                if not ret:
                    return
            else:
                self._done = True
                return
        frame = self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2RGB)
        frame = self._cv2.resize(frame, (self.width, self.height))
        self._surf = pygame.surfarray.make_surface(frame.transpose(1, 0, 2))
        self._last_t = pygame.time.get_ticks()

    # ── API pública ────────────────────────────────────────────────────────────

    def change(self, path: str, loop: bool = True) -> None:
        """Cambia el vídeo en reproducción."""
        self.loop  = loop
        self._path = path
        self._load(path)

    def update(self) -> None:
        """Avanza al siguiente frame cuando toca. Llamar una vez por tick del loop."""
        if self._done:
            return
        if pygame.time.get_ticks() - self._last_t >= self._ms_per_frame:
            self._read_frame()

    def draw(self, surface: pygame.Surface, x: int, y: int) -> None:
        if self._surf:
            surface.blit(self._surf, (x, y))
        else:
            pygame.draw.rect(surface, (15, 15, 25),
                             pygame.Rect(x, y, self.width, self.height))

    def is_done(self) -> bool:
        return self._done

    def get_progress(self) -> float:
        """Progreso 0.0-1.0 del vídeo (útil con loop=False)."""
        if self._done:
            return 1.0
        if not self._cap or not self._cv2:
            return 1.0
        total = self._cap.get(self._cv2.CAP_PROP_FRAME_COUNT)
        if total <= 0:
            return 1.0
        current = self._cap.get(self._cv2.CAP_PROP_POS_FRAMES)
        return min(1.0, current / total)

    def release(self) -> None:
        if self._cap:
            self._cap.release()
            self._cap = None


# ═══════════════════════════════════════════════════════════════════════════════
#   UTILIDADES
# ═══════════════════════════════════════════════════════════════════════════════

def _make_typing_sound() -> pygame.mixer.Sound | None:
    try:
        import numpy as np
        sr, dur = 44100, 0.022
        frames  = int(sr * dur)
        period  = max(1, int(sr / 820))
        wave    = np.array([3000 if (i % period) < period // 2 else -3000
                            for i in range(frames)], dtype=np.int16)
        stereo  = np.column_stack([wave, wave])
        snd     = pygame.sndarray.make_sound(stereo)
        snd.set_volume(0.22)
        return snd
    except Exception:
        return None


def _load_bg() -> pygame.Surface:
    surf = pygame.Surface((SCREEN_W, SCREEN_H))
    path = os.path.join(IMG_DIR, "Background.jpg")
    if os.path.isfile(path):
        raw    = pygame.image.load(path).convert()
        bw, bh = raw.get_size()
        scale  = max(SCREEN_W / bw, SCREEN_H / bh)
        scaled = pygame.transform.smoothscale(raw, (int(bw * scale), int(bh * scale)))
        surf.blit(scaled, ((SCREEN_W - scaled.get_width())  // 2,
                           (SCREEN_H - scaled.get_height()) // 2))
    else:
        surf.fill(BLACK)
    return surf


def _load_item_image(filename: str) -> pygame.Surface | None:
    path = os.path.join(IMG_DIR, filename)
    if not os.path.isfile(path):
        return None
    return pygame.image.load(path).convert()


def _hp_color(hp: float, max_hp: float) -> tuple:
    pct = hp / max_hp
    if pct > 0.50:
        return GREEN
    if pct > 0.25:
        return YELLOW
    return RED


def _draw_hp_bar(surface: pygame.Surface,
                 x: int, y: int, w: int,
                 hp: float, max_hp: float,
                 name: str,
                 font_nm: pygame.font.Font,
                 font_val: pygame.font.Font,
                 align_right: bool = False) -> None:
    # Nombre encima
    nm   = font_nm.render(name, True, WHITE)
    nm_x = (x + w - nm.get_width()) if align_right else x
    surface.blit(nm, (nm_x, NAME_Y))

    # Fondo de la barra
    bar_rect = pygame.Rect(x, y, w, HP_BAR_H)
    pygame.draw.rect(surface, HP_BG, bar_rect, border_radius=5)

    # Relleno proporcional (capeado al ancho de la barra para no desbordar)
    fill_w = int(w * min(1.0, max(0.0, hp / max_hp)))
    if fill_w > 0:
        pygame.draw.rect(surface, _hp_color(hp, max_hp),
                         pygame.Rect(x, y, fill_w, HP_BAR_H), border_radius=5)

    # Borde
    pygame.draw.rect(surface, (160, 160, 160), bar_rect, width=1, border_radius=5)

    # Valor HP
    val = font_val.render(f"{int(hp)} / {int(max_hp)}", True, WHITE)
    surface.blit(val, (x + (w - val.get_width()) // 2,
                       y + (HP_BAR_H - val.get_height()) // 2))


def _wrap_text_recursive(words: list[str], font: pygame.font.Font,
                         max_width: int, current: str = "",
                         lines: list[str] | None = None) -> list[str]:
    if lines is None:
        lines = []
    if not words:
        if current:
            lines.append(current)
        return lines

    word = words[0]
    rest = words[1:]
    candidate = (current + " " + word).strip()

    if font.size(candidate)[0] <= max_width or not current:
        return _wrap_text_recursive(rest, font, max_width, candidate, lines)

    lines.append(current)
    return _wrap_text_recursive(rest, font, max_width, word, lines)


def _draw_wrapped(surface: pygame.Surface, full_text: str, revealed: int,
                  font: pygame.font.Font, color: tuple,
                  rect: pygame.Rect) -> bool:
    partial = full_text[:revealed]
    words   = partial.split(" ")
    lines   = _wrap_text_recursive(words, font, rect.width)
    line_h = font.get_linesize()
    yp     = rect.y
    for line in lines:
        surface.blit(font.render(line, True, color), (rect.x, yp))
        yp += line_h
    return revealed >= len(full_text)


def _draw_dialogue_box(screen: pygame.Surface,
                       speaker: str, text: str,
                       revealed: int, typing_done: bool, now: int,
                       font_d: pygame.font.Font,
                       font_n: pygame.font.Font,
                       font_h: pygame.font.Font,
                       text_rect: pygame.Rect) -> None:
    style = _SPEAKER_STYLES.get(speaker, _DEFAULT_STYLE)
    name_color, name_bg, border_color = style

    box_surf = pygame.Surface((BOX_W, BOX_H), pygame.SRCALPHA)
    box_surf.fill(DARK_BOX)
    pygame.draw.rect(box_surf, border_color,
                     pygame.Rect(0, 0, BOX_W, BOX_H),
                     width=2, border_radius=BORDER_RADIUS)
    screen.blit(box_surf, (BOX_X, BOX_Y))

    if speaker:
        nm_surf = pygame.Surface((NM_BOX_W, NM_BOX_H), pygame.SRCALPHA)
        nm_surf.fill(name_bg)
        pygame.draw.rect(nm_surf, border_color,
                         pygame.Rect(0, 0, NM_BOX_W, NM_BOX_H),
                         width=2, border_radius=BORDER_RADIUS)
        screen.blit(nm_surf, (NM_BOX_X, NM_BOX_Y))
        nr = font_n.render(speaker, True, name_color)
        screen.blit(nr, (NM_BOX_X + (NM_BOX_W - nr.get_width())  // 2,
                         NM_BOX_Y + (NM_BOX_H - nr.get_height()) // 2))

    _draw_wrapped(screen, text, revealed, font_d, TEXT_COLOR, text_rect)

    if typing_done and (now // 550) % 2 == 0:
        arrow = font_h.render("▼  [Enter / Clic]", True, BLINK_COLOR)
        screen.blit(arrow, (BOX_X + BOX_W - arrow.get_width()  - 18,
                            BOX_Y + BOX_H - arrow.get_height() - 10))


# ═══════════════════════════════════════════════════════════════════════════════
#   ESCENA BASE DEL COMBATE
# ═══════════════════════════════════════════════════════════════════════════════

# Área disponible entre barras de HP y caja de diálogo
_VIDEO_AREA_Y      = HP_BAR_Y + HP_BAR_H + 4
_VIDEO_AREA_H      = BOX_Y - _VIDEO_AREA_Y - 6

def _draw_combat_base(screen: pygame.Surface,
                      bg: pygame.Surface,
                      player_panel: VideoPanel,
                      enemy_panel: VideoPanel,
                      player_hp: float, player_name: str,
                      enemy_hp: float,  enemy_name: str,
                      font_nm: pygame.font.Font,
                      font_val: pygame.font.Font,
                      item_surf: pygame.Surface | None = None,
                      active: str = "enemy") -> None:
    # Vídeo a pantalla completa
    if active == "player":
        player_panel.draw(screen, 0, 0)
    else:
        enemy_panel.draw(screen, 0, 0)

    # Barras de HP encima del vídeo
    _draw_hp_bar(screen, PLAYER_PX, HP_BAR_Y, PANEL_W,
                 player_hp, BASE_HP, player_name, font_nm, font_val,
                 align_right=False)
    _draw_hp_bar(screen, ENEMY_PX, HP_BAR_Y, PANEL_W,
                 enemy_hp,  BASE_HP, enemy_name,  font_nm, font_val,
                 align_right=True)

    # Recuadro con morado.png encima del vídeo (si aplica)
    if item_surf is not None:
        iw, ih  = item_surf.get_size()
        MAX_DIM = 320
        scale   = min(MAX_DIM / iw, MAX_DIM / ih)
        disp    = pygame.transform.smoothscale(
            item_surf, (int(iw * scale), int(ih * scale)))
        dw, dh  = disp.get_size()
        pad     = 20
        box_x   = (SCREEN_W - dw) // 2 - pad
        box_y   = _VIDEO_AREA_Y + (_VIDEO_AREA_H - dh) // 2 - pad
        dim     = pygame.Surface((dw + pad * 2, dh + pad * 2), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 170))
        pygame.draw.rect(dim, (220, 200, 80),
                         pygame.Rect(0, 0, dw + pad * 2, dh + pad * 2),
                         width=2, border_radius=10)
        screen.blit(dim, (box_x, box_y))
        screen.blit(disp, ((SCREEN_W - dw) // 2,
                           _VIDEO_AREA_Y + (_VIDEO_AREA_H - dh) // 2))


# ═══════════════════════════════════════════════════════════════════════════════
#   TRANSICIONES
# ═══════════════════════════════════════════════════════════════════════════════

def _flash_screen(screen: pygame.Surface, clock: pygame.time.Clock,
                  color: tuple, duration: float = 0.45) -> None:
    """Destello de color sobre la pantalla: aparece instantáneo y se desvanece."""
    snapshot = screen.copy()
    overlay  = pygame.Surface((SCREEN_W, SCREEN_H))
    overlay.fill(color)
    start = pygame.time.get_ticks()
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        elapsed  = (pygame.time.get_ticks() - start) / 1000.0
        alpha    = int(200 * max(0.0, 1.0 - elapsed / duration))
        screen.blit(snapshot, (0, 0))
        overlay.set_alpha(alpha)
        screen.blit(overlay, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)
        if elapsed >= duration:
            break
    screen.blit(snapshot, (0, 0))
    pygame.display.flip()


def _fade_to_black(screen: pygame.Surface, clock: pygame.time.Clock,
                   snapshot: pygame.Surface | None,
                   duration: float = 1.0) -> None:
    overlay = pygame.Surface((SCREEN_W, SCREEN_H))
    overlay.fill(BLACK)
    start = pygame.time.get_ticks()
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        elapsed = (pygame.time.get_ticks() - start) / 1000.0
        if snapshot:
            screen.blit(snapshot, (0, 0))
        else:
            screen.fill(BLACK)
        overlay.set_alpha(min(255, int(255 * elapsed / duration)))
        screen.blit(overlay, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)
        if elapsed >= duration:
            break
    screen.fill(BLACK)
    pygame.display.flip()


def _play_video_fullscreen(screen: pygame.Surface,
                           clock: pygame.time.Clock,
                           path: str) -> None:
    """Reproduce un vídeo mp4 a pantalla completa. Termina al acabar o con ESC."""
    try:
        import cv2
    except ImportError:
        screen.fill(BLACK)
        font = pygame.font.SysFont("Georgia", 32)
        msg  = font.render("(Instala opencv-python para ver el video)", True, (180, 140, 255))
        screen.blit(msg, msg.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2)))
        pygame.display.flip()
        pygame.time.wait(2500)
        return

    if not os.path.isfile(path):
        return

    cap       = cv2.VideoCapture(path)
    video_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    delay_ms  = 1000.0 / video_fps
    next_tick = float(pygame.time.get_ticks())

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                cap.release()
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                cap.release()
                return

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (SCREEN_W, SCREEN_H))
        screen.blit(pygame.surfarray.make_surface(frame.transpose(1, 0, 2)), (0, 0))
        pygame.display.flip()

        next_tick += delay_ms
        wait = int(next_tick - pygame.time.get_ticks())
        if wait > 0:
            pygame.time.wait(wait)

    cap.release()
    pygame.mixer.music.stop()


# ═══════════════════════════════════════════════════════════════════════════════
#   BUCLES DE DIÁLOGO SOBRE LA ESCENA DE COMBATE
# ═══════════════════════════════════════════════════════════════════════════════

def _run_dialogue(screen: pygame.Surface, clock: pygame.time.Clock,
                  bg: pygame.Surface,
                  player_panel: VideoPanel, enemy_panel: VideoPanel,
                  player_hp: float, player_name: str,
                  enemy_hp: float,  enemy_name: str,
                  font_d, font_n, font_h, font_nm, font_val,
                  text_rect: pygame.Rect,
                  speaker: str, text: str,
                  typing_snd: pygame.mixer.Sound | None = None,
                  item_surf: pygame.Surface | None = None,
                  auto_ms: int = 0,
                  typing_speed: int = TYPING_SPEED) -> None:
    """Muestra una línea de diálogo con efecto de tipeo sobre la escena de combate.
    auto_ms > 0: avanza automáticamente tras ese número de milisegundos.
    typing_speed: caracteres por segundo (mayor = más rápido)."""
    revealed    = 0
    typing_done = False
    call_start  = pygame.time.get_ticks()
    type_start  = call_start
    last_snd_ch = 0

    while True:
        now = pygame.time.get_ticks()
        advance = False
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return
            if (ev.type == pygame.KEYDOWN and
                    ev.key in (pygame.K_RETURN, pygame.K_SPACE,
                               pygame.K_KP_ENTER, pygame.K_z)) \
                    or (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1):
                advance = True

        # Auto-avance por tiempo
        if auto_ms > 0 and (now - call_start) >= auto_ms:
            advance = True

        if advance:
            if typing_done:
                break
            else:
                revealed    = len(text)
                typing_done = True

        if not typing_done:
            new_rev = int((now - type_start) * typing_speed / 1000)
            if new_rev > revealed:
                revealed = min(new_rev, len(text))
                if typing_snd and revealed > last_snd_ch:
                    if text[revealed - 1] not in (" ", "\n", "*"):
                        typing_snd.play()
                    last_snd_ch = revealed
            if revealed >= len(text):
                typing_done = True

        player_panel.update()
        enemy_panel.update()

        active = "player" if speaker == player_name else "enemy"
        _draw_combat_base(screen, bg, player_panel, enemy_panel,
                          player_hp, player_name, enemy_hp, enemy_name,
                          font_nm, font_val, item_surf, active)
        _draw_dialogue_box(screen, speaker, text, revealed, typing_done,
                           now, font_d, font_n, font_h, text_rect)
        pygame.display.flip()
        clock.tick(FPS)


def _run_attack_dialogue(screen: pygame.Surface, clock: pygame.time.Clock,
                         bg: pygame.Surface,
                         player_panel: VideoPanel, player_idle: str,
                         enemy_panel: VideoPanel,  enemy_idle: str,
                         attacker: str,
                         player_hp: float, player_name: str,
                         enemy_hp: float,  enemy_name: str,
                         font_d, font_n, font_h, font_nm, font_val,
                         text_rect: pygame.Rect,
                         speaker: str, text: str,
                         typing_snd: pygame.mixer.Sound | None = None,
                         drain_target: str | None = None,
                         drain_end_hp: float = 0.0,
                         attack_video: str | None = None,
                         auto_ms: int = 0) -> tuple[float, float]:
    """
    Reproduce la animación de ataque del `attacker` ("player"|"enemy").
    Si drain_target está definido, la HP del objetivo baja progresivamente
    hasta drain_end_hp mientras dura el vídeo de ataque.
    Se avanza automáticamente al terminar el vídeo Y el diálogo.
    attack_video: ruta explícita del vídeo (sobrescribe _VIDEO_MAP).
    Devuelve (new_player_hp, new_enemy_hp).
    """
    char_key    = player_name if attacker == "player" else enemy_name
    attack_path = (attack_video if attack_video else
                   os.path.join(VIDEO_DIR, _VIDEO_MAP.get(char_key, _VIDEO_MAP["Alberto"])["attack"]))
    idle_path   = player_idle if attacker == "player" else enemy_idle

    if attacker == "player":
        player_panel.change(attack_path, loop=True)
        acting = player_panel
    else:
        enemy_panel.change(attack_path, loop=True)
        acting = enemy_panel

    revealed        = 0
    typing_done     = False
    type_start      = pygame.time.get_ticks()
    last_snd_ch     = 0
    drain_start_val = ((enemy_hp if drain_target == "enemy" else player_hp)
                       if drain_target else 0.0)

    while True:
        now        = pygame.time.get_ticks()
        drain_done = drain_target is None or (now - type_start) >= _DRAIN_MS
        advance = False
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                acting.change(idle_path, loop=True)
                return (player_hp, enemy_hp)
            if (ev.type == pygame.KEYDOWN and
                    ev.key in (pygame.K_RETURN, pygame.K_SPACE,
                               pygame.K_KP_ENTER, pygame.K_z)) \
                    or (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1):
                advance = True

        if advance:
            if not typing_done:
                revealed    = len(text)
                typing_done = True
            elif drain_done:
                break   # segundo press (solo si el drenaje ya terminó): avanzar

        # Auto-avance por tiempo (si auto_ms > 0)
        if auto_ms > 0 and typing_done and drain_done and (now - type_start) >= auto_ms:
            break

        if False:  # sin auto-avance; requiere input del usuario
            break

        if not typing_done:
            new_rev = int((now - type_start) * TYPING_SPEED / 1000)
            if new_rev > revealed:
                revealed = min(new_rev, len(text))
                if typing_snd and revealed > last_snd_ch:
                    if text[revealed - 1] not in (" ", "\n", "*"):
                        typing_snd.play()
                    last_snd_ch = revealed
            if revealed >= len(text):
                typing_done = True

        player_panel.update()
        enemy_panel.update()

        # HP visual: drenaje rápido (_DRAIN_MS ms)
        if drain_target is not None:
            prog          = min(1.0, (now - type_start) / _DRAIN_MS)
            cur           = drain_start_val + (drain_end_hp - drain_start_val) * prog
            vis_player_hp = cur if drain_target == "player" else player_hp
            vis_enemy_hp  = cur if drain_target == "enemy"  else enemy_hp
        else:
            vis_player_hp = player_hp
            vis_enemy_hp  = enemy_hp

        _draw_combat_base(screen, bg, player_panel, enemy_panel,
                          vis_player_hp, player_name, vis_enemy_hp, enemy_name,
                          font_nm, font_val, active=attacker)
        ready = typing_done and drain_done
        _draw_dialogue_box(screen, speaker, text, revealed,
                           ready, now, font_d, font_n, font_h, text_rect)
        pygame.display.flip()
        clock.tick(FPS)

    acting.change(idle_path, loop=True)
    if drain_target == "enemy":
        return (player_hp, max(0.0, drain_end_hp))   # drain_end_hp puede ser >BASE_HP (curación)
    if drain_target == "player":
        return (max(0.0, drain_end_hp), enemy_hp)
    return (player_hp, enemy_hp)


# ═══════════════════════════════════════════════════════════════════════════════
#   ANIMACIÓN DE DRENAJE DE HP
# ═══════════════════════════════════════════════════════════════════════════════

def _drain_hp(screen: pygame.Surface, clock: pygame.time.Clock,
              bg: pygame.Surface,
              player_panel: VideoPanel, enemy_panel: VideoPanel,
              player_hp: float, player_name: str,
              enemy_hp: float,  enemy_name: str,
              font_nm, font_val,
              target: str, amount: float,
              duration: float = 1.8) -> tuple[float, float]:
    """
    Anima la barra de HP del `target` ("player"|"enemy") bajando `amount` puntos.
    Devuelve (new_player_hp, new_enemy_hp).
    """
    start_hp = player_hp if target == "player" else enemy_hp
    end_hp   = max(0.0, start_hp - amount)

    t_start = pygame.time.get_ticks()
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        elapsed  = (pygame.time.get_ticks() - t_start) / 1000.0
        progress = min(1.0, elapsed / duration)
        t        = 1.0 - (1.0 - progress) ** 2   # ease-out quadratic
        current  = start_hp + (end_hp - start_hp) * t

        p_hp = current if target == "player" else player_hp
        e_hp = current if target == "enemy"  else enemy_hp

        player_panel.update()
        enemy_panel.update()
        _draw_combat_base(screen, bg, player_panel, enemy_panel,
                          p_hp, player_name, e_hp, enemy_name,
                          font_nm, font_val, active=target)
        pygame.display.flip()
        clock.tick(FPS)
        if elapsed >= duration:
            break

    return (end_hp, enemy_hp) if target == "player" else (player_hp, end_hp)


# ═══════════════════════════════════════════════════════════════════════════════
#   MENÚ DE OPCIONES DEL JUGADOR (turno real)
# ═══════════════════════════════════════════════════════════════════════════════

def _run_choice_menu(screen: pygame.Surface, clock: pygame.time.Clock,
                     bg: pygame.Surface,
                     player_panel: VideoPanel, enemy_panel: VideoPanel,
                     player_hp: float, player_name: str,
                     enemy_hp: float,  enemy_name: str,
                     font_nm: pygame.font.Font,
                     font_val: pygame.font.Font,
                     special_charge: float) -> str:
    """
    Muestra el menú de turno del jugador con dos botones: Atacar y Especial.
    Devuelve "attack" o "special".
    special_charge [0-40]: daño acumulado desde la última especial.
    """
    font_btn  = pygame.font.SysFont("Georgia", 28, bold=True)
    font_hint = pygame.font.SysFont("Georgia", 20)

    BTN_W   = 300
    BTN_H   = 64
    gap     = 30
    total_w = BTN_W * 2 + gap
    BTN_Y   = SCREEN_H - BTN_H - 50
    bx1     = (SCREEN_W - total_w) // 2
    bx2     = bx1 + BTN_W + gap

    rect_atk = pygame.Rect(bx1, BTN_Y, BTN_W, BTN_H)
    rect_spc = pygame.Rect(bx2, BTN_Y, BTN_W, BTN_H)
    special_ready = special_charge >= 40.0

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                if rect_atk.collidepoint(mx, my):
                    return "attack"
                if rect_spc.collidepoint(mx, my) and special_ready:
                    return "special"
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_1, pygame.K_LEFT, pygame.K_a):
                    return "attack"
                if ev.key in (pygame.K_2, pygame.K_RIGHT, pygame.K_d) and special_ready:
                    return "special"

        player_panel.update()
        enemy_panel.update()
        _draw_combat_base(screen, bg, player_panel, enemy_panel,
                          player_hp, player_name, enemy_hp, enemy_name,
                          font_nm, font_val, active="player")

        mx_pos, my_pos = pygame.mouse.get_pos()

        # Fondo semitransparente del menú
        menu_bg = pygame.Surface((SCREEN_W, BTN_H + 80), pygame.SRCALPHA)
        menu_bg.fill((0, 0, 0, 160))
        screen.blit(menu_bg, (0, BTN_Y - 30))

        title = font_hint.render("Tu turno  —  elige una acción", True, (200, 200, 255))
        screen.blit(title, title.get_rect(centerx=SCREEN_W // 2, y=BTN_Y - 22))

        for rect, label, is_spc in [
            (rect_atk, "\u2694  Atacar  [1]", False),
            (rect_spc, f"\u2605  Especial  [2]  ({int(special_charge)}/40)", True),
        ]:
            disabled = is_spc and not special_ready
            hovered  = rect.collidepoint(mx_pos, my_pos) and not disabled
            c_bg  = (8,  8, 25, 215) if disabled else ((55, 30, 95, 235) if hovered else (15, 8, 40, 215))
            c_bdr = (60, 60, 80)     if disabled else ((255, 200, 80)    if hovered else (160, 120, 255))
            c_txt = (80, 80, 110)    if disabled else (WHITE             if hovered else (200, 180, 255))

            surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            surf.fill(c_bg)
            pygame.draw.rect(surf, c_bdr, surf.get_rect(), width=2, border_radius=10)
            screen.blit(surf, (rect.x, rect.y))
            txt = font_btn.render(label, True, c_txt)
            screen.blit(txt, (rect.x + (rect.w - txt.get_width())  // 2,
                               rect.y + (rect.h - txt.get_height()) // 2))

        pygame.display.flip()
        clock.tick(FPS)


# ═══════════════════════════════════════════════════════════════════════════════
#   PRIMERA PELEA: vs MAX (amañada)
# ═══════════════════════════════════════════════════════════════════════════════

def run_combat_max(screen: pygame.Surface,
                   clock: pygame.time.Clock,
                   character_name: str) -> None:
    """
    Pelea amañada contra Max.  Secuencia fija:
      1. Max habla  (x2)
      2. morado.png aparece  +  jugador dice "Aquí esta"
      3. Max ataca (MaxAttack.mp4) y grita su frase  [animación + diálogo simultáneos]
      4. Max pierde 100 HP  → animación de drenaje
      5. Fade a negro  →  win.mp4 a pantalla completa
    """
    # ── Assets ───────────────────────────────────────────────────────────────
    bg       = _load_bg()
    item_img = _load_item_image("morado.png")
    item2_img = _load_item_image("proto.jpg")

    p_vids = _VIDEO_MAP.get(character_name, _VIDEO_MAP["Alberto"])
    player_idle_path = os.path.join(VIDEO_DIR, p_vids["idle"])
    enemy_idle_path  = os.path.join(VIDEO_DIR, _VIDEO_MAP["Max"]["idle"])

    player_panel = VideoPanel(player_idle_path, SCREEN_W, SCREEN_H, loop=True)
    enemy_panel  = VideoPanel(enemy_idle_path,  SCREEN_W, SCREEN_H, loop=True)

    player_hp = float(BASE_HP)
    enemy_hp  = float(BASE_HP)

    # ── Música ───────────────────────────────────────────────────────────────
    pygame.mixer.music.stop()
    music_start_ms = 0
    mp = os.path.join(MUSIC_DIR, "max.mp3")
    if os.path.isfile(mp):
        pygame.mixer.music.load(mp)
        pygame.mixer.music.set_volume(0.55)
        pygame.mixer.music.play(-1)
        music_start_ms = pygame.time.get_ticks()

    # ── Fuentes ──────────────────────────────────────────────────────────────
    font_d   = pygame.font.SysFont("Georgia", 26)
    font_n   = pygame.font.SysFont("Georgia", 28, bold=True)
    font_h   = pygame.font.SysFont("Georgia", 20)
    font_nm  = pygame.font.SysFont("Georgia", 18, bold=True)
    font_val = pygame.font.SysFont("Georgia", 16, bold=True)
    typing_snd = _make_typing_sound()

    text_rect = pygame.Rect(
        BOX_X + TEXT_PAD, BOX_Y + TEXT_PAD,
        BOX_W - TEXT_PAD * 2, BOX_H - TEXT_PAD * 2,
    )

    # ── Helpers locales ───────────────────────────────────────────────────────
    def say(speaker: str, text: str, item=None, auto_ms: int = 0):
        _run_dialogue(screen, clock, bg, player_panel, enemy_panel,
                      player_hp, character_name, enemy_hp, "Max",
                      font_d, font_n, font_h, font_nm, font_val,
                      text_rect, speaker, text, typing_snd, item, auto_ms)

    def say_fast(speaker: str, text: str, auto_ms: int = 1500):
        """Diálogo a velocidad alta (efecto de hablar muy rápido)."""
        _run_dialogue(screen, clock, bg, player_panel, enemy_panel,
                      player_hp, character_name, enemy_hp, "Max",
                      font_d, font_n, font_h, font_nm, font_val,
                      text_rect, speaker, text, typing_snd, None, auto_ms,
                      typing_speed=350)

    def attack_drain(attacker: str, speaker: str, text: str,
                     drain_target: str | None = None, drain_end_hp: float = 0.0,
                     auto_ms: int = 0):
        nonlocal player_hp, enemy_hp
        player_hp, enemy_hp = _run_attack_dialogue(
            screen, clock, bg,
            player_panel, player_idle_path,
            enemy_panel,  enemy_idle_path,
            attacker,
            player_hp, character_name, enemy_hp, "Max",
            font_d, font_n, font_h, font_nm, font_val,
            text_rect, speaker, text, typing_snd,
            drain_target, drain_end_hp, auto_ms=auto_ms)

    # ════════════════════════════════════════════════════════════════
    #   SECUENCIA AMAÑADA – totalmente automática.
    #   win.mp4 arranca en el segundo 20 de max.mp3.
    # ════════════════════════════════════════════════════════════════
    WIN_TRIGGER_MS = 19_000

    # 1. Max habla  (auto ~2.5 s y ~3 s)
    if character_name == "Alberto":
        say("Max", "Otra vez llegando tarde, Alberto",           auto_ms=2000)
        say("Max", "Te iba a pedir que borraras el pizarron...", auto_ms=2500)
        say("Max", "Pero primero tengo que revisar tu diseño web", auto_ms=2500)
    elif character_name == "Angel":
        say("Max", "Buenos dias, Angel",           auto_ms=1500)
        say("Max", "¿Hoy no vino tu compañero el que prende el proyector? ", auto_ms=3000)
        say(character_name, "No, no vino", auto_ms=1000)
        say("Max", "Que mal, bueno, deja te reviso tu circuito", auto_ms=2500)
    elif character_name == "Paco":
        say("Max", "Paco, ¿nos podrías decir la definicion de Web Design en español?",           auto_ms=3000)
        say_fast(character_name, "Ah, claro… podríamos decir que es un concepto tecnológicamente adyacente a la organización de interfaces dentro del ecosistema digital,")
        say_fast(character_name, "similar a cómo Android Studio estructura proyectos mediante archivos y compilaciones;")
        say_fast(character_name, "en términos generales, una web es un conjunto de datos visibles en internet, como ocurre con plataformas de uso cotidiano tales como Google o YouTube,")
        say_fast(character_name, "que operan mediante servidores, usuarios y botones que, al ser presionados, ejecutan acciones computacionales dentro de sistemas interconectados.", auto_ms=1750)
    else:
        say("Max", f"Así que ya llegaste {character_name}.", auto_ms=2500)
        say("Max",  "Te estaba esperando para revisar tu diseño web", auto_ms=3000)

    # 2. Jugador muestra morado.png  (auto ~2 s)
    if character_name == "Angel":
        say(character_name, "Aquí esta", item=item2_img, auto_ms=2000)
        
        attack_drain("enemy", "Max", "¿¡CRUZADOS!? ¡CABLES CRUZADOS!",
                    drain_target="enemy", drain_end_hp=0.0, auto_ms=8000)
    elif character_name == "Paco":
        attack_drain("enemy", "Max", "¡PERO SOLO TE PREGUNTÉ LA DEFINICIÓN DE WEB DESIGN EN ESPAÑOL! !AAAAHHHHH¡",
                    drain_target="enemy", drain_end_hp=0.0, auto_ms=8000)
    else:    
        say(character_name, "Aquí esta", item=item_img, auto_ms=2000)

        # 3. Max ataca – la vida de Max baja de 100 a 0 al ritmo del vídeo
        attack_drain("enemy", "Max", "¿¡MORADO!? ¡ESO ES VIRUS!",
                    drain_target="enemy", drain_end_hp=0.0, auto_ms=8000)

    # 4. Mostrar MaxDerrota.png en pantalla completa (B&N) + texto hasta segundo 19
    derrota_path = os.path.join(IMG_DIR, "MaxDerrota.png")
    if os.path.isfile(derrota_path):
        _raw = pygame.image.load(derrota_path).convert()
        _raw = pygame.transform.smoothscale(_raw, (SCREEN_W, SCREEN_H))
        # Filtro blanco y negro vía surfarray
        import numpy as _np
        _arr = pygame.surfarray.pixels3d(_raw)
        _gray = (_arr[:, :, 0].astype(_np.uint32)
                 + _arr[:, :, 1].astype(_np.uint32)
                 + _arr[:, :, 2].astype(_np.uint32)) // 3
        _arr[:, :, 0] = _gray
        _arr[:, :, 1] = _gray
        _arr[:, :, 2] = _gray
        del _arr   # libera el lock del surface
        derrota_fs = _raw
    else:
        derrota_fs = None

    derrota_txt = font_h.render("Max se autodestruyo", True, YELLOW)
    txt_rect    = derrota_txt.get_rect(centerx=SCREEN_W // 2,
                                       centery=SCREEN_H * 3 // 4)

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        if music_start_ms > 0 and pygame.time.get_ticks() - music_start_ms >= WIN_TRIGGER_MS:
            break
        if music_start_ms == 0:   # sin música: no esperar
            break

        # Imagen B&N a pantalla completa (o negro si no existe el archivo)
        if derrota_fs:
            screen.blit(derrota_fs, (0, 0))
        else:
            screen.fill(BLACK)

        # Barras de HP encima
        _draw_hp_bar(screen, PLAYER_PX, HP_BAR_Y, PANEL_W,
                     player_hp, BASE_HP, character_name, font_nm, font_val,
                     align_right=False)
        _draw_hp_bar(screen, ENEMY_PX, HP_BAR_Y, PANEL_W,
                     enemy_hp,  BASE_HP, "Max", font_nm, font_val,
                     align_right=True)

        screen.blit(derrota_txt, txt_rect)
        pygame.display.flip()
        clock.tick(FPS)

    # 5. Fade + win.mp4 (la música sigue sonando hasta que termine el vídeo)
    snapshot = screen.copy()
    _fade_to_black(screen, clock, snapshot, duration=0.8)
    _play_video_fullscreen(screen, clock,
                           os.path.join(VIDEO_DIR, "win.mp4"))

    player_panel.release()
    enemy_panel.release()


# ═══════════════════════════════════════════════════════════════════════════════
#   ENCUENTRO 1 CON ZUAZO  (solo diálogo, misión al edificio D)
# ═══════════════════════════════════════════════════════════════════════════════

def run_zuazo_first(screen: pygame.Surface,
                    clock: pygame.time.Clock,
                    character_name: str) -> None:
    """Primer encuentro con Zuazo: diálogo puro, sin combate."""
    bg = _load_bg()

    p_vids = _VIDEO_MAP.get(character_name, _VIDEO_MAP["Alberto"])
    z_vids = _VIDEO_MAP["Zuazo"]
    player_idle_path = os.path.join(VIDEO_DIR, p_vids["idle"])
    zuazo_idle_path  = os.path.join(VIDEO_DIR, z_vids["idle"])

    player_panel = VideoPanel(player_idle_path, SCREEN_W, SCREEN_H, loop=True)
    enemy_panel  = VideoPanel(zuazo_idle_path,  SCREEN_W, SCREEN_H, loop=True)

    player_hp = float(BASE_HP)
    enemy_hp  = float(BASE_HP)

    pygame.mixer.music.stop()
    _zuazo_music = os.path.join(MUSIC_DIR, "zuazo.mp3")
    if os.path.isfile(_zuazo_music):
        pygame.mixer.music.load(_zuazo_music)
        pygame.mixer.music.set_volume(0.55)
        pygame.mixer.music.play(-1)

    font_d   = pygame.font.SysFont("Georgia", 26)
    font_n   = pygame.font.SysFont("Georgia", 28, bold=True)
    font_h   = pygame.font.SysFont("Georgia", 20)
    font_nm  = pygame.font.SysFont("Georgia", 18, bold=True)
    font_val = pygame.font.SysFont("Georgia", 16, bold=True)
    typing_snd = _make_typing_sound()

    text_rect = pygame.Rect(
        BOX_X + TEXT_PAD, BOX_Y + TEXT_PAD,
        BOX_W - TEXT_PAD * 2, BOX_H - TEXT_PAD * 2,
    )

    def say(speaker: str, text: str):
        _run_dialogue(screen, clock, bg, player_panel, enemy_panel,
                      player_hp, character_name, enemy_hp, "Zuazo",
                      font_d, font_n, font_h, font_nm, font_val,
                      text_rect, speaker, text, typing_snd)

    say(character_name, "Buenos dias profe, para que me ocupaba?")
    say("Zuazo", f"Ah, hola {character_name}")
    say("Zuazo", "Quer\u00eda que me trajeras unas cosas del D...")
    say(character_name, "Esta bien, deje voy")

    player_panel.release()
    enemy_panel.release()


# ═══════════════════════════════════════════════════════════════════════════════
#   COMBATE VS ZUAZO  (real, por turnos)
# ═══════════════════════════════════════════════════════════════════════════════

def run_combat_zuazo(screen: pygame.Surface,
                     clock: pygame.time.Clock,
                     character_name: str) -> None:
    """
    Segunda interacci\u00f3n con Zuazo: combate real por turnos.
      1. Di\u00e1logo de intro
      2. Zuazo ataca primero (Poner falta, 20-30 dmg)
      3. Bucle: turno jugador (Atacar / Especial  |  especial = 40 dmg, requiere 40 de carga)
    """
    import random

    bg = _load_bg()

    p_vids = _VIDEO_MAP.get(character_name, _VIDEO_MAP["Alberto"])
    z_vids = _VIDEO_MAP["Zuazo"]
    player_idle_path = os.path.join(VIDEO_DIR, p_vids["idle"])
    zuazo_idle_path  = os.path.join(VIDEO_DIR, z_vids["idle"])
    player_atk_path  = os.path.join(VIDEO_DIR, p_vids["attack"])
    _spc_file        = p_vids.get("special") or p_vids["attack"]
    player_spc_path  = os.path.join(VIDEO_DIR, _spc_file)
    zuazo_atk_path   = os.path.join(VIDEO_DIR, z_vids["attack"])
    _z_spc_file      = z_vids.get("special") or z_vids["attack"]
    zuazo_spc_path   = os.path.join(VIDEO_DIR, _z_spc_file)

    player_panel = VideoPanel(player_idle_path, SCREEN_W, SCREEN_H, loop=True)
    enemy_panel  = VideoPanel(zuazo_idle_path,  SCREEN_W, SCREEN_H, loop=True)

    player_hp            = float(BASE_HP)
    enemy_hp             = float(BASE_HP)
    special_charge       = 0.0   # carga especial del jugador (se llena al recibir daño)
    zuazo_special_charge = 0.0   # carga especial de Zuazo (se llena al recibir daño)
    angel_atk_count      = 0     # contador de ataques básicos para lógica de Angel
    abraham_atk_count    = 0     # contador de ataques de Abraham (combate amañado)

    pygame.mixer.music.stop()
    _zuazo_music = os.path.join(MUSIC_DIR, "zuazo.mp3")
    if os.path.isfile(_zuazo_music):
        pygame.mixer.music.load(_zuazo_music)
        pygame.mixer.music.set_volume(0.55)
        pygame.mixer.music.play(-1)

    font_d   = pygame.font.SysFont("Georgia", 26)
    font_n   = pygame.font.SysFont("Georgia", 28, bold=True)
    font_h   = pygame.font.SysFont("Georgia", 20)
    font_nm  = pygame.font.SysFont("Georgia", 18, bold=True)
    font_val = pygame.font.SysFont("Georgia", 16, bold=True)
    typing_snd = _make_typing_sound()

    text_rect = pygame.Rect(
        BOX_X + TEXT_PAD, BOX_Y + TEXT_PAD,
        BOX_W - TEXT_PAD * 2, BOX_H - TEXT_PAD * 2,
    )

    # ── Helpers ─────────────────────────────────────────────────────────────
    def say(speaker: str, text: str, auto_ms: int = 0):
        _run_dialogue(screen, clock, bg, player_panel, enemy_panel,
                      player_hp, character_name, enemy_hp, "Zuazo",
                      font_d, font_n, font_h, font_nm, font_val,
                      text_rect, speaker, text, typing_snd, None, auto_ms)

    def zuazo_attack(dmg_min: int, dmg_max: int, text: str):
        nonlocal player_hp, enemy_hp, special_charge
        dmg    = float(random.randint(dmg_min, dmg_max))
        end_hp = max(0.0, player_hp - dmg)
        player_hp, enemy_hp = _run_attack_dialogue(
            screen, clock, bg,
            player_panel, player_idle_path,
            enemy_panel,  zuazo_idle_path,
            "enemy",
            player_hp, character_name, enemy_hp, "Zuazo",
            font_d, font_n, font_h, font_nm, font_val,
            text_rect, "Zuazo", f"{text}  (-{int(dmg)} HP)", typing_snd,
            drain_target="player", drain_end_hp=end_hp,
            attack_video=zuazo_atk_path)
        special_charge = min(40.0, special_charge + dmg)
        if player_hp <= 0:
            _flash_screen(screen, clock, (220, 20, 20))

    _ALBERTO_ATK = ATK_LINES["Alberto"]
    _ABRAHAM_ATK = ATK_LINES["Abraham"]
    _PACO_ATK    = ATK_LINES["Paco"]

    def player_attack():
        nonlocal player_hp, enemy_hp, angel_atk_count, zuazo_special_charge, abraham_atk_count

        if character_name == "Angel":
            angel_atk_count += 1
            if angel_atk_count <= 2:
                # Primeros 2 ataques: curan 15 HP a Zuazo (no cargan la especial de Zuazo)
                heal   = 15.0
                end_hp = enemy_hp + heal
                player_hp, enemy_hp = _run_attack_dialogue(
                    screen, clock, bg,
                    player_panel, player_idle_path,
                    enemy_panel,  zuazo_idle_path,
                    "player",
                    player_hp, character_name, enemy_hp, "Zuazo",
                    font_d, font_n, font_h, font_nm, font_val,
                    text_rect, character_name, f"¡Toma tu Yakult!  (+{int(heal)} HP a Zuazo)", typing_snd,
                    drain_target="enemy", drain_end_hp=end_hp,
                    attack_video=player_atk_path)
            else:
                # 3er ataque en adelante: 25 de daño
                dmg    = 25.0
                end_hp = max(0.0, enemy_hp - dmg)
                player_hp, enemy_hp = _run_attack_dialogue(
                    screen, clock, bg,
                    player_panel, player_idle_path,
                    enemy_panel,  zuazo_idle_path,
                    "player",
                    player_hp, character_name, enemy_hp, "Zuazo",
                    font_d, font_n, font_h, font_nm, font_val,
                    text_rect, character_name, f"¡Toma tu Yakult!  (-{int(dmg)} HP)", typing_snd,
                    drain_target="enemy", drain_end_hp=end_hp,
                    attack_video=player_atk_path)
                zuazo_special_charge = min(40.0, zuazo_special_charge + dmg)
                if angel_atk_count == 3:
                    _run_dialogue(
                        screen, clock, bg,
                        player_panel, enemy_panel,
                        player_hp, character_name, enemy_hp, "Zuazo",
                        font_d, font_n, font_h, font_nm, font_val,
                        text_rect, "Zuazo", "Ay ya me dio chorrillo jeje", typing_snd)

        elif character_name == "Alberto":
            dmg    = float(random.randint(DMG_MIN, DMG_MAX))
            end_hp = max(0.0, enemy_hp - dmg)
            line   = random.choice(_ALBERTO_ATK) + f"  (-{int(dmg)} HP)"
            player_hp, enemy_hp = _run_attack_dialogue(
                screen, clock, bg,
                player_panel, player_idle_path,
                enemy_panel,  zuazo_idle_path,
                "player",
                player_hp, character_name, enemy_hp, "Zuazo",
                font_d, font_n, font_h, font_nm, font_val,
                text_rect, character_name, line, typing_snd,
                drain_target="enemy", drain_end_hp=end_hp,
                attack_video=player_atk_path)
            zuazo_special_charge = min(40.0, zuazo_special_charge + dmg)

        elif character_name == "Abraham":
            dmg    = float(random.randint(DMG_MIN, DMG_MAX))
            end_hp = max(0.0, enemy_hp - dmg)
            line   = random.choice(_ABRAHAM_ATK) + f"  (-{int(dmg)} HP)"
            player_hp, enemy_hp = _run_attack_dialogue(
                screen, clock, bg,
                player_panel, player_idle_path,
                enemy_panel,  zuazo_idle_path,
                "player",
                player_hp, character_name, enemy_hp, "Zuazo",
                font_d, font_n, font_h, font_nm, font_val,
                text_rect, character_name, line, typing_snd,
                drain_target="enemy", drain_end_hp=end_hp,
                attack_video=player_atk_path)
            zuazo_special_charge = min(40.0, zuazo_special_charge + dmg)
            abraham_atk_count += 1

        elif character_name == "Paco":
            dmg    = float(random.randint(DMG_MIN, DMG_MAX))
            end_hp = max(0.0, enemy_hp - dmg)
            line   = random.choice(_PACO_ATK) + f"  (-{int(dmg)} HP)"
            player_hp, enemy_hp = _run_attack_dialogue(
                screen, clock, bg,
                player_panel, player_idle_path,
                enemy_panel,  zuazo_idle_path,
                "player",
                player_hp, character_name, enemy_hp, "Zuazo",
                font_d, font_n, font_h, font_nm, font_val,
                text_rect, "Narrador", line, typing_snd,
                drain_target="enemy", drain_end_hp=end_hp,
                attack_video=player_atk_path)
            zuazo_special_charge = min(40.0, zuazo_special_charge + dmg)

        else:
            dmg    = float(random.randint(DMG_MIN, DMG_MAX))
            end_hp = max(0.0, enemy_hp - dmg)
            player_hp, enemy_hp = _run_attack_dialogue(
                screen, clock, bg,
                player_panel, player_idle_path,
                enemy_panel,  zuazo_idle_path,
                "player",
                player_hp, character_name, enemy_hp, "Zuazo",
                font_d, font_n, font_h, font_nm, font_val,
                text_rect, character_name, f"¡Ataque!  (-{int(dmg)} HP)", typing_snd,
                drain_target="enemy", drain_end_hp=end_hp,
                attack_video=player_atk_path)
            zuazo_special_charge = min(40.0, zuazo_special_charge + dmg)

    def player_special():
        nonlocal player_hp, enemy_hp, special_charge, zuazo_special_charge
        dmg       = 40.0
        end_hp    = max(0.0, enemy_hp - dmg)
        spc_main, spc_follow = SPC_LINE.get(character_name,
                                            (f"¡Habilidad especial!", None))
        player_hp, enemy_hp = _run_attack_dialogue(
            screen, clock, bg,
            player_panel, player_idle_path,
            enemy_panel,  zuazo_idle_path,
            "player",
            player_hp, character_name, enemy_hp, "Zuazo",
            font_d, font_n, font_h, font_nm, font_val,
            text_rect, character_name, f"{spc_main}  (-{int(dmg)} HP)",
            typing_snd,
            drain_target="enemy", drain_end_hp=end_hp,
            attack_video=player_spc_path)
        if spc_follow:
            say(character_name, spc_follow)
        special_charge       = 0.0
        zuazo_special_charge = min(40.0, zuazo_special_charge + dmg)

    def zuazo_special():
        nonlocal player_hp, enemy_hp, zuazo_special_charge
        dmg    = 10.0
        end_hp = max(0.0, player_hp - dmg)
        player_hp, enemy_hp = _run_attack_dialogue(
            screen, clock, bg,
            player_panel, player_idle_path,
            enemy_panel,  zuazo_idle_path,
            "enemy",
            player_hp, character_name, enemy_hp, "Zuazo",
            font_d, font_n, font_h, font_nm, font_val,
            text_rect, "Zuazo",
            f"¡TOMA MIS USBS CON WINDOWS 10 HOME!  (-{int(dmg)} HP)", typing_snd,
            drain_target="player", drain_end_hp=end_hp,
            attack_video=zuazo_spc_path)
        zuazo_special_charge = 0.0
        if player_hp <= 0:
            _flash_screen(screen, clock, (220, 20, 20))

    # ── Secuencia intro ──────────────────────────────────────────────────────
    say(character_name, "Esta cerrado el edificio D profe")
    say("Zuazo", "A caray, pero si yo acabo de salir de ahi")
    zuazo_attack(20, 30, "Por andar de gracioso le voy a poner falta")
    say(character_name, "Eh profe no me ponga falta")

    # ── Bucle de combate ─────────────────────────────────────────────────────
    _ZUAZO_PHRASES = [
        "\u00a1Te pongo otra falta!",
        "\u00a1A ver si as\u00ed aprendes!",
        "\u00a1Esto va al sistema escolar!",
        "\u00a1Revisa tus asistencias en Saeko!",
    ]
    turn = 0
    while player_hp > 0 and enemy_hp > 0:
        # Turno del jugador
        choice = _run_choice_menu(
            screen, clock, bg, player_panel, enemy_panel,
            player_hp, character_name, enemy_hp, "Zuazo",
            font_nm, font_val, special_charge)
        if choice == "special":
            player_special()
        else:
            player_attack()

        if enemy_hp <= 0:
            break

        # Combate amañado para Abraham: Zuazo gana tras 2+ ataques del jugador
        if character_name == "Abraham" and abraham_atk_count >= 2:
            player_hp, enemy_hp = _run_attack_dialogue(
                screen, clock, bg,
                player_panel, player_idle_path,
                enemy_panel,  zuazo_idle_path,
                "enemy",
                player_hp, character_name, enemy_hp, "Zuazo",
                font_d, font_n, font_h, font_nm, font_val,
                text_rect, "Zuazo", "Estas en rojos Jeshua", typing_snd,
                drain_target="player", drain_end_hp=0.0,
                attack_video=zuazo_atk_path)
            _flash_screen(screen, clock, (220, 20, 20))
            say(character_name, "P-Pero si yo no he faltado tanto...")
            break

        # Turno de Zuazo (normal)
        if zuazo_special_charge >= 40.0:
            zuazo_special()
        else:
            zuazo_attack(DMG_MIN, DMG_MAX, _ZUAZO_PHRASES[turn % len(_ZUAZO_PHRASES)])
        turn += 1

    # ── Resultado ────────────────────────────────────────────────────────────
    if enemy_hp <= 0:
        zuazo_defeat_path = os.path.join(VIDEO_DIR, "ZuazoDefeat.mp4")
        enemy_panel.change(zuazo_defeat_path, loop=True)
        say("Zuazo", "NOOOOOO")
        snapshot = screen.copy()
        _fade_to_black(screen, clock, snapshot, duration=0.8)
        _play_video_fullscreen(screen, clock, os.path.join(VIDEO_DIR, "win.mp4"))
    else:
        
        say("Zuazo", "Reprobado, a ver si estudias más")
        if character_name == "Abraham":
            # ── Gael interviene para salvar a Abraham ────────────────────────
            gael_vids      = _VIDEO_MAP["Gael"]
            gael_idle_path = os.path.join(VIDEO_DIR, gael_vids["idle"])
            gael_spc_file  = gael_vids.get("special") or gael_vids["idle"]
            gael_spc_path  = os.path.join(VIDEO_DIR, gael_spc_file)
            gael_panel     = VideoPanel(gael_idle_path, SCREEN_W, SCREEN_H, loop=True)
            gael_hp        = float(BASE_HP)

            def say_gael(speaker: str, text: str):
                _run_dialogue(screen, clock, bg,
                              gael_panel, enemy_panel,
                              gael_hp, "Gael", enemy_hp, "Zuazo",
                              font_d, font_n, font_h, font_nm, font_val,
                              text_rect, speaker, text, typing_snd)

            _flash_screen(screen, clock, (255, 255, 255))
            say_gael("Gael", "No te preocupes abraham")

            _, enemy_hp = _run_attack_dialogue(
                screen, clock, bg,
                gael_panel, gael_idle_path,
                enemy_panel, zuazo_idle_path,
                "player",
                gael_hp, "Gael", enemy_hp, "Zuazo",
                font_d, font_n, font_h, font_nm, font_val,
                text_rect, "Gael",
                "¡Aqui te van mis platinos, Zuazo!",
                typing_snd,
                drain_target="enemy", drain_end_hp=0.0,
                attack_video=gael_spc_path)

            zuazo_defeat_path = os.path.join(VIDEO_DIR, "ZuazoDefeat.mp4")
            enemy_panel.change(zuazo_defeat_path, loop=True)
            say_gael("Zuazo", "NOOOOO")
            gael_panel.release()
            snapshot = screen.copy()
            _fade_to_black(screen, clock, snapshot, duration=0.8)
            _play_video_fullscreen(screen, clock, os.path.join(VIDEO_DIR, "win.mp4"))

        elif character_name != "Abraham":
            # ── AbrahamSecundario interviene ──────────────────────────────────
            abram_vids      = _VIDEO_MAP["AbrahamSecundario"]
            abram_idle_path = os.path.join(VIDEO_DIR, abram_vids["idle"])
            abram_spc_file  = abram_vids.get("special") or abram_vids["idle"]
            abram_spc_path  = os.path.join(VIDEO_DIR, abram_spc_file)
            abram_panel     = VideoPanel(abram_idle_path, SCREEN_W, SCREEN_H, loop=True)
            abram_hp        = float(BASE_HP)

            def say_abram(speaker: str, text: str):
                _run_dialogue(screen, clock, bg,
                              abram_panel, enemy_panel,
                              abram_hp, "Abraham", enemy_hp, "Zuazo",
                              font_d, font_n, font_h, font_nm, font_val,
                              text_rect, speaker, text, typing_snd)

            _flash_screen(screen, clock, (255, 255, 255))
            say_abram("Abraham", f"¡Deje a {character_name}!")
            say_abram("Abraham", "¡Te voy a papear ahora mismo!")

            # Especial de AbrahamSecundario: drena a Zuazo a 0
            _, enemy_hp = _run_attack_dialogue(
                screen, clock, bg,
                abram_panel, abram_idle_path,
                enemy_panel, zuazo_idle_path,
                "player",
                abram_hp, "Abraham", enemy_hp, "Zuazo",
                font_d, font_n, font_h, font_nm, font_val,
                text_rect, "Abraham",
                "¿Ya vio? Yo sí sé usar cmd, pinche mediocre...",
                typing_snd,
                drain_target="enemy", drain_end_hp=0.0,
                attack_video=abram_spc_path)

            # Zuazo reproduce su animación de derrota y grita
            zuazo_defeat_path = os.path.join(VIDEO_DIR, "ZuazoDefeat.mp4")
            enemy_panel.change(zuazo_defeat_path, loop=True)
            _run_dialogue(screen, clock, bg,
                          abram_panel, enemy_panel,
                          abram_hp, "Abraham", enemy_hp, "Zuazo",
                          font_d, font_n, font_h, font_nm, font_val,
                          text_rect, "Zuazo", "NOOOOOOO", typing_snd)
            abram_panel.release()
            snapshot = screen.copy()
            _fade_to_black(screen, clock, snapshot, duration=0.8)
            _play_video_fullscreen(screen, clock, os.path.join(VIDEO_DIR, "win.mp4"))

    player_panel.release()
    enemy_panel.release()

# ═══════════════════════════════════════════════════════════════════════════════
#   PUNTO DE ENTRADA INDEPENDIENTE (para probar directamente)
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Almeida Fantasy – Combate vs Max")
    clock  = pygame.time.Clock()
    run_combat_max(screen, clock, "Angel")
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
