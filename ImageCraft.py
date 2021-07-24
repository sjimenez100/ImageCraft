'''
-7/24/2021
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
import GUI

# Variables
# GUI determined (not all)
resolution_divider = int()
threshold = int()
n_range = int()
keywords = []
show_image = False
fill_trans = False
output_directory = None
# global host image values
host_image = None
host_image_path = None
host_image_format = None
host_width = 0
host_height = 0
total_host_pixel_count = 0
tail = str()
resized = False
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


# calls GUI.gui() and sets the global variables accordingly
def set_gui():
    global threshold
    global keywords
    global host_image_path
    global resolution_divider
    global output_directory
    global show_image
    global n_range
    global fill_trans

    gui_data = GUI.gui()

    threshold = int(gui_data.threshold)
    n_range = int(gui_data.n_range)
    fill_trans = bool(gui_data.fill_trans)

    if gui_data.keywords is not None:
        keywords = gui_data.keywords.split()

    host_image_path = gui_data.host_image
    resolution_divider = int(gui_data.resolution_factor)
    output_directory = gui_data.output_directory
    show_image = not bool(gui_data.show_image)


# sets host_image variables
def set_host_image():
    global host_image_path
    global host_image
    global host_image_format
    global host_width
    global host_height
    global total_host_pixel_count
    global tail

    host_image = Image.open(host_image_path)

    host_image_format = host_image.format
    host_width, host_height = host_image.size[0], host_image.size[1]
    total_host_pixel_count = host_width * host_height
    tail = os.path.split(host_image_path)[1]


# if necessary, creates a new host image with a lower resolution
def host_resolution_configuration():
    global host_image_path
    global host_image
    global host_width
    global host_height
    global total_host_pixel_count
    global resized

    if resolution_divider > 1:
        host_image = host_image.resize((int(host_width / resolution_divider), int(host_height / resolution_divider)),
                                       Image.LANCZOS)

        host_image_path = os.path.join(cwd, rf'RESIZED-{tail}')
        host_image.save(host_image_path)

        resized = True

        host_width, host_height = host_image.size[0], host_image.size[1]
        total_host_pixel_count = (host_image.size[0] * host_image.size[1])


# configures all of the images into a dependent list of jimages
def dependent_image_configuration():
    global blank_jimage
    global trans_jimage

    # returns True if keyword is found inside string
    def keyword_inside(name):
        if len(keywords) > 0:
            for keyword in keywords:
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
    if pixel[3] <= threshold:
        if fill_trans:
            return trans_jimage
        else:
            return blank_jimage

    # returns best neighboring Jimage
    if threshold > 0:
        checked_neighbor = best_neighbor(pixel)
        if checked_neighbor is not None:
            n += 1
            return checked_neighbor

    # returns best dependent Jimage
    f += 1
    return check_dependents(pixel)


# returns the neighboring Jimage that is below the threshold
def best_neighbor(pixel):
    sel_len = len(selected_jimages)

    # only returns a Jimage once enough pixels have been covered
    if n_range == 0 or sel_len <= (host_width * n_range) + n_range:
        return None

    neighboring_images = find_neighbors(n_range, sel_len)

    for neighbor in neighboring_images:

        distance = numpy.linalg.norm(numpy.subtract(neighbor.av_color, pixel))

        if distance <= threshold:
            return neighbor

    return None


# returns the neighbors within the non-diagonal n_range
def find_neighbors(n_range, sel_len):

    neighbors = []

    for y in range(sel_len, sel_len - (host_width * n_range), -host_width):
        for x in range(-n_range, n_range+1):

            # logic prevents exceeding towards unknown elements in selected_jimages
            if y == sel_len and x >= 0:
                pass
            else:
                neighbor = selected_jimages[y + x]

            neighbors.append(neighbor)

    return neighbors


# returns the best possible dependent Jimage at or beneath the threshold
def check_dependents(pixel):
    best_jimage_distance = 510
    best_pot_jimage = Jimage(Image.new('RGBA', (0, 0)))

    for dependent_jimage in dependent_jimages:

        distance = numpy.linalg.norm(numpy.subtract(dependent_jimage.av_color, pixel))

        if distance <= threshold:
            return dependent_jimage

        if distance < best_jimage_distance:
            best_jimage_distance = distance
            best_pot_jimage = dependent_jimage

    return best_pot_jimage


# appends the best jimage to the selected jimages for each pixel and updates status
def main():
    i = 0
    last_pixel_time = 0
    last_pixel_number = 0

    # loops through each pixel of the host_image and appends a dependent_jimage to selected_jimages
    for pixel in host_image.getdata():

        pixel_copy = list(pixel)

        if host_image_format == 'JPEG' or host_image.mode == 'RGB':
            pixel_copy.append(225)

        jimage = best_jimage(pixel_copy)
        selected_jimages.append(jimage)

        # data status estimates/records/prints
        i += 1

        if i % numpy.floor(total_host_pixel_count/20) == 0:

            try:
                percent = i / total_host_pixel_count * 100
                speed = (i - last_pixel_number) / (time.time() - last_pixel_time)
                etc_raw = time.gmtime((total_host_pixel_count - i) / speed)
                etc = str(etc_raw.tm_hour) + 'hrs : ' + str(etc_raw.tm_min) + 'mins : ' + str(etc_raw.tm_sec) + 'secs'

                print(f'{format(percent, "0.2f")}% complete | pixel ({i} / {total_host_pixel_count}) | '
                      f'{format(speed, "0.2f")} pixels/sec | ETC: ({etc})')

            except:
                print(f'{format(i / total_host_pixel_count * 100, "0.2f")})% complete | pixel ({i} / '
                      f'{total_host_pixel_count} | n/a | n/a')

            last_pixel_time = time.time()
            last_pixel_number = i

        elif i == 1:
            print(f'{format(0, "0.2f")}% complete | pixel (0 / {total_host_pixel_count}) | n/a | n/a')

            last_pixel_time = time.time()
            last_pixel_number = i

        elif i == total_host_pixel_count:
            print(f'100% complete | pixel ({i} / {total_host_pixel_count}) | n/a | n/a')


# creates a mosaic from the list of selected_jimages
def create_mosaic():

    collage = Image.new('RGBA', (16*host_width, 16*host_height))

    rows = host_width
    cols = host_height

    i = 0

    for col in range(cols):
        for row in range(rows):
            x = row * 16
            y = col * 16
            collage.paste(selected_jimages[i].pil_image, (x, y))
            i += 1

    save_image(collage)


# saves the mosaic
def save_image(collage_image):
    global output_directory

    print('saving image...')

    # ensures that the new tail is .png
    copy_tail = tail
    tail_head = copy_tail.rsplit('.', 1)[0]
    new_tail = tail_head + '.png'

    # if output directory is undefined or not a directory (somehow)
    if output_directory is None or os.path.isdir(output_directory) is False:
        output_directory = os.path.join(cwd, r"mosaics")

    output_file = os.path.join(output_directory, rf'MOSAIC-{new_tail}')

    collage_image.save(output_file)
    print(f'image saved as "{output_file}"')

    if show_image:
        print('showing image...')
        collage_image.show()


# little bit of clean up and data print
def final_touches():

    # removes resized host_image
    if resized:
        os.remove(host_image_path)

    # does not show file explorer if it's on desktop
    if os.path.split(output_directory)[1] != 'Desktop':
        os.startfile(output_directory)

    # data print
    time_raw = time.gmtime(time.time() - start_time)
    time_complete = str(time_raw.tm_hour) + 'hrs : ' + str(time_raw.tm_min) + 'mins : ' + str(time_raw.tm_sec) + 'secs'

    n_cof = format(n/f, "0.2f")

    print(f'\nProcess Complete in ({time_complete}) | Parameters used - IT: {threshold} RF: '
          f'{resolution_divider} NR {n_range} | NCOF: {n_cof}')

    print()


if __name__ == "__main__":
    config_gui()
    set_gui()
    set_host_image()
    print('rescaling host image...')
    host_resolution_configuration()
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


