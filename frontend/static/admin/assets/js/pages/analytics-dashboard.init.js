/** @format */

// Series (số lượng log theo ngày)
series: [
    {
        name: 'Logs',
        data: [12, 15, 18, 11, 22, 9, 17],
    },
];

// Labels (ngày tương ứng)
xaxis: {
    categories: [
        '2025-06-18',
        '2025-06-19',
        '2025-06-20',
        '2025-06-21',
        '2025-06-22',
        '2025-06-23',
        '2025-06-24',
    ];
}
var options = {
    chart: { type: 'area', height: 45, sparkline: { enabled: true } },
    series: [{ name: 'Logs', data: [12, 15, 18, 11, 22, 9, 17] }],
    xaxis: {
        categories: [
            '2025-06-18',
            '2025-06-19',
            '2025-06-20',
            '2025-06-21',
            '2025-06-22',
            '2025-06-23',
            '2025-06-24',
        ],
        type: 'datetime',
    },
    stroke: { width: 2, curve: 'smooth' },
    fill: { opacity: 0.16, type: 'solid' },
    tooltip: { theme: 'light' },
    colors: ['#537AEF'],
};

new ApexCharts(document.querySelector('#website-visitors'), options).render();
