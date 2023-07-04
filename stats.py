"""
This script reads results from the experiments and, for a matrix of instances and commits (versions),
saves the results in a csv file. The results are (time, lower_bound, upper_bound).

Informações que podem ser ser úteis:
- Solução da heurística (upper bound)
- Quantidade de branchs
- Solver:
    - Tempo total
    - Resultado
    - Quantidade de conjuntos no começo
    - Quantidade de conjuntos adicionados no total
    - Para cada iteração:
        - Tempo resolvendo a relaxação
        - Valor da relaxação
        - Tempo resolvendo a precificação
        - Quantidade de conjuntos adicionados

commit_exec.json:
{ instace_name: { time: float,
                  lower: float,
                  upper: float,
                  heuristics: { time: float, result: float },
                  branchs: { created: int, branched: int, contracts: int, conflicts: int },
                  solvers: [ { time: float,
                               result: float,
                               num_sets_start: int,
                               num_sets_added: int,
                               iterations: [ { relaxation_time: float,
                                               relaxation_result: float,
                                               pricing_time: float,
                                               num_sets_added: int, }
                                           ]
                             }
                           ]
                }
}
"""
import os
import sys
import json

heus = ["dsatur", "waves"]


def parse_heuristic(lines: list[str], i: int):
    heuristic = {"solution": 0, "time": 0, "type": ""}
    while i < len(lines):
        if " SOL: " in lines[i]:
            # get the solution in the form "SOL: %f ="
            heuristic["solution"] = float(lines[i].split(" SOL: ")[1].split(" =")[0])

        if " s: " in lines[i]:
            # get the time spent in the form "INFO | } 0.000 s: (dsatur|waves)"
            heuristic["time"] = float(lines[i].split(" s: ")[0].split(" ")[-1])
            heuristic["type"] = lines[i].split(" s: ")[1].strip("\n")

        # end of heuristics
        if "solver" in lines[i].lower():
            break

        i += 1

    # print(heuristic)
    return (i, heuristic)


def parse_iteration(lines: list[str], i: int):
    iteration = {
        "r_time": 0.0,
        "r_result": 0.0,
        "p_time": 0.0,
        "sets_added": 0,
    }
    while i < len(lines):
        if "Solved in " in lines[i]:
            # get the time spent in the form "Solved in %f with value %f"
            iteration["r_time"] = float(
                lines[i].split("Solved in ")[1].split(" with value ")[0]
            )
            iteration["r_result"] = float(
                lines[i].split("with value ")[1].split("\n")[0]
            )
        if " new sets." in lines[i]:
            # get the number of sets in the form "INFO | } 0.000 s: 0 new sets."
            iteration["sets_added"] = int(lines[i].split(" ")[-3])
        if " s: Pricing." in lines[i]:
            # get the time spent in the form "INFO | } 0.000 s: Pricing."
            iteration["p_time"] = float(lines[i].split(" s: ")[0].split(" ")[-1])
            i += 1
            break
        i += 1

    # print(iteration)
    return (i, iteration)


def parse_solver(lines: list[str], i: int):
    solver = {
        "type": "",
        "result": 0,
        "time": 0,
        "sets_start": 0,
        "sets_added": 0,
        "iter": [],
    }
    if "contract" in lines[i - 2]:
        solver["type"] = "contract"
    else:
        solver["type"] = "conflict"
    while i < len(lines):
        if "Initial model with" in lines[i]:
            # get the number of sets in the form "Initial model with %d sets"
            solver["sets_start"] = int(
                lines[i].split("Initial model with ")[1].split(" sets")[0]
            )
        if "Final model with" in lines[i]:
            # get the number of sets in the form "Final model with %d sets"
            solver["sets_added"] = (
                int(lines[i].split("Final model with ")[1].split(" sets")[0])
                - solver["sets_start"]
            )
        if " s: Solver." in lines[i]:
            # get the time spent in the form "INFO | } 0.000 s: Solver."
            solver["time"] = float(lines[i].split(" s: ")[0].split(" ")[-1])
        if "Solved with value " in lines[i]:
            # get the solution in the form "Solved with value %f"
            solver["result"] = float(lines[i].split("Solved with value ")[1])
            break
        if "Solved in " in lines[i]:
            # get the solution in the form "Solved in %f"
            i, iteration = parse_iteration(lines, i)
            solver["iter"].append(iteration)

        i += 1
    # print(solver)
    return (i, solver)


def parse_result(file_path: str):
    general = {
        "lower": 0.0,
        "upper": 0.0,
        "time": 0.0,
        "branchs": {},
        "heu": {},
        "solver": [],
    }
    branchs = {"created": 0, "branched": 0, "contracts": 0, "conflicts": 0, "time": 0.0}
    with open(file_path, "r") as file:
        # read all lines
        lines = file.readlines()
        i = 0
        while i < len(lines):
            # if any heus in lines[i]
            if any(heu in lines[i] for heu in heus):
                i, general["heu"] = parse_heuristic(lines, i)
                continue

            if "INFO| { Solver." in lines[i]:
                i, s = parse_solver(lines, i)
                general["solver"].append(s)
                continue

            if "INFO| Solved with value" in lines[i] and general["lower"] == 0.0:
                # get the lower bound in the form "INFO| Solved with value %f"
                general["lower"] = float(lines[i].split("INFO| Solved with value ")[1])

            # TODO upper bound

            if "Adding branch on " in lines[i]:
                branchs["created"] += 1

            if "Looking node " in lines[i]:
                branchs["branched"] += 1

            if "Doing contract" in lines[i]:
                branchs["contracts"] += 1

            if "Doing conflict" in lines[i]:
                branchs["conflicts"] += 1

            if " s: Branch::" in lines[i]:
                # get the time spent in the form "INFO | } 0.000 s: Branch::"
                branchs["time"] += float(lines[i].split(" s: ")[0].split(" ")[-1])

            if i == len(lines) - 1:
                # get the time spent in the form "(  2.350s)"
                general["time"] = float(lines[i].split("s) ")[0][1:])

            i += 1

    general["branchs"] = branchs
    return general


if __name__ == "__main__":
    comp = {}
    # for each file in the directory in argv[1]
    for file in os.listdir(sys.argv[1]):
        instance = file.split("_")[-1]
        comp[instance] = parse_result(sys.argv[1] + file)
    # transform into json
    json_result = json.dumps(comp, indent=4)
    print(json_result)
    # # print the result
    # print(result)
