document.addEventListener('DOMContentLoaded', function() {
    fetch('/get_final_feedback')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateScoreChart(data.final_score);
                updateTotalScore(data.final_score.total_score);
                displayFeedback(data.overall_feedback);
            }
        })
        .catch(error => console.error('Error:', error));
});

function updateScoreChart(scores) {
    const ctx = document.getElementById('scoreChart').getContext('2d');
    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Technical', 'Communication', 'Confidence'],
            datasets: [{
                label: 'Score Breakdown',
                data: [
                    scores.technical_score,
                    scores.communication_score,
                    scores.confidence_score
                ],
                backgroundColor: 'rgba(0, 255, 157, 0.2)',
                borderColor: 'rgba(0, 255, 157, 1)',
                pointBackgroundColor: 'rgba(0, 255, 157, 1)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(0, 255, 157, 1)'
            }]
        },
        options: {
            scales: {
                r: {
                    angleLines: {
                        color: 'rgba(255, 255, 255, 0.2)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.2)'
                    },
                    pointLabels: {
                        color: 'rgba(255, 255, 255, 0.8)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.8)',
                        backdropColor: 'transparent'
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: 'rgba(255, 255, 255, 0.8)'
                    }
                }
            }
        }
    });
}

function updateTotalScore(score) {
    const circle = document.querySelector('.score-circle');
    const scoreText = document.querySelector('.total-score');
    const circumference = 2 * Math.PI * 60;
    const offset = circumference - (score / 100) * circumference;
    
    circle.style.strokeDashoffset = offset;
    
    let currentScore = 0;
    const duration = 2000;
    const increment = score / (duration / 16);
    
    const animation = setInterval(() => {
        currentScore += increment;
        if (currentScore >= score) {
            currentScore = score;
            clearInterval(animation);
        }
        scoreText.textContent = Math.round(currentScore);
    }, 16);
}

function displayFeedback(feedback) {
    const lists = {
        'strengthsList': feedback.strengths,
        'improvementsList': feedback.areas_for_improvement,
        'recommendationsList': feedback.recommendations
    };

    for (const [listId, items] of Object.entries(lists)) {
        const list = document.getElementById(listId);
        list.innerHTML = items.map(item => `
            <li class="feedback-item">
                ${item}
            </li>
        `).join('');
    }
}