# Location Art Prompts

Ready-to-paste image-generation prompts for the 16 locations that have no painting yet.
Each one is derived from the location's own writing in `game/data/locations.json`
(description, zone, danger, resources), so the art matches the text the player reads.

## How to use

1. Paste the **Style block** and the **Negative prompt** with each location prompt below.
2. Generate at **1512 x 1040** (3:2 landscape) — the same size as the 29 hand-made plates.
3. Save the result as `frontend-godot/assets/locations/<location_id>.png` using the id in each
   heading (`stream_fisher_wharf.png`, `thornwood_hollow.png`, ...).
4. Open the Godot project once so the textures import (Godot writes the `.import` sidecar).
   `python tools/gen_missing_location_art.py --list` should then report 0 gaps, and
   `pytest tests/test_location_artwork.py` proves the id/PNG contract still holds 1:1.
   Dropping a real file over a generated one is permanent: the generator only ever writes
   files that are missing.

### Compose for the crop (important)

The location panel renders art in a wide box (~200px tall) with aspect-cover, so the player
sees roughly the **middle fifth of the frame, full width** — about y 40%-60% of a 1040px
plate. Keep the horizon, the subject and its strongest light inside that central band, and
treat the top and bottom quarters as atmosphere that may be cropped away. Every prompt below
already states its focal band.

### Style block (paste with every prompt)

> Painterly dark-fantasy xianxia landscape, cinematic 3:2 wide shot, digital oil look with
> visible brush edges, muted ink-and-earth base palette with antique-gold accents, strong
> silhouetted forms against luminous atmospheric haze, soft volumetric light, thin mist
> between depth planes, high detail in the middle distance and simplified foreground.
> Serious wuxia tone, no comedy, no modern elements. Colour register: charcoal, iron grey,
> deep jade, river blue, ember orange, antique gold. Subject sits in the middle band of the
> frame with the horizon near the centre line. No text, no captions, no UI, no watermark,
> no border, no signature.

### Negative prompt

> text, letters, calligraphy strokes, watermark, signature, logo, UI, frame, border, modern
> buildings, cars, guns, neon signs, sci-fi, cyberpunk, chibi, cartoon outline, kitsch
> oversaturation, bloom haze, blurry mush, duplicate subject, extra limbs, low contrast grey
> flatness

---

## 1. `stream_fisher_wharf` — Stream Fisher Wharf

*Sky Spill World, story tier 2 · danger 1 · qi 2 · River Carp, Reed Cuttings*

> A weathered timber wharf on a slow river at first light. Flat-bottomed fishing boats tied to
> leaning pilings, wet planks catching a low gold sun, reed banks and a shallow gravel shore
> in the foreground, a small stilted fisher hamlet and misted far bank behind. Two fisherfolk
> mend nets, a harbour cat sits on a piling, ropes and drying carp hang from the beams.
> *Focal band:* the wharf and its moored boats across the middle of the frame, horizon just
> above centre, dawn haze above and water reflection below safe to crop.

## 2. `thornwood_hollow` — Thornwood Hollow

*Sky Spill World, story tier 2 · danger 3 · qi 3 · Thornfruit, Beast Cores*

> A thorn-choked forest hollow beyond a stone gorge: gnarled thorn trees with barbed tangles,
> a narrow trail marked by cloth strips and carved boundary tokens lashed to trunks, a hunter's
> trail-sign cairn, thornfruit in the undergrowth, deep green gloom with shafts of grey-green
> light. Something large has been dragged off the path — bent bracken, claw scars on bark.
> *Focal band:* the marked trail and the thorn thicket walls mid-frame, a pale light shaft
> behind them; canopy and forest floor can be cropped.

## 3. `sky_fortune_outskirts` — Sky Fortune Outskirts

*Sky Fortune Kingdom, story tier 2 · danger 2 · qi 2 · Golden Rice, Roadside Herbs*

> Terraced farmland ringing the outer wall of a fortified capital. Golden rice steps, a
> roadside shrine with a small stone altar and offering ribbons, merchant carts and pilgrim
> figures on a dirt road, oil-lantern posts at the verge, cypress and persimmon trees. The
> city wall and its watchtowers rise hazy in the background under a pale gold afternoon.
> *Focal band:* rice terraces, the road and the wayside shrine across the middle of the frame,
> wall and sky above, field rows below.

## 4. `deepwood_drift_outpost` — Deepwood Drift Outpost

*Sky Spill World, story tier 3 · danger 4 · qi 4 · Deepwood Herbs, Hunter Trophies*

> A palisade trading outpost hacked into the heart of an old-growth forest at dusk. Spiked
> timber wall with a lantern-lit gate, market stalls and drying racks under canvas, pelts and
> herb bundles, a hunter's trophy pole, deepwood trees towering beyond. Warm lantern pools of
> light on wet ground, cold blue dusk above the tree line.
> *Focal band:* the lit gate and stalls mid-frame with the palisade wall; sky and forest floor
> crop away.

## 5. `seven_profound_low_peaks` — Seven Profound Low Peaks

*Seven Profound Valleys, story tier 3 · danger 4 · qi 5 · Cloud Pool Dew, Spirit Stones*

> The outer peaks of a sect's trial range at dawn: sharp crags rising above a sea of cloud,
> shallow rock pools gathering dew on a stone terrace, a rope bridge and stone stair between
> pinnacles, two distant disciples sparring on a ledge. Almost nothing of the valley floor is
> visible — only cloud and crag.
> *Focal band:* the cloud-pool terrace and sparring ledge across the middle of the frame with
> peaks breaking through mist above.

## 6. `valleys_hidden_market` — Valleys Hidden Market

*Seven Profound Valleys, story tier 3 · danger 3 · qi 4 · Gambling Slips, Spirit Stones*

> A black market strung through a narrow canyon that only appears when the fog thins. Lantern
> strings between canyon walls, cloth stalls of alchemy bottles and rolled technique slips,
> a gambling table under a paper canopy, hooded buyers on stone steps. Fog pours in low between
> the stalls; the night is lit only by lantern warmth and one open brazier.
> *Focal band:* the lantern-lit stalls and gambling table mid-frame between the dark canyon
> walls.

## 7. `cloud_terrace_village` — Cloud Terrace Village

*South Horizon Region, story tier 3 · danger 2 · qi 3 · Terrace Rice, Mountain Herbs*

> A mountain village on a green shoulder in morning light: rice terraces stepping down in
> flooded silver-green contours, stilted farmhouses with dark tiled roofs, a small riverside
> shrine with a stone spirit tablet and prayer flags, a stone arch bridge over a fast stream,
> folded peaks behind and cloud in the valleys.
> *Focal band:* terraces, bridge and shrine across the middle of the frame with the river
> catching light; sky and terrace steps safe to crop.

## 8. `pearl_pavilion` — Pearl Pavilion

*Southern Sea, story tier 4 · danger 4 · qi 5 · Sea Pearls, Tide Herbs*

> A floating pavilion of white coral and pearl gauze at dusk, moored over a calm tide by heavy
> ancient chains, gauze curtains and paper lanterns stirring in the wind. Pearler boats and a
> pirate envoy's black-hulled skiff stand off at polite distance, pearl baskets and tide herbs
> on the coral deck. Moon path on the water, sea haze on the horizon.
> *Focal band:* the pavilion and its lantern glow mid-frame, chains and reflections below,
> sky above.

## 9. `tidecrook_cove` — Tidecrook Cove

*Southern Sea, story tier 4 · danger 5 · qi 4 · Salvage, Beast Cores*

> A crooked pirate harbour where hulls are careened on wet sand between black rocks. Bonfires
> burning in iron drums, loot spread on sailcloth, a chalked duelling ring, crooked jetty
> shacks with stolen banners, masts and rigging leaning against a dusk sky. Ships of salvage
> anchored in the cove mouth; spray against the cliff.
> *Focal band:* bonfires, beached hulls and the duelling ring across the middle of the frame.

## 10. `coral_prison_atoll` — Coral Prison Atoll

*Southern Sea, story tier 4 · danger 6 · qi 6 · Black Coral, Sunken Relics*

> A drowned prison built into a ring of black-coral towers rising from a reef in a hard grey
> squall. Barred cell windows stand half-submerged, chains and rusted grates at the waterline,
> spray bursting against the coral, rain sheets veiling the far towers. Cold storm light,
> no warmth anywhere; beyond the bars, a faint inner glow.
> *Focal band:* the coral towers and their barred windows mid-frame above a breaking sea.

## 11. `sea_of_mist_expanse` — Sea of Mist Expanse

*Southern Sea, story tier 4 · danger 5 · qi 5 · Mist Condensate, Deep-Sea Herb*

> Open ocean swallowed by a white void of fog. A single small boat with one lantern, its
> compass useless, wake vanishing after a few metres; the sea surface half-visible, dark reef
> heads breaking the fog like teeth. Pale diffused light, vertiginous emptiness, the fog
> carrying a faint electric shimmer as if memory of lightning.
> *Focal band:* the lone boat and the nearest reef heads in the middle of the frame, fog
> filling everything else — deliberately the emptiest composition in the set.

## 12. `furnace_pillar_city` — Furnace Pillar City

*Central Region, story tier 5 · danger 6 · qi 6 · Spirit Steel, Forge Salamander Cores*

> A forge city at night: monumental vents of everburning flame rising between tiered workshops,
> chimneys streaming ember-lit smoke, gantries and hoists over quenching canals, spirit-steel
> ingots glowing on racks. Tiered pagoda workshops crowd the slopes; the whole valley floor is
> bathed in orange forge light under a smoke-dark sky.
> *Focal band:* the burning pillars and forge district skyline across the middle of the frame.

## 13. `emberfall_citadel` — Emberfall Citadel

*Central Region, story tier 5 · danger 7 · qi 6 · War Spoils, Blood Crystals*

> A war fortress of black basalt with ash falling like slow snow. Battlements and siege-battered
> towers, war pavilions and drilling grounds outside the gate, war banners stiff in the wind,
> a chalked duelling ring before the barbican with two figures facing off, embers rising from
> braziers. Cold steel light against hot ember accents, no colour in the sky but grey.
> *Focal band:* the gate, duelling ring and pavilions across the middle of the frame with the
> curtain wall behind.

## 14. `zen_wilds_shrine` — Zen Wilds Shrine

*Great Zen Region, story tier 5 · danger 5 · qi 7 · Zen Heart Herbs, Bell Bronze*

> A chain of abandoned mountain shrines climbing into a high wild valley in thin cold dawn
> light: weathered stone stairs, tiled shrine roofs, a great bronze bell on a timber frame,
> votive tablets and moss, a single monk sweeping a path no pilgrim uses. Pines and cloud
> between the buildings; beasts absent, bells untouched.
> *Focal band:* the shrine rooflines, bell frame and the sweeping monk across the middle of
> the frame.

## 15. `rune_temple_undercroft` — Rune Temple Undercroft

*Five Element Region, story tier 6 · danger 8 · qi 8 · Rune Stones, Elemental Cores*

> A buried rune-hall beneath an elemental temple: carved stone circuitry running along the floor
> and up the pillars, glowing slowly through the five elements — ember orange, jade, river
> blue, gold, pale violet — a shallow reflecting pool at the centre with runes burning under
> the surface, broken statues and a warden's silhouette standing where the light crosses the
> hall. Pervading darkness, only the circuits light anything.
> *Focal band:* the central pool and the elemental circuits across the middle of the frame.

## 16. `gate_array_approach` — Gate Array Approach

*Ascension Gate, story tier 6 · danger 9 · qi 9 · Starlight Condensate, Ascension Gate Reeds*

> The last stair to a planetary ascension gate: a long stone stair rising out of frame through
> drifting star-fields, great concentric rings of rune-glyph stone hanging in the void and
> turning slowly, ancient pillars flanking the stair, gate reeds glowing at the verges, a lone
> ascending cultivator a tiny figure halfway up. Deep indigo and violet void, pale starlight,
> no ground but the stair. The most awe-scaled composition in the set.
> *Focal band:* the gate rings and the stair's mid-run across the middle of the frame.

---

## Reference: the 16 ids

| # | location_id | display name | zone | story tier |
|---|---|---|---|---|
| 1 | `stream_fisher_wharf` | Stream Fisher Wharf | Sky Spill World | 2 |
| 2 | `thornwood_hollow` | Thornwood Hollow | Sky Spill World | 2 |
| 3 | `sky_fortune_outskirts` | Sky Fortune Outskirts | Sky Fortune Kingdom | 2 |
| 4 | `deepwood_drift_outpost` | Deepwood Drift Outpost | Sky Spill World | 3 |
| 5 | `seven_profound_low_peaks` | Seven Profound Low Peaks | Seven Profound Valleys | 3 |
| 6 | `valleys_hidden_market` | Valleys Hidden Market | Seven Profound Valleys | 3 |
| 7 | `cloud_terrace_village` | Cloud Terrace Village | South Horizon Region | 3 |
| 8 | `pearl_pavilion` | Pearl Pavilion | Southern Sea | 4 |
| 9 | `tidecrook_cove` | Tidecrook Cove | Southern Sea | 4 |
| 10 | `coral_prison_atoll` | Coral Prison Atoll | Southern Sea | 4 |
| 11 | `sea_of_mist_expanse` | Sea of Mist Expanse | Southern Sea | 4 |
| 12 | `furnace_pillar_city` | Furnace Pillar City | Central Region | 5 |
| 13 | `emberfall_citadel` | Emberfall Citadel | Central Region | 5 |
| 14 | `zen_wilds_shrine` | Zen Wilds Shrine | Great Zen Region | 5 |
| 15 | `rune_temple_undercroft` | Rune Temple Undercroft | Five Element Region | 6 |
| 16 | `gate_array_approach` | Gate Array Approach | Ascension Gate | 6 |
