import sys
import time
from zipfile import ZipFile
import PIL.ImageFile
from PIL import Image
import numpy
import os
import GUI

n = 0
f = 0
# GUI globals
versions_directory = None
version = None
output_directory = None

n_range = None
start_time = time.time()
keywords = []
cwd = os.getcwd()
resolution_divider = int()
threshold = int()
show_image = False

# global host image values
host_image = Image.new('RGBA', (0, 0))
host_image_path = None
host_image_format = None
host_width = 0
host_height = 0
total_host_pixel_count = 0
tail = None
resized = False


# Set dependent images/jimages
dependent_images = []
dependent_images_directory = None
dependent_jimages = []

# Selected jimages
selected_jimages = []


class Jimage:

    def __init__(self, pil_image):
        self.pil_image = pil_image
        self.data = self.pil_image.getdata()
        self.av_color = [0, 0, 0, 0]

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


def set_gui():
    global version
    global threshold
    global keywords
    global host_image_path
    global resolution_divider
    global output_directory
    global show_image
    global n_range

    gui_data = GUI.gui(find_available_versions(), os.getcwd())

    version = gui_data.version
    threshold = int(gui_data.threshold)
    n_range = int(gui_data.n_range)

    if gui_data.keywords is not None:
        keywords = gui_data.keywords.split()

    host_image_path = gui_data.host_image
    resolution_divider = int(gui_data.resolution_factor)
    output_directory = gui_data.output_directory
    show_image = bool(gui_data.show_image)


def find_available_versions():
    global versions_directory
    available_versions = []

    versions_directory = rf'{os.environ["APPDATA"]}\.minecraft\versions'
    for _version in os.listdir(versions_directory):
        if os.path.isdir(rf'{versions_directory}\{_version}'):
            for file in os.listdir(rf'{versions_directory}\{_version}'):
                if file.endswith('.jar'):
                    available_versions.append(_version)

    return available_versions


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


def configure_files():

    global dependent_images_directory

    if version not in os.listdir(rf'{cwd}\versions'):
        os.system(fr'copy {versions_directory}\{version}\{version}.jar {cwd}\versions')
        os.rename(rf'versions\{version}.jar', rf'versions\{version}.zip')
        os.system(rf'mkdir versions\{version}')

        with ZipFile(rf'versions\{version}.zip', 'r') as zip:
            zip.extractall(path=rf'versions\{version}')

        os.remove(rf'versions\{version}.zip')

    dependent_images_directory = rf'{cwd}\versions\{version}\assets\minecraft\textures\block'


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
        host_image_path = rf'{cwd}\RESIZED-VERSION{tail}'
        host_image.save(host_image_path)

        resized = True

        host_width, host_height = host_image.size[0], host_image.size[1]
        total_host_pixel_count = (host_image.size[0] * host_image.size[1])


# configures all of the images into a dependent list of jimages
def dependent_image_configuration():

    def keyword_inside(name):
        if len(keywords) > 0:
            for keyword in keywords:
                if keyword in name:
                    return True
        else:
            return True

        return False

    # creates path and a unrefined list of .png images from the directory
    for dependent_image_name in os.listdir(dependent_images_directory):
        if dependent_image_name.endswith('.png') and keyword_inside(dependent_image_name):
            final_dependent_image_path = dependent_images_directory + '\\' + dependent_image_name
            dependent_images.append(Image.open(final_dependent_image_path))

    # removes anything that is not 16x16
    for image in dependent_images:
        if image.size != (16, 16) or (image.mode != 'RGBA' and image.mode != 'RGB'):
            dependent_images.remove(image)
        else:
            new_jimage_instance = Jimage(image)
            dependent_jimages.append(new_jimage_instance)
            new_jimage_instance.av_color = new_jimage_instance.average_color()


# returns the dependent jimage that is closes to a selected pixel in the host
def best_jimage(pixel):
    global n
    global f
    if threshold > 0:
        checked_neighbor = check_neighbors(pixel)
        if checked_neighbor is not None:
            n += 1
            return checked_neighbor
        else:
            f+= 1
            return check_dependents(pixel)
    else:
        f+=1
        return check_dependents(pixel)


def check_neighbors(pixel):
    sel_len = len(selected_jimages)

    if n_range == 0 or sel_len <= (host_width * n_range) + n_range:
        return None

    neighboring_images = find_neighbors(n_range, sel_len)

    for neighbor in neighboring_images:

        distance = numpy.linalg.norm(neighbor.av_color - pixel)

        if distance < threshold:
            return neighbor

    return None


def find_neighbors(n_range, sel_len):

    neighbors = []

    for y in range(sel_len, sel_len - (host_width * n_range), -host_width):
        for x in range(-n_range, n_range+1):

            if y == sel_len and x >= 0:
                pass
            else:
                neighbor = selected_jimages[y + x]

            neighbors.append(neighbor)

    return neighbors


def check_dependents(pixel):
    best_jimage_distance = 255
    best_pot_jimage = Jimage(Image.new('RGBA', (0, 0)))

    for dependent_jimage in dependent_jimages:

        distance = numpy.linalg.norm(dependent_jimage.av_color - pixel)

        if distance < threshold:
            return dependent_jimage

        if distance < best_jimage_distance:
            best_jimage_distance = distance
            best_pot_jimage = dependent_jimage

    return best_pot_jimage


def transition():
    i = 0
    last_pixel_time = 0
    last_pixel_number = 0

    for pixel in host_image.getdata():

        pixelcopy = list(pixel)

        if host_image_format == 'JPEG':
            pixelcopy.append(225)

        jimage = best_jimage(pixelcopy)
        selected_jimages.append(jimage)

        i += 1

        if i % numpy.floor(total_host_pixel_count/20) == 0:
            percent = i / total_host_pixel_count * 100
            speed = (i-last_pixel_number)/(time.time()-last_pixel_time)
            etc_raw = time.gmtime((total_host_pixel_count-i)/speed)
            etc = str(etc_raw.tm_hour) + 'hrs : ' + str(etc_raw.tm_min) + 'mins : ' + str(etc_raw.tm_sec) + 'secs'

            try:
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


def create_collage():

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


def save_image(collage_image):
    print('saving image...')
    global output_directory

    new_tail = tail
    formats = ['.JPEG', '.jpg', '.jpeg', '.JPG']

    for _format in formats:
        if _format in new_tail:
            new_tail = new_tail.removesuffix(_format) + '.png'

    if output_directory is None:
        output_directory = rf'{cwd}\COLLAGE-VERSION{new_tail}'
    else:
        output_directory += rf'\COLLAGE-VERSION{new_tail}'

    collage_image.save(output_directory)
    print(f'image saved as "{output_directory}"')

    if show_image:
        print('showing image...')
        collage_image.show()


def final_touches():
    if resized:
        os.remove(host_image_path)

    time_raw = time.gmtime(time.time() - start_time)
    time_complete = str(time_raw.tm_hour) + 'hrs : ' + str(time_raw.tm_min) + 'mins : ' + str(time_raw.tm_sec) + 'secs'

    n_cof = format(n/f, "0.2f")

    print(f'\nProcess Complete in ({time_complete}) | Parameters used - VR: {version} IT: {threshold} RF: '
          f'{resolution_divider} NR {n_range} | NCOF: {n_cof}')

    print()


if __name__ == "__main__":
    set_gui()
    set_host_image()
    print('configuring files...')
    configure_files()
    print('rescaling host image...')
    host_resolution_configuration()
    print('retrieving minecraft images...')
    dependent_image_configuration()
    print('main process initiated...')
    print()
    transition()
    print('\nmain process complete')
    print('mapping images...')
    create_collage()
    print('deleting resized host image...')
    final_touches()


