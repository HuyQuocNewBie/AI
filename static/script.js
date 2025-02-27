let countdown = 10;
let countdownElement = document.getElementById("countdown");
let countdownInterval = setInterval(updateCountdown, 1000);

function updateCountdown() {
    if (countdown > 0) {
        countdown--;
        countdownElement.innerText = countdown;
    } else {
        clearInterval(countdownInterval); // Dừng bộ đếm khi hết thời gian
        let choice = confirm("Hết thời gian trả lời. Bạn đã thua!\n\nOK: Chơi lại\nHủy: Trang chủ");
        
        if (choice) {
            window.location.href = "/choinoitu?reset=true"; // Chơi lại
        } else {
            window.location.href = "/"; // Trang chủ
        }
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