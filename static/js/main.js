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
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to generate questions');
        }

        if (!data.success || !Array.isArray(data.questions) || data.questions.length === 0) {
            throw new Error('Invalid response format');
        }

        questions = data.questions;
        displayCurrentQuestion();

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('question').innerHTML = `
            <div class="error-message">
                <p>Failed to generate interview questions. Please try again.</p>
                <button onclick="window.location.reload()" class="btn">Retry</button>
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
            if (data.is_final) {
                window.location.href = '/feedback';
            } else {
                if (data.score) {
                    displayScore(data.score);
                    displayFeedback(data.feedback);
                }
                
                setTimeout(() => {
                    currentQuestionIndex++;
                    displayCurrentQuestion();
                    document.getElementById('response').value = '';
                    clearFeedbackDisplay();
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

function displayScore(score) {
    if (!score) return;
    
    const scoreElement = document.getElementById('score');
    scoreElement.style.display = 'block';
    scoreElement.innerHTML = `
        <div class="score-details">
            <h3>Score Breakdown:</h3>
            <div class="score-item">
                <label>Technical Understanding:</label>
                <div class="score-bar">
                    <div class="score-fill" style="width: ${score.technical_score || 0}%"></div>
                </div>
                <span>${score.technical_score || 0}%</span>
            </div>
            <div class="score-item">
                <label>Communication:</label>
                <div class="score-bar">
                    <div class="score-fill" style="width: ${score.communication_score || 0}%"></div>
                </div>
                <span>${score.communication_score || 0}%</span>
            </div>
            <div class="score-item">
                <label>Confidence:</label>
                <div class="score-bar">
                    <div class="score-fill" style="width: ${score.confidence_score || 0}%"></div>
                </div>
                <span>${score.confidence_score || 0}%</span>
            </div>
            <div class="score-total">
                <h4>Total Score: ${score.total_score || 0}%</h4>
            </div>
        </div>
    `;
}

function displayFeedback(feedback) {
    if (!feedback) return;
    
    const feedbackElement = document.getElementById('feedback');
    feedbackElement.style.display = 'block';
    feedbackElement.innerHTML = `
        <h3>Feedback:</h3>
        <ul>
            ${Array.isArray(feedback) ? feedback.map(f => `<li>${f}</li>`).join('') : ''}
        </ul>
    `;
}

function clearFeedbackDisplay() {
    const scoreElement = document.getElementById('score');
    const feedbackElement = document.getElementById('feedback');
    
    if (scoreElement) {
        scoreElement.style.display = 'none';
        scoreElement.innerHTML = '';
    }
    
    if (feedbackElement) {
        feedbackElement.style.display = 'none';
        feedbackElement.innerHTML = '';
    }
}

function displayCurrentQuestion() {
    const questionElement = document.getElementById('question');
    const progressText = document.getElementById('progressText');
    const progressBar = document.querySelector('.progress');
    
    if (currentQuestionIndex < questions.length) {
        questionElement.textContent = questions[currentQuestionIndex];
        progressText.textContent = `Question ${currentQuestionIndex + 1} of ${questions.length}`;
        progressBar.style.width = `${((currentQuestionIndex + 1) / questions.length) * 100}%`;
    }
}

// Initialize questions when the page loads
document.addEventListener('DOMContentLoaded', function() {
    fetch('/get_questions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
    })
    .then(res => res.json())
    .then(data => {
        if (data.success && data.questions) {
            questions = data.questions;
            displayCurrentQuestion();
        } else {
            throw new Error(data.error || 'Failed to get questions');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to load interview questions. Please refresh the page.');
    });
});

document.getElementById('resumeForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const submitButton = document.querySelector('.btn-primary');
    const loadingDiv = document.getElementById('loading');
    
    // Show loading state
    submitButton.disabled = true;
    loadingDiv.style.display = 'block';
    
    try {
        const response = await fetch('/upload_resume', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success && data.redirect) {
            window.location.href = data.redirect;
        } else if (data.error) {
            alert(data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while processing your resume');
    } finally {
        submitButton.disabled = false;
        loadingDiv.style.display = 'none';
    }
});
