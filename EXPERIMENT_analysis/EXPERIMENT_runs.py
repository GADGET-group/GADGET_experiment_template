'''
Runs module of experiment EXPERIMENT: the run list and the TPC quantities, masks and PID cuts the gadget_analysis
library uses. The library imports it as EXPERIMENT_analysis.EXPERIMENT_runs and reads the interface listed in
README.md ("Runs-module interface"); ddas_interface.validate_experiment('EXPERIMENT') checks it.

Every place that must be set for a new experiment is marked TODO(EXPERIMENT). Derived from e25058_runs.py.
Conventions: paths relative to this file (current_dir), never the working directory; import-time work limited to
reading runs.csv; no degai calls at import time.
'''
from pathlib import Path
import os
import pickle

import pandas as pd
import numpy as np
import ROOT
from skimage.measure import points_in_poly

from gadget_analysis.tpc_data_processing import process_runs
from gadget_analysis.tpc_and_decay_station import ddas_interface
from gadget_analysis.track_fitting import srim_interface, build_sim

# TODO(EXPERIMENT): the experiment name; it must match the package name EXPERIMENT_analysis (rename_experiment.py sets
# both). The library also needs a branch for it in track_fitting/build_sim.get_gas_density (README.md, step 7).
experiment = 'EXPERIMENT'

# TODO(EXPERIMENT): germanium crystals to leave out of degai's crystal list, as (clover number, crystal letter), for
# example [(1, 'b'), (3, 'c')]. Every entry must exist in channel_map.csv as clover_<n><a-d>.
bad_crystals = []

# TODO(EXPERIMENT): budget for the shared caches (hist_cache/ + clarion_cache/ under
# /egr/research-tpc/shared/proc_runs/EXPERIMENT/analysis_cache): when a new cache file takes the total above it, the
# least recently read files are deleted, never ones read in the last CACHE_KEEP_DAYS (default 7) days.
# Dry run / report: python -m gadget_analysis.tpc_and_decay_station.cache_maintenance EXPERIMENT
CACHE_MAX_GB = 150
# CACHE_KEEP_DAYS = 7
# CACHE_DIR = '/some/other/folder'   # only to move the caches away from the shared default

current_dir = Path(__file__).parent.resolve()
run_df = pd.read_csv(os.path.join(current_dir, 'runs.csv'))
run_df['GET'] = pd.to_numeric(run_df['GET'], errors='coerce', downcast='integer')
run_df['DDAS'] = pd.to_numeric(run_df['DDAS'], errors='coerce', downcast='integer')
if 'degrader angle' in run_df.columns:
    run_df['degrader angle'] = pd.to_numeric(run_df['degrader angle'], errors='coerce', downcast='float')

def get_ddas_runs(good_gamma, good_low_energy_tpc, good_long_tracks_tpc, final_beam_settings, tpc_data_valid=True):
    '''
    DDAS runs selected by run conditions (placeholder: every DDAS run with a merged file, and with a GET run when
    tpc_data_valid).
    TODO(EXPERIMENT): the run selectors. Filter on the columns of runs.csv ('Run Type', 'Field Cage Functional?',
    'degrader angle', ...) for each argument; the arguments are unused until then.
    '''
    runs = []
    for run, get_run in zip(run_df['DDAS'], run_df['GET']):
        if tpc_data_valid:
            if not np.isfinite(get_run):
                continue
        if np.isnan(run):
            continue

        # TODO(EXPERIMENT): experiment-specific run filters here

        if os.path.exists(ddas_interface.get_ddas_root_file_path(experiment, run)):
            runs.append(run)
    return runs

def is_iterable(obj):
    try:
        iter(obj)
        return True
    except:
        return False

def get_GET_run_number(ddas_run_number):
    if is_iterable(ddas_run_number):
        return np.array([get_GET_run_number(i) for i in ddas_run_number])
    return run_df['GET'][run_df['DDAS']==ddas_run_number].iloc[0]

def get_DDAS_run_number(get_run_number):
    if is_iterable(get_run_number):
        return np.array([get_DDAS_run_number(i) for i in get_run_number])
    return run_df['DDAS'][run_df['GET']==get_run_number].iloc[0]


def get_veto_mask(get_run, tpc_ini_filename=""):
    '''True = keep: no veto pad above its threshold (ADC).'''
    # TODO(EXPERIMENT): veto thresholds per veto pad (e25058: 500 ADC on every veto pad, e23035: 200). Pad 509 is
    # set on its own so that one pad can be given a different threshold.
    veto_thresholds = np.ones(process_runs.raw_h5_file.NUM_PADS)*np.inf
    for pad in process_runs.raw_h5_file.VETO_PADS:
        veto_thresholds[pad] = 500
    veto_thresholds[509] = 500

    if is_iterable(get_run):
        return process_runs.get_veto_mask(experiment, get_run, veto_thresholds, config_filename=tpc_ini_filename)
    return process_runs.get_veto_mask(experiment, [get_run], veto_thresholds, config_filename=tpc_ini_filename)

GAIN_MATCH_DIR = os.path.join(current_dir, 'pad_gains')   # pad gain maps kept with the experiment

def get_pad_gain_path(tpc_ini_filename=""):
    '''
    Pad gain map for a TPC processing config (also the provenance string stored with the friend trees).
    TODO(EXPERIMENT): put the map(s) in pad_gains/ (pad_gains/README.md) and choose them here. One map for every
    config is fine to start. e23035 and e25058 pick by the config's main baseline:
        if process_runs.get_config_background_mode(tpc_ini_filename, experiment=experiment) == 'smart':
            return os.path.join(GAIN_MATCH_DIR, 'hybrid_v200_fft6_res3.pkl')   # smart1 / hybrid configs
        return os.path.join(GAIN_MATCH_DIR, 'gm_old', 'fft6_res3.pkl')          # smart2 configs
    '''
    return os.path.join(GAIN_MATCH_DIR, 'hybrid_v200_fft6_res3.pkl')

def get_pad_gains(tpc_ini_filename=""):
    with open(get_pad_gain_path(tpc_ini_filename), 'rb') as f:
        gain_match_result = pickle.load(f)
    return gain_match_result.pad_gains

def get_length_mm(get_run, tpc_ini_filename=""):
    if not is_iterable(get_run):
        get_run = [get_run]
    return process_runs.get_lengths(experiment, get_run, config_filename=tpc_ini_filename)

def get_energy_MeV(get_run, tpc_ini_filename=""):
    if not is_iterable(get_run):
        get_run = [get_run]
    to_return = []
    for i in get_run:
        to_return.append(process_runs.get_gm_ic(experiment, [i], get_pad_gains(tpc_ini_filename), config_filename=tpc_ini_filename))
    return np.concatenate(to_return)

def get_proton_mask_min_max_range(get_run, energies:np.ndarray):
    '''
    Proton band in the range-energy plane: the SRIM proton range at the gas density of the run, minus 37 mm / plus
    20 mm, with straight lines below 2 MeV (lower edge) and 1 MeV (upper edge).
    TODO(EXPERIMENT): the band margins and break points (e25058 values), checked on a range vs energy plot.
    The SRIM table path is resolved against the library checkout by srim_interface.
    '''
    if not is_iterable(get_run):
        get_run = [get_run]
    stopping_power_path = 'track_fitting/stopping_powers/%s_in_%s.txt'%('1H', 'P10')
    proton_srim_table = srim_interface.SRIM_Table(stopping_power_path, build_sim.get_gas_density(experiment, get_run[0]))
    expected_proton_length = proton_srim_table.get_stopping_distance(energies)
    lower_band = expected_proton_length - 37
    upper_band = expected_proton_length + 20

    x1, x2 = 0.81, 2
    y1 = proton_srim_table.get_stopping_distance(x1)
    y2 = proton_srim_table.get_stopping_distance(x2)-37
    lower_band[energies<x2] = y1 + (y2-y1)/(x2-x1)*(energies[energies<x2]-x1)

    xa, xb = 0.4, 1
    ya = y1 + (y2-y1)/(x2-x1)*(xa-x1)
    yb = proton_srim_table.get_stopping_distance(xb)+20
    upper_band[energies<xb] = ya + (yb-ya)/(xb-xa)*(energies[energies<xb]-xa)
    return lower_band, upper_band

def get_proton_mask(get_run, tpc_ini_filename=""):
    if not is_iterable(get_run):
        get_run = [get_run]
    lengths = get_length_mm(get_run, tpc_ini_filename=tpc_ini_filename)
    energy = get_energy_MeV(get_run, tpc_ini_filename=tpc_ini_filename)
    veto_mask = get_veto_mask(get_run, tpc_ini_filename=tpc_ini_filename)
    lower_band, upper_band = get_proton_mask_min_max_range(get_run, energy)
    return veto_mask & (lengths < upper_band) & (lengths > lower_band)

def get_alpha_mask_min_max_range(get_run, energies:np.ndarray):
    '''
    Alpha band: from 0 to the SRIM alpha range + 30 mm, kept 10 mm below the proton band.
    TODO(EXPERIMENT): the band margins (e25058 values).
    '''
    if not is_iterable(get_run):
        get_run = [get_run]
    stopping_power_path = 'track_fitting/stopping_powers/%s_in_%s.txt'%('4He', 'P10')
    alpha_srim_table = srim_interface.SRIM_Table(stopping_power_path, build_sim.get_gas_density(experiment, get_run[0]))
    expected_alpha_length = alpha_srim_table.get_stopping_distance(energies)
    lower_band = np.zeros(len(energies))
    lower_proton, upper_proton = get_proton_mask_min_max_range(get_run, energies)
    upper_band = np.min([lower_proton-10, expected_alpha_length + 30], axis=0)
    return lower_band, upper_band

def get_alpha_mask(get_run, tpc_ini_filename=""):
    if not is_iterable(get_run):
        get_run = [get_run]
    lengths = get_length_mm(get_run, tpc_ini_filename=tpc_ini_filename)
    energy = get_energy_MeV(get_run, tpc_ini_filename=tpc_ini_filename)
    veto_mask = get_veto_mask(get_run, tpc_ini_filename=tpc_ini_filename)
    lower_band, upper_band = get_alpha_mask_min_max_range(get_run, energy)
    return veto_mask & (lengths > lower_band) & (lengths < upper_band)

pid_cuts = {}
def get_pid_cut(ddas_run, species):
    '''Beam PID cut (ROOT.TCutG) for a species, registered under the name run<N>_<species>_cut.'''
    global pid_cuts
    name = 'run%d_%s_cut'%(ddas_run, species)
    if name in pid_cuts:
        return pid_cuts[name]

    # TODO(EXPERIMENT): this experiment's species and PID polygons (x, y) in the variables set below. The two
    # polygons are e23035's 60Ga and 59Zn cuts, kept only as an example of the format.
    if species == '60Ga':
        points = [(-6.22262e-7,6715.99),(-6.20756e-7,6829.88),(-6.19298e-7,6768.19),(-6.19465e-7,6635.32),(-6.2066e-7,6540.42),(-6.21903e-7,6583.12)]
    elif species == '59Zn':
        points=[(-6.20086e-7,6417.04),(-6.18461e-7,6554.65),(-6.16429e-7,6438.47),(-6.16429e-7,6307.9),(-6.18556e-7,6208.25),(-6.19943e-7,6269.94)]
    else:
        raise ValueError(f'no PID polygon for species {species!r}')
    points.append(points[0])

    timing_offset = 0
    points_arr = np.array(points, dtype=np.float64)
    xs = np.ascontiguousarray(points_arr[:,0], dtype=np.float64) + timing_offset
    ys = np.ascontiguousarray(points_arr[:,1], dtype=np.float64)
    to_return =  ROOT.TCutG(name, len(xs), xs, ys)
    # TODO(EXPERIMENT): PID variables (branches of the merged tree, so the channel names in channel_map.csv)
    to_return.SetVarX("cross_scint_b2_t - db_5_scint_t")
    to_return.SetVarY("msx100_e")
    pid_cuts[name] = to_return
    return to_return

# merged file of the last run get_counts_in_pid_cut opened
current_run = None
current_file = None
current_data = None

def get_counts_in_pid_cut(ddas_run, species):
    global current_run
    global current_file
    global current_data
    if current_run != ddas_run:
        current_run = ddas_run
        current_file = ROOT.TFile(ddas_interface.get_ddas_root_file_path(experiment, ddas_run), 'READ')
        current_data = current_file.Get('merged_data')
    cut = get_pid_cut(ddas_run, species)
    cut_name = 'run%d_%s_cut'%(ddas_run, species)
    # TODO(EXPERIMENT): the same PID variables and multiplicity conditions as get_pid_cut
    return current_data.Draw('msx100_e:(cross_scint_b2_t - db_5_scint_t)', 'cross_scint_b2_m==1 && db_5_scint_m==1 &&msx100_m==1 && %s'%cut_name, 'goff')
