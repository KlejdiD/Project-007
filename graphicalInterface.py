import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QCheckBox, QWidget, QSpinBox, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt, QTimer
from pyqtgraph import PlotWidget
import os
import serial
import time

class Motor:
    """Represents a single motor and its operations."""
    def __init__(self, name, axis, port, position_file="motor_positions.json"):
        self.name = name
        self.axis = axis
        self.port = port
        self.current_position = 0
        self.max_position = 40  # Maximum position limit
        self.target_position = 0
        self.is_moving = False
        self.position_file = position_file
        self.arduino = None


        self.connect()
        

        self.load_position()



    def connect(self):
        """Open a serial connection to the motor."""
        if self.arduino is None or not self.arduino.is_open:
                self.arduino = serial.Serial(self.port, 115200)
                time.sleep(2)  # Allow time for the connection to initialize
                print("Connected!" + self.name + self.port)

    def disconnect(self):
        """Close the serial connection."""
        if self.arduino and self.arduino.is_open:
            self.arduino.close()

    def send_command(self, command):
        """Send a raw command to the motor."""
        self.connect()
        self.arduino.write(str.encode("\r\n\r\n"))  # GRBL wake-up sequence
        self.arduino.write(str.encode(f"{command}") + b'\n')
        time.sleep(0.1)  # Allow time for the command to process


    def move(self, steps):
        """Move the motor by the specified number of steps."""
        command_set_system = "$J=G21G90"
        move_command = f"G0{self.axis}{steps}"
        self.send_command(command_set_system)
        self.send_command(move_command)
        return print( f"{self.name} has moved {steps}")

    def set_home(self):
        """Set the current position of the motor as home."""
        command_set_system = "$J=G21G90"
        command_set_home = f"G92{self.axis}0"
        self.send_command(command_set_system)
        self.send_command(command_set_home)
        return print("Home set")



    def home(self):
        """Move the motor to its home position."""
        command_set_system = "$J=G21G90"
        command_move_home = f"G0{self.axis}0"
        self.send_command(command_set_system)
        self.send_command(command_move_home)
        return print(f"{self.name} moved home")

    def __del__(self):
        """Ensure the connection is closed when the object is deleted."""
        self.disconnect()
        return print(f"disconnected {self.name}")

    

    def move(self, steps):
        """Simulate moving the motor."""
        if self.current_position + steps > self.max_position:
            steps = self.max_position - self.current_position
        elif self.current_position + steps < 0:
            steps = -self.current_position

        self.target_position = self.current_position + steps
        self.is_moving = True
        print(f"{self.name} moving to position {self.target_position}")

    def update_position(self):
        """Update motor position step by step."""
        if self.is_moving:
            if self.current_position < self.target_position:
                self.current_position += 1
            elif self.current_position > self.target_position:
                self.current_position -= 1

            if self.current_position == self.target_position:
                self.is_moving = False
                self.save_position()

    def set_home(self):
        """Set the motor's current position as home."""
        self.current_position = 0
        self.target_position = 0
        self.is_moving = False
        print(f"{self.name} set to home position.")
        self.save_position()

    def save_position(self):
        """Save motor position to a file."""
        with open(self.position_file, "a") as file:
            file.write(f"{self.name}: {self.current_position}\n")
        print(f"{self.name} position saved: {self.current_position}")

    def load_position(self):
        """Load motor position from a file."""
        if os.path.exists(self.position_file):
            with open(self.position_file, "r") as file:
                lines = file.readlines()
                for line in lines:
                    if line.startswith(self.name):
                        self.current_position = int(line.split(":")[1].strip())
                        self.target_position = self.current_position
                        print(f"{self.name} position loaded: {self.current_position}")

class MotorController:
    

    """Manages multiple motors."""
    def __init__(self, motors_config):
        self.motors = [Motor(m["name"], m["port"], m["axis"]) for m in motors_config]

    def get_motor(self, motor_name):
        """Retrieve a motor by its name."""
        return next((motor for motor in self.motors if motor.name == motor_name), None)

    def move_motor(self, motor_name, steps):
        """Move a specific motor by name."""
        motor = self.get_motor(motor_name)
        if motor:
            return motor.move(steps)
        else:
            return f"Error: Motor {motor_name} not found."

    def home_motor(self, motor_name):
        """Home a specific motor by name."""
        motor = self.get_motor(motor_name)
        if motor:
            return motor.home()
        else:
            return f"Error: Motor {motor_name} not found."

    def set_motor_home(self, motor_name):
        """Set the home position for a specific motor."""
        motor = self.get_motor(motor_name)
        if motor:
            return motor.set_home()
        else:
            return f"Error: Motor {motor_name} not found."
            
    """Manages multiple motors."""
    def __init__(self):
        self.motors = []

    def add_motor(self, name, axis, port):
        motor = Motor(name, axis, port)
        self.motors.append(motor)

    def move_multiple_motors(self, motor_steps):
        """Move multiple motors based on a dictionary of steps."""
        for motor_name, steps in motor_steps.items():
            motor = next((m for m in self.motors if m.name == motor_name), None)
            if motor:
                motor.move(steps)

class MotorControlGUI(QMainWindow):

    def __init__(self):
        super().__init__()
        self.controller = MotorController()
        self.motor_positions = []  # Custom positions for motors on the graph
        self.initUI()

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_motor_positions)
        self.update_timer.start(100)  # Update every 100ms


    def initUI(self):
        self.setWindowTitle("Motor Control GUI")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        main_layout = QVBoxLayout()
        

        # Motor Control Area
        self.motor_control_layout = QGridLayout()
        self.motor_checkboxes = []
        self.motor_inputs = []
        self.update_motor_controls()
        main_layout.addLayout(self.motor_control_layout)

        # Graph
        self.graph = PlotWidget()
        self.graph.setLabel('left', 'Position')
        self.graph.setLabel('bottom', 'Motor')
        self.graph.setYRange(0, 20)
        self.graph.setXRange(0, 10)  # Default initial range
        self.graph.setMouseEnabled(x=False, y=False)
        main_layout.addWidget(self.graph)

        # Buttons for operations
        button_layout = QHBoxLayout()
        move_button = QPushButton("Move Selected Motors")
        move_button.clicked.connect(self.move_selected_motors)
        button_layout.addWidget(move_button)

        home_button = QPushButton("Set Selected Motors Home")
        home_button.clicked.connect(self.home_selected_motors)
        button_layout.addWidget(home_button)

        main_layout.addLayout(button_layout)

        # Option to manually set motor positions
        position_layout = QHBoxLayout()
        self.custom_position_input = QLineEdit()
        self.custom_position_input.setPlaceholderText("Enter positions (comma-separated)")
        position_button = QPushButton("Set Motor Positions")
        position_button.clicked.connect(self.set_motor_positions)
        position_layout.addWidget(self.custom_position_input)
        position_layout.addWidget(position_button)
        main_layout.addLayout(position_layout)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def update_motor_controls(self):
        """Update the motor controls UI."""
        for i in reversed(range(self.motor_control_layout.count())):
            self.motor_control_layout.itemAt(i).widget().setParent(None)

        self.motor_checkboxes = []
        self.motor_inputs = []

        for i, motor in enumerate(self.controller.motors):
            checkbox = QCheckBox(motor.name)
            self.motor_checkboxes.append(checkbox)
            self.motor_control_layout.addWidget(checkbox, i, 0)

            input_box = QLineEdit()
            input_box.setPlaceholderText("Move steps")
            self.motor_inputs.append(input_box)
            self.motor_control_layout.addWidget(input_box, i, 1)

    def add_motor(self, name, axis, port):
        """Add a motor manually."""
        self.controller.add_motor(name, axis, port)
        self.update_motor_controls()

    def move_selected_motors(self):
        """Move selected motors."""
        motor_steps = {}
        for checkbox, input_box, motor in zip(self.motor_checkboxes, self.motor_inputs, self.controller.motors):
            if checkbox.isChecked():
                try:
                    steps = int(input_box.text())
                    motor_steps[motor.name] = steps
                except ValueError:
                    pass  # Ignore invalid inputs

        self.controller.move_multiple_motors(motor_steps)
        self.update_graph()

    def home_selected_motors(self):
        """Set selected motors to home position."""
        for checkbox, motor in zip(self.motor_checkboxes, self.controller.motors):
            if checkbox.isChecked():
                motor.set_home()
        self.update_graph()

    def set_motor_positions(self):
        """Manually set motor positions."""
        try:
            positions = list(map(int, self.custom_position_input.text().split(",")))
            if len(positions) != len(self.controller.motors):
                QMessageBox.warning(self, "Error", "Number of positions does not match number of motors.")
                return

            for motor, pos in zip(self.controller.motors, positions):
                motor.current_position = pos
                motor.target_position = pos
                motor.save_position()

            self.update_graph()
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid positions format. Please use integers separated by commas.")

    def update_motor_positions(self):
        """Update all motor positions."""
        for motor in self.controller.motors:
            motor.update_position()

        self.update_graph()

    def update_graph(self):
         """Update the graph to show motor positions."""
         positions = [motor.current_position for motor in self.controller.motors]
         self.graph.clear()  # Clear the previous plot
         self.graph.plot(range(len(self.controller.motors)), positions, pen="g", name="Motor Positions", symbol='o')

         x_axis = self.graph.getAxis('bottom')
         x_axis.setTicks([[(i, motor.name) for i, motor in enumerate(self.controller.motors)]])



# Main Function
if __name__ == "__main__":

    motors_config= []

    for motor in self.controller:
            motors_config.append({
                "name": motor.name,
                "axis": motor.axis,
                "port": motor.port
            })

    controller = MotorController(motors)

    app = QApplication(sys.argv)
    gui = MotorControlGUI()

    gui.show()
    sys.exit(app.exec_())
