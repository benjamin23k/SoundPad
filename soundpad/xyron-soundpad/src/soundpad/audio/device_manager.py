from PySide6.QtWidgets import QComboBox
from PySide6.QtCore import QTimer

from soundpad.audio.device_manager import DeviceManager


class AudioSettings:

    def __init__(self, input_combo, output_combo):

        self.input_combo = input_combo
        self.output_combo = output_combo

        self.refresh_devices()

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_devices)
        self.timer.start(3000)

    def refresh_devices(self):

        inputs = DeviceManager.get_input_devices()
        outputs = DeviceManager.get_output_devices()

        self.update_combo(
            self.input_combo,
            inputs
        )

        self.update_combo(
            self.output_combo,
            outputs
        )

    def update_combo(self, combo, devices):

        previous = combo.currentData()

        combo.blockSignals(True)
        combo.clear()

        for device in devices:

            label = (
                f'{device["name"]} '
                f'({device["hostapi"]})'
            )

            combo.addItem(
                label,
                device["index"]
            )

            if previous is not None:

                position = combo.findData(previous)

                if position >= 0:
                    combo.setCurrentIndex(position)

                    combo.blockSignals(False)