import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import h5py

def planck(wavelength, T):
    """
    Returns the spectral radiance of a black body at temperature T.

    Args:
    wavelength (float): Wavelength in meters
    T (float): Temperature in Kelvin

    Returns:
    (float): Spectral radiance in Watts per square meter per steradian per meter
    """
    h = 6.62607004e-34  # Planck constant (in m^2 kg / s)
    c = 299792458  # Speed of light (in m/s)
    k = 1.38064852e-23  # Boltzmann constant (in m^2 kg / s^2 K)

    a = 2.0 * h * c ** 2
    b = h * c / (wavelength * k * T)
    spectral_radiance = a / ((wavelength ** 5) * (np.exp(b) - 1.0))

    return spectral_radiance

def generate_letter_shape(text="A",size=(100,100)):
    # Create a blank image
    image = Image.new('L', size, color=0)  # 'L' mode for 8-bit pixels, black and white

    # Get a drawing context
    draw = ImageDraw.Draw(image)
    factor = size[0]/100
    # Choose a font (this will depend on what you have installed on your system)
    font = ImageFont.truetype("arialbd.ttf", 110*int(factor))  # Adjust path and size as needed
    text_width, text_height = draw.textsize(text, font=font)
    position = ((size[0] - text_width) / 2 , (size[1] - text_height) / 2 - 10*factor )
    # Draw the text
    draw.text(position, text, fill=1, font=font)
    # Convert to numpy array
    letter = np.array(image)

    return  letter

# loading spectrum and corresponding wavelengths
fluo_spectrum = np.load("./fluo_intensity_val.npy")
wavelengths = np.load("./wavelengths.npy")


sun_spectrum = planck(wavelengths * 1e-9, 5778)
sun_spectrum = sun_spectrum * ( 0.1/ np.max(sun_spectrum))

letter = generate_letter_shape(text="F",size=(201,201))

plt.imshow(letter)
plt.show()

# Initialize 3D array
spectrum_image = np.zeros((letter.shape[0], letter.shape[1], len(wavelengths)))

# Fill in spectrum values based on mask
for i in range(letter.shape[0]):
    for j in range(letter.shape[1]):
        if letter[i, j] == 0:
            # spectrum_image[i, j, :] = np.zeros(len(wavelengths))
            spectrum_image[i,j,:] = sun_spectrum
        else:
            spectrum_image[i, j, :] = fluo_spectrum

file = h5py.File("F_fluocompact.h5", "w")

# Create datasets for your arrays
file.create_dataset("scene", data=spectrum_image)
file.create_dataset("wavelengths", data=wavelengths)
file.create_dataset("gt", data=letter)
# Close the file
file.close()

# save the resultin
# spectrum_image - 3D cube
# corresponding wavelengths - 1D array
# corresponding mask - 2D array of 0 and 1

#

# fig, ax = plt.subplots()
#
# ax.plot(wavelengths, fluo_spectrum)
# ax.plot(wavelengths, sun_spectrum)
#
# ax.set_xlabel(r'$\lambda$ [nm]', fontsize=12)
# ax.set_ylabel(r'intensity value [no units]', fontsize=12)
# plt.legend(["fluocompact spectrum","sun spectrum"])
# # plt.xlim((400, 650))
# plt.show()







