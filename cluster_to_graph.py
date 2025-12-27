import json
import csv
import os.path

from config.config_manager import ConfigManager
from findspot_geolocation import get_findspot_coordinate
import glob
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io


config_manager = ConfigManager('Coin-Die-SNA-Interface/config/config.json')
config = config_manager.config


def get_findspots():
    """Returns { findspot: (coin_count, type) } dict"""
    findspots = dict()
    with open(config['paths']['findspot_data'], "r") as numisdata_file:
        _ = next(numisdata_file)
        dialect = csv.Sniffer().sniff(numisdata_file.read(1024))
        numisdata_file.seek(0)
        numisdata = csv.reader(numisdata_file, dialect)
        for row in numisdata:
            fs = row[13]
            count = 1
            if fs in findspots:
                count = findspots[fs][0] + 1

            findspots[fs] = (count, row[14])

    return findspots


def get_coin_findspots():
    """Returns { coind_id: findspot } dict"""
    coin_findspots = {}
    with open(config['paths']['findspot_data'], "r") as numisdata_file:
        _ = next(numisdata_file)
        dialect = csv.Sniffer().sniff(numisdata_file.read(1024))
        numisdata_file.seek(0)
        numisdata = csv.reader(numisdata_file, dialect)
        for row in numisdata:
            coin_findspots[row[0]] = row[13]

    return coin_findspots


def imagecluster_get_cluster(cluster_json, side):
    """Returns { cluster_id_side : [coin_id] } from { coin_id: cluster_id } input json"""
    with open(cluster_json, "r") as cluster_file:
        cluster_raw = json.load(cluster_file)

    clusters = {}
    for coin, cluster in cluster_raw.items():
        clusters.setdefault(cluster + "_" + side, []).append(coin)

    return clusters


def map_clusters_to_findspots(clusters, coin_findspots):
    """
    Returns { cluster_id: { findspot: [coin_id] } }
    clusters: { cluster_id : [coin_id] }
    coin_findspots: { coind_id: findspot }
    """
    clusters_at_findspot = {}
    for cluster, coins in clusters.items():
        coins_at_fs = {}
        for coin in coins:
            fs = coin_findspots.get(coin, "")
            coins_at_fs.setdefault(fs, []).append(coin)

        clusters_at_findspot[cluster] = coins_at_fs

    return clusters_at_findspot


def map_findspots_to_clusters(clusters, coin_findspots, findspot):
    """
    Returns { findspot: { cluster_id: [coind_id] } }
    clusters: { cluster_id : [coin_id] }
    coin_findspots: { coind_id: findspot }
    findspots: single findspot name
    """
    cluster_at_fs = {}
    for cluster, coins in clusters.items():
        if len(coins) <= 1:
            continue

        coins_of_fs = []
        for coin in coins:
            if coin_findspots.get(coin) == findspot:
                coins_of_fs.append(coin)

        if len(coins_of_fs) > 0:
            cluster_at_fs[cluster] = coins_of_fs

    return cluster_at_fs


def connect_nodes_pairwise(node_list, name_prefix=""):
    edges = []
    for i in range(len(node_list)):
        for k in range(i + 1, len(node_list)):
            edges.append((name_prefix + "_" + node_list[i], name_prefix + "_" + node_list[k]))
    return edges


def get_cluster_times(clusters, side):
    """
    Return { cluster_id: allen_type }
    clusters: { cluster_id : [coin_id] }
    """
    folder = config["paths"]["images_reverse"] if side == "r" else config["paths"]["images_obverse"]

    img_paths = glob.glob(folder + "/**/*")

    coin_times = {}
    for path in img_paths:
        img_file = os.path.basename(path)
        time = os.path.basename(os.path.dirname(path))
        img_id = img_file.split("_")[0]
        coin_times[img_id] = time

    cluster_times = {}
    for cluster, coins in clusters.items():
        cluster_times[cluster] = coin_times[coins[0]]

    return cluster_times


def construct_graph(cluster_file, side):
    """
    Nodes = Cluster, Findspots
    Edges = Coin of Cluster found at findspot
    """
    clusters = imagecluster_get_cluster(cluster_file, side)
    coin_findspots = get_coin_findspots()
    findspots = get_findspots()
    findspot_coords = get_findspot_coordinates(findspots)
    clusters_at_findspot = map_clusters_to_findspots(clusters, coin_findspots)
    cluster_times = get_cluster_times(clusters, side)

    # Nodes
    nodes = []
    for cluster, coins in clusters.items():
        node = (cluster, "Cluster", cluster, len(coins), tuple(coins), side, cluster_times[cluster])
        nodes.append(node)

    for findspot, (num_coins, fs_type) in findspots.items():
        node = (findspot, "Findspot", findspot, num_coins, (), findspot_coords[findspot], fs_type)
        nodes.append(node)

    # print(nodes)
    print(len(nodes), "Clusters")

    # Edges
    edges = []
    for cluster, coins_at_findspot in clusters_at_findspot.items():
        for findspot, coins in coins_at_findspot.items():
            edge = (cluster, findspot, len(coins))
            edges.append(edge)

    # print(edges)
    print(len(edges), "Edges")

    return nodes, edges


def construct_graph_both_sides(cluster_file_r, cluster_file_a):
    nodes_r, edges_r = construct_graph(cluster_file_r, "r")
    nodes_a, edges_a = construct_graph(cluster_file_a, "a")

    nodes = list(set(nodes_r) | set(nodes_a))
    edges = list(set(edges_r) | set(edges_a))

    # Connect reverse and obverse cluster
    # with open(cluster_file_r, "r") as cluster_file_r_json:
    #     cluster_raw_r = json.load(cluster_file_r_json)
    # with open(cluster_file_a, "r") as cluster_file_a_json:
    #     cluster_raw_a = json.load(cluster_file_a_json)
    #
    # for coin_r, cluster_r in cluster_raw_r.items():
    #     for coin_a, cluster_a in cluster_raw_a.items():
    #         if coin_a == coin_r:
    #             edge = (cluster_r + "_r", cluster_a + "_a", 1)
    #             edges.append(edge)

    print(len(nodes), "Clusters")
    print(len(edges), "Edges")

    return nodes, edges


def plot_coint_per_die(clusters):
    length_counts = {}

    for coins in clusters.values():
        length = len(coins)
        if length in length_counts:
            length_counts[length] += 1
        else:
            length_counts[length] = 1

    min_len = min(length_counts.keys())
    max_len = max(length_counts.keys())

    lengths = list(range(min_len, max_len + 1))
    counts = [length_counts.get(length, 0) for length in lengths]

    plt.figure(figsize=(8, 4))
    plt.bar(lengths, counts, color="#4689ea")
    plt.xlabel("Coins per die")
    plt.ylabel("Count")
    plt.xticks(lengths)
    plt.grid(axis="y", linestyle="-", alpha=0.7)
    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format="svg")
    plt.close()
    buffer.seek(0)
    return buffer
    # plt.show()


def get_findspot_coordinates(findspots):
    """Returns { findspot: coordinate } dict"""
    fs_coordinates = dict()
    for fs, _ in findspots.items():
        coords = get_findspot_coordinate(fs)
        fs_coordinates[fs] = coords

    return fs_coordinates


if __name__ == "__main__":
    pass
