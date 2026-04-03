document.addEventListener('DOMContentLoaded', () => {
    const chartNode = document.getElementById('skill-radar-chart');
    if (!chartNode || typeof Plotly === 'undefined') {
        return;
    }

    const prettyLabels = JSON.parse(chartNode.dataset.prettyLabels || '[]');
    const studentValues = JSON.parse(chartNode.dataset.student || '[]');
    const industryValues = JSON.parse(chartNode.dataset.industry || '[]');
    const theta = [...prettyLabels, prettyLabels[0]];
    const studentR = [...studentValues, studentValues[0]];
    const industryR = [...industryValues, industryValues[0]];

    const data = [
        {
            type: 'scatterpolar',
            r: studentR,
            theta,
            fill: 'toself',
            name: 'Student',
            line: { color: '#4da3ff', width: 3 },
            fillcolor: 'rgba(77, 163, 255, 0.28)',
        },
        {
            type: 'scatterpolar',
            r: industryR,
            theta,
            fill: 'toself',
            name: 'Industry Standard',
            line: { color: '#ff8b3d', width: 3 },
            fillcolor: 'rgba(255, 139, 61, 0.2)',
        },
    ];

    const layout = {
        showlegend: true,
        paper_bgcolor: '#0f1830',
        plot_bgcolor: '#0f1830',
        font: { color: '#f6f7fb', family: 'DM Sans, sans-serif' },
        margin: { t: 30, r: 40, b: 30, l: 40 },
        polar: {
            bgcolor: '#0f1830',
            radialaxis: {
                visible: true,
                range: [0, 10],
                tickfont: { color: '#dce6ff' },
                gridcolor: 'rgba(240, 192, 64, 0.18)',
                linecolor: 'rgba(255, 255, 255, 0.12)',
            },
            angularaxis: {
                tickfont: { size: 13, color: '#f4f1e6' },
                gridcolor: 'rgba(255, 255, 255, 0.08)',
                linecolor: 'rgba(255, 255, 255, 0.12)',
            },
        },
    };

    Plotly.newPlot(chartNode, data, layout, { responsive: true, displayModeBar: false });
});
