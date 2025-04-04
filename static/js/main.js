// Main application logic
document.addEventListener("DOMContentLoaded", function () {
    // Initialize based on current page
    if (document.getElementById("resumeForm")) {
        initHomePage();
    } else if (document.getElementById("questionText")) {
        initInterviewPage();
    } else if (document.getElementById("totalScore")) {
        initFeedbackPage();
    } else if (document.getElementById("leaderboardBody")) {
        initLeaderboardPage();
    }
});

function initHomePage() {
    const resumeForm = document.getElementById("resumeForm");
    const loading = document.getElementById("loading");

    resumeForm.addEventListener("submit", function (e) {
        e.preventDefault();

        const fileInput = document.getElementById("resume");
        if (!fileInput.files.length) {
            alert("Please select a resume file");
            return;
        }

        loading.style.display = "block";

        const formData = new FormData();
        formData.append("resume", fileInput.files[0]);

        fetch("/upload_resume", {
            method: "POST",
            body: formData,
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then((data) => {
                if (data.success) {
                    window.location.href = data.redirect;
                } else {
                    alert(
                        "Error: " + (data.error || "Failed to upload resume")
                    );
                }
            })
            .catch((error) => {
                console.error("Error:", error);
                alert("Failed to upload resume. Please make sure the server is running.");
                loading.style.display = "none";
            });
    });
}

let questions = [];
let currentQuestionIndex = 0;

async function initInterviewPage() {
    try {
        // Show loading state
        const questionElement = document.getElementById('question');
        questionElement.innerHTML = `
            <div class="loading-questions">
                <p>Generating personalized interview questions...</p>
                <div class="loader"></div>
            </div>
        `;

        const response = await fetch('/get_questions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        });

        const data = await response.json();
        console.log('Response data:', data); // Debug log

        if (!response.ok) {
            throw new Error(data.error || `HTTP error! status: ${response.status}`);
        }

        if (data.success && Array.isArray(data.questions) && data.questions.length > 0) {
            questions = data.questions;
            displayCurrentQuestion();
        } else {
            throw new Error('Invalid questions format received');
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('question').innerHTML = `
            <div class="error-message">
                <p>${error.message || 'Error loading questions. Please try again.'}</p>
                <button onclick="window.location.href='/'" class="btn">Return to Home</button>
            </div>
        `;
    }
}

function displayCurrentQuestion() {
    const questionElement = document.getElementById('question');
    const progressText = document.getElementById('progressText');
    const progressBar = document.querySelector('.progress');
    
    if (questions.length > 0 && currentQuestionIndex < questions.length) {
        // Display the current question with formatting
        questionElement.innerHTML = `
            <div class="question-content">
                <h3>Question ${currentQuestionIndex + 1}:</h3>
                <p>${questions[currentQuestionIndex]}</p>
            </div>
        `;
        
        // Update progress
        progressText.textContent = `Question ${currentQuestionIndex + 1} of ${questions.length}`;
        const progressPercentage = ((currentQuestionIndex + 1) / questions.length) * 100;
        progressBar.style.width = `${progressPercentage}%`;
    }
}

function submitAnswer() {
    const responseText = document.getElementById('response').value;
    if (!responseText.trim()) {
        alert('Please provide an answer');
        return;
    }

    // Show loading state
    const submitButton = document.querySelector('button.btn');
    submitButton.disabled = true;
    submitButton.textContent = 'Analyzing...';

    fetch('/analyze_response', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            question: questions[currentQuestionIndex],
            response: responseText
        }),
        credentials: 'same-origin'
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            displayFeedback(data.feedback);
            displayScore(data.score);
            
            if (data.is_final) {
                showFinalScore(data.final_score);
            } else {
                setTimeout(() => {
                    currentQuestionIndex++;
                    displayCurrentQuestion();
                    document.getElementById('response').value = '';
                    clearFeedback();
                }, 3000);
            }
        } else {
            throw new Error(data.error || 'Failed to analyze response');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to submit answer. Please try again.');
    })
    .finally(() => {
        submitButton.disabled = false;
        submitButton.textContent = 'Submit Answer';
    });
}

function displayFeedback(feedback) {
    const feedbackElement = document.getElementById('feedback');
    feedbackElement.style.display = 'block';
    feedbackElement.innerHTML = `
        <h3>Feedback:</h3>
        <ul>
            ${Array.isArray(feedback) ? feedback.map(f => `<li>${f}</li>`).join('') : ''}
        </ul>
    `;
}

function displayScore(score) {
    const scoreElement = document.getElementById('score');
    scoreElement.style.display = 'block';
    scoreElement.innerHTML = `
        <div class="score-details">
            <h3>Score Breakdown:</h3>
            <div class="score-item">
                <label>Technical Understanding:</label>
                <div class="score-bar">
                    <div class="score-fill" style="width: ${score.technical_score}%"></div>
                </div>
                <span>${score.technical_score}%</span>
            </div>
            <div class="score-item">
                <label>Communication:</label>
                <div class="score-bar">
                    <div class="score-fill" style="width: ${score.communication_score}%"></div>
                </div>
                <span>${score.communication_score}%</span>
            </div>
            <div class="score-item">
                <label>Confidence:</label>
                <div class="score-bar">
                    <div class="score-fill" style="width: ${score.confidence_score}%"></div>
                </div>
                <span>${score.confidence_score}%</span>
            </div>
            <div class="score-total">
                <h4>Total Score: ${score.total_score}%</h4>
            </div>
        </div>
    `;
}

function showFinalScore(finalScore) {
    const container = document.querySelector('.question-section');
    container.innerHTML = `
        <h2>Interview Complete!</h2>
        <div class="final-score">
            <div class="score-circle">
                <h3>Final Score: ${finalScore.total_score.toFixed(1)}%</h3>
            </div>
            <div class="score-breakdown">
                <h3>Performance Breakdown:</h3>
                <div class="score-item">
                    <label>Technical Knowledge:</label>
                    <div class="score-bar">
                        <div class="score-fill" style="width: ${finalScore.technical_score}%"></div>
                    </div>
                    <span>${finalScore.technical_score.toFixed(1)}%</span>
                </div>
                <div class="score-item">
                    <label>Communication Skills:</label>
                    <div class="score-bar">
                        <div class="score-fill" style="width: ${finalScore.communication_score}%"></div>
                    </div>
                    <span>${finalScore.communication_score.toFixed(1)}%</span>
                </div>
                <div class="score-item">
                    <label>Overall Performance:</label>
                    <div class="score-bar">
                        <div class="score-fill" style="width: ${finalScore.overall_score}%"></div>
                    </div>
                    <span>${finalScore.overall_score.toFixed(1)}%</span>
                </div>
            </div>
        </div>
        <a href="/feedback" class="btn">View Detailed Feedback</a>
    `;
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', initInterviewPage);
