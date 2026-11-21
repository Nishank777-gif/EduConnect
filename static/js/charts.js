/**
 * EduConnect - Interactive Statistics & Charts
 * Powered by Chart.js and MySQL Dynamic API (/api/stats)
 */

document.addEventListener('DOMContentLoaded', function () {
    let votesPieChart = null;
    let ratingsBarChart = null;

    const refreshBtn = document.getElementById('refresh-btn');
    const liveIndicator = document.getElementById('live-indicator');

    // Color palette for charts
    const chartColors = [
        '#2563eb', '#0d9488', '#8b5cf6', '#f59e0b', '#ec4899',
        '#06b6d4', '#10b981', '#6366f1', '#f97316', '#64748b'
    ];

    /**
     * Fetch statistics from the Flask /api/stats endpoint
     */
    async function fetchAndUpdateStats() {
        try {
            if (liveIndicator) {
                liveIndicator.style.opacity = '0.5';
            }

            const response = await fetch('/api/stats');
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();

            // 1. Update KPI Summary Counters
            if (document.getElementById('stat-students')) {
                document.getElementById('stat-students').innerText = data.total_students;
            }
            if (document.getElementById('stat-votes')) {
                document.getElementById('stat-votes').innerText = data.total_votes;
            }
            if (document.getElementById('stat-courses')) {
                document.getElementById('stat-courses').innerText = data.total_courses;
            }
            if (document.getElementById('stat-platforms')) {
                document.getElementById('stat-platforms').innerText = data.total_platforms;
            }

            // 2. Extract Chart Data
            const labels = data.top_organizations.map(org => org.name);
            const votesData = data.top_organizations.map(org => org.total_votes);
            const ratingsData = data.top_organizations.map(org => org.rating);

            // 3. Render or Update Votes Pie / Doughnut Chart
            renderVotesChart(labels, votesData);

            // 4. Render or Update Ratings Bar Chart
            renderRatingsChart(labels, ratingsData);

            if (liveIndicator) {
                liveIndicator.style.opacity = '1';
            }
        } catch (error) {
            console.error('Error fetching statistics:', error);
            if (liveIndicator) {
                liveIndicator.style.opacity = '1';
            }
        }
    }

    /**
     * Render or Update the Votes Pie / Doughnut Chart
     */
    function renderVotesChart(labels, votesData) {
        const ctx = document.getElementById('votesPieChart');
        if (!ctx) return;

        if (votesPieChart) {
            votesPieChart.data.labels = labels;
            votesPieChart.data.datasets[0].data = votesData;
            votesPieChart.update();
            return;
        }

        votesPieChart = new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: votesData,
                    backgroundColor: chartColors,
                    borderWidth: 2,
                    borderColor: '#ffffff',
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 14,
                            padding: 10,
                            font: {
                                size: 11
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const value = context.raw;
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return ` ${context.label}: ${value} votes (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * Render or Update the Platform Ratings Bar Chart
     */
    function renderRatingsChart(labels, ratingsData) {
        const ctx = document.getElementById('ratingsBarChart');
        if (!ctx) return;

        if (ratingsBarChart) {
            ratingsBarChart.data.labels = labels;
            ratingsBarChart.data.datasets[0].data = ratingsData;
            ratingsBarChart.update();
            return;
        }

        ratingsBarChart = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Student Rating (out of 5.0)',
                    data: ratingsData,
                    backgroundColor: '#2563eb',
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        min: 3.5,
                        max: 5.0,
                        ticks: {
                            stepSize: 0.5
                        },
                        grid: {
                            color: '#f1f5f9'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                size: 10
                            },
                            maxRotation: 45,
                            minRotation: 25
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return ` Rating: ${context.raw} / 5.0`;
                            }
                        }
                    }
                }
            }
        });
    }

    // Manual Refresh Button Event
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function () {
            refreshBtn.innerText = '⏳ Loading...';
            fetchAndUpdateStats().then(() => {
                refreshBtn.innerText = '🔄 Refresh Data';
            });
        });
    }

    // Initial Fetch on page load
    fetchAndUpdateStats();

    // Periodic automatic background refresh every 20 seconds
    setInterval(fetchAndUpdateStats, 20000);
});
