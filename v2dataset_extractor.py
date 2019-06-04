# -*- coding: utf-8 -*-
from __future__ import print_function

from datetime import datetime
import os

import npyscreen

from apollo import create_app, models, services
# class TestApp(npyscreen.NPSApp):
#     def main(self):
#         # These lines create the form and populate it with widgets.
#         # A fairly complex screen in only 8 or so lines of code - a line for each control.
#         F  = npyscreen.Form(name = "Welcome to Npyscreen",)
#         t  = F.add(npyscreen.TitleText, name = "Text:",)
#         fn = F.add(npyscreen.TitleFilename, name = "Filename:")
#         fn2 = F.add(npyscreen.TitleFilenameCombo, name="Filename2:")
#         dt = F.add(npyscreen.TitleDateCombo, name = "Date:")
#         s  = F.add(npyscreen.TitleSlider, out_of=12, name = "Slider")
#         ml = F.add(npyscreen.MultiLineEdit,
#                value = """try typing here!\nMutiline text, press ^R to reformat.\n""",
#                max_height=5, rely=9)
#         ms = F.add(npyscreen.TitleSelectOne, max_height=4, value = [1,], name="Pick One",
#                 values = ["Option1","Option2","Option3"], scroll_exit=True)
#         ms2= F.add(npyscreen.TitleMultiSelect, max_height =-2, value = [1,], name="Pick Several",
#                 values = ["Option1","Option2","Option3"], scroll_exit=True)

#         # This lets the user interact with the Form.
#         F.edit()

#         print ms.get_selected_objects()

# if __name__ == "__main__":
#     App = TestApp()
#     App.run()


def export_locations(deployment, path):
    locations = services.locations.find(deployment=deployment)
    timestamp = datetime.utcnow()
    filename = 'locations-{:%Y%m%d%H%M%S%f}.csv'.format(timestamp)

    with open(os.path.join(path, deployment.name, filename), 'w') as f:
        for line in services.locations.export_list(locations):
            f.write(line)


def export_samples(deployment, path):
    samples = services.samples.find(deployment=deployment)
    output_path = os.path.join(path, deployment.name, 'samples')
    if not os.path.exists(output_path):
        os.mkdir(output_path)

    for sample in samples:
        filename = '{}.csv'.format(sample.name)
        with open(os.path.join(output_path, filename), 'w') as f:
            location_codes = services.locations.find(
                samples=sample).scalar('code')
            for code in location_codes:
                f.write('{}\n'.format(code))


class MainForm(npyscreen.Form):
    def __init__(self, *args, **kwargs):
        self.deployment = kwargs.pop('deployment')
        super(MainForm, self).__init__(*args, **kwargs)

    def create(self):
        self.output_path = self.add(
            npyscreen.TitleFilename, name='Export path')
        self.event_picker = self.add(
            npyscreen.TitleMultiSelect, max_height=-2, name='Select events',
            values=models.Event.objects.filter(
                deployment=self.deployment
            ).order_by('start_date').scalar('name'),
            scroll_exit=True)

    def afterEditing(self):
        deployment_path = os.path.join(
            self.output_path.value, self.deployment.name)
        if not os.path.exists(deployment_path):
            os.mkdir(deployment_path)

        # export_locations(self.deployment, self.output_path.value)
        export_samples(self.deployment, self.output_path.value)

        self.parentApp.setNextForm(None)


class ExtractorApp(npyscreen.NPSAppManaged):
    def __init__(self, *args, **kwargs):
        self.deployment = models.Deployment.objects.filter(
            hostnames='localhost').first()

        super(ExtractorApp, self).__init__(*args, **kwargs)

    def onStart(self):
        self.registerForm(
            'MAIN', MainForm(
                deployment=self.deployment, name='Apollo 2 Data Exporter'))


if __name__ == '__main__':
    app = create_app()

    with app.app_context():
        App = ExtractorApp()
        App.run()
