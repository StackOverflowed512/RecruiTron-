document.addEventListener('DOMContentLoaded', function() {
    fetch('/get_final_feedback')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayPerformanceChart(data.final_score);
                displayAIFeedback(data.overall_feedback);
            }
        })
        .catch(error => console.error('Error:', error));
});

function displayPerformanceChart(scores) {
    const ctx = document.getElementById('performanceChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Technical Knowledge', 'Communication', 'Confidence', 'Overall Score'],
            datasets: [{
                label: 'Performance Scores',
                data: [
                    scores.technical_score,
                    scores.communication_score,
                    scores.confidence_score,
                    scores.total_score
                ],
                backgroundColor: [
                    'rgba(0, 255, 157, 0.5)',
                    'rgba(108, 99, 255, 0.5)',
                    'rgba(255, 51, 102, 0.5)',
                    'rgba(255, 206, 86, 0.5)'
                ],
                borderColor: [
                    'rgba(0, 255, 157, 1)',
                    'rgba(108, 99, 255, 1)',
                    'rgba(255, 51, 102, 1)',
                    'rgba(255, 206, 86, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#fff'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#fff'
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#fff'
                    }
                }
            }
        }
    });
}

function displayAIFeedback(feedback) {
    document.getElementById('overallAssessment').textContent = feedback.overall_assessment;
    
    const strengthsList = document.getElementById('strengths');
    feedback.strengths.forEach(strength => {
        const li = document.createElement('li');
        li.textContent = strength;
        strengthsList.appendChild(li);
    });
    
    const improvementsList = document.getElementById('improvements');
    feedback.areas_for_improvement.forEach(area => {
        const li = document.createElement('li');
        li.textContent = area;
        improvementsList.appendChild(li);
    });
    
    const recommendationsList = document.getElementById('recommendations');
    feedback.recommendations.forEach(rec => {
        const li = document.createElement('li');
        li.textContent = rec;
        recommendationsList.appendChild(li);
    });
}