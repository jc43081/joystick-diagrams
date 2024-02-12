import logging
import os
from dataclasses import dataclass
from pathlib import Path

import qtawesome as qta  # type: ignore
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QFileDialog, QMainWindow

from joystick_diagrams.app_state import AppState
from joystick_diagrams.db.db_device_management import (
    add_update_device_template_path,
    get_device_templates,
)
from joystick_diagrams.export import export
from joystick_diagrams.ui.device_setup import DeviceSetup
from joystick_diagrams.ui.qt_designer import export_ui
from joystick_diagrams.utils import install_root

_logger = logging.getLogger(__name__)


@dataclass
class DeviceTemplate:
    guid: str
    path: Path | None


class ExportPage(
    QMainWindow, export_ui.Ui_Form
):  # Refactor pylint: disable=too-many-instance-attributes
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.appState = AppState()
        self.ExportButton.clicked.connect(self.run_exporter)

        # self.tableWidget.itemClicked.connect(self.device_template_item_clicked)
        self.pushButton.clicked.connect(self.select_template)
        self.pushButton.setIconSize(QSize(32, 32))
        self.pushButton.setIcon(
            qta.icon(
                "fa5s.file-code",
                color="white",
            )
        )
        self.pushButton.setText("Setup template")
        self.pushButton.setProperty("class", "success")

        # UI Setup

        self.device_widget = DeviceSetup()
        self.device_widget.device_item_selected.connect(self.change_template_button)
        self.horizontalLayout.addWidget(self.device_widget)

    def change_template_button(self, data):
        print(data)

    def select_template(self):
        _file = QFileDialog.getOpenFileName(
            self,
            caption="Select an SVG file to use as a template",
            filter=("SVG Files (*.svg)"),
            dir=os.path.join(install_root(), "templates"),
        )
        if _file[0]:
            file_path = Path(_file[0])
            self.set_template_for_device(file_path)

    def set_template_for_device(self, template_path: Path):
        selected_table_rows = self.device_widget.treeWidget.currentItem()

        # Selection Mode is single so force select first
        if not selected_table_rows:
            return  # Add handling here...

        # Not a root object, child was selected
        if selected_table_rows.parent() is not None:
            return

        row_guid_data = selected_table_rows.data(0, Qt.ItemDataRole.UserRole)

        # Save the device information
        _save = add_update_device_template_path(row_guid_data, template_path.__str__())

        if _save:
            self.device_widget.devices_updated.emit()

    def run_exporter(self):
        # Check what is selected / Child / Parent
        items_to_export = self.device_widget.treeWidget.currentItem()

        item_data = items_to_export.data(0, Qt.ItemDataRole.UserRole)

        export(item_data)


def get_unique_devices() -> list[DeviceTemplate]:
    "Gets the unique device list from stored device configurations and new device configurations"

    # Get stored devices
    stored_devices = get_device_template_configurations()

    # Get the devices active from profiles
    active_profile_devices = get_devices_from_profiles()

    # Remove items from new profiles where intersect with stored
    active_profile_devices.difference_update({x[0] for x in stored_devices})

    # Create wrapper objects
    stored_objs = [DeviceTemplate(x[0], x[1]) for x in stored_devices]
    new_objs = [DeviceTemplate(x, None) for x in active_profile_devices]

    return stored_objs + new_objs


def get_device_template_configurations() -> list:
    "Gets the stored device template configurations from datastore"

    return get_device_templates()


def get_devices_from_profiles():
    "Retreives a unique set of devices from all processed profiles"

    all_profiles = AppState().get_processed_profiles().values()

    merge_set = set()
    for profile in all_profiles:
        merge_set.update(profile.get_all_device_guids())

    return merge_set


if __name__ == "__main__":
    pass