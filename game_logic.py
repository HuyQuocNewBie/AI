import random
from queue import PriorityQueue

# Hàm đọc file words.txt và trả về danh sách từ vựng cùng với bảng ánh xạ theo từ đầu tiên
def doc_file_tu_vung():
    try:
        with open("words.txt", "r", encoding="utf-8") as file:
            tu_vung = file.read().splitlines()
        # Tạo bảng ánh xạ: key là từ đầu tiên, value là danh sách các cụm từ bắt đầu bằng key đó.
        tu_map = {}
        for phrase in tu_vung:
            words = phrase.split()
            if words:
                first_word = words[0]
                if first_word in tu_map:
                    tu_map[first_word].append(phrase)
                else:
                    tu_map[first_word] = [phrase]
        return tu_vung, tu_map
    except FileNotFoundError:
        print("File words.txt không tồn tại. Vui lòng kiểm tra lại.")
        return [], {}

# Hàm tách từ cuối cùng trong cụm từ
def tach_tu_cuoi(cum_tu):
    words = cum_tu.split()
    if not words:
        return None
    return words[-1]

# Hàm tìm tất cả các cụm từ bắt đầu bằng từ cho trước và chưa được sử dụng, sử dụng bảng ánh xạ tu_map để tối ưu
def tim_tat_ca_tu_bat_dau_bang(tu, tu_map, da_su_dung):
    if tu not in tu_map:
        return []
    return [phrase for phrase in tu_map[tu] if phrase not in da_su_dung]

# # Hàm đánh giá độ khó của từ (dùng trong chiến lược greedy)
# def danh_gia_do_kho(tu, tu_map, da_su_dung):
#     tu_cuoi = tach_tu_cuoi(tu)
#     if not tu_cuoi:
#         return 0
#     danh_sach_phu_hop = tim_tat_ca_tu_bat_dau_bang(tu_cuoi, tu_map, da_su_dung)
#     so_luong_tu_noi_tiep = len(danh_sach_phu_hop)
#     if so_luong_tu_noi_tiep == 0:
#         return -1  # Từ “tử đường”
#     return so_luong_tu_noi_tiep

# # Hàm chọn từ nối tiếp tối ưu theo chiến lược greedy
# def chon_tu_toi_uu(danh_sach_phu_hop, tu_map, da_su_dung):
#     tu_toi_uu = None
#     diem_cao_nhat = -float('inf')
#     tu_don_nguoi_choi_vao_the_bi = None

#     for phrase in danh_sach_phu_hop:
#         diem = danh_gia_do_kho(phrase, tu_map, da_su_dung)
#         if diem > diem_cao_nhat:
#             diem_cao_nhat = diem
#             tu_toi_uu = phrase
#         # Kiểm tra xem từ này có “dồn” đối thủ vào thế bế không
#         tu_cuoi = tach_tu_cuoi(phrase)
#         danh_sach_phu_hop_nguoi_choi = tim_tat_ca_tu_bat_dau_bang(tu_cuoi, tu_map, da_su_dung + [phrase])
#         if len(danh_sach_phu_hop_nguoi_choi) == 0:
#             tu_don_nguoi_choi_vao_the_bi = phrase

#     if tu_don_nguoi_choi_vao_the_bi:
#         return tu_don_nguoi_choi_vao_the_bi
#     return tu_toi_uu

# Các hàm kiểm tra tính hợp lệ của từ nhập
def kiem_tra_tu_nhap(tu):
    return len(tu.split()) >= 2

def kiem_tra_tu_trong_danh_sach(tu, tu_vung):
    return tu in tu_vung

def kiem_tra_tu_hop_le(tu):
    return all(char.isalpha() or char.isspace() for char in tu)

def kiem_tra_tu_noi_tiep(tu_nhap, tu_truoc_do):
    tu_cuoi_truoc_do = tach_tu_cuoi(tu_truoc_do)
    if not tu_cuoi_truoc_do:
        return False
    tu_dau_tien_nhap = tu_nhap.split()[0]
    return tu_dau_tien_nhap == tu_cuoi_truoc_do

# --- ÁP DỤNG A* SEARCH ---
# Mô hình trạng thái:
#   state = (current_last, used_set, turn, seq)
# - current_last: từ cuối của nước đi vừa thực hiện.
# - used_set: tập hợp các từ đã được sử dụng.
# - turn: lượt của "ai" hoặc "player".
# - seq: chuỗi các nước đi của AI (chỉ lưu nước đi của AI).
#
# Mục tiêu: Khi đến lượt của đối thủ (player) mà không còn nước đi hợp lệ.
def a_star_search(last_word, used, turn, tu_map, depth_limit=3):  # Giảm độ sâu tìm kiếm
    open_set = PriorityQueue()
    initial_state = (last_word, frozenset(used), turn, [])
    open_set.put((0, 0, initial_state))
    
    best_sequence = []  # Lưu lại chuỗi tốt nhất tìm được

    while not open_set.empty():
        f, g, state = open_set.get()
        current_last, used_set, current_turn, seq = state

        valid_moves = tim_tat_ca_tu_bat_dau_bang(current_last, tu_map, list(used_set))
        
        # Nếu đến lượt của đối thủ và không có nước đi nào, AI giành chiến thắng.
        if current_turn == "player" and len(valid_moves) == 0:
            return True, seq  # AI thắng

        # Nếu đến lượt của AI mà không còn nước đi, nhánh này không khả thi.
        if current_turn == "ai" and len(valid_moves) == 0:
            continue
        
        if g >= depth_limit:
            continue  # Giới hạn độ sâu tìm kiếm
        
        # Thêm độ ngẫu nhiên vào nước đi của AI
        random.shuffle(valid_moves)  # Trộn danh sách từ hợp lệ

        for move in valid_moves:
            new_used = set(used_set)
            new_used.add(move)
            new_last = tach_tu_cuoi(move)
            new_turn = "ai" if current_turn == "player" else "player"
            new_seq = seq.copy()

            if current_turn == "ai":
                new_seq.append(move)

            new_state = (new_last, frozenset(new_used), new_turn, new_seq)
            new_g = g + 1
            new_f = new_g  # Ở đây dùng h = 0 (uniform-cost search)
            open_set.put((new_f, new_g, new_state))

            # Lưu lại chuỗi nước đi dài nhất của AI tìm được
            if len(new_seq) > len(best_sequence):
                best_sequence = new_seq

    # Nếu AI không tìm được nước đi để thắng ngay, nó sẽ chơi nước đi hợp lệ dài nhất
    return False, best_sequence if best_sequence else []

# --- HÀM CHÍNH CHƠI TRÒ CHƠI NỐI TỪ ---
def choi_noi_tu():
    print("Chào mừng đến với trò chơi nối từ!")
    tu_vung, tu_map = doc_file_tu_vung()
    if not tu_vung:
        return
    
    da_su_dung = []  # Danh sách các từ đã sử dụng

    while True:
        tu_hien_tai = input("Nhập từ của bạn: ").strip().lower()
        
        if len(tu_hien_tai.split()) == 1:
            print("Bạn đã nhập 1 từ. Bạn thua!")
            break
        if not kiem_tra_tu_nhap(tu_hien_tai):
            print("Từ nhập vào phải có ít nhất 2 từ. Bạn thua!")
            break
        if not kiem_tra_tu_hop_le(tu_hien_tai):
            print("Từ nhập vào không hợp lệ. Bạn thua!")
            break
        if not kiem_tra_tu_trong_danh_sach(tu_hien_tai, tu_vung):
            print("Từ nhập vào không có trong danh sách từ vựng. Bạn thua!")
            break
        if da_su_dung and not kiem_tra_tu_noi_tiep(tu_hien_tai, da_su_dung[-1]):
            print(f"Từ nhập vào phải bắt đầu bằng '{tach_tu_cuoi(da_su_dung[-1])}'. Bạn thua!")
            break
        if tu_hien_tai in da_su_dung:
            print("Từ này đã được sử dụng. Bạn thua!")
            break
        
        da_su_dung.append(tu_hien_tai)
        tu_cuoi = tach_tu_cuoi(tu_hien_tai)
        if not tu_cuoi:
            print("Bạn chưa nhập từ hợp lệ. Bạn thua!")
            break

        danh_sach_phu_hop = tim_tat_ca_tu_bat_dau_bang(tu_cuoi, tu_map, da_su_dung)
        
        if danh_sach_phu_hop:
            win, seq = a_star_search(tu_cuoi, da_su_dung, "ai", tu_map, depth_limit=6)
            if win and seq:
                tu_ke_tiep = seq[0]
                print(f"AI nối (A*): {tu_ke_tiep}")
            # else:
            #     tu_ke_tiep = chon_tu_toi_uu(danh_sach_phu_hop, tu_map, da_su_dung)
            #     print(f"AI nối (Greedy): {tu_ke_tiep}")
            da_su_dung.append(tu_ke_tiep)
        else:
            print("AI không tìm được từ phù hợp. Bạn thắng!")
            break

# Hàm hiển thị menu và xử lý lựa chọn của người dùng
# def hien_thi_menu():
#     while True:
#         print("\n--- MENU ---")
#         print("Nhập 's' để bắt đầu trò chơi.")
#         print("Nhập 'q' để thoát.")
#         lua_chon = input("Lựa chọn của bạn: ").strip().lower()

#         if lua_chon == 's':
#             choi_noi_tu()
#             while True:
#                 print("\nBạn có muốn chơi lại không?")
#                 print("Nhập 'r' để chơi lại.")
#                 print("Nhập 'q' để thoát.")
#                 lua_chon = input("Lựa chọn của bạn: ").strip().lower()
#                 if lua_chon == 'r':
#                     choi_noi_tu()
#                 elif lua_chon == 'q':
#                     print("Cảm ơn bạn đã chơi! Hẹn gặp lại.")
#                     return
#                 else:
#                     print("Lựa chọn không hợp lệ. Vui lòng nhập lại.")
#         elif lua_chon == 'q':
#             print("Cảm ơn bạn đã chơi! Hẹn gặp lại.")
#             break
#         else:
#             print("Lựa chọn không hợp lệ. Vui lòng nhập lại.")

# # Chạy chương trình
# hien_thi_menu()
