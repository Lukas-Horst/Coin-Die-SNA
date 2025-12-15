import os
import sys
import traceback

# Set the submodule path for all subsequent imports in this process
SUBMODULE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Coin-Die-SNA-Interface")
if SUBMODULE_PATH not in sys.path:
    sys.path.insert(0, SUBMODULE_PATH)

from flask import Flask, render_template, jsonify, request, send_file
import json
import glob
from check_gt import check_gt_file
from main import social_network_analysis_pipeline
from cluster_to_graph import imagecluster_get_cluster, get_coin_findspots, map_clusters_to_findspots, plot_coint_per_die, map_findspots_to_clusters
from findspot_geolocation import get_findspot_osmtypeid
from config.config_manager import ConfigManager
from data_utils import find_file

try:
    from matching_plot import get_matches_plot

    auto_die_studies_available = True
except ImportError:
    auto_die_studies_available = False


app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/graphdata")
def graphdata_api():
    """
    API endpoint to serve the pre-calculated network graph data (nodes and edges).

    Query Params:
        filterTime (str): Time period filter (default: "X").
        filterAvRv (str): Side filter (default: "").

    Returns:
        Response: JSON object containing the graph data ('nodes' and 'edges') for visualization.
                  Returns empty structure if the file does not exist.
    """
    filterTime = request.args.get("filterTime", "X")
    filterAvRv = request.args.get("filterAvRv", "")

    file_path = f"Cache/graph_export/{filterTime}_{filterAvRv}/networkx_export.json"

    if not os.path.exists(file_path):
        # Prevent crash if SNA pipeline hasn't run yet for this combination
        print(f"Graph file not found: {file_path}. Did the SNA pipeline run?")
        return jsonify({"nodes": [], "edges": []})

    with open(file_path, "r") as f:
        try:
            data = json.load(f)
            return jsonify(data)
        except json.JSONDecodeError as e:
            print(f"Error reading JSON from {file_path}: {e}")
            return jsonify({"nodes": [], "edges": []})


@app.route("/analysislist")
def analysislist_api():
    """
    API endpoint to retrieve a list of available coin die analysis files.

    Scans for analysis files, calculates metrics against Ground Truth (GT) if available,
    and marks files that are currently selected in the configuration.

    Returns:
        Response: A JSON response containing a list of tuples, where each tuple contains:
            - name (str): Filename of the analysis file.
            - ri (float): Rand Index metric (or None).
            - ari (float): Adjusted Rand Index metric (or None).
            - selected (str): 'r' if selected as reverse, 'a' if selected as obverse, else empty.
            - ami (float): Adjusted Mutual Information metric (or None).
    """
    analysis_list = []

    config = config_manager.config

    analysis_files = config_manager.get_coin_die_analysis_files()

    for path, name in analysis_files:
        side = "r" if ("reverse" in name) else "a"
        ri, ari, ami = check_gt_file(path, side)

        selected = ""
        if config.get("paths", {}).get("dataset-reverse") == name:
            selected = "r"
        if config.get("paths", {}).get("dataset-obverse") == name:
            selected = "a"

        analysis_list.append((name, ri, ari, selected, ami))

    json_data = jsonify(analysis_list)
    return json_data


@app.route("/config")
def config_api():
    """
    API endpoint to retrieve the current full configuration.

    Returns:
        Response: JSON object representing the current configuration state.
    """
    return jsonify(config_manager.config)


@app.route("/configset", methods=["POST"])
def config_set_api():
    """
    API endpoint to update a specific path configuration value.

    Expects a JSON payload with:
    - key (str): The configuration key (relative to 'paths').
    - value (str): The new value to set.

    Returns:
        Response: JSON confirmation {"text": "ok"}.
    """
    data = json.loads(request.data)
    key = data.get("key")
    value = data.get("value")

    config_manager.set_config_value(f'paths.{key}', value)
    config_manager.save_config()

    return jsonify({"text": "ok"})


@app.route("/snapipeline", methods=["POST"])
def start_sna_pipeline():
    """
    API endpoint to execute the Social Network Analysis (SNA) pipeline for a specific subset.

    Expects a JSON payload with:
    - filterTime (str): Time period filter (e.g., 'A', 'B', 'X').
    - filterAvRv (str): Side filter ('a' for obverse, 'r' for reverse, '' for both).

    Returns:
        Response: JSON object containing the status text (e.g., "A_r" on success or "A_r - ERROR").
    """
    data = json.loads(request.data)
    filterTime = data.get("filterTime")
    filterAvRv = data.get("filterAvRv")
    try:
        social_network_analysis_pipeline(filterTime, filterAvRv)
    except Exception as e:
        # Improved error logging with exception details
        print(
            f"\033[91m Test {10 * '='} [{filterTime}_{filterAvRv}] ERROR in SNA Pipeline: {e} {10 * '='} \033[00m")
        return jsonify({"text": filterTime + "_" + filterAvRv + " - ERROR"})

    return jsonify({"text": filterTime + "_" + filterAvRv})


@app.route("/snapipelineall", methods=["POST"])
def start_sna_pipeline_all():
    """
    API endpoint to execute the SNA pipeline for ALL defined combinations of time periods and coin sides.

    Iterates through sides ['', 'r', 'a'] and time periods ['X', 'A', ..., 'U'] and
    runs the analysis for each combination sequentially. Errors in individual runs are logged
    but do not stop the entire process.

    Returns:
        Response: JSON confirmation message when all pipelines have finished.
    """
    for filterAvRv in ["", "r", "a"]:
        for filterTime in ["X", "A", "B", "C", "D", "E", "F", "G", "H", "P", "U"]:
            try:
                social_network_analysis_pipeline(filterTime, filterAvRv)
            except Exception as e:
                print(
                    f"\033[91m{10 * '='} [{filterTime}_{filterAvRv}] ERROR in SNA Pipeline: {e} {10 * '='}\033[00m")

                # Print the full stack trace for detailed debugging
                traceback.print_exc()

                # Print a separator for clarity
                print("-" * 50)

    return jsonify({"text": "All SNA Piplines finished"})


@app.route("/cluster")
def cluster_api():
    """
    API endpoint to retrieve detailed information about a specific die cluster.

    Query Params:
        clusterId (str): The ID of the cluster to retrieve.

    Workflow:
    1. Loads cluster data for both reverse ('r') and obverse ('a') from the current analysis files.
    2. Merges these clusters.
    3. Maps the clusters to geographical findspots of the coins.
    4. Returns the specific data for the requested `clusterId`.

    Returns:
        Response: JSON object containing the cluster details and associated findspots.
    """
    cluster_id = request.args.get("clusterId", "")

    # Retrieve current analysis files via ConfigManager
    clusters_r = imagecluster_get_cluster(config_manager.get_current_analysis_file(), "r")
    clusters_a = imagecluster_get_cluster(config_manager.get_current_analysis_file("a"), "a")

    # Merge dictionaries
    clusters = clusters_r | clusters_a

    coin_findspots = get_coin_findspots()
    clusters_at_findspot = map_clusters_to_findspots(clusters, coin_findspots)

    return jsonify(clusters_at_findspot.get(cluster_id, {}))


@app.route("/findspot")
def findspot_api():
    """
    API endpoint to retrieve clusters associated with a specific findspot.

    Query Params:
        fs (str): The findspot name to filter by.

    Returns:
        Response: JSON object containing cluster data for the specified findspot.
    """
    findspot = request.args.get("fs", "")

    # Retrieve current analysis files
    clusters_r = imagecluster_get_cluster(config_manager.get_current_analysis_file(), "r")
    clusters_a = imagecluster_get_cluster(config_manager.get_current_analysis_file("a"), "a")

    # Merge clusters
    clusters = clusters_r | clusters_a

    coin_findspots = get_coin_findspots()
    cluster_at_fs = map_findspots_to_clusters(clusters, coin_findspots, findspot)

    return jsonify(cluster_at_fs)


@app.route("/findspotosm")
def findspotosm_api():
    """
    API endpoint to retrieve OpenStreetMap (OSM) type and ID for a given findspot.

    Query Params:
        fs (str): The findspot name.

    Returns:
        Response: JSON object containing OSM type and ID (e.g., {'type': 'node', 'id': 12345}).
    """
    findspot = request.args.get("fs", "")
    return jsonify(get_findspot_osmtypeid(findspot))


@app.route("/coinimg")
def coinimg():
    """
    API endpoint to retrieve the image file for a specific coin.

    Query Params:
        id (str): The unique coin ID.
        side (str): The side of the coin ('r' for reverse, 'a' for obverse).

    Returns:
        Response: The image file (MIME type image/png) if found, otherwise string "not available".
    """
    coin_id = request.args.get("id", "")
    side = request.args.get("side", "r")

    config = config_manager.config

    if side == "r":
        folder = config["paths"].get("images_reverse", "")
    else:
        folder = config["paths"].get("images_obverse", "")

    pattern = folder + "/**/" + coin_id + "_*"
    paths = glob.glob(pattern, recursive=True)

    if not paths:
        return "not available"
    else:
        return send_file(paths[0], mimetype="image/png")


@app.route("/coinsperdiechart")
def coinsperimg_chart():
    """
    API endpoint to generate and serve a chart showing the distribution of coins per die.

    Query Params:
        file (str): The filename of the analysis file to process.

    Returns:
        Response: An SVG image of the plot (MIME type image/svg+xml).
    """
    analysis_file = request.args.get("file", "")
    side = "r" if ("reverse" in analysis_file) else "a"

    clusters = imagecluster_get_cluster(find_file(config_manager.get_output_dir(), analysis_file),
                                        side)
    buffer = plot_coint_per_die(clusters)

    return send_file(buffer, mimetype="image/svg+xml")


@app.route("/coinmatching")
def coinmatching_img():
    """
    API endpoint to generate a visual comparison (matching points) between two coin images.

    Query Params:
        coinid1 (str): ID of the first coin.
        coinid2 (str): ID of the second coin.
        side (str): Side to compare ('r' or 'a').

    Returns:
        Response: A JPEG image showing the matches if available, otherwise string "not available".
    """
    if not auto_die_studies_available:
        return "not available"

    coin_id1 = request.args.get("coinid1", "")
    coin_id2 = request.args.get("coinid2", "")
    side = request.args.get("side", "r")

    num_matches, img_matches = get_matches_plot(coin_id1, coin_id2, side)
    return send_file(img_matches, mimetype="image/jpeg")


@app.route("/snametricsnode")
def snametrics_node():
    """
    API endpoint to serve node-level SNA metrics (e.g., centrality measures).

    Query Params:
        filterTime (str): Time period filter (default: "X").
        filterAvRv (str): Side filter (default: "").

    Returns:
        Response: JSON object containing node metrics. Returns empty object if file not found.
    """
    filterTime = request.args.get("filterTime", "X")
    filterAvRv = request.args.get("filterAvRv", "")

    file_path = f"Cache/SNA_results/{filterTime}_{filterAvRv}/node_sna_metrics.json"

    if not os.path.exists(file_path):
        print(
            f"Node metrics file not found: {file_path}. The SNA pipeline might not have been run for this filter.")
        return jsonify({})

    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            return jsonify(data)
    except json.JSONDecodeError as e:
        print(f"Error reading JSON from {file_path}: Invalid JSON content: {e}")
        return jsonify({})


@app.route("/snametricsedge")
def snametrics_edge():
    """
    API endpoint to serve edge-level SNA metrics (e.g., betweenness centrality).

    Query Params:
        filterTime (str): Time period filter (default: "X").
        filterAvRv (str): Side filter (default: "").

    Returns:
        Response: JSON object containing edge metrics. Returns empty object if file not found.
    """
    filterTime = request.args.get("filterTime", "X")
    filterAvRv = request.args.get("filterAvRv", "")

    file_path = f"Cache/SNA_results/{filterTime}_{filterAvRv}/edge_sna_metrics.json"

    if not os.path.exists(file_path):
        print(
            f"Edge metrics file not found: {file_path}. Did the SNA pipeline run for this filter?")
        return jsonify({})

    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            return jsonify(data)
    except json.JSONDecodeError as e:
        print(f"Error reading JSON from {file_path}: Invalid JSON content: {e}")
        return jsonify({})


@app.route("/communities")
def communities():
    """
    API endpoint to serve community detection results (Louvain/Leiden communities).

    Query Params:
        filterTime (str): Time period filter (default: "X").
        filterAvRv (str): Side filter (default: "").

    Returns:
        Response: JSON object containing community assignments and metadata.
                  Returns empty structure if file not found.
    """
    filterTime = request.args.get("filterTime", "X")
    filterAvRv = request.args.get("filterAvRv", "")

    file_path = f"Cache/subgraphs/{filterTime}_{filterAvRv}/community_data.json"

    if not os.path.exists(file_path):
        print(
            f"Community file not found: {file_path}. The SNA pipeline might not have been run for this filter.")
        return jsonify({"communities": [], "metadata": {}})

    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            return jsonify(data)
    except json.JSONDecodeError as e:
        print(f"Error reading JSON from {file_path}: Invalid JSON content: {e}")
        return jsonify({"communities": [], "metadata": {}})


if __name__ == "__main__":
    config_manager = ConfigManager('Coin-Die-SNA-Interface/config/config.json')
    app.run(host="0.0.0.0", port=5001, debug=True)
