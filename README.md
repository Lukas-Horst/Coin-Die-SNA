# Coin-Die-SNA

Social Network Analysis based on die studies of ancient coin collections and their findspots.

### Input Data
Die data has to be provided as two JSON files for reverse and obverse in the `rsc` directory. The content must be in the form of key-value pairs where the key is the coin identifier and the value is the respective cluster identifier, e.g. `{ coin1: cluster1, coin2: cluster1, coin3: cluster2 }`.

Findspot data is taken from the numisdata export expected in the project root directory as an CSV file named `numisdata_bushel.csv`. If you have a ground truth to compare with, also put it as an csv file named `die_ground_truth.csv` into the project root (Columns: coind_id, obverse_die, reverse_die).

Additionally, provide the path to images of coin reverse and obverse in the `config.json` file, to view them in the web view.

If you want to see the similarity rating of two coins in a cluster with our used method to get an automated die study, Auto-Die-Studies, clone their repository and put the path to it in the config.


### Results
To view the results, run the `webserver.py` script and open the web view in your browser at `localhost:5001`.
In the "Die Data" tab, select which die study data to use for reverse and oberverse. 
Then start the social network analysis pipeline with the start button. This can take a view seconds to process and is automatically loaded upon finishing.

The two visualisations can be found in the Force Graph and Map View tabs, where you can navigate the graphs by dragging and zoom via the mouse wheel.
Clicking a node opens the inspector, revealing SNA metrics, coins and XFeat image matching. Additionally, edges to connected findspots are highlighted.
In the top bar there are filter options for reverse/obverse and the Allen Types of the coins.