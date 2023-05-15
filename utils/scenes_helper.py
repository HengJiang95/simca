import os
from scipy import io
from imageio import imread
import spectral
import pickle as pkl
import numpy as np
import matplotlib.image as mpimg

DATASETS_CONFIG = {
    "PaviaU": {
        "img": "PaviaU.mat",
        "gt": "PaviaU_gt.mat",
    },
    "IndianPines": {
        "img": "Indian_pines.mat",
        "gt": "Indian_pines_gt.mat",
    },
    "WashMall":{
        "img": "DC.tif",
        "gt": "GT.tif"
    },
}


def get_dataset(dataset_name, target_folder="./", datasets=DATASETS_CONFIG):
    """Gets the dataset specified by name and return the related components.
    Args:
        dataset_name: string with the name of the dataset
        target_folder (optional): folder to store the datasets, defaults to ./
        datasets (optional): dataset configuration dictionary, defaults to prebuilt one
    Returns:
        img: 3D hyperspectral image (WxHxB)
        gt: 2D int array of labels
        label_values: list of class names
        ignored_labels: list of int classes to ignore
        rgb_bands: int tuple that correspond to red, green and blue bands
        delta_lambda: auxiliary
    """
    palette = None
    ignored_labels = []
    label_values = {}
    rgb_bands = []
    delta_lambda = None

    if dataset_name not in datasets.keys():
        raise ValueError("{} dataset is unknown.".format(dataset_name))

    dataset = datasets[dataset_name]

    folder = target_folder + datasets[dataset_name].get("folder", dataset_name + "/")
    if dataset_name == "WashMall":
        # Load the image
        img = open_file(folder + "DC.tif")
        gt = open_file(folder + "GT.png")

        gt = gt + np.ones_like(gt)

        img = np.transpose(img, (1, 2, 0))
        label_values = ['Undefined', 'Roofs', 'Road', 'Grass', 'Trees', 'Trail', 'Water', 'Shadow']
        ignored_labels = [0]
        rgb_bands = (60, 27, 17)

        delta_lambda = 2505-401

    elif dataset_name == "dfc":
        # Load the image
        img = open_file(folder + dataset['img'])
        cropped_gt = open_file(folder + dataset['gt'])
        img = np.transpose(img, (1, 2, 0))
        gt = np.zeros((img.shape[0], img.shape[1]), dtype=np.int)
        gt[-cropped_gt.shape[0]:, 596:cropped_gt.shape[1]+596] = cropped_gt

        label_values = ['Unclassified', 'Healthy grass', 'Stressed grass', 'Artificial turf', 'Evergreen trees',
                        'Deciduous trees', 'Bare earth', 'Water', 'Residential buildings', 'Non-residential buildings',
                        'Roads', 'Sidewalks', 'Crosswalks', 'Major thoroughfares', 'Highways', 'Railways',
                        'Paved parking lots', 'Unpaved parking lots', 'Cars', 'Trains', 'Stadium seats']
        ignored_labels = [0]
        rgb_bands = (0, 25, 40)
        delta_lambda = 1050 - 380

    elif dataset_name == "PaviaU":
        # Load the image
        img = open_file(folder + "PaviaU.mat")["paviaU"]

        rgb_bands = (55, 41, 12)

        gt = open_file(folder + "PaviaU_gt.mat")["paviaU_gt"]

        label_values = [
            "Undefined",
            "Asphalt",
            "Meadows",
            "Gravel",
            "Trees",
            "Painted metal sheets",
            "Bare Soil",
            "Bitumen",
            "Self-Blocking Bricks",
            "Shadows",
        ]

        ignored_labels = [0]

        delta_lambda = 850 - 430

    elif dataset_name == "IndianPines":
        # Load the image
        img = open_file(folder + "Indian_pines_corrected.mat")
        img = img["indian_pines_corrected"]

        rgb_bands = (43, 21, 11)  # AVIRIS sensor

        gt = open_file(folder + "Indian_pines_gt.mat")["indian_pines_gt"]
        label_values = [
            "Undefined",
            "Alfalfa",
            "Corn-notill",
            "Corn-mintill",
            "Corn",
            "Grass-pasture",
            "Grass-trees",
            "Grass-pasture-mowed",
            "Hay-windrowed",
            "Oats",
            "Soybean-notill",
            "Soybean-mintill",
            "Soybean-clean",
            "Wheat",
            "Woods",
            "Buildings-Grass-Trees-Drives",
            "Stone-Steel-Towers",
        ]

        ignored_labels = [0]

        delta_lambda = 2500-400


    # No NaN accepted
    nan_mask = np.isnan(img.sum(axis=-1))
    assert np.count_nonzero(nan_mask) == 0

    img[nan_mask] = 0
    gt[nan_mask] = 0

    ignored_labels = list(set(ignored_labels))
    img = np.asarray(img, dtype="float32")
    return img, gt, label_values, ignored_labels, rgb_bands, palette, delta_lambda


def open_file(dataset):
    _, ext = os.path.splitext(dataset)
    ext = ext.lower()
    if ext == '.mat':
        # Load Matlab array
        return io.loadmat(dataset)
    elif ext == '.tif' or ext == '.tiff':
        # Load TIFF file
        return imread(dataset)
        # return np.array(mpimg.imread(dataset))
    elif ext == '.hdr':
        img = spectral.open_image(dataset)
        return img.load()
    elif ext == '.pkl':
        img = pkl.load(open(dataset, 'rb'))
        return img
    elif ext == '.png':
        # img = PIL.Image.open(dataset)
        img = mpimg.imread(dataset)
        return img
    else:
        raise ValueError("Unknown file format: {}".format(ext))