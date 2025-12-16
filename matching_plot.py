"""
Apache-2.0 license
https://www.apache.org/licenses/LICENSE-2.0

Copyright 2024 VeRLab

MODIFIED for use in Coin Die SNA
"""

import cv2
import numpy as np
from io import BytesIO
import torch
from skimage import io
from timeit import default_timer as timer

from config.config_manager import ConfigManager

config_manager = ConfigManager('Coin-Die-SNA-Interface/config/config.json')
config = config_manager.config


def warp_corners_and_draw_matches(ref_points, dst_points, img1, img2):
    # Calculate the Homography matrix
    H, mask = cv2.findHomography(ref_points, dst_points, method=cv2.USAC_MAGSAC, ransacReprojThreshold=8)
    score = mask.sum()
    mask = mask.flatten()

    # Get corners of the first image (image1)
    h, w = img1.shape[:2]
    corners_img1 = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=np.float32).reshape(-1, 1, 2)

    # Warp corners to the second image (image2) space
    warped_corners = cv2.perspectiveTransform(corners_img1, H)

    # Draw the warped corners in image2
    img2_with_corners = img2.copy()
    for i in range(len(warped_corners)):
        start_point = tuple(warped_corners[i - 1][0].astype(int))
        end_point = tuple(warped_corners[i][0].astype(int))
        # Using solid green for corners
        cv2.line(img2_with_corners, start_point, end_point, (0, 255, 0), 4)

    # Prepare keypoints and matches for drawMatches function
    keypoints1 = [cv2.KeyPoint(p[0], p[1], 5) for p in ref_points]
    keypoints2 = [cv2.KeyPoint(p[0], p[1], 5) for p in dst_points]
    matches = [cv2.DMatch(i, i, 0) for i in range(len(mask)) if mask[i]]

    # Draw inlier matches
    img_matches = cv2.drawMatches(img1, keypoints1, img2_with_corners, keypoints2, matches,
                                  None, matchColor=(0, 255, 0), flags=2)

    cv2.putText(img_matches, str(score), (w - 25, 50), cv2.FONT_HERSHEY_DUPLEX, 1.5,
                (237, 114, 50), 2)

    return img_matches


def matches_two_files(i1, i2, im1, im2):
    filtering = config_manager.get_pipeline_config("auto_die_studies")["parameters"]["filtering"]
    matches_list = xfeat.match_xfeat_star_from_cache(i1, i2)

    mkpts_0, mkpts_1 = matches_list[0], matches_list[1]
    canvas = warp_corners_and_draw_matches(mkpts_0, mkpts_1, im1, im2)
    _, buffer = cv2.imencode(".jpg", canvas)
    bytes_buffer = BytesIO(buffer.tobytes())
    bytes_buffer.seek(0)

    if not filtering:
        return len(matches_list[0]), bytes_buffer

    _, mask = cv2.findHomography(
        matches_list[0],
        matches_list[1],
        method=cv2.USAC_MAGSAC,
        ransacReprojThreshold=8,
    )
    return mask.sum(), bytes_buffer


def get_matches_plot(image_files):
    start = timer()
    top_k = config_manager.get_pipeline_config("auto_die_studies")["parameters"]["matching_params"]["XFeat-TopK"]

    IMAGES = [io.imread(im) for im in image_files]
    im_list = []

    for im in IMAGES:
        if len(im.shape) == 3:
            im_list.append(torch.tensor(im.transpose(2, 0, 1)))
        else:
            im_list.append(torch.tensor(im[None, :, :]))
    xfeat = XFeat(top_k=top_k)
    xfeat.cache_feats(im_list)

    im1 = cv2.imread(image_files[0])
    im2 = cv2.imread(image_files[1])
    num_matches, img_matches = matches_two_files(0, 1, im1, im2)

    end = timer()
    print(end - start, "s")
    print(num_matches)

    return num_matches, img_matches
