# Graphical Migration Plan

## Product direction

The game is a fast, replayable Pokémon roguelite presented as a fictional battle
terminal. A successful run should take about 20 minutes. Familiar Pokémon rules
provide clarity; route choices, scarce resources, build synergies, and encounter
modifiers provide purposeful chaos.

The interface should feel raw and personal rather than glossy. Color and motion
exist to communicate state and impact, not to hide the terminal aesthetic.

## Selected stack

| Concern | Library | Reason |
| --- | --- | --- |
| Window, input, audio, rendering | `pygame-ce` | Mature SDL-based game foundation without imposing a UI style |
| Sprite decoding and conversion | `Pillow` | Reliable resizing, RGBA transparency, palette, and image-format support |
| PokéAPI and sprite downloads | `aiohttp` | Already used by the project; supports concurrent loading |
| Game rules | Existing domain modules | Keeps graphical presentation independent from battle behavior |
| Persistence | Standard-library JSON initially | Small, inspectable local saves are enough for one player |

The project will not adopt a general GUI toolkit or terminal game engine. The
custom visual identity is easier to maintain with a thin Pygame presentation
layer over the existing engine.

## Migration phases

### Phase 1: graphical battle slice (complete)

- Root launcher opens a desktop window by default.
- Trainer name and starter selection are graphical.
- PokéAPI front/back sprites become transparent, colored ASCII glyph grids.
- Battle commands support mouse and number-key input.
- Health, status, combat events, loading, errors, victory, and defeat are shown.
- The original terminal interface remains available with `--terminal`.

This phase proves the visual direction without changing the underlying rules.

### Phase 2: make one run genuinely fun

- Add a run controller separate from the battle controller.
- Build a short branching route of approximately 8 encounters.
- Alternate wild battles, trainers, recovery, shops, risks, and events.
- Place a distinct rule-changing boss at the end of each run.
- Add rewards after every encounter so the player's build changes frequently.
- Cache PokéAPI data and sprites so network access never interrupts a run.

Target pacing: setup under one minute, normal encounters around two minutes,
and a final boss lasting three to four minutes.

### Phase 3: purposeful build chaos

- Introduce a small set of run-only artifacts that bend one understandable rule.
- Let artifacts interact with types, statuses, switching, items, and move PP.
- Give elite encounters visible modifiers and proportionally stronger rewards.
- Use route previews so risk is chosen rather than silently imposed.
- Keep the first content pool small enough that combinations can be balanced.

Every modifier must create a decision, enable a build, or demand adaptation. A
modifier that only adds variance or numerical power does not belong.

### Phase 4: lasting progression

- Store achievements, discovered Pokémon, settings, and unlocked starters.
- Catching a Pokémon unlocks its base evolutionary form for future runs.
- Do not carry levels, moves, items, or combat power between runs.
- Make achievements encourage unusual strategies rather than repetitive grinding.
- Add a terminal-style archive showing discoveries and memorable run statistics.

### Phase 5: presentation and release

- Add compact impact animations, screen shake, particles, and battle transitions.
- Use Pygame's audio mixer for restrained UI sounds, cries, and music controls.
- Add settings for volume, text speed, color accessibility, and reduced motion.
- Package desktop builds for the prioritized operating systems.
- Record a short gameplay trailer and update the README with real screenshots.

## ASCII renderer extraction gate

The current Pillow adapter remains internal while the game is evolving. A
separate PyPI library will only be created when all of these are true:

1. At least two non-Pokémon examples need the same renderer.
2. Existing packages cannot meet a documented requirement without invasive forks.
3. The data model works for still images, animation frames, and more than one UI.
4. Rendering behavior has stable tests and benchmark targets.
5. The public package contains no Pokémon-specific names or assumptions.

Likely extraction-worthy gaps include consistent animation-frame alignment,
game-oriented anchoring and layers, deterministic palette conversion, and the
same compiled sprite format rendering in both real and graphical terminals.

## Decision log

| Decision | Alternatives | Reason |
| --- | --- | --- |
| Graphical terminal aesthetic | Plain TUI; conventional sprite UI | Preserves the project's original personality while improving accessibility |
| Pygame-ce presentation | Textual; Tkinter; full terminal engine | Best balance of freedom, game support, and modest complexity |
| Pillow sprite conversion | Write an image decoder; depend on a full ASCII app | Established image handling with a small integration surface |
| Keep rules presentation-neutral | Move battle logic into screens | Allows terminal fallback and future UI changes without duplicating mechanics |
| Internal renderer first | Publish a package immediately | Real game requirements should shape the API before it becomes public |
| Fun-first roadmap | Architecture-first expansion | The project's success criterion is replayability and personality |
