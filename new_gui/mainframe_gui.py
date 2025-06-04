# uncompyle6 version 3.9.2
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.7.3 (v3.7.3:ef4ec6ed12, Mar 25 2019, 22:22:05) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: /home/pi/Desktop/new GUI/main_gui.py
# Compiled at: 2023-02-14 23:59:31
# Size of source mod 2**32: 11801 bytes
from remi.gui import *
from remi import start, App
import threading
import webview
import time
from myguilab import StyledContainer, StyledButton, StyledLabel, StyledDropDown, Terminal

class NIR_Measurment_System(App):

    def __init__(self, *args, **kwargs):
        if "editing_mode" not in kwargs.keys():
            (super(NIR_Measurment_System, self).__init__)(*args, **{"static_file_path": {"my_res": "./res/"}})

    def idle(self):
        pass

    def main(self):
        return NIR_Measurment_System.construct_ui(self)

    @staticmethod
    def construct_ui(self):
        ip_address = "10.2.113.37"
        main = StyledContainer(variable_name="main", left=0, top=0, height=715, width=650)
        main_tab = TabBox()
        main_tab.attr_editor_newclass = False
        main_tab.css_align_content = "center"
        main_tab.css_align_items = "center"
        main_tab.css_height = "100%"
        main_tab.css_left = "0px"
        main_tab.css_margin = "0px"
        main_tab.css_position = "inherit"
        main_tab.css_top = "0px"
        main_tab.css_width = "100%"
        main_tab.variable_name = "main_tab"
        tab_cfg = [
            ("Start", 9000),
            ("Instruments", 9001),
            ("Registration", 9002),
            ("Devices", 9003),
            ("Testing", 9004),
        ]

        def make_iframe(port: int):
            w = Widget(_type="iframe", width="100%", height="100%", margin="0px")
            w.attributes.update({
                "src": f"http://{ip_address}:{port}",
                "width": "100%",
                "height": "100%",
            })
            w.style["border"] = "none"
            return w

        for title, port in tab_cfg:
            frame = make_iframe(port)
            setattr(self, title.lower(), frame)
            main_tab.add_tab(frame, title)

        main.append(main_tab, "main_tab")
        self.main = main
        return self.main

    #def onclick_setting(self, emitter):
      #  js = " var win = window.open('http://127.0.0.1:9999', 'popup','width=365,height=450,resizable=yes,scrollbars=yes');"
     #   self.execute_javascript(js)

def run_remi():
    start(NIR_Measurment_System,
          address='0.0.0.0', port=80,
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

    webview.create_window(
        'Probe Stage',
        'http://10.2.113.37',
        width=675,
        height=775,
        resizable=True
    )

    webview.start(func=disable_scroll)