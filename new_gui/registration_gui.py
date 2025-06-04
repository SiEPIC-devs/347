from remi.gui import *
from remi import start, App
import os
from myguilab import (StyledContainer, StyledButton, StyledLabel, StyledDropDown,
                      Terminal, StyledFileUploader, StyledTable, StyledCheckBox)

class registration(App):
    def __init__(self, *args, **kwargs):
        self.timestamp = -1
        if "editing_mode" not in kwargs:
            super(registration, self).__init__(*args, **{"static_file_path": {"my_res": "./res/"}})

    def idle(self):
        self.terminal.terminal_refresh()

    def main(self):
        return registration.construct_ui(self)

    @staticmethod
    def construct_ui(self):
        registration_container = StyledContainer(container=None, variable_name="registration_container", left=0, top=0)

        # File
        file_container  = StyledContainer(container=registration_container, variable_name="file_container",
                                          left=10, top=10, height=45, width=625, border=True)
        StyledFileUploader(container=file_container, variable_name="uploader",
                           left=10, top=10, width=220, height=30)
        StyledLabel(container=file_container, text="Stage:", variable_name="label_stage",
                    left=130, top=15, width=150, height=20, font_size=100, color='#444', align='right')
        StyledDropDown(container=file_container, text=["Fiber Stage", "Chip Stage"], variable_name="choose_stage",
                       left=290, top=10, width=220, height=30)
        StyledButton(container=file_container, text="Setting", variable_name="setting",
                     left=515, top=10, normal_color='#007BFF', press_color='#0056B3')

        # Coordinate
        coordinate_container = StyledContainer(container=registration_container, variable_name="coordinate_container",
                                               left=10, top=70, height=185, width=625, border=True)
        StyledButton(container=coordinate_container, text="Reset", variable_name="reset",
                     left=10, top=10, normal_color='#007BFF', press_color='#0056B3')

        headers = ['Device ID', 'GDS x', 'GDS y', 'Stage x', 'Stage y', 'Set']
        widths = [150, 80, 80, 80, 80, 40]
        StyledTable(container=coordinate_container, variable_name="device_table",
                    left=0, top=50, height=30, table_width=625, headers=headers, widths=widths, row=4)

        # Terminal
        terminal_container = StyledContainer(container=registration_container, variable_name="terminal_container",
                                             left=0, top=500, height=150, width=650, bg_color=True)
        self.terminal = Terminal(container=terminal_container, variable_name="terminal_text",
                                 left=10, top=15, width=610, height=100)

        self.registration_container = registration_container


        for row_index in range(1, 4):
            table = self.registration_container.children["coordinate_container"].children["device_table"]
            row = list(table.children.values())[row_index]
            cell0 = list(row.children.values())[0]
            cell1 = list(row.children.values())[1]
            cell2 = list(row.children.values())[2]
            cell3 = list(row.children.values())[3]
            cell4 = list(row.children.values())[4]
            cell5 = list(row.children.values())[5]
            cell5.style["text-align"] = "center"
            device_id = StyledDropDown(container=None, text=["FarmMiddl_1", "FarmMiddl_2", "FarmMiddl_3"],
                                       variable_name=f"device_id_{row_index}",
                                       bg_color="#ffffff" if row_index % 2 != 0 else "#f6f7f9",
                                       border="0px", border_radius="0px",
                                       left=0, top=0, width=100, height=100, position="inherit", percent=True)
            gds_x = StyledLabel(container=None, text="0", variable_name=f"gds_x_{row_index}", left=0, top=0,
                                width=100, height=100, font_size=100, color="#222", align="right", position="inherit", percent=True, flex=True)
            gds_y = StyledLabel(container=None, text="0", variable_name=f"gds_y_{row_index}", left=0, top=0,
                                width=100, height=100, font_size=100, color="#222", align="right", position="inherit", percent=True, flex=True)
            stage_x = StyledLabel(container=None, text="0", variable_name=f"stage_x_{row_index}", left=0, top=0,
                                  width=100, height=100, font_size=100, color="#222", align="right", position="inherit", percent=True, flex=True)
            stage_y = StyledLabel(container=None, text="0", variable_name=f"stage_y_{row_index}", left=0, top=0,
                                  width=100, height=100, font_size=100, color="#222", align="right", position="inherit", percent=True, flex=True)
            checkbox = StyledCheckBox(container=None, variable_name=f"checkbox_{row_index}", left=0, top=0,
                                      width=10, height=10, position="inherit")
            cell0.append(device_id)
            cell1.append(gds_x)
            cell2.append(gds_y)
            cell3.append(stage_x)
            cell4.append(stage_y)
            cell5.append(checkbox)

        return registration_container


if __name__ == "__main__":
    configuration = {
        'config_project_name': 'registration',
        'config_address': '0.0.0.0',
        'config_port': 9002,
        'config_multiple_instance': False,
        'config_enable_file_cache': False,
        'config_start_browser': True,
        'config_resourcepath': '"./res/"'
    }
    start(registration,
          address=configuration['config_address'],
          port=configuration['config_port'],
          multiple_instance=configuration['config_multiple_instance'],
          enable_file_cache=configuration['config_enable_file_cache'],
          start_browser=configuration['config_start_browser'])
