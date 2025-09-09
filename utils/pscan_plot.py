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


from multiprocessing import Pool, cpu_count, current_process
cpu_count = cpu_count()

def process_channel(df, adc_list, chn):
    max_chi2 = 0.1
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
            if r[-1] < 0.05:
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

def process_p_scan_files(ladder_sn, module_sn, files_idx=None, q_lim=68):
    # Relative route from utils/ to pscanfiles/
    source_dir = os.path.join("..", "..", "..", "..", "..", "..", "cbmsoft", 
                             "emu_test_module_arr", "python", "module_files", 
                             ladder_sn, module_sn, "pscan_files")
    
    print(f"🔍 DEBUG: Searching in directory: {source_dir}")
    
    # Verify the directory exists
    if not os.path.exists(source_dir):
        print(f"❌ DEBUG: Directory {source_dir} does not exist for ladder {ladder_sn}, module {module_sn}")
        logger.error(f"Directory {source_dir} does not exist")
        return
    
    print(f"✅ DEBUG: Directory found")

    files = os.listdir(source_dir)
    print(f"📁 DEBUG: {len(files)} files found in total")

    txt_files = [f for f in files if f.endswith('.txt')]
    print(f"📝 DEBUG: {len(txt_files)} .txt files found")
    
    if not txt_files:
        print(f"⚠️ DEBUG: No .txt files found in {source_dir}")
        return None

    # Show some example files
    for i, f in enumerate(txt_files[:3]):
        print(f"📋 DEBUG: File {i+1}: {f}")

    table_values = []

    if files_idx is not None:
        files = [files[idx] for idx in files_idx]
        print(f"🎯 DEBUG: Processing only selected files: {files_idx}")
    else:
        files = txt_files
        print(f"🎯 DEBUG: Processing all .txt files")

    for f_name in files:

        """ Search the number of injected pulses in the filename
            If not found, assume 1 pulse, so the normalization will not change the data
        """
        try:
            match = re.search(r"_NP_(\d+)_", f_name)
            if not match:
                raise ValueError(f"No pulse count found in filename: {f_name}")
            n_of_pulses = int(match.group(1))
            logger.info(f"File: {f_name}\nNumber of Pulses: {n_of_pulses}\n")
        except Exception as e:
            logger.warning(f"Failed to extract number of pulses from {f_name}: {e}")
            n_of_pulses = 1

        file_path = f"{source_dir}/{f_name}"

        """ Search for ADC list in the first line of the file """
        try:
            with open(file_path, "r") as f:
                first_line = f.readline().strip()
                match = re.search(r"\[(.*?)\]", first_line)
                if not match:
                    raise ValueError(f"No ADC list found in {file_path}")
                adc_list = [int(a) for a in match.group(1).split(",")]
        except Exception as e:
            logger.error(f"{e}")
            continue  # Skip this file if extraction fails

        # Load the file, skipping the first line
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
            continue

        df = df.drop('VP_label', axis=1)
        df = df.drop('CH_label', axis=1)

        df["CH_value"] = df["CH_value"].str.rstrip(":").astype(np.int8)

        for adc in adc_list:
            df[f"ADC_{adc}"] = df[f"ADC_{adc}"].astype(np.int16)


        adc_fields = [f for f in df.columns if f.startswith("ADC")]

        """ Normalize by number of injected pulses avoid oveflow
            Additionally, ensure nromalization for the s-curve fit
            effectively decreasing the numer of fit parameters """
        df[adc_fields] = df[adc_fields] / n_of_pulses

        """ Remove double pulse injection by seting large values to 1
            Amplitude of measured signal cannot be largert than the number of injected pulses
        """
        df.loc[:, adc_fields] = df.loc[:, adc_fields].mask(df.loc[:, adc_fields] > 1.1, 1)

        args = [(df, adc_list[:-1], chn) for chn in range(128)]
        with Pool() as p:
            results = p.starmap(process_channel, args)

        linear_fits = np.array([r['linear_fit'] for r in results if 'linear_fit' in r])

        thre = (linear_fits[:,0] + linear_fits[:,2] * adc_list[-2]) * 350
        gain = linear_fits[:,2] * -350
        q_scores = np.array([r['q_score'] for r in results if 'q_score' in r])

        enc = np.array([r['enc'] for r in results if 'enc' in r]) *350

        q_str = f"{np.sum(q_scores)/128:.4f}"
        if np.sum(q_scores) > q_lim:
            q_str = f"{q_str} *** warning ***"
        table_values.append([f_name] + [x for v in (thre, gain, enc) for x in (np.mean(v), np.std(v))] + [q_str, int(np.sum(q_scores[1::2])), int(np.sum(q_scores[::2]))])

        # if generate_file_summary:
        #     labels = ['Empty Channel']
        #     values = [np.sum(1 for r in results if r is None)]

        #     with open(f"summary/{f_name}_summary.txt", "w") as summary_file:
        #         for label, value in zip(labels, [f_name] + list(thre) + list(gain) + list(enc) + [q_str]):
        #             summary_file.write(tabulate(values, headers=labels, tablefmt='simple', floatfmt=".3f"))


        if True:
            # for chn, r in enumerate(results):
            #     plot_s_curve(chn, adc_list[:-1], r, df)
            #     plot_linear_fit(chn, r)

            fig, axs = plt.subplots(1, 2, figsize=(9, 4))
            h_thre = plot_histogram(thre, 'Thr', "Entries", axs[0])
            h_gain = plot_histogram(gain, 'gain', "Entries", axs[1])
            plt.tight_layout()
            plt.savefig(f"images/{f_name}_thr_gain.png", dpi=300)
            plt.close()

    table_labels = ['File', 'Thr (e)', 'Thr_std (e)', 'Gain (e/LSB)', 'Gain_std (e/LSB)', 'ENC (e)', 'ENC_std (e)', 'Q_score', 'Odd_failed', 'Even_failed']
    logger.info(f"Summary:\n{tabulate(table_values, headers=table_labels, tablefmt='simple', floatfmt='.0f')}")