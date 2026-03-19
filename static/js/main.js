// ============================================
// Image Preview
// ============================================
document.getElementById("imageInput").addEventListener(
    "change",
    function (e) {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = function (e) {
            document.getElementById("imagePreview").src = e.target.result;
            document.getElementById("previewContainer").style.display = "block";
            document.getElementById("dropZone").style.display = "none";
        };
        reader.readAsDataURL(file);
    }
);

// ============================================
// Drag and Drop
// ============================================
const dropZone = document.getElementById("dropZone");

dropZone.addEventListener("dragover", function (e) {
    e.preventDefault();
    dropZone.style.borderColor = "#e63946";
});

dropZone.addEventListener("dragleave", function () {
    dropZone.style.borderColor = "#2d2f45";
});

dropZone.addEventListener("drop", function (e) {
    e.preventDefault();
    dropZone.style.borderColor = "#2d2f45";

    const file = e.dataTransfer.files[0];
    if (file) {
        document.getElementById("imageInput").files = e.dataTransfer.files;
        const reader = new FileReader();
        reader.onload = function (e) {
            document.getElementById("imagePreview").src = e.target.result;
            document.getElementById("previewContainer").style.display = "block";
            dropZone.style.display = "none";
        };
        reader.readAsDataURL(file);
    }
});

// ============================================
// Form Submit
// ============================================
document.getElementById("uploadForm").addEventListener(
    "submit",
    async function (e) {
        e.preventDefault();

        const imageInput = document.getElementById("imageInput");
        if (!imageInput.files[0]) {
            alert("Please select an image first!");
            return;
        }

        // Show loading
        showLoading(true);
        document.getElementById("resultsSection").style.display = "none";
        document.getElementById("analyzeBtn").disabled = true;

        const loadingMessages = [
            "Analyzing image...",
            "Running Google Vision API...",
            "Running AWS Rekognition...",
            "Running Azure Language Analysis...",
            "Generating audio alert..."
        ];

        let msgIndex = 0;
        const msgInterval = setInterval(function () {
            if (msgIndex < loadingMessages.length) {
                document.getElementById("loadingText").textContent =
                    loadingMessages[msgIndex];
                msgIndex++;
            }
        }, 1500);

        // Form data
        const formData = new FormData();
        formData.append("image",    imageInput.files[0]);
        formData.append("location", document.getElementById("location").value);

        try {
            const response = await fetch("/analyze", {
                method: "POST",
                body:   formData
            });

            const data = await response.json();

            clearInterval(msgInterval);
            showLoading(false);
            document.getElementById("analyzeBtn").disabled = false;

            if (data.error) {
                alert("Error: " + data.error);
                return;
            }

            displayResults(data);

        } catch (error) {
            clearInterval(msgInterval);
            showLoading(false);
            document.getElementById("analyzeBtn").disabled = false;
            alert("Network error: " + error.message);
        }
    }
);

// ============================================
// Show Loading
// ============================================
function showLoading(show) {
    document.getElementById("loading").style.display =
        show ? "block" : "none";
}

// ============================================
// Reset Form
// ============================================
function resetForm() {
    document.getElementById("uploadForm").reset();
    document.getElementById("previewContainer").style.display = "none";
    document.getElementById("dropZone").style.display = "block";
    document.getElementById("imageInput").value = "";
    document.getElementById("resultsSection").style.display = "none";
    document.getElementById("alertBanner").style.display = "none";
    document.getElementById("googleResults").innerHTML = '<p class="no-data">No data</p>';
    document.getElementById("awsResults").innerHTML = '<p class="no-data">No data</p>';
    document.getElementById("azureResults").innerHTML = '<p class="no-data">No data</p>';
    document.getElementById("audioResults").innerHTML = '<p class="no-data">No alert generated</p>';
    document.getElementById("resLocation").textContent = "-";
    document.getElementById("resTime").textContent = "-";
    document.getElementById("resLevel").textContent = "-";
    document.getElementById("resSentiment").textContent = "-";
    window.scrollTo({ top: 0, behavior: "smooth" });
}

// ============================================
// Display Results
// ============================================
function displayResults(data) {
    document.getElementById("resultsSection").style.display = "block";

    // Info cards
    document.getElementById("resLocation").textContent =
        data.location || "-";
    document.getElementById("resTime").textContent =
        data.timestamp || "-";

    if (data.severity) {
        const levelEl = document.getElementById("resLevel");
        levelEl.textContent    = data.severity.level;
        levelEl.className      = "card-value level-" + data.severity.level;

        document.getElementById("resSentiment").textContent =
            data.severity.sentiment.toUpperCase();
    }

    // Alert banner
    // Alert banner
    if (data.alert) {
        const banner  = document.getElementById("alertBanner");
        const heading = document.querySelector(".alert-content h3");
        const icon    = document.querySelector(".alert-icon");

        banner.style.display = "flex";
        document.getElementById("alertText").textContent = data.alert;

        if (data.severity && data.severity.negative >= 40) {
            banner.style.background   = "rgba(230, 57, 70, 0.15)";
            banner.style.borderColor  = "#e63946";
            icon.style.background     = "#e63946";
            heading.textContent       = "INCIDENT DETECTED";
        } else {
            banner.style.background   = "rgba(76, 175, 80, 0.15)";
            banner.style.borderColor  = "#4caf50";
            icon.style.background     = "#4caf50";
            heading.textContent       = "ROAD STATUS: NORMAL";
        }
    } else {
        document.getElementById("alertBanner").style.display = "none";
    }

    // Google Vision Results
    if (data.google && data.google.labels) {
        const html = data.google.labels.map(function (label) {
            const cls = getScoreClass(label.score);
            return `
                <div class="label-item">
                    <span class="label-name">${label.name}</span>
                    <span class="label-score ${cls}">${label.score}%</span>
                </div>
            `;
        }).join("");
        document.getElementById("googleResults").innerHTML = html;
    }

    // AWS Results
    if (data.aws && data.aws.labels) {
        const html = data.aws.labels.map(function (label) {
            const cls = getScoreClass(label.score);
            return `
                <div class="label-item">
                    <span class="label-name">${label.name}</span>
                    <span class="label-score ${cls}">${label.score}%</span>
                </div>
            `;
        }).join("");
        document.getElementById("awsResults").innerHTML = html;
    }

    // Azure NLU Results
    if (data.severity) {
        const s    = data.severity;
        const html = `
            <div class="severity-item">
                <div class="severity-label">
                    <span>Negative</span>
                    <span>${s.negative}%</span>
                </div>
                <div class="severity-bar">
                    <div
                        class="severity-fill fill-negative"
                        style="width: ${s.negative}%"
                    ></div>
                </div>
            </div>
            <div class="severity-item">
                <div class="severity-label">
                    <span>Positive</span>
                    <span>${s.positive}%</span>
                </div>
                <div class="severity-bar">
                    <div
                        class="severity-fill fill-positive"
                        style="width: ${s.positive}%"
                    ></div>
                </div>
            </div>
            <div class="level-badge level-${s.level}">
                Alert Level: ${s.level}
            </div>
        `;
        document.getElementById("azureResults").innerHTML = html;
    }

    // Audio Player
    if (data.audio) {
        const html = `
            <div class="audio-player">
                <p class="audio-label">${data.alert}</p>
                <audio controls autoplay>
                    <source src="/${data.audio}" type="audio/mpeg">
                </audio>
            </div>
        `;
        document.getElementById("audioResults").innerHTML = html;
    }

    // Scroll to results
    document.getElementById("resultsSection").scrollIntoView({
        behavior: "smooth"
    });
}

// ============================================
// Score Class Helper
// ============================================
function getScoreClass(score) {
    if (score >= 90) return "score-high";
    if (score >= 70) return "score-medium";
    return "score-low";
}