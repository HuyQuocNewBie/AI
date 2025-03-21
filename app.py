import os
import random
from flask import Flask, render_template, request, session, redirect, url_for
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

# Load từ vựng khi ứng dụng khởi động
tu_vung, tu_map = doc_file_tu_vung()

# Load danh sách từ phổ thông
danh_sach_tu_de = doc_file_tu_pho_bien()

@app.route("/")
def home():
    return render_template("giaodien.html")

@app.route('/reset-session')
def reset_session():
    session.clear()  # Xóa toàn bộ session
    return redirect('/')  # Chuyển hướng về trang chủ

@app.route("/choinoitu", methods=["GET", "POST"]) 
def index():
    # Reset trò chơi nếu cần
    if request.method == "GET":
        if request.args.get("reset") == "true":
            score = session.get("score", 0) 
            session.clear()
            session["score"] = max(0, score - 2)
        elif request.args.get("continue") == "true":
            score = session.get("score", 0)
            session.clear()
            session["score"] = score + random.randint(2, 5)  # Cộng điểm khi thắng AI
            session["ai_thua"] = False  # Reset trạng thái AI thua
        
    # Khởi tạo điểm số nếu chưa có
    if "score" not in session:
        session["score"] = 0

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
                         score=session.get("score", 0))

if __name__ == "__main__":
    app.run(debug=True)