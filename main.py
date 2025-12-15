import os
import sys

SUBMODULE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Coin-Die-SNA-Interface")
if SUBMODULE_PATH not in sys.path:
    sys.path.insert(0, SUBMODULE_PATH)

from cluster_to_graph import construct_graph_both_sides, construct_graph
from NetworkX_SNA import shorten_edges, create_graph, network_analysis, get_subgraphs, export_graph
from config.config_manager import ConfigManager


def social_network_analysis_pipeline(filterTime="X", filterAvRv=""):
    config_manager = ConfigManager('Coin-Die-SNA-Interface/config/config.json')

    folder = filterTime + "_" + filterAvRv
    print(10 * "=", "[" + folder + "] Starting SNA Pipeline", 10 * "=")

    # Graph Construction
    if filterAvRv == "":
        nodes, edges = construct_graph_both_sides(config_manager.get_current_analysis_file(),
                                                  config_manager.get_current_analysis_file('a'))
    elif filterAvRv == "a":
        nodes, edges = construct_graph(config_manager.get_current_analysis_file('a'), "a")
    elif filterAvRv == "r":
        nodes, edges = construct_graph(config_manager.get_current_analysis_file(), "r")
    print("[" + folder + "] Graph construction done")

    # Social Network Analysis
    short_edges = shorten_edges(edges)
    NetworkX_Graph = create_graph(short_edges, nodes, True, [] if filterTime == "X" else [filterTime])
    network_analysis(NetworkX_Graph, folder)
    get_subgraphs(NetworkX_Graph, folder)
    print("[" + folder + "] SNA done")

    # Export
    export_graph(NetworkX_Graph, folder)
    print("[" + folder + "] Export done")

    print(10 * "=", "[" + folder + "] Finished SNA Pipeline", 10 * "=")


if __name__ == "__main__":
    # social_network_analysis_pipeline()

    for filterAvRv in ["", "r", "a"]:
        for filterTime in ["X", "A", "B", "C", "D", "E", "F", "G", "H", "P", "U"]:
            try:
                social_network_analysis_pipeline(filterTime, filterAvRv)
            except:
                print("\033[91m" + 10 * "=", "[" + filterTime + "_" + filterAvRv + "] ERROR in SNA Pipeline", 10 * "=", "\033[00m")

