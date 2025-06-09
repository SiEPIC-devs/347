from myguilab import *
from remi.gui import *
from remi import start, App
import os


class testing(App):
    def __init__(self, *args, **kwargs):
        self.timestamp = -1
        if "editing_mode" not in kwargs:
            super(testing, self).__init__(*args, **{"static_file_path": {"my_res": "./res/"}})

    def idle(self):
        self.terminal.terminal_refresh()

    def main(self):
        return testing.construct_ui(self)

    @staticmethod
    def construct_ui(self):
        testing_container = StyledContainer(container=None, variable_name="testing_container", left=0, top=0)

        # Image
        image_container = StyledContainer(container=testing_container, variable_name="image_container",
                                          left=10, top=10, height=335, width=370, border=True)
        path_container = StyledContainer(container=testing_container, variable_name="path_container",
                                         left=10, top=370, height=110, width=370)
        StyledLabel(container=path_container, text="Save path", variable_name="save_path", left=5, top=20,
                    width=80, height=50, font_size=100, color="#222", align="left")
        StyledLabel(container=path_container, text="Save format", variable_name="save_format", left=5, top=60,
                    width=80, height=50, font_size=100, color="#222", align="left")
        StyledTextInput(container=path_container, variable_name="save_path_input", left=90, top=15,
                        width=162, height=28, position="absolute", text="")
        StyledDropDown(container=path_container, text=["Comma seperated (.csv)", "Other"], variable_name="save_format_dd",
                       left=90, top=55, width=180, height=30)
        StyledButton(container=path_container, text="Set Path", variable_name="set_path",
                     left=275, top=15, width=90, height=30, normal_color="#007BFF", press_color="#0056B3")
        StyledButton(container=path_container, text="Open Path", variable_name="open_path",
                     left=275, top=55, width=90, height=30, normal_color="#007BFF", press_color="#0056B3")
        StyledImageBox(
            container=image_container,
            variable_name="display_plot",
            left=0, top=0,
            width=100, height=100,
            image_path="my_res:plot.png",
            percent=True
        )

        separator = Container()
        separator.css_position = "absolute"
        separator.css_left = "390px"
        separator.css_top = "10px"
        separator.css_width = "1px"
        separator.css_height = "470px"
        separator.style.update({
            "background-color": "#bbb",
        })
        testing_container.append(separator, "image_setting_separator")

        # Setting
        setting_container = StyledContainer(container=testing_container, variable_name="setting_container",
                                            left=400, top=10, height=475, width=240)
        StyledDropDown(container=setting_container, text=["Laser Sweep", "...."],
                       variable_name="laser_sweep", left=10, top=0, width=120, height=30)
        StyledButton(container=setting_container, text="Setting", variable_name="setting",
                     left=145, top=0, width=90, height=30, normal_color="#007BFF", press_color="#0056B3")
        headers = ["Device", "Status"]
        widths = [60, 40]
        table_container = StyledContainer(container=setting_container, variable_name="setting_container",
                                          left=0, top=40, height=295, width=240, border=True, overflow=True)
        StyledTable(container=table_container, variable_name="device_status",
                    left=0, top=0, height=25, table_width=240, headers=headers, widths=widths, row=14)
        StyledButton(container=setting_container, text="Start", variable_name="start",
                     left=0, top=375, width=70, height=30, normal_color="#007BFF", press_color="#0056B3")
        StyledButton(container=setting_container, text="Stop", variable_name="stop",
                     left=0, top=415, width=70, height=30, normal_color="#007BFF", press_color="#0056B3")
        StyledLabel(container=setting_container, text="Elapsed", variable_name="elapsed", left=80, top=382,
                    width=65, height=30, font_size=100, color="#222", align="right")
        StyledLabel(container=setting_container, text="Remaining", variable_name="remaining", left=80, top=422,
                    width=65, height=30, font_size=100, color="#222", align="right")
        StyledLabel(container=setting_container, text="00:00:00", variable_name="elapsed_time", left=165, top=375,
                    width=75, height=25, font_size=100, color="#222", border=True, flex=True)
        StyledLabel(container=setting_container, text="00:00:00", variable_name="remaining_time", left=165, top=415,
                    width=75, height=25, font_size=100, color="#222", border=True, flex=True)

        # Terminal
        terminal_container = StyledContainer(container=testing_container, variable_name="terminal_container",
                                             left=0, top=500, height=150, width=650, bg_color=True)
        self.terminal = Terminal(container=terminal_container, variable_name="terminal_text",
                                 left=10, top=15, width=610, height=100)

        self.testing_container = testing_container
        return testing_container


if __name__ == "__main__":
    configuration = {
        "config_project_name": "testing",
        "config_address": "0.0.0.0",
        "config_port": 9004,
        "config_multiple_instance": False,
        "config_enable_file_cache": False,
        "config_start_browser": False,
        "config_resourcepath": "./res/"
    }
    start(testing,
          address=configuration["config_address"],
          port=configuration["config_port"],
          multiple_instance=configuration["config_multiple_instance"],
          enable_file_cache=configuration["config_enable_file_cache"],
          start_browser=configuration["config_start_browser"])
