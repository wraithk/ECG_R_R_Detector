from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSlider,QMessageBox, QApplication
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np

class InteractivePoints:
    """
    This class is used for creating interactive points on the graph display. It contains functions
    for adding/ subtracting datapoints from the main classes curr_r_peaks_chunk. 
    """
    def __init__(self, main_window, scatter):
        self.main_window = main_window
        self.scatter = scatter
        
        self.cid = scatter.figure.canvas.mpl_connect('button_press_event', self)

    def __call__(self, event):
        if event.inaxes != self.scatter.axes: return

        # Left click to add a point
        if event.button == 1:  
            self.get_scaled_distances(event)
            if self.main_window.overlay_on == True and self.main_window.curr_raw_chunk is not None and self.main_window.curr_filtered_chunk is not None:
                raw_distances = np.sqrt(((self.main_window.curr_raw_chunk[:,0] / self.x_range) - self.x_data_scaled)**2 + ((self.main_window.curr_raw_chunk[:,1] / self.y_range) - self.y_data_scaled)**2)
                filtered_distances = np.sqrt(((self.main_window.curr_filtered_chunk[:,0] / self.x_range) - self.x_data_scaled)**2 + ((self.main_window.curr_filtered_chunk[:,1] / self.y_range) - self.y_data_scaled)**2)

                nearest_raw_point_index = raw_distances.argmin()
                nearest_filtered_point_index = filtered_distances.argmin()

                if raw_distances[nearest_raw_point_index] <= filtered_distances[nearest_filtered_point_index]:
                    new_point = self.main_window.curr_raw_chunk[nearest_raw_point_index]
                else:
                    new_point = self.main_window.curr_filtered_chunk[nearest_filtered_point_index]

                self.main_window.curr_r_peaks_chunk = np.vstack([self.main_window.curr_r_peaks_chunk, new_point])
            else:
                distances = np.sqrt(((self.main_window.curr_primary_chunk[:,0] / self.x_range) - self.x_data_scaled)**2 + ((self.main_window.curr_primary_chunk[:,1] / self.y_range) - self.y_data_scaled)**2)
                nearest_point_index = distances.argmin()

                if distances[nearest_point_index] <= 0.01:
                    new_point = self.main_window.curr_primary_chunk[nearest_point_index]
                    self.main_window.curr_r_peaks_chunk = np.vstack([self.main_window.curr_r_peaks_chunk, new_point])
        
        # Right click to remove a point
        elif event.button == 3:  
            if len(self.main_window.curr_r_peaks_chunk) == 0: return  # empty, nothing to remove

            self.get_scaled_distances(event)

            distances = np.sqrt(((self.main_window.curr_r_peaks_chunk[:,0] / self.x_range) - self.x_data_scaled)**2 + ((self.main_window.curr_r_peaks_chunk[:,1] / self.y_range) - self.y_data_scaled)**2)
            nearest_point_index = distances.argmin()

            if distances[nearest_point_index] <= 0.01:
                self.main_window.curr_r_peaks_chunk = np.delete(self.main_window.curr_r_peaks_chunk, nearest_point_index, 0)
        self.main_window.handle_updated_r_peaks()
    def get_scaled_distances(self,event):
        """Scales the x and y values of the mouse click according to the length of the axes.

        Args:
            event (button_press_event): event contains the x and y axis data of a mouse click on the figure
        """
        self.x_range = self.main_window.ax.get_xlim()[1] - self.main_window.ax.get_xlim()[0]
        self.y_range = self.main_window.ax.get_ylim()[1] - self.main_window.ax.get_ylim()[0]

        self.x_data_scaled = event.xdata / self.x_range
        self.y_data_scaled = event.ydata / self.y_range

class ScrollableWindow(QWidget):
    """This class inherits from the QWidget class and is used for creating a scrollable window for 
    the graph display. It includes a QVBoxLayout which houses a FigureCanvas for the figure to be 
    displayed and a slider widget. The wheelEvent is overrided in this class to control the scroll 
    behavior of the widget. It captures the wheel scroll event and calculates how much the slider's 
    value should be adjusted based on the amount of wheel scroll.

    Args:
        QWidget (_type_): _description_
    """
    def __init__(self, main_window, fig, ax, slider):
        super().__init__()

        self.canvas = FigureCanvas(fig)
        self.slider = slider
        self.main_window = main_window
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.slider)

        self.setLayout(layout)

    def wheelEvent(self, event):
        super().wheelEvent(event)
        degrees = event.angleDelta().y() 
        steps = int((degrees /15)) # Multiply steps by zoom_factor
        new_value = self.slider.value() + steps
        if self.slider.minimum() <= new_value <= self.slider.maximum():
            self.slider.setValue(new_value)

class ErrorMessage(QMessageBox):
    """This class inherits from the QMessageBox class and is used for creating an error message box.

    Args:
        QMessageBox (): Inherits from the QMessageBox class.
    """
    def __init__(self, message, function,file_path):
        super().__init__()
        self.setIcon(QMessageBox.Warning)
        self.setText(message)
        self.setInformativeText("Would you like to try again or quit the application?")
        self.setWindowTitle("An error occurred")
        retry_button = self.addButton('Retry', QMessageBox.AcceptRole)
        quit_button = self.addButton('Quit', QMessageBox.RejectRole)
        if file_path is not None: 
            close_button = self.addButton('Close', QMessageBox.RejectRole)
        self.exec_()
        if self.clickedButton() == retry_button:
            function()
        elif self.clickedButton() == quit_button:
            QApplication.quit()
        elif self.clickedButton() == close_button:
            self.close()

class SliderHandler(QSlider):
    """This class inherits from the QSlider class and is used for creating a slider widget for the
    main window class in main.py. It contains a function for handling the slider movement event, 
    as well as resetting the slider to its minimum value.

    Args:
        QSlider (QSlider): Inherits from the QSlider class.
    """
    def __init__(self, main_window):
        super().__init__(Qt.Horizontal)  # SliderHandler itself is a QSlider
        self.main_window = main_window
        
        self.valueChanged.connect(self.slider_moved)
        self.setTickInterval(self.main_window.tick)
        self.setEnabled(False)
        self.setSingleStep(1)

    def slider_moved(self, value):
        if not self.main_window.showing_hist:
            value /= self.main_window.zoom_factor  # Convert back to original scale
            self.main_window.ax.set_xlim(value, value + self.main_window.x_width)
            self.main_window.ax.figure.canvas.draw()

    def reset_slider(self):
        self.setEnabled(False)  # Disabling the slider
        self.setValue(self.minimum())  # Resetting the slider to its minimum value

