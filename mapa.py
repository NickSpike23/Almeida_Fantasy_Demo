"""
mapa.py - Pantalla de exploracion de Bmap (demo).

Exporta:
    run_bmap(screen, clock, character, spawn_pos=None)

Controles: WASD / flechas para mover al jugador.
           ESC para salir.
"""

import pygame
import sys
import os
from game_state import get_game_state

# ── Rutas ─────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
IMG_DIR   = os.path.join(BASE_DIR, "img")
MUSIC_DIR = os.path.join(BASE_DIR, "music")
VIDEO_DIR = os.path.join(BASE_DIR, "video")

# ── Constantes ────────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1280, 720
FPS          = 60
PLAYER_SPEED = 6
SPRITE_W     = 32
SPRITE_H     = 32   

# Nombre de imagen por personaje (clave en minúsculas)
_CHAR_IMAGE: dict[str, str] = {
    "alberto": "Alberto.jpg",
    "angel":   "Angel.jpg",
    "rafa":    "Rafa.jpg",
    "paco":    "Paco.jpg",
    "abraham": "Abraham.jpg",
}

# Posición inicial en el mapa por personaje (esquina superior-izquierda del sprite)
_CHAR_START: dict[str, tuple[int, int]] = {
    "angel":   (961,  1511),
    "alberto": (1155, 1213),
    "paco":    (1623, 1338),
    "abraham": (1488, 1205),
}

# Estado persistente de Bmap (se mantiene aunque el jugador salga y vuelva a entrar)
_max_bmap_defeated: bool = False
_zuazo_first_done:  bool = False   # primer diálogo con Zuazo completado
_door_d_visited:    bool = True   # jugador vio la puerta D cerrada (post 1er diálogo)
_zuazo_combat_done: bool = False   # combate con Zuazo completado
_door_d_visited2nd: bool = False   # jugador vio la puerta D cerrada por segunda vez

# ── Sonido de tipeo (beep 8-bit generado proceduralmente) ─────────────────────
_type_sound_cache: "pygame.mixer.Sound | None" = None

def _get_type_sound() -> "pygame.mixer.Sound | None":
    global _type_sound_cache
    if _type_sound_cache is not None:
        return _type_sound_cache
    try:
        import array as _arr
        freq, size, ch = pygame.mixer.get_init()
        tone_freq = 800          # Hz – tono 8-bit
        duration  = 0.035        # segundos por beep
        volume    = 0.12
        n         = int(freq * duration)
        period    = max(1, int(freq / tone_freq))
        amplitude = int((2 ** (abs(size) - 1) - 1) * volume)
        typecode  = 'h' if size < 0 else 'H'
        mono = _arr.array(typecode)
        for i in range(n):
            val = amplitude if (i % period) < period // 2 else -amplitude
            mono.append(val)
        if ch == 2:
            stereo = _arr.array(typecode)
            for s in mono:
                stereo.append(s)
                stereo.append(s)
            buf = stereo
        else:
            buf = mono
        _type_sound_cache = pygame.mixer.Sound(buffer=buf)
    except Exception:
        _type_sound_cache = None
    return _type_sound_cache


def _sync_legacy_state_cache(state) -> None:
    global _max_bmap_defeated, _zuazo_first_done, _door_d_visited
    global _zuazo_combat_done, _door_d_visited2nd

    _max_bmap_defeated = state.max_bmap_defeated
    _zuazo_first_done = state.zuazo_first_done
    _door_d_visited = state.door_d_visited
    _zuazo_combat_done = state.zuazo_combat_done
    _door_d_visited2nd = state.door_d_visited2nd


def _is_walkable_point(rx: int, ry: int, walkable_rects: list[pygame.Rect]) -> bool:
    cx = int(rx) + SPRITE_W // 2
    cy = int(ry) + SPRITE_H // 2
    return any(w.collidepoint(cx, cy) for w in walkable_rects)


def _find_nearest_walkable_position(seed_x: float, seed_y: float,
                                    walkable_rects: list[pygame.Rect],
                                    max_x: int, max_y: int,
                                    radius: int = 0,
                                    max_radius: int = 240) -> tuple[int, int]:
    candidate_x = max(0, min(max_x, int(seed_x)))
    candidate_y = max(0, min(max_y, int(seed_y)))

    if _is_walkable_point(candidate_x, candidate_y, walkable_rects):
        return candidate_x, candidate_y

    if radius >= max_radius:
        return candidate_x, candidate_y

    step = max(1, radius + 1)
    offsets = [
        (step, 0), (-step, 0), (0, step), (0, -step),
        (step, step), (-step, step), (step, -step), (-step, -step),
    ]
    for off_x, off_y in offsets:
        nx = max(0, min(max_x, candidate_x + off_x))
        ny = max(0, min(max_y, candidate_y + off_y))
        if _is_walkable_point(nx, ny, walkable_rects):
            return nx, ny

    return _find_nearest_walkable_position(
        candidate_x, candidate_y, walkable_rects, max_x, max_y, radius + step, max_radius
    )


# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
def run_bmap(screen: pygame.Surface,
             clock: pygame.time.Clock,
             character: str,
             spawn_pos: tuple[int, int] | None = None) -> tuple[int, int] | None:
    """Pantalla de exploración del mapa interior (Bmap.png).
    DEMO: Solo Bmap disponible. Las salidas muestran un mensaje."""

    # Zonas de salida de Bmap (DEMO: no llevan a map)
    BMAP_EXITS = [
        pygame.Rect(221,    0, 437 - 221,   97 -    0),
        pygame.Rect(219, 1201, 436 - 219, 1297 - 1201),
        pygame.Rect(597,  838, 648 - 597,  979 -  838),
    ]
    
    # Posiciones de rebote para las salidas (para evitar repetición del mensaje)
    EXIT_BOUNCE_POSITIONS = [
        (330, 150),      # Rebote para la salida superior
        (330, 1050),     # Rebote para la salida inferior
        (550, 900),      # Rebote para la salida derecha
    ]

    # Áreas caminables en Bmap (todo lo demás tiene colisión)
    BMAP_WALKABLE = [
        pygame.Rect(215,    0, 221, 1299),  # 215,1299 – 436,0
        pygame.Rect(436,  839, 463,  138),  # 436,839 – 899,977
        pygame.Rect(157,  851,  58,   53),  # 215,851 – 157,904
        pygame.Rect( 11,  852, 153,  101),  # 11,852 – 164,953
        pygame.Rect( 12,  733, 154,   92),  # 12,733 – 166,825
        pygame.Rect(166,  775,  57,   50),  # 166,825 – 223,775
        pygame.Rect( 61,  304, 533,   36),  # 61,340 – 594,304
        pygame.Rect( 61,  182, 157,  152),  # 61,182 – 218,334
        pygame.Rect( 61,   22, 154,  149),  # 61,22 – 215,171
        pygame.Rect( 61,  137, 531,   35),  # 61,172 – 592,137
        pygame.Rect(442,   23, 150,  159),  # 442,23 – 592,182
        pygame.Rect(442,  191, 150,  161),  # 442,191 – 592,352
    ]

    # ── Cargar mapa B ─────────────────────────────────────────────────────────
    bmap_path = os.path.join(IMG_DIR, "Bmap.png")
    if not os.path.isfile(bmap_path):
        return   # si el archivo aún no existe, volver sin crashear
    bmap_surf = pygame.image.load(bmap_path).convert()
    bmap_w, bmap_h = bmap_surf.get_size()
    state = get_game_state()

    # ── Música del Bmap ───────────────────────────────────────────────────────
    pygame.mixer.music.stop()
    pygame.mixer.music.fadeout(100)  # fade out rápido
    _map_music = os.path.join(MUSIC_DIR, "map.mp3")
    if os.path.isfile(_map_music):
        pygame.mixer.music.load(_map_music)
        pygame.mixer.music.set_volume(0.7)  # Volumen más alto para la demo
        pygame.mixer.music.play(-1)
    else:
        print(f"Advertencia: No se pudo cargar música del mapa en {_map_music}")

    # ── Sprite del jugador ────────────────────────────────────────────────────
    img_name = _CHAR_IMAGE.get(character.lower(), f"{character}.jpg")
    img_path = os.path.join(IMG_DIR, img_name)
    if os.path.isfile(img_path):
        raw    = pygame.image.load(img_path).convert()
        sprite = pygame.transform.smoothscale(raw, (SPRITE_W, SPRITE_H))
    else:
        sprite = pygame.Surface((SPRITE_W, SPRITE_H))
        sprite.fill((60, 120, 220))

    # ── Sprite de Max en Bmap ─────────────────────────────────────────────────
    MAX_MAP_X, MAX_MAP_Y = 66, 138
    max_img_path = os.path.join(IMG_DIR, "max.png")
    if os.path.isfile(max_img_path):
        max_raw    = pygame.image.load(max_img_path).convert_alpha()
        max_sprite = pygame.transform.smoothscale(max_raw, (32, 32))
    else:
        max_sprite = pygame.Surface((32, 32), pygame.SRCALPHA)
        max_sprite.fill((220, 50, 50, 200))
    max_rect = pygame.Rect(MAX_MAP_X, MAX_MAP_Y, 32, 32)
    max_defeated      = state.max_bmap_defeated
    zuazo_first_done  = state.zuazo_first_done
    zuazo_combat_done = state.zuazo_combat_done

    # ── Sprite de Zuazo en Bmap (aparece tras derrotar a Max) ─────────────────
    ZUAZO_MAP_X, ZUAZO_MAP_Y = 517, 145
    zuazo_img_path = os.path.join(IMG_DIR, "Zuazo.png")
    if os.path.isfile(zuazo_img_path):
        zuazo_raw    = pygame.image.load(zuazo_img_path).convert_alpha()
        zuazo_sprite = pygame.transform.smoothscale(zuazo_raw, (32, 32))
    else:
        zuazo_sprite = pygame.Surface((32, 32), pygame.SRCALPHA)
        zuazo_sprite.fill((50, 180, 50, 200))
    zuazo_rect = pygame.Rect(ZUAZO_MAP_X, ZUAZO_MAP_Y, 32, 32)

    # Solo Max y Zuazo aparecen en Bmap para la demo.

    # ── Fuentes para diálogo post-combate ─────────────────────────────────────
    font_dlg  = pygame.font.SysFont("Georgia", 26)
    font_name = pygame.font.SysFont("Georgia", 28, bold=True)

    # ── Posición inicial del jugador ──────────────────────────────────────────
    if spawn_pos is not None:
        px = float(spawn_pos[0])
        py = float(spawn_pos[1])
    else:
        px = float(bmap_w // 2 - SPRITE_W // 2)
        py = float(bmap_h // 2 - SPRITE_H // 2)

    px, py = _find_nearest_walkable_position(
        px, py, BMAP_WALKABLE, bmap_w - SPRITE_W, bmap_h - SPRITE_H
    )

    # ── Helper: mostrar una línea de diálogo encima de la escena ─────────────
    def show_line(speaker: str, text: str) -> None:
        """Bloquea hasta que el jugador pulsa Enter/clic."""
        BOX_H_  = 120
        BOX_M   = 22
        bx      = BOX_M
        bw      = SCREEN_W - BOX_M * 2
        by      = SCREEN_H - BOX_H_ - BOX_M
        NM_H    = 40
        WHITE_  = (240, 240, 245)
        BLINK_  = (160, 200, 255)

        _tw_shown = 0
        _tw_last  = pygame.time.get_ticks()
        _tw_delay = 35
        _type_snd = _get_type_sound()
        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if (ev.type == pygame.KEYDOWN and
                        ev.key in (pygame.K_RETURN, pygame.K_SPACE,
                                   pygame.K_KP_ENTER, pygame.K_z)) \
                        or (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1):
                    if _tw_shown < len(text):
                        _tw_shown = len(text)
                    else:
                        return

            # Actualizar tipeo
            now = pygame.time.get_ticks()
            if _tw_shown < len(text) and now - _tw_last >= _tw_delay:
                _tw_shown += 1
                _tw_last = now
                if _type_snd and text[_tw_shown - 1] != ' ':
                    _type_snd.play()

            # Fondo del mapa
            cam_x_ = max(0, min(bmap_w - SCREEN_W, int(px + SPRITE_W // 2 - SCREEN_W // 2)))
            cam_y_ = max(0, min(bmap_h - SCREEN_H, int(py + SPRITE_H // 2 - SCREEN_H // 2)))
            screen.fill((0, 0, 0))
            screen.blit(bmap_surf, (0, 0),
                        pygame.Rect(cam_x_, cam_y_, SCREEN_W, SCREEN_H))
            screen.blit(sprite, (int(px) - cam_x_, int(py) - cam_y_))

            # Caja de nombre
            nm_surf = pygame.Surface((200, NM_H), pygame.SRCALPHA)
            nm_surf.fill((10, 30, 60, 235))
            pygame.draw.rect(nm_surf, (80, 180, 255),
                             nm_surf.get_rect(), width=2, border_radius=8)
            screen.blit(nm_surf, (bx, by - NM_H + 6))
            nm_txt = font_name.render(speaker, True, (100, 200, 255))
            screen.blit(nm_txt, (bx + 10, by - NM_H + 6 + (NM_H - nm_txt.get_height()) // 2))

            # Caja de diálogo
            box = pygame.Surface((bw, BOX_H_), pygame.SRCALPHA)
            box.fill((8, 12, 20, 215))
            pygame.draw.rect(box, (80, 180, 255), box.get_rect(), width=2, border_radius=10)
            screen.blit(box, (bx, by))
            line = font_dlg.render(text[:_tw_shown], True, WHITE_)
            screen.blit(line, (bx + 20, by + 20))

            # Indicador ▼ (solo cuando el texto está completo)
            now = pygame.time.get_ticks()
            if _tw_shown >= len(text) and (now // 500) % 2 == 0:
                ind = font_dlg.render("▼", True, BLINK_)
                screen.blit(ind, (bx + bw - 30, by + BOX_H_ - ind.get_height() - 10))

            pygame.display.flip()
            clock.tick(FPS)

    # ── Helper: mostrar mensaje de zona no disponible ─────────────────────
    def show_unavailable_zone() -> None:
        """Muestra mensaje de zona disponible en versión completa."""
        BOX_H_  = 120
        BOX_M   = 22
        bx      = BOX_M
        bw      = SCREEN_W - BOX_M * 2
        by      = SCREEN_H - BOX_H_ - BOX_M
        NM_H    = 40
        WHITE_  = (240, 240, 245)
        BLINK_  = (200, 100, 100)
        message = "Zona disponible en la version completa ;)"

        _tw_shown = 0
        _tw_last  = pygame.time.get_ticks()
        _tw_delay = 35
        _type_snd = _get_type_sound()
        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if (ev.type == pygame.KEYDOWN and
                        ev.key in (pygame.K_RETURN, pygame.K_SPACE,
                                   pygame.K_KP_ENTER, pygame.K_z,
                                   pygame.K_ESCAPE)) \
                        or (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1):
                    if _tw_shown < len(message):
                        _tw_shown = len(message)
                    else:
                        return

            # Actualizar tipeo
            now = pygame.time.get_ticks()
            if _tw_shown < len(message) and now - _tw_last >= _tw_delay:
                _tw_shown += 1
                _tw_last = now
                if _type_snd and message[_tw_shown - 1] != ' ':
                    _type_snd.play()

            # Fondo del mapa
            cam_x_ = max(0, min(bmap_w - SCREEN_W, int(px + SPRITE_W // 2 - SCREEN_W // 2)))
            cam_y_ = max(0, min(bmap_h - SCREEN_H, int(py + SPRITE_H // 2 - SCREEN_H // 2)))
            screen.fill((0, 0, 0))
            screen.blit(bmap_surf, (0, 0),
                        pygame.Rect(cam_x_, cam_y_, SCREEN_W, SCREEN_H))
            screen.blit(sprite, (int(px) - cam_x_, int(py) - cam_y_))

            # Caja de nombre
            nm_surf = pygame.Surface((200, NM_H), pygame.SRCALPHA)
            nm_surf.fill((40, 20, 10, 235))
            pygame.draw.rect(nm_surf, (220, 160, 60),
                             nm_surf.get_rect(), width=2, border_radius=8)
            screen.blit(nm_surf, (bx, by - NM_H + 6))
            nm_txt = font_name.render("Sistema", True, (255, 200, 80))
            screen.blit(nm_txt, (bx + 10, by - NM_H + 6 + (NM_H - nm_txt.get_height()) // 2))

            # Caja de diálogo
            box = pygame.Surface((bw, BOX_H_), pygame.SRCALPHA)
            box.fill((20, 10, 5, 215))
            pygame.draw.rect(box, (220, 160, 60), box.get_rect(), width=2, border_radius=10)
            screen.blit(box, (bx, by))
            line = font_dlg.render(message[:_tw_shown], True, WHITE_)
            screen.blit(line, (bx + 20, by + 20))

            # Indicador ▼ parpadeante
            if _tw_shown >= len(message) and (pygame.time.get_ticks() // 500) % 2 == 0:
                ind = font_dlg.render("▼", True, BLINK_)
                screen.blit(ind, (bx + bw - 30, by + BOX_H_ - ind.get_height() - 10))

            pygame.display.flip()
            clock.tick(FPS)

    # ── Bucle principal de Bmap ───────────────────────────────────────────────
    while True:
        clock.tick(FPS)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return None   # volver al mapa principal sin posición específica

        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += PLAYER_SPEED
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= PLAYER_SPEED
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += PLAYER_SPEED
        if dx != 0 and dy != 0:
            dx = int(dx * 0.707)
            dy = int(dy * 0.707)

        # Movimiento con colisión por eje contra zonas caminables
        def _walkable(rx, ry):
            # Usa el centro del sprite para el chequeo (más fiable que rect-rect)
            cx = int(rx) + SPRITE_W // 2
            cy = int(ry) + SPRITE_H // 2
            return any(w.collidepoint(cx, cy) for w in BMAP_WALKABLE)

        clamped_px = max(0.0, min(float(bmap_w - SPRITE_W), px + dx))
        if _walkable(clamped_px, py):
            px = clamped_px
        clamped_py = max(0.0, min(float(bmap_h - SPRITE_H), py + dy))
        if _walkable(px, clamped_py):
            py = clamped_py

        # Comprobar salidas de Bmap (DEMO: muestran mensaje de zona no disponible)
        player_rect_exit = pygame.Rect(int(px), int(py), SPRITE_W, SPRITE_H)
        for i, exit_rect in enumerate(BMAP_EXITS):
            if player_rect_exit.colliderect(exit_rect):
                show_unavailable_zone()
                # Rebotar al jugador fuera del área de salida
                px, py = _find_nearest_walkable_position(
                    EXIT_BOUNCE_POSITIONS[i][0], EXIT_BOUNCE_POSITIONS[i][1],
                    BMAP_WALKABLE, bmap_w - SPRITE_W, bmap_h - SPRITE_H
                )

        # Colisión con Max → combate
        if not max_defeated:
            player_rect = pygame.Rect(int(px), int(py), SPRITE_W, SPRITE_H)
            if player_rect.colliderect(max_rect):
                from combate import run_combat_max
                run_combat_max(screen, clock, character)
                # Reactivar música del mapa al volver
                _map_music = os.path.join(MUSIC_DIR, "map.mp3")
                if os.path.isfile(_map_music):
                    pygame.mixer.music.load(_map_music)
                    pygame.mixer.music.set_volume(0.7)
                    pygame.mixer.music.play(-1)
                state.mark_max_bmap_defeated()
                _sync_legacy_state_cache(state)
                max_defeated = True  # Actualizar variable local
                show_line(character, "Que pedo con Max jajaja")
                show_line(character, "Cierto, Zuazo me pidió que fuera a verlo...")
                show_line(character, "Dijo que estaría en el laboratorio 3")

        # Colisión con Zuazo → diálogo / combate
        if max_defeated and not zuazo_combat_done:
            player_rect_z = pygame.Rect(int(px), int(py), SPRITE_W, SPRITE_H)
            if player_rect_z.colliderect(zuazo_rect):
                if not zuazo_first_done:
                    from combate import run_zuazo_first
                    run_zuazo_first(screen, clock, character)
                    _map_music = os.path.join(MUSIC_DIR, "map.mp3")
                    if os.path.isfile(_map_music):
                        pygame.mixer.music.load(_map_music)
                        pygame.mixer.music.set_volume(0.5)
                        pygame.mixer.music.play(-1)
                    state.mark_zuazo_first_done()
                    _sync_legacy_state_cache(state)
                    zuazo_first_done = True

                elif state.door_d_visited:
                    from combate import run_combat_zuazo
                    run_combat_zuazo(screen, clock, character)
                    _map_music = os.path.join(MUSIC_DIR, "map.mp3")
                    if os.path.isfile(_map_music):
                        pygame.mixer.music.load(_map_music)
                        pygame.mixer.music.set_volume(0.5)
                        pygame.mixer.music.play(-1)
                    state.mark_zuazo_combat_done()
                    _sync_legacy_state_cache(state)
                    zuazo_combat_done = True
                    show_line(character, "Andele, por andarme queriendo poner faltas")
                    show_line(character, "Aunque, ¿por qué está cerrado el D...?")
                    show_line(character, "Supongo que solo lo sabré si consigo el juego completo :P")
                    show_line(character, "Ponganos 10 profe jeje")

        cam_x = max(0, min(bmap_w - SCREEN_W, int(px + SPRITE_W // 2 - SCREEN_W // 2)))
        cam_y = max(0, min(bmap_h - SCREEN_H, int(py + SPRITE_H // 2 - SCREEN_H // 2)))

        screen.fill((0, 0, 0))
        screen.blit(bmap_surf, (0, 0),
                    pygame.Rect(cam_x, cam_y, SCREEN_W, SCREEN_H))

        if not max_defeated:
            screen.blit(max_sprite, (MAX_MAP_X - cam_x, MAX_MAP_Y - cam_y))

        if max_defeated and not zuazo_combat_done:
            screen.blit(zuazo_sprite, (ZUAZO_MAP_X - cam_x, ZUAZO_MAP_Y - cam_y))

        screen.blit(sprite, (int(px) - cam_x, int(py) - cam_y))

        pygame.display.flip()
        clock.tick(FPS)


def main() -> None:
    """Punto de entrada para ejecutar Bmap directamente."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Almeida Fantasy - Demo Bmap")
    clock = pygame.time.Clock()
    try:
        run_bmap(screen, clock, "angel", spawn_pos=(325, 237))
    finally:
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()

