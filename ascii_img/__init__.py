import math
import numpy as np
import cv2
from typing import Dict, List
from enum import Enum


class CharacterIdx(Enum):
    EMPTY = -99
    ANGLE_0 = 0
    ANGLE_45 = 1
    ANGLE_90 = 2
    ANGLE_135 = 3
    BRIGHTNESS_0 = 4
    BRIGHTNESS_1 = 5
    BRIGHTNESS_2 = 6
    BRIGHTNESS_3 = 7
    BRIGHTNESS_4 = 8
    BRIGHTNESS_5 = 9
    BRIGHTNESS_6 = 10
    BRIGHTNESS_7 = 11
    BRIGHTNESS_8 = 12
    BRIGHTNESS_9 = 13


def split_img(img: np.ndarray, boxsize: int, proportion_thing: int) -> np.ndarray:
    shape = img.shape
    w = shape[1]
    h = shape[0]

    parts_w = math.floor(w / boxsize)
    parts_h = math.floor(h / boxsize)

    ret: np.ndarray = np.ndarray((parts_h, parts_w, boxsize, boxsize, 3))
    for i in range(parts_h):
        for j in range(parts_w):
            ret[i][j] = img[
                i * boxsize : (i + 1) * boxsize, j * boxsize : (j + 1) * boxsize, :
            ]

    # only use every second chunk in y range because terminal fonts are kind of 1:2

    return ret[range(0, ret.shape[0], proportion_thing), :, :]


def char_for_normalised_rad(angle: float) -> int:
    """
    Map normalized direction to character
    """
    """
    Acerolas Shader Code:

    if (any(sobel.g)) {
        if ((0.0f <= absTheta) && (absTheta < 0.05f)) direction = 0; // VERTICAL
        else if ((0.9f < absTheta) && (absTheta <= 1.0f)) direction = 0;
        else if ((0.45f < absTheta) && (absTheta < 0.55f)) direction = 1; // HORIZONTAL
        else if (0.05f < absTheta && absTheta < 0.45f) direction = sign(theta) > 0 ? 3 : 2; // DIAGONAL 1
        else if (0.55f < absTheta && absTheta < 0.9f) direction = sign(theta) > 0 ? 2 : 3; // DIAGONAL 2
    }
    """
    absangle = abs(angle)
    if absangle <= 0.1 or absangle > 0.9:
        return CharacterIdx.ANGLE_0.value
    elif absangle <= 0.6 and absangle > 0.4:
        return CharacterIdx.ANGLE_90.value
    elif absangle <= 0.4 and absangle > 0.1:
        return (
            CharacterIdx.ANGLE_45.value if angle > 0 else CharacterIdx.ANGLE_135.value
        )
    return CharacterIdx.ANGLE_135.value if angle > 0 else CharacterIdx.ANGLE_45.value


def edge_char_map(
    # chunks: np.ndarray,
    grayscale: np.ndarray,
    kernelsize: int,
    threshold: float,
    edge_color_hex: str,
    # edge_chars: str,
) -> np.ndarray:
    """
    takes in chunks created with the split_img function
    and outputs a similar shaped ndarray with the character
    representing each edge/corner.
    """

    # translate hex to rgb uint8 triplet
    edge_color = [
        int(edge_color_hex[1:3], 16),
        int(edge_color_hex[3:5], 16),
        int(edge_color_hex[5:7], 16),
    ]

    """
    Sobel Filter analogous to the method showcased in Acerola Video
    (yes half of this is based on the video)
    """
    kernel_half: int = math.floor(kernelsize / 2)

    # create the sobel filter
    G_x: np.ndarray = np.array(
        [
            [
                (j / (i * i + j * j)) if i != 0 or j != 0 else 0
                for j in range(-kernel_half, kernel_half + 1)
            ]
            for i in range(-kernel_half, kernel_half + 1)
        ]
    )
    G_y = G_x.T

    angles: np.ndarray = np.ndarray((grayscale.shape[:2]) + (2,))
    for i in range(grayscale.shape[0]):
        for j in range(grayscale.shape[1]):
            # But Acerola,
            gx = np.sum(grayscale[i, j, :, :] * G_x)
            gy = np.sum(grayscale[i, j, :, :] * G_y)
            angles[i, j] = [math.atan2(gy, gx), math.sqrt(gx**2 + gy**2)]

    character_map = np.array(
        [
            [
                (
                    [char_for_normalised_rad(angles[i, j, 0] / math.pi)] + edge_color
                    if angles[i, j, 1] > threshold
                    else [CharacterIdx.EMPTY.value] + edge_color
                )
                for j in range(angles.shape[1])
            ]
            for i in range(angles.shape[0])
        ]
    )

    return character_map


def color(
    chunks: np.ndarray,
) -> np.ndarray:

    return np.array(
        [
            [
                # average over color channels
                # colors are BGR because opencv
                [CharacterIdx.EMPTY.value]
                + [int(np.average(chunks[i, j, :, :, k])) for k in range(2, -1, -1)]
                for j in range(chunks.shape[1])
            ]
            for i in range(chunks.shape[0])
        ]
    )


def color_bin(chunks: np.ndarray, cluster_count: int) -> np.ndarray:

    colors: np.ndarray = np.float32(
        np.array(
            [
                [
                    [int(np.average(chunks[i, j, :, :, k])) for k in range(2, -1, -1)]
                    for j in range(chunks.shape[1])
                ]
                for i in range(chunks.shape[0])
            ]
        ).reshape(-1, 3)
    )

    _, label, center = cv2.kmeans(
        colors,
        cluster_count,
        None,
        (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0),
        10,
        cv2.KMEANS_RANDOM_CENTERS,
    )
    colorcodes = np.uint8(center)
    return np.reshape(
        np.array(
            [
                np.insert(code, 0, CharacterIdx.EMPTY.value)
                for code in colorcodes[label.flatten()]
            ]
        ),
        (chunks.shape[0], chunks.shape[1], 4),
    )


def character_selection(brightness: np.ndarray) -> np.ndarray:
    return np.array(
        [
            [
                [
                    round((np.average(brightness[i, j])) / 28)
                    + CharacterIdx.BRIGHTNESS_0.value,
                    0,
                    0,
                    0,
                ]
                for j in range(brightness.shape[1])
            ]
            for i in range(brightness.shape[0])
        ]
    )


def set_fg(clist: List[int]) -> str:
    return f"\033[38;2;{clist[0]};{clist[1]};{clist[2]}m"


def set_bg(clist: List[int]) -> str:
    return f"\033[48;2;{clist[0]};{clist[1]};{clist[2]}m"


def main(args) -> None:
    img = cv2.imread(args.image, flags=cv2.IMREAD_COLOR)

    if args.subtract_bg:
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresholding_segment = cv2.threshold(
            gray_img, 0.0, 255.0, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )[1]
        # TODO: epxand with proper watershed
        img = img * (thresholding_segment == 0)[:, :, None]

    chunks = split_img(img, args.kernelsize, 1 if args.dont_adjust_to_font else 2)
    brightness: np.ndarray = np.average(chunks, -1)  # average of rgb -> monochrome

    if args.edge_value is None:
        args.edge_value = args.kernelsize**2

    color_and_char_map: np.ndarray = np.zeros(
        (chunks.shape[0], chunks.shape[1], 4), np.int8
    ) + [CharacterIdx.EMPTY.value, 0, 0, 0]

    for a in args.actions.split(","):
        match a:
            case "edge":
                edge_run = edge_char_map(
                    brightness, args.kernelsize, args.edge_value, args.edge_color
                )
                # apply edge chars only
                for i in range(color_and_char_map.shape[0]):
                    for j in range(color_and_char_map.shape[1]):
                        if edge_run[i, j, 0] != CharacterIdx.EMPTY.value:
                            color_and_char_map[i, j] = edge_run[i, j]

            case "brightness":
                brightness_run = character_selection(brightness)
                for i in range(color_and_char_map.shape[0]):
                    for j in range(color_and_char_map.shape[1]):
                        color_and_char_map[i, j, 0] = brightness_run[i, j, 0]

            case "color":
                color_run = color(chunks)
                for i in range(color_and_char_map.shape[0]):
                    for j in range(color_and_char_map.shape[1]):
                        color_and_char_map[i, j, 1] = color_run[i, j, 1]
                        color_and_char_map[i, j, 2] = color_run[i, j, 2]
                        color_and_char_map[i, j, 3] = color_run[i, j, 3]
            case "color_bin":
                color_run = color_bin(chunks, args.color_bins)
                for i in range(color_and_char_map.shape[0]):
                    for j in range(color_and_char_map.shape[1]):
                        color_and_char_map[i, j, 1] = color_run[i, j, 1]
                        color_and_char_map[i, j, 2] = color_run[i, j, 2]
                        color_and_char_map[i, j, 3] = color_run[i, j, 3]
            case _:
                print(f"Method {a} not implemented!")

    if args.bg:
        print(set_bg([0, 0, 0]))

    # translate numbers to characters
    character_map = {
        CharacterIdx.EMPTY.value: " ",
        CharacterIdx.ANGLE_0.value: "|",
        CharacterIdx.ANGLE_45.value: "/",
        CharacterIdx.ANGLE_90.value: "-",
        CharacterIdx.ANGLE_135.value: "\\",
        CharacterIdx.BRIGHTNESS_0.value: " ",
        CharacterIdx.BRIGHTNESS_1.value: ".",
        CharacterIdx.BRIGHTNESS_2.value: ";",
        CharacterIdx.BRIGHTNESS_3.value: "c",
        CharacterIdx.BRIGHTNESS_4.value: "o",
        CharacterIdx.BRIGHTNESS_5.value: "P",
        CharacterIdx.BRIGHTNESS_6.value: "O",
        CharacterIdx.BRIGHTNESS_7.value: "?",
        CharacterIdx.BRIGHTNESS_8.value: "@",
        CharacterIdx.BRIGHTNESS_9.value: "#",
    }

    ascii_art = np.array(
        [
            [
                set_fg(color_and_char_map[i, j, 1:4])
                + character_map[color_and_char_map[i, j, 0]]
                for j in range(chunks.shape[1])
            ]
            for i in range(chunks.shape[0])
        ]
    )
    for i, e in enumerate(ascii_art):
        print("".join(e))
