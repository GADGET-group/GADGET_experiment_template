# EXPERIMENT_analysis

A GADGET II experiment repository holds what is specific to one experiment: its run list (`runs.csv`), DDAS channel
map (`channel_map.csv`), runs module (TPC energy, track length, veto and particle masks, PID cuts), pad gain maps,
gamma calibrations, optional pinned TPC processing configs, and the experiment's own scripts. The processing and
analysis code is the shared library `gadget_analysis` (packages `tpc_data_processing`, `tpc_and_decay_station`,
`analysis_tools`, `main_gui`, `track_fitting`, `fit_gui`, `detector_efficiency`). Every library function takes the
experiment name first and finds the experiment by importing the installed package `<experiment>_analysis` and
reading its folder. This repository starts as a template (gadget_experiment_template); after step 2 below every
placeholder in it, this README included, names your experiment, and the steps stay as the record of how it was set up.

## Setting up a new experiment

1. Copy the template into a fresh repository:
   `git clone <template> eNNNNN_analysis && cd eNNNNN_analysis && rm -rf .git && git init`
2. `python3 rename_experiment.py eNNNNN` (add `-n` for a dry run). It renames the package folder and the runs module
   and replaces the placeholder in every text file, refuses if a target name already exists, and prints what it did.
   Delete `rename_experiment.py` afterwards if you like.
3. Fill `EXPERIMENT_analysis/runs.csv`: one row per GET/DDAS run pairing. The library needs `GET` and `DDAS`; leave
   `GET` blank for DDAS-only runs (background, sources); a DDAS run spanning several GET runs gets several rows. The
   other columns are for your run selectors; add columns as needed (e23035 also has `good tpc data?`,
   `final beam settings?`, `source type`, `source location`).
4. Fill `EXPERIMENT_analysis/channel_map.csv` from the DDAS cabling (format and naming in
   `EXPERIMENT_analysis/channel_map.README.md`): the four required logic channels, the PID detectors, and every
   germanium crystal as `clover_<n><a-d>` with source-calibration slopes and offsets where known.
5. Edit `EXPERIMENT_analysis/EXPERIMENT_runs.py`; `grep -n "TODO(EXPERIMENT)" EXPERIMENT_analysis/EXPERIMENT_runs.py`
   lists the places:
   - `experiment` (already set by step 2);
   - `bad_crystals` (crystals to leave out of the add-back, default `[]`);
   - `CACHE_MAX_GB` (150; optionally `CACHE_KEEP_DAYS`, `CACHE_DIR`);
   - the run selectors in `get_ddas_runs` (a placeholder);
   - the veto thresholds in `get_veto_mask`;
   - the pad gain map: nothing to edit in `get_pad_gain_path`, each config names its map in a `pad_gain_file` row
     (step 6);
   - the PID bands in `get_proton_mask_min_max_range` and `get_alpha_mask_min_max_range`;
   - the PID polygons and variables in `get_pid_cut` and `get_counts_in_pid_cut`.
6. Pad gains: copy the maps the presets name into `EXPERIMENT_analysis/pad_gains/` (`pad_gains/README.md`: e23035's
   `hybrid_v200_fft6_res3.pkl` for the smart1-based presets, `gm_old/fft6_res3.pkl` for the smart2 ones). A map of
   your own gets a config of its own: a copy of a preset in `tpc_processing_configs/` with the map in its
   `pad_gain_file` row.
7. Gas density: set `GAS_PRESSURE_TORR` and `GAS_TEMPERATURE_K` in `EXPERIMENT_runs.py` (`get_gas_density`; make it a
   per-run lookup if they changed during the experiment). The proton and alpha masks and `track_fitting.build_sim`
   use it; e23035 and e25058 ran P10 at 860.3 torr, 20 C. The library README lists the experiment-specific constants
   that still live in the library (mesh-to-trigger delay of the DDAS merge, `zscale`, paths on hosts other than tpcgpu).
8. Put the data in the standard folders on tpcgpu: raw GET files in
   `/egr/research-tpc/shared/experiments/EXPERIMENT/h5/run_NNNN.h5`, the DDAS event-builder files in
   `/egr/research-tpc/shared/proc_runs/EXPERIMENT/ddas/run-NNNN.root`, and create
   `/egr/research-tpc/shared/proc_runs/EXPERIMENT/proc_pkl/` for the processed TPC files.
9. `pip install -e .` in this repository, in the env that has the library installed (`pip install -e .` in the
   library checkout first).
10. `python -c "from gadget_analysis.tpc_and_decay_station import ddas_interface; print(ddas_interface.validate_experiment('EXPERIMENT'))"`
    until it prints `[]`.
11. First processing, merge and histogram (`from gadget_analysis.tpc_data_processing import process_runs`,
    `from gadget_analysis.tpc_and_decay_station import ddas_interface`):
    - process one GET run: `process_runs.process_tpc_run('EXPERIMENT', get_run)` uses `DEFAULT_TPC_CONFIG` from the runs module (`smart1.csv` in the template); pass a config name to try another preset
    - merge one DDAS run and read `run<N>_merge_v2.log` in the DDAS folder: `ddas_interface.make_ddas_root_file('EXPERIMENT', ddas_run)`
    - first histogram: `ddas_interface.get_histogram('EXPERIMENT', ddas_run, (8000, 0, 8000), 'h', 'clover 1a', 'clover_1a_e')`

    Then look at `get_energy_MeV` against `get_length_mm` (range vs energy) and a known line, and check the
    mesh-to-trigger delay of the merge as the library README describes.
12. Gamma gain match: copy e23035's `align_gamma_energies.py` (e23035 experiment repository,
    `e23035_analysis/align_gamma_energies.py`) into `scripts/` and adapt `experiment`, the runs-module import, the run
    selection (`runs_to_align_desc`), the calibration peaks (`gm_label`) and the non-linearity peak list. Run
    `do_gain_match(run)` on one run and look at `EXPERIMENT_analysis/calibrations/<run>/<gm_name>/gain_match.pdf`,
    then `process_all()`, `make_summary_pdf()` and optionally `make_nonlinearity_correction()`.

## Runs-module interface

`EXPERIMENT_analysis/EXPERIMENT_runs.py` must provide (the library calls these with `get_runs` = GET run numbers):

`run_df` (pandas DataFrame from runs.csv, numeric `GET` and `DDAS` columns, one row per GET/DDAS pairing),
`get_energy_MeV(get_runs, tpc_ini_filename="")`, `get_length_mm(get_runs, tpc_ini_filename="")`,
`get_veto_mask(get_runs, tpc_ini_filename="")` (True = keep), `get_proton_mask(...)`, `get_alpha_mask(...)`,
`get_pad_gains(tpc_ini_filename="")`, `DEFAULT_TPC_CONFIG` (the processing config used when a call gives none);
optional `get_pad_gain_path(tpc_ini_filename="")` (both read the config's `pad_gain_file` row through
`process_runs.get_config_pad_gain_file`). The data functions take
`(get_runs, tpc_ini_filename="")` positionally, in that order; any experiment-specific option goes after a `*` as a
keyword-only argument (`validate_experiment` checks this), so calls mean the same for every experiment. Paths inside
the module relative to `Path(__file__).parent`, never the working directory; no degai calls at import time.

Settings the library reads from the module with `getattr`:

| setting | meaning | default |
|---|---|---|
| `experiment` | the experiment name, equal to the package prefix | |
| `bad_crystals` | list of `(clover:int, 'a'..'d')` left out of degai's crystal list | `[]` |
| `CACHE_MAX_GB` | budget of the shared caches; least recently read files are deleted above it | no limit |
| `CACHE_KEEP_DAYS` | files read within this many days are never deleted | 7 |
| `CACHE_DIR` | override of the shared cache root | `/egr/research-tpc/shared/proc_runs/EXPERIMENT/analysis_cache` |

`ddas_interface.validate_experiment('EXPERIMENT')` returns a list of problems (empty = OK): the logic channels
`mesh_pre_amp` 118, `get_trig_accepted` 119, `beam_off` 123 and `chopper_off` 125 in `channel_map.csv`, the
attributes above, the `run_df` columns, and that degai can build the crystal list (every `clover_<n><a-d>` channel).

## Layout

| path | contents |
|---|---|
| `EXPERIMENT_analysis/` | the package the library imports: `__init__.py`, `runs.csv`, `channel_map.csv` (+ `channel_map.README.md`), `EXPERIMENT_runs.py` |
| `EXPERIMENT_analysis/pad_gains/` | pad gain maps (committed `.pkl` files) |
| `EXPERIMENT_analysis/tpc_processing_configs/` | usually empty; a config here overrides the library preset of the same name |
| `EXPERIMENT_analysis/calibrations/`, `nonlinearity_corrections/` | written by the library's gamma gain-match tools |
| `scripts/` | driver scripts, run from the repository root as `python scripts/<name>.py` |
| `pyproject.toml` | the distribution `EXPERIMENT_analysis`, depending on `gadget_analysis` |

## Data and caches on tpcgpu

| data | path |
|---|---|
| raw GET h5 | `/egr/research-tpc/shared/experiments/EXPERIMENT/h5/run_NNNN.h5` |
| processed TPC data | `/egr/research-tpc/shared/proc_runs/EXPERIMENT/proc_pkl/` |
| DDAS data | `/egr/research-tpc/shared/proc_runs/EXPERIMENT/ddas/`: `run-NNNN.root` from the event builder; the merged files and TPC friend trees are written there |
| caches | `/egr/research-tpc/shared/proc_runs/EXPERIMENT/analysis_cache/` (`hist_cache/`, `clarion_cache/`) |

These are the default branches of the library's path functions (`process_runs.get_h5_path`, `get_save_path`,
`ddas_interface.get_root_file_path`, `get_cache_dir`); an experiment that needs other folders needs a branch there
(pull request). Report on the caches (dry run): `python -m gadget_analysis.tpc_and_decay_station.cache_maintenance EXPERIMENT`.

## Rules

- Library changes go to `gadget_analysis` by pull request. Never edit the library in place for one experiment: the
  other experiments share it, and a library checkout with uncommitted changes writes its caches to a private
  `dev_<user>/` folder instead of the shared one.
- Caches are shared by everyone on the experiment and budgeted (`CACHE_MAX_GB`); they live under
  `/egr/research-tpc/shared/proc_runs/EXPERIMENT/analysis_cache/`, never in this repository.
- Calibrations are committed here (`EXPERIMENT_analysis/calibrations/`, `nonlinearity_corrections/`), except ROOT
  files and the per-run PDFs, which `.gitignore` excludes.
- Run Python from the repository root, or anywhere except the folder that contains this clone: there the clone
  folder, also named `EXPERIMENT_analysis`, is imported as a namespace package in place of the installed one.
