import os
import random
import time
import json
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from game_logic import (
    doc_file_tu_vung, 
    kiem_tra_tu_nhap, 
    kiem_tra_tu_hop_le, 
    kiem_tra_tu_trong_danh_sach,
    kiem_tra_tu_noi_tiep,
    tach_tu_cuoi,
    a_star_search
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# Đường dẫn đến file lưu trữ bảng xếp hạng
LEADERBOARD_FILE = "leaderboard.json"
RANKED_LEADERBOARD_FILE = "ranked_leaderboard.json"

# Đọc toàn bộ danh sách từ phổ biến từ file easy_words.txt
def doc_file_tu_pho_bien():
    try:
        with open("easy_words.txt", "r", encoding="utf-8") as file:
            tu_pho_bien = file.read().splitlines() # Đọc từng dòng trong file
        return tu_pho_bien  # Trả về toàn bộ danh sách từ phổ biến
    except FileNotFoundError:
        print("❌ Lỗi: File easy_words.txt không tồn tại!")
    except Exception as e:
        print(f"❌ Lỗi khi đọc file: {e}")
    
    return []

# Hàm đọc bảng xếp hạng từ file
def load_leaderboard(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        return []
    except Exception as e:
        print(f"Lỗi khi đọc bảng xếp hạng: {e}")
        return []

# Hàm lưu bảng xếp hạng vào file
def save_leaderboard(leaderboard_data, file_path):
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(leaderboard_data, file, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Lỗi khi lưu bảng xếp hạng: {e}")

# Load từ vựng khi ứng dụng khởi động
tu_vung, tu_map = doc_file_tu_vung()

# Load danh sách từ phổ thông
danh_sach_tu_de = doc_file_tu_pho_bien()

# Bảng xếp hạng
leaderboard = load_leaderboard(LEADERBOARD_FILE)
ranked_leaderboard = load_leaderboard(RANKED_LEADERBOARD_FILE)

# Hệ thống xếp hạng
RANKS = [
    "Phàm Nhân", "Luyện Khí", "Trúc Cơ", "Kết Đan", "Nguyên Anh", "Hóa Thần",
    "Luyện Hư", "Hợp Thể", "Đại Thừa", "Độ Kiếp", "Tiên Nhân", "Chân Tiên",
    "Huyền Tiên", "Kim Tiên", "Đại La Kim Tiên", "Thiên Tiên", "Thần Nhân",
    "Chân Thần", "Thượng Cổ Thần", "Thánh Nhân", "Thiên Tôn", "Hỗn Độn Chí Tôn"
]

RANK_COLORS = [
    "#8B4513", "#CD853F", "#DAA520", "#FFD700", "#32CD32", "#00FA9A",
    "#00CED1", "#1E90FF", "#4169E1", "#0000FF", "#8A2BE2", "#9400D3",
    "#FF00FF", "#FF1493", "#FF69B4", "#FFA07A", "#FF6347", "#FF4500",
    "#FF0000", "#B22222", "#8B0000", "#000000"
]

# Update the get_rank_and_progress function to match the new calculate_rank function
def get_rank_and_progress(score):
    rank_index = min(score // 100, len(RANKS) - 1)
    current_rank = RANKS[rank_index]
    next_rank = RANKS[min(rank_index + 1, len(RANKS) - 1)]
    progress = (score % 100) / 100
    return current_rank, next_rank, progress, RANK_COLORS[rank_index]

# Phòng chờ PVP
pvp_waiting_room = {}
pvp_active_games = {}

# Hàm tính toán cấp bậc dựa trên điểm
def calculate_rank(points):
    # Calculate rank index based on points (100 points per rank)
    rank_index = min(points // 100, len(RANKS) - 1)
    
    # Get current rank and next rank
    current_rank = RANKS[rank_index]
    next_rank = RANKS[min(rank_index + 1, len(RANKS) - 1)]
    
    # Calculate progress to next rank (as a percentage)
    progress = (points % 100) / 100
    
    # Get the color for the current rank
    rank_color = RANK_COLORS[rank_index]
    
    return {
        "current": current_rank,
        "next": next_rank,
        "progress": progress * 100,  # Convert to percentage
        "color": rank_color,
        "total_points": points
    }

@app.route("/")
def home():
    # Lưu điểm vào bảng xếp hạng nếu có tên và điểm > 0
    player_name = session.get("player_name", "")
    score = session.get("score", 0)
    
    if player_name and score > 0:
        global leaderboard
        
        # Kiểm tra xem người chơi đã có trong bảng xếp hạng chưa
        player_exists = False
        for player in leaderboard:
            if player["name"] == player_name and player["score"] < score:
                player["score"] = score  # Cập nhật điểm cao hơn
                player_exists = True
                break
            elif player["name"] == player_name:
                player_exists = True
                break
                
        # Nếu chưa có trong bảng xếp hạng, thêm mới
        if not player_exists:
            leaderboard.append({"name": player_name, "score": score})
            
        # Sắp xếp lại bảng xếp hạng
        leaderboard.sort(key=lambda x: x["score"], reverse=True)
        leaderboard = leaderboard[:10]  # Giữ top 10
        
        # Lưu bảng xếp hạng vào file
        save_leaderboard(leaderboard, LEADERBOARD_FILE)
    
    # Giữ lại tên người chơi, reset các thông tin khác
    old_name = session.get("player_name", "")
    old_rank_points = session.get("rank_points", 0)
    session.clear()
    if old_name:
        session["player_name"] = old_name
    if old_rank_points:
        session["rank_points"] = old_rank_points
    
    # Nếu người chơi đã có tên, chuyển thẳng đến trang chơi
    if "player_name" in session and session["player_name"].strip():
        return render_template("giaodien.html", auto_start=False)
    return render_template("giaodien.html", auto_start=False)

@app.route('/reset-session')
def reset_session():
    # Lưu tên người chơi và điểm số trước khi xóa session
    player_name = session.get("player_name", "")
    score = session.get("score", 0)
    rank_points = session.get("rank_points", 0)
    
    # Lưu điểm vào bảng xếp hạng nếu có tên và điểm > 0
    if player_name and score > 0:
        global leaderboard
        
        # Kiểm tra xem người chơi đã có trong bảng xếp hạng chưa
        player_exists = False
        for player in leaderboard:
            if player["name"] == player_name and player["score"] < score:
                player["score"] = score  # Cập nhật điểm cao hơn
                player_exists = True
                break
            elif player["name"] == player_name:
                player_exists = True
                break
                
        # Nếu chưa có trong bảng xếp hạng, thêm mới
        if not player_exists:
            leaderboard.append({"name": player_name, "score": score})
            
        # Sắp xếp lại bảng xếp hạng
        leaderboard.sort(key=lambda x: x["score"], reverse=True)
        leaderboard = leaderboard[:10]  # Giữ top 10
        
        # Lưu bảng xếp hạng vào file
        save_leaderboard(leaderboard, LEADERBOARD_FILE)
    
    # Lưu tên người chơi
    old_name = session.get("player_name", "")
    
    # Xóa toàn bộ session
    session.clear()
    
    # Khôi phục tên người chơi và điểm xếp hạng
    if old_name:
        session["player_name"] = old_name
    if rank_points:
        session["rank_points"] = rank_points
        
    return redirect('/')  # Chuyển hướng về trang chủ

@app.route('/save-name', methods=["POST"])
def save_name():
    player_name = request.form.get("player_name", "").strip()
    if player_name:
        session["player_name"] = player_name
        # Reset điểm số khi bắt đầu game mới với tên mới
        session["score"] = 0
        # Khởi tạo điểm xếp hạng nếu chưa có
        if "rank_points" not in session:
            session["rank_points"] = 0
    return redirect('/')

@app.route('/change-name', methods=["POST"])
def change_name():
    player_name = request.form.get("player_name", "").strip()
    if player_name:
        # Lưu tên cũ để cập nhật bảng xếp hạng nếu cần
        old_name = session.get("player_name", "")
        
        # Cập nhật tên mới trong session
        session["player_name"] = player_name
        
        # Cập nhật tên trong bảng xếp hạng nếu người chơi đã có điểm
        if old_name:
            global leaderboard, ranked_leaderboard
            for player in leaderboard:
                if player["name"] == old_name:
                    player["name"] = player_name
                    break
            
            for player in ranked_leaderboard:
                if player["name"] == old_name:
                    player["name"] = player_name
                    break
            
            # Lưu bảng xếp hạng vào file
            save_leaderboard(leaderboard, LEADERBOARD_FILE)
            save_leaderboard(ranked_leaderboard, RANKED_LEADERBOARD_FILE)
    
    # Nếu đang ở trang chơi, quay lại trang chơi
    if request.form.get("from_game") == "true":
        game_mode = session.get("game_mode", "solo")
        if game_mode == "ranked":
            return redirect('/ranked')
        elif game_mode == "pvp":
            return redirect('/pvp')
        else:
            return redirect('/choinoitu')
    # Nếu không, quay lại trang chủ
    return redirect('/')

@app.route('/auto-start', methods=["GET"])
def auto_start():
    # Chuyển thẳng đến trang chơi nếu đã có tên
    if "player_name" in session and session["player_name"].strip():
        return redirect('/choinoitu')
    return redirect('/')

@app.route('/save-score', methods=["POST"])
def save_score():
    player_name = session.get("player_name", "Người chơi ẩn danh")
    score = session.get("score", 0)
    game_mode = session.get("game_mode", "solo")
    
    if score <= 0:
        return jsonify({"success": False, "message": "Điểm số phải lớn hơn 0"})
    
    # Xác định bảng xếp hạng dựa trên chế độ chơi
    global leaderboard, ranked_leaderboard
    current_leaderboard = ranked_leaderboard if game_mode == "ranked" or game_mode == "pvp" else leaderboard
    current_file = RANKED_LEADERBOARD_FILE if game_mode == "ranked" or game_mode == "pvp" else LEADERBOARD_FILE
    
    # Kiểm tra xem người chơi đã có trong bảng xếp hạng chưa
    player_exists = False
    for player in current_leaderboard:
        if player["name"] == player_name and player["score"] < score:
            player["score"] = score  # Cập nhật điểm cao hơn
            player_exists = True
            break
        elif player["name"] == player_name:
            player_exists = True
            break
            
    # Nếu chưa có trong bảng xếp hạng, thêm mới
    if not player_exists:
        current_leaderboard.append({"name": player_name, "score": score})
        
    # Sắp xếp lại bảng xếp hạng
    current_leaderboard.sort(key=lambda x: x["score"], reverse=True)
    current_leaderboard = current_leaderboard[:10]  # Giữ top 10
    
    # Cập nhật biến toàn cục
    if game_mode == "ranked" or game_mode == "pvp":
        ranked_leaderboard = current_leaderboard
    else:
        leaderboard = current_leaderboard
    
    # Lưu bảng xếp hạng vào file
    save_leaderboard(current_leaderboard, current_file)
    
    return jsonify({"success": True})

@app.route('/get-leaderboard')
def get_leaderboard():
    # Xác định bảng xếp hạng dựa trên chế độ chơi hiện tại
    game_mode = session.get("game_mode", "solo")
    if (game_mode == "ranked" or game_mode == "pvp") and request.args.get("type") == "ranked":
        # Tải lại bảng xếp hạng từ file để đảm bảo dữ liệu mới nhất
        global ranked_leaderboard
        ranked_leaderboard = load_leaderboard(RANKED_LEADERBOARD_FILE)
        return jsonify(ranked_leaderboard)
    
    # Tải lại bảng xếp hạng từ file để đảm bảo dữ liệu mới nhất
    global leaderboard
    leaderboard = load_leaderboard(LEADERBOARD_FILE)
    return jsonify(leaderboard)

# Add this new route after the get-leaderboard route
@app.route('/check-game-state')
def check_game_state():
    game_mode = session.get("game_mode", "solo")
    return jsonify({
        "current_word": session.get("current_word", ""),
        "score": session.get("score", 0),
        "time_limit": session.get("time_limit", 10),
        "da_su_dung": session.get("da_su_dung", []),
        "game_mode": game_mode,
        "stop_timer": session.get("stop_timer", False),
        "timestamp": time.time()
    })

@app.route('/ranked-leaderboard')
def get_ranked_leaderboard():
    # Tải lại bảng xếp hạng từ file để đảm bảo dữ liệu mới nhất
    global ranked_leaderboard
    ranked_leaderboard = load_leaderboard(RANKED_LEADERBOARD_FILE)
    return jsonify(ranked_leaderboard)

@app.route('/get-rank')
def get_rank():
    player_name = session.get("player_name", "")
    rank_points = session.get("rank_points", 0)
    
    rank_info = calculate_rank(rank_points)
    
    return jsonify({
        "player": player_name,
        "rank": rank_info
    })

@app.route('/update-rank-points', methods=["POST"])
def update_rank_points():
    data = request.get_json()
    points_to_add = data.get("points", 0)
    
    current_points = session.get("rank_points", 0)
    new_points = current_points + points_to_add
    session["rank_points"] = new_points
    
    rank_info = calculate_rank(new_points)
    
    return jsonify({
        "success": True,
        "rank": rank_info,
        "points_added": points_to_add
    })

@app.route("/choinoitu", methods=["GET", "POST"]) 
def index():
  # Đặt chế độ chơi là solo
  session["game_mode"] = "solo"
  
  # Kiểm tra xem người chơi đã nhập tên chưa
  if "player_name" not in session or not session["player_name"].strip():
      return redirect('/')
      
  # Reset trò chơi nếu cần
  if request.method == "GET":
      if request.args.get("reset") == "true":
          score = session.get("score", 0) 
          player_name = session.get("player_name", "")
          
          # Lưu điểm trước khi reset
          if player_name and score > 0:
              global leaderboard
              
              # Kiểm tra xem người chơi đã có trong bảng xếp hạng chưa
              player_exists = False
              for player in leaderboard:
                  if player["name"] == player_name and player["score"] < score:
                      player["score"] = score  # Cập nhật điểm cao hơn
                      player_exists = True
                      break
                  elif player["name"] == player_name:
                      player_exists = True
                      break
                      
              # Nếu chưa có trong bảng xếp hạng, thêm mới
              if not player_exists:
                  leaderboard.append({"name": player_name, "score": score})
                  
              # Sắp xếp lại bảng xếp hạng
              leaderboard.sort(key=lambda x: x["score"], reverse=True)
              leaderboard = leaderboard[:10]  # Giữ top 10
              
              # Lưu bảng xếp hạng vào file
              save_leaderboard(leaderboard, LEADERBOARD_FILE)
          
          # Reset session nhưng giữ lại tên người chơi
          old_name = session.get("player_name", "")
          old_rank_points = session.get("rank_points", 0)
          session.clear()
          session["score"] = max(0, score - 2)
          session["player_name"] = old_name
          session["rank_points"] = old_rank_points
          session["game_mode"] = "solo"
          session["game_state_id"] = str(int(time.time()))  # Add a unique game state ID
          
      elif request.args.get("continue") == "true":
          score = session.get("score", 0)
          player_name = session.get("player_name", "")
          rank_points = session.get("rank_points", 0)
          
          # Reset session nhưng giữ lại tên người chơi và cộng điểm
          old_name = session.get("player_name", "")
          old_game_state_id = session.get("game_state_id", "")
          session.clear()
          session["score"] = score + random.randint(2, 5)  # Cộng điểm khi thắng AI
          session["ai_thua"] = False  # Reset trạng thái AI thua
          session["player_name"] = old_name
          session["rank_points"] = rank_points
          session["game_mode"] = "solo"
          session["game_state_id"] = old_game_state_id or str(int(time.time()))
      
  # Khởi tạo điểm số nếu chưa có
  if "score" not in session:
      session["score"] = 0

  # Khởi tạo game_state_id nếu chưa có
  if "game_state_id" not in session:
      session["game_state_id"] = str(int(time.time()))

  # Nếu chưa có danh sách từ đã sử dụng
      session["game_state_id"] = str(int(time.time()))

  # Nếu chưa có danh sách từ đã sử dụng, AI bắt đầu trước
  if "da_su_dung" not in session or not session["da_su_dung"]:
      if danh_sach_tu_de:  
          ai_first_word = random.choice(danh_sach_tu_de)
      else:
          ai_first_word = "học tập"

      session["da_su_dung"] = [ai_first_word] 
      session["current_word"] = ai_first_word 

  if request.method == "POST":
      user_word = request.form.get("user_word", "").strip().lower()
      da_su_dung = session.get("da_su_dung", [])  # Danh sách từ đã sử dụng
      last_word = session.get("current_word", "") # Lấy từ cuối cùng trong danh sách từ đã sử dụng

      # Kiểm tra lỗi nhập từ
      if len(user_word.split()) < 2: 
          session["ket_qua"] = "Bạn đã nhập 1 từ. Bạn thua!"
          session["stop_timer"] = True
          session["ai_thua"] = False
      elif not kiem_tra_tu_nhap(user_word):
          session["ket_qua"] = "Từ nhập vào phải có ít nhất 2 từ. Bạn thua!"
          session["stop_timer"] = True
          session["ai_thua"] = False
      elif not kiem_tra_tu_hop_le(user_word):
          session["ket_qua"] = "Từ nhập vào không hợp lệ. Bạn thua!"
          session["stop_timer"] = True
          session["ai_thua"] = False
      elif not kiem_tra_tu_trong_danh_sach(user_word, tu_vung):
          session["ket_qua"] = "Từ nhập vào không có trong danh sách từ vựng. Bạn thua!"
          session["stop_timer"] = True
          session["ai_thua"] = False
      elif user_word in da_su_dung:
          session["ket_qua"] = "Từ này đã được sử dụng. Bạn thua!"
          session["stop_timer"] = True
          session["ai_thua"] = False
      elif not kiem_tra_tu_noi_tiep(user_word, last_word):
          session["ket_qua"] = f"Từ nhập vào phải bắt đầu bằng '{tach_tu_cuoi(last_word)}'. Bạn thua!"
          session["stop_timer"] = True
          session["ai_thua"] = False
      else:
          # Người chơi nhập hợp lệ
          da_su_dung.append(user_word) # Thêm từ người chơi vào danh sách từ đã sử dụng
          session["da_su_dung"] = da_su_dung # Cập nhật danh sách từ đã sử dụng
          session["current_word"] = user_word # Cập nhật từ hiện tại

          # Cập nhật điểm số
          session["score"] += random.randint(2, 5)

          # AI tìm từ tiếp theo
          tu_cuoi = tach_tu_cuoi(user_word) # Tách từ cuối cùng của từ người chơi
          ai_win, ai_sequence = a_star_search(tu_cuoi, da_su_dung, "ai", tu_map) # Tìm từ phù hợp cho AI

          # Nếu AI thắng, thêm từ AI vào danh sách từ đã sử dụng
          if ai_win and ai_sequence: 
              ai_move = ai_sequence[0] # Lấy từ đầu tiên trong chuỗi nước đi của AI
              da_su_dung.append(ai_move) # Thêm từ AI vào danh sách từ đã sử dụng
              session["da_su_dung"] = da_su_dung # Cập nhật danh sách từ đã sử dụng
              session["current_word"] = ai_move # Cập nhật từ hiện tại
          else:
              session["ket_qua"] = "AI không tìm được từ phù hợp. Bạn thắng!"
              session["stop_timer"] = True
              session["ai_thua"] = True

  return render_template("choinoitu.html", 
                       da_su_dung=session.get("da_su_dung", []),
                       ket_qua=session.pop("ket_qua", None), 
                       stop_timer=session.pop("stop_timer", False),
                       ai_thua=session.pop("ai_thua", False),
                       score=session.get("score", 0),
                       player_name=session.get("player_name", "Người chơi ẩn danh"),
                       game_mode="solo")

# Modify the ranked_mode function to update localStorage when a word is submitted
@app.route("/ranked", methods=["GET", "POST"])
def ranked_mode():
  # Đặt chế độ chơi là ranked
  session["game_mode"] = "ranked"
  
  # Kiểm tra xem người chơi đã nhập tên chưa
  if "player_name" not in session or not session["player_name"].strip():
      return redirect('/')
      
  # Reset trò chơi nếu cần
  if request.method == "GET":
      if request.args.get("reset") == "true":
          score = session.get("score", 0) 
          player_name = session.get("player_name", "")
          rank_points = session.get("rank_points", 0)
          
          # Lưu điểm trước khi reset
          if player_name and score > 0:
              global ranked_leaderboard
              
              # Kiểm tra xem người chơi đã có trong bảng xếp hạng chưa
              player_exists = False
              for player in ranked_leaderboard:
                  if player["name"] == player_name and player["score"] < score:
                      player["score"] = score  # Cập nhật điểm cao hơn
                      player_exists = True
                      break
                  elif player["name"] == player_name:
                      player_exists = True
                      break
                      
              # Nếu chưa có trong bảng xếp hạng, thêm mới
              if not player_exists:
                  ranked_leaderboard.append({"name": player_name, "score": score})
                  
              # Sắp xếp lại bảng xếp hạng
              ranked_leaderboard.sort(key=lambda x: x["score"], reverse=True)
              ranked_leaderboard = ranked_leaderboard[:10]  # Giữ top 10
              
              # Lưu bảng xếp hạng vào file
              save_leaderboard(ranked_leaderboard, RANKED_LEADERBOARD_FILE)
          
          # Reset session nhưng giữ lại tên người chơi
          old_name = session.get("player_name", "")
          session.clear()
          session["score"] = 0  # Trong chế độ xếp hạng, điểm bắt đầu từ 0
          session["player_name"] = old_name
          session["rank_points"] = rank_points
          session["game_mode"] = "ranked"
          session["game_state_id"] = str(int(time.time()))  # Add a unique game state ID
          
      elif request.args.get("continue") == "true":
          score = session.get("score", 0)
          player_name = session.get("player_name", "")
          rank_points = session.get("rank_points", 0)
          
          # Reset session nhưng giữ lại tên người chơi và cộng điểm
          old_name = session.get("player_name", "")
          old_game_state_id = session.get("game_state_id", "")
          session.clear()
          session["score"] = score + random.randint(5, 10)  # Cộng điểm nhiều hơn khi thắng trong chế độ xếp hạng
          session["ai_thua"] = False  # Reset trạng thái AI thua
          session["player_name"] = old_name
          session["rank_points"] = rank_points
          session["game_mode"] = "ranked"
          session["game_state_id"] = old_game_state_id or str(int(time.time()))
      
  # Khởi tạo điểm số nếu chưa có
  if "score" not in session:
      session["score"] = 0

  # Khởi tạo game_state_id nếu chưa có
  if "game_state_id" not in session:
      session["game_state_id"] = str(int(time.time()))

  # Nếu chưa có danh sách từ đã sử dụng, AI bắt đầu trước với từ khó hơn
  if "da_su_dung" not in session or not session["da_su_dung"]:
      # Trong chế độ xếp hạng, chọn từ khó hơn
      if len(tu_vung) > 0:
          ai_first_word = random.choice(tu_vung)
      else:
          ai_first_word = "học tập"

      session["da_su_dung"] = [ai_first_word] 
      session["current_word"] = ai_first_word
      session["time_limit"] = 8  # Thời gian ngắn hơn trong chế độ xếp hạng

  if request.method == "POST":
      user_word = request.form.get("user_word", "").strip().lower()
      da_su_dung = session.get("da_su_dung", [])  # Danh sách từ đã sử dụng
      last_word = session.get("current_word", "") # Lấy từ cuối cùng trong danh sách từ đã sử dụng

      # Kiểm tra lỗi nhập từ
      if len(user_word.split()) < 2: 
          session["ket_qua"] = "Bạn đã nhập 1 từ. Bạn thua!"
          session["stop_timer"] = True
          session["ai_thua"] = False
      elif not kiem_tra_tu_nhap(user_word):
          session["ket_qua"] = "Từ nhập vào phải có ít nhất 2 từ. Bạn thua!"
          session["stop_timer"] = True
          session["ai_thua"] = False
      elif not kiem_tra_tu_hop_le(user_word):
          session["ket_qua"] = "Từ nhập vào không hợp lệ. Bạn thua!"
          session["stop_timer"] = True
          session["ai_thua"] = False
      elif not kiem_tra_tu_trong_danh_sach(user_word, tu_vung):
          session["ket_qua"] = "Từ nhập vào không có trong danh sách từ vựng. Bạn thua!"
          session["stop_timer"] = True
          session["ai_thua"] = False
      elif user_word in da_su_dung:
          session["ket_qua"] = "Từ này đã được sử dụng. Bạn thua!"
          session["stop_timer"] = True
          session["ai_thua"] = False
      elif not kiem_tra_tu_noi_tiep(user_word, last_word):
          session["ket_qua"] = f"Từ nhập vào phải bắt đầu bằng '{tach_tu_cuoi(last_word)}'. Bạn thua!"
          session["stop_timer"] = True
          session["ai_thua"] = False
      else:
          # Người chơi nhập hợp lệ
          da_su_dung.append(user_word) # Thêm từ người chơi vào danh sách từ đã sử dụng
          session["da_su_dung"] = da_su_dung # Cập nhật danh sách từ đã sử dụng
          session["current_word"] = user_word # Cập nhật từ hiện tại

          # Cập nhật điểm số - trong chế độ xếp hạng, điểm thưởng cao hơn
          session["score"] += random.randint(5, 10)

          # AI tìm từ tiếp theo - trong chế độ xếp hạng, AI thông minh hơn
          tu_cuoi = tach_tu_cuoi(user_word) # Tách từ cuối cùng của từ người chơi
          ai_win, ai_sequence = a_star_search(tu_cuoi, da_su_dung, "ai", tu_map, depth=5) # Tìm từ phù hợp cho AI với độ sâu lớn hơn

          # Nếu AI thắng, thêm từ AI vào danh sách từ đã sử dụng
          if ai_win and ai_sequence: 
              ai_move = ai_sequence[0] # Lấy từ đầu tiên trong chuỗi nước đi của AI
              da_su_dung.append(ai_move) # Thêm từ AI vào danh sách từ đã sử dụng
              session["da_su_dung"] = da_su_dung # Cập nhật danh sách từ đã sử dụng
              session["current_word"] = ai_move # Cập nhật từ hiện tại
              
              # Giảm thời gian đếm ngược sau mỗi lượt trong chế độ xếp hạng
              if session.get("time_limit", 10) > 5:
                  session["time_limit"] = session.get("time_limit", 10) - 1
          else:
              session["ket_qua"] = "AI không tìm được từ phù hợp. Bạn thắng!"
              session["stop_timer"] = True
              session["ai_thua"] = True
              # Cộng điểm xếp hạng khi thắng AI trong chế độ xếp hạng
              current_points = session.get("rank_points", 0)
              session["rank_points"] = current_points + random.randint(20, 30)
              
              # Lưu điểm xếp hạng vào file
              player_data = {"name": player_name, "rank_points": session["rank_points"]}
              save_player_data(player_data)

  # Tính toán thông tin xếp hạng
  rank_info = calculate_rank(session.get("rank_points", 0))

  return render_template("ranked.html", 
                       da_su_dung=session.get("da_su_dung", []),
                       ket_qua=session.pop("ket_qua", None), 
                       stop_timer=session.pop("stop_timer", False),
                       ai_thua=session.pop("ai_thua", False),
                       score=session.get("score", 0),
                       player_name=session.get("player_name", "Người chơi ẩn danh"),
                       game_mode="ranked",
                       time_limit=session.get("time_limit", 8),
                       rank=rank_info,
                       game_state_id=session.get("game_state_id", ""))

# Hàm lưu dữ liệu người chơi
def save_player_data(player_data):
    try:
        player_file = "players.json"
        players = []
        
        # Đọc dữ liệu hiện có
        if os.path.exists(player_file):
            with open(player_file, 'r', encoding='utf-8') as file:
                players = json.load(file)
        
        # Kiểm tra xem người chơi đã tồn tại chưa
        player_exists = False
        for player in players:
            if player["name"] == player_data["name"]:
                player["rank_points"] = player_data["rank_points"]
                player_exists = True
                break
        
        # Nếu chưa tồn tại, thêm mới
        if not player_exists:
            players.append(player_data)
        
        # Lưu lại vào file
        with open(player_file, 'w', encoding='utf-8') as file:
            json.dump(players, file, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Lỗi khi lưu dữ liệu người chơi: {e}")

# Hàm đọc dữ liệu người chơi
def load_player_data(player_name):
    try:
        player_file = "players.json"
        if os.path.exists(player_file):
            with open(player_file, 'r', encoding='utf-8') as file:
                players = json.load(file)
                
            for player in players:
                if player["name"] == player_name:
                    return player
        
        return None
    except Exception as e:
        print(f"Lỗi khi đọc dữ liệu người chơi: {e}")
        return None

# Modify the pvp_mode function to better handle matchmaking and game creation
@app.route("/pvp", methods=["GET", "POST"])
def pvp_mode():
    # Đặt chế độ chơi là pvp
    session["game_mode"] = "pvp"
    
    # Kiểm tra xem người chơi đã nhập tên chưa
    if "player_name" not in session or not session["player_name"].strip():
        return redirect('/')
    
    player_id = session.get("player_id", None)
    if not player_id:
        player_id = str(int(time.time() * 1000)) + str(random.randint(1000, 9999))
        session["player_id"] = player_id
    
    player_name = session.get("player_name", "Người chơi ẩn danh")
    
    # Khởi tạo điểm xếp hạng nếu chưa có
    if "rank_points" not in session:
        session["rank_points"] = 0
        
        # Kiểm tra xem có dữ liệu người chơi đã lưu không
        player_data = load_player_data(player_name)
        if player_data:
            session["rank_points"] = player_data["rank_points"]
    
    # Tính toán thông tin xếp hạng
    rank_info = calculate_rank(session.get("rank_points", 0))
    
    # Xóa người chơi khỏi game hiện tại nếu có
    for game_id, game in list(pvp_active_games.items()):
        if player_id in [game["player1"]["id"], game["player2"]["id"]]:
            # Đánh dấu người chơi đã rời game
            if player_id == game["player1"]["id"]:
                game["player1_connected"] = False
            else:
                game["player2_connected"] = False
        
        # Nếu cả hai người chơi đều đã rời game, xóa game
        if not game["player1_connected"] and not game["player2_connected"]:
            del pvp_active_games[game_id]
    
    # Kiểm tra xem người chơi đã trong phòng chờ hay chưa
    if player_id in pvp_waiting_room:
        # Người chơi đã trong phòng chờ, kiểm tra xem có đối thủ không
        waiting_since = pvp_waiting_room[player_id]["waiting_since"]
        waiting_time = int(time.time() - waiting_since)
        
        # Kiểm tra xem có game đang hoạt động không
        for game_id, game in pvp_active_games.items():
            if player_id in [game["player1"]["id"], game["player2"]["id"]]:
                # Người chơi đang trong game
                return redirect(f'/pvp/game/{game_id}')
        
        return render_template("pvp_waiting.html", 
                             player_name=player_name,
                             waiting_time=waiting_time,
                             rank=rank_info)
    
    # Nếu người chơi không trong phòng chờ, kiểm tra xem có ai đang đợi không
    if len(pvp_waiting_room) > 0:
        # Tìm đối thủ phù hợp (có thể thêm logic ghép cặp dựa trên xếp hạng)
        opponent_id = next(iter(pvp_waiting_room))
        opponent = pvp_waiting_room.pop(opponent_id)
        
        # Tạo game mới
        game_id = str(int(time.time())) + str(random.randint(1000, 9999))
        
        # Chọn ngẫu nhiên từ đầu tiên từ danh sách từ dễ
        if len(danh_sach_tu_de) > 0:
            first_word = random.choice(danh_sach_tu_de)
        else:
            # Nếu không có từ dễ, thử lấy từ danh sách từ vựng chung
            if len(tu_vung) > 0:
                first_word = random.choice(tu_vung)
            else:
                first_word = "học tập"
        
        # Người chơi vào phòng chờ trước sẽ đi trước
        pvp_active_games[game_id] = {
            "player1": {
                "id": opponent_id,
                "name": opponent["name"],
                "score": 0
            },
            "player2": {
                "id": player_id,
                "name": player_name,
                "score": 0
            },
            "current_turn": "player1",  # Người chơi vào trước luôn đi trước
            "da_su_dung": [first_word],
            "current_word": first_word,
            "time_limit": 15,
            "last_move_time": time.time(),
            "game_over": False,
            "winner": None,
            "game_start_time": time.time(),  # Thêm thời gian bắt đầu game
            "player1_connected": True,
            "player2_connected": True
        }
        
        return redirect(f'/pvp/game/{game_id}')
    else:
        # Không có ai đang đợi, thêm người chơi vào phòng chờ
        pvp_waiting_room[player_id] = {
            "name": player_name,
            "rank_points": session.get("rank_points", 0),
            "waiting_since": time.time()
        }
        
        return render_template("pvp_waiting.html", 
                             player_name=player_name,
                             waiting_time=0,
                             rank=rank_info)

@app.route("/pvp/game/<game_id>", methods=["GET", "POST"])
def pvp_game(game_id):
    # Kiểm tra xem game có tồn tại không
    if game_id not in pvp_active_games:
        return redirect('/pvp')
    
    game = pvp_active_games[game_id]
    player_id = session.get("player_id", None)
    
    # Kiểm tra xem người chơi có trong game không
    if player_id not in [game["player1"]["id"], game["player2"]["id"]]:
        return redirect('/pvp')
    
    # Xác định người chơi hiện tại và đối thủ
    is_player1 = player_id == game["player1"]["id"]
    current_player = "player1" if is_player1 else "player2"
    opponent = "player2" if is_player1 else "player1"
    
    # Đánh dấu người chơi đã kết nối
    game[f"{current_player}_connected"] = True
    
    # Xử lý nước đi của người chơi
    if request.method == "POST" and game["current_turn"] == current_player and not game["game_over"]:
        user_word = request.form.get("user_word", "").strip().lower()
        da_su_dung = game["da_su_dung"]
        last_word = game["current_word"]
        
        # Kiểm tra lỗi nhập từ
        if len(user_word.split()) < 2:
            game["game_over"] = True
            game["winner"] = opponent
            game["lose_reason"] = "Bạn đã nhập 1 từ. Bạn thua!"
        elif not kiem_tra_tu_nhap(user_word):
            game["game_over"] = True
            game["winner"] = opponent
            game["lose_reason"] = "Từ nhập vào phải có ít nhất 2 từ. Bạn thua!"
        elif not kiem_tra_tu_hop_le(user_word):
            game["game_over"] = True
            game["winner"] = opponent
            game["lose_reason"] = "Từ nhập vào không hợp lệ. Bạn thua!"
        elif not kiem_tra_tu_trong_danh_sach(user_word, tu_vung):
            game["game_over"] = True
            game["winner"] = opponent
            game["lose_reason"] = "Từ nhập vào không có trong danh sách từ vựng. Bạn thua!"
        elif user_word in da_su_dung:
            game["game_over"] = True
            game["winner"] = opponent
            game["lose_reason"] = "Từ này đã được sử dụng. Bạn thua!"
        elif not kiem_tra_tu_noi_tiep(user_word, last_word):
            game["game_over"] = True
            game["winner"] = opponent
            game["lose_reason"] = f"Từ nhập vào phải bắt đầu bằng '{tach_tu_cuoi(last_word)}'. Bạn thua!"
        else:
            # Người chơi nhập hợp lệ
            da_su_dung.append(user_word)
            game["da_su_dung"] = da_su_dung
            game["current_word"] = user_word
            game["last_move_time"] = time.time()
            
            # Cập nhật điểm số
            game[current_player]["score"] += random.randint(5, 10)
            
            # Chuyển lượt cho đối thủ
            game["current_turn"] = opponent
    
    # Kiểm tra thời gian hết lượt
    if not game["game_over"] and time.time() - game["last_move_time"] > game["time_limit"]:
        # Người chơi hiện tại hết thời gian
        if game["current_turn"] == current_player:
            game["game_over"] = True
            game["winner"] = opponent
            game["lose_reason"] = "Bạn đã hết thời gian. Bạn thua!"
    
    # Nếu game kết thúc và người chơi thắng, cập nhật điểm xếp hạng
    if game["game_over"] and game["winner"] == current_player and not session.get("rank_updated_" + game_id, False):
        # Cộng điểm xếp hạng khi thắng PVP
        current_points = session.get("rank_points", 0)
        points_to_add = random.randint(30, 50)
        session["rank_points"] = current_points + points_to_add
        session["rank_updated_" + game_id] = True
        session["points_added"] = points_to_add
        
        # Lưu điểm xếp hạng vào file
        player_data = {"name": session.get("player_name", ""), "rank_points": session["rank_points"]}
        save_player_data(player_data)
    
    # Tính toán thông tin xếp hạng
    rank_info = calculate_rank(session.get("rank_points", 0))
    
    return render_template("pvp_game.html",
                         game=game,
                         game_id=game_id,
                         player_id=player_id,
                         is_player1=is_player1,
                         current_player=current_player,
                         opponent=opponent,
                         player_name=session.get("player_name", "Người chơi ẩn danh"),
                         rank=rank_info,
                         points_added=session.pop("points_added", 0),
                         rank_updated=session.get("rank_updated_" + game_id, False))

@app.route("/pvp/cancel", methods=["POST"])
def cancel_waiting():
    player_id = session.get("player_id", None)
    
    if player_id and player_id in pvp_waiting_room:
        del pvp_waiting_room[player_id]
    
    return redirect('/')

@app.route("/pvp/check-status", methods=["GET"])
def check_pvp_status():
    player_id = session.get("player_id", None)
    
    if not player_id:
        return jsonify({"status": "error", "message": "Không tìm thấy người chơi"})
    
    # Kiểm tra xem người chơi có trong phòng chờ không
    if player_id in pvp_waiting_room:
        waiting_since = pvp_waiting_room[player_id]["waiting_since"]
        waiting_time = int(time.time() - waiting_since)
        
        return jsonify({
            "status": "waiting",
            "waiting_time": waiting_time
        })
    
    # Kiểm tra xem người chơi có trong game không
    for game_id, game in pvp_active_games.items():
        if player_id in [game["player1"]["id"], game["player2"]["id"]]:
            return jsonify({
                "status": "matched",
                "game_id": game_id
            })
    
    return jsonify({"status": "not_found"})

@app.route("/pvp/game-status/<game_id>", methods=["GET"])
def get_game_status(game_id):
    if game_id not in pvp_active_games:
        return jsonify({"status": "error", "message": "Game không tồn tại"})
    
    game = pvp_active_games[game_id]
    player_id = session.get("player_id", None)
    
    # Kiểm tra xem người chơi có trong game không
    if player_id not in [game["player1"]["id"], game["player2"]["id"]]:
        return jsonify({"status": "error", "message": "Bạn không trong game này"})
    
    # Xác định người chơi hiện tại và đối thủ
    is_player1 = player_id == game["player1"]["id"]
    current_player = "player1" if is_player1 else "player2"
    opponent = "player2" if is_player1 else "player1"
    
    # Đánh dấu người chơi đã kết nối
    game[f"{current_player}_connected"] = True
    
    # Kiểm tra xem đối thủ đã ngắt kết nối chưa
    opponent_connected = game[f"{opponent}_connected"]
    
    # Tính toán thời gian còn lại chính xác
    remaining_time = max(0, int(game["time_limit"] - (time.time() - game["last_move_time"])))
    
    # Kiểm tra thời gian hết lượt
    if not game["game_over"] and remaining_time <= 0:
        # Người chơi hiện tại hết thời gian
        if game["current_turn"] == current_player:
            game["game_over"] = True
            game["winner"] = opponent
            game["lose_reason"] = "Bạn đã hết thời gian. Bạn thua!"
        # Đối thủ hết thời gian
        elif game["current_turn"] == opponent and not opponent_connected:
            game["game_over"] = True
            game["winner"] = current_player
            game["lose_reason"] = "Đối thủ đã hết thời gian. Bạn thắng!"
    
    # Tính toán thời gian đã trôi qua kể từ khi bắt đầu game
    elapsed_time = int(time.time() - game.get("game_start_time", time.time()))
    
    return jsonify({
        "status": "success",
        "game": game,
        "is_player1": is_player1,
        "current_player": current_player,
        "opponent": opponent,
        "opponent_connected": opponent_connected,
        "remaining_time": remaining_time,
        "elapsed_time": elapsed_time,
        "server_time": int(time.time())
    })

# Add a new route to handle the "Play Again" action
@app.route("/pvp/play-again", methods=["POST"])
def pvp_play_again():
    player_id = session.get("player_id", None)
    player_name = session.get("player_name", "Người chơi ẩn danh")
    
    if not player_id:
        return redirect('/')
    
    # Xóa người chơi khỏi game hiện tại nếu có
    for game_id, game in list(pvp_active_games.items()):
        if player_id in [game["player1"]["id"], game["player2"]["id"]]:
            # Đánh dấu người chơi đã rời game
            if player_id == game["player1"]["id"]:
                game["player1_connected"] = False
            else:
                game["player2_connected"] = False
            
            # Nếu cả hai người chơi đều đã rời game, xóa game
            if not game["player1_connected"] and not game["player2_connected"]:
                del pvp_active_games[game_id]
    
    # Thêm người chơi vào phòng chờ
    pvp_waiting_room[player_id] = {
        "name": player_name,
        "rank_points": session.get("rank_points", 0),
        "waiting_since": time.time()
    }
    
    # Xóa các session data liên quan đến game cũ
    for key in list(session.keys()):
        if key.startswith("rank_updated_"):
            session.pop(key, None)
    
    return redirect('/pvp')

if __name__ == "__main__":
    app.run(debug=True)