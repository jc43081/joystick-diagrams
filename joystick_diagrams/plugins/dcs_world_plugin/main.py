import logging
from pathlib import Path

from dynaconf.loaders.json_loader import write

from joystick_diagrams.input.profile_collection import ProfileCollection
from joystick_diagrams.plugins.dcs_world_plugin.dcs_world import DCSWorldParser
from joystick_diagrams.plugins.plugin_interface import PluginInterface

from .config import settings

_logger = logging.getLogger("__name__")


class ParserPlugin(PluginInterface):
    def __init__(self):
        self.settings = settings
        self.settings.validators.register()
        self.path = None
        self.instance: DCSWorldParser = None

    def process(self) -> ProfileCollection:
        return self.instance.process_profiles()

    def set_path(self, path: Path) -> bool:
        try:
            self.instance = DCSWorldParser(path)

        except Exception as e:
            return False

        self.path = path
        return True

    def load_settings(self) -> None:
        pass

    @property
    def path_type(self):
        return self.FolderPath("Select your DCS World directory", "\\%%USERPROFILE%%\\Saved Games")

    @property
    def icon(self):
        return f"{Path.joinpath(Path(__file__).parent,self.settings.PLUGIN_ICON)}"


if __name__ == "__main__":
    plugin = ParserPlugin()
