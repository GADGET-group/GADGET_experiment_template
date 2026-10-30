# pad_gains

Pad gain maps of the experiment: pickled gain-match results (a `scipy.optimize.OptimizeResult` with an added
`.pad_gains` array, one gain per pad). Each TPC processing config names its map in a row `pad_gain_file,str,<path>`,
a path relative to this folder; `EXPERIMENT_runs.get_pad_gain_path` resolves it
(`process_runs.get_config_pad_gain_file`), `get_pad_gains` returns its `.pad_gains`, and `get_energy_MeV` multiplies
the per-pad charges by them. `.gitignore` ignores `*.pkl` everywhere except here, so the maps are committed.

## To start

The library presets name `hybrid_v200_fft6_res3.pkl` (smart1-based configs) and `gm_old/fft6_res3.pkl` (smart2
configs). Copy both from the e23035 or e25058 experiment repository, `<exp>_analysis/pad_gains/`, for example
`/egr/research-tpc/adamsa52/e25058_analysis/e25058_analysis/pad_gains/hybrid_v200_fft6_res3.pkl` on tpcgpu. The first
is e23035's map made on smart1/hybrid charges, the second the older map made on smart2 charges.

## A map of your own

The library's gain-match scripts are `tpc_data_processing/pad_gain_match/combined_run_gm_fft.py` (Fourier-limited
gain map, the one the maps above came from) and `combined_run_gm.py`; they need a GPU (cupy). Copy one into
`scripts/` rather than editing it in the library, set `exp_runs = [('EXPERIMENT', (run, run, ...))]` and
`TPC_CONFIG`, and adapt the event selections and the energies they are matched to (the copy in the library uses
e23035 preparation runs). The script writes `gain_match_results/fft<N>_res1/2/3.pkl` next to itself; copy the final
`res3` here under a descriptive name and give it a config of its own: a copy of a preset in `tpc_processing_configs/`
under a new name, with the map in its `pad_gain_file` row.

Friend trees (`run<N>_tpc_<config>_v2.root` in the DDAS folder), `gm_ic` caches and histograms are kept apart by the
config name, so the old and the new map can be compared side by side. A friend tree records the hash of the gains it
was made with, and `ddas_interface.check_friend_provenance` refuses one whose recorded hash differs from the config's
current map (delete the file, it is remade on the next call); so never change the map a config names in place while
its friend trees exist, use a new config name instead.
