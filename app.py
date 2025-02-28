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
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

# Load từ vựng và bảng ánh xạ khi ứng dụng khởi động
tu_vung, tu_map = doc_file_tu_vung()

@app.route("/")
def home():
    return render_template("giaodien.html")

@app.route("/choinoitu", methods=["GET", "POST"])
def index():
    if request.method == "GET" and request.args.get("reset") == "true":
        session.pop("da_su_dung", None)
        session.pop("ket_qua", None)

    if "da_su_dung" not in session or not session["da_su_dung"]:
        ai_first_word = random.choice(list(tu_vung))
        session["da_su_dung"] = [ai_first_word]

    if request.method == "POST":
        user_word = request.form.get("user_word", "").strip().lower()
        da_su_dung = session.get("da_su_dung", [])

        if len(user_word.split()) < 2:
            session["ket_qua"] = "Bạn đã nhập 1 từ. Bạn thua!"
            session["stop_timer"] = True
        elif not kiem_tra_tu_nhap(user_word):
            session["ket_qua"] = "Từ nhập vào phải có ít nhất 2 từ. Bạn thua!"
            session["stop_timer"] = True
        elif not kiem_tra_tu_hop_le(user_word):
            session["ket_qua"] = "Từ nhập vào không hợp lệ. Bạn thua!"
            session["stop_timer"] = True
        elif not kiem_tra_tu_trong_danh_sach(user_word, tu_vung):
            session["ket_qua"] = "Từ nhập vào không có trong danh sách từ vựng. Bạn thua!"
            session["stop_timer"] = True
        elif user_word in da_su_dung:
            session["ket_qua"] = "Từ này đã được sử dụng. Bạn thua!"
            session["stop_timer"] = True
        elif da_su_dung and not kiem_tra_tu_noi_tiep(user_word, da_su_dung[-1]):
            session["ket_qua"] = f"Từ nhập vào phải bắt đầu bằng '{tach_tu_cuoi(da_su_dung[-1])}'. Bạn thua!"
            session["stop_timer"] = True
        else:
            da_su_dung.append(user_word)
            session["da_su_dung"] = da_su_dung

            tu_cuoi = tach_tu_cuoi(user_word)
            ai_win, ai_sequence = a_star_search(tu_cuoi, da_su_dung, "ai", tu_map)

            if ai_win and ai_sequence:
                ai_move = ai_sequence[0]  # Lấy từ đầu tiên AI chọn
                da_su_dung.append(ai_move)
                session["da_su_dung"] = da_su_dung
            else:
                session["ket_qua"] = "AI không tìm được từ phù hợp. Bạn thắng!"
                session["stop_timer"] = True

    return render_template("choinoitu.html", da_su_dung=session.get("da_su_dung", []), ket_qua=session.pop("ket_qua", None), stop_timer=session.pop("stop_timer", False))

if __name__ == "__main__":
    app.run(debug=True)