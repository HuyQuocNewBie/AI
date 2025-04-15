let countdown = 10
const countdownElement = document.getElementById("countdown")
const countdownInterval = setInterval(updateCountdown, 1000)

function updateCountdown() {
  if (countdown > 0) {
    countdown--
    countdownElement.innerText = countdown
  } else {
    clearInterval(countdownInterval) // Dừng bộ đếm khi hết thời gian
    showAlert(
      "Hết thời gian! Bạn đã thua!",
      () => {
        saveScoreAndReset() // Lưu điểm và chơi lại
      },
      () => {
        window.location.href = "/reset-session" // Trang chủ
      },
    )
  }
}

// Hàm dừng thời gian khi có lỗi
function stopCountdown() {
  clearInterval(countdownInterval)
}

// Lấy giá trị stop_timer từ thẻ span
const stopTimer = document.getElementById("stopTimer").dataset.stop === "true"

if (stopTimer) {
  stopCountdown() // Nếu có lỗi thì dừng bộ đếm
}

// Update the showAlert function to use the correct URL for the home button
function showAlert(message, onRetry, onHome) {
  const alertBox = document.createElement("div")
  alertBox.classList.add("custom-alert")

  alertBox.innerHTML = `
      <div class="alert-content">
          <h2>${message}</h2>
          <div class="alert-buttons">
              <button class="btn home-btn" onclick="goHome()">Trang chủ</button>
              <button class="btn retry-btn" onclick="saveScoreAndReset()">Chơi lại</button>
          </div>
      </div>
  `

  document.body.appendChild(alertBox)

  document.querySelector(".retry-btn").addEventListener("click", () => {
    alertBox.remove()
    if (onRetry) onRetry()
  })

  document.querySelector(".home-btn").addEventListener("click", () => {
    alertBox.remove()
    if (onHome) onHome()
  })
}

// Add a new function to handle going home
function goHome() {
  // Save score before going home
  fetch("/save-score", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then(() => {
      // Redirect to home page
      window.location.href = "/"
    })
    .catch((error) => {
      console.error("Lỗi khi lưu điểm:", error)
      window.location.href = "/"
    })
}

function updateScore(scoreChange) {
  const scoreElement = document.getElementById("scoreValue")
  const currentScore = Number.parseInt(scoreElement.innerText)
  scoreElement.innerText = Math.max(0, currentScore + scoreChange)
}

// Chuyển JSON string thành object trong script.js
document.addEventListener("DOMContentLoaded", () => {
  var winSound = document.getElementById("winSound")
  var loseSound = document.getElementById("loseSound")

  // Khai báo gameData để tránh lỗi
  const gameData = window.gameData || {}

  // Kiểm tra nếu gameData tồn tại
  if (typeof gameData !== "undefined" && gameData.ketQua) {
    if (gameData.aiThua) {
      winSound.play()
    } else {
      loseSound.play()
    }
  }

  // Kiểm tra nếu có bảng xếp hạng
  if (document.getElementById("leaderboard-body")) {
    loadLeaderboard()
  }
})

// Hàm hiển thị/ẩn bảng xếp hạng
function toggleLeaderboard() {
  const leaderboard = document.getElementById("leaderboard")
  if (leaderboard.classList.contains("show")) {
    leaderboard.classList.remove("show")
  } else {
    leaderboard.classList.add("show")
    loadLeaderboard()
  }
}

// Hàm tải dữ liệu bảng xếp hạng - Improved to force reload from server
function loadLeaderboard() {
  // Add a cache-busting parameter to force a fresh request
  const timestamp = new Date().getTime()
  fetch(`/get-leaderboard?_=${timestamp}`)
    .then((response) => response.json())
    .then((data) => {
      const leaderboardBody = document.getElementById("leaderboard-body")
      leaderboardBody.innerHTML = ""

      if (data.length === 0) {
        const row = document.createElement("tr")
        row.innerHTML = '<td colspan="3">Chưa có dữ liệu</td>'
        leaderboardBody.appendChild(row)
      } else {
        data.forEach((player, index) => {
          const row = document.createElement("tr")
          row.innerHTML = `
                        <td>${index + 1}</td>
                        <td>${player.name}</td>
                        <td>${player.score}</td>
                    `
          leaderboardBody.appendChild(row)
        })
      }
    })
    .catch((error) => console.error("Lỗi khi tải bảng xếp hạng:", error))
}

// Hàm lưu điểm và chơi lại - Improved to ensure score is saved
function saveScoreAndReset() {
  fetch("/save-score", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    cache: "no-store",
  })
    .then((response) => response.json())
    .then((data) => {
      // Add a small delay to ensure the score is saved
      setTimeout(() => {
        window.location.href = "/choinoitu?reset=true&_=" + new Date().getTime()
      }, 300)
    })
    .catch((error) => {
      console.error("Lỗi khi lưu điểm:", error)
      window.location.href = "/choinoitu?reset=true&_=" + new Date().getTime()
    })
}

// Hàm lưu điểm và tiếp tục - Improved to ensure score is saved
function saveScoreAndContinue() {
  fetch("/save-score", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    cache: "no-store",
  })
    .then((response) => response.json())
    .then((data) => {
      // Add a small delay to ensure the score is saved
      setTimeout(() => {
        window.location.href = "/choinoitu?continue=true&_=" + new Date().getTime()
      }, 300)
    })
    .catch((error) => {
      console.error("Lỗi khi lưu điểm:", error)
      window.location.href = "/choinoitu?continue=true&_=" + new Date().getTime()
    })
}

// Add these functions to script.js to handle game state synchronization
let gameStateCheckInterval

// Function to check game state from server
function checkGameStateFromServer() {
  // Get the game state ID from the hidden span
  const gameStateIdElement = document.getElementById("gameStateId")
  if (!gameStateIdElement) return // Exit if element doesn't exist

  const gameStateId = gameStateIdElement.dataset.id
  if (!gameStateId) return // Exit if no game state ID

  // Add a timestamp to prevent caching
  const timestamp = new Date().getTime()
  fetch(`/check-game-state?_=${timestamp}`)
    .then((response) => response.json())
    .then((data) => {
      const currentWord = document.getElementById("currentWord")
      if (!currentWord) return // Exit if element doesn't exist

      const currentWordText = currentWord.innerText.trim()

      // If the current word is different from the server's word, update the UI
      if (data.current_word && data.current_word !== currentWordText) {
        // Update the word display
        currentWord.innerText = data.current_word

        // Update the score
        const scoreElement = document.getElementById("scoreValue")
        if (scoreElement) {
          scoreElement.innerText = data.score
        }

        // Update the timer if needed
        const countdownElement = document.getElementById("countdown")
        if (countdownElement && window.countdown !== data.time_limit) {
          window.countdown = data.time_limit
          countdownElement.innerText = window.countdown

          // Restart the timer if it's running
          if (window.countdownInterval) {
            clearInterval(window.countdownInterval)
            window.countdownInterval = setInterval(updateCountdown, 1000)
          }
        }

        // Save the updated state to localStorage for cross-tab communication
        localStorage.setItem(
          "gameState_" + gameStateId,
          JSON.stringify({
            word: data.current_word,
            score: data.score,
            timeLimit: data.time_limit,
            timestamp: Date.now(),
          }),
        )
      }

      // Check if timer should be stopped
      const stopTimerElement = document.getElementById("stopTimer")
      if (stopTimerElement && data.stop_timer && stopTimerElement.dataset.stop !== "true") {
        stopTimerElement.dataset.stop = "true"
        if (window.countdownInterval) {
          clearInterval(window.countdownInterval)
        }
      }
    })
    .catch((error) => console.error("Error checking game state:", error))
}

// Start checking game state when the document is loaded
document.addEventListener("DOMContentLoaded", () => {
  const gameStateIdElement = document.getElementById("gameStateId")
  if (gameStateIdElement && gameStateIdElement.dataset.id) {
    // Start periodic checking - more frequent checks (500ms instead of 2000ms)
    gameStateCheckInterval = setInterval(checkGameStateFromServer, 500)

    // Listen for storage events (cross-tab communication)
    window.addEventListener("storage", (e) => {
      if (e.key === "gameState_" + gameStateIdElement.dataset.id) {
        try {
          const data = JSON.parse(e.newValue)

          // Update the UI with the new state
          const currentWord = document.getElementById("currentWord")
          if (currentWord) {
            currentWord.innerText = data.word
          }

          const scoreElement = document.getElementById("scoreValue")
          if (scoreElement) {
            scoreElement.innerText = data.score
          }

          // Update the timer if needed
          const countdownElement = document.getElementById("countdown")
          if (countdownElement && window.countdown !== data.timeLimit) {
            window.countdown = data.timeLimit
            countdownElement.innerText = window.countdown

            // Restart the timer if it's running
            if (window.countdownInterval) {
              clearInterval(window.countdownInterval)
              window.countdownInterval = setInterval(updateCountdown, 1000)
            }
          }
        } catch (error) {
          console.error("Error parsing storage event data:", error)
        }
      }
    })
  }
})