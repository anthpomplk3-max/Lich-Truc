import streamlit as st
import pandas as pd
import calendar
import numpy as np
from datetime import datetime
import random

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Xếp lịch trực TBA 500kV", layout="wide")
st.title("🔄 Xếp lịch trực TBA 500kV - Hệ thống Tăng Ca Luân Phiên")

# --- DANH SÁCH NHÂN VIÊN ---
truong_kiep = ["Nguyễn Minh Dũng", "Ngô Quang Việt", "Nguyễn Trọng Tình", "Đặng Nhật Nam"]
van_hanh_vien = ["Trương Hoàng An", "Lê Vũ Vĩnh Lợi", "Nguyễn Cao Cường", "Trần Văn Võ"]
all_staff = truong_kiep + van_hanh_vien

# Ưu tiên tăng ca (Index thấp = Ưu tiên cao)
priority_map = {
    "Nguyễn Minh Dũng": 0, "Ngô Quang Việt": 1, "Nguyễn Trọng Tình": 2, "Đặng Nhật Nam": 3,
    "Trương Hoàng An": 0, "Lê Vũ Vĩnh Lợi": 1, "Nguyễn Cao Cường": 2, "Trần Văn Võ": 3
}

# --- KHỞI TẠO SESSION STATE ---
if 'init' not in st.session_state:
    st.session_state.update({
        'init': True,
        'schedule_data': None,
        'staff_stats': None,
        'day_off': {s: [] for s in all_staff},
        'business_trip': {s: [] for s in all_staff},
        'line_inspection': [],
        'night_shift_goals': {s: 0 for s in all_staff},
        'original_schedule': None
    })

# --- SIDEBAR CÀI ĐẶT ---
with st.sidebar:
    st.header("Thông tin tháng")
    month = st.selectbox("Tháng", range(1, 13), index=datetime.now().month-1)
    year = st.selectbox("Năm", range(2023, 2030), index=datetime.now().year-2023)
    num_days = calendar.monthrange(year, month)[1]
    
    st.header("Sự kiện cố định")
    training_day = st.slider("Ngày đào tạo nội bộ", 1, num_days, 15)
    tk_substitute_vhv = st.checkbox("Cho phép TK thay VHV khi cần thiết", value=True)

# --- CÁC HÀM LOGIC ---

def get_priority_score(name, staff_data, is_overtime):
    """Tính điểm ưu tiên: Ưu tiên người ít lần tăng ca trước (luân phiên)"""
    p_idx = priority_map.get(name, 99)
    overtime_val = staff_data[name].get('overtime_count', 0)
    
    if is_overtime:
        # Tăng ca: ưu tiên người có số lần tăng ca thấp nhất, sau đó mới xét đến tên
        return overtime_val * 100 + p_idx
    else:
        # Bình thường: ưu tiên theo tên
        return p_idx

def select_staff(available_list, staff_data, day, shift_type, is_overtime_mode):
    """Chọn nhân viên dựa trên quy tắc nghỉ, 24h và 17 công"""
    eligible = []
    for s in available_list:
        sd = staff_data[s]
        
        # 1. Chặn vượt 17 công nếu không ở chế độ tăng ca
        if not is_overtime_mode and sd['current_credits'] >= 17:
            continue
            
        # 2. Quy tắc 24h: Không trực ca tiếp theo nếu vừa trực ca trước đó cùng ngày
        if sd['last_day'] == day:
            continue
            
        # 3. Quy tắc ca liên tiếp
        max_cons = 4 if sd['night_goal'] >= 15 else 3
        if shift_type == 'night' and sd['cons_night'] >= max_cons: continue
        if shift_type == 'day' and sd['cons_day'] >= max_cons: continue
            
        eligible.append(s)
    
    if not eligible: return None
    
    # Sắp xếp theo điểm ưu tiên (luân phiên)
    eligible.sort(key=lambda x: get_priority_score(x, staff_data, is_overtime_mode))
    return eligible[0]

def update_stats(staff_data, name, day, shift_type):
    """Cập nhật dữ liệu sau mỗi ca trực"""
    sd = staff_data[name]
    sd['shifts'] += 1
    sd['last_day'] = day
    if shift_type == 'day':
        sd['day_shifts'] += 1
        sd['cons_day'] += 1
        sd['cons_night'] = 0
    else:
        sd['night_shifts'] += 1
        sd['cons_night'] += 1
        sd['cons_day'] = 0
    
    sd['current_credits'] = sd['admin_credits'] + sd['shifts']
    if sd['current_credits'] > 17:
        sd['overtime_count'] = sd['current_credits'] - 17

def run_scheduling(emergency_mode=False, start_day=1, history=None):
    """Hàm chạy thuật toán xếp lịch"""
    staff_data = {}
    for s in all_staff:
        # Tính công hành chính (Đào tạo + Kiểm tra + Công tác)
        li_count = len([g for g in st.session_state.line_inspection if (g['tk'] == s or g['vhv'] == s) and g['day']])
        bt_count = len(st.session_state.business_trip.get(s, []))
        admin_total = 1 + li_count + bt_count # 1 là công đào tạo
        
        staff_data[s] = {
            'shifts': 0, 'day_shifts': 0, 'night_shifts': 0,
            'cons_day': 0, 'cons_night': 0, 'last_day': -1,
            'admin_credits': admin_total, 'current_credits': admin_total,
            'overtime_count': 0, 'night_goal': st.session_state.night_shift_goals.get(s, 0),
            'unavailable': set(st.session_state.day_off.get(s, []) + st.session_state.business_trip.get(s, []) + 
                               [g['day'] for g in st.session_state.line_inspection if (g['tk'] == s or g['vhv'] == s) and g['day']])
        }

    schedule = []
    # Khôi phục lịch sử nếu là điều chỉnh đột xuất
    if emergency_mode and history:
        for shift in history:
            if shift['Ngày'] < start_day:
                schedule.append(shift)
                update_stats(staff_data, shift['Trưởng kiếp'], shift['Ngày'], 'day' if "Ngày" in shift['Ca'] else 'night')
                update_stats(staff_data, shift['Vận hành viên'], shift['Ngày'], 'day' if "Ngày" in shift['Ca'] else 'night')

    # Chế độ tăng ca kích hoạt khi có người đi công tác
    is_overtime_active = any(len(v) > 0 for v in st.session_state.business_trip.values())

    for d in range(start_day, num_days + 1):
        if d == training_day: continue
        
        for s_name, s_type in [("Ngày (6h-18h)", "day"), ("Đêm (18h-6h)", "night")]:
            avail_tk = [s for s in truong_kiep if d not in staff_data[s]['unavailable']]
            avail_vhv = [s for s in van_hanh_vien if d not in staff_data[s]['unavailable']]
            
            sel_tk = select_staff(avail_tk, staff_data, d, s_type, is_overtime_active)
            sel_vhv = select_staff(avail_vhv, staff_data, d, s_type, is_overtime_active)
            
            # Nếu thiếu VHV, cho phép TK thay thế
            if not sel_vhv and tk_substitute_vhv:
                rem_tk = [s for s in avail_tk if s != sel_tk]
                sel_vhv = select_staff(rem_tk, staff_data, d, s_type, is_overtime_active)

            if sel_tk and sel_vhv:
                update_stats(staff_data, sel_tk, d, s_type)
                update_stats(staff_data, sel_vhv, d, s_type)
                schedule.append({
                    'Ngày': d, 'Ca': s_name, 'Trưởng kiếp': sel_tk, 'Vận hành viên': sel_vhv,
                    'Ghi chú': "Tăng ca" if staff_data[sel_tk]['current_credits'] > 17 or staff_data[sel_vhv]['current_credits'] > 17 else ""
                })
    
    return schedule, staff_data

# --- GIAO DIỆN CHÍNH ---
t1, t2, t3 = st.tabs(["⚙️ Thiết lập", "📅 Lịch trực", "📊 Thống kê & Đột xuất"])

with t1:
    st.subheader("Ngày nghỉ & Mục tiêu ca đêm")
    c1, c2 = st.columns(2)
    for i, s in enumerate(all_staff):
        target_col = c1 if i < 4 else c2
        with target_col.expander(f"Cài đặt cho {s}"):
            st.session_state.day_off[s] = st.multiselect(f"Ngày nghỉ ({s})", range(1, num_days+1), key=f"off_{s}", default=st.session_state.day_off[s])
            st.session_state.night_shift_goals[s] = st.slider(f"Mục tiêu ca đêm ({s})", 0, 15, key=f"goal_{s}", value=st.session_state.night_shift_goals[s])

with t2:
    if st.button("🚀 Xếp lịch trực", type="primary"):
        with st.spinner("Đang tính toán..."):
            res_sch, res_stat = run_scheduling()
            st.session_state.schedule_data = res_sch
            st.session_state.staff_stats = res_stat
            st.session_state.original_schedule = res_sch
            st.success("Đã tạo lịch mới!")

    if st.session_state.schedule_data:
        df = pd.DataFrame(st.session_state.schedule_data)
        st.dataframe(df, use_container_width=True, height=500)

with t3:
    if st.session_state.staff_stats:
        st.subheader("Bảng tổng hợp công")
        stat_rows = []
        for s, d in st.session_state.staff_stats.items():
            stat_rows.append({
                "Nhân viên": s, "Tổng công": d['current_credits'], "Số ca": d['shifts'],
                "Ca đêm": d['night_shifts'], "Tăng ca": d['overtime_count']
            })
        st.table(pd.DataFrame(stat_rows))
        
        st.divider()
        st.subheader("🚨 Điều chỉnh công tác đột xuất")
        ce1, ce2, ce3 = st.columns(3)
        e_staff = ce1.selectbox("Nhân viên đi CT", all_staff)
        e_start = ce2.number_input("Từ ngày", 1, num_days, 1)
        e_end = ce3.number_input("Đến ngày", e_start, num_days, e_start)
        
        if st.button("🔄 Cập nhật & Tính lại tăng ca"):
            st.session_state.business_trip[e_staff] = list(set(st.session_state.business_trip[e_staff] + list(range(int(e_start), int(e_end) + 1))))
            new_sch, new_stat = run_scheduling(emergency_mode=True, start_day=int(e_start), history=st.session_state.original_schedule)
            st.session_state.schedule_data = new_sch
            st.session_state.staff_stats = new_stat
            st.rerun()
