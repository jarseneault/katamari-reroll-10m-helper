# North Star 10m Helper (Katamari Damacy REROLL)

**Use it:** https://jarseneault.github.io/katamari-reroll-10m-helper/

`index.html` is a self-contained page (no server needed, just open it). Type the object named on the pause
screen and it shows how many of that object equal a 10 m katamari (or whatever target size you set). It
also works backwards: type the count you see and it tells you your current size.

## How the pause-screen count works (taken from the game's code)

- `PauseMenu.sInit` → `GlobalManager.sInitGetSize(katamariVolume)` picks a random registered object that is
  still in the level and smaller than `0.98 × katamariVolume`. It then displays
  `round(katamariVolume / monoVolume[obj])` (C# `ToString("#")`). Objects within ±2% of the katamari's volume show as 1.
- `katamariVolume` comes from the native `PS2KatamariSimulation.dll`. The HUD diameter is
  `D_cm = 2·(100·∛(3V/4π) + 0.01)`, so 10m00cm0mm ⇔ V ≈ 523.567 m³.
- `monoVolume` (`MonoGetVolume`) is worked out natively from the object's model bounding box:
  `max(ext,0.1)·0.01` for each axis, multiplied together, then multiplied by a per-object factor table in the DLL.
  The model data comes from the mission's `M_21.mono` TextAsset.
- Cross-check: for every object, the game's own `mononame.SIZE` ("pick-up size") equals the diameter of a sphere
  with 10× that object's volume. The only exception is the Truck, which the native code adjusts on purpose.

## Regenerating `data/northstar-objects.json`

The steps used to build the data (run the Python with `-I`, in a venv with `UnityPy TypeTreeGeneratorAPI unicorn pefile`):

1. Decompile `katamari_Data/Managed/Assembly-CSharp.dll` with `ilspycmd -p` (needed for `MonoGroup.cs`).
2. `dump_name_tables.py <game dir> <work>` writes the raw `mononame` and `king_text` MonoBehaviours;
   `parse_name_tables.py <work>` turns them into JSON.
3. `extract_placements.py <game dir> m_21_b <work>/placements.json` reads the AttachableProps in the North Star scene bundle.
4. `extract_mono.py <StreamingAssets>/StandaloneWindows/mission M_21.mono <work>/M_21.mono` extracts the mission model data.
5. `emulate_volumes.py <PS2KatamariSimulation.dll> <work>/M_21.mono <work>/volumes.json 21 1 1 <comma-separated ids>`
   runs the game's native DllMain → `MonoInitStart` → `Init` → `MonoInitAddProp` → `MonoGetVolume` under Unicorn.
6. `build_dataset.py <work> data/northstar-objects.json` applies the pause screen's eligibility rules. It needs
   `<work>/src/MonoGroup.cs` from step 1.
7. `python3 tools/build_site.py` copies the JSON into `index.html`.

## License

The code is MIT licensed (see `LICENSE`). Katamari Damacy REROLL and its object names belong to BANDAI NAMCO
Entertainment. This is an unofficial fan tool. The repository contains only derived numbers and names, with no game files.
