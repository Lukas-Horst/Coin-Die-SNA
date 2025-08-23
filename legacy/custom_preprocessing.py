import cv2 as cv
import numpy as np
import os


def preprocess_image(image_path):
    """This function uses the bibliothek OpenCV to preprocess pictures of coins. In order to do so various
    of its featzres were applied e.g. making pictures black and white, bringing them to the same size,
    removing the background etc. In the end this type or preprocessing proofed not to be efficient enough
    in order to reliable classify the images of coins by die. But since one of our examples for clustering the coins
    also contains a dataset prepared with this function we decided to include it

    Path to the OpenCV wiki: https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html
    """

    image = cv.imread(image_path)

    # convert to grayscale
    gray_image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

    data_name = os.path.basename(image_path)

    # normalize grayscale
    norm_gray = cv.normalize(gray_image, None, 0, 255, cv.NORM_MINMAX)

    # apply gaussian blur
    blurred = cv.GaussianBlur(norm_gray, (7, 7), 0)

    # detect edges
    edges = cv.Canny(blurred, 30, 100)

    # find small gaps in edges
    kernel = np.ones((3, 3), np.uint8)
    edges_closed = cv.morphologyEx(edges, cv.MORPH_CLOSE, kernel)

    # find contours
    contours, _ = cv.findContours(edges_closed, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    contour = max(contours, key=cv.contourArea)

    # compute convex hull
    hull = cv.convexHull(contour)

    # find smallest circle enclosed by contour
    (x, y), radius = cv.minEnclosingCircle(contour)

    # create mask and extract coin from image
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    cv.drawContours(mask, [hull], -1, 255, thickness=-1)
    result = cv.bitwise_and(image, image, mask=mask)
    target_size = 255

    # resize and center coin
    resized = cv.resize(result, (target_size, target_size))
    canvas = np.zeros((512, 512, 3), dtype=np.uint8)
    offset = (512 - target_size) // 2

    canvas[offset: offset + target_size, offset: offset + target_size] = resized

    target_path = os.path.join("target1", data_name)

    gray_canvas = cv.cvtColor(canvas, cv.COLOR_BGR2GRAY)
    gray_canvas = cv.normalize(gray_canvas, None, 0, 255, cv.NORM_MINMAX)

    # adjust brightness
    mean_val = np.mean(gray_canvas)
    target_brightness = 128
    adjustment = target_brightness - mean_val
    gray_canvas = np.clip(gray_canvas + adjustment, 0, 255).astype(np.uint8)

    cv.imwrite(target_path, gray_canvas)


def main():
    """Main function. In order to run the preprocessing function just replace the variable 'source'
    with the path to the directory that contains the pictures of your coins. After that you can run the
    function by just running this Python file. ATTENTION: This part of the code is not part of the SNA-Analysis
    and visualisation of our results"""
    source = ""  # Change it so that it contains the path to the pictures you want to preprocess

    for entry in os.listdir(source):
        picture_path = os.path.join(source, entry)
        preprocess_image(picture_path)


if __name__ == "__main__":
    main()
