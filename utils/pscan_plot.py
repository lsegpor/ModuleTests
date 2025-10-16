generate_file_summary = True

import pandas as pd
import numpy as np
import re
from scipy import stats
import matplotlib.pyplot as plt


from multiprocessing import Pool, cpu_count, current_process

import mplhep
mplhep.style.use("ATLAS")

from scripts.fit_err_fnc import fit_s_curve
from scripts.fit_err_fnc import err_func

from scripts.plotting import plot_s_curve
from scripts.plotting import plot_linear_fit
from scripts.plotting import plot_histogram

from functions.variables_definition import VariablesDefinition as vd

from tabulate import tabulate

import os
""" Create subfolder for plots """
os.makedirs("images", exist_ok=True)
os.makedirs("logs", exist_ok=True)
os.makedirs("summary", exist_ok=True)


from datetime import datetime

import logging


start_stamp = datetime.now().strftime("%Y_%m_%d:%H")

info_log   = f"logs/{start_stamp}_info.log"
warn_log   = f"logs/{start_stamp}_warn_err.log"
debug_log  = f"logs/{start_stamp}_debug.log"

logger = logging.getLogger("p_scan_analysis")
logger.setLevel(logging.DEBUG)  # capture everything, handlers will filter

# --- Color formatter for console ---
class ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",    # cyan
        "INFO": "\033[32m",     # green
        "WARNING": "\033[33m",  # yellow
        "ERROR": "\033[31m",    # red
        "CRITICAL": "\033[41m", # red background
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)

# --- INFO only file handler ---
info_handler = logging.FileHandler(info_log)
info_handler.setLevel(logging.INFO)
info_handler.addFilter(lambda record: record.levelno == logging.INFO)
info_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# --- WARNING + ERROR file handler ---
logging.captureWarnings(True)
warn_handler = logging.FileHandler(warn_log)
warn_handler.setLevel(logging.WARNING)
warn_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# --- DEBUG only file handler ---
debug_handler = logging.FileHandler(debug_log)
debug_handler.setLevel(logging.DEBUG)
debug_handler.addFilter(lambda record: record.levelno == logging.DEBUG)
debug_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# --- Console handler (everything) ---
class MaxLevelFilter(logging.Filter):
    def __init__(self, max_level):
        self.max_level = max_level
    def filter(self, record):
        return record.levelno <= self.max_level

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.addFilter(MaxLevelFilter(logging.INFO))
console_handler.setFormatter(ColorFormatter('%(asctime)s - %(levelname)s - %(message)s'))

# --- Add handlers to logger ---
for h in (info_handler, warn_handler, debug_handler, console_handler):
    logger.addHandler(h)

logger.propagate = False

logger.info("Loading rules ...")
import inspect
import scripts.rule_set as rule_set
# Get all functions defined in that module
rules = {
    name: obj
    for name, obj in inspect.getmembers(rule_set, inspect.isfunction)
    if obj.__module__ == rule_set.__name__ and name.startswith("rule_")
}
for idx,rule_name in enumerate(rules.keys()):
    logger.info(f"Rule {idx} : {rule_name}")

from multiprocessing import Pool, cpu_count, current_process
cpu_count = cpu_count()

def process_channel(df, adc_list, chn):
    df_channel = df[df["CH_value"] == chn]
    q_score = 0

    if df_channel.empty:
        return None  # in case of missing channels

    x = df_channel['VP_value'].to_numpy()
    y = df_channel[[f"ADC_{adc}" for adc in adc_list]].to_numpy()

    results = {}
    valid_adc_fit = []
    for j in range(y.shape[1]):
        r = fit_s_curve(x, y[:, j], curve_type="erf")
        if r is None:
            logger.warning(f"Channel {chn}, ADC {adc_list[j]} fit failed")
        else:
            # Check all user defined rules
            all_passed = True
            for rule in rules.values():
                if not rule(r):
                    all_passed = False
                    break

            if all_passed:
                valid_adc_fit.append(adc_list[j])

        results[adc_list[j]] = r

    q_score += len(adc_list) - len(valid_adc_fit)

    if len(valid_adc_fit) < 2:
        logger.warning(f"Not enough valid points to perform linear fit for channel {chn}")
    else:
        res = stats.linregress(valid_adc_fit, [results[adc][1] for adc in valid_adc_fit])
        results['linear_fit'] = [res.intercept, res.intercept_stderr, res.slope, res.stderr, res.rvalue, res.pvalue]

    # Append sigma statistics
    sigma_values = np.array([results[adc][0] for adc in valid_adc_fit]).astype(np.float64)

    if len(sigma_values) != 0:
        results['enc'] = [np.mean(sigma_values), np.std(sigma_values), np.min(sigma_values), np.max(sigma_values), np.median(sigma_values), len(sigma_values)]

    results['q_score'] = q_score

    return results

def process_single_p_scan_file(ladder_sn, module_sn, asic_id_str, hw_addr, polarity, pscan_dir, q_lim=68):
    # Looks for the pscan file corresponding to the given asic_id_str
    if not os.path.exists(pscan_dir):
        logger.error(f"Directory {pscan_dir} does not exist")
        return None
    
    files = os.listdir(pscan_dir)
    txt_files = [f for f in files if f.endswith('.txt')]

    # Looks for the pscan file corresponding to the given asic_id_str
    target_file = None
    for f_name in txt_files:
        if asic_id_str in f_name:
            target_file = f_name
            break
    
    if not target_file:
        logger.warning(f"No file found for ASIC ID '{asic_id_str}' in {pscan_dir}")
        return None
    
    logger.info(f"Processing file: {target_file} for ASIC {hw_addr} ({polarity})")

    # Extract number of pulses from filename
    try:
        match = re.search(r"_NP_(\d+)_", target_file)
        if not match:
            raise ValueError(f"No pulse count found in filename: {target_file}")
        n_of_pulses = int(match.group(1))
        logger.info(f"Number of Pulses: {n_of_pulses}")
    except Exception as e:
        logger.warning(f"Failed to extract number of pulses from {target_file}: {e}")
        n_of_pulses = 1

    file_path = f"{pscan_dir}/{target_file}"

    # Extract ADC list from the first line
    try:
        with open(file_path, "r") as f:
            first_line = f.readline().strip()
            match = re.search(r"DISC_LIST:\s*\[(.*?)\]", first_line)
            if not match:
                raise ValueError(f"No DISC_LIST found in {file_path}")
            adc_list = [int(a) for a in match.group(1).split(",")]
    except Exception as e:
        logger.error(f"Error reading ADC list from {target_file}: {e}")
        return None

    # Load the file
    column_names = ["VP_label", "VP_value", "CH_label", "CH_value"] + [f"ADC_{a}" for a in adc_list]
    try:
        df = pd.read_csv(
            file_path,
            sep='\\s+',
            header=None,
            skiprows=1,
            names=column_names
        )
    except pd.errors.ParserError as e:
        logger.error(f"Error parsing file {file_path}: {e}")
        return None

    # Process the dataframe
    df = df.drop('VP_label', axis=1)
    df = df.drop('CH_label', axis=1)
    df["CH_value"] = df["CH_value"].str.rstrip(":").astype(np.int8)

    for adc in adc_list:
        df[f"ADC_{adc}"] = df[f"ADC_{adc}"].astype(np.int16)

    adc_fields = [f for f in df.columns if f.startswith("ADC")]

    # Normalize by number of pulses
    df[adc_fields] = df[adc_fields] / n_of_pulses
    df.loc[:, adc_fields] = df.loc[:, adc_fields].mask(df.loc[:, adc_fields] > 1.1, 1)

    # Process channels
    args = [(df, adc_list[:-1], chn) for chn in range(128)]
    with Pool() as p:
        results = p.starmap(process_channel, args)

    # Filter valid results
    valid_results = [r for r in results if r is not None]
    
    if not valid_results:
        logger.error(f"No valid results for file {target_file}")
        return None

    # Calculate metrics
    linear_fits_data = [r['linear_fit'] for r in valid_results if 'linear_fit' in r]
    
    if not linear_fits_data:
        logger.error(f"No valid linear fits found for file {target_file}")
        return None
        
    linear_fits = np.array(linear_fits_data)
    thre = (linear_fits[:,0] + linear_fits[:,2] * adc_list[-2]) * 350
    gain = linear_fits[:,2] * -350
    
    q_scores = np.array([r['q_score'] for r in valid_results])
    
    enc_data = [r['enc'][0] for r in valid_results if 'enc' in r]
    if not enc_data:
        logger.warning(f"No ENC data found for file {target_file}")
        enc = np.array([0])
    else:
        enc = np.array(enc_data) * 350

    # Calculate Q score
    q_str = f"{np.sum(q_scores)/128:.4f}"
    if np.sum(q_scores) > q_lim:
        q_str = f"{q_str} *** warning ***"

    # Calculate odd/even failed
    channel_q_map = {}
    for i, result in enumerate(results):
        if result is not None:
            channel_q_map[i] = result['q_score']
        else:
            channel_q_map[i] = 1
    
    odd_failed = sum(channel_q_map[i] for i in range(1, 128, 2))
    even_failed = sum(channel_q_map[i] for i in range(0, 128, 2))

    # Generate histograms
    try:
        fig, axs = plt.subplots(1, 2, figsize=(9, 4))
        plot_histogram(thre, 'Thr', "Entries", axs[0])
        plot_histogram(gain, 'gain', "Entries", axs[1])
        plt.tight_layout()
        plt.savefig(f"images/{target_file}_thr_gain.png", dpi=300)
        plt.close()
        logger.info(f"Histogram saved for {target_file}")
    except Exception as e:
        logger.warning(f"Could not save histogram for {target_file}: {e}")

    # Return data row
    result_row = [target_file, hw_addr, polarity] + [x for v in (thre, gain, enc) for x in (np.mean(v), np.std(v))] + [q_str, int(odd_failed), int(even_failed)]
    
    logger.info(f"Successfully processed {target_file}: HW_Addr={hw_addr}, Polarity={polarity}")
    
    return result_row