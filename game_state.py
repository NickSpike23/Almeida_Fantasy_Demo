"""
game_state.py - Estado global compartido del juego
Centraliza todas las variables de estado para evitar desincronización entre módulos.
"""

class GameState:
    """Singleton para manejar el estado global del juego"""
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GameState, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not GameState._initialized:
            self._init_state()
            GameState._initialized = True
    
    def _init_state(self):
        """Inicializar todas las variables de estado"""
        # Variables de Max/Bmap
        self.max_bmap_defeated: bool = False
        
        # Variables de Zuazo
        self.zuazo_first_done: bool = False       # primer diálogo con Zuazo completado
        self.zuazo_combat_done: bool = False      # combate con Zuazo completado
        
        # Variables de puertas
        self.door_d_visited: bool = False         # jugador vio la puerta D cerrada (post 1er diálogo)
        self.door_d_visited2nd: bool = False      # jugador vio la puerta D cerrada (segunda vez)

# Función de conveniencia para obtener la instancia
def get_game_state() -> GameState:
    """Obtiene la instancia singleton del estado del juego"""
    return GameState()

# Funciones de compatibilidad con el código existente
def sync_from_mapa_globals():
    """Sincroniza desde las variables globales de mapa.py"""
    import mapa
    state = get_game_state()
    
    if hasattr(mapa, '_max_bmap_defeated'):
        state.max_bmap_defeated = mapa._max_bmap_defeated
    if hasattr(mapa, '_zuazo_first_done'):
        state.zuazo_first_done = mapa._zuazo_first_done
    if hasattr(mapa, '_zuazo_combat_done'):
        state.zuazo_combat_done = mapa._zuazo_combat_done
    if hasattr(mapa, '_door_d_visited'):
        state.door_d_visited = mapa._door_d_visited
    if hasattr(mapa, '_door_d_visited2nd'):
        state.door_d_visited2nd = mapa._door_d_visited2nd

def sync_to_mapa_globals():
    """Sincroniza hacia las variables globales de mapa.py"""
    import mapa
    state = get_game_state()
    
    mapa._max_bmap_defeated = state.max_bmap_defeated
    mapa._zuazo_first_done = state.zuazo_first_done
    mapa._zuazo_combat_done = state.zuazo_combat_done
    mapa._door_d_visited = state.door_d_visited
    mapa._door_d_visited2nd = state.door_d_visited2nd

def sync_from_combate_globals():
    """Sincroniza desde las variables globales de combate.py"""
    import combate
    state = get_game_state()
    
    return

def sync_to_combate_globals():
    """Sincroniza hacia las variables globales de combate.py"""
    import combate
    state = get_game_state()
    
    return