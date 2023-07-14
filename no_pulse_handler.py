
from PyQt5.QtWidgets import QComboBox, QCheckBox, QDialogButtonBox, QFormLayout, QLabel, QVBoxLayout,  QDialog, QLineEdit, QMessageBox
from PyQt5.QtCore import Qt
import processor as p 
import numpy as np 
import gui

class NoPulseSettingsDialog(QDialog):
    """A QDialog that allows the user to enter settings for data analysis when 
    there is no Pulse in the data.

    Attributes:
        file_length (float): The length of the file to be analyzed.
        minutes (int): The total minutes of the file.
        seconds (int): The remaining seconds of the file.
        ecg_column (int): The column with ECG Data.
        file_label (QLabel): A label to display the file's name.
        total_length_label (QLabel): A label to display the total length of the file.
        start_time_edit (QLineEdit): An input field to enter the start time.
        end_time_edit (QLineEdit): An input field to enter the end time.
        start_time_valid (bool): Validation status of start_time_edit.
        end_time_valid (bool): Validation status of end_time_edit.
        analyse_whole_dataset_checkbox (QCheckBox): Checkbox to decide if the whole dataset should be analyzed.
        need_filtering_checkbox (QCheckBox): Checkbox to decide if the data needs to be filtered.
        ecg_column_dropdown (QComboBox): A dropdown menu to select the column with ECG data.

    Args:
        file_name (str, optional): The name of the file.
        file_length (float, optional): The length of the file in seconds.
        file_width (int, optional): The width of the file (i.e., number of columns).
        parent (QWidget, optional): The parent widget.

    """
    def __init__(self, file_name=None, file_length = None, file_width = None, sr = int(1000), parent=None):
       
        super(NoPulseSettingsDialog, self).__init__(parent)
        self.setWindowTitle("Settings")
        self.file_length = file_length
        self.sr = sr
        self.minutes, self.seconds = divmod(self.file_length/self.sr, 60)
        self.ecg_column = 1

        self.file_label = QLabel(f"File: {file_name}")
        self.total_length_label = QLabel(f"The file is {int(self.minutes)} minutes and {int(self.seconds)} seconds long")
        
        self.start_time_edit = QLineEdit(self)
        self.end_time_edit = QLineEdit(self)

        self.start_time_valid = False
        self.aend_time_valid = False

        self.start_time_edit.textEdited.connect(lambda: self.on_edit())
        self.end_time_edit.textEdited.connect(lambda: self.on_edit())

        self.analyse_whole_dataset_checkbox = QCheckBox(self)
        self.analyse_whole_dataset_checkbox.stateChanged.connect(self.analyse_whole_dataset_handler)

        self.need_filtering_checkbox = QCheckBox(self)
        
        self.ecg_column_dropdown = QComboBox()
        for i in range(1, file_width):
            self.ecg_column_dropdown.addItem(f"{i}")
        self.ecg_column_dropdown.currentIndexChanged.connect(self.index_changed)
        
        form_layout = QFormLayout()
        form_layout.addRow("Start Time", self.start_time_edit)
        form_layout.addRow("End Time", self.end_time_edit)
        form_layout.addRow("Analyse the whole dataset?", self.analyse_whole_dataset_checkbox)

        form_layout.addRow("Column with ECG Data", self.ecg_column_dropdown)
        form_layout.addRow("Filter this data", self.need_filtering_checkbox)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        button_box.accepted.connect(self.accept_check)
        button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.file_label)
        main_layout.addWidget(self.total_length_label)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)

    def on_edit(self):
        """
        Handles the edit event for start and end time fields.

        This method checks whether the entered start and end times are valid.
        If they are not valid, it changes the background color of the respective QLineEdit to red.
        If they are valid, it changes the background color of the QLineEdit to default.
        """
        self.is_valid_time()
        if self.analyse_whole_dataset_checkbox.isChecked():
            self.analyse_whole_dataset_checkbox.setChecked(False)

        if not self.start_time_valid:
            self.start_time_edit.setStyleSheet("background-color: red")
        else:
            self.start_time_edit.setStyleSheet("background-color: none")

        if not self.end_time_valid:
            self.end_time_edit.setStyleSheet("background-color: red")
        else:
            self.end_time_edit.setStyleSheet("background-color: none")
    
    def is_valid_time(self):
        """
        Validates the start and end time entries.

        It tries to convert the string values from QLineEdit fields to float and checks if they 
        satisfy certain conditions such as being within the total length of the file and if 
        start time is not greater than end time.
        Updates self.start_time_valid and self_end_time_valid to be used in other sections of the 
        class.
        Returns:
            bool: True if both times are valid, False otherwise.
        
        Raises:
            ValueError: If the entered values cannot be converted to float.
        """
        try: 
            start_time = float(self.start_time_edit.text())
            self.start_time_valid = True
        except ValueError:
            self.start_time_valid = False

        try: 
            end_time = float(self.end_time_edit.text())
            self.end_time_valid = True
        except ValueError:
            self.end_time_valid = False
            
        total_length = self.minutes + self.seconds / 60
        
        if self.start_time_valid and self.end_time_valid:
            if start_time >= end_time: 
                self.start_time_valid = False
                self.end_time_valid = False 
            elif end_time > total_length or end_time < 0: 
                self.end_time_valid = False 
            elif start_time > total_length or start_time < 0:
                self.start_time_valid = False 

        return (self.start_time_valid and self.end_time_valid)

    def analyse_whole_dataset_handler(self, state):
        if state == Qt.Checked:

            self.start_time_edit.setText('0')
            self.end_time_edit.setText(f'{float(round(self.file_length/(60*self.sr),2))}')
            self.start_time_edit.setStyleSheet("background-color: none")
            self.end_time_edit.setStyleSheet("background-color: none")

    def get_values(self):

        if self.is_valid_time() or self.analyse_whole_dataset_checkbox.isChecked():
            return (
                self.start_time_edit.text(),
                self.end_time_edit.text(),
                self.need_filtering_checkbox.isChecked(),
                self.ecg_column,
                self.analyse_whole_dataset_checkbox.isChecked()
            )
        else:
            return None
    def index_changed(self, i):
        self.ecg_column = i + 1

    def accept_check(self):
        if not self.is_valid_time() and self.analyse_whole_dataset_checkbox.isChecked() == False:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers for the start and end time.")
            return
        else:
            self.accept()

def no_pulse_settings_pane(self):
    """
    Opens the settings pane for data analysis when there is no pulse.

    Raises:
        ValueError: If the entered values cannot be converted to float.
    """
    try:
        self.minutes, self.seconds = divmod(self.file_length/self.sr, 60)
        dialog = NoPulseSettingsDialog(self.file_name,self.file_length, self.file_width, self.sr, self)
        result = dialog.exec_()
    except Exception:
        QMessageBox.warning(self, "An Error Occured", "Please try again.")
        self.select_file()
    if result == QDialog.Accepted:
        try:
            values = dialog.get_values()
            if values is None:
                raise ValueError("Invalid input")
            
            start_time, end_time, selected_filtering, ecg_column, analyse_whole_dataset = values
            
            if analyse_whole_dataset:
                self.start_time = 0
                self.end_time = self.file_length/(60*self.sr)
            else:
                if self.start_time > self.end_time: 
                    choice = gui.ErrorMessage('The start time cannot be greater than the end time. Please try again.', self.no_pulse_settings_pane,self.file_path)
                    return choice
                self.start_time = float(start_time)
                self.end_time = float(end_time)
            
            self.selected_filtering = selected_filtering

            if ecg_column < 1:
                raise ValueError("Invalid column selection.")
            self.ecg_column = ecg_column
            self.analyse_whole_dataset = analyse_whole_dataset
            self.overlay_toggle_button.setEnabled(True)
            if self.selected_filtering:
                self.overlay_toggle_button.setText("Show Original Signal")
                self.is_filtered = True
                self.scrollable_window.canvas.figure.suptitle(f"File: {self.file_name}\nR Peaks Detected From a Fourier Transform of the Orignal Signal")
                self.scrollable_window.canvas.draw()
            else:
                self.overlay_toggle_button.setText("Show Filtered Signal")
                self.is_filtered = False
                self.scrollable_window.canvas.figure.suptitle(f"File: {self.file_name}\nR Peaks Detected from the Orignal Signal")
                self.scrollable_window.canvas.draw()
            run_data_analysis(self)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers for the sr, ecg column and pulse column.")
            no_pulse_settings_pane(self)
        except FileNotFoundError:
            QMessageBox.warning(self, "File Not Found", "Please select a file before exiting the settings pane.")
            no_pulse_settings_pane(self)
    else:
        QMessageBox.warning(self, "No Changes Made", "You have closed the settings pane without making any changes.")
        return
                
def run_data_analysis(self):
    """
    Runs the data analysis on the selected file.
    """
    try:
        self.raw_timeseries = np.column_stack((self.file_data[:,0], self.file_data[:,self.ecg_column]))
        self.ts = 1/self.sr
        self.filtered_timeseries = p.filter(self.raw_timeseries,self.sr) 
        
        if self.selected_filtering: 
            self.r_peaks_list = p.find_r_peaks(self.filtered_timeseries,self.sr)
            self.snr = p.signal_to_noise(self.filtered_timeseries,self.raw_timeseries)
            self.primary_timeseries = self.filtered_timeseries
        else:    
            self.r_peaks_list = p.find_r_peaks(self.raw_timeseries,self.sr)       
            self.snr = "N/A"
            self.primary_timeseries = self.raw_timeseries
        carve_timeseries(self)
        self.handle_data_analysis_result()
    except OSError:
        QMessageBox.warning(self, "Invalid File", "The selected file could not be opened. Please check the file path and try again.")
        

def carve_timeseries(self):
    if self.analyse_whole_dataset:
        self.curr_filtered_chunk = self.filtered_timeseries
        self.curr_raw_chunk = self.raw_timeseries
        self.curr_r_peaks_chunk = self.r_peaks_list
        self.curr_primary_chunk = self.curr_filtered_chunk if self.selected_filtering else self.curr_raw_chunk
    else:
        start_point = int(self.start_time*self.sr*60)
        end_point = int(self.end_time*self.sr*60)

        self.curr_raw_chunk = self.raw_timeseries[start_point:end_point]
        self.curr_filtered_chunk = self.filtered_timeseries[start_point:end_point]
        
        self.curr_primary_chunk = self.curr_filtered_chunk if self.selected_filtering else self.curr_raw_chunk

        min_time = self.curr_primary_chunk[0, 0]
        max_time = self.curr_primary_chunk[-1, 0]

        time_filter = (self.r_peaks_list[:, 0] >= min_time) & (self.r_peaks_list[:, 0] <= max_time)

        self.curr_r_peaks_chunk = self.r_peaks_list[time_filter]

    
