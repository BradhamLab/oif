# System level imports
import sys
import shutil
from os import path, makedirs
import getopt

# ignore warnings
import warnings

# import json to dump meta information
import json

# numerics
import numpy as np

# image library
from skimage.io import imsave

# Local libraries
# sys.path.append("/home/dakota/PythonModules/OIF/")
import oiffile
# from CellLabeller import scale_image

def scale_bit_image(image, bits, img_min=0, new_min=0, new_max=1):
    """
    Scale amplitude values to a new range.

    Scale values within an array between `new_min` and `old_min`.

    Arguments:
        image (numpy.ndarray): image to be scaled.
        bits (int): how many unsigned bits the integer can take. (ex. 8-bit)
        img_min (int): minimum value for image range. Default is 0.
        new_min (float): new minimum for re-scaled data.
        new_max (float): new maximum for re-scaled data.
    Returns:
        (numpy.ndarray): scaled image with values in [`new_min`, `new_max`].
    """
    img_max = 2**bits - 1
    scale_quotient = (new_max - new_min)/(img_max - img_min)
    scaled = scale_quotient*(image - img_min) + new_min
    return(scaled)


def oif_to_dir_tree(in_file, channel_stains, person, hpf, treatment, out_dir, prefix=""):
    """
    Write data contained in a .oif file to directories.

    Write data contained in a .oif file to directories. Directories are
    structured such that the name of the basename of the .oif file (e.g. 
    /path/to/my/<basename>.oif) is used as the parent directory. Each parent
    directory then contains subdirectories for every channel contained in the
    .oif file. Every channel subdirectory then contains .png images for each
    z-stack contained for that channel. Within each parent directory a file
    "metadata.json" is also created to house annotated data for the embryo.

    File structure example using "/path/to/my/<basename>.oif" with 3 Channels:
    |_out_dir
      metadata.json
      |_basename
      |_Channel1
        |_z0.png
        |_z1.png
        ...
      |_Channel2
        |_z0.png
        |_z1.png
        ...
      |_Channel3
        |_z0.png
        |_z1.png
        ...

    Arguments:
        in_file (string): path to .oif file to parse.
        channel_stains (list, string): list of strings denoting what each
            channel, in order, is staining for.
        person (string): person who imaged the embryo.
        hpf (float): hours past fertilization 
        treatment (string): treatment embryo was exposed to.
        out_dir (string): output directory to house output directory tree.
        prefix (string, optional): string to append to beginning of directory
            names. Default is the empty string "". 
    Returns:
        None
    """
    metadata = {}
    metadata["Person"] = person
    metadata["HPF"] = hpf
    metadata["Treatment"] = treatment
    for i, each in enumerate(channel_stains):
        metadata["Channel{}".format(i + 1)] = {"Stain": each}
    with oiffile.OifFile(in_file) as oif:
        datetime = oif.mainfile["Acquisition Parameters Common"]["ImageCaputreDate"]
        metadata["CaptureDateTime"] = datetime
        reference = oif.mainfile['Reference Image Parameter']
        metadata["HeightConvert"] = "{} {}".format(
                                             reference['HeightConvertValue'],
                                             reference['HeightUnit'])
        metadata["WidthConvert"] = "{} {}".format(
                                             reference['WidthConvertValue'],
                                             reference['WidthUnit'])
        nbits = reference['ValidBitCounts']
        axis_order = oif.mainfile['Axis Parameter Common']['AxisOrder']
        z_axis = [str(i) for i, x in enumerate(axis_order) if x == 'Z']
        axis_key = "Axis {} Parameters Common".format(z_axis[0])
        metadata['DepthConvert'] = "{} {}".format(
                                           oif.mainfile[axis_key]['Interval'],
                                           oif.mainfile[axis_key]['UnitName'])
        axes = oif.tiffs.axes
        image = oif.asarray()
        base_name = prefix + path.splitext(path.basename(in_file))[0]
        base_dir = path.join(out_dir, base_name)
        if (not path.exists(base_dir)):
            makedirs(base_dir)
        else:
            msg = "WARNING: {} already exists. Potentially overwrite contents?"
            confirm = input(msg.format(base_dir))
            if confirm.lower() not in ['y', 'yes']:
                sys.exit()
        
        # Get axis information for multidimensional array of images
        axes_dict = {axes[i]:i for i in range(len(axes))}
        try:
            channel_idx = axes_dict['C']
        except:
            raise ValueError("Error: No channel axis found.")
        try:
            z_idx = axes_dict['Z']
        except:
            raise ValueError("Error: No z-axis found.")
        
        # Iterate through channels, make directory for each, write each
        # z-stack to single image file. 
        for channel in range(image.shape[channel_idx]):
            channel_string = "Channel" + str(channel + 1)
            channel_path = path.join(base_dir, channel_string)
            # check if overwrite necessary/desired
            if (not path.exists(channel_path)):
                makedirs(channel_path)
            else:
                msg = "WARNING: {} already exists. Overwrite contents?"
                confirm = input(msg.format(channel_path))
                if confirm.lower() not in ['y', 'yes']:
                    sys.exit()
                shutil.rmtree(channel_path)
                makedirs(channel_path)

            # scale and write z-slices within a channel to distinct directories
            for z in range(image.shape[z_idx]):
                z_string = 'z' + z_to_string(z, image.shape[z_idx])
                file_name = base_name + 'c' + str(channel + 1) + z_string
                img_file = path.join(channel_path, file_name + '.png')
                # scale images to 0 - 255
                out_img = scale_bit_image(image[channel][z], nbits, 0, 0, 255)
                imsave(img_file, out_img.astype(int))

        # Write metadata to json file
        with open(path.join(base_dir, "metadata.json"), 'w') as out_file:
            json.dump(metadata, out_file, indent=2, sort_keys=True)


def z_to_string(value, max_value):
    """Convert an integer z value to a string that will order correctly."""
    max_str = str(max_value)
    val_str = str(value)
    char_dif = len(max_str) - len(val_str)
    out_str = val_str
    if (char_dif > 0):
        out_str = '0'*char_dif + val_str
    return(out_str)


def usage():
    msg = 'Parse an oif file to extract channel images and relevant metadata.\
    \n\nThis script takes a .json file as input with the following format:\n\n\
    {\n\
    "oif_file": <location to oif file>,\n\
    "stains": {"1": <stain used in first channel>,\n\
               "2": <stain used in second channel>,\n\
               "3": <stain used in third channel>,\n\
               "4": <stain used in fourth channel>},\n\
    "person": <name of person who collected the data>,\n\
    "hpf": <hours past fertilization>,\n\
    "treatment": <treatment applied to embryo>,\n\
    "out_dir": <desired location to write output directories>,\n\
    "prefix": <optinal string to write in front of output files>\n\
    }\n\nTo run the script, issue the following command:\n\
    \n\npython parse_oif.py <input_file.json>'
    print(msg)


def check_input_dict(input_data):
    expected_keys = ['oif_file', 'stains', 'person', 'hpf', 'treatment',
                     'out_dir', 'prefix']
    key_check = [x in expected_keys for x in input_data.keys()]
    if not all(key_check):
        usage()
    if input_data['out_dir'] is not None:
        if input_data['out_dir'] == '':
            input_data['out_dir'] = '.'
    if input_data['prefix'] is None:
        input_data['prefix'] = ''
    return input_data

if __name__ == "__main__":
    warnings.filterwarnings('ignore')
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    except getopt.GetoptError as err:
        print("Failure retrieving parameters.")
        usage()
        sys.exit(1)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)
    if len(args) == 1 and args[0].endswith('.json'):
        with open(args[0]) as infile:
            input_data = json.load(infile)
            if input_data['out_dir'] is not None:
                if input_data['out_dir'] == '':
                    input_data['out_dir'] = '.'
            # check json keys
            stain_keys = list(input_data['stains'].keys())
            stain_keys.sort()
            stains = [input_data['stains'][i] for i in stain_keys]
            oif_to_dir_tree(input_data['oif_file'], stains, input_data['person'],
                            input_data['hpf'], input_data['treatment'],
                            input_data['out_dir'], input_data['prefix'])
    else:
        usage()