"""Star Citizen XML Parser for use with Joystick Diagrams"""
import os
from pathlib import Path
from xml.dom import minidom
import functions.helper as helper
import adaptors.joystick_diagram_interface as jdi


class StarCitizen(jdi.JDinterface):
    def __init__(self, file_path):
        jdi.JDinterface.__init__(self)
        self.file_path = file_path
        self.data = self.__load_file()
        self.hat_formats = {"up": "U", "down": "D", "left": "L", "right": "R"}
        self.hat = None
        self.devices = {}
        self.button_array = {}

    def __load_file(self):
        if os.path.exists(self.file_path):
            if (os.path.splitext(self.file_path))[1] == ".xml":
                data = Path(self.file_path).read_text(encoding="utf-8")
                try:
                    self.__validate_file(data)
                except Exception:
                    raise Exception("File is not a valid Star Citizen XML")
                else:
                    return data
            else:
                raise Exception("File must be an XML file")
        else:
            raise FileNotFoundError("File not found")

    def __validate_file(self, data):
        try:
            parsed_xml = minidom.parseString(data)
        except ValueError:
            raise Exception("File is not a valid Star Citizen XML")
        else:
            if (
                (
                    len(parsed_xml.getElementsByTagName("ActionMaps")) == 1
                    and len(parsed_xml.getElementsByTagName("options")) > 0
                    and len(parsed_xml.getElementsByTagName("actionmap")) > 0
                )
            ):
                return True
            else:
                raise Exception

    def parse_map(self, bind_map):
        segments = bind_map.split("_")
        helper.log("Bind Information: {}".format(segments), "debug")
        bind_device = segments[0]
        device_object = self.get_stored_device(bind_device)
        helper.log("Device: {}".format(device_object), "debug")
        if device_object is None:
            c_map = None
            return (device_object, c_map)
        if segments[1] == "":
            c_map = None
            return (device_object, c_map)
        elif segments[1][0:6] == "button":
            button_id = segments[1][6:]
            c_map = "BUTTON_{id}".format(id=button_id)
            return (device_object, c_map)
        elif segments[1][0:3] == "hat":
            pov_id = segments[1][3:]
            pov_dir = self.convert_hat_format(segments[2])
            c_map = "POV_{id}_{dir}".format(id=pov_id, dir=pov_dir)
            return (device_object, c_map)
        elif segments[1][0] in ("x", "y", "z"):
            axis = segments[1][0]
            c_map = "AXIS_{axis}".format(axis=axis)
            return (device_object, c_map)
        elif segments[1][0:3] == "rot":
            axis = segments[1][3:]
            c_map = "AXIS_R{axis}".format(axis=axis)
            return (device_object, c_map)
        elif segments[1][0:6] == "slider":
            slider_id = segments[1][6:]
            c_map = "AXIS_SLIDER_{id}".format(id=slider_id)
            return (device_object, c_map)
        else:
            c_map = None
            return (device_object, c_map)

    def get_human_readable_name(self):
        # Future for str replacements
        pass

    def convert_hat_format(self, hat):
        helper.log("Convert Hat: {}".format(hat), "debug")
        return self.hat_formats[hat]

    def extract_device_information(self, option):
        """ Accepts parsed OPTION from Star Citizen XML"""
        name = (
            option.getAttribute("Product")[
                0 : (len(option.getAttribute("Product")) - 38)
            ]
        ).strip()
        guid = option.getAttribute("Product")[-37:-2]  # GUID Fixed
        return {"name": name, "guid": guid}

    def get_stored_device(self, device):

        if device in self.devices:
            return self.devices[device]
        else:
            return None

    def add_device(self, option):
        """ Accepts parsed OPTION from Star Citizen XML"""
        self.devices.update(
            {
                self.device_id(
                    option.getAttribute("type"), option.getAttribute("instance")
                ): self.extract_device_information(option)
            }
        )
        helper.log("Device List: {}".format(self.devices), "debug")

    def process_name(self, name):
        helper.log("Bind Name: {}".format(name), "debug")
        # Force some Labels, this ideally need to be declared elsewhere or from an external file
        customLabels = {
            "v_increase_mining_throttle" : "v_mining_power_+",
            "v_decrease_mining_throttle" : "v_mining_power_",
            "v_mining_throttle" : "v_mining_power",
            "v_dec_ping_focus_angle" : "v_ping_angle_-",
            "v_inc_ping_focus_angle": "v_ping_angle_+", 
            "v_weapon_launch_missile" : "v_launch_missile",
            "v_weapon_countermeasure_decoy_launch_panic" : "v_weapon_countermeasure_decoy_launch_x5",
            "v_scanning_trigger_scan" : "v_scan",
            "v_toggle_qdrive_engagement" : "v_toggle_engage_quantum",
            "v_attack1_group1" : "v_fire_1",
            "v_attack1_group2" : "v_fire_2",
            "v_target_lock_selected" : "v_target_lock",
            "v_weapon_cycle_missile_back" : "v_cycle_missile_-",
            "v_weapon_cycle_missile_fwd" : "v_cycle_missile_+",
            "v_target_cycle_friendly_back" : "v_cycle_friendly_-",
            "v_target_cycle_friendly_fwd" : "v_cycle_friendly_+",
            "v_target_cycle_friendly_reset" : "v_reset_friendly",
            "v_target_cycle_hostile_back" : "v_cycle_hostile_-",
            "v_target_cycle_hostile_fwd" : "v_cycle_hostile_+",
            "v_target_cycle_hostile_reset" : "v_reset_hostile",
            "v_shield_raise_level_left" : "v_left_shield_+",
            "v_shield_raise_level_right" : "v_right_shield_+",
            "v_shield_raise_level_forward" : "v_forward_shield_+",
            "v_shield_raise_level_back" : "v_back_shield_+",
        }
        replacedWords = {
            "_ifcs" : "",
            "_toggle" : "",
            "_use_consumable" : "_use_",
            "_weapon_countermeasure" : "",
            "_scanning_trigger_scan" : "_scan",
            "_qdrive" : "_quantum",
            "_attack": "_fire",
            "_weapon" : "",
        }
        # Set Custom Labels
        if name in customLabels:
            name = customLabels.get(name)
        # Replace Partial String
        for key in replacedWords:
            if key in name:
                name = name.replace(key, replacedWords.get(key))
        # Split the String to Array
        name = name.split("_")
        if len(name) == 1:
            return name[0].capitalize()
        else:
            return (" ".join(name[1:])).capitalize()

    def build_button_map(self, device, button, name):
        if device in self.button_array:
            self.button_array[device].update({button: name})
        else:
            self.button_array.update({device: {button: name}})

    def device_id(self, device_type, instance):
        if device_type == "keyboard":
            device_code = "kb"
        elif device_type == "joystick":
            device_code = "js"
        else:
            device_code = "mo"  ## Catch all for now
        return "{type}{instance}".format(type=device_code, instance=instance)

    def parse(self):
        parse = minidom.parseString(self.data)
        joysticks = parse.getElementsByTagName("options")
        for j in joysticks:
            self.add_device(j)
        actions = parse.getElementsByTagName("actionmap")

        for i in actions:
            helper.log(
                "Bind Category: {}".format(self.process_name(i.getAttribute("name"))),
                "debug",
            )
            actionsMapBypass = {
                "Fire 1",
                "Fire 2"
            }
            single_actions = i.getElementsByTagName("action")
            for action in single_actions:
                name = self.process_name(action.getAttribute("name"))
                binds = action.getElementsByTagName("rebind")
                helper.log("Binds in group: {}".format(binds), "debug")
                for bind in binds:
                    bind = bind.getAttribute("input")
                    button = self.parse_map(bind)
                    helper.log("Parsed Control: {}".format(button), "debug")
                    if button and button[1] is not None:
                        helper.log("Valid button, adding to map", "debug")
                        # Check if the Device exist is already Mapped
                        if (button[0]["name"] in self.button_array):
                            # Check if the Button is already Mapped for this Device
                            if (button[1] not in self.button_array[button[0]["name"]]):
                                # Add Mapping
                                self.build_button_map(button[0]["name"], button[1], name)
                            else :
                                # Check if the current Binding bypass existing one
                                if (name in actionsMapBypass) :
                                    self.build_button_map(button[0]["name"], button[1], name)
                        else:
                            # Add Mapping
                            self.build_button_map(button[0]["name"], button[1], name)
                        helper.log("Button Map is now: {}".format(self.button_array))
                    else:
                        helper.log("Button not valid, skipping", "debug")

        for item in self.button_array:
            self.update_joystick_dictionary(
                item, "Default", False, self.button_array[item]
            )

        return self.joystick_dictionary
