'''
Copyright (C) 2021 Tobias Himstedt


This file is part of Timeline.

Timeline is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Timeline is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
'''

from PIL import Image
import numpy


def exif_transpose(image):
    """
    If an image has an EXIF Orientation tag, return a new image that is
    transposed accordingly. Otherwise, return a copy of the image.

    :param image: The image to transpose.
    :return: An image.
    """
    exif = image.getexif()
    orientation = exif.get(0x0112)
    method = {
        2: Image.FLIP_LEFT_RIGHT,
        3: Image.ROTATE_180,
        4: Image.FLIP_TOP_BOTTOM,
        5: Image.TRANSPOSE,
        6: Image.ROTATE_270,
        7: Image.TRANSVERSE,
        8: Image.ROTATE_90,
    }.get(orientation)
    if method is not None:
        transposed_image = image.transpose(method)
        del exif[0x0112]
        try:
            transposed_image.info["exif"] = exif.tobytes()
        except:
            pass

        return transposed_image
    return image

def resize_width(image, new_height):
    height = image.size[1]
    new_width = new_height * image.width / height
    return new_width, new_height


def read_and_transpose_as_array(image_path):
    return numpy.asarray(read_and_transpose(image_path))


def read_and_transpose(image_path):
    image_data = Image.open(image_path)
    return exif_transpose(image_data)


def read_transpose_scale_image_as_array(image_path, dimension = None):
    image = read_and_transpose(image_path)
    factor = 1.0
    if image.size[0] > image.size[1]:
        max_dim = image.size[0]
    else:
        max_dim = image.size[1]
    if dimension and max_dim > dimension:
        factor = max_dim / dimension
        image.thumbnail((dimension, dimension))
    return numpy.asarray(image), factor
