import json
import shutil
import networkx as nx
import regex as re
import os

from cluster_to_graph import construct_graph_both_sides
from networkx.algorithms.community import greedy_modularity_communities

from config.config_manager import ConfigManager

config_manager = ConfigManager('Coin-Die-SNA-Interface/config/config.json')
cache_dir = config_manager.config["paths"]["cache_dir"]


def shorten_edges(edge_list):
    """Some coins have unknown findspots. This in turn leads to some edges lying between a
    coin-cluster and an empty string. To prevent having the unknown findspot also as node in the
    chart this function is used to filter those edges out before creating the NetworkX chart"""
    two_values_edge = [(a, b) for (a, b, _) in edge_list]
    pattern = re.compile(r"^\d{1,4}_[a-zA-Z]$")
    # remove Edges where one of the nodes is '' (Ignoring Clusters or Cluster edges that have no
    # findspot)
    filtered_two_value_edge = [(c, d) for (c, d) in two_values_edge if c != "" and d != ""]
    # only keep edges between a cluster and a place
    relevant_edges = [(e, f) for (e, f) in filtered_two_value_edge if not (pattern.match(e) and pattern.match(f))]
    return relevant_edges


def create_graph(edge_list, node_list, remove_low_degree_clusters, filter=[]):
    """Function to create a NetworkX chart that serves als the basis for visualisation"""
    if filter is None:
        filter = []
    network_graph = nx.Graph()
    network_graph.add_edges_from(edge_list)

    # removes coin cluster that are only connected to one findspot since those don't say
    # anything about social networks of that time
    if remove_low_degree_clusters:
        pattern = re.compile(r"^\d{1,4}_[a-zA-Z]$")
        removal = [node for node in network_graph.nodes() if network_graph.degree(node) == 1 and pattern.match(node)]
        network_graph.remove_nodes_from(removal)

    attributes = {}
    # add attributes to nodes in NetworkX Graph
    for node in node_list:
        node_id = node[0]
        if node_id in network_graph:
            if node[1] == "Cluster":
                attributes[node_id] = {"type": node[1], "cluster_id": node_id, "num_coins_in_cluster": node[3], "coins_in_cluster": node[4], "node_type": node[5], "time_frame": node[6]}
            elif node[1] == "Findspot":
                attributes[node_id] = {
                    "type": node[1],
                    "Findspot_name": node_id,
                    "num_coins_at_findspot": node[3],
                    "coins_at_findspot": node[4],
                    "findspot_coordinates": node[5],
                    "findspot_type": node[6],
                }
    nx.set_node_attributes(network_graph, attributes)
    
    # Filters Graph to only contain coins from certain time period if it was requested to do so
    # when calling the function
    if len(filter) > 0:
        removal_filter = [entry for entry, attributes in network_graph.nodes(data=True) if attributes.get("type") == "Cluster" and attributes.get("time_frame") not in filter]
        network_graph.remove_nodes_from(removal_filter)

    

    return network_graph


def network_analysis(graph, save_directory):
    """Calculates and saves SNA metrics for edges and nodes"""

    degree_centrality = nx.degree_centrality(graph)

    closeness_centrality = nx.closeness_centrality(graph)

    betweenness_centrality = nx.betweenness_centrality(graph)

    eigenvector_centrality = nx.eigenvector_centrality(graph, max_iter=1000)

    pagerank = nx.pagerank(graph)

    av_neighbor_degree = nx.average_neighbor_degree(graph)

    edge_betweeness_centrality = nx.edge_betweenness_centrality(graph)

    edge_load_centrality = nx.edge_load_centrality(graph)

    num_edges = dict(graph.degree())

    sna_node_metrics = []
    sna_edge_metrics = []

    for node in graph.nodes():
        sna_node_metrics.append(
            {
                "node": node,
                "num_edges": num_edges.get(node, 0),
                "degree_centrality": degree_centrality.get(node, 0),
                "closeness_centrality": closeness_centrality.get(node, 0),
                "betweenness_centrality": betweenness_centrality.get(node, 0),
                "eigenvector_centrality": eigenvector_centrality.get(node, 0),
                "pagerank": pagerank.get(node, 0),
                "av_neighbor_degree": av_neighbor_degree.get(node, 0),
            }
        )
    for a, b in graph.edges():
        key = tuple(sorted((a, b)))
        sna_edge_metrics.append({"From": a, "To": b, "edge_betweeness_centrality": edge_betweeness_centrality.get(key, 0), "edge_load_centrality": edge_load_centrality.get(key, 0)})

    base_output_path = os.path.join(cache_dir, "SNA_results",
        config_manager.get_combined_analysis_file_name(), save_directory)
    node_path = os.path.join(base_output_path, "node_sna_metrics.json")
    edge_path = os.path.join(base_output_path, "edge_sna_metrics.json")
    os.makedirs(os.path.dirname(node_path), exist_ok=True)

    with open(node_path, "w") as f:
        json.dump(sna_node_metrics, f, indent=2)

    with open(edge_path, "w") as f_2:
        json.dump(sna_edge_metrics, f_2, indent=2)


def get_subgraphs(graph, save_directory):
    """Searches and saves communities found in a NetworkX chart."""

    directory = f"{cache_dir}/subgraphs/{config_manager.get_combined_analysis_file_name()}"
    full_directory = os.path.join(directory, save_directory)
    os.makedirs(os.path.dirname(full_directory), exist_ok=True)

    if os.path.exists(full_directory):
        shutil.rmtree(full_directory)  # removes all contents
    os.makedirs(full_directory)

    communities = list(greedy_modularity_communities(graph))
    communities = [community for community in communities if len(community) > 1]
    community_data = []

    for counter, entry in enumerate(communities):
        subgraph = graph.subgraph(entry).copy()

        nodes = list(subgraph.nodes())
        edges = list(subgraph.edges())

        community_data.append({"id": counter, "nodes": nodes, "edges": [list(edge) for edge in edges]})

        """plt.figure(figsize=(12, 12))
        pos = nx.spring_layout(subgraph, seed=50)
        nx.draw(subgraph, pos, with_labels=True, node_size=300)
        plt.title(f"Community_{counter}")

        save_path = os.path.join(full_directory, f"Community_{counter}.png")
        plt.savefig(save_path)
        plt.close"""

    json_path = os.path.join(full_directory, "community_data.json")
    with open(json_path, "w") as f:
        json.dump(community_data, f, indent=2)


def export_graph(graph, save_directory):
    """Export a NetworkX chart"""
    data1 = nx.node_link_data(graph, edges="edges")
    json_graph = json.dumps(data1, indent=4)
    directory = os.path.join(f"{cache_dir}/graph_export/",
                             config_manager.get_combined_analysis_file_name(),
                             save_directory, "networkx_export.json")

    os.makedirs(os.path.dirname(directory), exist_ok=True)

    with open(directory, "w") as f:
        f.write(json_graph)


if __name__ == "__main__":
    pass
