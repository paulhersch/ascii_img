from argparse import ArgumentParser
from ascii_img import main


if __name__ == "__main__":
    args = ArgumentParser(prog="ascii_img")
    args.add_argument(
        "image",
        help="The input image. Supports whatever opencv supports loading.",
        type=str,
    )
    args.add_argument(
        "actions",
        help="Actions to execute in order. Available actions are the capabilites"
        + "of the program, like colors, edges, ...",
    )
    args.add_argument(
        "--bg", help="Add ESC Sequence for black background", action="store_true"
    )
    args.add_argument(
        "-s",
        "--subtract-bg",
        help="Try to extract the foreground of the image before creating the ascii art",
        action="store_true",
    )
    args.add_argument(
        "-d",
        "--downscaling-factor",
        help="Factor by which the image should be downscaled, corresponds to the kernel size"
        + " for image filtering",
        dest="kernelsize",
        default=7,
        type=int,
    )
    args.add_argument(
        "-t",
        "--threshold-edges",
        help="'Edginess' value needed to detect as edge. Default is kernelsize^1.5 (i though this was a good value)",
        dest="edge_value",
        default=None,
        type=int,
    )
    args.add_argument(
        "-b",
        "--color-bins",
        type=int,
        help="Number of colorbins that are supposed to be found",
        default=8,
    )
    args.add_argument(
        "-e",
        "--edge-color",
        type=str,
        help="Color assigned to detected edges (if they should be visible the edge action should"
        + " be used AFTER colorizing), default=#000000",
        default="#000000",
    )
    args.add_argument(
        "--dont-adjust-to-font",
        action="store_true",
        help="Don't remove half the image height to adjust to usual terminal font sizing. Recommended"
        + " if you use a bitmap font that has the same height as width.",
    )
    main(args.parse_args())
