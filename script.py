"""
Objetivo desse script é receber um projeto de pesquisa operacional e
realizar os experimentos necessários, recuperar estatísticas e gerar
um relatório com os dados.

Gostaríamos que o script seja capaz de indentificar quais experimentos
já foram realizados e quais ainda precisam ser realizados, recuperando
em caso de falhas.
"""
import argparse
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import product
from tqdm import tqdm

# Varibles that will be set by the parser
repo_path = "proj_path"
proj_name = "proj_name"
commit_list = "HEAD"
command = "command"
log_path = "./logs"

# Command line parser
# python script.py https://github.com/ieremies/mest-code "[exe:bin] [file:inst]" -c HEAD,HEAD~1
# TODO python script.py gh:ieremies/mest-code
parser = argparse.ArgumentParser(
    prog="RoboLOCo",
    description="Run experiments and generate reports",
    epilog="And thanks for all the fish",
)
parser.add_argument("repository", help="Git repository path (can be a remote URL).")
parser.add_argument(
    "command", help="Command used to run experiments (see readme for syntax)."
)
parser.add_argument(
    "-c",
    "--commit",
    help="Must be a list of commits hashs separeted by commas.",
    nargs=1,
    default=["HEAD"],
)


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
    if repo_path.startswith("http"):
        if not os.path.exists(f"./{proj_name}"):
            os.system(f"git clone {repo_path} {proj_name}")
        repo_path = proj_name  # new path
    else:
        # otherwise, just pull the latest changes
        os.system(f"git -C {repo_path} pull")


def clean_commit_list():
    """
    Replaces any HEAD reference in the commit list with the actual commit.
    """
    global commit_list
    if "HEAD" in commit_list:
        commit_list.remove("HEAD")
        commit_list.append(
            os.popen(f"git -C {repo_path} rev-parse --short HEAD").read().strip()
        )


def checkout_and_make(commit):
    global repo_path
    os.system(f"git -C {repo_path} checkout {commit}")
    os.system(f"make -C {repo_path}")


def run_experiments(commit, binary, instance):
    global log_path
    # Create log file name
    log = f"{log_path}/{commit}_{binary.split('/')[-1]}"
    log += f"_{instance.split('/')[-1]}.log" if instance else ".log"
    # if the log exists, skip
    if os.path.exists(log):
        return

    cmd = f"{binary}"
    cmd += f" {instance}" if instance else ""
    cmd += f" &> {log}"

    # TODO dont use pipe, capture stderr and stdout them save to file
    # in case of sudden loss of power, we won't think we have the results
    os.system(cmd)


def find_exec(path):
    global repo_path
    print(path)
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
    return os.popen(f"find {repo_path}/{path} -type f").read().strip().split("\n")


def run_for_commit(commit):
    global bin_path, inst_path

    params = []
    for c in command:
        if c[0] == "[":
            c = c.split(":")
            if "[exe" in c[0]:
                # [:-1] to remove the last char, which is ']'
                params.append(find_exec(c[-1][:-1]))
            if "[file" in c[0]:
                params.append(find_files(c[-1][:-1]))
            # TODO range param
        else:
            params.append([c])

    total_tasks = 1
    for p in params:
        total_tasks *= len(p)

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(run_experiments, commit, *p) for p in product(*params)
        ]

        with tqdm(total=total_tasks) as pbar:
            for future in as_completed(futures):
                pbar.update()


def run():
    clone_repository()
    clean_commit_list()

    # Ensures logs folder exists
    if not os.path.exists(log_path):
        os.mkdir(log_path)

    for commit in commit_list:
        checkout_and_make(commit)
        run_for_commit(commit)


if __name__ == "__main__":
    args = parser.parse_args(sys.argv[1:])
    print(args)
    repo_path = args.repository
    command = args.command.split()
    commit_list = args.commit
    run()
