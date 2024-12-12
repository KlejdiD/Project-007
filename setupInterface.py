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

from graphicalInterface import MotorControlGUI


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
        self.num_arduinos_spinner.setMinimum(1)
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
            # if selected_port != "Not Assigned":
            self.arduino_configs.append(selected_port)

        # if not self.arduino_configs:
        #     QMessageBox.warning(self, "Warning", "No Arduinos assigned! Using mock data for testing.")
        #     self.arduino_configs = ["COM_TEST_1", "COM_TEST_2"]

        # Open Motor Config Window
        self.motor_config_window = MotorConfigurator(self.arduino_configs)
        self.motor_config_window.show()
        self.close()


from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QFrame, QCheckBox, QLabel, QPushButton, QScrollArea, QWidget
from PyQt5.QtCore import Qt

class MotorConfigurator(QMainWindow):
    def __init__(self, arduino_configs):
        super().__init__()
        self.setWindowTitle("Motor Configurator")
        self.setGeometry(300, 150, 800, 600)

        self.arduino_configs = arduino_configs
        self.selected_motors = {}

        self.init_ui()

    def init_ui(self):
        # Create central widget for the window
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Create main layout for central widget
        self.main_layout = QVBoxLayout(self.central_widget)

        # Create a scroll area to allow scrolling when content overflows
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)  # Make the widget inside resizeable

        # Create a widget to hold the motor controls inside the scroll area
        scroll_content_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_content_widget)

        # Display each Arduino with checkboxes for motors
        for index, port in enumerate(self.arduino_configs, 1):  # Start enumeration from 1
            group_frame = QFrame(self)
            group_frame.setStyleSheet("border: 1px solid #ccc; background-color: #e9f7ff; margin-bottom: 10px;")
            group_layout = QVBoxLayout(group_frame)

            # If the port is not assigned, use a logical Arduino name
            port_label = f"Arduino {index} ({port})"
            label = QLabel(port_label)  # Show Arduino number and port (if available)
            label.setStyleSheet("font-weight: bold;")
            group_layout.addWidget(label)

            motor_checkboxes = {}
            for axis in ["X", "Y", "Z"]:
                checkbox = QCheckBox(f"Motor ({axis})")
                motor_checkboxes[axis] = checkbox
                group_layout.addWidget(checkbox)

            # Use logical Arduino ID for motor grouping
            self.selected_motors[port_label] = motor_checkboxes
            scroll_layout.addWidget(group_frame)

        # Add scroll area containing motor control content
        scroll_area.setWidget(scroll_content_widget)
        self.main_layout.addWidget(scroll_area)

        # Set Configuration Button
        self.button_layout = QHBoxLayout()
        self.set_config_button = QPushButton("Set Configuration")
        self.set_config_button.clicked.connect(self.run_graph)
        self.set_config_button.setStyleSheet("font-size: 14px; padding: 10px;")
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.set_config_button)
        self.button_layout.addStretch()

        # Add the button layout to the main layout
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
        for i, (port, motor_checkboxes) in enumerate(self.selected_motors.items()):
            arduino_label = f"Arduino {i + 1}"  # Add Arduino label
            for axis, checkbox in motor_checkboxes.items():
                if checkbox.isChecked():
                    motor_name = f"{arduino_label} - Motor {axis}"  # Group by Arduino
                    selected_motors.append(Motor(motor_name, port, axis))
        return selected_motors


class MotorGraphWindow(MotorControlGUI):
    def __init__(self, motors_to_display):
        super().__init__()
        self.setWindowTitle("Motor Graph")
        self.setGeometry(300, 150, 1200, 800)
        
        # Clear existing motors in MotorControlGUI
        self.controller.motors = []

        # Add only the selected motors to the controller
        for motor in motors_to_display:
            self.add_motor(motor.name, motor.axis)

        # Update the UI to reflect the new set of motors
        self.update_motor_controls()
        self.update_graph()

    def update_motor_positions(self):
        """Override to update only the passed motors."""
        for motor in self.controller.motors:
            motor.update_position()

        self.update_graph()

    def home_selected_motors(self):
        """Override to reset home for selected motors."""
        for checkbox, motor in zip(self.motor_checkboxes, self.controller.motors):
            if checkbox.isChecked():
                motor.set_home()
        self.update_graph()

""" def move_selected_motors(self):
        motor_steps = {}
        for checkbox, input_box, motor in zip(self.motor_checkboxes, self.motor_inputs, self.controller.motors):
            if checkbox.isChecked():
                try:
                    steps = int(input_box.text())
                    motor_steps[motor.name] = steps
                except ValueError:
                    pass  # Ignore invalid inputs

        self.controller.move_multiple_motors(motor_steps)
        self.update_graph()"""

def move_selected_motors(self):
    """Override to move only the selected motors."""
    motor_steps = {}
    for checkbox, input_box, motor in zip(self.motor_checkboxes, self.motor_inputs, self.controller.motors):
        if checkbox.isChecked():
            try:
                steps = int(input_box.text())
                if -40 <= steps <= 40:  # Validate the range
                    motor_steps[motor.name] = steps
                else:
                    print(f"Input {steps} out of range for motor {motor.name}. Must be between -40 and 40.")
            except ValueError:
                print(f"Invalid input for motor {motor.name}. Must be an integer.")

    self.controller.move_multiple_motors(motor_steps)
    self.update_graph()


# Main Function

if __name__ == "__main__":
    app = QApplication(sys.argv)
    configurator = ArduinoConfigurator()
    configurator.show()
    sys.exit(app.exec_())
