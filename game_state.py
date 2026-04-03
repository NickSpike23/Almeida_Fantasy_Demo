"""
game_state.py - Estado compartido del juego.
Centraliza el progreso del mundo con una interfaz controlada en lugar de
exponer variables mutables por todo el proyecto.
"""


class GameState:
    """Singleton para manejar el estado global del juego con acceso encapsulado."""

    _instance = None
    _initialized = False

    __slots__ = (
        "_max_bmap_defeated",
        "_zuazo_first_done",
        "_zuazo_combat_done",
        "_door_d_visited",
        "_door_d_visited2nd",
    )

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GameState, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not GameState._initialized:
            self._init_state()
            GameState._initialized = True

    def _init_state(self):
        self._max_bmap_defeated = False
        self._zuazo_first_done = False
        self._zuazo_combat_done = False
        self._door_d_visited = False
        self._door_d_visited2nd = False

    @property
    def max_bmap_defeated(self) -> bool:
        return self._max_bmap_defeated

    @max_bmap_defeated.setter
    def max_bmap_defeated(self, value: bool) -> None:
        self._max_bmap_defeated = bool(value)

    @property
    def zuazo_first_done(self) -> bool:
        return self._zuazo_first_done

    @zuazo_first_done.setter
    def zuazo_first_done(self, value: bool) -> None:
        self._zuazo_first_done = bool(value)

    @property
    def zuazo_combat_done(self) -> bool:
        return self._zuazo_combat_done

    @zuazo_combat_done.setter
    def zuazo_combat_done(self, value: bool) -> None:
        self._zuazo_combat_done = bool(value)

    @property
    def door_d_visited(self) -> bool:
        return self._door_d_visited

    @door_d_visited.setter
    def door_d_visited(self, value: bool) -> None:
        self._door_d_visited = bool(value)

    @property
    def door_d_visited2nd(self) -> bool:
        return self._door_d_visited2nd

    @door_d_visited2nd.setter
    def door_d_visited2nd(self, value: bool) -> None:
        self._door_d_visited2nd = bool(value)

    def mark_max_bmap_defeated(self) -> None:
        self._max_bmap_defeated = True

    def mark_zuazo_first_done(self) -> None:
        self._zuazo_first_done = True

    def mark_zuazo_combat_done(self) -> None:
        self._zuazo_combat_done = True

    def mark_door_d_visited(self) -> None:
        self._door_d_visited = True

    def mark_door_d_visited2nd(self) -> None:
        self._door_d_visited2nd = True

    def reset_progress(self) -> None:
        self._init_state()


def get_game_state() -> GameState:
    """Obtiene la instancia singleton del estado del juego."""
    return GameState()


def sync_from_mapa_globals():
    """Sincroniza desde las variables globales de mapa.py si aún existen."""
    import mapa

    state = get_game_state()
    state.max_bmap_defeated = getattr(mapa, "_max_bmap_defeated", state.max_bmap_defeated)
    state.zuazo_first_done = getattr(mapa, "_zuazo_first_done", state.zuazo_first_done)
    state.zuazo_combat_done = getattr(mapa, "_zuazo_combat_done", state.zuazo_combat_done)
    state.door_d_visited = getattr(mapa, "_door_d_visited", state.door_d_visited)
    state.door_d_visited2nd = getattr(mapa, "_door_d_visited2nd", state.door_d_visited2nd)


def sync_to_mapa_globals():
    """Sincroniza hacia las variables globales de mapa.py para compatibilidad."""
    import mapa

    state = get_game_state()
    mapa._max_bmap_defeated = state.max_bmap_defeated
    mapa._zuazo_first_done = state.zuazo_first_done
    mapa._zuazo_combat_done = state.zuazo_combat_done
    mapa._door_d_visited = state.door_d_visited
    mapa._door_d_visited2nd = state.door_d_visited2nd


def sync_from_combate_globals():
    """Reservado para compatibilidad con el código antiguo."""
    import combate
    _ = combate
    return


def sync_to_combate_globals():
    """Reservado para compatibilidad con el código antiguo."""
    import combate
    _ = combate
    return