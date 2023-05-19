import yaml
from PyQt5.QtWidgets import (QTabWidget,QHBoxLayout, QPushButton, QLabel, QLineEdit,
                             QWidget, QFormLayout, QScrollArea, QGroupBox,QComboBox)
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import  QVBoxLayout, QSlider
from PyQt5.QtCore import Qt
import pyqtgraph as pg
from utils.scenes_helper import *
from utils.toolbox import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.colors import ListedColormap
import matplotlib.patches as mpatches
import os

class SceneContentDisplay(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Create a label
        self.label = QLabel("Slice Number: ")
        self.layout.addWidget(self.label)

        # Create a slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.valueChanged.connect(self.update_image)
        self.layout.addWidget(self.slider)

        # Create ImageView item with a PlotItem as its view box
        self.imageView = pg.ImageView(view=pg.PlotItem())
        self.layout.addWidget(self.imageView)

    def diplay_scene_content(self, scene, list_wavelengths):

        self.list_wavelengths = list_wavelengths

        # Normalize filtering_cube values to range [0, 255] for ImageView
        self.data = (scene - np.min(scene)) / (np.max(scene) - np.min(scene)) * 255
        self.data = self.data.astype(np.uint8)

        # Set slider maximum value
        self.slider.setMaximum(self.data.shape[2] - 1)

        # Display the first slice
        self.update_image(0)

    def update_image(self, slice_index):
        # Update the label
        self.label.setText("wavelength: " + str(int(self.list_wavelengths[slice_index])) + " nm")

        # Display the slice
        self.imageView.setImage(np.rot90(self.data[:, :, slice_index]), levels=(0, 255))

class SceneHistogram(QWidget):

    def __init__(self):
        super().__init__()

        # Create a QVBoxLayout for the widget
        self.layout = QVBoxLayout(self)

        # Create a figure and a canvas
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas)

    def plot_label_histogram(self, ground_truth, label_values, ignored_labels,palette):
        """
        Plot a histogram with the occurrence of each data label in the dataset.

        :param ground_truth: np.array, ground truth labels
        :param label_values: list, label_values[i] = name of the class i
        :param palette: color palette to use, must be a list of colors where the index corresponds to the label
        :param ignored_labels: list of ignored labels (pixel with no label)
        """
        # Clear the figure
        self.figure.clear()

        # Create an axes
        ax = self.figure.add_subplot(111)

        # Compute the occurrence of each label
        values, counts = np.unique(ground_truth, return_counts=True)

        # Remove ignored labels
        valid_indices = [i for i, v in enumerate(values) if v not in ignored_labels]
        values = values[valid_indices]
        counts = counts[valid_indices]

        # Create a list of label names
        labels = [label_values[i] for i in values]

        # Get the colors from the palette and convert to the range [0, 1]
        colors = [tuple([x / 255 for x in palette[i]]) for i in values]

        # Plot the histogram
        ax.bar(labels, counts, color=colors)

        # Set the title and labels
        ax.set_title("Label occurrence")
        ax.set_xlabel("Label")
        ax.set_ylabel("Occurrence")

        # Rotate the x-axis labels
        ax.set_xticks(range(len(labels)))  # Add this line
        ax.set_xticklabels(labels, rotation=45)

        # Redraw the canvas
        self.canvas.draw()

class SceneLabelisation(QWidget):
    def __init__(self):
        super().__init__()

        # Create a QVBoxLayout for the widget
        self.layout = QVBoxLayout(self)

        # Create a figure and a canvas
        self.figure = plt.figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas)



    def display_ground_truth(self, ground_truth, label_values, palette):
        """
        Display the ground truth with each color corresponding to a label_value.

        :param ground_truth: np.array, ground truth labels
        :param label_values: list, label_values[i] = name of the class i
        :param palette: color palette to use, must be a list of colors where the index corresponds to the label
        :param ignored_labels: list of ignored labels (pixel with no label)
        """
        # Clear the figure
        self.figure.clear()

        # Create an axes
        ax = self.figure.add_subplot(111)

        # Convert palette to matplotlib color map
        cmap = ListedColormap([tuple([x / 255 for x in palette[i]]) for i in range(len(label_values))])

        # Plot the ground truth
        ax.imshow(ground_truth, cmap=cmap,interpolation='nearest')

        # Create a patch (colored square) for each label
        patches = [mpatches.Patch(color=cmap(i), label=f"{label_values[i]}: {np.sum(ground_truth == i)}")
                   for i in range(len(label_values))]

        # Create a legend using the patches
        ax.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)

        # Redraw the canvas
        self.canvas.draw()



class SpectralDataDisplay(QWidget):
    def __init__(self):
        super().__init__()

        # Create a QVBoxLayout for the widget
        self.layout = QVBoxLayout(self)

        # Create a figure and a canvas
        self.figure = plt.figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas)

    def plot_spectrums(self, spectrums, std_spectrums, palette, label_values):
        """Plot mean and intra-class covariance spectrum for each class on a single graph

        Args:
            spectrums: dictionary (name -> spectrum) of spectrums to plot
            std_spectrums: dictionary (name -> std of spectrum) of spectrums to plot
            palette: dictionary, color palette
            label_values: list, label_values[i] = name of the ith class
        """
        # Clear previous figure
        self.figure.clear()

        # Create an axes
        ax = self.figure.add_subplot(111)

        for k, v in spectrums.items():
            std_spec = std_spectrums[k]
            up_spec = v + std_spec
            low_spec = v - std_spec
            x = np.arange(len(v))
            i = label_values.index(k)

            # Convert RGB to normalized tuple
            color = tuple([x / 255 for x in palette[i]])

            ax.fill_between(x, up_spec, low_spec, color=color, alpha=0.3)

        for k, v in spectrums.items():
            x = np.arange(len(v))
            i = label_values.index(k)

            # Convert RGB to normalized tuple
            color = tuple([x / 255 for x in palette[i]])

            ax.plot(x, v, color=color, label=k)

        ax.set_title("Mean spectrum per class")
        ax.legend()

        # Draw the figure on the canvas
        self.canvas.draw()



    def display_spectral_data(self, mean_spectrums, std_spectrums, palette, label_values):
        # Call the plot function
        self.plot_spectrums(mean_spectrums, std_spectrums, palette, label_values)




class SceneConfigEditor(QWidget):

    scene_loaded = pyqtSignal(int,int,int,float,float)
    def __init__(self,initial_config_file=None):
        super().__init__()
        self.initial_config_file = initial_config_file

        # Create a QScrollArea
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)

        # Create a widget for the scroll area
        scroll_widget = QWidget()

        self.scenes_directory = QLineEdit()


        self.directories_combo = QComboBox()




        self.scene_dimension_x = QLineEdit()
        self.scene_dimension_x.setReadOnly(True)  # The dimensions should be read-only
        self.scene_dimension_y = QLineEdit()
        self.scene_dimension_y.setReadOnly(True)  # The dimensions should be read-only
        self.scene_nb_of_spectral_bands = QLineEdit()
        self.scene_nb_of_spectral_bands.setReadOnly(True)  # The dimensions should be read-only
        self.minimum_wavelengths = QLineEdit()
        self.minimum_wavelengths.setReadOnly(True)  # The dimensions should be read-only
        self.maximum_wavelengths = QLineEdit()
        self.maximum_wavelengths.setReadOnly(True)  # The dimensions should be read-only

        self.scene_loaded.connect(self.update_scene_dimensions)

        # Add the dimensioning configuration editor, the result display widget, and the run button to the layout


        scene_layout = QFormLayout()
        scene_layout.addRow("scenes directory", self.scenes_directory)

        self.reload_scenes_button = QPushButton('reload scenes')
        self.reload_scenes_button.clicked.connect(self.load_scenes)

        scene_layout.addWidget(self.reload_scenes_button)

        chosen_scene = QFormLayout()



        chosen_scene.addRow("scene name",self.directories_combo)
        chosen_scene.addRow("dimension along X", self.scene_dimension_x)
        chosen_scene.addRow("dimension along Y", self.scene_dimension_y)
        chosen_scene.addRow("number of spectral bands", self.scene_nb_of_spectral_bands)
        chosen_scene.addRow("minimum wavelength", self.minimum_wavelengths)
        chosen_scene.addRow("maximum wavelength", self.maximum_wavelengths)

        chosen_scene_group = QGroupBox("Chosen Scene")
        chosen_scene_group.setLayout(chosen_scene)

        # scene_layout.addRow("chosen scene", chosen_scene)


        scene_group = QGroupBox("Settings")
        scene_group.setLayout(scene_layout)




        main_layout = QVBoxLayout()
        main_layout.addWidget(scene_group)
        main_layout.addWidget(chosen_scene_group)



        # Set the layout on the widget within the scroll area
        scroll_widget.setLayout(main_layout)

        # Set the widget for the scroll area
        scroll.setWidget(scroll_widget)

        # Create a layout for the current widget and add the scroll area
        layout = QVBoxLayout(self)
        layout.addWidget(scroll)

        # Load the initial configuration file if one was provided
        if self.initial_config_file is not None:
            self.load_config(initial_config_file)

        self.load_scenes()


    def load_scene(self):


            img, gt, list_wavelengths, label_values, ignored_labels, rgb_bands, palette, delta_lambda = get_dataset(self.directories_combo.currentText(), self.scenes_directory.text())
            self.scene = img
            self.scene_gt = gt
            self.list_wavelengths = list_wavelengths
            self.scene_label_values = label_values
            self.scene_ignored_labels = ignored_labels
            self.scene_rgb_bands = rgb_bands
            self.scene_palette = palette
            self.scene_delta_lambda = delta_lambda

            self.scene_palette = palette_init(label_values, palette)
            #
            # print("Error: scene not found")
            self.scene_loaded.emit(self.scene.shape[1],self.scene.shape[0],self.scene.shape[2],list_wavelengths[0],list_wavelengths[-1])

    def interpolate_scene(self,new_sampling):
        self.scene_interpolated = interpolate_scene_cube_along_wavelength(self.scene, self.list_wavelengths, new_sampling)
        return self.scene_interpolated

    def load_scenes(self):

        scene_dir = self.scenes_directory.text()
        self.directories_combo.clear()
        if os.path.isdir(scene_dir):
            sub_dirs = [name for name in os.listdir(scene_dir)
                        if os.path.isdir(os.path.join(scene_dir, name))]
            self.directories_combo.clear()
            self.directories_combo.addItems(sub_dirs)

    def load_config(self, file_name):
        with open(file_name, 'r') as file:
            self.config = yaml.safe_load(file)
        # Call a method to update the GUI with the loaded config
        self.update_config()
    def update_config(self):
        # This method should update your QLineEdit and QSpinBox widgets with the loaded config.
        self.scenes_directory.setText(self.config['scenes directory'])


    @pyqtSlot(int,int,int,float,float)
    def update_scene_dimensions(self, x_dim,y_dim,wav_dim,min_wav,max_wav):
        # Update the GUI in this slot function, which is called from the main thread
        self.scene_dimension_x.setText(str(x_dim))
        self.scene_dimension_y.setText(str(y_dim))
        self.scene_nb_of_spectral_bands.setText(str(wav_dim))
        self.minimum_wavelengths.setText(str(min_wav))
        self.maximum_wavelengths.setText(str(max_wav))


class Worker(QThread):
    finished_load_scene = pyqtSignal(np.ndarray,list)
    finished_explore_scene = pyqtSignal(dict,dict,list)
    finished_scene_labelisation = pyqtSignal(np.ndarray, list, dict)
    finished_scene_label_histogram = pyqtSignal(np.ndarray, list, list,dict)

    def __init__(self,scene_config_editor):
        super().__init__()

        self.scene_config_editor = scene_config_editor

    def run(self):

        self.scene_config_editor.load_scene()
        self.stats_per_class = explore_spectrums(self.scene_config_editor.scene, self.scene_config_editor.scene_gt, self.scene_config_editor.scene_label_values,
                          ignored_labels=self.scene_config_editor.scene_ignored_labels, delta_lambda=None)


        self.finished_load_scene.emit(self.scene_config_editor.scene,self.scene_config_editor.list_wavelengths)  # Emit a tuple of arrays
        self.finished_explore_scene.emit(self.stats_per_class,self.scene_config_editor.scene_palette,self.scene_config_editor.scene_label_values)
        self.finished_scene_labelisation.emit(self.scene_config_editor.scene_gt,self.scene_config_editor.scene_label_values,self.scene_config_editor.scene_palette)# Emit a tuple of arrays
        self.finished_scene_label_histogram.emit(self.scene_config_editor.scene_gt,self.scene_config_editor.scene_label_values,self.scene_config_editor.scene_ignored_labels,self.scene_config_editor.scene_palette)
class SceneWidget(QWidget):
    def __init__(self,scene_config_path="config/scene.yml"):
        super().__init__()

        self.layout = QHBoxLayout()

        if scene_config_path is not None:
            self.scene_config_editor = SceneConfigEditor(scene_config_path)

        self.layout.addWidget(self.scene_config_editor)

        self.result_display_widget = QTabWidget()

        self.scene_content_display = SceneContentDisplay()
        self.scene_spectral_data_display = SpectralDataDisplay()
        self.scene_labelisation_display = SceneLabelisation()
        self.scene_label_histogram = SceneHistogram()

        self.result_display_widget.addTab(self.scene_content_display, "Scene Content")
        self.result_display_widget.addTab(self.scene_spectral_data_display, "Scene Caracterization")
        self.result_display_widget.addTab(self.scene_labelisation_display, "Scene Labelisation")
        self.result_display_widget.addTab(self.scene_label_histogram, "Scene Labels Histogram")


        self.run_button = QPushButton('Load Scene')
        self.run_button.setStyleSheet('QPushButton {background-color: green; color: white;}')        # Connect the button to the run_dimensioning method
        self.run_button.clicked.connect(self.run_load_scene)

        # Create a group box for the run button
        self.run_button_group_box = QGroupBox()
        run_button_group_layout = QVBoxLayout()

        run_button_group_layout.addWidget(self.run_button)
        run_button_group_layout.addWidget(self.result_display_widget)

        self.run_button_group_box.setLayout(run_button_group_layout)
        self.layout.addWidget(self.run_button_group_box)


        self.layout.setStretchFactor(self.run_button_group_box, 1)
        self.layout.setStretchFactor(self.result_display_widget, 3)
        self.setLayout(self.layout)
    #
    def run_load_scene(self):
        # Get the configs from the editors

        self.worker = Worker(self.scene_config_editor)
        self.worker.finished_load_scene.connect(self.display_scene_content)
        self.worker.finished_explore_scene.connect(self.display_spectral_data)
        self.worker.finished_scene_labelisation.connect(self.display_ground_truth)
        self.worker.finished_scene_label_histogram.connect(self.scene_label_histogram.plot_label_histogram)
        self.worker.start()

    @pyqtSlot(np.ndarray,list)
    def display_scene_content(self, scene,list_wavelengths):
        self.scene = scene
        self.scene_content_display.diplay_scene_content(scene,list_wavelengths)


    @pyqtSlot(dict,dict,list)
    def display_spectral_data(self,stats_class,palette,label_values):

        mean_spectrums, std_spectrums= stats_class["mean_spectrums"], stats_class["std_spectrums"]
        self.scene_spectral_data_display.display_spectral_data(mean_spectrums, std_spectrums,palette, label_values)

    @pyqtSlot(np.ndarray, list, dict)
    def display_ground_truth(self,ground_truth, label_values, palette):
        self.scene_labelisation_display.display_ground_truth(ground_truth, label_values, palette)

    @pyqtSlot(np.ndarray, list, list,dict)
    def display_plot_label_histogram(self, ground_truth, label_values, ignored_labels,palette):
        self.scene_label_histogram.plot_label_histogram(ground_truth, label_values, ignored_labels,palette)
