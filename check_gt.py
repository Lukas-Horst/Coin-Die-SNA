import json
import csv
import collections
from math import comb
from sklearn.metrics import adjusted_mutual_info_score
from config import get_config


def get_cluster_assignments_json(cluster_json):
    """
    Get cluster assignments from json { id: cluster, ... }
    """
    clusters = {}
    with open(cluster_json, "r") as cluster_file:
        cluster_raw = json.load(cluster_file)

        for coin, assignment in cluster_raw.items():
            coin_id = coin.split("_")[0]
            clusters[coin_id] = assignment

    return clusters


def get_cluster_assignments_csv(cluster_csv, side="r"):
    """
    Get cluster assignmets of ground truth csv from Neuses findspot
    """
    if side == "r":
        col_index = 2
    else:
        col_index = 1

    clusters_raw = {}
    with open(cluster_csv, "r") as cluster_file:
        _ = next(cluster_file)
        dialect = csv.Sniffer().sniff(cluster_file.read(1024)) # Reads the first 1024 Bytes, to get the dialect
        cluster_file.seek(0) # Setting the pointer back to the start
        cluster_reader = csv.reader(cluster_file, dialect)
        for row in cluster_reader:
            clusters_raw[row[0]] = row[col_index]

    return clusters_raw


def ri(c1, c2, elements):
    a = 0
    b = 0
    n = len(elements)
    count_n_2 = 0

    for i in range(n):
        for k in range(i + 1, n):
            x1 = elements[i]
            x2 = elements[k]
            count_n_2 += 1
            same_c1 = c1[x1] == c1[x2]
            same_c2 = c2[x1] == c2[x2]
            if same_c1 and same_c2:
                a += 1
            elif not same_c1 and not same_c2:
                b += 1

    n_2 = n * (n - 1) / 2
    ri = (a + b) / n_2

    return ri


def ari(c1, c2, elements):
    n = len(elements)

    c1_grouped = collections.defaultdict(set)
    c2_grouped = collections.defaultdict(set)

    for i, (d, c) in enumerate(c1.items()):
        if d in elements:
            c1_grouped[c].add(d)
    for i, (d, c) in enumerate(c2.items()):
        if d in elements:
            c2_grouped[c].add(d)

    contingency = []
    for x1 in c1_grouped.values():
        row = []
        for x2 in c2_grouped.values():
            row.append(len(x1 & x2))
        contingency.append(row)

    sum_nij = 0
    for row in contingency:
        for n_ij in row:
            sum_nij += comb(n_ij, 2)

    sum_ai = 0
    for row in contingency:
        a_i = 0
        for n_ij in row:
            a_i += n_ij
        sum_ai += comb(a_i, 2)

    sum_bi = 0
    for col in zip(*contingency):
        b_i = 0
        for n_ij in col:
            b_i += n_ij
        sum_bi += comb(b_i, 2)

    n_2 = comb(n, 2)

    expected_ri = sum_ai * sum_bi / n_2
    max_ri = 0.5 * (sum_ai + sum_bi)

    ari = (sum_nij - expected_ri) / (max_ri - expected_ri)
    return ari


def check_gt(cluster_pred, cluster_true):
    intersect = list(set(cluster_pred) & set(cluster_true))
    ri_score = ri(cluster_pred, cluster_true, intersect)
    ari_score = ari(cluster_pred, cluster_true, intersect)

    ids = sorted(set(cluster_true) & set(cluster_pred))
    labels_true = [cluster_true[cid] for cid in ids]
    labels_pred = [cluster_pred[cid] for cid in ids]
    ami_score = adjusted_mutual_info_score(labels_true, labels_pred)

    return ri_score, ari_score, ami_score


def check_gt_file(pred_file, coin_side):
    cluster_imagecluster = get_cluster_assignments_json(pred_file)
    try:
        cluster_gt_neuses = get_cluster_assignments_csv("die_ground_truth.csv", side=coin_side)
    except FileNotFoundError:
        return (0, 0, 0)

    return check_gt(cluster_imagecluster, cluster_gt_neuses)


if __name__ == "__main__":
    config = get_config()

    cluster_imagecluster_r = get_cluster_assignments_json("rsc/" + config["dataset-reverse"])
    cluster_imagecluster_a = get_cluster_assignments_json("rsc/" + config["dataset-obverse"])
    cluster_gt_neuses_r = get_cluster_assignments_csv("die_ground_truth.csv", side="r")
    cluster_gt_neuses_a = get_cluster_assignments_csv("die_ground_truth.csv", side="a")

    ri_r, ari_r, ami_r = check_gt_file("rsc/" + config["dataset-reverse"], "r")
    ri_a, ari_a, ami_a = check_gt_file("rsc/" + config["dataset-obverse"], "a")
    print("Reverse RI:", ri_r)
    print("Reverse ARI:", ari_r)
    print("Obverse RI:", ri_a)
    print("Obverse ARI:", ari_a)

    intersect = list(set(cluster_imagecluster_r) & set(cluster_gt_neuses_r))
    with open("neuses_matches.csv", "w", newline="") as matchfile:
        writer = csv.writer(matchfile)
        writer.writerow(["Id", "Av", "Rv"])
        for coin in intersect:
            writer.writerow([coin, cluster_imagecluster_a[coin],  cluster_imagecluster_r[coin]])
