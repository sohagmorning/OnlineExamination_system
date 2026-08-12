// Exam Timer - 10 minutes
var totalSeconds = 10 * 60;

function updateTimer() {
    var minutes = Math.floor(totalSeconds / 60);
    var seconds = totalSeconds % 60;

    var display = "⏱ " 
        + (minutes < 10 ? "0" : "") + minutes 
        + ":" 
        + (seconds < 10 ? "0" : "") + seconds;

    document.getElementById("timer").textContent = display;

    // Warning when 2 minutes left
    if (totalSeconds <= 120) {
        document.getElementById("timer").style.backgroundColor = "#e67e22";
    }

    // Warning when 30 seconds left
    if (totalSeconds <= 30) {
        document.getElementById("timer").style.backgroundColor = "#c0392b";
    }

    // Time up - auto submit
    if (totalSeconds <= 0) {
        document.getElementById("timer").textContent = "⏱ 00:00";
        alert("সময় শেষ! পরীক্ষা স্বয়ংক্রিয়ভাবে জমা হচ্ছে।");
        document.getElementById("examForm").submit();
        return;
    }

    totalSeconds--;
}

// Run immediately then every second
updateTimer();
var countdown = setInterval(function() {
    if (totalSeconds < 0) {
        clearInterval(countdown);
    } else {
        updateTimer();
    }
}, 1000);
