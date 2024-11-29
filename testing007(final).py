import sys
import threading
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QSlider, QLineEdit, QCheckBox, QWidget, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer
from pyqtgraph import PlotWidget
import os


class Motor:
    """Represents a single motor and its operations."""
    def __init__(self, name, port, axis, position_file="motor_positions.txt"):
        self.name = name
        self.port = port
        self.axis = axis
        self.current_position = 0
        self.max_position = 40  # Set the maximum position limit (length of the pole)
        self.target_position = 0  # Target position for movement
        self.is_moving = False
        self.position_file = position_file

        # Try to load the stored position from the file
        self.load_position()

    def move(self, steps):
        """Simulate moving the motor with a delay and within the limits."""
        # Ensure the movement stays within the maximum limit of 40
        if self.current_position + steps > self.max_position:
            steps = self.max_position - self.current_position
        elif self.current_position + steps < 0:
            steps = -self.current_position  # Prevent negative positions

        self.target_position = self.current_position + steps
        self.is_moving = True
        print(f"{self.name} started moving to position {self.target_position}")

    def update_position(self):
        """Update the motor's position gradually during movement."""
        if self.is_moving:
            if self.current_position < self.target_position:
                self.current_position += 1
            elif self.current_position > self.target_position:
                self.current_position -= 1

            if self.current_position == self.target_position:
                self.is_moving = False
                print(f"{self.name} reached target position {self.target_position}")
                self.save_position()  # Save position when target is reached

    def set_home(self):
        """Set the current position as home."""
        self.current_position = 0
        self.target_position = 0
        self.is_moving = False
        print(f"{self.name} home position set to {self.current_position}")
        self.save_position()  # Save position after setting home

    def save_position(self):
        """Save the current position to a file."""
        with open(self.position_file, "a") as file:
            file.write(f"{self.name}: {self.current_position}\n")
        print(f"Position of {self.name} saved: {self.current_position}")

    def load_position(self):
        """Load the stored position from the file."""
        if os.path.exists(self.position_file):
            with open(self.position_file, "r") as file:
                lines = file.readlines()
                for line in lines:
                    if line.startswith(self.name):
                        # Extract the position from the line
                        self.current_position = int(line.split(":")[1].strip())
                        self.target_position = self.current_position
                        print(f"Position of {self.name} loaded: {self.current_position}")


class MotorController:
    """Manages multiple motors."""
    def __init__(self):
        self.motors = []

    def add_motor(self, name, port, axis):
        motor = Motor(name, port, axis)
        self.motors.append(motor)

    def move_motor(self, motor_name, steps):
        motor = next((m for m in self.motors if m.name == motor_name), None)
        if motor:
            motor.move(steps)

    def move_multiple_motors(self, motor_steps):
        """Start moving multiple motors at once."""
        for motor_name, steps in motor_steps.items():
            motor = next((m for m in self.motors if m.name == motor_name), None)
            if motor:
                motor.move(steps)


class MotorControlGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.controller = MotorController()
        self.initUI()

        # Timer to update the motor's movement and the graph
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_motor_positions)
        self.update_timer.start(100)  # Update every 100ms

    def initUI(self):
        self.setWindowTitle("Motor Control GUI")
        self.setGeometry(100, 100, 1000, 700)

        # Main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Arduino and Motor Configuration
        config_layout = QHBoxLayout()
        self.arduino_count_input = QSpinBox()
        self.arduino_count_input.setRange(1, 9000)
        self.arduino_count_input.setValue(4)
        config_layout.addWidget(QLabel("Number of Arduinos:"))
        config_layout.addWidget(self.arduino_count_input)

        self.motor_count_input = QSpinBox()
        self.motor_count_input.setRange(1, 9000)
        self.motor_count_input.setValue(10)
        config_layout.addWidget(QLabel("Number of Motors:"))
        config_layout.addWidget(self.motor_count_input)

        generate_button = QPushButton("Generate Motors")
        generate_button.clicked.connect(self.generate_motors)
        config_layout.addWidget(generate_button)
        main_layout.addLayout(config_layout)

        # Motor Control Area
        self.motor_control_layout = QGridLayout()
        self.motor_checkboxes = []
        self.motor_inputs = []
        self.update_motor_controls()

        main_layout.addLayout(self.motor_control_layout)

        # Buttons for operations
        button_layout = QHBoxLayout()
        move_button = QPushButton("Move Selected Motors")
        move_button.clicked.connect(self.move_selected_motors)
        button_layout.addWidget(move_button)

        home_button = QPushButton("Set Selected Motors Home")
        home_button.clicked.connect(self.home_selected_motors)
        button_layout.addWidget(home_button)

        main_layout.addLayout(button_layout)

        # Graph
        self.graph = PlotWidget()
        self.graph.setLabel('left', 'Position')
        self.graph.setLabel('bottom', 'Motors')
        self.graph.addLegend()
        self.graph_data = []
        self.update_graph()
        main_layout.addWidget(self.graph)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def update_motor_controls(self):
        """Update the motor control UI."""
        # Clear previous controls
        for i in reversed(range(self.motor_control_layout.count())):
            self.motor_control_layout.itemAt(i).widget().setParent(None)

        self.motor_checkboxes = []
        self.motor_inputs = []

        # Add new controls
        for i, motor in enumerate(self.controller.motors):
            checkbox = QCheckBox(motor.name)
            self.motor_checkboxes.append(checkbox)
            self.motor_control_layout.addWidget(checkbox, i, 0)

            input_box = QLineEdit()
            input_box.setPlaceholderText("Move steps")
            self.motor_inputs.append(input_box)
            self.motor_control_layout.addWidget(input_box, i, 1)

    # def generate_motors(self):
    #     """Generate motors based on input configuration."""
    #     num_arduinos = self.arduino_count_input.value()
    #     num_motors = self.motor_count_input.value()
    #
    #     self.controller.motors.clear()
    #     motor_count = 0
    #     for i in range(num_arduinos):
    #         max_motors = 1 if i == 0 else 3
    #         for j in range(min(max_motors, num_motors - motor_count)):
    #             motor_name = f"Arduino {i+1} Motor {j+1}"
    #             self.controller.add_motor(motor_name, f"COM{i+1}", "X")
    #             motor_count += 1
    #             if motor_count >= num_motors:
    #                 break
    #
    #     self.update_motor_controls()
    def generate_motors(self):
        """Generate motors based on input configuration."""
        num_arduinos = self.arduino_count_input.value()
        num_motors = self.motor_count_input.value()

        self.controller.motors.clear()  # Clear the current motors list
        motor_count = 0  # Counter for assigned motors

        # Check if motors can be evenly distributed among Arduinos
        if num_motors % num_arduinos == 0:
            motors_per_arduino = num_motors // num_arduinos
        else:
            motors_per_arduino = 3  # Default to 3 motors for all but the first Arduino

        for i in range(num_arduinos):
            if i == 0 and num_motors % num_arduinos != 0:
                # First Arduino takes the remainder if motors can't be evenly distributed
                max_motors = num_motors % num_arduinos or 1
            else:
                # Remaining Arduinos take 3 motors (or equal share in case of divisibility)
                max_motors = motors_per_arduino

            # Assign motors to the current Arduino
            for j in range(min(max_motors, num_motors - motor_count)):
                motor_name = f"Arduino {i + 1} Motor {j + 1}"
                self.controller.add_motor(motor_name, f"COM{i + 1}", "X")
                motor_count += 1

                # Stop when all motors are assigned
                if motor_count >= num_motors:
                    break

        self.update_motor_controls()  # Update UI or motor controls

    def move_selected_motors(self):
        """Move selected motors."""
        motor_steps = {}
        for checkbox, input_box, motor in zip(self.motor_checkboxes, self.motor_inputs, self.controller.motors):
            if checkbox.isChecked():
                try:
                    steps = int(input_box.text())
                    # Ensure the steps don't exceed the limit
                    if steps > motor.max_position:
                        steps = motor.max_position
                    motor_steps[motor.name] = steps
                except ValueError:
                    pass  # Ignore invalid inputs

        self.controller.move_multiple_motors(motor_steps)
        self.update_graph()

    def home_selected_motors(self):
        """Set home for selected motors."""
        for checkbox, motor in zip(self.motor_checkboxes, self.controller.motors):
            if checkbox.isChecked():
                motor.set_home()
        self.update_graph()

    def update_motor_positions(self):
        """Update motor positions in real-time and update the graph."""
        for motor in self.controller.motors:
            motor.update_position()  # Move the motor step by step

        self.update_graph()

    def update_graph(self):
        """Update the graph to show motor positions."""
        positions = [motor.current_position for motor in self.controller.motors]
        motor_labels = [motor.name for motor in self.controller.motors]

        self.graph.clear()
        self.graph.plot(range(len(positions)), positions, pen="g", name="Positions", symbol='o')

        # Set custom labels for the x-axis to show both Arduino and Motor
        x_axis = self.graph.getAxis('bottom')
        x_axis.setTicks([[(i, label) for i, label in enumerate(motor_labels)]])
        self.graph.setXRange(0, len(motor_labels) - 1)  # Adjust the x-axis range to fit the number of motors


# Main Function
if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = MotorControlGUI()
    gui.show()
    sys.exit(app.exec_())
