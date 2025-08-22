import { getRequest, postRequest } from "./utils.js"
import { fdGraph } from "./fdgraph.js"
import { initMap } from "./map.js"

let timeMap = { 0: "X", 1: "A", 2: "B", 3: "C", 4: "D", 5: "E", 6: "F", 7: "G", 8: "H", 9: "P", 10: "U" };
let snaMetricsNode;

let snaMetricSection = (snaMetrics) => {
    let snaHtml = /*html*/`
    <label>${snaMetrics.num_edges}</label>
    <label class="sec">degree</label>
    <label class="sep">|</label>
    <label>${snaMetrics.pagerank.toFixed(2)}</label>
    <label class="sec">pagerank</label>
    <label class="sep">|</label>
    <label>${snaMetrics.av_neighbor_degree.toFixed(0)}</label>
    <label class="sec">avg neighbor degree</label>
    <div class="line"></div>
    <label>${snaMetrics.degree_centrality.toFixed(2)}</label>
    <label class="sec">degree centrality</label><br>
    <label>${snaMetrics.betweenness_centrality.toFixed(2)}</label>
    <label class="sec">betweenness centrality</label><br>
    <label>${snaMetrics.closeness_centrality.toFixed(2)}</label>
    <label class="sec">closeness centrality</label>
    `;
    return snaHtml;
}

let openInspector = async (id) => {
    $("#inspector-container").show();
    $("#inspector-heading").html(id);
    $("#inspector-comparison").html("");

    let clusterData = await getRequest("cluster", { clusterId: id });
    console.log(clusterData);

    let snaMetrics = snaMetricsNode.find(d => d.node === id);
    let snaHtml = snaMetricSection(snaMetrics)
    $("#sna-section").html(snaHtml);

    $("#coin-section").html("");
    for (let fs in clusterData) {
        let sectionHtml = /*html*/`<h4 style="margin: 8px 0">${fs}</h4><div class="grid">`;
        for (let coin of clusterData[fs]) {
            sectionHtml += /*html*/`
                        <label class="sec flex coin-img-container">
                        <img class="coin-img" alt="${coin}" src="coinimg?id=${coin}&side=${id.split("_")[1]}">
                        <input type="checkbox" value="${coin}_${id.split("_")[1]}" name="compare-coins">${coin}
                        </label>
                    `;
        }
        sectionHtml += `</div>`;
        $("#coin-section").append(sectionHtml)
    }
}

let openInspectorFs = async (id) => {
    $("#inspector-container").show();
    $("#inspector-comparison").html("");
    
    let fsData = await getRequest("findspot", { fs: id });
    let fsOsm = await getRequest("findspotosm", { fs: id });
    console.log(fsData);

    $("#inspector-heading").html(`<a href="https://openstreetmap.org/${fsOsm}" target="_blank">${id}</a>`);

    let snaMetrics = snaMetricsNode.find(d => d.node === id);
    let snaHtml = snaMetricSection(snaMetrics)
    $("#sna-section").html(snaHtml);
    console.log(snaMetrics);

    $("#coin-section").html("");
    for (let cluster in fsData) {
        let sectionHtml = /*html*/`<h4 style="margin: 8px 0">Coins of findspot in ${cluster}</h4><div class="grid">`;
        for (let coin of fsData[cluster]) {
            sectionHtml += /*html*/`
                        <label class="sec flex coin-img-container">
                        <img class="coin-img" alt="${coin}" src="coinimg?id=${coin}&side=${cluster.split("_")[1]}">
                        <input type="checkbox" value="${coin}_${cluster.split("_")[1]}" name="compare-coins">${coin}
                        </label>
                    `;
        }
        sectionHtml += `</div>`;
        $("#coin-section").append(sectionHtml)
    }
}

let openAnalysisDataPage = async () => {
    $("#analysis-data-container").show();

    const analysisList = await getRequest("analysislist", {});
    console.log(analysisList);
    $("#analysis-list").html("");
    for (let analysis of analysisList) {
        $("#analysis-list").append(/*html*/`
            <div class="list-item">
                <div class="flex">
                    <label class="file-name">${analysis[0]}</label>
                    <div class="flex" style="gap: 8px">
                        <label class="sec">RI</label>
                        <label style="width: 30px">${Math.round(analysis[1] * 100) / 100}</label>
                        <label class="sec">ARI</label>
                        <label style="color: hsl(${((analysis[2]) * 128)}, 100%, 40%); width: 30px">${Math.round(analysis[2] * 100) / 100}</label>
                        <label class="sec">AMI</label>
                        <label style="color: hsl(${((analysis[4]) * 128)}, 100%, 40%); width: 30px">${Math.round(analysis[4] * 100) / 100}</label>
                        <label><input type="radio" name="dataset-obverse" value="${analysis[0]}" ${analysis[3] === "a" ? "checked" : ""}>Av</label>
                        <label><input type="radio" name="dataset-reverse" value="${analysis[0]}" ${analysis[3] === "r" ? "checked" : ""}>Rv</label>
                    </div>
                </div>
                <div class="coinsperdie-chart"></div>
            </div>
            `);
    }
}

let loadGraphs = async () => {
    let time = $("#time-control").val();
    time = timeMap[time];
    let avrv = $("#avrvfilter").val();
    
    const graphData = await getRequest("graphdata", { filterTime: time, filterAvRv: avrv });
    if (graphData == 500) {
        alert(`Error: Filter ${avrv} ${time} not available because of an error in the SNA pipeline`);
        return;
    }

    snaMetricsNode = await getRequest("snametricsnode", { filterTime: time, filterAvRv: avrv })
    const snaMetricsEdge = await getRequest("snametricsedge", { filterTime: time, filterAvRv: avrv })

    const communities = await getRequest("communities", { filterTime: time, filterAvRv: avrv })

    let chart = fdGraph(graphData, snaMetricsNode, snaMetricsEdge, communities);
    $("#graph-container").html(chart);

    initMap(graphData, snaMetricsNode, snaMetricsEdge, communities);
}

/**
 * Event Handler
 */
$(() => {
    $("button#appearance").on("click", () => {
        $("body").toggleClass("white");
        $("button#appearance > i").toggleClass("fa-moon fa-sun");
    })

    $("button.tab").on("click", async (e) => {
        $("button.tab").removeClass("active");
        $(e.currentTarget).addClass("active");

        $("#main-pages").children().hide();
        if (e.currentTarget.id === "analysis-data-btn") {
            openAnalysisDataPage();
        } else if (e.currentTarget.id === "map-graph-btn") {
            $("#map-container").show();
        } else {
            $("#graph-container").show();
        }
    })

    $("#analysis-list").on("click", ".list-item", (e) => {
        let name = $(e.currentTarget).find(".file-name")[0].innerHTML;
        if ($(e.currentTarget).find(".coinsperdie-chart").html() === "") {
            $(e.currentTarget).find(".coinsperdie-chart").html(`<img src="coinsperdiechart?file=${name}">`);
        } else {
            $(e.currentTarget).find(".coinsperdie-chart").html("")
        }
    })

    $("#analysis-list").on("change", "input", (e) => {
        let key = e.currentTarget.name;
        let value = e.currentTarget.value;
        postRequest("configset", JSON.stringify({ key: key, value: value }));
    })

    $("#start-sna").on("click", async (e) => {
        $("#sna-check").hide();
        $("#sna-spinner").show();
        const result = await postRequest("snapipelineall", {});
        console.log(result);
        
        /* const promisesAvRv = Object.values(timeMap).map(val => postRequest("snapipeline", JSON.stringify({ filterTime: val, filterAvRv: "" })));
        const responsesAvRv = await Promise.all(promisesAvRv);
        console.log(responsesAvRv);

        const promisesAv = Object.values(timeMap).map(val => postRequest("snapipeline", JSON.stringify({ filterTime: val, filterAvRv: "a" })));
        const responsesAv = await Promise.all(promisesAv);
        console.log(responsesAv);

        const promisesRv = Object.values(timeMap).map(val => postRequest("snapipeline", JSON.stringify({ filterTime: val, filterAvRv: "r" })));
        const responsesRv = await Promise.all(promisesRv);
        console.log(responsesRv); */
        
        $("#sna-spinner").hide();
        $("#sna-check").show();
        loadGraphs();
    })

    $("#time-control").on("change", () => {
        loadGraphs();
    })

    $("#avrvfilter").on("change", () => {
        loadGraphs();
    })

    $("#close-inspector").on("click", () => {
        $("#inspector-container").hide();
    })

    $("#coin-section").on("change", "input[type=checkbox]", (e) => {
        let numChecked = $("#coin-section input[type=checkbox]:checked").length;
        if (numChecked > 2) {
            e.currentTarget.checked = false;
            return;
        }
        if (numChecked != 2) return;

        let coinId1 = $("#coin-section input[type=checkbox]:checked")[0].value.split("_")[0];
        let coinId2 = $("#coin-section input[type=checkbox]:checked")[1].value.split("_")[0];
        let side = $("#coin-section input[type=checkbox]:checked")[0].value.split("_")[1];
        $("#inspector-comparison").html(/*html*/`
            <img src="coinmatching?coinid1=${coinId1}&coinid2=${coinId2}&side=${side}" class="matching-img">
            <br>
            <img src="coinmatching?coinid1=${coinId2}&coinid2=${coinId1}&side=${side}" class="matching-img">
        `);
    })
})

/**
 * Start Script
 */
$(async () => {
    loadGraphs();
})

export { openInspector, openInspectorFs }
