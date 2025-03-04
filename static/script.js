let countdown = 10;
let countdownElement = document.getElementById("countdown");
let countdownInterval = setInterval(updateCountdown, 1000);

function updateCountdown() {
    if (countdown > 0) {
        countdown--;
        countdownElement.innerText = countdown;
    } else {
        clearInterval(countdownInterval); // Dừng bộ đếm khi hết thời gian
        showAlert("Hết thời gian! Bạn đã thua!", () => {
            window.location.href = "/choinoitu?reset=true"; // Chơi lại
        }, () => {
            window.location.href = "/reset-session"; // Trang chủ
        });
    }
}

// Hàm dừng thời gian khi có lỗi
function stopCountdown() {
    clearInterval(countdownInterval);
}

// Lấy giá trị stop_timer từ thẻ span
let stopTimer = document.getElementById("stopTimer").dataset.stop === "true";

if (stopTimer) {
    stopCountdown(); // Nếu có lỗi thì dừng bộ đếm
}

// Hàm hiển thị alert tùy chỉnh
function showAlert(message, onRetry, onHome) {
    let alertBox = document.createElement("div");
    alertBox.classList.add("custom-alert");
    
    alertBox.innerHTML = `
        <div class="alert-content">
            <h2>${message}</h2>
            <div class="alert-buttons">
                <button class="btn retry-btn" onclick="window.location.href='/choinoitu?reset=true'">Chơi lại</button>
                <button class="btn home-btn" onclick="window.location.href='/reset-session'">Trang chủ</button>
            </div>
        </div>
    `;

    document.body.appendChild(alertBox);

    document.querySelector(".retry-btn").addEventListener("click", () => {
        alertBox.remove();
        if (onRetry) onRetry();
    });

    document.querySelector(".home-btn").addEventListener("click", () => {
        alertBox.remove();
        if (onHome) onHome();
    });
}

function updateScore(scoreChange) {
    let scoreElement = document.getElementById("scoreValue");
    let currentScore = parseInt(scoreElement.innerText);
    scoreElement.innerText = Math.max(0, currentScore + scoreChange);
}