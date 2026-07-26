import numpy as np


def create_blob(image: np.ndarray) -> np.ndarray:
    # Swap BGR to RGB
    image = image[:, :, ::-1]
    # Convert to float
    image = image.astype("float32")
    #  Normalizing
    image = image * (1 / 255)
    # HWC -> CHW
    chw = image.transpose(2, 0, 1)
    # Add N-Dimension
    blob = np.expand_dims(chw, axis=0)

    return blob