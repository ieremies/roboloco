import argparse

parser = argparse.ArgumentParser(
    prog="RoboLOCo",
    description="Run experiments and generate reports",
    epilog="And thanks for all the fish",
)

parser.add_argument("repository", help="Git repository path (can be a remote URL).")
# Can have multiple commits
parser.add_argument(
    "-c",
    "--commit",
    help="Commit hash reference in the main branch. By default we will use the current HEAD.",
    nargs="*",
    default=["HEAD"],
)
parser.add_argument(
    "-b",
    "--binary",
    help="Binary to run. By default we will run all binaries in the PROJ_NAME/bin folder.",
    nargs="*",
    default=None,
)
parser.add_argument(
    "-i",
    "--instance",
    help="Instance(s) to run. By default we will run all instances in the PROJ_NAME/inst folder. If the argument is a number, we will run the instance with that number. If the argument is a range, we will run all instances in that range. If the argument is also a folder, we run all instances directly under it.",
    nargs="*",
    default=None,
)
parser.add_argument(
    "-o",
    "--output",
    help="Output folder. By default we will use the PROJ_NAME/logs folder.",
    default="logs",
)
