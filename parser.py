import argparse

parser = argparse.ArgumentParser(
    prog="RoboLOCo",
    description="Run experiments and generate reports",
    epilog="And thanks for all the fish",
)

parser.add_argument("repository", help="Git repository path (can be a remote URL).")
parser.add_argument(
    "-c",
    "--commit",
    help="Must be a list of commits hashs separeted by commas.",
    nargs=1,
    default="HEAD",
)
parser.add_argument(
    "-b",
    "--binary",
    help=(
        "Must be either the name of the folder (string) inside PROJ_NAME with the binaries "
        "(all executables inside will be run). "
        "It can also be a list of executables given by its relative path to the project path."
    ),
    nargs="*",
    default=None,
)
parser.add_argument(
    "-i",
    "--instance",
    help=(
        "Must be either a (string) path relative (to project) to a folder, "
        "all instances inside it will be used as the first argument to all binary. "
        "It can also be a list of instances given by its relative path to the project path. "
        "Lastly, it can be False, in which case we will not use  any instance. "
        "By default we will use all instances in the PROJ_NAME/inst folder."
    ),
    nargs="*",
    default="inst",
)
parser.add_argument(
    "-o",
    "--output",
    help="Output folder. This will be used to redirect the stdout and stderr of your experiments.",
    default="logs",
)
