from myguilab import *
from remi.gui import *
from remi import start, App
import json
import coordinates
import os

def fmt(val):
    try:
        return f"{float(val):.2f}"
    except (ValueError, TypeError):
        return str(val)

class testing(App):
    def __init__(self, *args, **kwargs):
        file_path = os.path.join(os.getcwd(), "database", "selection_serial.json")
        with open(file_path, "r") as f:
            self.serial_list = json.load(f)
        self.timestamp = -1
        self.gds = coordinates.coordinates(read_file=False, name="./database/coordinates.json")
        self.number = self.gds.listdeviceparam("number")
        self.coordinate = self.gds.listdeviceparam("coordinate")
        self.polarization = self.gds.listdeviceparam("polarization")
        self.wavelength = self.gds.listdeviceparam("wavelength")
        self.type = self.gds.listdeviceparam("type")
        self.devicename = [f"{name} ({num})" for name, num in zip(self.gds.listdeviceparam("devicename"), self.number)]
        self.length = len(self.serial_list)
        self.filtered_idx = self.serial_list
        self.page_size = 50
        self.page_index = 0
        if "editing_mode" not in kwargs:
            super(testing, self).__init__(*args, **{"static_file_path": {"my_res": "./res/"}})

    def idle(self):
        self.terminal.terminal_refresh()

    def main(self):
        return testing.construct_ui(self)

    def build_table_rows(self):
        table = self.table
        data_rows = list(table.children.values())[1:]

        start_i = self.page_index * self.page_size
        end_i = min(len(self.filtered_idx), start_i + self.page_size)
        page_idx_slice = self.filtered_idx[start_i:end_i]
        needed = len(page_idx_slice)
        cur = len(data_rows)

        if needed > cur:
            for _ in range(needed - cur):
                tr = TableRow()
                for w in self.col_widths:
                    tr.append(TableItem("", style={
                        "width": f"{w}px",
                        "height": "30px",
                        "text-align": "center",
                        "border-bottom": "1px solid #ebebeb",
                        "padding": "1px 2px",
                        "overflow": "hidden",
                        "text-overflow": "ellipsis",
                        "white-space": "nowrap"
                    }))
                table.append(tr)
                data_rows.append(tr)

        for row_idx, row in enumerate(data_rows):
            if row_idx < needed:
                global_idx = page_idx_slice[row_idx]
                cells = list(row.children.values())
                bg = "#ffffff" if (start_i + row_idx) % 2 == 0 else "#f6f7f9"
                for c in cells:
                    c.style.update({"display": "table-cell", "background-color": bg})

                cells[0].set_text(self.devicename[global_idx])
                cells[1].set_text("0")

            else:
                for c in row.children.values():
                    c.style["display"] = "none"


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
        self.col_widths = [100, 20]
        table_container = StyledContainer(container=setting_container, variable_name="setting_container",
                                          left=0, top=40, height=295, width=240, border=True, overflow=True)
        self.table = StyledTable(container=table_container, variable_name="device_status",
                                 left=0, top=0, height=25, table_width=240, headers=headers, widths=self.col_widths, row=1)
        self.build_table_rows()

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
        "config_start_browser": True,
        "config_resourcepath": "./res/"
    }
    start(testing,
          address=configuration["config_address"],
          port=configuration["config_port"],
          multiple_instance=configuration["config_multiple_instance"],
          enable_file_cache=configuration["config_enable_file_cache"],
          start_browser=configuration["config_start_browser"])
