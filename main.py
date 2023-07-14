import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QGridLayout, QPushButton, QWidget, QLabel, QSlider,QButtonGroup, QMessageBox, QInputDialog, QHBoxLayout
from PyQt5.QtCore import Qt, QDir
from matplotlib.figure import Figure
import numpy as np
import processor as p
import no_pulse_handler as nopul
import pulse_handler as pul
import gui as gui
            

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.initialise_variables()
        self.setup_ui()
    

    def initialise_variables(self):
        """
        This function initialises all the variables used in the program.
        """
        self.file_path = ""
        self.file_name = ""
        self.file_data = None
        self.file_width = 0 
        self.file_length = 0
        
        self.raw_timeseries = np.empty((0,0))
        self.filtered_timeseries = np.empty((0,0))
        self.primary_timeseries = np.empty((0,0))
        
        self.r_peaks_list = np.empty((0,0))
        self.snr = 0
        
        self.pulse_timeseries = np.empty((0,0))
        self.segments = None
        self.num_segments = 0
        self.curr_segment_idx = 0
        self.curr_raw_chunk = np.empty((0,0))
        self.curr_filtered_chunk = np.empty((0,0))
        self.curr_primary_chunk = np.empty((0,0))
        self.curr_r_peaks_chunk = np.empty((0,2))
        
        self.start_time = 0 
        self.end_time = 1
        self.minimum_x = 0
        self.sr = int(1000)
        self.tick = 1
        self.zoom_factor = 1
        self.default_width = 30
        self.x_width = self.default_width
        
        self.overlay_on = False
        self.plot2 = None
        self.selected_filtering = None
        self.max_interval_pos = 0
        self.min_interval_pos = 0
        self.average_interval = 0

        self.desktop_path = QDir.homePath() + "/Desktop"
        self.analyse_whole_dataset = False
        self.showing_hist = False
        
    def setup_ui(self):
        """
        This function sets up the UI of the program.
        """
        self.setWindowTitle('ECG Data Analysis')
        self.resize(1920,1080)

        self.select_file_button = QPushButton('Select File')
        self.select_file_button.clicked.connect(self.select_file)
    
        self.graph_label = QLabel()
        
        self.info_label = QLabel("")
        
        self.max_interval_button = QPushButton('Max Interval (Q)')
        self.max_interval_button.clicked.connect(self.to_max_interval)
        self.min_interval_button = QPushButton('Min Interval (W)')
        self.min_interval_button.clicked.connect(self.to_min_interval)
        
        interval_button_layout = QGridLayout()
        interval_button_layout.addWidget(self.max_interval_button,0,0)
        interval_button_layout.addWidget(self.min_interval_button,0,1)
        
        self.overlay_toggle_button = QPushButton("")
        self.overlay_toggle_button.setCheckable(True)
        self.overlay_toggle_button.toggled.connect(self.overlay_toggler)
        self.overlay_toggle_button.setEnabled(False)
        
        self.graph_toggle_button = QPushButton("Display R-R Interval Histogram")
        self.graph_toggle_button.clicked.connect(self.graph_toggler)
        self.graph_toggle_button.setEnabled(False)
        
        self.figure = Figure(figsize=(10,5))
        self.ax = self.figure.add_subplot(111)
        self.scatter = self.ax.scatter(self.curr_r_peaks_chunk[:,0],self.curr_r_peaks_chunk[:,1], color = 'red',zorder=3)
        
        self.slider = gui.SliderHandler(self)
        
        self.scrollable_window = gui.ScrollableWindow(self,self.figure, self.ax, self.slider)
        
        self.zoom_buttons_label = QLabel("Zoom")
        
        self.zoom_button_group = QButtonGroup(self)
        self.zoom_button1 = QPushButton('1')
        self.zoom_button2 = QPushButton('2')
        self.zoom_button3 = QPushButton('3')
        self.zoom_button5 = QPushButton('5')
        self.zoom_button10 = QPushButton('10')
        
        self.zoom_button1.clicked.connect(lambda: self.set_zoom(1))
        self.zoom_button2.clicked.connect(lambda: self.set_zoom(2))
        self.zoom_button3.clicked.connect(lambda: self.set_zoom(3))
        self.zoom_button5.clicked.connect(lambda: self.set_zoom(5))
        self.zoom_button10.clicked.connect(lambda: self.set_zoom(10))
        
        self.zoom_button_group.addButton(self.zoom_button1, 1)
        self.zoom_button_group.addButton(self.zoom_button2, 2)
        self.zoom_button_group.addButton(self.zoom_button3, 3)
        self.zoom_button_group.addButton(self.zoom_button5, 5)
        self.zoom_button_group.addButton(self.zoom_button10, 10)

        zoom_button_layout = QGridLayout()
        zoom_button_layout.addWidget(self.zoom_button1,0,0)
        zoom_button_layout.addWidget(self.zoom_button2,0,1)
        zoom_button_layout.addWidget(self.zoom_button3,0,2)
        zoom_button_layout.addWidget(self.zoom_button5,0,3)
        zoom_button_layout.addWidget(self.zoom_button10,0,4)
        
        self.re_run_analysis_button = QPushButton('Re-detect R Peaks')
        self.re_run_analysis_button.clicked.connect(self.re_run_analysis_handler)
        self.re_run_analysis_button.setEnabled(False)

        self.export_r_peaks_button = QPushButton('Export R Peaks')
        self.export_rr_intervals_button = QPushButton('Export RR Intervals')
        self.export_r_peaks_button.clicked.connect(lambda: self.export_function(True))
        self.export_rr_intervals_button.clicked.connect(lambda: self.export_function(False))
        self.export_rr_intervals_button.setEnabled(False)
        self.export_r_peaks_button.setEnabled(False)
        
        export_button_layout = QGridLayout()
        export_button_layout.addWidget(self.export_r_peaks_button,0,0)
        export_button_layout.addWidget(self.export_rr_intervals_button,0,1)
        
        self.grid_layout = QGridLayout()
        self.grid_layout.addWidget(self.select_file_button, 0,1,1,2)
        self.grid_layout.addWidget(self.info_label,0,0)
        self.grid_layout.addWidget(self.overlay_toggle_button, 0, 3)
        self.grid_layout.addLayout(interval_button_layout, 1,0)
        self.grid_layout.addWidget(self.graph_toggle_button,1,1,1,2)
        self.grid_layout.addWidget(self.scrollable_window, 2, 0, 5 ,4)
        self.grid_layout.addWidget(self.re_run_analysis_button,7,0)
        self.grid_layout.addLayout(export_button_layout,7,1,1,2)
        self.grid_layout.addWidget(self.slider,9,0,1,4)
        self.grid_layout.addWidget(self.zoom_buttons_label, 10, 0)
        self.grid_layout.addLayout(zoom_button_layout, 10, 1,1,2)
    
        widget = QWidget()
        widget.setLayout(self.grid_layout)
        self.setCentralWidget(widget)
        self.showFullScreen()
        
    def keyPressEvent(self, event):
        """
        This function handles key presses.

        Args:
            event (QKeyEvent): The key press event.
        """
        if not self.showing_hist:
            key = event.key()
            if key in [Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_4, Qt.Key_5]:
                zoom_level = key - Qt.Key_0
                if zoom_level == 4:  # map key 4 to zoom level 5
                    zoom_level = 5
                elif zoom_level == 5:  # map key 5 to zoom level 10
                    zoom_level = 10
                self.set_zoom(zoom_level)
            elif key == Qt.Key_Q:
                self.to_max_interval()
            elif key == Qt.Key_W:
                self.to_min_interval()

    def select_file(self):
        """
        This function opens a file dialog to select a file.

        """
        self.initialise_variables()
        self.file_path, ok = QFileDialog.getOpenFileName(self, 'Open File', self.desktop_path)
        if ok: 
            if not os.path.isfile(self.file_path):
                choice = gui.ErrorMessage("You have not selected a valid file. Would you like to try again or quit the application?", self.select_file, self.file_path)
                return choice
            elif not self.file_path.lower().endswith('.txt') and not self.file_path.lower().endswith('.rtf') :
                choice = gui.ErrorMessage("The selected file is not a .txt or .rtf file. Would you like to try again or quit the application?", self.select_file, self.file_path)
                return choice
            self.file_name = os.path.basename(self.file_path)
            self.file_name, _ = os.path.splitext(self.file_name)  # this line removes the extension from the filename
            self.prompt_sr()

    def prompt_sr(self):
        """
        This function prompts the user to enter the sampling frequency of the data.

        """
        text, ok = QInputDialog.getText(None, "Input", "Please enter the data's sampling frequency (Hz)", text = "1000")
        if ok:
            if not text.isdigit():
                choice = gui.ErrorMessage("Please enter a valid sampling rate", self.prompt_sr, self.file_path)
                return choice
            self.sr = int(text)
            self.open_file_handler()
            
    def open_file_handler(self):
        """
        This function handles the opening of the file.
        
        Side effects:
            Calls self.has_pulse_button() if the file is opened successfully.
        """
        try:
            self.file_data, self.file_length, self.file_width, self.num_rows_removed = p.file_opener(self.file_path, self.sr)
            self.percentage_removed = round((self.num_rows_removed/(self.num_rows_removed+self.file_length))*100,2)
        except Exception as e:
            choice = gui.ErrorMessage(f"Error opening file: {str(e)}", self.open_file_handler, self.file_path)
            return choice
        if (self.file_data is None or self.file_length <= 0 or self.file_width <= 1):
            choice = gui.ErrorMessage("Data could not be imported",self.select_file, self.file_path)
            return choice
        QMessageBox.information(self, "Data Rows Removed", f"{self.num_rows_removed} rows of invalid data were removed,\nrepresenting {self.percentage_removed}% of the original data.")
        self.has_pulse_button()

    def has_pulse_button(self):
        """
        This function asks the user if the segments are defined by a pulse.
        """
        self.has_pulse = QMessageBox.question(self, "Question Dialog Title", "Are the segments defined by a pulse?",
                                            QMessageBox.Yes | QMessageBox.No)
        
        if self.has_pulse not in (QMessageBox.Yes, QMessageBox.No): 
            return

        if self.has_pulse == QMessageBox.Yes: 
            if self.file_width < 3: 
                QMessageBox.warning(self, "Invalid File", "The selected file does not have enough columns to be divided by a pulse. Please select a different file.")
                self.has_pulse_button()
            self.prev_button = QPushButton("Previous Segment")
            self.grid_layout.addWidget(self.prev_button, 8,1,1,1)
            self.prev_button.clicked.connect(self.prev_button_clicked)
            self.prev_button.setEnabled(False)
            self.next_button = QPushButton("Next Segment")
            self.grid_layout.addWidget(self.next_button, 8,2,1,1)
            self.next_button.clicked.connect(self.next_button_clicked)
            
            pul.pulse_settings_pane(self)
        else: nopul.no_pulse_settings_pane(self)
    
    def handle_data_analysis_result(self):
        """
        This function handles the result of the data analysis.
        """
        if self.curr_primary_chunk.size == 0:
            QMessageBox.warning(self, "Empty Data", "The selected data segment is empty. Please select a different segment.")
            return
        if len(self.curr_r_peaks_chunk) > 0:       
            self.handle_updated_r_peaks()
        else:
            self.average_interval = None 
            self.max_interval = None
            self.min_interval = None
            self.info_label.setText(f'Signal to Noise Ratio: {round(self.snr, 1) if isinstance(self.snr, (float, int)) else self.snr}\nAverage Interval: {round(self.average_interval, 3)}s\nLargest Interval: {round(self.max_interval, 3)}s\nSmallest Interval: {round(self.min_interval, 3)}s')
        self.minimum_x = int(self.curr_primary_chunk[0,0])
        self.reset_canvas()
        self.slider.reset_slider()
        self.plot_ecg_data()
        
    def plot_ecg_data(self):
        """
        This function plots the ECG data on the graph.
        """
        self.ax.clear()
        self.graph_toggle_button.setText("Display R-R Interval Histogram")

        self.plot, = self.ax.plot(self.curr_primary_chunk[:,0],self.curr_primary_chunk[:,1],zorder=2)
        self.scatter = self.ax.scatter(self.curr_r_peaks_chunk[:,0],self.curr_r_peaks_chunk[:,1], color = 'red',zorder=3)
        self.interactive_points = gui.InteractivePoints(self, self.scatter)
        
        self.ax.set_xlim(self.curr_primary_chunk[0,0], self.curr_primary_chunk[0,0]+self.x_width)

        self.slider.setMinimum(self.minimum_x)
        self.slider.setMaximum(int((self.minimum_x+ (len(self.curr_primary_chunk[:,0])/(self.sr)))-self.x_width))
        self.slider.setEnabled(True)
        self.export_r_peaks_button.setEnabled(True)
        self.export_rr_intervals_button.setEnabled(True)
        self.re_run_analysis_button.setEnabled(True)
        self.overlay_toggle_button.setEnabled(True)
        self.max_interval_button.setEnabled(True)
        self.min_interval_button.setEnabled(True)
        self.graph_toggle_button.setEnabled(True)
        self.re_run_analysis_button.setEnabled(True)
        self.showing_hist = False
        self.ax.figure.canvas.draw()

    def plot_r_r_histogram(self):
        """
        This function plots a histogram of the R-R Intervals on the graph.
        """
        self.ax.clear()
        self.graph_toggle_button.setText("Display ECG Graph")
        bin_edges = np.arange(0, 2, 0.1)

        diffs = np.diff(self.curr_r_peaks_chunk[:, 0])
        n, bins, patches = self.ax.hist(diffs, bins=bin_edges, edgecolor='black')

        self.ax.axvline(0.6, color='r', linestyle='--')
        self.ax.axvline(1.2, color='r', linestyle='--')

        ymax = max(n)  
        ytext = ymax + ymax*0.05 
        self.ax.text(0.6, ytext, '600 ms', color='r', ha='center')
        self.ax.text(1.2, ytext, '1200 ms', color='r', ha='center')

        self.slider.setEnabled(False)
        self.export_r_peaks_button.setEnabled(False)
        self.export_rr_intervals_button.setEnabled(False)
        self.re_run_analysis_button.setEnabled(False)
        self.overlay_toggle_button.setEnabled(False)
        self.max_interval_button.setEnabled(False)
        self.min_interval_button.setEnabled(False)
        self.graph_toggle_button.setEnabled(True)
        self.showing_hist = True
        self.ax.figure.canvas.draw()

    def slider_moved(self, value):
        """
        This function handles slider movements, which changes the graph display.
        Args:
            value ( int): The value of the slider.
        """
        if not self.showing_hist:
            value /= self.zoom_factor 
            self.ax.set_xlim(value, value + self.x_width)
            self.ax.figure.canvas.draw()
            
    def set_zoom(self, zoom_factor):
        """
        This function updated the zoom of the graph and the slider's sensitivity

        Args:
            zoom_factor (int): The zoom factor to be applied to the graph.       
        """
        self.zoom_factor = zoom_factor
        for button in self.zoom_button_group.buttons():
            button.setStyleSheet('')

        button = self.zoom_button_group.button(zoom_factor)
        if button is None:
            return

        button.setStyleSheet("""
        QPushButton {
            background-color: grey;
        }
        QPushButton:focus {
            outline: none;
        }
        """)
        self.minimum_x = int(self.curr_primary_chunk[0,0])
        current_xlim = self.ax.get_xlim()
        current_width = current_xlim[1] - current_xlim[0]
        self.x_width = self.default_width/self.zoom_factor
 
        new_start = int(current_xlim[0] + current_width/2 - self.x_width/2)
        if (new_start < self.minimum_x): new_start = self.minimum_x

        self.slider.setMinimum(int(self.minimum_x)*self.zoom_factor)
        self.slider.setMaximum(int((self.minimum_x+ (len(self.curr_primary_chunk[:,0])/(self.sr)))-self.x_width)*self.zoom_factor)
        self.slider.setValue(new_start*self.zoom_factor)

        self.ax.figure.canvas.draw()

    def graph_toggler(self):
        """
        This function toggles between the ECG graph and the R-R Interval histogram.
        """
        if len(self.curr_r_peaks_chunk) > 0:
            if self.showing_hist:
                self.plot_ecg_data()
            else:
                self.plot_r_r_histogram()
    

    def overlay_toggler(self):
        """
        This function toggles the overlay of the filtered data on the graph.
        """
        self.overlay_on = not self.overlay_on
        if self.overlay_on:
                if self.selected_filtering: 
                    self.plot2, = self.ax.plot(self.curr_raw_chunk[:,0],self.curr_raw_chunk[:,1],color='black',zorder=1)
                else:
                    self.snr = p.signal_to_noise(self.curr_filtered_chunk,self.curr_raw_chunk)
                    self.plot2, = self.ax.plot(self.curr_filtered_chunk[:,0],self.curr_filtered_chunk[:,1],color='black',zorder=4)  
        else:
            if not self.selected_filtering:
                self.snr = "N/A"
            if self.plot2:
                self.plot2.remove()
            self.plot2 = None
        self.info_label.setText(f'Signal to Noise Ratio: {round(self.snr, 1) if isinstance(self.snr, (float, int)) else self.snr}\nAverage Interval: {round(self.average_interval, 3)}s\nLargest Interval: {round(self.max_interval, 3)}s\nSmallest Interval: {round(self.min_interval, 3)}s')
        self.ax.figure.canvas.draw()
    
    def handle_updated_r_peaks(self):
        """
        This function handles the updated R Peaks.
        """
        indices = np.argsort(self.curr_r_peaks_chunk[:,0])

        self.curr_r_peaks_chunk[:] = self.curr_r_peaks_chunk[indices]

        differences = np.diff(self.curr_r_peaks_chunk[:,0])
        self.average_interval = np.mean(differences)
        
        max_index = np.argmax(differences)
        self.max_interval = differences[max_index]
        self.max_interval_pos = self.curr_r_peaks_chunk[max_index, 0]
        
        min_index = np.argmin(differences)
        self.min_interval = differences[min_index]
        self.min_interval_pos = self.curr_r_peaks_chunk[min_index, 0]
        self.info_label.setText(f'Signal to Noise Ratio: {round(self.snr, 1) if isinstance(self.snr, (float, int)) else self.snr}\nAverage Interval: {round(self.average_interval, 3)}s\nLargest Interval: {round(self.max_interval, 3)}s\nSmallest Interval: {round(self.min_interval, 3)}s')
        
        self.scatter.set_offsets(self.curr_r_peaks_chunk)
        self.scatter.figure.canvas.draw()

    def re_run_analysis_handler(self):
        """
        This function handles the re-running of the R Peaks analysis.
        """
        self.curr_r_peaks_chunk = p.r_peaks_filter(self.curr_r_peaks_chunk,self.curr_raw_chunk,self.curr_filtered_chunk)
        self.handle_updated_r_peaks()
        
    def to_max_interval(self):
        """
        This function moves the graph to the maximum interval between R Peaks.
        """
        centre = self.max_interval_pos+self.max_interval/2
        self.slider.setValue(int(centre-self.x_width/2))
        self.ax.set_xlim(centre-self.x_width/2, centre+self.x_width/2)
        self.ax.figure.canvas.draw()
 
    def to_min_interval(self):
        """
        This function moves the graph to the minimum interval between R Peaks.
        """
        centre = self.min_interval_pos+self.min_interval/2
        self.slider.setValue(int(centre-self.x_width/2))
        self.ax.set_xlim(centre-self.x_width/2, centre+self.x_width/2)
        self.ax.figure.canvas.draw()
        
    def next_button_clicked(self):
        """
        This function handles the case when there is a pulse and the user want to move
        """
        self.prev_button.setEnabled(True) 
        if self.curr_segment_idx == self.num_segments-2:
            self.next_button.setEnabled(False)  
        if self.plot2:
            self.plot2.remove()
            self.plot2 = None
            self.ax.figure.canvas.draw()       
        self.curr_segment_idx += 1
        self.overlay_toggle_button.setChecked(False)
        pul.chunk_from_segment(self)
        self.handle_data_analysis_result()
    
    def prev_button_clicked(self):
        """
        This function handles the case when there is a pulse and the user want to move
        """
        self.next_button.setEnabled(True) 
        if self.curr_segment_idx == 1:
            self.prev_button.setEnabled(False)  
        if self.plot2:
            self.plot2.remove()
            self.plot2 = None
            self.ax.figure.canvas.draw()          
        self.curr_segment_idx -= 1 
        self.overlay_toggle_button.setChecked(False)
        pul.chunk_from_segment(self)
        self.handle_data_analysis_result()
    
    def export_function(self, is_r_peaks):
        """
        This function exports the R Peaks or R-R Intervals to a text file.

        Args:
            is_r_peaks (bool):  Whether the data to be exported is R Peaks or R-R Intervals.
        """
        file_directory = QFileDialog.getExistingDirectory(self, 'Save File', self.desktop_path)
        if not file_directory:
            QMessageBox.warning(self, "Invalid Directory", "You have not selected a valid directory. Please try again.")
            return
        try:
            indices = np.argsort(self.curr_r_peaks_chunk[:,0])
            self.curr_r_peaks_chunk = self.curr_r_peaks_chunk[indices] 
            if self.num_segments != 0:
                if is_r_peaks:
                    file_path = os.path.join(file_directory, f"{self.file_name}_R-Peaks_Segment_{self.curr_segment_idx+1}.txt")
                    np.savetxt(file_path, self.curr_r_peaks_chunk, delimiter='\t')
                else:
                    file_path = os.path.join(file_directory, f"{self.file_name}_R-R_Intervals_Segment_{self.curr_segment_idx+1}.txt")
                    diffs = np.diff(self.curr_r_peaks_chunk[:, 0])
                    np.savetxt(file_path, diffs, delimiter='\t')
            elif self.analyse_whole_dataset:
                if is_r_peaks:
                    file_path = os.path.join(file_directory, f"{self.file_name}_R-Peaks.txt")
                    np.savetxt(file_path, self.curr_r_peaks_chunk, delimiter='\t')
                else:
                    file_path = os.path.join(file_directory, f"{self.file_name}_R-R_Intervals.txt")
                    diffs = np.diff(self.curr_r_peaks_chunk[:, 0])
                    np.savetxt(file_path, diffs, delimiter='\t')
            else:
                if is_r_peaks:
                    file_path = os.path.join(file_directory, f"{self.file_name}_R-Peaks_{self.start_time}-{self.end_time}.txt")
                    np.savetxt(file_path, self.curr_r_peaks_chunk, delimiter='\t')
                else:
                    file_path = os.path.join(file_directory, f"{self.file_name}_R-R_Intervals_{self.start_time}-{self.end_time}.txt")
                    diffs = np.diff(self.curr_r_peaks_chunk[:, 0])
                    np.savetxt(file_path, diffs, delimiter='\t')
        except Exception as e:
            choice = gui.ErrorMessage(f"An error occurred while exporting the data: {e}", self.export_function,self.file_path)
            return choice
    
    def reset_canvas(self):
        """
        This function resets the canvas to its default state.
        """
        self.x_width = self.default_width
        self.slider.setValue(0)
        self.showing_hist = False
        self.set_zoom(1)
  
app = QApplication(sys.argv)

main = MainWindow()
main.show()

sys.exit(app.exec_())

