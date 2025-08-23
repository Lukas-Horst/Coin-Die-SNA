import { mapGraph } from "./mapgraph.js"

let mapisinit = false;

let map;

async function init() {
    map = new L.Map("map-container", { zoomControl: false, dragging: true, zoomSnap: 0.05, zoomAnimation: false, fadeAnimation: false }).setView([48.029, 10.180], 7);
    
    const tiles = new L.TileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);
    
    new L.Control.Scale({ maxWidth: 200, position: 'bottomleft', imperial: false }).addTo(map);
    new L.Control.Zoom({ position: 'bottomleft' }).addTo(map);
    
    let svgGraphLayer = new L.SVG();
    svgGraphLayer.addTo(map);

    mapisinit = true;
}

async function initMap(graphData, snaMetricsNode, snaMetricsEdge, communities) {
    if (!mapisinit) await init();

    $("#map-container svg g").empty();
    let svg = d3.select("#map-container").select("svg");

    let svgGraph = mapGraph(graphData, svg, map, snaMetricsNode, snaMetricsEdge, communities);
}

export { initMap }