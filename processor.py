import numpy as np
import scipy.fft
import pandas as pd
from io import StringIO

def file_opener(file_path, sr):
    """
    Reads a file from the provided file path, processes the data into a pandas DataFrame and then a NumPy array.

    Args:
        file_path (string): The path to the file to be read
        sr (int): The sampling rate of the data

    Returns:
        np.array: The imported data
        int: The number of rows in the data
        int: The number of columns in the data
        int: The number of NaN values changed to 0s in the data
    """
    with open(file_path, 'r', encoding='iso-8859-1') as f:
        lines = f.readlines()

    first_data_line = next((i for i, line in enumerate(lines) if all(c.isdigit() or c.isspace() or c=='.' or c=='-' for c in line.strip())), 0)


    data_str = ''.join(lines[first_data_line:])


    df = pd.read_csv(StringIO(data_str), sep="\t", header=None)


    df = df.drop(df.columns[0], axis=1)
    

    num_nan_values = df.isna().sum().sum()
    
  
    df.fillna(0, inplace=True)
    

    data = df.to_numpy().astype(float)
    
    time_array = np.arange(0, data.shape[0]/sr, 1/sr)
    data = np.insert(data, 0, time_array, axis=1)

    return data, data.shape[0], data.shape[1], num_nan_values

def filter(timeseries,sr):
    """
    Apples a Fourier Transform to the timeseries and removes frequencies 
    below 0.5Hz and above 15Hz. Then converts the data back to the time domain.

    Args:
        timeseries (np.array): The timeseries data to be filtered
        sr (int): The sampling rate of the timeseries data

    Returns:
        np.array: The filtered timeseries data
    """
    ts = 1/sr
    time_sample = timeseries[:,0]
    data_sample = timeseries[:,1]
    sig_fft = scipy.fft.fft(data_sample)
    sample_freq = scipy.fft.fftfreq(data_sample.size, d=ts)
    # Filtering

    mask = (np.abs(sample_freq) < 0.5) | (np.abs(sample_freq) > 15)
    sig_fft[mask] = 0
    filtered_signal = np.real(scipy.fft.ifft(sig_fft))

    time_series = np.column_stack((time_sample, filtered_signal))
    return time_series

def signal_to_noise(clean_time_series, noisy_time_series):
    """
    Calculates the signal-to-noise ratio of the provided time-series data.

    Args:
        clean_time_series (np.array): The clean timeseries data
        noisy_time_series (np.array): The noisy timeseries data

    Returns:
        int: the signal to noise ratio
    """
    noise = noisy_time_series - clean_time_series
    return 20 * np.log10(np.linalg.norm(clean_time_series) / np.linalg.norm(noise)) if np.any(noise) else float("inf") 


def find_r_peaks(timeseries,sample_rate = 1000,sample_length_mult = 1, step_length_mult = 0.5):
    """
    Detects R-peaks in the filtered signal using a two-stage process based on threshold values. 
    R-peaks are specific points of interest in an ECG signal. 
    he function also implements a chunking strategy to improve peak detection.

    Args:
        timeseries (np.array): The timeseries data to be filtered
        sample_rate (int, optional): The sample rate of the data. Defaults to 1000.
        sample_length_mult (int, optional): The factor of the sampling rate in each chunked portion (1 = 1 second per chunk). Defaults to 1.
        step_length_mult (float, optional): The factor of the sampling rate that is stepped through int he chunk. Defaults to 0.5.

    Returns:
        np.array: The time-domain location and voltages of the R Peaks.
    """
    time_sample = timeseries[:,0]
    data_sample = timeseries[:,1]

    sample_length = int(sample_rate * sample_length_mult)
    step_length = int(sample_rate * step_length_mult)

    all_times = []
    all_volts = []
    indices = np.arange(0,len(time_sample)-(sample_length-step_length),step_length)
    for idx in indices:
        time_chunk = time_sample[idx:idx+sample_length]
        data_chunk = data_sample[idx:idx+sample_length]
        
        max_val = np.max(data_chunk)
        peaks_1, _ = scipy.signal.find_peaks(data_chunk, height = max_val*0.8)

        if (len(data_chunk[peaks_1]) != 0):
            mean_val = np.mean(data_chunk[peaks_1])
            peaks, _ = scipy.signal.find_peaks(data_chunk, height = mean_val*0.8)

            times = time_chunk[peaks]
            volts = data_chunk[peaks]

            # Collect the results from this chunk
            all_times.extend(times)
            all_volts.extend(volts)
    # Convert back to arrays for convenience
    all_times = np.array(all_times)
    all_volts = np.array(all_volts)
    result = np.column_stack((all_times, all_volts))
    _, idx = np.unique(result[:, 0], return_index=True)

    # Use these indices to select rows with unique values in the first column
    unique_rows = result[np.sort(idx)]
    unique_rows = r_peaks_filter(unique_rows)
    return unique_rows

# The above code is the filter for the r peaks. It takes a list of r peaks, and uses the time difference between each peak to determine if it needs to be removed or if there are any missing peaks.
# If the time difference between two peaks is too small, the code looks at the voltage of the peaks and removes the one with the lower voltage.
# If the time difference between two peaks is too large, the code looks for missing peaks in between the two peaks and adds them to the list of r peaks.

def r_peaks_filter(r_peaks_list):
    """
    Filters out R-peaks that are too close together in time, based on a threshold. 
    This is to ensure that the detected peaks are not artifacts or noise, but represent real heartbeats.

    Args:
        r_peaks_list (np.array): The list of r peaks to be filtered
    Returns:
        np.array: The filtered list of r peaks
    """
    timestamps = r_peaks_list[:, 0]
    voltages = r_peaks_list[:, 1]
    
    time_diffs = np.diff(timestamps)
    lower_threshold = np.mean(time_diffs) - np.std(time_diffs)

    i = 1
    while i < len(timestamps):
        if timestamps[i] - timestamps[i-1] < lower_threshold:
            if voltages[i] > voltages[i-1]:
                r_peaks_list = np.delete(r_peaks_list, i-1, axis=0)
            else:
                r_peaks_list = np.delete(r_peaks_list, i, axis=0)

            timestamps = r_peaks_list[:, 0]
            voltages = r_peaks_list[:, 1]
        else:
            i += 1  

    return r_peaks_list

def divide_by_chunks(pulse_series, sr, sr_multiple=5):
    """
    Divides the time-series data into chunks where the pulse amplitude exceeds a threshold.

    Args:
        pulse_series (np.array): The pulse column of the dataset
        sample_rate (int): The sample rate of the data
        thresh (int, optional): The minimum length of a chunk as a factor of the 
        sample rate to be considered a chunk. Defaults to 5000.

    Returns:
        np.array: The indices of the start and end of each chunk. 
    """
    thresh = int(sr * sr_multiple)
    max_pulse = np.max(pulse_series)
    results = []
    curr_start = 0
    in_pulse = False
    for i in range(len(pulse_series)):
        if pulse_series[i] > 0.9*max_pulse and in_pulse == False:
            if (i - curr_start) > thresh:
                results.append((curr_start,i))
            curr_start = i
            in_pulse = True 
        elif pulse_series[i] < 0.9*max_pulse and in_pulse == True:
            if (i - curr_start) > thresh:
                results.append((curr_start,i))
            curr_start = i
            in_pulse = False
        elif i == len(pulse_series) -1:
            results.append((curr_start,i))
    return results 
