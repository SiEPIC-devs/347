from lab_gui import *
from remi.gui import *
from remi import start, App
import threading
import webview
import signal
import socket
import time
import lab_coordinates
import glob

filename = "coordinates.json"

class stage_control(App):
    def __init__(self, *args, **kwargs):
        self.timestamp = -1
        if "editing_mode" not in kwargs:
            super(stage_control, self).__init__(*args, **{"static_file_path": {"my_res": "./res/"}})

    def idle(self):
        pass

    def main(self):
        return self.construct_ui()

    def run_in_thread(self, target, *args):
        threading.Thread(target=target, args=args, daemon=True).start()

    def construct_ui(self):
        stage_control_container = StyledContainer(container=None, variable_name="stage_control_container",
                                                  left=0, top=0, height=350, width=650)

        xyz_container = StyledContainer(container=stage_control_container, variable_name="xyz_container",
                                        left=0, top=20, height=300, width=410)

        self.stop_btn = StyledButton(container=xyz_container, text="Stop", variable_name="stop_button", font_size=100,
                     left=125, top=10, width=90, height=30, normal_color="#dc3545", press_color="#c82333")
        self.lock_box = StyledCheckBox(container=xyz_container, variable_name="lock_box", left=225, top=10,
                       width=10, height=10, position="absolute")
        StyledLabel(container=xyz_container, text="Lock", variable_name="lock_label", left=255, top=17,
                    width=80, height=50, font_size=100, color="#222")

        labels = ["X", "Y", "Z", "Chip", "Fiber"]
        top_positions = [70, 110, 150, 190, 230]
        left_arrows = ["⮜", "⮟", "Down", "⭮", "⭮"]
        right_arrows = ["⮞", "⮝", "Up", "⭯", "⭯"]
        var_prefixes = ["x", "y", "z", "chip", "fiber"]
        position_texts = [f"{210.4} um", f"{211.4} um", f"{212.4} um", f"{0.1} deg", f"{0.1} deg"]

        for i in range(5):
            prefix = var_prefixes[i]
            top = top_positions[i]

            StyledLabel(container=xyz_container, text=labels[i], variable_name=f"{prefix}_label", left=0, top=top,
                        width=55, height=30, font_size=100, color="#222", flex=True, bold=True, justify_content="right")
            setattr(self, f"{prefix}_left_btn",
                    StyledButton(container=xyz_container, text=left_arrows[i],
                                 variable_name=f"{prefix}_left_button",
                                 font_size=100, left=65, top=top, width=50, height=30,
                                 normal_color="#007BFF", press_color="#0056B3"))
            setattr(self, f"{prefix}_input",
                    StyledSpinBox(container=xyz_container, variable_name=f"{prefix}_step", min_value=0, max_value=1000,
                                    step=0.1, left=125, top=top, width=73, height=30, position="absolute"))
            setattr(self, f"{prefix}_right_btn",
                    StyledButton(container=xyz_container, text=right_arrows[i],
                                 variable_name=f"{prefix}_right_button",
                                 font_size=100, left=225, top=top, width=50, height=30,
                                 normal_color="#007BFF", press_color="#0056B3"))
            StyledLabel(container=xyz_container, text=position_texts[i], variable_name=f"{prefix}_position_label",
                        left=280, top=top, width=100, height=30, font_size=100, color="#222",
                        flex=True, bold=True, justify_content="right")

        self.zero_btn = StyledButton(container=xyz_container, text="Zero", variable_name="zero_button", font_size=100,
                     left=310, top=10, width=90, height=30, normal_color="#007BFF", press_color="#0056B3")

        limits_container = StyledContainer(container=stage_control_container, variable_name="limits_container",
                                           left=430, top=20, height=90, width=90, border=True)
        StyledLabel(container=limits_container, text="Limits", variable_name="limits_label",
                    left=22.5, top=-12, width=40, height=20, font_size=100, color="#444", position="absolute",
                    flex=True, on_line=True, justify_content="center")
        self.limit_setting_btn = StyledButton(container=limits_container, text="Setting", variable_name="limit_setting_btn",
                                          font_size=100, left=5, top=10, width=80, height=30,
                                          normal_color="#007BFF", press_color="#0056B3")
        StyledButton(container=limits_container, text="Clear", variable_name="clear_button",
                     font_size=100, left=5, top=50, width=80, height=30,
                     normal_color="#007BFF", press_color="#0056B3")

        fine_align_container = StyledContainer(container=stage_control_container, variable_name="fine_align_container",
                                               left=540, top=20, height=90, width=90, border=True)
        StyledLabel(container=fine_align_container, text="Fine Align",
                    variable_name="fine_align_label", left=12.5, top=-12, width=65, height=20,
                    font_size=100, color="#444", position="absolute", flex=True, on_line=True, justify_content="center")
        StyledButton(container=fine_align_container, text="Setting", variable_name="fine_align_setting_btn",
                     font_size=100, left=5, top=10, width=80, height=30,
                     normal_color="#007BFF", press_color="#0056B3")
        StyledButton(container=fine_align_container, text="Start", variable_name="start_button",
                     font_size=100, left=5, top=50, width=80, height=30,
                     normal_color="#007BFF", press_color="#0056B3")

        raster_container = StyledContainer(container=stage_control_container, variable_name="raster_container",
                                           left=430, top=130, height=90, width=90, border=True)
        StyledLabel(container=raster_container, text="Raster", variable_name="raster_label",
                    left=25, top=-12, width=40, height=20, font_size=100, color="#444", position="absolute",
                    flex=True, on_line=True, justify_content="center")
        StyledButton(container=raster_container, text="Setting", variable_name="raster_setting_btn",
                     font_size=100, left=5, top=10, width=80, height=30,
                     normal_color="#007BFF", press_color="#0056B3")
        StyledButton(container=raster_container, text="Scan", variable_name="scan_button",
                     font_size=100, left=5, top=50, width=80, height=30,
                     normal_color="#007BFF", press_color="#0056B3")

        move_container = StyledContainer(container=stage_control_container, variable_name="move_container",
                                         left=430, top=240, height=88, width=200, border=True)
        StyledLabel(container=move_container, text="Move To Device", variable_name="move_label",
                    left=50, top=-12, width=100, height=20, font_size=100, color="#444", position="absolute",
                    flex=True, on_line=True, justify_content="center")
        StyledLabel(container=move_container, text="Move to", variable_name="move_to_label",
                    left=0, top=15, width=60, height=28, font_size=100, color="#222",
                    position="absolute", flex=True, justify_content="right")
        self.move_dd = StyledDropDown(container=move_container, variable_name="move_to_dd", text="N/A",
                       left=75, top=15, height=28, width=115)
        self.move_dd.attributes["title"] = "N/A"
        self.load_btn = StyledButton(container=move_container, text="Load", variable_name="load_button",
                     font_size=100, left=10, top=50, width=85, height=28,
                     normal_color="#007BFF", press_color="#0056B3")
        self.move_btn = StyledButton(container=move_container, text="Move", variable_name="move_button",
                     font_size=100, left=105, top=50, width=85, height=28,
                     normal_color="#007BFF", press_color="#0056B3")

        self.stop_btn.do_onclick(lambda *_: self.run_in_thread(self.onclick_stop))
        self.zero_btn.do_onclick(lambda *_: self.run_in_thread(self.onclick_zero))
        self.x_left_btn.do_onclick(lambda *_: self.run_in_thread(self.onclick_x_left))
        self.x_right_btn.do_onclick(lambda *_: self.run_in_thread(self.onclick_x_right))
        self.y_left_btn.do_onclick(lambda *_: self.run_in_thread(self.onclick_y_left))
        self.y_right_btn.do_onclick(lambda *_: self.run_in_thread(self.onclick_y_right))
        self.z_left_btn.do_onclick(lambda *_: self.run_in_thread(self.onclick_z_left))
        self.z_right_btn.do_onclick(lambda *_: self.run_in_thread(self.onclick_z_right))
        self.chip_left_btn.do_onclick(lambda *_: self.run_in_thread(self.onclick_chip_left))
        self.chip_right_btn.do_onclick(lambda *_: self.run_in_thread(self.onclick_chip_right))
        self.fiber_left_btn.do_onclick(lambda *_: self.run_in_thread(self.onclick_fiber_left))
        self.fiber_right_btn.do_onclick(lambda *_: self.run_in_thread(self.onclick_fiber_right))
        self.load_btn.do_onclick(lambda *_: self.run_in_thread(self.onclick_load_btn))
        self.move_btn.do_onclick(lambda *_: self.run_in_thread(self.onclick_move_btn))
        self.limit_setting_btn.do_onclick(lambda *_: self.run_in_thread(self.onclick_limit_setting_btn))
        self.lock_box.onchange.do(lambda emitter, value: self.run_in_thread(self.onchange_lock_box, emitter, value))
        self.move_dd.onchange.do(lambda emitter, value: self.run_in_thread(self.onchange_move_dd, emitter, value))

        self.stage_control_container = stage_control_container
        return stage_control_container

    def onclick_stop(self):
        print("Stop")

    def onclick_zero(self):
        print("Zero")

    def onclick_x_left(self):
        value = self.x_input.get_value()
        print(f"X Left {value} um")

    def onclick_x_right(self):
        value = self.x_input.get_value()
        print(f"X Right {value} um")

    def onclick_y_left(self):
        value = self.y_input.get_value()
        print(f"Y Left {value} um")

    def onclick_y_right(self):
        value = self.y_input.get_value()
        print(f"Y Right {value} um")

    def onclick_z_left(self):
        value = self.z_input.get_value()
        print(f"Z Down {value} um")

    def onclick_z_right(self):
        value = self.z_input.get_value()
        print(f"Z Up {value} um")

    def onclick_chip_left(self):
        value = self.chip_input.get_value()
        print(f"Chip Turn CW {value} deg")

    def onclick_chip_right(self):
        value = self.chip_input.get_value()
        print(f"Chip Turn CCW {value} deg")

    def onclick_fiber_left(self):
        value = self.fiber_input.get_value()
        print(f"Fiber Turn CW {value} deg")

    def onclick_fiber_right(self):
        value = self.fiber_input.get_value()
        print(f"Fiber Turn CCW {value} deg")

    def onclick_load_btn(self):
        self.gds = lab_coordinates.coordinates(("./res/" + filename), read_file=False,
                                               name="./database/coordinates.json")
        self.number = self.gds.listdeviceparam("number")
        self.coordinate = self.gds.listdeviceparam("coordinate")
        self.polarization = self.gds.listdeviceparam("polarization")
        self.wavelength = self.gds.listdeviceparam("wavelength")
        self.type = self.gds.listdeviceparam("type")
        self.devices = [f"{name} ({num})" for name, num in zip(self.gds.listdeviceparam("devicename"), self.number)]

        self.move_dd.empty()
        self.move_dd.append(self.devices)
        self.move_dd.attributes["title"] = self.devices[0]

    def onclick_move_btn(self):
        print("Move")

    def onchange_lock_box(self, emitter, value):
        enabled = value == 0
        widgets_to_check = [self.stage_control_container]
        while widgets_to_check:
            widget = widgets_to_check.pop()

            if hasattr(widget, "variable_name") and widget.variable_name == "lock_box":
                continue

            if isinstance(widget, (Button, DropDown)):
                widget.set_enabled(enabled)

            if hasattr(widget, "children"):
                widgets_to_check.extend(widget.children.values())

        print("Unlocked" if enabled else "Locked")

    def onclick_limit_setting_btn(self):
        local_ip = get_local_ip()
        webview.create_window(
            "Setting",
            f"http://{local_ip}:7002",
            width=317,
            height=206,
            resizable=True,
            on_top=True,
        )

    def onchange_move_dd(self, emitter, value):
        self.move_dd.attributes["title"] = value


def get_local_ip():
    """Automatically detect local LAN IP address"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Fake connect to get route IP
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"  # fallback


def run_remi():
    start(stage_control,
          address='0.0.0.0', port=8000,
          start_browser=False,
          multiple_instance=False)


def disable_scroll():
    try:
        webview.windows[0].evaluate_js("""
            document.documentElement.style.overflow = 'hidden';
            document.body.style.overflow = 'hidden';
        """)
    except Exception as e:
        print("JS Wrong", e)


if __name__ == '__main__':
    threading.Thread(target=run_remi, daemon=True).start()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    local_ip = get_local_ip()
    webview.create_window(
        'Stage Control',
        f'http://{local_ip}:8000',
        width=672,
        height=407,
        resizable=True
    )

    webview.start(func=disable_scroll)
