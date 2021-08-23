'''
-08/23/2021
-ImageCraft, a program made by Sebastian Jimenez
-This script is responsible for running the main functionalities of Image Craft.
This does not include the custom GUI.
'''
# Imports
import sys
import time
import PIL.ImageFile
from PIL import Image
import numpy
import os
import IC_GUI

# Variables
# GUI determined 
image_gui = IC_GUI.ImageGUI()

# dependents
dependent_images = []
dependent_jimages = []
blank_jimage = None
trans_jimage = None

# misc.
selected_jimages = []
start_time = time.time()
cwd = os.getcwd()
n = 0
f = 0


# Classes

# Jimage class responsible for creating a synthetic of PIL.Image()
class Jimage:

    def __init__(self, pil_image):
        self.pil_image = pil_image
        self.data = self.pil_image.getdata()
        self.av_color = [0, 0, 0, 0]

    # returns the average color as a vector
    def average_color(self):
        num_pixels = 0
        av_color = numpy.array([0, 0, 0, 0])

        for p in range(len(self.data)):

            data_copy = list(self.data[p])

            if self.pil_image.mode == 'RGB':
                # assumes max opacity
                data_copy.append(255)

            av_color = numpy.add(av_color, data_copy)
            num_pixels += 1

        av_color = numpy.divide(av_color, num_pixels)

        return av_color


class HostImage:

    def __init__(self, fp):
        self.fp = fp
        self.pil_image = Image.open(fp)
        self.format = self.pil_image.format
        self.width, self.height = self.pil_image.size[0], self.pil_image.size[1]
        self.pixel_count = self.width * self.height
        self.tail = os.path.split(self.fp)[1]
        self.mode = self.pil_image.mode
        self.resized = False
        
    def lower_resolution(self):
        if image_gui.resolution_divider > 1:
            self.pil_image = self.pil_image.resize((int(self.width / image_gui.resolution_divider), 
                                                    int(self.height / image_gui.resolution_divider)), Image.LANCZOS)

            self.fp = os.path.join(cwd, rf'RESIZED-{self.tail}')
            self.pil_image.save(self.fp)

            self.resized = True

            self.width, self.height = self.pil_image.size[0], self.pil_image.size[1]
            self.pixel_count = (self.pil_image.size[0] * self.pil_image.size[1])

# Functions
# ensures that system does not ignore print() updates
def config_gui():
    class Unbuffered(object):
        def __init__(self, stream):
            self.stream = stream

        def write(self, data):
            self.stream.write(data)
            self.stream.flush()

        def writelines(self, datas):
            self.stream.writelines(datas)
            self.stream.flush()

        def __getattr__(self, attr):
            return getattr(self.stream, attr)

    sys.stdout = Unbuffered(sys.stdout)


# configures all of the images into a dependent list of jimages
def dependent_image_configuration():
    global blank_jimage
    global trans_jimage

    # returns True if keyword is found inside string
    def keyword_inside(name):
        if len(image_gui.keywords) > 0:
            for keyword in image_gui.keywords:
                if keyword in name:
                    return True
        else:
            return True

        return False

    dependent_images_directory = os.path.join(cwd, 'mc_images')

    # sets common images
    blank_jimage = Jimage(Image.new('RGBA', (0, 0)))
    trans_jimage = Jimage(Image.open(os.path.join(dependent_images_directory, 'glass.png')))

    # creates path and a unrefined list of .png images from the directory
    for dependent_image_name in os.listdir(dependent_images_directory):
        if keyword_inside(dependent_image_name):
            final_dependent_image_path = os.path.join(dependent_images_directory, dependent_image_name)
            dependent_images.append(Image.open(final_dependent_image_path))

    # turns each PIL.Image() into a Jimage() with a pre-calculated av_color
    for image in dependent_images:
        new_jimage_instance = Jimage(image)
        dependent_jimages.append(new_jimage_instance)
        new_jimage_instance.av_color = new_jimage_instance.average_color()


# returns first dependent Jimage that in beneath the threshold number
def best_jimage(pixel):
    global n
    global f

    # returns the Jimage for transparent space
    if pixel[3] <= image_gui.threshold:
        if image_gui.fill_trans:
            return trans_jimage
        else:
            return blank_jimage

    return check_dependents(pixel)


# returns the best possible dependent Jimage at or beneath the threshold
def check_dependents(pixel):
    best_jimage_distance = 510
    best_dependent = Jimage(Image.new('RGBA', (0, 0)))
    index = -1

    for dependent_jimage in dependent_jimages:
        index += 1

        distance = numpy.linalg.norm(numpy.subtract(dependent_jimage.av_color, pixel))

        if distance <= image_gui.threshold:
            return dependent_jimage

        if distance < best_jimage_distance:
            best_jimage_distance = distance
            best_dependent = dependent_jimage

    # insert best_dependent into the front of the list
    dependent_jimages.insert(0, dependent_jimages.pop(index))

    return best_dependent


# appends the best jimage to the selected jimages for each pixel and updates status
def main():
    i = 0
    last_pixel_time = 0
    last_pixel_number = 0

    # loops through each pixel of the host_image and appends a dependent_jimage to selected_jimages
    for pixel in host_image.pil_image.getdata():

        pixel_copy = list(pixel)

        if host_image.format == 'JPEG' or host_image.mode == 'RGB':
            pixel_copy.append(225)

        jimage = best_jimage(pixel_copy)
        selected_jimages.append(jimage)

        # data status estimates/records/prints
        i += 1

        if i % numpy.floor(host_image.pixel_count/20) == 0:

            try:
                percent = i / host_image.pixel_count * 100
                speed = (i - last_pixel_number) / (time.time() - last_pixel_time)
                etc_raw = time.gmtime((host_image.pixel_count - i) / speed)
                etc = str(etc_raw.tm_hour) + 'hrs : ' + str(etc_raw.tm_min) + 'mins : ' + str(etc_raw.tm_sec) + 'secs'

                print(f'{format(percent, "0.2f")}% complete | pixel ({i} / {host_image.pixel_count}) | '
                      f'{format(speed, "0.2f")} pixels/sec | ETC: ({etc})')

            except:
                print(f'{format(i / host_image.pixel_count * 100, "0.2f")})% complete | pixel ({i} / '
                      f'{host_image.pixel_count} | n/a | n/a')

            last_pixel_time = time.time()
            last_pixel_number = i

        elif i == 1:
            print(f'{format(0, "0.2f")}% complete | pixel (0 / {host_image.pixel_count}) | n/a | n/a')

            last_pixel_time = time.time()
            last_pixel_number = i

        elif i == host_image.pixel_count:
            print(f'100% complete | pixel ({i} / {host_image.pixel_count}) | n/a | n/a')


# creates a mosaic from the list of selected_jimages
def create_mosaic():

    mosaic = Image.new('RGBA', (16*host_image.width, 16*host_image.height))

    rows = host_image.width
    cols = host_image.height

    i = 0

    for col in range(cols):
        for row in range(rows):
            x = row * 16
            y = col * 16
            mosaic.paste(selected_jimages[i].pil_image, (x, y))
            i += 1

    save_image(mosaic)


# saves the mosaic
def save_image(mosaic_image):
    print('saving image...')

    # ensures that the new tail is .png
    copy_tail = host_image.tail
    tail_head = copy_tail.rsplit('.', 1)[0]
    new_tail = tail_head + '.png'

    # mkdir 'mosaics' if it does not already exist
    if 'mosaics' not in os.listdir(cwd):
        os.mkdir('mosaics')

    # if output directory is undefined or not a directory (somehow)
    if image_gui.output_directory is None or os.path.isdir(image_gui.output_directory) is False:
        image_gui.output_directory = os.path.join(cwd, r"mosaics")

    output_file = os.path.join(image_gui.output_directory, rf'MOSAIC-{new_tail}')

    mosaic_image.save(output_file)
    print(f'image saved as "{output_file}"')

    if image_gui.show_image:
        print('showing image...')
        mosaic_image.show()


# little bit of clean up and data print
def final_touches():

    # removes resized host_image
    if host_image.resized:
        os.remove(host_image.fp)

    # does not show file explorer if it's on desktop
    if os.path.split(image_gui.output_directory)[1] != 'Desktop':
        os.startfile(image_gui.output_directory)

    # data print
    time_raw = time.gmtime(time.time() - start_time)
    time_complete = str(time_raw.tm_hour) + 'hrs : ' + str(time_raw.tm_min) + 'mins : ' + str(time_raw.tm_sec) + 'secs'

    print(f'\nProcess Complete in ({time_complete}) | Parameters used - IT: {image_gui.threshold} RF: '
          f'{image_gui.resolution_divider}')

    print()


if __name__ == "__main__":
    config_gui()
    image_gui.start_get_and_clean()
    host_image = HostImage(image_gui.host_image_path)
    print('rescaling host image...')
    host_image.lower_resolution()
    print('retrieving minecraft images...')
    dependent_image_configuration()
    print('main process initiated...')
    print()
    main()
    print('\nmain process complete')
    print('mapping images...')
    create_mosaic()
    print('deleting resized host image...')
    final_touches()


