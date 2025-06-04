from remi.gui import *
from remi import start, App
import os
from myguilab import StyledContainer, StyledButton, StyledLabel, StyledDropDown, Terminal

class starts(App):
    def __init__(self, *args, **kwargs):
        if "editing_mode" not in kwargs:
            super(starts, self).__init__(*args, **{"static_file_path": {"my_res": "./res/"}})

    def idle(self):
        self.terminal.terminal_refresh()

    def main(self):
        return starts.construct_ui(self)

    @staticmethod
    def construct_ui(self):

        starts_container = StyledContainer(variable_name="starts_container", left=0, top=0)

        for idx, key in enumerate(('user', 'mode')):
            StyledLabel(container=starts_container, text={'user': 'User:', 'mode': 'Operating Mode:'}[key], variable_name=f"label_{key}",
                                     left=100, top=105 + idx*40, width=150, height=20, font_size=100, color='#444', align='right')
            StyledDropDown(container=starts_container, text={'user': ['User A', 'User B', 'User C'], 'mode': ['TE mode', 'TM mode']}[key],
                                variable_name=f"set_{key}", left=260, top=100 + idx*40, width=220, height=30)

        StyledLabel(container=starts_container, text="Welcome to 347 Probe Stage", variable_name="label_configuration",
                                 left=180, top=20, width=300, height=20, font_size=150, color="#222", align="left")
        StyledButton(container=starts_container, text="Edit", variable_name="edit",
                            left=260, top=180, normal_color='#007BFF', press_color='#0056B3')
        StyledButton(container=starts_container, text="Remove", variable_name='remove',
                              left=380, top=180, normal_color='#dc3545', press_color='#c82333')
        terminal_container = StyledContainer(container=starts_container, variable_name="terminal_container",
                                             left=0, top=500, height=150, width=650, bg_color=True)
        self.terminal = Terminal(container=terminal_container, variable_name="terminal_text",
                                 left=10, top=15, width=610, height=100)


        self.starts_container = starts_container
        return starts_container

    def onclick_connect(self, key):
        pass

if __name__ == "__main__":
    configuration = {
        'config_project_name': 'starts',
        'config_address': '0.0.0.0',
        'config_port': 9000,
        'config_multiple_instance': False,
        'config_enable_file_cache': False,
        'config_start_browser': True,
        'config_resourcepath': '"./res/"'
    }
    start(starts,
          address=configuration['config_address'],
          port=configuration['config_port'],
          multiple_instance=configuration['config_multiple_instance'],
          enable_file_cache=configuration['config_enable_file_cache'],
          start_browser=configuration['config_start_browser'])
