from PyQt5.QtWidgets import QComboBox, QCheckBox, QDialogButtonBox, QFormLayout, QLabel, QVBoxLayout,  QDialog, QMessageBox, QPushButton, QApplication
import processor as p 
import numpy as np

class PulseSettingsDialog(QDialog):
    """This class creates a QDialog that allows the user to specify various 
        settings for analyzing ECG data. The user can specify which columns of the data file contain 
        the ECG data and the pulse data respectively, and whether the data should be filtered. 
        This is done via two QComboBox widgets for selecting the ECG and pulse data columns, and 
        a QCheckBox for specifying whether filtering is needed. There are also "OK", "Cancel", 
        and "Quit" buttons, and functions to handle changes in the selected ECG and pulse data columns.

    Args:
        QDialog (PyQt Dialog): This class inherits from the PyQt QDialog class.
    """
    def __init__(self, file_name=None, file_width=None, parent=None):
        super(PulseSettingsDialog, self).__init__(parent)
        self.setWindowTitle("Settings")
        self.ecg_column = 1
        self.pulse_column = 4
        self.file_label = QLabel(f"File: {file_name}")
        self.need_filtering_checkbox = QCheckBox("Filter this data?", self)

        if file_width is None or file_width < 1:
            raise ValueError("Invalid file width.")

        self.ECGColumnDropdown = QComboBox()
        for i in range(1, file_width):
            self.ECGColumnDropdown.addItem(f"{i}")
        self.ECGColumnDropdown.currentIndexChanged.connect(self.ecg_index_changed)

        self.pulseColumnDropdown = QComboBox()
        for i in range(1, file_width):
            self.pulseColumnDropdown.addItem(f"{i}")
        self.pulseColumnDropdown.currentIndexChanged.connect(self.pulse_index_changed)

        form_layout = QFormLayout()
        form_layout.addRow("Column with ECG Data", self.ECGColumnDropdown)
        form_layout.addRow("Column with Pulse", self.pulseColumnDropdown)
        form_layout.addRow(self.need_filtering_checkbox)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        quit_button = QPushButton('Quit', self)
        quit_button.clicked.connect(QApplication.quit)
        button_box.addButton(quit_button, QDialogButtonBox.RejectRole)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.file_label)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)

    def get_values(self):
        return (
            self.need_filtering_checkbox.isChecked(),
            self.ecg_column,
            self.pulse_column
        )

    def ecg_index_changed(self, i):
        """This function is called when the user changes the selected ECG data column. It updates the
        column number attribute of the dialog.

        Args:
            i (index): The index of the selected ECG data column.
        """
        self.ecg_column = i + 1

    def pulse_index_changed(self, i):
        self.pulse_column = i + 1
            
def pulse_settings_pane(self):
    """
    Opens a settings dialog for the user to configure pulse settings, handles exceptions and
    interacts with the main window to reflect the settings selected by the user.

    This function is a method in the MainWindow class. It's called when the user wants to 
    configure the pulse settings. The function opens a PulseSettingsDialog, retrieves 
    values from it, and configures the MainWindow according to these values. It also handles 
    exceptions, showing warning messages to the user if something goes wrong.

    Args:
        self (MainWindow instance): A reference to the MainWindow object, where the function is called.

    Raises:
        ValueError: If the selected ecg_column or pulse_column is less than 1, or if the inputs for sr, 
                    ecg column and pulse column are not valid numbers.
        FileNotFoundError: If the selected file does not exist.

    Side effects:
        Changes the configuration of the MainWindow according to user's input.
        Calls QMessageBox to show warning messages to the user if something goes wrong.
        Calls run_data_analysis if all inputs are valid and accepted.
    """
    try:
        dialog = PulseSettingsDialog(self.file_path, self.file_width, self)
        result = dialog.exec()
    except Exception:
        QMessageBox.warning(self, "An Error Occured", "Please try again.")
        self.select_file()
    if result == QDialog.Accepted:
        try:
            selected_filtering, ecg_column, pulse_column = dialog.get_values()
            if ecg_column < 1 or pulse_column < 1:
                raise ValueError("Invalid column selection.")
            self.selected_filtering = selected_filtering
            self.ecg_column = ecg_column
            self.pulse_column = pulse_column
            self.overlay_toggle_button.setEnabled(True)
            if self.selected_filtering:
                self.overlay_toggle_button.setText("Overlay Original Signal")
                self.is_filtered = True
                self.title = "R Peaks Detected From a Fourier Transform of the Orignal Signal"
            else:
                self.overlay_toggle_button.setText("Overlay Filtered Signal")
                self.is_filtered = False
                self.title = "R Peaks Detected from the Orignal Signal"
        
            self.scrollable_window.canvas.figure.suptitle(self.title)
            self.scrollable_window.canvas.draw()
            run_data_analysis(self)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers for the sr, ecg column and pulse column.")
            pulse_settings_pane(self)
        except FileNotFoundError:
            QMessageBox.warning(self, "File Not Found", "Please select a file before exiting the settings pane.")
            pulse_settings_pane(self)
    else:
        QMessageBox.warning(self, "No Changes Made", "You have closed the settings pane without making any changes.")
        pulse_settings_pane(self)

def run_data_analysis(self):
    """
    Perform data analysis on the selected file data by applying filters, 
    dividing by chunks and finding r_peaks.
    
    This function operates on the MainWindow class. It prepares raw and filtered 
    time series from the file data, divides the pulse time series into segments,
    detects R-peaks in the time series, and handles the results of data analysis.

    Args:
        self (MainWindow instance): A reference to the MainWindow object.

    Side effects:
        Modifies raw_timeseries, filtered_timeseries, pulse_timeseries, segments,
        num_segments, r_peaks_list, snr, and primary_timeseries attributes of the MainWindow instance.
        Calls chunk_from_segment and handle_data_analysis_result methods.
    """
    self.raw_timeseries = np.column_stack((self.file_data[:,0], self.file_data[:,self.ecg_column]))
    self.filtered_timeseries = p.filter(self.raw_timeseries,self.sr) 
    self.pulse_timeseries = self.file_data[:,self.pulse_column]
    self.segments = p.divide_by_chunks(self.pulse_timeseries,self.sr)
    self.num_segments = len(self.segments)
    
    if self.selected_filtering: 
        self.r_peaks_list = p.find_r_peaks(self.filtered_timeseries, self.sr)
        self.snr = p.signal_to_noise(self.filtered_timeseries,self.raw_timeseries)
        self.primary_timeseries = self.filtered_timeseries
    else:    
        self.r_peaks_list = p.find_r_peaks(self.raw_timeseries, self.sr)       
        self.snr = "N/A"
        self.primary_timeseries = self.raw_timeseries
    chunk_from_segment(self)
    self.handle_data_analysis_result()
        
def chunk_from_segment(self):
    """
    Filters a segment of the filtered and raw time series and sets the current chunk to this segment.

    This function operates on the MainWindow class. It extracts a segment from the 
    filtered and raw time series and sets this as the current chunk. It also filters 
    the R-peaks list based on the time values in the current chunk. Updates the title 
    of the plot to show the start and end times of the current chunk.

    Args:
        self (MainWindow instance): A reference to the MainWindow object.

    Side effects:
        Modifies curr_filtered_chunk, curr_raw_chunk, curr_primary_chunk,
        curr_r_peaks_chunk of the MainWindow instance. Updates the figure title in the 
        scrollable window canvas.
    """
    segment = self.segments[self.curr_segment_idx]
    self.curr_filtered_chunk = self.filtered_timeseries[segment[0]:segment[1]]
    self.curr_raw_chunk = self.raw_timeseries[segment[0]:segment[1]]

    self.curr_primary_chunk = self.curr_filtered_chunk if self.selected_filtering else self.curr_raw_chunk

    min_time = self.curr_primary_chunk[0, 0]
    max_time = self.curr_primary_chunk[-1, 0]

    # Filter rows from self.r_peaks_list based on time values in the curr_primary_chunk
    time_filter = (self.r_peaks_list[:, 0] >= min_time) & (self.r_peaks_list[:, 0] <= max_time)

    self.curr_r_peaks_chunk = self.r_peaks_list[time_filter]

    minutes1, seconds1 = divmod(self.curr_primary_chunk[0, 0], 60)
    minutes2, seconds2 = divmod(self.curr_primary_chunk[-1, 0], 60)
    self.scrollable_window.canvas.figure.suptitle(f"File: {self.file_name}\n{self.title}\nSegment {self.curr_segment_idx+1}/{self.num_segments}\n{int(minutes1)}:{int(seconds1)} : {int(minutes2)}:{int(seconds2)}")
    self.scrollable_window.canvas.draw()