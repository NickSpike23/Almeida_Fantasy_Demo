"""
rafa_intro.py  –  Introducción visual novel de Rafa
Dependencias externas: opencv-python, numpy
    pip install opencv-python numpy
"""

import pygame
import sys
import os

# ── Rutas ────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
IMG_DIR   = os.path.join(BASE_DIR, "img")
MUSIC_DIR = os.path.join(BASE_DIR, "music")
VIDEO_DIR = os.path.join(BASE_DIR, "video")

# ── Constantes ───────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1280, 720
FPS            = 60
FADE_DURATION  = 2.5      # segundos del fade-in desde negro
TYPING_SPEED   = 38       # caracteres por segundo

# Paleta
BLACK      = (0,   0,   0)
DARK_BOX   = (10,  8,  28, 215)
BOX_BORDER = (180, 140, 255)
TEXT_COLOR = (230, 210, 255)
NAME_BG    = (35,  18,  70, 235)
NAME_COLOR = (255, 215,  80)
BLINK_COLOR = (200, 180, 255)

# Caja de texto
BOX_H      = 165
BOX_MARGIN = 22
BOX_X      = BOX_MARGIN
BOX_W      = SCREEN_W - BOX_MARGIN * 2
BOX_Y      = SCREEN_H - BOX_H - BOX_MARGIN
TEXT_PAD   = 20

NAME_BOX_W = 190
NAME_BOX_H = 44
NAME_BOX_X = BOX_X
NAME_BOX_Y = BOX_Y - NAME_BOX_H + 6

BORDER_RADIUS = 10

# Diálogos: (hablante, texto)
DIALOGUE = [
    ("Rafa", "*Bostezo*   ¿Ya es de mañana?"),
    ("Rafa", "Hoy es un buen día para no ir a la uni..."),
]


# ─────────────────────────────────────────────────────────────────────────────
#  Sonido de escritura generado con numpy (onda cuadrada 8-bit style)
# ─────────────────────────────────────────────────────────────────────────────
def _make_typing_sound(frequency: int = 880, duration: float = 0.022,
                       sample_rate: int = 44100) -> pygame.mixer.Sound | None:
    try:
        import numpy as np
        frames = int(sample_rate * duration)
        period = max(1, int(sample_rate / frequency))
        wave   = np.array(
            [3200 if (i % period) < (period // 2) else -3200 for i in range(frames)],
            dtype=np.int16
        )
        # La información de canales del mixer ya está inicializada;
        # pygame.sndarray.make_sound espera (N, 2) para estéreo.
        stereo = np.column_stack([wave, wave])
        snd    = pygame.sndarray.make_sound(stereo)
        snd.set_volume(0.25)
        return snd
    except Exception:
        return None          # sin numpy o fallo → sin sonido de tecleo


# ─────────────────────────────────────────────────────────────────────────────
#  Texto con word-wrap progresivo
# ─────────────────────────────────────────────────────────────────────────────
def _draw_wrapped(surface: pygame.Surface, full_text: str,
                  revealed: int, font: pygame.font.Font,
                  color: tuple, rect: pygame.Rect) -> bool:
    """Dibuja solo los primeros `revealed` caracteres con word-wrap.
    Devuelve True cuando el texto está completamente revelado."""
    partial = full_text[:revealed]
    words   = partial.split(' ')
    lines: list[str] = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        if font.size(test)[0] <= rect.width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)

    line_h = font.get_linesize()
    y      = rect.y
    for line in lines:
        surf = font.render(line, True, color)
        surface.blit(surf, (rect.x, y))
        y += line_h

    return revealed >= len(full_text)


# ─────────────────────────────────────────────────────────────────────────────
#  Reproducción de video con opencv-python
# ─────────────────────────────────────────────────────────────────────────────
def _play_video(screen: pygame.Surface, path: str,
                clock: pygame.time.Clock,
                audio_path: str | None = None) -> None:
    try:
        import cv2
    except ImportError:
        # Fallback: pantalla negra con mensaje
        screen.fill(BLACK)
        font = pygame.font.SysFont("Georgia", 32)
        msg  = font.render("(Instala opencv-python para ver el video)", True, (180, 140, 255))
        screen.blit(msg, msg.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2)))
        pygame.display.flip()
        pygame.time.wait(3000)
        return

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return

    video_fps   = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_delay = 1000 / video_fps          # ms por frame

    pygame.mixer.music.stop()
    if audio_path and os.path.isfile(audio_path):
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.set_volume(0.8)
        pygame.mixer.music.play()
    next_tick = pygame.time.get_ticks()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                cap.release()
                return

        ret, frame = cap.read()
        if not ret:
            break

        # BGR → RGB y ajustar al tamaño de pantalla
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (SCREEN_W, SCREEN_H))
        surf  = pygame.surfarray.make_surface(frame.transpose(1, 0, 2))
        screen.blit(surf, (0, 0))
        pygame.display.flip()

        # Control de velocidad
        next_tick += frame_delay
        wait = int(next_tick - pygame.time.get_ticks())
        if wait > 0:
            pygame.time.wait(wait)

    cap.release()
    pygame.mixer.music.stop()


# ─────────────────────────────────────────────────────────────────────────────
#  Función principal de la intro — llámala desde menu.py
# ─────────────────────────────────────────────────────────────────────────────
def run_rafa_intro(screen: pygame.Surface, clock: pygame.time.Clock) -> None:
    font_dialogue = pygame.font.SysFont("Georgia", 26)
    font_name     = pygame.font.SysFont("Georgia", 28, bold=True)
    font_hint     = pygame.font.SysFont("Georgia", 20)

    # ── Cargar fondo ─────────────────────────────────────────────────────────
    raw_bg = pygame.image.load(os.path.join(IMG_DIR, "morning.jpg")).convert()
    bw, bh = raw_bg.get_size()
    scale  = max(SCREEN_W / bw, SCREEN_H / bh)
    morning = pygame.transform.smoothscale(raw_bg, (int(bw * scale), int(bh * scale)))
    bg_x    = (SCREEN_W - morning.get_width())  // 2
    bg_y    = (SCREEN_H - morning.get_height()) // 2

    # ── Música ambient en bucle ───────────────────────────────────────────────
    pygame.mixer.music.load(os.path.join(MUSIC_DIR, "Ambient.mp3"))
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)

    # ── Sonido de escritura ───────────────────────────────────────────────────
    typing_snd = _make_typing_sound()

    # ── Superficies estáticas ─────────────────────────────────────────────────
    fade_surf = pygame.Surface((SCREEN_W, SCREEN_H))
    fade_surf.fill(BLACK)

    text_rect = pygame.Rect(
        BOX_X + TEXT_PAD,
        BOX_Y + TEXT_PAD,
        BOX_W  - TEXT_PAD * 2,
        BOX_H  - TEXT_PAD * 2
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Fase 1  –  Fade-in desde negro
    # ─────────────────────────────────────────────────────────────────────────
    fade_start = pygame.time.get_ticks()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

        elapsed = (pygame.time.get_ticks() - fade_start) / 1000.0
        screen.blit(morning, (bg_x, bg_y))
        alpha = max(0, int(255 * (1.0 - elapsed / FADE_DURATION)))
        fade_surf.set_alpha(alpha)
        screen.blit(fade_surf, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)

        if elapsed >= FADE_DURATION:
            break

    # ─────────────────────────────────────────────────────────────────────────
    # Fase 2  –  Diálogos tipo novela visual
    # ─────────────────────────────────────────────────────────────────────────
    dia_index       = 0
    revealed        = 0
    typing_done     = False
    type_start_ms   = pygame.time.get_ticks()
    last_sound_char = 0

    while dia_index < len(DIALOGUE):
        now                    = pygame.time.get_ticks()
        speaker, text          = DIALOGUE[dia_index]

        # ── Eventos ──────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            advance = (
                (event.type == pygame.KEYDOWN and
                 event.key in (pygame.K_RETURN, pygame.K_SPACE,
                               pygame.K_KP_ENTER, pygame.K_z))
                or
                (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
            )
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

            if advance:
                if typing_done:
                    # Pasar al siguiente diálogo
                    dia_index      += 1
                    revealed        = 0
                    typing_done     = False
                    type_start_ms   = pygame.time.get_ticks()
                    last_sound_char = 0
                else:
                    # Mostrar todo el texto de golpe
                    revealed    = len(text)
                    typing_done = True

        # ── Avanzar el tipeo ─────────────────────────────────────────────────
        if not typing_done:
            elapsed_ms  = now - type_start_ms
            new_revealed = int(elapsed_ms * TYPING_SPEED / 1000)
            if new_revealed > revealed:
                revealed = min(new_revealed, len(text))
                # Sonido por cada carácter no-espacio nuevo
                if typing_snd and revealed > last_sound_char:
                    ch = text[revealed - 1]
                    if ch not in (' ', '\n', '*'):
                        typing_snd.play()
                    last_sound_char = revealed
            if revealed >= len(text):
                typing_done = True

        # ── Dibujar ──────────────────────────────────────────────────────────
        screen.blit(morning, (bg_x, bg_y))

        # Text box
        box_surf = pygame.Surface((BOX_W, BOX_H), pygame.SRCALPHA)
        box_surf.fill(DARK_BOX)
        pygame.draw.rect(box_surf, BOX_BORDER,
                         pygame.Rect(0, 0, BOX_W, BOX_H),
                         width=2, border_radius=BORDER_RADIUS)
        screen.blit(box_surf, (BOX_X, BOX_Y))

        # Name box
        nm_surf = pygame.Surface((NAME_BOX_W, NAME_BOX_H), pygame.SRCALPHA)
        nm_surf.fill(NAME_BG)
        pygame.draw.rect(nm_surf, BOX_BORDER,
                         pygame.Rect(0, 0, NAME_BOX_W, NAME_BOX_H),
                         width=2, border_radius=BORDER_RADIUS)
        screen.blit(nm_surf, (NAME_BOX_X, NAME_BOX_Y))

        name_render = font_name.render(speaker, True, NAME_COLOR)
        screen.blit(name_render, (
            NAME_BOX_X + (NAME_BOX_W - name_render.get_width())  // 2,
            NAME_BOX_Y + (NAME_BOX_H - name_render.get_height()) // 2
        ))

        # Texto con tipeo progresivo
        _draw_wrapped(screen, text, revealed, font_dialogue, TEXT_COLOR, text_rect)

        # Indicador ▼ parpadeante cuando el diálogo está completo
        if typing_done and (now // 550) % 2 == 0:
            arrow = font_hint.render("▼  [Enter / Clic]", True, BLINK_COLOR)
            screen.blit(arrow, (
                BOX_X + BOX_W - arrow.get_width()  - 18,
                BOX_Y + BOX_H - arrow.get_height() - 10
            ))

        pygame.display.flip()
        clock.tick(FPS)

    # ─────────────────────────────────────────────────────────────────────────
    # Fase 3  –  Video de créditos
    # ─────────────────────────────────────────────────────────────────────────
    _play_video(
        screen,
        os.path.join(VIDEO_DIR, "Credits.mp4"),
        clock,
        audio_path=os.path.join(MUSIC_DIR, "Credits.mp3")
    )
    


# ─────────────────────────────────────────────────────────────────────────────
#  Punto de entrada independiente
# ─────────────────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Almeida Fantasy – Intro Rafa")
    clock  = pygame.time.Clock()

    run_rafa_intro(screen, clock)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
