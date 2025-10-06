let TEAMS = null;  // { teamId -> "Baltimore Orioles" }
let TMS   = null;  // { teamId -> "BAL" }

// On loading the DOM, get the power, standings, odds, batting, pitching, and fielding data
document.addEventListener("DOMContentLoaded", async () => {
  const app = document.getElementById("app");
    
    try {
      const [power, standings, odds, batting, pitching, fielding, teams] = await Promise.all([
        fetch("/power").then((res) => res.json()),
        fetch("/standings").then((res) => res.json()),
        fetch("/odds").then((res) => res.json()),
        fetch("/batting").then((res) => res.json()),
        fetch("/pitching").then((res) => res.json()),
        fetch("/fielding").then((res) => res.json()),
        fetch("/teams").then((res) => res.json()),
      ]);
        TEAMS = teams.teams;
        TMS = teams.tms;

        // create the content boxes
        // for now create chart-div-6 manually

        await createContentBox(TEAMS, TMS, "Team Rankings", app, "container-1", "team-checkboxes-1", "mode-1", "chart-div-1", "checkbox", ["mlb", "power", "diff", "both"], [getRankings], 'TOR',"The easiest way to see how a team's performing is to track its ranking through the season. Pick any number of teams from the selector and compare their journeys over time. Choose <strong>MLB</strong> Rank for win-based standings, <strong>Power</strong> Rank for analyst insights, <strong>Both</strong> to see them side-by-side, or <strong>Diff</strong> to reveal where perception and performance split - positive means overrated, negative means underrated.");
        styleTeamSelectors();
        await createContentBox(TEAMS, TMS, "Rank Changes", app, "container-2", "team-checkboxes-2", "mode-2", "chart-div-2", "checkbox", ["mlb", "power"], [getKDEs],'TOR', "This chart shows how a team's ranking shifts week to week. The bars show actual changes, while the curve shows the probability of those changes. If the peak is above zero, the team usually climbs, below, they tend to drop. The spread reveals how consistent they are - a narrow curve means steady performance, a wide one means volatility. Choose <strong>MLB</strong> Rank for win-based standings or <strong>Power</strong> Rank for analyst insights. Pick any number of teams from the selector to compare their rank movements and consistency.");
        styleTeamSelectors();
        await createContentBox(TEAMS, TMS, "Volatility", app, "container-3", "team-checkboxes-3", "mode-3", "chart-div-3", "checkbox", ["mlb", "power"], [getVolatility], 'TOR', "This line shows how a team's ranking volatility changes through the season. Every team starts at zero - no games mean no volatility. Rising slopes signal growing unpredictability, while falling slopes show steadier performance. Spikes mean the team's performance swings wildly from week to week; dips show steady, predictable play. It's the easiest way to see who’s stable and who's chaotic. Pick any number of teams from the selector to compare their volatility trends.");
        styleTeamSelectors();
        await createContentBox(TEAMS, TMS, "Stability", app, "container-4", "team-radios-4", "mode-4", "chart-div-4", "radio", ["mlb", "power"], [getStability], 'TOR', "These curves show how much a team's past performance influences its future results. Each lookback represents how many weeks of performance we're looking at. Positive  means momentum - good weeks tend to follow good ones. Negative values mean reversals - ups are followed by downs. When the curve drops, consistency is fading, when it rises, trends are strengthening. I know this is getting a bit mathy, but it's a powerful way to see who's riding hot streaks and who's stuck in slumps. Pick any team from the selector to see how their performance stability shifts with different lookback periods.");
        styleTeamSelectors();
        // after these 4 are loaded remove the loader
        const loaderParent = document.querySelector(".loader-parent");
        if (loaderParent) {
          // slide it to the left and fade out
            loaderParent.style.transition = "all 0.5s ease";
            loaderParent.style.transform = "translateX(-100%)";
            loaderParent.style.opacity = "0";
            // set body overflow to auto
            document.body.style.overflow = "auto";
            // set overflow-x to hidden
            document.body.style.overflowX = "hidden";
        }
        await createContentBox(TEAMS, TMS, "Causality", app, "container-5", "team-radios-5", "mode-5", "chart-div-5", "radio", [], [getGranger,null, statsFill], 'TOR', "This chart tests whether power rankings can predict actual MLB rankings - basically, how reliable they even are. Each bar shows a lag, meaning how many weeks back the power ranking is compared to the MLB rank. If a bar falls below the red line, it means the power rankings have predictive power when looking back that many weeks. The lower the bar, the stronger the prediction. If all bars are above the line, it means power rankings don't really help predict actual performance of that team. Pick any team from the selector to see how well their power rankings forecast their real-world results.");
        styleTeamSelectors();
        await createContentBox(TEAMS, TMS, "Similarity", app, "container-7", "team-checkboxes-7", "mode-7", "chart-div-7", "checkbox", ["mlb", "power"], [getSimilarity, null, getSimilarityData],'TOR',"Here you can see the similarity between any two teams. The Average Rank Difference shows how far apart they usually sit in the standings. Similarity in Week-by-Week Changes captures how often they move in the same direction - a higher value means they rise and fall together, while a negative one means opposite momentum. Overall Trend Similarity reflects whether their trends align over time. Finally, the Overall Trajectory Similarity score summarizes how closely their season paths match overall - higher means more alike. Select any two teams from the selector to see how closely their seasons mirror each other.");
        styleTeamSelectors();


        // manually create chart-div-6 content box
        const box6 = document.createElement("div");
        box6.id = `container-6-box`;
        box6.classList.add("content-box");
        app.appendChild(box6);
        const header6 = document.createElement("h2");
        header6.textContent = "Clustering";
        box6.appendChild(header6);
        const p6 = document.createElement("p");
        p6.id = `container-6-content1`;
        p6.classList.add("content-box-text1");
        p6.innerHTML = `This chart groups teams based on their batting, pitching, and fielding performance throughout the season. Using these stats, teams with similar technical profiles are placed in the same cluster - essentially, they play the game in a similar way. On the chart, the x-axis shows each cluster's average MLB rank, while the y-axis shows the actual rank of each individual team.
        <br><br>
        You'll notice a clear pattern: the top clusters are packed with playoff teams - technically sharp, consistent across all areas. The bottom clusters contain teams that struggled across the board, finishing near the bottom of their divisions. The middle clusters are more crowded: these teams have comparable stats, but their final rankings vary widely, suggesting that other factors like injuries, luck, clutch hitting, or managerial choices likely influenced outcomes.
        <br><br>
        In short, the higher a team appears on the chart, the better it performed overall, and this clustering shows how technical quality translates into results, though not always perfectly. Baseball's still a game of numbers, but also of moments.`;
        box6.appendChild(p6);
        const chartDiv6 = document.createElement("div");
        chartDiv6.id = "chart-div-6";
        chartDiv6.classList.add("chart");
        box6.appendChild(chartDiv6);
        getClusters("chart-div-6");

        await createContentBox(TEAMS, TMS, "Performance Tier", app, "container-8", "team-radios-8", "mode-8", "chart-div-8", "radio", [], [getHmm, null, getHmmData],'TOR',"Select any team. Here, each week's performance for that team is measured against all other teams across both leagues to see how it stacks up. Every week is classified as Good, Mediocre, or Bad, based on how strong that performance was in context. Over the season, these weekly states reveal each team's rhythm - who stays hot, who cools off, and who swings between extremes. From these patterns, we can estimate the chances of performing well next week, capturing each team's momentum in motion and predict how well they might do going forward.");

        styleTeamSelectors();
        // add event listener to checkboxes and radio buttons to restyle on change
        document.body.addEventListener("change", styleTeamSelectors);
    } catch (error) {
        console.error("Error fetching data:", error);
    }
});

// DOM generation functions
async function createContentBox(teams, tms, title, parent, containerId, inputBoxId, modeName, chartDivId, inputType, modeOptions, callbackArray, defaultTeam="TOR", content1="", content2="") {
    const box = document.createElement("div");
    box.id = `${containerId}-box`;
    box.classList.add("content-box");
    const header = document.createElement("h2");
    header.textContent = title;
    box.appendChild(header);
    // add two top level p elements for content1 and content2, one before chartDiv and one after
    const p1 = document.createElement("p");
    p1.id = `${containerId}-content1`;
    p1.classList.add("content-box-text1");
    if (content1 && content1.length > 0) {
        p1.innerHTML = content1;
    }

    
    // add the second top level p element for content2
    const p2 = document.createElement("p");
    p2.id = `${containerId}-content2`;
    p2.classList.add("content-box-text2");
    if (content2 && content2.length > 0) {
        p2.innerHTML = content2;
    }

    box.appendChild(p1);
    // create the input elements
    if (inputType === "checkbox") {
        await createTeamCheckboxes(teams, tms, box, inputBoxId, modeName, chartDivId, callbackArray, p1, p2);
    }
    else if (inputType === "radio") {
        await createTeamRadioButtons(teams, tms, box, inputBoxId, modeName, chartDivId, callbackArray, p1, p2);
    }
    // create the mode options
    if (modeOptions && modeOptions.length > 0) {
        let anychecked = false;
        const modeContainer = document.createElement("div");
        modeContainer.id = `${modeName}-container`;
        modeContainer.classList.add("mode-container");
        modeOptions.forEach(mode => {
            const radio = document.createElement("input");
            radio.type = "radio";
            radio.name = modeName;
            radio.id = `${modeName}-${mode}`;
            radio.value = mode;
            radio.classList.add("mode-radio");
            const label = document.createElement("label");
            label.textContent = mode;
            label.htmlFor = `${modeName}-${mode}`;
            modeContainer.appendChild(radio);
            modeContainer.appendChild(label);
            if (mode === "both") {
                radio.checked = true;
                anychecked = true;
            }
        });
        // if none were checked, check the first one
        if (!anychecked && modeOptions.length > 0) {
            const firstRadio = modeContainer.querySelector("input[type='radio']");
            if (firstRadio) {
                firstRadio.checked = true;
            }
        }

        box.appendChild(modeContainer);
    }

    // add the box to the parent
    parent.appendChild(box);
    // on change of mode, call the callbacks in the array
    if (callbackArray && callbackArray.length > 0 && modeOptions && modeOptions.length > 0 && callbackArray[0] != null) {
        const modeContainer = box.querySelector(`#${modeName}-container`);
        modeContainer.addEventListener("change", async () => {
            callbackArray[0](defaultTeam, inputBoxId, modeName, chartDivId, false, true, true, inputType === "checkbox" ? "team-checkbox" : "team-radio");
        });
    }
    if (callbackArray && callbackArray.length > 0 && modeOptions && modeOptions.length > 0 && callbackArray[1] != null) {
        const modeContainer = box.querySelector(`#${modeName}-container`);
        modeContainer.addEventListener("change", async () => {
            p1.innerHTML = await callbackArray[1](containerId);
        });
    }
    if (callbackArray && callbackArray.length > 0 && modeOptions && modeOptions.length > 0 && callbackArray[2] != null) {
        const modeContainer = box.querySelector(`#${modeName}-container`);
        modeContainer.addEventListener("change", async () => {
            p2.innerHTML = await callbackArray[2](containerId);
        });
    }

    // add a div for the plotly chart
    const chartDiv = document.createElement("div");
    chartDiv.id = chartDivId;
    chartDiv.classList.add("chart");
    box.appendChild(chartDiv);
    // initial call to the callbacks in the array to render the chart for the default team
    if (callbackArray && callbackArray.length > 0 && callbackArray[0] != null) {
        callbackArray[0](defaultTeam, inputBoxId, modeName, chartDivId, false, true, true, inputType === "checkbox" ? "team-checkbox" : "team-radio");
    }
    if (callbackArray && callbackArray.length > 1 && callbackArray[1] != null) {
        p1.innerHTML = callbackArray[1](containerId);
    }
    if (callbackArray && callbackArray.length > 2 && callbackArray[2] != null) {
        p2.innerHTML = callbackArray[2](containerId);
    }

    // if there are more callbacks, use callback[1] to fill content1 and callback[2] to fill content2. Both callback[1] and callback[2] MUST take containerId as their only parameter and return the innerHTML string

    // if there is a callbackArray[1], use it to fill content1
    if (callbackArray && callbackArray.length > 1 && callbackArray[1] != null) {
        // could be async, so await it
        p1.innerHTML = await callbackArray[1](containerId);
    }

    // if there is a callbackArray[2], use it to fill content2
    if (callbackArray && callbackArray.length > 2 && callbackArray[2] != null) {
        // could be async, so await it
        p2.innerHTML = await callbackArray[2](containerId);
    }
    box.appendChild(p2);
}

async function createTeamCheckboxes(teams,tms,parent, containerId, modeName, chartDivId, eventupdate = [getRankings], p1, p2) {
    const container = document.createElement("div");
    container.id = containerId;
    container.classList.add("team-checkbox-container-main");
    for (const [teamId, teamName] of Object.entries(teams)) {
        const teamAbbr = tms[teamId];
        const color = await fetch(`/color?team=${teamAbbr}`).then((res) => res.json());
        const logo = await fetch(`/logo?team=${teamAbbr}`).then((res) => res.json());
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.classList.add("team-checkbox");
        checkbox.classList.add(`${containerId}-checkbox`);
        checkbox.value = teamAbbr;
        checkbox.name = `${containerId}-checkbox`;
        checkbox.dataset.logo = logo.url;
        checkbox.dataset.pcolor = color.color.primary_color ? `rgb(${color.color.primary_color.join(",")})` : "";
        checkbox.dataset.scolor = color.color.secondary_color ? `rgb(${color.color.secondary_color.join(",")})` : "";
        checkbox.dataset.association = color.color.association;
        checkbox.id = `checkbox-${teamId}-${containerId}`;
        const label = document.createElement("label");
        label.htmlFor = `checkbox-${teamId}-${containerId}`;
        label.textContent = teamName;
        // put both into one div
        const div = document.createElement("div");
        div.classList.add("team-checkbox-container");
        div.appendChild(checkbox);
        div.appendChild(label);
        container.appendChild(div);
        // on change of checkbox, call eventupdate with the containerId and the team code
        checkbox.addEventListener("change", async () => {
            eventupdate[0](checkbox.value, containerId, modeName, chartDivId);
            if (eventupdate.length > 1 && eventupdate[1] != null) {
                // remove -box from parent.id
                const passId = parent.id.replace("-box", "");
                p1.innerHTML = await eventupdate[1](passId);
            }
            if (eventupdate.length > 2 && eventupdate[2] != null) {
                const passId = parent.id.replace("-box", "");
                p2.innerHTML = await eventupdate[2](passId);
            }
        });
        // if team is TOR, check the box
        if (teamAbbr === "TOR") {
            checkbox.checked = true;
        }
    }
    parent.appendChild(container);
}

async function createTeamRadioButtons(teams,tms,parent, containerId, modeName, chartDivId, eventupdate = [getRankings], p1, p2) {
    const container = document.createElement("div");
    container.id = containerId;
    container.classList.add("team-radio-container-main");
    for (const [teamId, teamName] of Object.entries(teams)) {
        const teamAbbr = tms[teamId];
        const color = await fetch(`/color?team=${teamAbbr}`).then((res) => res.json());
        const logo = await fetch(`/logo?team=${teamAbbr}`).then((res) => res.json());
        const radio = document.createElement("input");
        radio.type = "radio";
        radio.classList.add("team-radio");
        radio.classList.add(`${containerId}-radio`);
        radio.value = teamAbbr;
        radio.name = `${containerId}-radio-group`;
        radio.dataset.logo = logo.url;
        radio.dataset.pcolor = color.color.primary_color ? `rgb(${color.color.primary_color.join(",")})` : "";
        radio.dataset.scolor = color.color.secondary_color ? `rgb(${color.color.secondary_color.join(",")})` : "";
        radio.dataset.association = color.color.association;
        radio.id = `radio-${teamId}-${containerId}`;
        const label = document.createElement("label");
        label.htmlFor = `radio-${teamId}-${containerId}`;
        label.textContent = teamName;
        // put both into one div
        const div = document.createElement("div");
        div.classList.add("team-radio-container");
        div.appendChild(radio);
        div.appendChild(label);
        container.appendChild(div);
        // on change of radio, call eventupdate with the containerId and the team code
        radio.addEventListener("change", async () => {
            eventupdate[0](radio.value, containerId, modeName, chartDivId);
            if (eventupdate.length > 1 && eventupdate[1] != null) {
                console.log("Updating content1 via callback");
                const passId = parent.id.replace("-box", "");
                p1.innerHTML = await eventupdate[1](passId);
            }
            if (eventupdate.length > 2 && eventupdate[2] != null) {
                console.log("Updating content2 via callback");
                const passId = parent.id.replace("-box", "");
                p2.innerHTML = await eventupdate[2](passId);
            }
        });
        // if team is TOR, check the radio
        if (teamAbbr === "TOR") {
            radio.checked = true;
        }
    }
    parent.appendChild(container);
}


// API call and chart rendering functions

// 1. Ranking functions
async function getRankings(code, checkboxContainerId, modeName, chart_div, noMarkers = false, drawLine = true, drawShading = true, typeClass="team-checkbox") {
    const selectedTeams = Array.from(
        document.querySelectorAll(`#${checkboxContainerId} input.${typeClass}:checked`)
    ).map(cb => cb.value);
    // if nothing is selected, use the code parameter (for initial load)
    if (selectedTeams.length === 0 && code) {
        selectedTeams.push(code);
    }
    // if nothing is selected AND there is no code parameter, display toronto
    else if (selectedTeams.length === 0) {
        selectedTeams.push("TOR");
    }
    const mode = document.querySelector(`input[name="${modeName}"]:checked`) ? document.querySelector(`input[name="${modeName}"]:checked`).value : "both";
    if (selectedTeams.length > 0) {
        const query = selectedTeams.map(team => `teams=${team}`).join("&") + `&mode=${mode}`;
        const data = await fetch(`/ranks?${query}`).then(res => res.json());
        if (mode === "diff") {
            renderChart(data, selectedTeams, mode, chart_div, noMarkers, drawLine, false);
        }
        else {
            renderChart(data, selectedTeams, mode, chart_div, noMarkers, drawLine, drawShading);
        }
    }
}

function renderChart(data, selectedTeams, mode, chartDivId, noMarkers = false, drawLine = true, drawShading = true) {
    // use the selectedTeams to get the color
    const colors = {};
    const scolors = {};
    selectedTeams.forEach(team => {
        const checkbox = document.querySelector(`.team-checkbox[value="${team}"], .team-radio[value="${team}"]`);
        // check association to determine which color to use
        const association = checkbox ? checkbox.dataset.association : "primary";
        colors[team] = checkbox ? (association === "primary" ? checkbox.dataset.pcolor : checkbox.dataset.scolor) : "#000000";
        scolors[team] = checkbox ? (association === "primary" ? checkbox.dataset.scolor : checkbox.dataset.pcolor) : "#000000";
    });
    const traces = [];
    const dateStrings = data.ranks.map(row => row.date);
    const dates = dateStrings.map(dateStr => new Date(dateStr));
    const shape = 'spline'; // 'spline' for smooth lines, 'linear' for straight lines
    selectedTeams.forEach(teamCode => {
        const teamFullName = getTeamFullNameFromCode(teamCode, TEAMS, TMS);
        let yValues = [];
        let yLabel = "";
        if (mode === "mlb") {
            yValues = data.ranks.map(row => row[`${teamFullName} — MLB Rank`]);
            yLabel = "MLB Rank";
        } else if (mode === "power") {
            yValues = data.ranks.map(row => row[`${teamFullName} — Power Rank`]);
            yLabel = "Power Rank";
        }
        else if (mode === "diff") {
            yValues = data.ranks.map(row => row[`${teamFullName} — Δ`]);
            yLabel = "Difference (Δ)";
        }
        else if (mode === "both") {
            // create two traces, one for MLB and one for Power
            const yValuesMLB = data.ranks.map(row => row[`${teamFullName} — MLB Rank`]);
            const yValuesPower = data.ranks.map(row => row[`${teamFullName} — Power Rank`]);
            traces.push({
                x: dates,
                y: yValuesMLB,
                mode: 'lines+markers',
                name: `${teamFullName} (MLB)`,
                line: { shape: shape, color: colors[teamCode] || "#000000" },
                marker: { color: scolors[teamCode] || "#000000" },
                hovertemplate: `Team: ${teamFullName}<br>%{x|%Y-%m-%d}<br>MLB Rank: %{y}<extra></extra>`,
            });
            traces.push({
                x: dates,
                y: yValuesPower,
                mode: 'lines+markers',
                name: `${teamFullName} (Power)`,
                line: { shape: shape, dash: 'dash', color: colors[teamCode] || "#000000" },
                marker: { color: scolors[teamCode] || "#000000" },
                hovertemplate: `Team: ${teamFullName}<br>%{x|%Y-%m-%d}<br>Power Rank: %{y}<extra></extra>`,
            });
            return; // skip the rest of the loop
        }

        traces.push({
            x: dates,
            y: yValues,
            mode: 'lines+markers',
            name: teamFullName,
            line: { shape: shape, color: colors[teamCode] || "#000000" },
            marker: { color: scolors[teamCode] || "#000000" },
            hovertemplate: `Team: ${teamFullName}<br>%{x|%Y-%m-%d}<br>${yLabel}: %{y}<extra></extra>`,
        });
    });

    const layout = {
        title: 'Team Rankings Over Time',
        xaxis: {
            title: 'Date',
            type: 'date',
            tickformat: '%Y-%m-%d',
        },
        yaxis: {
            title: mode === "diff" ? 'Difference (Δ)' : 'Rank',
            autorange: mode === "diff" ? true : 'reversed', // invert y-axis for ranks, but not for difference
            dtick: 1,
            tick0: 1,
        },
        legend: {
            orientation: 'h',
            y: -0.2,
        },
        hovermode: 'closest',
        margin: { l: 30, r: 30, t: 30, b: 30 },  // tighten margins (left, right, top, bottom)
        autosize: true,
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
    };

    //remove the x axis (do not make a dark line)
    layout.xaxis.showline = false;
    layout.xaxis.zeroline = false;
    layout.yaxis.showline = false;
    layout.yaxis.zeroline = false;

    // show ticks every 5 ranks
    layout.yaxis.dtick = 5;

    // add a dashed horizontal line at y=15 if mode is not diff, otherwise at y=0
    if (drawLine === true) {
        if (mode !== "diff") {
            layout.shapes = [{
                type: 'line',
                x0: 0,
                x1: 1,
                y0: 15,
                y1: 15,
                yref: 'y',
                xref: 'paper',
                line: {
                    color: 'grey',
                    width: 2,
                    dash: 'dash',
                    opacity: 0.5
                }
            }];
        }
        else {
            layout.shapes = [{
                type: 'line',
                x0: 0,
                x1: 1,
                y0: 0,
                y1: 0,
                yref: 'y',
                xref: 'paper',
                line: {
                    color: 'grey',
                    width: 2,
                    dash: 'dash',
                    opacity: 0.5
                }
            }];
        }
    }

    if (drawShading === true) {

        layout.shapes = layout.shapes || [];

        if (mode !== "diff") {
            // Green above 15
            layout.shapes.push({
                type: 'rect',
                x0: 0,
                x1: 1,
                y0: 15,
                y1: Math.max(...dates.map(() => 30)), // or your max rank
                xref: 'paper',
                yref: 'y',
                fillcolor: 'rgba(255, 0, 0, 0.1)',
                line: { width: 0 }
            });
            // Red below 15
            layout.shapes.push({
                type: 'rect',
                x0: 0,
                x1: 1,
                y0: 0,
                y1: 15,
                xref: 'paper',
                yref: 'y',
                fillcolor: 'rgba(0, 255, 0, 0.1)',
                line: { width: 0 }
            });
        } else {
            // For diff mode: shade above 0 green, below 0 red
            layout.shapes.push({
                type: 'rect',
                x0: 0,
                x1: 1,
                y0: 0,
                y1: Math.max(...dates.map(() => 30)), // or your max Δ
                xref: 'paper',
                yref: 'y',
                fillcolor: 'rgba(255, 0, 0, 0.1)',
                line: { width: 0 }
            });
            layout.shapes.push({
                type: 'rect',
                x0: 0,
                x1: 1,
                y0: Math.min(...dates.map(() => -30)), // or your min Δ
                y1: 0,
                xref: 'paper',
                yref: 'y',
                fillcolor: 'rgba(0, 255, 0, 0.1)',
                line: { width: 0 }
            });
        }
    }



    // make all lines thicker and markers larger
    traces.forEach(trace => {
        trace.line.width = 3;
        trace.marker.size = 8;
    });

    if (noMarkers === true) {
        traces.forEach(trace => {
            trace.mode = 'lines';
        });
    }

    const config = { responsive: true, displayModeBar: false };
    const el = document.getElementById(chartDivId);
    Plotly.newPlot(el, traces, layout, config);

}


// 2. KDE functions
async function getKDEs(code, checkboxContainerId, modeName, chart_div, noMarkers = true, drawLine = false, drawShading = true, typeClass="team-checkbox") {
    const selectedTeams = Array.from(
        document.querySelectorAll(`#${checkboxContainerId} input.${typeClass}:checked`)
    ).map(cb => cb.value);
    // if nothing is selected, use the code parameter (for initial load)
    if (selectedTeams.length === 0 && code) {
        selectedTeams.push(code);
    }
    // if nothing is selected AND there is no code parameter, display toronto
    else if (selectedTeams.length === 0) {
        selectedTeams.push("TOR");
    }
    const mode = document.querySelector(`input[name="${modeName}"]:checked`) ? document.querySelector(`input[name="${modeName}"]:checked`).value : "both";
    if (selectedTeams.length > 0) {
        const query = selectedTeams.map(team => `teams=${team}`).join("&") + `&source=${mode}`;
        const data = await fetch(`/kdes?${query}`).then(res => res.json());
        const wrangled = wrangleKDEPayload(data, mode);
        console.log("KDE Data:", wrangled);
        renderKDE(wrangled, chart_div, noMarkers=true, drawLine=true, drawShading=false);
        
    }
}

function wrangleKDEPayload(payload, datasetKey = "dataset0") {
  const datasets = Array.isArray(payload) ? payload : [payload];
  const result = {};

  datasets.forEach((data, idx) => {
    const key = Array.isArray(payload)
      ? (data.source ?? (idx === 0 ? "power" : "mlb"))
      : (data.source ?? datasetKey);

    const teams = {};
    const order = [];

    // Build maps for quick lookups
    const peaks = data.peaks || {};
    const bws   = data.bandwidth || {};

    // Pre-seed team shells from peaks/bandwidth/maps (ensures we capture teams even if arrays are empty)
    for (const code of Object.keys(peaks)) {
      if (!teams[code]) {
        teams[code] = {
          label: code,
          bandwidth: bws[code] ?? null,
          peak: peaks[code] ?? null,
          kde: [],
          hist: []
        };
        order.push(code);
      }
    }

    // Fold KDE rows
    for (const row of (data.kde_data || [])) {
      const code = row.team_code;
      if (!teams[code]) {
        teams[code] = {
          label: row.label ?? code,
          bandwidth: row.bandwidth ?? (bws[code] ?? null),
          peak: peaks[code] ?? null,
          kde: [],
          hist: []
        };
        order.push(code);
      } else {
        // Update label/bandwidth if present
        if (row.label) teams[code].label = row.label;
        if (row.bandwidth != null) teams[code].bandwidth = row.bandwidth;
      }
      teams[code].kde.push({ x: Number(row.x), y: Number(row.density) });
    }

    // Fold Histogram rows
    for (const row of (data.hist_data || [])) {
      const code = row.team_code;
      if (!teams[code]) {
        teams[code] = {
          label: row.label ?? code,
          bandwidth: bws[code] ?? null,
          peak: peaks[code] ?? null,
          kde: [],
          hist: []
        };
        order.push(code);
      } else {
        if (row.label) teams[code].label = row.label;
      }
      teams[code].hist.push({ x: Number(row.x), y: Number(row.pdf) });
    }

    result[key] = { teams, order };
  });

  return result;
}

function renderKDE(data, chartDivId, noMarkers = true, drawLine = false, drawShading = true) {
  const mode = Object.keys(data)[0]; // "power" or "mlb"
  const selectedTeams = data[mode].order;

  const colors = {};
  const scolors = {};
  const xData1 = {}; // hist x (bin centers)
  const yData1 = {}; // hist y (scaled pdf)
  const xData2 = {}; // kde x
  const yData2 = {}; // kde y
  const labels = {};
  const peaks = {};

  selectedTeams.forEach(team => {
    const checkbox = document.querySelector(`.team-checkbox[value="${team}"], .team-radio[value="${team}"]`);
    const association = checkbox ? checkbox.dataset.association : "primary";
    colors[team]  = checkbox ? (association === "primary" ? checkbox.dataset.pcolor : checkbox.dataset.scolor) : "#000000";
    scolors[team] = checkbox ? (association === "primary" ? checkbox.dataset.scolor : checkbox.dataset.pcolor) : "#000000";

    labels[team] = data[mode].teams[team].label || team;

    // CHANGED: use nullish coalescing so a 0 peak is NOT dropped
    peaks[team]  = (data[mode].teams[team].peak ?? null);

    xData1[team] = data[mode].teams[team].hist.map(p => p.x);
    yData1[team] = data[mode].teams[team].hist.map(p => p.y);
    xData2[team] = data[mode].teams[team].kde.map(p => p.x);
    yData2[team] = data[mode].teams[team].kde.map(p => p.y);
  });

  const traces = [];
  const shape = 'spline';

  // Histogram bars — legend shows ONLY these; name is just the team, no hover
  selectedTeams.forEach(teamCode => {
    traces.push({
      type: 'bar',
      x: xData1[teamCode],
      y: yData1[teamCode],
      name: `${labels[teamCode]}`,                 // CHANGED: no "(Hist)"
      marker: { color: colors[teamCode] || "#000000", opacity: noMarkers ? 0.2 : 0.5 },
      legendgroup: teamCode,                       // keep legend tidy by team
      showlegend: true,                            // CHANGED: legend only on bars
      hoverinfo: 'skip'                            // CHANGED: no hover on bars
    });
  });

  // KDE line — stays out of legend
  selectedTeams.forEach(teamCode => {
    traces.push({
      type: 'scattergl',
      x: xData2[teamCode],
      y: yData2[teamCode],
      mode: 'lines',
      name: `${labels[teamCode]} (KDE)`,
      line: { shape: shape, color: colors[teamCode] || "#000000", width: 3 },
      hovertemplate: `Team: ${labels[teamCode]}<br>Probability (scaled): %{y}<extra></extra>`,
      marker: { color: scolors[teamCode] || "#000000", size: noMarkers ? 0 : 8 },
      legendgroup: teamCode,
      showlegend: false                            // CHANGED: hide KDE from legend
    });
  });

  const layout = {
    title: `Team ${mode === "power" ? "Power" : "MLB"} Rating Distributions`,
    xaxis: { title: "Value" },
    yaxis: { title: "Density", autorange: true, range: [0, null] },
    legend: { orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 },
    shapes: [],                                // CHANGED: start fresh; we won't overwrite later
    margin: { l: 50, r: 30, t: 50, b: 30 },  // tighten margins (left, right, top, bottom)
    autosize: true,
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
  };

  // CHANGED: always plot per-team peak (and do NOT overwrite later)
  selectedTeams.forEach(teamCode => {
    if (Number.isFinite(peaks[teamCode])) {
      layout.shapes.push({
        type: 'line',
        x0: peaks[teamCode], x1: peaks[teamCode],
        y0: 0, y1: 1,
        xref: 'x', yref: 'paper',
        line: { color: colors[teamCode] || "#000000", width: 2, dash: 'dash' },
        layer: 'below'
      });
    }
  });

  // Optional zero line — CHANGED: push, don't replace peak shapes
  if (drawLine === true) {
    layout.shapes.push({
      type: 'line',
      x0: 0, x1: 0, y0: 0, y1: 1,
      xref: 'x', yref: 'paper',
      line: { color: 'grey', width: 2, dash: 'dash' },
      layer: 'below'
    });
  }

  // Optional shading — CHANGED: push, don't replace
  if (drawShading === true) {
    layout.shapes.push(
      {
        type: 'rect',
        x0: -15, x1: 0, y0: 0, y1: 1,
        xref: 'x', yref: 'paper',
        fillcolor: 'red', opacity: 0.1,
        line: { width: 0 }, layer: 'below'
      },
      {
        type: 'rect',
        x0: 0, x1: 15, y0: 0, y1: 1,
        xref: 'x', yref: 'paper',
        fillcolor: 'green', opacity: 0.1,
        line: { width: 0 }, layer: 'below'
      }
    );
  }

  const el = document.getElementById(chartDivId);
  Plotly.newPlot(el, traces, layout, { responsive: true, displayModeBar: false });
}

// 3. Volatility functions
async function getVolatility(code, radioContainerId, modeName, chart_div, noMarkers = false, drawLine = true, drawShading = true, typeClass="team-checkbox") {
    const selectedTeams = Array.from(
        document.querySelectorAll(`#${radioContainerId} input.${typeClass}:checked`)
    ).map(checkbox => checkbox.value);
    // if nothing is selected, use the code parameter (for initial load)
    if (selectedTeams.length === 0 && code) {
        selectedTeams.push(code);
    }
    // if nothing is selected AND there is no code parameter, display toronto
    else if (selectedTeams.length === 0) {
        selectedTeams.push("TOR");
    }

    const mode = document.querySelector(`input[name="${modeName}"]:checked`) ? document.querySelector(`input[name="${modeName}"]:checked`).value : "both";
    if (selectedTeams.length > 0) {
        const query = selectedTeams.map(team => `teams=${team}`).join("&") + `&source=${mode}`;
        const data = await fetch(`/volatility?${query}`).then(res => res.json());
        const wrangled = wrangleVolatilityPayload(data);
        renderVolatility(wrangled, chart_div, noMarkers=noMarkers, drawLine=drawLine, drawShading=drawShading);
    }
}

function wrangleVolatilityPayload(payload, datasetKey = "dataset0") {
    const result = {};
    const source = payload.volatility_data[0].source || datasetKey;
    result[source] = { teams: {}, order: [] };
    // the unique values in payload.volatility_data.team_code define the teams
    const order = [];
    payload.volatility_data.forEach(item => {
        const teamCode = item.team_code;
        if (!result[source].teams[teamCode]) {
            result[source].teams[teamCode] = {
                label: item.label,
                data: []
            };
            order.push(teamCode);
        }
        result[source].teams[teamCode].data.push({'date': item.date, 'value': item.sigma});
    });
    result[source].order = order;
    return result;
}

function renderVolatility(data, chartDivId, noMarkers = false, drawLine = true, drawShading = true) {
    const colors = {};
    const scolors = {};
    const selectedTeams = data[Object.keys(data)[0]].order;
    selectedTeams.forEach(team => {
        const checkbox = document.querySelector(`.team-checkbox[value="${team}"], .team-radio[value="${team}"]`);
        const association = checkbox ? checkbox.dataset.association : "primary";
        colors[team]  = checkbox ? (association === "primary" ? checkbox.dataset.pcolor : checkbox.dataset.scolor) : "#000000";
        scolors[team] = checkbox ? (association === "primary" ? checkbox.dataset.scolor : checkbox.dataset.pcolor) : "#000000";
    });
    // similar to renderChart but y axis is not reversed and title is different
    const layout = {
        title: 'Volatility',
        xaxis: { title: 'Date' },
        yaxis: { title: 'Volatility (σ)', autorange: true },
        showlegend: true,
        margin: { l: 50, r: 30, t: 30, b: 30 },  // tighten margins (left, right, top, bottom)
        autosize: true,
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
    };
    const traces = [];
    const teams = data[Object.keys(data)[0]].teams;
    const shape = 'spline'; // 'spline' for smooth lines, 'linear' for straight lines
    selectedTeams.forEach(teamCode => {
        const teamFullName = getTeamFullNameFromCode(teamCode, TEAMS, TMS);
        const yValues = teams[teamCode].data.map(row => row.value);
        const dates = teams[teamCode].data.map(row => new Date(row.date));
        traces.push({
            x: dates,
            y: yValues,
            mode: 'lines+markers',
            name: teamFullName,
            line: { shape: shape, color: colors[teamCode] || "#000000", width: 3 },
            marker: { color: scolors[teamCode] || "#000000", size: noMarkers ? 0 : 8 },
            hovertemplate: `Team: ${teamFullName}<br>%{x|%Y-%m-%d}<br>Volatility (σ): %{y}<extra></extra>`,
        });
    });

    // layout adjustments
    layout.legend = { orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 };


    const el = document.getElementById(chartDivId);
    Plotly.newPlot(el, traces, layout, { responsive: true, displayModeBar: false });
}

// 4. Stability functions
async function getStability(code, radioContainerId, modeName, chart_div, noMarkers = false, drawLine = true, drawShading = true, typeClass="team-checkbox") {
    const selectedTeams = Array.from(
        document.querySelectorAll(`#${radioContainerId} input.${typeClass}:checked`)
    ).map(checkbox => checkbox.value);
    // if nothing is selected, use the code parameter (for initial load)
    if (selectedTeams.length === 0 && code) {
        selectedTeams.push(code);
    }
    // if nothing is selected AND there is no code parameter, display toronto
    else if (selectedTeams.length === 0) {
        selectedTeams.push("TOR");
    }
    const mode = document.querySelector(`input[name="${modeName}"]:checked`) ? document.querySelector(`input[name="${modeName}"]:checked`).value : "mlb";
    // Only one team allowed, and because radio buttons, it will be the only selected one
    const team = selectedTeams[0];
    if (team) {
        const query = `team=${team}&source=${mode}`;
        const data = await fetch(`/stability?${query}`).then(res => res.json());
        const wrangled = wrangleStabilityPayload(data);
        renderStability(wrangled, chart_div, noMarkers=false, drawLine=true, drawShading=false);
    }
}

function wrangleStabilityPayload(payload) {
    const result = {}
    const source  = payload.stability_data[0].source || "dataset0";
    const label  = payload.stability_data[0].label;
    const teamCode = payload.stability_data[0].team_code;
    result[source] = { teams: {}, order: [teamCode] };
    result[source].teams[teamCode] = { label: label, data: [] };
    // get all lag values (all unique values of payload.stability_data.lag)
    const lagValues = [...new Set(payload.stability_data.map(item => item.lag))];
    lagValues.forEach(lag => {
        const lagData = payload.stability_data.filter(item => item.lag === lag);
        const lagKey = `${lag}`;
        result[source].teams[teamCode].data[lagKey] = lagData.map(row => ({ 'date': row.date, 'value': row.value }));
    });
    return result;
}

function renderStability(data, chartDivId, noMarkers = false, drawLine = true, drawShading = true) {
    const colors = {};
    const scolors = {};
    const selectedTeams = data[Object.keys(data)[0]].order;
    // only one team, so get the first one
    const teamCode = selectedTeams[0];
    const checkbox = document.querySelector(`.team-checkbox[value="${teamCode}"], .team-radio[value="${teamCode}"]`);
    const association = checkbox ? checkbox.dataset.association : "primary";
    colors[teamCode]  = checkbox ? (association === "primary" ? checkbox.dataset.pcolor : checkbox.dataset.scolor) : "#000000";
    scolors[teamCode] = checkbox ? (association === "primary" ? checkbox.dataset.scolor : checkbox.dataset.pcolor) : "#000000";
    const layout = {
        title: 'Stability',
        xaxis: { title: 'Date' },
        yaxis: { title: 'Stability', autorange: true },
        showlegend: true,
        margin: { l: 50, r: 30, t: 30, b: 50 },  // tighten margins (left, right, top, bottom)
        autosize: true,
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
    };
    const traces = [];
    const teams = data[Object.keys(data)[0]].teams;
    const shape = 'spline';
    const lagKeys = Object.keys(teams[teamCode].data);
    lagKeys.forEach(lagKey => {
        const lag = parseInt(lagKey);
        const dates = teams[teamCode].data[lagKey].map(row => new Date(row.date));
        const yValues = teams[teamCode].data[lagKey].map(row => row.value);

        const lagColors = ["#1f77b4", "#2ca02c", "#ff7f0e", "#d62728", "#9467bd", "#8c564b", "#e377c2"];
        const lagColor = lag < lagColors.length ? lagColors[lag] : "#000000";
        traces.push({
            x: dates,
            y: yValues,
            mode: 'lines+markers',
            name: `${lag} week`,
            line: { shape: shape, width: 3 , color: lagColor },
            marker: { color: lagColor, size: noMarkers ? 0 : 8 },
            hovertemplate: `Team: ${getTeamFullNameFromCode(teamCode, TEAMS, TMS)}<br>Lag: ${lag}<br>%{x|%Y-%m-%d}<br>Stability: %{y}<extra></extra>`,
        });
    });

    // layout adjustments
    layout.legend = { orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 };
    // give a title to the legend
    layout.legend.title = { text: 'Lookback' };
    const el = document.getElementById(chartDivId);
    Plotly.newPlot(el, traces, layout, { responsive: true, displayModeBar: false });

}

// 5. Granger Causality functions

async function getGranger(code, radioContainerId, modeName, chart_div, typeClass="team-checkbox") {
    const selectedTeams = Array.from(
        document.querySelectorAll(`#${radioContainerId} input.${typeClass}:checked`)
    ).map(checkbox => checkbox.value);
    // if nothing is selected, use the code parameter (for initial load)
    if (selectedTeams.length === 0 && code) {
        selectedTeams.push(code);
    }
    // if nothing is selected AND there is no code parameter, display toronto
    else if (selectedTeams.length === 0) {
        selectedTeams.push("TOR");
    }
    const mode = document.querySelector(`input[name="${modeName}"]:checked`) ? document.querySelector(`input[name="${modeName}"]:checked`).value : "power_to_mlb";
    // set height of chart_div to 300px
    document.getElementById(chart_div).style.height = "300px";
    // Only one team allowed, and because radio buttons, it will be the only selected one
    const team = selectedTeams[0];
    if (team) {
        const query = `team=${team}`;
        const data = await fetch(`/granger?${query}`).then(res => res.json());
        renderGranger(data, chart_div);
    }
}

function renderGranger(data, chartDivId) {
    const teamCode = data.stats.team_code;
    const teamFullName = getTeamFullNameFromCode(teamCode, TEAMS, TMS);
    const lagData = data.granger_data;

    const checkbox = document.querySelector(`.team-checkbox[value="${teamCode}"], .team-radio[value="${teamCode}"]`);
    const association = checkbox ? checkbox.dataset.association : "primary";
    const color  = checkbox ? (association === "primary" ? checkbox.dataset.pcolor : checkbox.dataset.scolor) : "#000000";

    const traces = [{
        type: "bar",
        orientation: "h",
        x: lagData.map(row => row.p_value),
        y: lagData.map(row => row.lag),
        name: teamFullName,
        hovertemplate: `Team: ${teamFullName}<br>Lag: %{y}<br>p-value: %{x}<extra></extra>`,
        marker: { color: color, opacity: 0.8 },
        width: 0.4, // thinner bars (default is 0.8)
    }];

    const layout = {
        title: `Granger Causality Test p-values for ${teamFullName} (Power → MLB)`,
        xaxis: { title: "p-value", range: [0, 1] },
        yaxis: { title: "Lag (weeks)", dtick: 1 },
        bargap: 0.01,   // smaller gap between bars
        bargroupgap: 0.02, // minimal internal gap (when multiple bars per lag)
        shapes: [
            {
                type: "line",
                x0: 0.05, x1: 0.05,
                y0: 0.5, y1: lagData.length + 0.5,
                line: { color: "red", width: 2, dash: "dashdot" }
            }
        ],
        barcornerradius: 35, // subtle rounding
        margin: { l: 40, r: 30, t: 50, b: 40 },
        autosize: true,
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
    };

    Plotly.newPlot(chartDivId, traces, layout, { responsive: true, displayModeBar: false });
}

async function statsFill(containerId) {
  console.log(`Filling stats for container ${containerId}`);
  const checked = document.querySelector(`#${containerId}-box input.team-radio:checked`);
  const team = checked ? checked.value : defaultTeam;

  const data = await fetch(`/granger?team=${team}`).then(res => res.json());
  const stats = data.stats;

  return `
    <p class="granger-team"><strong>Team:</strong> ${getTeamFullNameFromCode(stats.team_code, TEAMS, TMS)}</p>
    <p class="granger-best-lag"><strong>Most predictive amount of weeks:</strong> ${stats.best_lag} week${stats.best_lag === 1 ? "" : "s"}</p>
    <p class="granger-best-p-value"><strong>Best confidence score:</strong> ${100-100 * (+stats.best_p).toFixed(2)}%</p>
    <p class="granger-significant"><strong>Do power rankings matter for this team:</strong> ${stats.is_significant ? "Yes" : "No"}</p>
  `;
}

// 6. Cluster functions

// Get the clusters data
async function getClusters(chart_div) {
  const figDiv = document.getElementById(chart_div);

  // 1) Fetch cluster data
  const data = await fetch(`/clusters`).then(res => res.json());

  // 2) Build team objects in parallel (and actually await them!)
  //    We add a tiny jitter PER team to prevent perfect overlap.
  const teamPromises = [];
  for (const cluster of data.clusters) {
    for (const teamFullName of cluster.teams) {
      teamPromises.push((async () => {
        const jitter = (2*Math.random() - 1); // ±
        const lastRank = await getLastRankForTeam(teamFullName);
        const logo = await getTeamLogo(teamFullName);
        return {
          code: TMS[teamFullName],                 // e.g., "TOR"
          cluster: cluster.cluster,                 // cluster id/label
          avg_last_mlb_rank: cluster.avg_last_mlb_rank,
          last_mlb_rank: lastRank,
          x: cluster.avg_last_mlb_rank + jitter,
          y: (lastRank ?? NaN),
          logo
        };
      })());
    }
  }
  const teams = (await Promise.all(teamPromises)).filter(t => Number.isFinite(t.y));

  // 3) Initialize an empty Plotly figure (once).
  //    We draw a blank scatter so axes are there.
  const trace = {
    x: teams.map(t => t.x),
    y: teams.map(t => t.y),
    mode: 'markers',
    marker: { size: 0, color: 'rgba(0,0,0,0)' }, // hide default markers; logos will show instead
    hoverinfo: 'skip'    // optional: no hover for the invisible markers
  };

  // A reasonable axis range if you don’t have one:
  const xVals = teams.map(t => t.x);
  const yVals = teams.map(t => t.y);
  const pad = 1;

  await Plotly.newPlot(figDiv, [trace], {
    margin: { l: 50, r: 10, t: 30, b: 50 },
    xaxis: {
      title: 'Average of last MLB ranks',
      range: [Math.min(...xVals) - pad, Math.max(...xVals) + pad],
      zeroline: false
    },
    yaxis: {
      title: 'Latest MLB rank',
      autorange: 'reversed', // smaller rank = better; if you prefer up = better, remove this
      range: [Math.min(...yVals) - pad, Math.max(...yVals) + pad],
      zeroline: false
    },
    images: [] // start empty; we’ll add all logos next
  }, { responsive: true, displayModeBar: false });

  const contourTraces = buildClusterContours(teams);

    // Add contours first so they render underneath logos
    await Plotly.addTraces(figDiv, contourTraces);

  // 4) Add ALL logos in one relayout (faster than many calls)
  // scale by rank of the team (bigger = better)
  const maxRank = Math.max(...teams.map(t => t.last_mlb_rank));
  const minRank = Math.min(...teams.map(t => t.last_mlb_rank));
  const rankRange = maxRank - minRank;
  const baseSize = 5;
  const images = teams.map(t => ({
    source: t.logo,       // base64 or URL
    x: t.x,
    y: t.y,
    xref: 'x',
    yref: 'y',
    //sizex: baseSize - (rankRange > 0 ? 0.5*(t.last_mlb_rank - minRank) / rankRange * baseSize : 0),
    //sizey: baseSize - (rankRange > 0 ? 0.5*(t.last_mlb_rank - minRank) / rankRange * baseSize : 0),
    sizex: 3,
    sizey: 3,
    xanchor: 'center',
    yanchor: 'middle',
    layer: 'above',
    name: t.code          // not shown, but handy to carry along
  }));

  await Plotly.relayout(figDiv, { images });

  // (Optional) If you want hover tooltips, add a transparent scatter on top with text:
    const hoverTrace = {
        x: teams.map(t => t.x),
        y: teams.map(t => t.y),
        mode: 'markers',
        marker: { size: 20, opacity: 0 }, // invisible hover targets
        text: teams.map(t => `${t.code} <br> Rank: ${t.last_mlb_rank} <br> Cluster: ${7-t.cluster} <br> Avg Cluster Rank: ${t.avg_last_mlb_rank.toFixed(2)}`),
        hovertemplate: '%{text}<extra></extra>'
    };
    await Plotly.addTraces(figDiv, hoverTrace);

    // remove axis ticks and tickmarks, keep grid lines
    await Plotly.relayout(figDiv, {
        'xaxis.showticklabels': false,
        'yaxis.showticklabels': false,
        'xaxis.ticks': '',
        'yaxis.ticks': ''
    });

    // remove legend
    await Plotly.relayout(figDiv, {
        'showlegend': false
    });


}
async function getLastRankForTeam(teamFullName) {
    const teamCode = TMS[teamFullName]
    const standings = await fetch(`/standings`).then(res => res.json());
    // filer by tema id
    const teamStandings = standings.standings.filter(item => item.team_name === teamFullName);
    // get the entry with the highest date
    const latestEntry = teamStandings.reduce((latest, entry) => {
        const entryDate = new Date(entry.date);
        return entryDate > new Date(latest.date) ? entry : latest;
    }, teamStandings[0]);
    return latestEntry ? latestEntry.mlb_rank : null;
}

async function getLastWinPctForTeam(teamFullName) {
    const teamCode = TMS[teamFullName]
    const standings = await fetch(`/standings`).then(res => res.json());
    // filer by tema id
    const teamStandings = standings.standings.filter(item => item.team_name === teamFullName);
    // get the entry with the highest date
    const latestEntry = teamStandings.reduce((latest, entry) => {
        const entryDate = new Date(entry.date);
        return entryDate > new Date(latest.date) ? entry : latest;
    }, teamStandings[0]);
    return latestEntry ? latestEntry.winning_pct : null;
}

async function getTeamLogo(teamFullName) {
    const teamCode = TMS[teamFullName];
    const logoURL = `/logo?team=${teamCode}`;
    const response = await fetch(logoURL).then(res => res.json());
    return response.logo;
}

function groupByCluster(teams) {
  const byCluster = new Map();
  for (const t of teams) {
    if (!byCluster.has(t.cluster)) byCluster.set(t.cluster, []);
    byCluster.get(t.cluster).push(t);
  }
  return byCluster;
}

// 2) Build one contour trace per cluster
function buildClusterContours(teams) {
  const byCluster = new Map();
  for (const t of teams) {
    if (!byCluster.has(t.cluster)) byCluster.set(t.cluster, []);
    byCluster.get(t.cluster).push(t);
  }

  const colors = ['blue', 'red', 'green', 'purple', 'orange', 'teal', 'brown'];

  const traces = [];
  let i = 0;
  for (const [clusterId, arr] of byCluster.entries()) {
    const xs = arr.map(t => t.x);
    const ys = arr.map(t => t.y);

    traces.push({
      type: 'histogram2dcontour',
      name: `Cluster ${clusterId}`,
      x: xs,
      y: ys,
      ncontours: 10,                 // how many contour rings per cluster
      contours: { coloring: 'lines' }, // ONLY lines, no fill
      line: { color: colors[i % colors.length], width: 2 },
      showscale: false,
      hoverinfo: 'skip',
      opacity: 0.2
    });
    i++;
  }
  return traces;
}

// helper functions
function getTeamFullNameFromCode(teamCode,TEAMS,TMS) {
    const teamId = Object.keys(TMS).find(id => TMS[id] === teamCode);
    return TEAMS[teamId];
}

function getCodeFromFullName(teamFullName,TEAMS,TMS) {
    const teamId = Object.keys(TEAMS).find(id => TEAMS[id] === teamFullName);
    return TMS[teamId];
}

// function to add an image dot to a plotly chart
function addImageDot(figDiv, imageSrc, x, y, sizeScale = 0.5) {
  const images = (figDiv.layout && figDiv.layout.images) ? figDiv.layout.images.slice() : [];
  images.push({
    source: imageSrc,
    x, y,
    xref: 'x', yref: 'y',
    sizex: sizeScale, sizey: sizeScale,
    xanchor: 'center', yanchor: 'middle',
    layer: 'above'
  });
  return Plotly.relayout(figDiv, { images });
}

// 6b. 3D Cluster function (scatter3d with team-code markers)
async function getClusters2(chart_div, zMetric = "winpct") {
  const figDiv = document.getElementById(chart_div);

  // 1) Fetch cluster data once
  const data = await fetch(`/clusters`).then(res => res.json());

  // 2) Build team objects in parallel (awaited correctly)
  const teamPromises = [];
  for (const cluster of data.clusters) {
    for (const teamFullName of cluster.teams) {
      teamPromises.push((async () => {
        const jitter = (2 * Math.random() - 1); // small jitter to avoid perfect overlap
        const lastRank = await getLastRankForTeam(teamFullName);
        const winPct   = await getLastWinPctForTeam(teamFullName); // for z
        const code     = TMS[teamFullName];

        // choose z by metric (easy to extend later)
        let z = null;
        if (zMetric === "winpct")      z = winPct;                       // 0..1
        else if (zMetric === "rankz")  z = lastRank ? 1 / lastRank : NaN; // example alt
        else                           z = winPct;

        return {
          code,
          teamFullName,
          cluster: cluster.cluster,
          avg_last_mlb_rank: cluster.avg_last_mlb_rank,
          last_mlb_rank: lastRank,
          x: cluster.avg_last_mlb_rank + jitter * 0.25,
          y: (lastRank ?? NaN) + jitter * 0.25,
          z
        };
      })());
    }
  }

  const teams = (await Promise.all(teamPromises))
    .filter(t => Number.isFinite(t.y) && Number.isFinite(t.z));

  // Early out if nothing to plot
  if (teams.length === 0) {
    await Plotly.newPlot(figDiv, [], {title: "No data for 3D clusters"});
    return [];
  }

  // Color per cluster
  const clusterColors = [
    "#2563eb", "#ef4444", "#10b981", "#7c3aed", "#f59e0b", "#0d9488", "#92400e"
  ];
  const colorFor = c => clusterColors[(c ?? 0) % clusterColors.length];

  // Split into traces per cluster for legend filtering
  const byCluster = new Map();
  for (const t of teams) {
    if (!byCluster.has(t.cluster)) byCluster.set(t.cluster, []);
    byCluster.get(t.cluster).push(t);
  }

  const traces = [];
  for (const [cid, arr] of byCluster.entries()) {
    traces.push({
      type: "scatter3d",
      mode: "markers+text",
      name: `Cluster ${cid}`,
      x: arr.map(t => t.x),
      y: arr.map(t => t.y),
      z: arr.map(t => t.z),
      text: arr.map(t => t.code),                 // readable labels instead of logos
      textposition: "top center",
      marker: {
        size: 6,
        opacity: 0.95,
        color: colorFor(cid),
        line: { width: 1 }
      },
      hovertemplate:
        "<b>%{text}</b><br>" +
        "Avg last MLB rank: %{x:.2f}<br>" +
        "Latest MLB rank: %{y:.2f}<br>" +
        (zMetric === "winpct"
          ? "Latest Win%: %{z:.3f}<br>"
          : `Z (${zMetric}): %{z:.3f}<br>`) +
        "Cluster: %{meta}<extra></extra>",
      meta: cid
    });
  }

  // Ranges & axis labels
  const xs = teams.map(t => t.x);
  const ys = teams.map(t => t.y);
  const zs = teams.map(t => t.z);
  const pad = 0.5;

  const layout = {
    margin: { l: 0, r: 0, t: 30, b: 0 },
    scene: {
      xaxis: {
        title: "Average of last MLB ranks",
        range: [Math.min(...xs) - pad, Math.max(...xs) + pad],
        zeroline: false
      },
      yaxis: {
        title: "Latest MLB rank",
        // ranks: smaller is better; flip so 'up = better' if you want:
        // autorange: "reversed",  // uncomment if you prefer reversed in 3D too
        range: [Math.min(...ys) - pad, Math.max(...ys) + pad],
        zeroline: false
      },
      zaxis: {
        title: (zMetric === "winpct" ? "Latest Winning %" : `Z (${zMetric})`),
        range: [Math.min(...zs), Math.max(...zs)],
        tickformat: (zMetric === "winpct" ? ".2%" : ".3f"),
        zeroline: false
      },
      camera: { eye: { x: 1.6, y: 1.4, z: 0.8 } },
      dragmode: "orbit",
    },
    legend: { orientation: "h" },
  };

  const images = teams.map(t => ({
    source: t.logo,       // base64 or URL
    x: t.x,
    y: t.y,
    xref: 'x',
    yref: 'y',
    sizex: 4,           // your scale here; axis-units
    sizey: 4,
    xanchor: 'center',
    yanchor: 'middle',
    layer: 'above',
    name: t.code          // not shown, but handy to carry along
  }));

  await Plotly.relayout(figDiv, { images });

  await Plotly.newPlot(figDiv, traces, layout, {displayModeBar: true});

  // (Optional) return teams for downstream use
  return teams;
}

// 7. Compare functions

async function getSimilarity(code, checkboxContainerId, modeName, chart_div, noMarkers = false, drawLine = false, drawShading = false, typeClass="team-checkbox"){
    // check if two teams are selected
    const selectedTeams = Array.from(
        document.querySelectorAll(`#${checkboxContainerId} input.${typeClass}:checked`)
    ).map(checkbox => checkbox.value);
    if (selectedTeams.length !== 2) {
        // clear the chart div
        document.getElementById(chart_div).innerHTML = "<p style='color:red;'>Please select exactly two teams for comparison.</p>";
        console.log("Please select exactly two teams for comparison.");
        return;
    }
    // if two teams are selected, proceed, remove the red text and run getRankings
    document.getElementById(chart_div).innerHTML = "";
    getRankings(code, checkboxContainerId, modeName, chart_div, noMarkers = false, drawLine = false, drawShading = false, typeClass="team-checkbox");
}

async function getSimilarityData(containerId){
    console.log(`Getting similarity data for container ${containerId}`);
    const selectedTeams = Array.from(
        document.querySelectorAll(`#${containerId}-box input.team-checkbox:checked`)
    ).map(checkbox => checkbox.value);

    if (selectedTeams.length !== 2) {
        console.log(selectedTeams);
        return null;
    }
    const teamA = selectedTeams[0];
    const teamB = selectedTeams[1];
    // find name of selected mode radio button inside containerId + "-box"
    const mode = document.querySelector(`#${containerId}-box input[name^="mode"]:checked`) ? document.querySelector(`#${containerId}-box input[name^="mode"]:checked`).value : "power";
    const query = `team_a=${teamA}&team_b=${teamB}&source=${mode}`;
    const data = await fetch(`/similarity?${query}`).then(res => res.json());
    // return a string of inner HTML to fill a div
    const stats = data.similarity_stats;
    const string = `
        <p class="similarity-team-a"><strong>Team A:</strong> ${stats.team_a} (${teamA})</p>
        <p class="similarity-team-b"><strong>Team B:</strong> ${stats.team_b} (${teamB})</p>
        <p class="similarity-source"><strong>Ranking Type:</strong> ${stats.source.toUpperCase()}</p>
        <p class="similarity-avg-abs-rank-gap"><strong>Average Rank Difference:</strong> ${stats.avg_abs_rank_gap.toFixed(2)}</p>
        <p class="similarity-corr-delta"><strong>Similarity in Week by Week Changes:</strong> ${stats.corr_delta.toFixed(2)*100}%</p>
        <p class="similarity-corr-levels"><strong>Overall Trend Similarity:</strong> ${stats.corr_levels.toFixed(2)*100}%</p>
        <p class="similarity-dtw-similarity-z"><strong>Overall Trajectory Similarity:</strong> ${stats.dtw_similarity_z.toFixed(2)}%</p>
    `;
    console.log(string)
    return string;
}

// 8. HMM functions

async function getHmm(code, checkboxContainerId, modeName, chart_div, noMarkers = false, drawLine = false, drawShading = false, typeClass="team-radio"){
    await getRankings(code, checkboxContainerId, modeName, chart_div, noMarkers = false, drawLine = false, drawShading = false, typeClass="team-radio");
    const el = document.getElementById(chart_div);
    // get hmm data
    const selectedTeams = Array.from(
        document.querySelectorAll(`#${checkboxContainerId} input.${typeClass}:checked`)
    ).map(input => input.value);

    const hmmData = await fetch(`/hmm?team=${selectedTeams[0]}`).then(res => res.json());
    const states = hmmData.states;
    const stats = hmmData.stats;
    const state_color_map = {
        0: "#77DD77",  // pastel green
        1: "#FDFD96",  // pastel yellow
        2: "#FF6961"   // pastel red
    };
    // Plotly.restyle(chart_div, { 'marker.color': 'green' });
    // change marker color based on state
    const newColors = states.map(s => state_color_map[s.state] || "#000000");
    // add black to newColors because initial state is null
    newColors.unshift("#000000");
    console.log(newColors);
    Plotly.restyle(el, { 'marker.color': [newColors] });
    // change hovertemplate to include state label
    const newHoverTemplate = states.map(s =>
        `State: ${s.label}<br>` +
        `Rank: %{y}<extra></extra>`
    );
    Plotly.restyle(el, { 'hovertemplate': [newHoverTemplate] });
    // larger markers
    Plotly.restyle(el, { 'marker.size': 12 });
    // give markers edges of same color but darker
    const darkerColors = states.map(s => {
        const color = state_color_map[s.state] || "#000000";
        // convert hex to rgb
        const r = parseInt(color.slice(1, 3), 16);
        const g = parseInt(color.slice(3, 5), 16);
        const b = parseInt(color.slice(5, 7), 16);
        // darken by 30%
        const factor = 0.7;
        const r2 = Math.max(0, Math.min(255, Math.floor(r * factor)));
        const g2 = Math.max(0, Math.min(255, Math.floor(g * factor)));
        const b2 = Math.max(0, Math.min(255, Math.floor(b * factor)));
        return `rgb(${r2},${g2},${b2})`;
    });
    // add black to darkerColors because initial state is null
    darkerColors.unshift("#000000");
    Plotly.restyle(el, { 'marker.line.color': [darkerColors], 'marker.line.width': 2 });
    // Remove everytihng from legend. Make new legend with states only
    
    Plotly.restyle(el, { showlegend: false });

    // Make sure the legend itself is on (and disable toggling if you want)
    Plotly.relayout(el, { 
    showlegend: true,
    legend: { itemclick: false, itemdoubleclick: false }
    });

    // Add state legend chips as dummy marker traces (not greyed out)
    const legendTraces = [];
    for (const state of Object.keys(state_color_map).map(Number).sort((a, b) => a - b)) {
    const color = state_color_map[state];
    legendTraces.push({
        type: 'scatter',
        mode: 'markers',
        x: [null], y: [null],          // nothing gets drawn on the axes
        showlegend: true,
        name: stats.P_labels[state],
        hoverinfo: 'skip',
        marker: {
        size: 12,
        color: color,
        line: { width: 2, color: color }
        }
    });
    }
    Plotly.addTraces(el, legendTraces);
    // position legend at bottom left
    Plotly.relayout(el, { 
    legend: { x: 0, y: -0.2, orientation: 'h' }
    });
}

async function getHmmData(containerId){
    const selectedTeams = Array.from(
        document.querySelectorAll(`#${containerId}-box input.team-radio:checked`)
    ).map(checkbox => checkbox.value);
    console.log(selectedTeams);
    const query = `team=${selectedTeams[0]}`;
    const hmmData = await fetch(`/hmm?${query}`).then(res => res.json());
    // create a state array of the states
    const stateArray = hmmData.states.map(s => s.state);
    console.log(stateArray);
    // get final state
    const finalState = hmmData.states[hmmData.states.length - 1];
    const string = `<p class="hmm-team"><strong>Team:</strong> ${getTeamFullNameFromCode(selectedTeams[0],TEAMS,TMS)}</p>
    <p class="hmm-prob-good"><strong>Probability of the team performing well next week:</strong> ${getProbfromTransitionMatrix(hmmData.stats.P, finalState.state, 0)}%</p>
    <p class="hmm-prob-mediocre"><strong>Probability of the team performing mediocre next week:</strong> ${getProbfromTransitionMatrix(hmmData.stats.P, finalState.state, 1)}%</p>
    <p class="hmm-prob-bad"><strong>Probability of the team performing poorly next week:</strong> ${getProbfromTransitionMatrix(hmmData.stats.P, finalState.state, 2)}%</p>
    `;
    return string;

}

function getProbfromTransitionMatrix(P, fromState, toState) {
    console.log(fromState, toState);
    let Probability = P[fromState][toState];
    // round to 2 decimal places
    Probability = (Probability * 100).toFixed(2);
    return Probability;
}

function getProbfromTransitionMatrixFromBeginning(P, toState, stateArray) {
    let prob = 1.0;
    for (let i = 0; i < stateArray.length - 1; i++) {
        const from = stateArray[i];
        const to = stateArray[i + 1];
        prob *= P[from][to];
    }
    // finally multiply by the probability of going from last state to toState
    prob *= P[stateArray[stateArray.length - 1]][toState];
    return prob;
}

// Design functions

// function that detects every radio and chechbox with team-checkbox or team-radio class
// 1. remove the actual checkbox/radio input
// 2. Remove the label text
// 3. Add the team logo as background image to the label
function styleTeamSelectors() {
    const checkboxes = document.querySelectorAll('input.team-checkbox, input.team-radio');
    checkboxes.forEach(checkbox => {
        const label = document.querySelector(`label[for="${checkbox.id}"]`);
        if (label) {
            // get team code from checkbox value
            const teamCode = checkbox.value;
            // get logo url from data-logo attribute
            const logoUrl = checkbox.dataset.logo;
            // remove checkbox/radio input
            checkbox.style.display = 'none';
            // remove label text
            label.innerHTML = '';
            // add team logo as background image to label
            label.style.backgroundImage = `url(${logoUrl})`;
        }
    });
    // color each .team-checkbox-container-main and .team-radio-container-main div based on the current selection's data-pcolor or data-scolor depending on data-association
    // for team-checkbox-container-main, create an array of all checkboxes inside it that are checked, then get their data-pcolor or data-scolor and set the background color of the container to a gradient of those colors
    // for team-radio-container-main, get the checked radio button inside it, then get its data-pcolor or data-scolor and set the background color of the container to that color
    const checkboxContainers = document.querySelectorAll('.team-checkbox-container-main');
    checkboxContainers.forEach(container => {
        const checkedCheckboxes = container.querySelectorAll('input.team-checkbox:checked');
        if (checkedCheckboxes.length > 0) {
            const colors = Array.from(checkedCheckboxes).map(checkbox => {
                const association = checkbox.dataset.association;
                return (association === "primary" ? checkbox.dataset.pcolor : checkbox.dataset.scolor);
            });
            // create a gradient from those colors
            const gradient = `linear-gradient(45deg, ${colors.join(', ')})`;
            container.style.backgroundImage = gradient;
            container.style.backgroundColor = 'white';
        } else {
            container.style.backgroundImage = 'none';
        }
    });
    const radioContainers = document.querySelectorAll('.team-radio-container-main');
    radioContainers.forEach(container => {
        const checkedRadio = container.querySelector('input.team-radio:checked');
        if (checkedRadio) {
            const association = checkedRadio.dataset.association;
            const color = (association === "primary" ? checkedRadio.dataset.pcolor : checkedRadio.dataset.scolor);
            container.style.backgroundColor = color;
        }
        else {
            container.style.backgroundColor = 'transparent';
        }
    });
}
        
// transparent paper
// after all charts are loaded, make their background transparent by adding to their layout: paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)'
function makeChartsTransparent() {
   const charts = document.querySelectorAll('.plotly-graph-div');
    charts.forEach(chart => {
        Plotly.relayout(chart, { paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)' });
    });
}