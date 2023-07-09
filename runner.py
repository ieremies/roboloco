import argparse
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import product
from tqdm import tqdm
from configparser import ConfigParser
import subprocess
import shlex

# Varibles that will be set by the parser or config
repo_path = "proj_path"
proj_name = "proj_name"
commit_list = "HEAD"
command = "command"
log_path = "./logs"
single = False
make_command = "make"
git = True
dry_run = False
time_limit = 60 * 5


def expand_links(link: str) -> str:
    l = link.split(":")
    if len(l) < 0 or l[0].startswith("http"):
        return link
    if "h" in l[0]:
        l[0] = "https://github.com/"
    elif "l" in l[0]:
        l[0] = "https://gitlab.com/"
    elif "c" in l[0]:
        l[0] = "https://gitlab.ic.unicamp.br/"
    return "".join(l)


def clone_repository():
    """
    Ensures we have acess to the repository, either by clonning or checking
    if it already exists.
    """
    global repo_path, proj_name

    # parse the proj_name from a url like "https://github.com/user/proj_name.git"
    # or a local path like "/home/user/proj_name"
    proj_name = repo_path.split("/")[-1].split(".")[0]

    # if the repository is a remote url
    if ":" in repo_path:
        if not os.path.exists(f"./{proj_name}"):
            os.system(f"git clone {expand_links(repo_path)} {proj_name}")
        repo_path = proj_name  # new path
    os.system(f"git -C {repo_path} pull")


def clean_commit_list():
    """
    Resolves any reference to commits like HEAD or HEAD~4
    """
    global commit_list
    for i in range(len(commit_list)):
        commit_list[i] = (
            os.popen(f"git -C {repo_path} rev-parse --short HEAD").read().strip()
        )


def checkout_and_make(commit):
    global repo_path
    if git:
        os.system(f"git -C {repo_path} checkout {commit}")
    # if Makefile exists inside repo_path
    if os.path.exists(f"{repo_path}/Makefile"):
        os.system(f"make -C {repo_path}")


def run_experiments(commit, *args):
    global log_path
    # Create log file name

    log = f"{log_path}/{commit}"
    for arg in args:
        log += f"_{arg.split('/')[-1]}"
    log += ".log"
    # if the log exists, skip
    if os.path.exists(log):
        return

    cmd = " ".join(args)
    # cmd += f" &> {log}"

    # TODO pipe
    if dry_run:
        print(cmd)
        return
    try:
        cmd_args = shlex.split(cmd)

        with open(log, "w") as file:
            # Run the command with stderr redirected to the file
            # print(cmd_args)
            subprocess.run(cmd_args, timeout=time_limit, stderr=file, text=True)

    except subprocess.TimeoutExpired:
        pass
    except subprocess.CalledProcessError as e:
        pass


def find_exec(path):
    global repo_path
    if not os.path.exists(f"{repo_path}/{path}"):
        return path.split(",")
    return (
        os.popen(f"find {repo_path}/{path} -executable -type f")
        .read()
        .strip()
        .split("\n")
    )


def find_files(path):
    global repo_path
    if not os.path.exists(f"{repo_path}/{path}"):
        return path.split(",")
    # we now run instance in order of size
    return [
        file.split()[-1]
        for file in os.popen(f"find {repo_path}/{path} -type f -ls | sort -n -k7")
        .read()
        .strip()
        .split("\n")
    ]
    # return os.popen(f"find {repo_path}/{path} -type f").read().strip().split("\n")


def run_for_commit(commit):
    global bin_path, inst_path, single

    params = []
    for c in command:
        if c[0] != "[":
            params.append(c.split(","))
            continue
        c = c[1:-1].split(":")
        if len(c) < 2:
            print(c)
            params.append(c[0].split(","))
            continue
        if "exe" in c[0]:
            params.append(find_exec(c[-1]))
        elif "file" in c[0]:
            params.append(find_files(c[-1]))

    total_tasks = 1
    for p in params:
        total_tasks *= len(p)

    # If single, run in a single thread
    max_workers = 1 if single else os.cpu_count()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(run_experiments, commit, *p) for p in product(*params)
        ]

        with tqdm(total=total_tasks) as pbar:
            for _ in as_completed(futures):
                pbar.update()


def run():
    clean_commit_list()

    # Ensures logs folder exists
    if not os.path.exists(log_path):
        os.mkdir(log_path)

    if git:
        for commit in commit_list:
            checkout_and_make(commit)
            run_for_commit(commit)
    else:
        checkout_and_make("local")
        run_for_commit("local")


# Command line parser
parser = argparse.ArgumentParser(
    prog="RoboLOCo",
    description=(
        "This is a simple script to run operational research experiments."
        "It tries to abstract much of the struct of the code it self, allowing to quickly run"
        "a bunch of combinations of instances and parameters and save its logs"
    ),
    epilog="And thanks for all the fish",
)
parser.add_argument("repository", help="Git repository path (can be a remote URL).")
parser.add_argument(
    "command",
    help="Command used to run experiments (see readme for syntax).",
    default=None,
    nargs="?",
)
parser.add_argument(
    "-c",
    "--commit",
    help="Must be a list of commits hashs separeted by commas.",
    nargs=1,
    default=None,
)
parser.add_argument(
    "--single",
    help="Run experiments in a single thread.",
    action="store_true",
)
parser.add_argument(
    "-m", "--make-comand", help="Command used to make the project.", default="make"
)
parser.add_argument(
    "--no-git",
    help="Do not use git to checkout commits.",
    action="store_true",
)
parser.add_argument(
    "--dry-run",
    help="Do not run the experiments, just print the commands.",
    action="store_true",
)
parser.add_argument(
    "-tl",
    "--time-limit",
    help="Time limit for each instance (in seconds)",
    default=60*5, # 5 minutes
)

if __name__ == "__main__":
    args = parser.parse_args(sys.argv[1:])
    repo_path = args.repository
    clone_repository()

    # Read the config file, if present, in the project
    config = None
    if os.path.isfile(f"{repo_path}/roboloco.conf"):
        config = ConfigParser()
        config.read(f"{repo_path}/roboloco.conf")
    if os.path.isfile(f"{repo_path}/.roboloco.conf"):
        config = ConfigParser()
        config.read(f"{repo_path}/.roboloco.conf")

    if args.command is not None:
        command = args.command.split()
    elif config is not None:
        command = config["DEFAULT"]["command_string"].split()

    if args.commit is not None:
        commit_list = args.commit[0].split(",")
    elif config is not None and "commit" in config["DEFAULT"]:
        commit_list = config["DEFAULT"]["commit"].split(",")
    else:
        commit_list = ["HEAD"]

    if args.single is not None:
        single = bool(args.single)
    elif config is not None and "single" in config["DEFAULT"]:
        single = bool(config["DEFAULT"]["single"])
    else:
        single = False

    if args.make_comand is not None:
        make_command = args.make_comand
    elif config is not None and "make_command" in config["DEFAULT"]:
        make_command = config["DEFAULT"]["make_command"]
    else:
        make_command = "make"

    if args.no_git is not None:
        git = not bool(args.no_git)

    if args.dry_run is not None:
        dry_run = bool(args.dry_run)

    time_limit = int(args.time_limit)

    run()
