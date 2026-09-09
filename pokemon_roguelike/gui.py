"""Pygame-powered graphical interface with a terminal-inspired aesthetic."""

from __future__ import annotations

import argparse
import asyncio
import math
import os
import random
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from enum import StrEnum

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .api import PokeAPIClient
from .ascii_art import AsciiSprite
from .battle import Battle, BattleEvent, Side
from .factories import create_player, create_random_trainer
from .models import Move, Pokemon, StatusCondition

WINDOW_SIZE = (1280, 720)
FPS = 60
STARTERS = ("bulbasaur", "charmander", "squirtle")

BACKGROUND = (7, 12, 18)
PANEL = (12, 24, 30)
PANEL_HOVER = (20, 43, 49)
GRID = (13, 31, 37)
GREEN = (104, 255, 180)
CYAN = (78, 219, 255)
AMBER = (255, 205, 92)
RED = (255, 94, 105)
MUTED = (108, 139, 145)
TEXT = (220, 244, 235)

STATUS_CURE_ITEMS = {
    StatusCondition.POISONED: "antidote",
    StatusCondition.FROZEN: "freeze_heal",
    StatusCondition.PARALYZED: "paralyze_heal",
    StatusCondition.BURNED: "burn_heal",
    StatusCondition.ASLEEP: "awakening",
}


class Screen(StrEnum):
    SETUP = "setup"
    LOADING = "loading"
    BATTLE = "battle"
    FINISHED = "finished"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class Button:
    rect: pygame.Rect
    label: str
    value: str
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class LoadedBattle:
    battle: Battle
    sprites: dict[tuple[Side, int], AsciiSprite]


def run() -> None:
    """Launch the graphical game, or the original terminal UI on request."""

    parser = argparse.ArgumentParser(description="Play the Pokémon roguelike")
    parser.add_argument("--seed", type=int, help="Use a reproducible random seed")
    parser.add_argument(
        "--terminal",
        action="store_true",
        help="Use the plain terminal interface instead of the graphical window",
    )
    args = parser.parse_args()

    if args.terminal:
        from .cli import play

        try:
            asyncio.run(play(seed=args.seed))
        except (EOFError, KeyboardInterrupt):
            print("\nGame closed.")
        return

    GraphicalGame(seed=args.seed).run()


class GraphicalGame:
    """Own the window, input state, and presentation of one battle."""

    def __init__(self, seed: int | None = None) -> None:
        pygame.init()
        pygame.key.start_text_input()
        pygame.display.set_caption("Pokémon Roguelike // Terminal Link")
        self.surface = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.Clock()
        self.font = _font(19)
        self.small_font = _font(15)
        self.large_font = _font(42, bold=True)
        self.medium_font = _font(25, bold=True)
        self.sprite_font = _font(18, bold=True)

        self.seed = seed
        self.screen = Screen.SETUP
        self.running = True
        self.player_name = ""
        self.name_active = True
        self.starter_index = 0
        self.menu = "root"
        self.error_message = ""
        self.battle: Battle | None = None
        self.sprite_surfaces: dict[tuple[Side, int], pygame.Surface] = {}
        self.messages: deque[str] = deque(maxlen=7)
        self.buttons: list[Button] = []
        self.started_at = pygame.time.get_ticks()
        self.action_flash_until = 0
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="poke-load")
        self.loading_future: Future[LoadedBattle] | None = None
        self.scanline_overlay = self._make_scanline_overlay()

    def run(self) -> None:
        try:
            while self.running:
                self._handle_events()
                self._update()
                self._draw()
                pygame.display.flip()
                self.clock.tick(FPS)
        finally:
            self.executor.shutdown(wait=False, cancel_futures=True)
            pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.screen is Screen.BATTLE and self.menu != "root":
                    self.menu = "root"
                else:
                    self.running = False
            elif self.screen is Screen.SETUP:
                self._handle_setup_event(event)
            elif self.screen is Screen.BATTLE:
                self._handle_battle_event(event)
            elif self.screen in {Screen.FINISHED, Screen.ERROR}:
                if event.type == pygame.KEYDOWN and event.key in {
                    pygame.K_RETURN,
                    pygame.K_SPACE,
                }:
                    self._reset()

    def _handle_setup_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.TEXTINPUT and self.name_active:
            candidate = self.player_name + event.text
            if len(candidate) <= 16 and event.text.isprintable():
                self.player_name = candidate
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE and self.name_active:
                self.player_name = self.player_name[:-1]
            elif event.key == pygame.K_LEFT:
                self.starter_index = (self.starter_index - 1) % len(STARTERS)
            elif event.key == pygame.K_RIGHT:
                self.starter_index = (self.starter_index + 1) % len(STARTERS)
            elif event.key == pygame.K_RETURN:
                self._begin_loading()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            name_rect = pygame.Rect(420, 245, 440, 52)
            self.name_active = name_rect.collidepoint(event.pos)
            for index, rect in enumerate(self._starter_rects()):
                if rect.collidepoint(event.pos):
                    self.starter_index = index
            if pygame.Rect(475, 570, 330, 58).collidepoint(event.pos):
                self._begin_loading()

    def _handle_battle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.menu = "root"
                return
            number = event.key - pygame.K_1
            if 0 <= number < len(self.buttons):
                self._activate_button(self.buttons[number])
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.enabled and button.rect.collidepoint(event.pos):
                    self._activate_button(button)
                    break

    def _update(self) -> None:
        if self.screen is not Screen.LOADING or self.loading_future is None:
            return
        if not self.loading_future.done():
            return

        try:
            loaded = self.loading_future.result()
        except Exception as error:  # surfaced cleanly inside the window
            self.error_message = str(error)
            self.screen = Screen.ERROR
            return

        self.battle = loaded.battle
        self.sprite_surfaces = {
            key: self._render_ascii_sprite(sprite)
            for key, sprite in loaded.sprites.items()
        }
        opponent = self.battle.opponent
        opponent_pokemon = self.battle.active_pokemon(Side.OPPONENT)
        self.messages.extend(
            (
                f"> TRAINER {opponent.name.upper()} REQUESTS COMBAT",
                f"> {opponent.name.upper()} DEPLOYED {opponent_pokemon.display_name.upper()}",
                f"> GO, {self.battle.active_pokemon(Side.PLAYER).display_name.upper()}!",
            )
        )
        self.screen = Screen.BATTLE

    def _draw(self) -> None:
        self.surface.fill(BACKGROUND)
        self._draw_grid()
        if self.screen is Screen.SETUP:
            self._draw_setup()
        elif self.screen is Screen.LOADING:
            self._draw_loading()
        elif self.screen is Screen.BATTLE:
            self._draw_battle()
        elif self.screen is Screen.FINISHED:
            self._draw_finished()
        else:
            self._draw_error()
        self._draw_scanlines()

    def _draw_setup(self) -> None:
        _text(self.surface, self.large_font, "POKÉMON://ROGUE", (640, 78), GREEN, center=True)
        _text(
            self.surface,
            self.font,
            "A TWENTY-MINUTE TERMINAL RUN // BUILD. RISK. SURVIVE.",
            (640, 132),
            MUTED,
            center=True,
        )

        _text(self.surface, self.small_font, "TRAINER HANDLE", (420, 218), CYAN)
        name_rect = pygame.Rect(420, 245, 440, 52)
        self._draw_panel(name_rect, CYAN if self.name_active else MUTED)
        cursor = "_" if self.name_active and pygame.time.get_ticks() // 450 % 2 else ""
        _text(
            self.surface,
            self.medium_font,
            (self.player_name or "PLAYER") + cursor,
            (438, 257),
            TEXT,
        )

        _text(self.surface, self.small_font, "SELECT STARTER PROCESS", (170, 340), CYAN)
        starter_cards = zip(STARTERS, self._starter_rects(), strict=True)
        for index, (starter, rect) in enumerate(starter_cards):
            selected = index == self.starter_index
            self._draw_panel(
                rect,
                GREEN if selected else MUTED,
                fill=PANEL_HOVER if selected else PANEL,
            )
            _text(
                self.surface,
                self.medium_font,
                f"0{index + 1}",
                (rect.x + 18, rect.y + 16),
                GREEN if selected else MUTED,
            )
            _text(
                self.surface,
                self.font,
                starter.upper(),
                (rect.centerx, rect.y + 67),
                TEXT,
                center=True,
            )

        start_rect = pygame.Rect(475, 570, 330, 58)
        self._draw_panel(start_rect, GREEN, fill=(15, 48, 41))
        _text(
            self.surface,
            self.medium_font,
            "[ INITIATE RUN ]",
            start_rect.center,
            GREEN,
            center=True,
        )
        _text(
            self.surface,
            self.small_font,
            "ENTER TO START  //  ← → TO SELECT  //  ESC TO QUIT",
            (640, 665),
            MUTED,
            center=True,
        )

    def _draw_loading(self) -> None:
        elapsed = (pygame.time.get_ticks() - self.started_at) / 1000
        spinner = "|/-\\"[int(elapsed * 8) % 4]
        _text(self.surface, self.large_font, "ESTABLISHING LINK", (640, 270), GREEN, center=True)
        _text(
            self.surface,
            self.medium_font,
            f"[{spinner}] RETRIEVING CREATURE DATA + GLYPH MATRICES",
            (640, 350),
            CYAN,
            center=True,
        )
        dots = "." * (int(elapsed * 2) % 4)
        _text(self.surface, self.font, f"PLEASE HOLD{dots}", (640, 405), MUTED, center=True)

    def _draw_battle(self) -> None:
        assert self.battle is not None
        battle = self.battle
        now = pygame.time.get_ticks()
        border = AMBER if now < self.action_flash_until else GREEN

        _text(self.surface, self.small_font, "PKMN_ROGUE // BATTLE LINK ACTIVE", (34, 22), GREEN)
        seed_label = str(self.seed) if self.seed is not None else "RANDOM"
        _text(self.surface, self.small_font, f"SEED::{seed_label}", (1120, 22), MUTED)
        pygame.draw.line(self.surface, GRID, (30, 50), (1250, 50), 1)

        opponent = battle.active_pokemon(Side.OPPONENT)
        player = battle.active_pokemon(Side.PLAYER)
        self._draw_status_panel(opponent, pygame.Rect(55, 77, 475, 96), RED)
        self._draw_status_panel(player, pygame.Rect(730, 350, 495, 105), GREEN)

        self._draw_active_sprite(Side.OPPONENT, pygame.Rect(735, 62, 500, 275))
        self._draw_active_sprite(Side.PLAYER, pygame.Rect(45, 185, 520, 285))

        log_rect = pygame.Rect(35, 490, 770, 195)
        self._draw_panel(log_rect, border)
        _text(self.surface, self.small_font, "// COMBAT LOG", (55, 506), border)
        for index, message in enumerate(self.messages):
            color = RED if "FAINTED" in message else TEXT
            _text(self.surface, self.small_font, message, (56, 535 + index * 20), color)

        action_rect = pygame.Rect(825, 490, 420, 195)
        self._draw_panel(action_rect, CYAN)
        title = "COMMAND" if self.menu == "root" else self.menu.upper()
        _text(self.surface, self.small_font, f"// {title}", (845, 506), CYAN)
        self.buttons = self._battle_buttons()
        mouse_position = pygame.mouse.get_pos()
        for index, button in enumerate(self.buttons, start=1):
            hovered = button.rect.collidepoint(mouse_position)
            fill = PANEL_HOVER if hovered else PANEL
            self._draw_panel(button.rect, CYAN if hovered else MUTED, fill=fill)
            label = f"{index}. {button.label}"
            _text(self.surface, self.small_font, label, button.rect.center, TEXT, center=True)

    def _draw_finished(self) -> None:
        assert self.battle is not None
        won = self.battle.winner is Side.PLAYER
        color = GREEN if won else RED
        heading = "BATTLE CLEARED" if won else "RUN TERMINATED"
        _text(self.surface, self.large_font, heading, (640, 250), color, center=True)
        detail = (
            f"{self.battle.player.name.upper()} SURVIVED THE LINK"
            if won
            else "THE PARTY CAN NO LONGER CONTINUE"
        )
        _text(self.surface, self.font, detail, (640, 325), TEXT, center=True)
        _text(
            self.surface,
            self.font,
            "PRESS ENTER TO INITIALIZE ANOTHER RUN",
            (640, 430),
            CYAN,
            center=True,
        )

    def _draw_error(self) -> None:
        _text(self.surface, self.large_font, "LINK FAILURE", (640, 245), RED, center=True)
        _text(self.surface, self.font, self.error_message[:90], (640, 330), TEXT, center=True)
        _text(
            self.surface,
            self.font,
            "PRESS ENTER TO RETRY  //  ESC TO QUIT",
            (640, 410),
            CYAN,
            center=True,
        )

    def _begin_loading(self) -> None:
        if self.screen is not Screen.SETUP:
            return
        self.player_name = self.player_name.strip() or "PLAYER"
        self.screen = Screen.LOADING
        self.started_at = pygame.time.get_ticks()
        starter = STARTERS[self.starter_index]
        self.loading_future = self.executor.submit(
            _load_battle,
            self.player_name,
            starter,
            self.seed,
        )

    def _activate_button(self, button: Button) -> None:
        if not button.enabled or self.battle is None:
            return
        if button.value in {"fight", "item", "switch"}:
            self.menu = button.value
            return
        if button.value == "back":
            self.menu = "root"
            return

        forced_switch = False
        try:
            if button.value.startswith("move:"):
                move_name = button.value.removeprefix("move:")
                events = self.battle.attack(Side.PLAYER, move_name)
            elif button.value.startswith("item:"):
                item = button.value.removeprefix("item:")
                events = (self.battle.use_item(Side.PLAYER, item),)
            elif button.value.startswith("switch:"):
                forced_switch = self.battle.active_pokemon(Side.PLAYER).is_fainted
                party_index = int(button.value.removeprefix("switch:"))
                events = (self.battle.switch(Side.PLAYER, party_index),)
            else:
                return
        except ValueError as error:
            self.messages.append(f"> INVALID COMMAND: {str(error).upper()}")
            return

        self._record_events(events)
        self.action_flash_until = pygame.time.get_ticks() + 160
        self.menu = "root"
        if forced_switch:
            return
        self._complete_round()

    def _complete_round(self) -> None:
        assert self.battle is not None
        battle = self.battle
        if battle.winner is not None:
            self.screen = Screen.FINISHED
            return

        opponent_fainted = battle.active_pokemon(Side.OPPONENT).is_fainted
        if opponent_fainted:
            self._replace_opponent()
        else:
            self._record_events(self._trainer_turn())

        if battle.winner is None:
            for side in (Side.PLAYER, Side.OPPONENT):
                self._record_events(battle.apply_end_of_turn_effects(side))

        if battle.winner is None and battle.active_pokemon(Side.OPPONENT).is_fainted:
            self._replace_opponent()

        if battle.winner is not None:
            self.screen = Screen.FINISHED
        elif battle.active_pokemon(Side.PLAYER).is_fainted:
            choices = battle.player.healthy_party_indices()
            if choices:
                self.menu = "switch"

    def _trainer_turn(self) -> tuple[BattleEvent, ...]:
        assert self.battle is not None
        battle = self.battle
        trainer = battle.opponent
        pokemon = battle.active_pokemon(Side.OPPONENT)
        cure = STATUS_CURE_ITEMS.get(pokemon.status)
        if cure and trainer.inventory.count(cure) > 0:
            return (battle.use_item(Side.OPPONENT, cure),)
        if pokemon.hp <= pokemon.max_hp * 0.2 and trainer.inventory.count("potion") > 0:
            return (battle.use_item(Side.OPPONENT, "potion"),)
        return battle.attack(Side.OPPONENT, battle.choose_trainer_move())

    def _replace_opponent(self) -> None:
        assert self.battle is not None
        choices = self.battle.opponent.healthy_party_indices()
        if choices:
            event = self.battle.switch(Side.OPPONENT, self.battle.rng.choice(choices))
            self._record_events((event,))

    def _record_events(self, events: tuple[BattleEvent, ...]) -> None:
        for event in events:
            self.messages.append(f"> {event.message.upper()}")

    def _battle_buttons(self) -> list[Button]:
        assert self.battle is not None
        battle = self.battle
        entries: list[tuple[str, str]] = []

        if self.menu == "root":
            entries.append(("FIGHT", "fight"))
            if self._usable_items():
                entries.append(("ITEM", "item"))
            if battle.player.healthy_party_indices(excluding=battle.player_active_index):
                entries.append(("SWITCH", "switch"))
        elif self.menu == "fight":
            pokemon = battle.active_pokemon(Side.PLAYER)
            entries.extend(
                (f"{_move_label(move)} [{move.current_pp}]", f"move:{move.name}")
                for move in pokemon.moves.values()
                if move.current_pp > 0
            )
            entries.append(("< BACK", "back"))
        elif self.menu == "item":
            entries.extend(
                (
                    f"{item.replace('_', ' ').upper()} x{battle.player.inventory.count(item)}",
                    f"item:{item}",
                )
                for item in self._usable_items()
            )
            entries.append(("< BACK", "back"))
        elif self.menu == "switch":
            entries.extend(
                (
                    battle.player.party[index].display_name.upper(),
                    f"switch:{index}",
                )
                for index in battle.player.healthy_party_indices(
                    excluding=battle.player_active_index
                )
            )
            if not battle.active_pokemon(Side.PLAYER).is_fainted:
                entries.append(("< BACK", "back"))

        return [
            Button(self._button_rect(index), label, value)
            for index, (label, value) in enumerate(entries)
        ]

    def _usable_items(self) -> tuple[str, ...]:
        assert self.battle is not None
        battle = self.battle
        pokemon = battle.active_pokemon(Side.PLAYER)
        usable: list[str] = []
        if battle.player.inventory.count("potion") and 0 < pokemon.hp < pokemon.max_hp:
            usable.append("potion")
        cure = STATUS_CURE_ITEMS.get(pokemon.status)
        if cure and battle.player.inventory.count(cure):
            usable.append(cure)
        return tuple(usable)

    def _draw_active_sprite(self, side: Side, bounds: pygame.Rect) -> None:
        assert self.battle is not None
        index = (
            self.battle.player_active_index
            if side is Side.PLAYER
            else self.battle.opponent_active_index
        )
        sprite = self.sprite_surfaces.get((side, index))
        if sprite is None:
            return

        scale = min(bounds.width / sprite.get_width(), bounds.height / sprite.get_height(), 1)
        if scale < 1:
            sprite = pygame.transform.scale(
                sprite,
                (round(sprite.get_width() * scale), round(sprite.get_height() * scale)),
            )
        bob = round(math.sin(pygame.time.get_ticks() / 420 + index) * 3)
        sprite_rect = sprite.get_rect(midbottom=(bounds.centerx, bounds.bottom - 3 + bob))
        self.surface.blit(sprite, sprite_rect)

    def _draw_status_panel(
        self,
        pokemon: Pokemon,
        rect: pygame.Rect,
        accent: tuple[int, int, int],
    ) -> None:
        self._draw_panel(rect, accent)
        _text(
            self.surface,
            self.medium_font,
            f"{pokemon.display_name.upper()}  L{pokemon.level:02}",
            (rect.x + 18, rect.y + 13),
            TEXT,
        )
        status = pokemon.status.value.upper() if pokemon.status else "STABLE"
        _text(self.surface, self.small_font, status, (rect.right - 100, rect.y + 20), accent)

        bar = pygame.Rect(rect.x + 18, rect.y + 60, rect.width - 118, 13)
        pygame.draw.rect(self.surface, GRID, bar)
        health_ratio = pokemon.hp / pokemon.max_hp
        health_color = GREEN if health_ratio > 0.5 else AMBER if health_ratio > 0.2 else RED
        fill = bar.copy()
        fill.width = round(bar.width * health_ratio)
        pygame.draw.rect(self.surface, health_color, fill)
        _text(
            self.surface,
            self.small_font,
            f"HP {pokemon.hp:03}/{pokemon.max_hp:03}",
            (bar.right + 10, bar.y - 3),
            health_color,
        )

    def _draw_panel(
        self,
        rect: pygame.Rect,
        accent: tuple[int, int, int],
        fill: tuple[int, int, int] = PANEL,
    ) -> None:
        pygame.draw.rect(self.surface, fill, rect)
        pygame.draw.rect(self.surface, accent, rect, 1)
        corner = 9
        for x, y, sx, sy in (
            (rect.left, rect.top, 1, 1),
            (rect.right, rect.top, -1, 1),
            (rect.left, rect.bottom, 1, -1),
            (rect.right, rect.bottom, -1, -1),
        ):
            pygame.draw.line(self.surface, accent, (x, y), (x + corner * sx, y), 3)
            pygame.draw.line(self.surface, accent, (x, y), (x, y + corner * sy), 3)

    def _draw_grid(self) -> None:
        for x in range(0, WINDOW_SIZE[0], 32):
            pygame.draw.line(self.surface, GRID, (x, 0), (x, WINDOW_SIZE[1]))
        for y in range(0, WINDOW_SIZE[1], 32):
            pygame.draw.line(self.surface, GRID, (0, y), (WINDOW_SIZE[0], y))

    def _draw_scanlines(self) -> None:
        self.surface.blit(self.scanline_overlay, (0, 0))

    @staticmethod
    def _make_scanline_overlay() -> pygame.Surface:
        overlay = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        for y in range(0, WINDOW_SIZE[1], 4):
            pygame.draw.line(overlay, (0, 0, 0, 28), (0, y), (WINDOW_SIZE[0], y))
        return overlay

    def _render_ascii_sprite(self, sprite: AsciiSprite) -> pygame.Surface:
        cell_width = self.sprite_font.size("M")[0]
        cell_height = self.sprite_font.get_linesize()
        surface = pygame.Surface(
            (sprite.width * cell_width, sprite.height * cell_height),
            pygame.SRCALPHA,
        )
        for y, row in enumerate(sprite.rows):
            for x, cell in enumerate(row):
                if cell is None:
                    continue
                glyph = self.sprite_font.render(cell.character, True, cell.color)
                surface.blit(glyph, (x * cell_width, y * cell_height))
        return surface

    @staticmethod
    def _starter_rects() -> tuple[pygame.Rect, ...]:
        return tuple(pygame.Rect(170 + index * 320, 370, 275, 135) for index in range(3))

    @staticmethod
    def _button_rect(index: int) -> pygame.Rect:
        column = index % 2
        row = index // 2
        return pygame.Rect(845 + column * 194, 535 + row * 52, 180, 46)

    def _reset(self) -> None:
        self.screen = Screen.SETUP
        self.menu = "root"
        self.battle = None
        self.sprite_surfaces.clear()
        self.messages.clear()
        self.loading_future = None
        self.error_message = ""


def _load_battle(player_name: str, starter_name: str, seed: int | None) -> LoadedBattle:
    return asyncio.run(_load_battle_async(player_name, starter_name, seed))


async def _load_battle_async(
    player_name: str,
    starter_name: str,
    seed: int | None,
) -> LoadedBattle:
    rng = random.Random(seed)
    async with PokeAPIClient(timeout_seconds=30) as client:
        starter = await client.get_pokemon(starter_name, level=5)
        opponent = await create_random_trainer(
            client,
            level=5,
            rng=rng,
            max_party_size=3,
        )
        player = create_player(player_name, starter)
        battle = Battle(player, opponent, rng=rng)

        sprite_requests: list[tuple[tuple[Side, int], str, bool]] = []
        for side, combatant in (
            (Side.PLAYER, battle.player),
            (Side.OPPONENT, battle.opponent),
        ):
            for index, pokemon in enumerate(combatant.party):
                preferred = (
                    pokemon.back_sprite_url
                    if side is Side.PLAYER
                    else pokemon.front_sprite_url
                )
                fallback = pokemon.front_sprite_url or pokemon.back_sprite_url
                url = preferred or fallback
                if url:
                    mirrored = side is Side.PLAYER and preferred is None
                    sprite_requests.append(((side, index), url, mirrored))

        image_bytes = await asyncio.gather(
            *(client.get_bytes(url) for _, url, _ in sprite_requests)
        )

    sprites = {
        key: AsciiSprite.from_image_bytes(data, width=30, mirrored=mirrored)
        for (key, _, mirrored), data in zip(sprite_requests, image_bytes, strict=True)
    }
    return LoadedBattle(battle=battle, sprites=sprites)


def _font(size: int, bold: bool = False) -> pygame.font.Font:
    return pygame.font.SysFont(
        ["consolas", "dejavusansmono", "liberationmono", "monospace"],
        size,
        bold=bold,
    )


def _text(
    target: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    position: tuple[int, int],
    color: tuple[int, int, int],
    center: bool = False,
) -> None:
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(center=position) if center else rendered.get_rect(topleft=position)
    target.blit(rendered, rect)


def _move_label(move: Move) -> str:
    return move.name.replace("-", " ").upper()
