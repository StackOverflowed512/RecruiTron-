// Video analysis functionality
let videoAnalysisInterval;

function startVideoAnalysis() {
    const video = document.getElementById("videoElement");
    const canvas = document.getElementById("canvasElement");
    const eyeContactMetric = document.getElementById("eyeContactMetric");
    const expressionMetric = document.getElementById("expressionMetric");

    // Analyze video frames periodically
    videoAnalysisInterval = setInterval(() => {
        if (video.readyState === video.HAVE_ENOUGH_DATA) {
            // Capture frame
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas
                .getContext("2d")
                .drawImage(video, 0, 0, canvas.width, canvas.height);

            // Convert to base64 for sending to server
            const imageData = canvas.toDataURL("image/jpeg");

            // Send to server for analysis
            fetch("/analyze_video_frame", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ image_data: imageData }),
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data) {
                        // Update UI with metrics
                        eyeContactMetric.querySelector(
                            ".metric-value"
                        ).textContent = `${data.eye_contact}%`;
                        expressionMetric.querySelector(
                            ".metric-value"
                        ).textContent = data.facial_expression;

                        // Visual feedback
                        updateVideoFeedback(data);
                    }
                });
        }
    }, 2000); // Analyze every 2 seconds
}

function updateVideoFeedback(data) {
    // Implement visual feedback based on video analysis
    // For example, change colors based on metrics
    const eyeContactElement = document.getElementById("eyeContactMetric");
    const expressionElement = document.getElementById("expressionMetric");

    // Eye contact feedback
    if (data.eye_contact > 75) {
        eyeContactElement.style.color = "#4CAF50"; // Green
    } else if (data.eye_contact > 50) {
        eyeContactElement.style.color = "#FFC107"; // Yellow
    } else {
        eyeContactElement.style.color = "#F44336"; // Red
    }

    // Expression feedback
    switch (data.facial_expression.toLowerCase()) {
        case "happy":
            expressionElement.style.color = "#4CAF50";
            break;
        case "neutral":
            expressionElement.style.color = "#2196F3";
            break;
        default:
            expressionElement.style.color = "#F44336";
    }
}

function stopVideoAnalysis() {
    clearInterval(videoAnalysisInterval);
}

// Start analysis when page loads
document.addEventListener("DOMContentLoaded", function () {
    if (document.getElementById("videoElement")) {
        startVideoAnalysis();
    }
});
