'''
-08/09/2021
-ImageCraft, a program made by Sebastian Jimenez
-This script is responsible for running the custom GUI for ImageCraft
'''

# Imports
from gooey import Gooey, GooeyParser
import os


# GUI configuration of tabs, size , name, ect..
@Gooey(program_name='IMAGE CRAFT', default_size=(700, 650),
       program_description='A program designed to turn digital images into mosaics made of minecraft blocks.',
       menu=[{
           'name': 'File',
           'items': [{
               'type': 'AboutDialog',
               'menuTitle': 'About',
               'name': 'Image Craft (Beta)',
               'description': '2021',
               'website': 'https://potassium3919.itch.io/',
               'developer': 'Sebastian Jimenez',

           }]
       }, {
           'name': 'Help',
           'items': [{
               'type': 'Link',
               'menuTitle': 'Source Code',
               'url': 'https://github.com/sjimenez100/ImageCraft'
           }]}])

# contains attributes that are refined versions of the raw GUI inputs
class ImageGUI:

    def __init__(self):
        self.host_image_path = None
        self.keywords = None
        self.threshold = None
        self.resolution_divider = None
        self.show_image = None
        self.fill_trans = None
        self.n_range = None
        self.output_directory = None

    def start_get_and_clean(self):
        parser = GooeyParser()

        parser.add_argument('host_image_path',
                            metavar='Host Image',
                            widget='FileChooser', gooey_options={
                'validator': {
                    'test': 'str(user_input).endswith(".png") or str(user_input).endswith(".jpg")',
                    'message': 'Only image formats: (.png) or (.jpg) will be accepted'}},
                            help='Enter path of the image to process\n'
                                 r'Example: "C:\Users\user\Desktop\image.png"')

        parser.add_argument('-keywords',
                            metavar='Keywords (Recommended)',
                            help='Enter keywords separated by spaces to filter search\n'
                                 'Example: "concrete wool plank diamond blue"')

        parser.add_argument('-threshold',
                            metavar='Inverse Threshold', widget='Slider',
                            help='Enter an integer to adjust inverse threshold', default=15,
                            gooey_options={
                                'max': 150})

        parser.add_argument('-resolution_divider',
                            metavar='Resolution Factor', widget='Slider',
                            help='Enter an integer to adjust resolution (pixels per block)', default=8,
                            gooey_options={
                                'min': 1,
                                'max': 16})

        parser.add_argument('-show_image',
                            metavar='Display Image', widget='CheckBox',
                            help='Toggle whether to display image when process is complete',
                            action='store_false', default=True)

        parser.add_argument('-fill_trans',
                            metavar='Fill Transparency', widget='CheckBox',
                            help='Toggle whether to fill transparent pixels', action='store_true', default=False)

        parser.add_argument('-n_range',
                            metavar='Neighbor Range', widget='Slider', default=0,
                            gooey_options={'max': 3}, help='Enter non-diagonal search range for neighboring images\n'
                                                           'Only recommended with non-color-diverse images')

        parser.add_argument('-output_directory',
                            metavar='Output Location', widget='DirChooser',
                            default=rf'{os.path.join(os.getcwd(), "mosaics")}',
                            help='Enter path to output directory')

        inputs = parser.parse_args()

        self.threshold = int(inputs.threshold)
        self.n_range = int(inputs.n_range)
        self.fill_trans = bool(inputs.fill_trans)

        if str(inputs.keywords).isspace() or inputs.keywords is None:
            self.keywords = []
        else:
            self.keywords = list(str(inputs.keywords).split())

        self.host_image_path = inputs.host_image_path
        self.resolution_divider = int(inputs.resolution_divider)
        self.output_directory = inputs.output_directory
        self.show_image = not bool(inputs.show_image)




