import sys
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QPushButton, QComboBox, QMessageBox, QFrame, QCheckBox
)
from PyQt5.QtCore import Qt
import time
import subprocess
import os
import pyqtgraph as pg


class Motor:
    def __init__(self, name, port, axis):
        self.name = name
        self.port = port
        self.axis = axis
        self.current_position = 0  # Add this attribute to store the current position
        self.target_position = 0  # Target position (can be used for movement logic)

    def move(self, steps):
        """Move the motor by the specified number of steps."""
        self.current_position += steps

    def set_home(self):
        """Set the motor to the home position."""
        self.current_position = 0

    def save_position(self):
        """Save the current position."""
        # You could save the position to a file or database here, if needed.
        pass

    def update_position(self):
        """Update the motor position (if necessary)."""
        # This could be used to simulate position updates from a controller or external system.
        pass


class ArduinoConfigurator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arduino Configurator")
        self.setGeometry(300, 150, 800, 600)

        self.num_arduinos = 0
        self.arduino_widgets = []
        self.com_ports = []
        self.arduino_configs = []

        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)

        # Top row: Arduino count
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

        # Middle row: Arduino configuration
        self.arduino_frame = QFrame(self)
        self.arduino_frame.setStyleSheet("border: 1px solid #ccc; background-color: #f9f9f9;")
        self.arduino_layout = QVBoxLayout(self.arduino_frame)
        self.main_layout.addWidget(self.arduino_frame)

        # Bottom row: Buttons
        self.bottom_row_frame = QFrame(self)
        self.bottom_row_frame.setFixedHeight(80)
        self.bottom_row_layout = QHBoxLayout(self.bottom_row_frame)

        self.set_arduino_button = QPushButton("Set Arduino Count")
        self.set_arduino_button.clicked.connect(self.reset_arduino_inputs)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.open_motor_config)

        self.bottom_row_layout.addStretch()
        self.bottom_row_layout.addWidget(self.set_arduino_button)
        self.bottom_row_layout.addWidget(self.next_button)
        self.bottom_row_layout.addStretch()

        self.main_layout.addWidget(self.bottom_row_frame)

    def reset_arduino_inputs(self):
        self.num_arduinos = self.num_arduinos_spinner.value()
        self.clear_arduino_widgets()

        if self.num_arduinos > 0:
            self.update_arduino_inputs()

    def clear_arduino_widgets(self):
        """Completely clears the Arduino configuration area, removing all widgets and resetting the layout."""
        while self.arduino_layout.count() > 0:
            item = self.arduino_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.arduino_widgets.clear()

    def update_arduino_inputs(self):
        self.com_ports = self.scan_com_ports()

        for i in range(self.num_arduinos):
            row_layout = QHBoxLayout()

            label = QLabel(f"Arduino {i + 1}:")
            combo_box = QComboBox()
            combo_box.addItem("Not Assigned")
            combo_box.addItems(self.com_ports)

            row_layout.addWidget(label)
            row_layout.addWidget(combo_box)

            container_widget = QWidget()
            container_widget.setLayout(row_layout)

            self.arduino_layout.addWidget(container_widget)
            self.arduino_widgets.append((label, combo_box))

    def scan_com_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def open_motor_config(self):
        # Check if any valid COM port is assigned
        self.arduino_configs = []
        for label, combo_box in self.arduino_widgets:
            selected_port = combo_box.currentText()
            if selected_port != "Not Assigned":
                self.arduino_configs.append(selected_port)

        if not self.arduino_configs:
            QMessageBox.warning(self, "Warning", "No Arduinos assigned! Using mock data for testing.")
            self.arduino_configs = ["COM_TEST_1", "COM_TEST_2"]

        # Open Motor Config Window
        self.motor_config_window = MotorConfigurator(self.arduino_configs)
        self.motor_config_window.show()
        self.close()


class MotorConfigurator(QMainWindow):
    def __init__(self, arduino_configs):
        super().__init__()
        self.setWindowTitle("Motor Configurator")
        self.setGeometry(300, 150, 800, 600)

        self.arduino_configs = arduino_configs
        self.selected_motors = {}

        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)

        # Display each Arduino with checkboxes for motors
        for port in self.arduino_configs:
            group_frame = QFrame(self)
            group_frame.setStyleSheet("border: 1px solid #ccc; background-color: #e9f7ff; margin-bottom: 10px;")
            group_layout = QVBoxLayout(group_frame)

            label = QLabel(f"Arduino ({port}):")
            label.setStyleSheet("font-weight: bold;")
            group_layout.addWidget(label)

            motor_checkboxes = {}
            for axis in ["X", "Y", "Z"]:
                checkbox = QCheckBox(f"Motor ({axis})")
                motor_checkboxes[axis] = checkbox
                group_layout.addWidget(checkbox)

            self.selected_motors[port] = motor_checkboxes
            self.main_layout.addWidget(group_frame)

        # Set Configuration Button
        self.button_layout = QHBoxLayout()
        self.set_config_button = QPushButton("Set Configuration")
        self.set_config_button.clicked.connect(self.run_graph)
        self.set_config_button.setStyleSheet("font-size: 14px; padding: 10px;")
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.set_config_button)
        self.button_layout.addStretch()

        self.main_layout.addLayout(self.button_layout)

    def run_graph(self):
            # Extract motor selection and open the graph window
            motors_to_display = self.get_selected_motors()

            # Open Graph Window
            self.graph_window = MotorGraphWindow(motors_to_display)
            self.graph_window.show()
            self.close()

    def get_selected_motors(self):
        selected_motors = []
        for port, motor_checkboxes in self.selected_motors.items():
            for axis, checkbox in motor_checkboxes.items():
                if checkbox.isChecked():
                    selected_motors.append(Motor(f"{axis} Motor", port, axis))
        return selected_motors

class MotorGraphWindow(QMainWindow):
    def __init__(self, motors_to_display):
        super().__init__()
        self.setWindowTitle("Motor Graph")
        self.setGeometry(300, 150, 800, 600)

        self.motors = motors_to_display  # Store the motors to be displayed
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)

        # Create the plot widget
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setMouseEnabled(False)  # Lock movement of the graph
        self.graph_widget.setYRange(0, 40, padding=0)  # Lock Y-axis to a fixed range
        self.graph_widget.setXRange(0, 80, padding=0)  # Lock X-axis to show a 40-unit window
        self.main_layout.addWidget(self.graph_widget)

        # Initialize a plot for each motor with a specific color
        self.motor_plots = {}
        for motor in self.motors:
            # Create a plot for each motor and assign a color (e.g., red for all)
            pen_color = (255, 0, 0)  # Red color by default
            plot = self.graph_widget.plot(pen=pg.mkPen(color=pen_color))  
            self.motor_plots[motor.name] = plot

        # Timer to update motor positions every 500ms
        self.timer = pg.QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_graph)
        self.timer.start(500)

        # Buttons for motor control
        button_layout = QHBoxLayout()

        move_button = QPushButton("Move Motors")
        move_button.clicked.connect(self.move_selected_motors)
        button_layout.addWidget(move_button)

        home_button = QPushButton("Set Motors Home")
        home_button.clicked.connect(self.home_selected_motors)
        button_layout.addWidget(home_button)

        self.main_layout.addLayout(button_layout)

    def update_graph(self):
        """Update the graph with the current motor positions."""
        for motor in self.motors:
            self.motor_plots[motor.name].setData([motor.current_position])

    def move_selected_motors(self):
        """Move selected motors."""
        for motor in self.motors:
            motor.move(5)  # Example move of 5 steps
            motor.update_position()  # Update the motor position
        self.update_graph()

    def home_selected_motors(self):
        """Set selected motors to home position."""
        for motor in self.motors:
            motor.set_home()  # Set the motor to home
        self.update_graph()

# Main Function

if __name__ == "__main__":
    app = QApplication(sys.argv)
    configurator = ArduinoConfigurator()
    configurator.show()
    sys.exit(app.exec_())
