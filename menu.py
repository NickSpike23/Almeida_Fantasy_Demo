import pygame
import sys
import os

# ── Rutas ────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
IMG_DIR   = os.path.join(BASE_DIR, "img")
MUSIC_DIR = os.path.join(BASE_DIR, "music")
# Asegurar que el propio directorio esté en sys.path para imports locales
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Importar módulos locales con validación
try:
    import rafa_intro
except ImportError:
    print("Advertencia: rafa_intro.py no encontrado")
    rafa_intro = None

try:
    import mapa
except ImportError:
    print("Advertencia: mapa.py no encontrado")
    mapa = None
# ── Constantes ───────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60

# Paleta RPG
COLOR_BTN_NORMAL    = (20,  12,  40)
COLOR_BTN_HOVER     = (60,  30, 100)
COLOR_BTN_DISABLED  = (30,  20,  55)
COLOR_BTN_BORDER    = (180, 140, 255)
COLOR_TEXT          = (230, 210, 255)
COLOR_TEXT_HOVER    = (255, 255, 255)
COLOR_TEXT_DISABLED = (120, 100, 160)
COLOR_OVERLAY       = (0,   0,   0,  140)

# Paleta de tarjetas de personaje
COLOR_CARD_NORMAL   = (15,   8,  35, 210)
COLOR_CARD_HOVER    = (55,  28,  95, 230)
COLOR_CARD_SELECTED = (90,  50, 170, 245)
COLOR_CARD_BORDER_SEL = (255, 215,  80)  # dorado al seleccionar

FONT_SIZE_BTN = 36
BTN_W, BTN_H  = 220, 58
BTN_MARGIN    = 18
BTN_PAD_X     = 60
BTN_PAD_Y     = 60
BORDER_RADIUS = 10

# Dimensiones de las tarjetas de personaje
CARD_W   = 190
CARD_H   = 290
CARD_GAP = 14
IMG_W    = 160
IMG_H    = 205

# Lista de personajes en orden
CHARACTERS = [
    {"name": "Angel",   "img": "Angel.jpg"},
    {"name": "Abraham", "img": "Abraham.jpg"},
    {"name": "Alberto", "img": "Alberto.jpg"},
    {"name": "Paco",    "img": "Paco.jpg"},
    {"name": "Rafa",    "img": "Rafa.jpg"},
]


# Estados del juego
STATE_MENU   = "menu"
STATE_SELECT = "select"
STATE_GAME   = "game"


# ─────────────────────────────────────────────────────────────────────────────
class Button:
    def __init__(self, x, y, w, h, text, font, enabled=True):
        self.rect    = pygame.Rect(x, y, w, h) # Rectángulo del botón
        self.text    = text # Texto a mostrar
        self.font    = font # Fuente para renderizar el texto
        self.hovered = False # el mouse está sobre el botón
        self.focused = False   # foco por teclado
        self.enabled = enabled # el botón está activo (clickeable) o no

    def draw(self, surface): # Dibuja el botón con estilos según su estado
        active = self.hovered or self.focused # el botón está activo por hover o foco de teclado
        if not self.enabled: # el botón está deshabilitado
            color_bg  = COLOR_BTN_DISABLED # fondo más oscuro
            color_txt = COLOR_TEXT_DISABLED # texto más apagado
            border_c  = (80, 60, 120) # borde más oscuro
        elif active: # el botón está activo por hover o foco de teclado
            color_bg  = COLOR_BTN_HOVER # fondo más claro
            color_txt = COLOR_TEXT_HOVER # texto más brillante
            border_c  = COLOR_BTN_BORDER # borde normal
        else: # estado normal
            color_bg  = COLOR_BTN_NORMAL # fondo normal
            color_txt = COLOR_TEXT # texto normal
            border_c  = COLOR_BTN_BORDER # borde normal

        shadow_rect = self.rect.move(4, 4) # sombra desplazada hacia abajo y derecha
        pygame.draw.rect(surface, (0, 0, 0), shadow_rect, border_radius=BORDER_RADIUS) # sombra negra
        pygame.draw.rect(surface, color_bg,  self.rect,   border_radius=BORDER_RADIUS) # fondo del botón
        pygame.draw.rect(surface, border_c,  self.rect,   width=2, border_radius=BORDER_RADIUS) # borde del botón

        # Anillo blanco extra cuando el foco viene del teclado
        if self.focused and self.enabled:
            focus_rect = self.rect.inflate(6, 6)
            pygame.draw.rect(surface, (255, 255, 255), focus_rect,
                             width=2, border_radius=BORDER_RADIUS + 3)

        text_surf = self.font.render(self.text, True, color_txt)
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

    def update(self, mouse_pos):
        self.hovered = self.enabled and self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event):
        return (self.enabled
                and event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))


# ─────────────────────────────────────────────────────────────────────────────
class CharacterCard:
    def __init__(self, x, y, name, image, font):
        self.rect     = pygame.Rect(x, y, CARD_W, CARD_H)
        self.name     = name
        self.image    = image          # Surface ya escalada a IMG_W × IMG_H
        self.font     = font
        self.hovered  = False
        self.focused  = False   # foco por teclado
        self.selected = False

        # Rectángulo de la imagen: centrado horizontalmente, con margen superior
        self.img_rect = pygame.Rect(
            x + (CARD_W - IMG_W) // 2,
            y + 14,
            IMG_W, IMG_H
        )

    def draw_focus_ring(self, surface):
        """Anillo blanco exterior para indicar foco de teclado."""
        ring = self.rect.inflate(8, 8)
        pygame.draw.rect(surface, (255, 255, 255), ring, width=2, border_radius=BORDER_RADIUS + 4)

    def draw(self, surface):
        active = self.hovered or self.focused
        # ── Fondo de la tarjeta (semi-transparente) ──────────────────────────
        if self.selected:
            bg_color = COLOR_CARD_SELECTED
            border_c = COLOR_CARD_BORDER_SEL
            border_w = 3
        elif active:
            bg_color = COLOR_CARD_HOVER
            border_c = COLOR_BTN_BORDER
            border_w = 2
        else:
            bg_color = COLOR_CARD_NORMAL
            border_c = COLOR_BTN_BORDER
            border_w = 1

        card_surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        card_surf.fill(bg_color)
        pygame.draw.rect(card_surf, border_c,
                         pygame.Rect(0, 0, CARD_W, CARD_H),
                         width=border_w, border_radius=BORDER_RADIUS)
        surface.blit(card_surf, self.rect.topleft)

        # ── Imagen del personaje ─────────────────────────────────────────────
        surface.blit(self.image, self.img_rect.topleft)

        # ── Nombre ──────────────────────────────────────────────────────────
        name_color = (COLOR_CARD_BORDER_SEL if self.selected
                      else (COLOR_TEXT_HOVER if active else COLOR_TEXT))
        name_surf = self.font.render(self.name, True, name_color)
        nx = self.rect.x + (CARD_W - name_surf.get_width()) // 2
        ny = self.img_rect.bottom + 10
        surface.blit(name_surf, (nx, ny))

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))

    def activate(self):
        """Simula un clic por teclado."""
        return True


# ─────────────────────────────────────────────────────────────────────────────
def draw_background(surface, bg, screen_w, screen_h):
    """Escala el fondo manteniendo aspecto y lo centra."""
    bg_w, bg_h = bg.get_size()
    scale  = max(screen_w / bg_w, screen_h / bg_h)
    new_w  = int(bg_w * scale)
    new_h  = int(bg_h * scale)
    scaled = pygame.transform.smoothscale(bg, (new_w, new_h))
    surface.blit(scaled, ((screen_w - new_w) // 2, (screen_h - new_h) // 2))


def load_character_images():
    images = []
    for ch in CHARACTERS:
        path = os.path.join(IMG_DIR, ch["img"])
        try:
            img = pygame.image.load(path).convert()
            img = pygame.transform.smoothscale(img, (IMG_W, IMG_H))
        except Exception:
            img = pygame.Surface((IMG_W, IMG_H))
            img.fill((80, 60, 120))
        images.append(img)
    return images


def build_character_cards(images, font):
    n       = len(CHARACTERS)
    total_w = n * CARD_W + (n - 1) * CARD_GAP
    start_x = (SCREEN_W - total_w) // 2

    # Zona disponible: debajo del título (~110 px) y encima de los botones (~590 px)
    available_h = 590 - 110
    start_y     = 110 + (available_h - CARD_H) // 2

    cards = []
    for i, (ch, img) in enumerate(zip(CHARACTERS, images)):
        x = start_x + i * (CARD_W + CARD_GAP)
        cards.append(CharacterCard(x, start_y, ch["name"], img, font))
    return cards


# ─────────────────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Almeida Fantasy – La Caída de Javier")
    clock  = pygame.time.Clock()

    # ── Assets ───────────────────────────────────────────────────────────────
    # Cargar imagen de fondo con validación
    menu_bg_path = os.path.join(IMG_DIR, "menu.png")
    try:
        background = pygame.image.load(menu_bg_path).convert()
    except (pygame.error, FileNotFoundError):
        print(f"Advertencia: No se pudo cargar {menu_bg_path}")
        # Crear fondo de fallback
        background = pygame.Surface((SCREEN_W, SCREEN_H))
        background.fill((20, 12, 40))  # Color de fondo por defecto

    # Cargar música de fondo con validación
    menu_music_path = os.path.join(MUSIC_DIR, "Menu.mp3")
    try:
        pygame.mixer.music.load(menu_music_path)
        pygame.mixer.music.set_volume(0.6)
        pygame.mixer.music.play(-1)
    except (pygame.error, FileNotFoundError):
        print(f"Advertencia: No se pudo cargar {menu_music_path}")

    # ── Fuentes ──────────────────────────────────────────────────────────────
    font_btn    = pygame.font.SysFont("Georgia", 36, bold=True)
    font_title  = pygame.font.SysFont("Georgia", 72, bold=True)
    font_char   = pygame.font.SysFont("Georgia", 24, bold=True)
    font_select = pygame.font.SysFont("Georgia", 52, bold=True)

    # ── Menú principal: botones ───────────────────────────────────────────────
    btn_inicio = Button(
        BTN_PAD_X,
        SCREEN_H - BTN_PAD_Y - BTN_H * 2 - BTN_MARGIN,
        BTN_W, BTN_H, "Inicio", font_btn
    )
    btn_salir = Button(
        BTN_PAD_X,
        SCREEN_H - BTN_PAD_Y - BTN_H,
        BTN_W, BTN_H, "Salir", font_btn
    )

    overlay_menu = pygame.Surface((BTN_W + 40, BTN_H * 2 + BTN_MARGIN + 40), pygame.SRCALPHA)
    overlay_menu.fill(COLOR_OVERLAY)

    # ── Pantalla de selección de personaje ────────────────────────────────────
    char_images = load_character_images()
    char_cards  = build_character_cards(char_images, font_char)

    btn_continuar = Button(
        SCREEN_W // 2 + 20,
        SCREEN_H - BTN_PAD_Y - BTN_H,
        BTN_W, BTN_H, "Continuar", font_btn, enabled=False
    )
    btn_volver = Button(
        SCREEN_W // 2 - BTN_W - 20,
        SCREEN_H - BTN_PAD_Y - BTN_H,
        BTN_W, BTN_H, "Volver", font_btn
    )

    dark_overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    dark_overlay.fill((0, 0, 0, 170))

    # ── Estado ───────────────────────────────────────────────────────────────
    state         = STATE_MENU
    selected_char = None

    def launch_character():
        """Detiene el menú y lanza la intro del personaje elegido."""
        nonlocal running
        pygame.mixer.music.fadeout(400)
        pygame.time.wait(430)
        if selected_char == "Rafa":
            if rafa_intro is not None:
                rafa_intro.run_rafa_intro(screen, clock)
            else:
                print("Error: No se pudo cargar rafa_intro.py")
        else:
            # Para los demás personajes, ir directamente a Bmap en coordenadas 325,237
            if mapa is not None:
                mapa.run_bmap(screen, clock, selected_char, spawn_pos=(325, 237))
            else:
                print("Error: No se pudo cargar mapa.py")
        running = False

    # Navegación por teclado
    using_keyboard      = False
    menu_kb_focus       = 0      # 0=Inicio, 1=Salir
    menu_buttons_list   = [btn_inicio, btn_salir]
    select_zone         = 0      # 0=tarjetas, 1=botones inferiores
    card_kb_focus       = 0
    select_btn_kb_focus = 0      # 0=Volver, 1=Continuar
    select_btn_list     = [btn_volver, btn_continuar]

    def enter_select_screen():
        nonlocal state, selected_char, select_zone, card_kb_focus, select_btn_kb_focus
        state                 = STATE_SELECT
        selected_char         = None
        select_zone           = 0
        card_kb_focus         = 0
        select_btn_kb_focus   = 0
        btn_continuar.enabled = False
        for card in char_cards:
            card.selected = False

    def select_card(index):
        nonlocal selected_char
        for c in char_cards:
            c.selected = False
        char_cards[index].selected = True
        selected_char              = char_cards[index].name
        btn_continuar.enabled      = True

    # ── Loop principal ────────────────────────────────────────────────────────
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # El mouse desactiva el foco de teclado
            if event.type == pygame.MOUSEMOTION:
                using_keyboard = False

            # ── Menú principal ────────────────────────────────────────────────
            if state == STATE_MENU:
                # Teclado
                if event.type == pygame.KEYDOWN:
                    using_keyboard = True
                    if event.key in (pygame.K_UP, pygame.K_DOWN):
                        delta = 1 if event.key == pygame.K_DOWN else -1
                        menu_kb_focus = (menu_kb_focus + delta) % len(menu_buttons_list)
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        if menu_kb_focus == 0:
                            enter_select_screen()
                        else:
                            running = False
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                # Mouse
                if btn_inicio.is_clicked(event):
                    enter_select_screen()
                if btn_salir.is_clicked(event):
                    running = False

            # ── Selección de personaje ────────────────────────────────────────
            elif state == STATE_SELECT:
                # Teclado
                if event.type == pygame.KEYDOWN:
                    using_keyboard = True
                    if select_zone == 0:   # zona tarjetas
                        if event.key == pygame.K_LEFT:
                            card_kb_focus = (card_kb_focus - 1) % len(char_cards)
                        elif event.key == pygame.K_RIGHT:
                            card_kb_focus = (card_kb_focus + 1) % len(char_cards)
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            select_card(card_kb_focus)
                        elif event.key == pygame.K_DOWN:
                            select_zone         = 1
                            select_btn_kb_focus = 0
                        elif event.key == pygame.K_ESCAPE:
                            state = STATE_MENU
                    else:                  # zona botones inferiores
                        if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                            select_btn_kb_focus = 1 - select_btn_kb_focus
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            if select_btn_kb_focus == 0:   # Volver
                                state = STATE_MENU
                            elif btn_continuar.enabled:    # Continuar
                                state = STATE_GAME
                                launch_character()
                        elif event.key == pygame.K_UP:
                            select_zone = 0
                        elif event.key == pygame.K_ESCAPE:
                            state = STATE_MENU
                # Mouse
                if btn_volver.is_clicked(event):
                    state = STATE_MENU
                if btn_continuar.is_clicked(event):
                    state = STATE_GAME
                    launch_character()
                for card in char_cards:
                    if card.is_clicked(event):
                        select_card(char_cards.index(card))

        # ── Actualizar ────────────────────────────────────────────────────────
        if state == STATE_MENU:
            # Foco de teclado en botones del menú
            for i, btn in enumerate(menu_buttons_list):
                btn.focused = using_keyboard and (i == menu_kb_focus)
            btn_inicio.update(mouse_pos)
            btn_salir.update(mouse_pos)

        elif state == STATE_SELECT:
            # Foco de teclado en tarjetas y botones
            for i, card in enumerate(char_cards):
                card.focused = using_keyboard and (select_zone == 0) and (i == card_kb_focus)
            for i, btn in enumerate(select_btn_list):
                btn.focused = using_keyboard and (select_zone == 1) and (i == select_btn_kb_focus)
            for card in char_cards:
                card.update(mouse_pos)
            btn_volver.update(mouse_pos)
            btn_continuar.update(mouse_pos)

        # ── Dibujar ───────────────────────────────────────────────────────────
        draw_background(screen, background, SCREEN_W, SCREEN_H)

        if state == STATE_MENU:
            overlay_x = BTN_PAD_X - 20
            overlay_y = SCREEN_H - BTN_PAD_Y - BTN_H * 2 - BTN_MARGIN - 20
            screen.blit(overlay_menu, (overlay_x, overlay_y))
            btn_inicio.draw(screen)
            btn_salir.draw(screen)

        elif state == STATE_SELECT:
            # Oscurecer el fondo
            screen.blit(dark_overlay, (0, 0))

            # Título
            title_s  = font_select.render("Elige tu personaje", True, COLOR_TEXT_HOVER)
            shadow_s = font_select.render("Elige tu personaje", True, (0, 0, 0))
            tx = (SCREEN_W - title_s.get_width()) // 2
            screen.blit(shadow_s, (tx + 3, 33))
            screen.blit(title_s,  (tx,     30))

            # Tarjetas de personajes
            for card in char_cards:
                card.draw(screen)
            # Anillo de foco (teclado) encima de todo
            if using_keyboard and select_zone == 0:
                char_cards[card_kb_focus].draw_focus_ring(screen)

            # Nombre seleccionado (sobre los botones)
            if selected_char:
                sel_s = font_btn.render(f"► {selected_char} ◄", True, COLOR_CARD_BORDER_SEL)
                screen.blit(sel_s, (
                    (SCREEN_W - sel_s.get_width()) // 2,
                    SCREEN_H - BTN_PAD_Y - BTN_H - 52
                ))

            btn_volver.draw(screen)
            btn_continuar.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
