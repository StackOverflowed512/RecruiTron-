// Voice analysis functionality
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
const recordButton = document.getElementById("recordAudioBtn");

function startAudioRecording() {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices
            .getUserMedia({ audio: true })
            .then(function (stream) {
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = function (e) {
                    audioChunks.push(e.data);
                };

                mediaRecorder.onstop = function () {
                    const audioBlob = new Blob(audioChunks, {
                        type: "audio/wav",
                    });
                    analyzeAudio(audioBlob);
                };

                mediaRecorder.start();
                isRecording = true;
                recordButton.textContent = "Stop Recording";
                recordButton.classList.add("recording");
            })
            .catch(function (error) {
                console.error("Error accessing microphone:", error);
                recordButton.disabled = true;
                recordButton.textContent = "Mic Not Available";
            });
    } else {
        console.warn("getUserMedia not supported");
        recordButton.disabled = true;
        recordButton.textContent = "Not Supported";
    }
}

function stopAudioRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        recordButton.textContent = "Start Recording";
        recordButton.classList.remove("recording");
    }
}

function analyzeAudio(audioBlob) {
    const reader = new FileReader();
    reader.onload = function () {
        const base64Audio = reader.result.split(",")[1];

        fetch("/analyze_audio", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ audio_data: base64Audio }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data) {
                    updateVoiceFeedback(data);
                }
            });
    };
    reader.readAsDataURL(audioBlob);
}

function updateVoiceFeedback(data) {
    // Implement visual feedback based on voice analysis
    // For example, show metrics or give suggestions
    const feedbackContent = document.getElementById("feedbackContent");

    let feedback = "<h4>Voice Analysis</h4>";
    feedback += `<p>Speech Rate: ${data.speech_rate.toFixed(
        1
    )} words/sec (${data.speech_rate_score.toFixed(0)}%)</p>`;
    feedback += `<p>Volume: ${data.volume.toFixed(
        1
    )} dB (${data.volume_score.toFixed(0)}%)</p>`;
    feedback += `<p>Clarity: ${data.clarity.toFixed(0)}%</p>`;

    feedbackContent.innerHTML += feedback;
}

// Toggle recording
if (recordButton) {
    recordButton.addEventListener("click", function () {
        if (isRecording) {
            stopAudioRecording();
        } else {
            startAudioRecording();
        }
    });
}
