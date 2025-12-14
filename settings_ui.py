"""Serial UI module.

Regroup all required classes to manage the Serial Connection UI
and the link with the communication module.

Module : serial_ui
Authors : yannick
"""
from concurrent.futures import process
import PyQt6.QtGui
import PyQt6.QtSerialPort
import PyQt6.QtCore
import PyQt6.QtWidgets
import base_ui
import main
import helper


class Settings(base_ui.WidgetUI, base_ui.CommunicationHandler):
    """This classe is the main Serial Chooser manager.

    *) Display the UI
    *) Manage the user interraction : connect/disconnect
    *) Manage the serial port status
    """

    OFFICIAL_VID_PID = [(0x1209, 0xFFB0)]  # Highlighted in serial selector

    def __init__(self,  main, serialport : PyQt6.QtSerialPort.QSerialPort):
        """Initialize the manager with the QSerialPort for serial commmunication and the mainUi."""
        base_ui.WidgetUI.__init__(self, main, "settings_serial.ui")
        base_ui.CommunicationHandler.__init__(self)

        self.main = main
        self.main_id = None

        # prefer the serial port managed by the shared comms object if present
        self._serial = self.comms.serial

        self.pushButton_send.clicked.connect(self.send_line)
        self.lineEdit_cmd.returnPressed.connect(self.send_line)
        self.pushButton_mainclasschange.clicked.connect(self.main_btn)
        
        # Update UI according to current connection state
        self.update_connected()

    def showEvent(self, event): # pylint: disable=unused-argument, invalid-name
        """On show event, init the param.

        Connect the communication module with the history widget to load the board response.
        """
        self.get_raw_reply().connect(self.serial_log)

    # Tab is hidden
    def hideEvent(self, event): # pylint: disable=unused-argument, invalid-name
        """On hide event, disconnect the event.

        Disconnect the communication module with the history widget
        to stop to log the board response.
        """
        try:
            self.get_raw_reply().disconnect(self.serial_log)
        except TypeError:
            pass

    def serial_log(self, txt):
        """Add a new text in the history widget."""
        if isinstance(txt, list):
            txt = "\n".join(txt)
        else:
            txt = str(txt)
        self.serialLogBox.append(txt)

    def send_line(self):
        """Read the command input text, display it in history widget and send it to the board."""
        cmd = self.lineEdit_cmd.text() + "\n"
        self.serial_log(">" + cmd)
        self.serial_write_raw(cmd)

    def write(self, data):
        """Write data to the serial port."""
        self._serial.write(data)

    def update_connected(self, state=None):
        """Update the UI when a connection is successfull.

        Disable connection button, dropbox, etc.
        Emit for all the UI the [connected] event.
        """
        if state:
            
            self.label.setEnabled(True)
            self.comboBox_main.setEnabled(True)
            self.pushButton_mainclasschange.setEnabled(True)
                                          
            self.pushButton_send.setEnabled(True)
            self.lineEdit_cmd.setEnabled(True)
            self.groupBox_system.setEnabled(True)

            self.get_main_classes()
        else:
            
            self.label.setEnabled(False)
            self.comboBox_main.setEnabled(False)
            self.pushButton_mainclasschange.setEnabled(False)
            
            self.pushButton_send.setEnabled(False)
            self.lineEdit_cmd.setEnabled(False)
            self.groupBox_system.setEnabled(False)

    def update_mains(self, dat):
        """Parse the list of main classes received from board, and update the combobox."""
        self.comboBox_main.clear()
        self._class_ids, self._classes = helper.classlistToIds(dat)

        if self.main_id is None:
            # TODO VMA self.main.resetPort()
            self.groupBox_system.setEnabled(False)
            return
        #self.groupBox_system.setEnabled(True)

        helper.updateClassComboBox(
            self.comboBox_main, self._class_ids, self._classes, self.main_id
        )

        self.main.log("Detected mode: " + self.comboBox_main.currentText())
        self.main.update_tabs()

    def get_main_classes(self):
        """Get the main classes available from the board in Async."""

        def fct(i):
            """Store the main currently selected to refresh the UI."""
            self.main_id = i

        self.get_value_async("main", "id", fct, conversion=int, delete=True)
        self.get_value_async("sys", "lsmain", self.update_mains, delete=True)

    def main_btn(self):
        """Read the select main class in the combobox.

        Push it to the board and display the reload warning.
        """
        index = self._classes[self.comboBox_main.currentIndex()][0]
        self.send_value("sys", "main", index)
        self.main.reconnect()
        msg = PyQt6.QtWidgets.QMessageBox(
            PyQt6.QtWidgets.QMessageBox.Icon.Information,
            "Main class changed",
            "Chip is rebooting. Please reconnect.",
        )
        msg.exec()
