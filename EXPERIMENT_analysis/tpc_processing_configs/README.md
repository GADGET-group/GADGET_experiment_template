# tpc_processing_configs

Usually empty. TPC processing configs are used by name, for example
`process_runs.process_tpc_run('EXPERIMENT', run, 'smart1_veto2_rpr_fzp.csv')`, and the library's presets in its
`tpc_data_processing/tpc_processing_configs/` are what that name finds.

Put a config here only

- to pin a copy: processed files are named after the config name, not its content, so a preset that later changes
  in the library would no longer describe your processed files; or
- to add a variant the presets lack.

A file here with the same name as a preset overrides the preset for this experiment, and the library prints a
warning when the two differ (`process_runs.get_config_path`).
