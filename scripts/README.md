# scripts

Driver scripts of the experiment: plots, fits, gain matches, and adapted copies of library or other experiments'
scripts (for example e23035's `align_gamma_energies.py` or the library's pad gain-match script). Run them from the
repository root:

```bash
python scripts/<name>.py
```

Scripts import the library (`from tpc_data_processing import process_runs`, `from tpc_and_decay_station import
ddas_interface`, ...) and the experiment package (`from EXPERIMENT_analysis import EXPERIMENT_runs`), both installed
with `pip install -e`. `scripts/` is not a package: a script that imports another one, or an interactive driver
that reloads one with `importlib`, is run as `python -m scripts.<name>` (or from IPython started in the repository
root) so that `scripts.<other>` can be found.

Code that every experiment could use belongs in the library (pull request to `gadget_analysis`), not here.
