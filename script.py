"""
Objetivo desse script é receber um projeto de pesquisa operacional e
realizar os experimentos necessários, recuperar estatísticas e gerar
um relatório com os dados.

Gostaríamos que o script seja capaz de indentificar quais experimentos
já foram realizados e quais ainda precisam ser realizados, recuperando
em caso de falhas.
"""
from parser import parser
import sys
import os


class RoboLOCo:
    # List of varibles that need to be defined
    def __init__(self, repo_path, commit, binary, instance, output):
        self.repo_path = repo_path
        self.proj_name = repo_path.split("/")[-1]
        self.commit = commit
        self.binary = binary
        self.instance = instance
        self.log_path = output
        # check if logs folder exists
        if not os.path.exists(self.log_path):
            os.mkdir(self.log_path)

    def clone_repository(self):
        # if the repository is a remote url and not cloned
        if this.repo_path.startswith("http") and not os.path.exists(this.repo_path):
            os.system(f"git clone {this.repo_path} {this.proj_name}")
            this.repo_path = this.proj_name  # new path
        else:
            # otherwise, just pull the latest changes
            os.system(f"git -C {this.repo_path} pull")

    def run_experiments(self, commit):
        for binary in os.listdir(f"{this.repo_path}/bin"):
            for instance in os.listdir(f"{this.repo_path}/inst"):
                log = f"logs/{commit}_{binary}_{instance}.log"
                # if the log exists, skip
                if os.path.exists(log):
                    continue
                # run the binary with the instance
                os.system(
                    f"{this.repo_path}/bin/{binary} {this.repo_path}/inst/{instance} > {log}"
                )

    def run_for_commit(self, commit):
        # if commit is "HEAD" get the right checksum for it
        if commit == "HEAD":
            commit = (
                os.popen(f"git -C {this.repo_path} rev-parse --short HEAD")
                .read()
                .strip()
            )
        # checkout the commit
        os.system(f"git -C {this.repo_path} checkout {commit}")
        # run the experiments
        os.system(f"make -C {this.repo_path}")
        this.run_experiments(commit)

    def run(self):
        this.clone_repository()
        for commit in this.commit:
            this.run_for_commit(commit)


if __name__ == "__main__":
    args = parser.parse_args(sys.argv[1:])
    this = RoboLOCo(
        repo_path=args.repository,
        commit=args.commit,
        binary=args.binary,
        instance=args.instance,
        output=args.output,
    )
    this.run()
