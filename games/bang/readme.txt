# BANG — CrossFire Gaming

5x5 cluster-pays slot, Wild-West dynamite theme.

## Mechanic
- Symbols pay in clusters of 4+ connected (4-way adjacency).
- Tumble cascade: winning symbols destroyed -> remaining fall -> new fill from top -> repeat until no wins.

## Symbol set
- High pays: H1 (Safe/Vault), H2 (Gold Bar), H3 (Sheriff Badge), H4 (Horseshoe).
- Low pays: L1 (Diamond), L2 (Heart), L3 (Club), L4 (Spade).
- Specials: DS (Small Dynamite — row/column destroyer), DB (Big Dynamite — 3x3 destroyer).
- No wild, no scatter.

## Bonus
- Trigger: 50 destroyed cells in one spin (across full cascade chain).
- Award: 10 free spins with sticky dynamites.
- Bonus buy: 100x bet for guaranteed bonus entry.
- Multiplier mechanic in bonus: TNT-Crate symbols (2x-500x) collected during bonus, summed, applied to total bonus win.

## Math targets
- Base RTP: 96.5%.
- Bonus-buy RTP: 97.0%.
- Volatility: high (9/10).
- Max win: 10,000x bet.

## Scaffold state (C1)
This game is currently at C1 scaffolding stage:
- Symbol set, paytable, board size, bet modes: complete.
- Dynamite area-effect resolution: NOT YET IMPLEMENTED (C2 task).
- DH/DV directional variants: deferred (currently uses single 'DS' board symbol).
- Destruction-count bonus trigger: NOT YET IMPLEMENTED (still uses inherited
  scatter-based trigger; scatters are unreachable so bonus only fires from
  force_freegame in the bonus BetMode).
- Grid-position multipliers from the cluster sample are inherited but
  effectively disabled via maximum_board_mult=1.

Running `make run GAME=bang` should produce books/lookup-tables/index files,
but the math is NOT correct yet — this is a structural scaffold to validate
the pipeline end-to-end before layering in the signature mechanics.

See ../../crossfire-bang/docs/GDD.md for the canonical spec
and ../../crossfire-bang/docs/SDK_NOTES.md for SDK-vs-BANG deltas.
