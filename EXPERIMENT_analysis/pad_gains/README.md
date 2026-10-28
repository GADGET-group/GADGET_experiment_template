# pad_gains

Pad gain maps of the experiment: pickled gain-match results (a `scipy.optimize.OptimizeResult` with an added
`.pad_gains` array, one gain per pad). `EXPERIMENT_runs.get_pad_gain_path` says which file a TPC config uses, and
`get_pad_gains` returns its `.pad_gains`; `get_energy_MeV` multiplies the per-pad charges by them. `.gitignore`
ignores `*.pkl` everywhere except here, so the maps are committed.

## To start

Copy e23035's map made on smart1/hybrid charges, `hybrid_v200_fft6_res3.pkl`, into this folder under the same name,
which is the one `get_pad_gain_path` returns. It is in the e23035 and e25058 experiment repositories at
`<exp>_analysis/pad_gains/hybrid_v200_fft6_res3.pkl`, for example
`/egr/research-tpc/adamsa52/e25058_analysis/e25058_analysis/pad_gains/hybrid_v200_fft6_res3.pkl` on tpcgpu.
Those repositories also have `gm_old/fft6_res3.pkl`, the older map made on smart2 charges, for smart2 configs.

## A map of your own

The library's gain-match scripts are `tpc_data_processing/pad_gain_match/combined_run_gm_fft.py` (Fourier-limited
gain map, the one the maps above came from) and `combined_run_gm.py`; they need a GPU (cupy). Copy one into
`scripts/` rather than editing it in the library, set `exp_runs = [('EXPERIMENT', (run, run, ...))]` and
`TPC_CONFIG`, and adapt the event selections and the energies they are matched to (the copy in the library uses
e23035 preparation runs). The script writes `gain_match_results/fft<N>_res1/2/3.pkl` next to itself; copy the final
`res3` here under a descriptive name and point `get_pad_gain_path` at it.

Friend trees (`run<N>_tpc_<config>_v2.root` in the DDAS folder) store `tpc_energy` made with the pad gains and are
not remade when the map changes: delete them after changing it.
