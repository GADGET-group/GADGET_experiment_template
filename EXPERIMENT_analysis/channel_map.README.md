# channel_map.csv

The DDAS channel map of the experiment. `ddas_interface.make_ddas_root_file` turns every row into branches of the
merged tree `merged_data`, `degai` builds its germanium crystal list from it, and
`ddas_interface.validate_experiment('EXPERIMENT')` checks it.

```
Index,Name,Slope,Offset
118, mesh_pre_amp, 1.000000, 0.000000
48, clover_1a, 0.190140, 5.332810
```

- The first line is a header and is skipped. Rows are split on `", "` (a comma followed by one space): keep that
  spacing, and no comment lines.
- `Index` is the DDAS channel, 16 x module + channel (0-159): the position in the event builder's 160-channel
  arrays. Module 3 channel 0 is 48.
- `Name` becomes the branch prefix in `merged_data`: `<name>_e` (keV, 0 when the channel did not fire), `<name>_t`
  (s, NaN when it did not fire), `<name>_m` (multiplicity), `<name>_c` (raw ADC) and `<name>_cr` (raw ADC plus a
  uniform random number in [-0.5, 0.5]). Use lower case and underscores.
- `Slope`, `Offset`: keV = slope x ADC + offset, from a source calibration; slope 1 and offset 0 mean uncalibrated.
  They are applied to `_e` when the merged file is made and seed the gamma gain-match peak search; `_c` and `_cr`
  stay raw ADC. A changed slope reaches `_e` only after the merged file is deleted and remade.

## Required rows

The library's logic channels are fixed numbers (`ddas_interface.CH_MAP`); the cabling must put them there:

| Index | Name |
|---|---|
| 118 | `mesh_pre_amp` |
| 119 | `get_trig_accepted` |
| 123 | `beam_off` |
| 125 | `chopper_off` |

`CH_MAP` also has `sca_logic` 120, `veto_logic` 121, `beam_on` 122 and `chopper_on` 124; add them when they are
cabled.

## Germanium crystals

Every CLARION crystal is a row named `clover_<n><a-d>`: `n` is the CLARION detector number (1-24, as in the
library's `tpc_and_decay_station/clarion_det_locations.csv`), and `a`-`d` are its crystals 1-4. `degai` finds the
crystals by this name pattern; crystals listed in the runs module's `bad_crystals` are left out.

## The example rows

`clover_1a` (48), the beam PID channels `cross_scint_b2` (13), `db_5_scint` (16) and `msx100` (128) are the e23035 and
e25058 cabling with slope 1 and offset 0, kept as examples: replace them with this experiment's cabling and
calibration. The PID helpers (`get_pid_cut` in the runs module and the library's `ddas_interface.show_pid`) use
`msx100_e` against `cross_scint_b2_t - db_5_scint_t`.
