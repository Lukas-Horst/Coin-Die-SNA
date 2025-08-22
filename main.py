from config import get_config
from cluster_to_graph import construct_graph_both_sides, construct_graph
from NetworkX_SNA import shorten_edges, create_graph, network_Analysis, get_subgraphs, export_graph


def social_network_analysis_pipeline(filterTime="X", filterAvRv=""):
    config = get_config()

    folder = filterTime + "_" + filterAvRv
    print(10 * "=", "[" + folder + "] Starting SNA Pipeline", 10 * "=")

    # Graph Konstruktion
    if filterAvRv == "":
        nodes, edges = construct_graph_both_sides("rsc/" + config["dataset-reverse"], "rsc/" + config["dataset-obverse"])
    elif filterAvRv == "a":
        nodes, edges = construct_graph("rsc/" + config["dataset-obverse"], "a")
    elif filterAvRv == "r":
        nodes, edges = construct_graph("rsc/" + config["dataset-reverse"], "r")
    print("[" + folder + "] Graph construction done")

    # Social Network Analysis
    short_edges = shorten_edges(edges)
    NetworkX_Graph = create_graph(short_edges, nodes, True, [] if filterTime == "X" else [filterTime])
    network_Analysis(NetworkX_Graph, folder)
    get_subgraphs(NetworkX_Graph, folder)
    print("[" + folder + "] SNA done")

    # Export
    export_graph(NetworkX_Graph, folder)
    print("[" + folder + "] Export done")

    print(10 * "=", "[" + folder + "] Finished SNA Pipeline", 10 * "=")


if __name__ == "__main__":
    social_network_analysis_pipeline()
