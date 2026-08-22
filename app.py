import os
import subprocess
import sys

from PyQt6.QtGui import (
    QIntValidator,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt Sim-Runner")
        self.setFixedSize(900,600)
        self.process=SimulationRunner()

        # Main Container
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Form Section
        form_layout = QFormLayout()

        # File Selection Section
        file_layout = QHBoxLayout()
        
        layout.addLayout(file_layout) 
        layout.addLayout(form_layout)

        self.file_path_display = QLineEdit()
        self.file_path_display.setReadOnly(True)
        self.file_path_display.setPlaceholderText("No file selected...")

        self.browsebutton = QPushButton("Select File")
        self.browsebutton.setToolTip("Select the OpenModelica Executable:")
        self.browsebutton.clicked.connect(self.open_file_dialog)
        file_layout.addWidget(self.file_path_display)
        file_layout.addWidget(self.browsebutton)

        # Start Time Row
        self.inputstart = QLineEdit(self)
        self.inputstart.setValidator(QIntValidator(0,4,self))
        self.inputstart.setToolTip("Enter an integer between 0 and 3(Must be < StopTime)")
        form_layout.addRow("Start Time:", self.inputstart,)

        # Stop Time Row
        self.inputstop = QLineEdit(self)
        self.inputstop.setValidator(QIntValidator(0,4,self))
        self.inputstop.setToolTip("Enter an integer between 0 and 4(must be > than StartTime)")
        form_layout.addRow("Stop Time:", self.inputstop)



        self.buttsubmit = QPushButton("Run Simulation")
        self.buttsubmit.setToolTip("Click to run the simulation with the selected file and specified start/stop times.")
        layout.addWidget(self.buttsubmit)
        self.buttsubmit.clicked.connect(self.SubmitButton)


        self.tershowbutton = QPushButton("Hide Terminal Log")
        self.tershowbutton.setToolTip("Use this to hide the Terminal")
        self.tershowbutton.clicked.connect(self.toggle_terminal)
        layout.addWidget(self.tershowbutton)

        self.Terminal = QTextEdit(self)
        self.Terminal.setReadOnly(True)
        self.Terminal.setPlaceholderText("Simulation terminal logs will appear here:")
        layout.addWidget(self.Terminal)
        
    def open_file_dialog(self):
        self.file_path, self.file_extension = QFileDialog.getOpenFileName(
            self,                     
            "Select a Document",      
            "",                       
            "Executible (*.exe);:All Files (*)"
        )
        if self.file_path:
            print(f"Selected file path: {self.file_path}")
            print(f"Selected filter: {self.file_extension}")
            self.file_path_display.setText(self.file_path)
        else:
            print("File selection canceled.")
            QMessageBox.warning(self,"Warning","File selection canceled")

    def toggle_terminal(self):
        is_visible = self.Terminal.isVisible()
        self.Terminal.setVisible(not is_visible)
        self.tershowbutton.setText("Show Terminal Log" if is_visible else "Hide Terminal Log")

    def SubmitButton(self):
        startT = self.inputstart.text()
        stopT = self.inputstop.text()
        try:
            if startT:
                startT = int(startT)
            else:
                QMessageBox.warning(self,"Warning","Please enter Value in the StartTime.")
                return

            if stopT:
                stopT = int(stopT)
            else:
                QMessageBox.warning(self,"Warning", "Please enter Value in the StopTime.")
                return
        except ValueError:
            print("Invalid input. Please enter valid integers for start and stop times.")
            QMessageBox.critical(self,"Error","Please enter Value in the StartTime and StopTime.")
            return      
        
        if startT >= stopT:
            print("wrong Input")
            QMessageBox.warning(self,"Warning","Start time must be less than stop time.")
            return
        else:
            pass

        if hasattr(self, 'file_path'):
            self.success, self.console_output = self.process.run(self.file_path,startT,stopT)
            if self.success:
                QMessageBox.information(self, "Success", "Simulation finished successfully!")
            else:
                QMessageBox.critical(self, "Simulation Failed", "Check the terminal logs for details.")

            self.Terminal.append(self.console_output) 

        else:
            print("No file selected. Please select a file before submitting.")
            QMessageBox.warning(self,"Warning","No file selected. Please select a file before submiting.")



class SimulationRunner:
    def run(self,exe_path,startT,stopT):
        try:
            output_dir = "./output"
            os.makedirs(output_dir, exist_ok=True)
            self.sim_result = subprocess.run([exe_path, f"-startTime={startT}", f"-stopTime={stopT}",f"-outputPath=.{output_dir}"],cwd="./model",capture_output=True, check=False,text=True)
            # the ".{}" in the subproces was added as cwd is set to ./model and if we add the "".." in the output_dir the os.makedirs creates the output folder outside our Sim_Runner because to "../"
            print(f"Simulation completed with return code: {self.sim_result.returncode}")

            with open(os.path.join("./output", "simulation_log.txt"), "w") as log_file:
                log_file.write(self.sim_result.stdout)
                log_file.write("\n")
                log_file.write(self.sim_result.stderr)
            # Note: The TwoConnectedTanks executable returns 255 on successful 
            # completion with warnings (verified via $? and .mat file generation).
            if self.sim_result.returncode == 0:
                return True, self.sim_result.stdout
            elif self.sim_result.returncode == 255:
                return True, f"Completed with warnings (exit code 255):\n{self.sim_result.stdout}"
            else:
                return False, f"STDOUT:\n{self.sim_result.stdout}\nSTDERR:\n{self.sim_result.stderr}"



        except (FileNotFoundError, PermissionError, OSError) as e:
            print(f"Error running simulation: {e}")
            return False , str(e)
     

def main():
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()