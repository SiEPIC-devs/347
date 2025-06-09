from remi.gui import *
from myguilab import *
from remi import start, App
import os


class devices(App):
    def __init__(self, *args, **kwargs):
        self.timestamp = -1
        if "editing_mode" not in kwargs:
            super(devices, self).__init__(*args, **{"static_file_path": {"my_res": "./res/"}})

    def idle(self):
        self.terminal.terminal_refresh()

    def main(self):
        return devices.construct_ui(self)

    @staticmethod
    def construct_ui(self):
        devices_container = StyledContainer(container=None, variable_name="devices_container", left=0, top=0)

        # Devices List
        coordinate_container = StyledContainer(container=devices_container, variable_name="coordinate_container",
                                               left=10, top=10, height=320, width=625, overflow=True, border=True)
        headers = ["Device ID", "Test", "Mode", "Wvl", "Type", "Comment", "GDS x", "GDS y"]
        widths = [120, 40, 50, 50, 60, 100, 50, 50]
        StyledTable(container=coordinate_container, variable_name="device_table",
                    left=0, top=0, height=30, table_width=625, headers=headers, widths=widths, row=14)
        for row_index in range(1, 13):
            table = devices_container.children["coordinate_container"].children["device_table"]
            row = list(table.children.values())[row_index]
            cell0 = list(row.children.values())[0]
            cell1 = list(row.children.values())[1]
            cell2 = list(row.children.values())[2]
            cell3 = list(row.children.values())[3]
            cell4 = list(row.children.values())[4]
            cell5 = list(row.children.values())[5]
            cell6 = list(row.children.values())[6]
            cell7 = list(row.children.values())[7]
            cell1.style["text-align"] = "center"
            device_id = StyledLabel(container=None, text=f"Device_{row_index}", variable_name=f"Device_{row_index}", left=0, top=0,
                                    width=100, height=100, font_size=100, color="#222", align="right", position="inherit", percent=True, flex=True, justify_content="left")
            test = StyledCheckBox(container=None, variable_name=f"test_{row_index}", left=0, top=0,
                                  width=10, height=10, position="inherit")
            mode = StyledLabel(container=None, text="TE", variable_name=f"mode_{row_index}", left=0, top=0,
                               width=100, height=100, font_size=100, color="#222", align="right", position="inherit", percent=True, flex=True)
            wvl = StyledLabel(container=None, text="1550", variable_name=f"wvl_{row_index}", left=0, top=0,
                              width=100, height=100, font_size=100, color="#222", align="right", position="inherit", percent=True, flex=True)
            type = StyledLabel(container=None, text="device", variable_name=f"type_{row_index}", left=0, top=0,
                               width=100, height=100, font_size=100, color="#222", align="right", position="inherit", percent=True, flex=True)
            comment = StyledLabel(container=None, text="", variable_name=f"comment_{row_index}", left=0, top=0,
                                  width=100, height=100, font_size=100, color="#222", align="right", position="inherit", percent=True, flex=True)
            gds_x = StyledLabel(container=None, text="0", variable_name=f"gds_x_{row_index}", left=0, top=0,
                                width=100, height=100, font_size=100, color="#222", align="right", position="inherit",
                                percent=True, flex=True)
            gds_y = StyledLabel(container=None, text="0", variable_name=f"gds_y_{row_index}", left=0, top=0,
                                width=100, height=100, font_size=100, color="#222", align="right", position="inherit",
                                percent=True, flex=True)
            cell0.append(device_id)
            cell1.append(test)
            cell2.append(mode)
            cell3.append(wvl)
            cell4.append(type)
            cell5.append(comment)
            cell6.append(gds_x)
            cell7.append(gds_y)

        # Selection
        selection_container = StyledContainer(container=devices_container, variable_name="selection_container",
                                              left=10, top=350, height=130, width=625, border=True)
        StyledLabel(container=selection_container, text="Device Selection Control",
                    variable_name=f"device_selection_control", left=15, top=-12, width=185, height=20,
                    font_size=120, color="#222", align="center", position="absolute", flex=True, on_line=True)
        StyledTextInput(container=selection_container, variable_name="selection_id", left=20, top=70,
                        width=110, height=25, position="absolute")
        StyledDropDown(container=selection_container, text=["TE", "TM"], variable_name="selection_mode",
                       left=160, top=70, width=60, height=25)
        StyledDropDown(container=selection_container, text=["1550", "1310"], variable_name="selection_wvl",
                       left=230, top=70, width=90, height=25)
        StyledDropDown(container=selection_container, text=["Any", "Devicec"], variable_name="selection_type",
                       left=330, top=70, width=90, height=25)
        StyledButton(container=selection_container, text="Reset Filter", variable_name="reset_filter",
                     left=435, top=70, width=80, height=25, normal_color="#007BFF", press_color="#0056B3")
        StyledButton(container=selection_container, text="Clear All", variable_name="clear_all",
                     left=525, top=70, width=80, height=25, normal_color="#007BFF", press_color="#0056B3")
        StyledButton(container=selection_container, text="Select All", variable_name="select_all",
                     left=525, top=35, width=80, height=25, normal_color="#007BFF", press_color="#0056B3")
        StyledLabel(container=selection_container, text="Device ID Contains", variable_name="device_id_contains",
                    left=22, top=45, width=150, height=25, font_size=100, color="#222", align="left", position="absolute")
        StyledLabel(container=selection_container, text="Mode", variable_name="mode",
                    left=162, top=45, width=100, height=25, font_size=100, color="#222", align="left", position="absolute")
        StyledLabel(container=selection_container, text="Wavelength", variable_name="wavelength",
                    left=232, top=45, width=100, height=25, font_size=100, color="#222", align="left", position="absolute")
        StyledLabel(container=selection_container, text="Type", variable_name="type",
                    left=332, top=45, width=100, height=25, font_size=100, color="#222", align="left", position="absolute")


        # Terminal
        terminal_container = StyledContainer(container=devices_container, variable_name="terminal_container",
                                             left=0, top=500, height=150, width=650, bg_color=True)
        self.terminal = Terminal(container=terminal_container, variable_name="terminal_text",
                                 left=10, top=15, width=610, height=100)

        self.devices_container = devices_container
        return devices_container


if __name__ == "__main__":
    configuration = {
        "config_project_name": "devices",
        "config_address": "0.0.0.0",
        "config_port": 9003,
        "config_multiple_instance": False,
        "config_enable_file_cache": False,
        "config_start_browser": False,
        "config_resourcepath": "./res/"
    }
    start(devices,
          address=configuration["config_address"],
          port=configuration["config_port"],
          multiple_instance=configuration["config_multiple_instance"],
          enable_file_cache=configuration["config_enable_file_cache"],
          start_browser=configuration["config_start_browser"])
