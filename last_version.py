import sys
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QPushButton, QComboBox, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt


class ArduinoConfigurator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arduino Configurator")
        self.setGeometry(300, 150, 800, 600)

        self.num_arduinos = 0
        self.arduino_widgets = []
        self.com_ports = []

        self.init_ui()

    def init_ui(self):
        """Initializes the user interface."""
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Main vertical layout
        self.main_layout = QVBoxLayout(self.central_widget)

        # Top row (Number of Arduinos)
        self.top_row_frame = QFrame(self)
        self.top_row_frame.setFixedHeight(80)
        self.top_row_layout = QHBoxLayout(self.top_row_frame)
        self.num_arduinos_label = QLabel("Number of Arduinos:")
        self.num_arduinos_spinner = QSpinBox()
        self.num_arduinos_spinner.setMinimum(0)
        self.num_arduinos_spinner.setMaximum(10)

        self.top_row_layout.addWidget(self.num_arduinos_label)
        self.top_row_layout.addWidget(self.num_arduinos_spinner)
        self.main_layout.addWidget(self.top_row_frame)

        # Middle area (Arduino configuration)
        self.arduino_frame = QFrame(self)
        self.arduino_frame.setStyleSheet("border: 1px solid #ccc; background-color: #f9f9f9;")
        self.arduino_layout = QVBoxLayout(self.arduino_frame)
        self.main_layout.addWidget(self.arduino_frame)

        # Bottom row (Buttons)
        self.bottom_row_frame = QFrame(self)
        self.bottom_row_frame.setFixedHeight(80)
        self.bottom_row_layout = QHBoxLayout(self.bottom_row_frame)

        self.set_arduino_button = QPushButton("Set Arduino Count")
        self.set_arduino_button.clicked.connect(self.reset_arduino_inputs)

        self.set_config_button = QPushButton("Set Configuration")
        self.set_config_button.clicked.connect(self.set_configuration)

        self.bottom_row_layout.addStretch()  # Spacer
        self.bottom_row_layout.addWidget(self.set_arduino_button)
        self.bottom_row_layout.addWidget(self.set_config_button)
        self.bottom_row_layout.addStretch()  # Spacer

        self.main_layout.addWidget(self.bottom_row_frame)

    def reset_arduino_inputs(self):
        """Fully resets the Arduino COM inputs when the 'Set Arduino Count' button is pressed."""
        self.num_arduinos = self.num_arduinos_spinner.value()

        # Clear existing widgets
        self.clear_arduino_widgets()

        # Rebuild the inputs if the number of Arduinos is greater than 0
        if self.num_arduinos > 0:
            self.update_arduino_inputs()

    def clear_arduino_widgets(self):
        """Completely removes all widgets in the Arduino layout."""
        for widget in self.arduino_widgets:
            self.arduino_layout.removeWidget(widget)
            widget.deleteLater()
        self.arduino_widgets.clear()  # Clear the list of tracked widgets

    def update_arduino_inputs(self):
        """Creates dropdown menus for Arduino-to-COM port assignments."""
        self.com_ports = self.scan_com_ports()

        for i in range(self.num_arduinos):
            row_layout = QHBoxLayout()

            label = QLabel(f"Arduino {i + 1}:")
            combo_box = QComboBox()
            combo_box.addItem("Not Assigned")
            combo_box.addItems(self.com_ports)

            # Add to layout and track widgets
            row_layout.addWidget(label)
            row_layout.addWidget(combo_box)

            container_widget = QWidget()
            container_widget.setLayout(row_layout)

            self.arduino_layout.addWidget(container_widget)
            self.arduino_widgets.append(container_widget)

    def scan_com_ports(self):
        """Returns a list of available COM ports."""
        return [port.device for port in serial.tools.list_ports.comports()]

    def set_configuration(self):
        """Validates the configuration and shows the result."""
        if self.num_arduinos == 0:
            QMessageBox.warning(self, "Configuration Error", "No Arduinos specified!")
            return

        assigned_ports = []
        for widget in self.arduino_widgets:
            combo_box = widget.findChild(QComboBox)
            if combo_box.currentText() != "Not Assigned":
                assigned_ports.append(combo_box.currentText())

        if not assigned_ports:
            QMessageBox.warning(self, "Configuration Error", "No Arduinos have been assigned to COM ports!")
        else:
            QMessageBox.information(self, "Configuration Set", f"Configuration complete: {', '.join(assigned_ports)}")
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    configurator = ArduinoConfigurator()
    configurator.show()
    sys.exit(app.exec_())
