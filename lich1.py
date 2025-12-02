import streamlit as st
import pandas as pd
import calendar
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict, deque
import random

# Tiêu đề ứng dụng
st.set_page_config(page_title="Xếp lịch trực TBA 500kV", layout="wide")
st.title("🔄 Xếp lịch trực TBA 500kV")
st.markdown("---")

# Danh sách nhân viên
truong_kiep = [
    "Nguyễn Trọng Tình",
    "Nguyễn Minh Dũng", 
    "Ngô Quang Việt",
    "Đặng Nhật Nam"
]

van_hanh_vien = [
    "Trương Hoàng An",
    "Lê Vũ Vĩnh Lợi",
    "Nguyễn Cao Cường",
    "Trần Văn Võ"
]

all_staff = truong_kiep + van_hanh_vien

# Khởi tạo session state
if 'schedule_created' not in st.session_state:
    st.session_state.schedule_created = False
if 'schedule_data' not in st.session_state:
    st.session_state.schedule_data = None
if 'staff_stats' not in st.session_state:
    st.session_state.staff_stats = None

# Sidebar cho thông tin nhập
with st.sidebar:
    st.header("Thông tin tháng")
    
    # Chọn tháng/năm
    col1, col2 = st.columns(2)
    with col1:
        month = st.selectbox("Tháng", range(1, 13), index=datetime.now().month-1)
    with col2:
        year = st.selectbox("Năm", range(2023, 2030), index=datetime.now().year-2023)
    
    # Tính số ngày trong tháng
    num_days = calendar.monthrange(year, month)[1]
    st.markdown(f"**Tháng {month}/{year} có {num_days} ngày**")
    st.markdown("---")
    
    st.header("Ngày đào tạo nội bộ")
    training_day = st.slider("Chọn ngày đào tạo", 1, num_days, 15)
    
    st.markdown("---")
    st.header("Hướng dẫn")
    st.info("""
    **Quy tắc xếp lịch:**
    1. Mỗi ca: 1 Trưởng kiếp + 1 Vận hành viên
    2. Tổng công: 17 công/người/tháng
    3. Tối đa 3 ca đêm liên tiếp
    4. Ưu tiên: 2 ca ngày + 2 ca đêm rồi nghỉ
    5. Mỗi người có 2 ngày hành chính
    6. Ngày đào tạo: tất cả có mặt
    """)

# Main content
tab1, tab2, tab3 = st.tabs(["📅 Chọn ngày nghỉ", "📊 Xếp lịch tự động", "📋 Thống kê"])

with tab1:
    st.subheader("Chọn ngày nghỉ cho từng nhân viên")
    st.warning("Mỗi người chọn tối đa 5 ngày nghỉ trong tháng")
    
    # Khởi tạo session state cho ngày nghỉ
    if 'day_off' not in st.session_state:
        st.session_state.day_off = {staff: [] for staff in all_staff}
    
    # Tạo layout cho từng nhân viên
    cols_per_row = 2
    for i in range(0, len(all_staff), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j in range(cols_per_row):
            if i + j < len(all_staff):
                staff = all_staff[i + j]
                with cols[j]:
                    st.markdown(f"**{staff}**")
                    
                    # Chọn ngày nghỉ
                    days_off = st.multiselect(
                        f"Ngày nghỉ - {staff}",
                        options=list(range(1, num_days + 1)),
                        default=st.session_state.day_off.get(staff, []),
                        key=f"off_{staff}_{month}_{year}"
                    )
                    
                    # Kiểm tra số ngày nghỉ
                    if len(days_off) > 5:
                        st.error(f"{staff} chọn quá 5 ngày nghỉ!")
                        days_off = days_off[:5]
                    
                    st.session_state.day_off[staff] = days_off
                    
                    # Chọn 2 ngày hành chính (không trùng ngày nghỉ và không trùng ngày đào tạo)
                    available_days = [d for d in range(1, num_days + 1) 
                                    if d not in days_off and d != training_day]
                    
                    admin_days = st.multiselect(
                        f"Ngày hành chính - {staff}",
                        options=available_days,
                        default=[],
                        max_selections=2,
                        key=f"admin_{staff}_{month}_{year}"
                    )
                    
                    # Lưu ngày hành chính
                    if f'admin_days_{staff}' not in st.session_state:
                        st.session_state[f'admin_days_{staff}'] = admin_days
                    else:
                        st.session_state[f'admin_days_{staff}'] = admin_days
                    
                    st.caption(f"Ngày nghỉ: {len(days_off)}/5 | HC: {len(admin_days)}/2")

# Thuật toán xếp lịch
def generate_schedule(month, year, training_day, day_off_dict):
    """Tạo lịch trực tự động"""
    num_days = calendar.monthrange(year, month)[1]
    schedule = []
    
    # Khởi tạo queue luân phiên
    tk_queue = deque(truong_kiep)
    vhv_queue = deque(van_hanh_vien)
    
    # Thống kê công việc
    staff_work_count = {staff: {'day': 0, 'night': 0, 'total': 0, 'consecutive_night': 0} for staff in all_staff}
    staff_last_shifts = {staff: {'type': None, 'consecutive': 0} for staff in all_staff}
    
    # Mục tiêu mỗi người 17 ca
    target_shifts = 17
    
    # Tạo lịch cho từng ngày
    for day in range(1, num_days + 1):
        # Kiểm tra ngày đào tạo
        if day == training_day:
            schedule.append({
                'Ngày': day,
                'Thứ': calendar.day_name[calendar.weekday(year, month, day)],
                'Ca': 'Đào tạo',
                'Trưởng kiếp': 'Tất cả',
                'Vận hành viên': 'Tất cả',
                'Ghi chú': 'Đào tạo nội bộ'
            })
            continue
        
        # Tìm người có sẵn cho ngày này
        available_tk = [tk for tk in truong_kiep if day not in day_off_dict.get(tk, [])]
        available_vhv = [vhv for vhv in van_hanh_vien if day not in day_off_dict.get(vhv, [])]
        
        # Xử lý ca ngày
        if available_tk and available_vhv:
            # Ưu tiên người ít ca nhất
            available_tk.sort(key=lambda x: staff_work_count[x]['total'])
            available_vhv.sort(key=lambda x: staff_work_count[x]['total'])
            
            # Chọn người ít ca nhất
            selected_tk = available_tk[0]
            selected_vhv = available_vhv[0]
            
            # Kiểm tra ca đêm liên tiếp
            if staff_last_shifts[selected_tk]['type'] == 'night' and staff_last_shifts[selected_tk]['consecutive'] >= 3:
                # Tìm người khác nếu có thể
                for tk in available_tk[1:]:
                    if staff_last_shifts[tk]['type'] != 'night' or staff_last_shifts[tk]['consecutive'] < 3:
                        selected_tk = tk
                        break
            
            if staff_last_shifts[selected_vhv]['type'] == 'night' and staff_last_shifts[selected_vhv]['consecutive'] >= 3:
                for vhv in available_vhv[1:]:
                    if staff_last_shifts[vhv]['type'] != 'night' or staff_last_shifts[vhv]['consecutive'] < 3:
                        selected_vhv = vhv
                        break
            
            # Cập nhật thống kê
            staff_work_count[selected_tk]['day'] += 1
            staff_work_count[selected_tk]['total'] += 1
            staff_work_count[selected_vhv]['day'] += 1
            staff_work_count[selected_vhv]['total'] += 1
            
            # Cập nhật ca liên tiếp
            if staff_last_shifts[selected_tk]['type'] == 'day':
                staff_last_shifts[selected_tk]['consecutive'] += 1
            else:
                staff_last_shifts[selected_tk]['consecutive'] = 1
            staff_last_shifts[selected_tk]['type'] = 'day'
            
            if staff_last_shifts[selected_vhv]['type'] == 'day':
                staff_last_shifts[selected_vhv]['consecutive'] += 1
            else:
                staff_last_shifts[selected_vhv]['consecutive'] = 1
            staff_last_shifts[selected_vhv]['type'] = 'day'
            
            schedule.append({
                'Ngày': day,
                'Thứ': calendar.day_name[calendar.weekday(year, month, day)],
                'Ca': 'Ngày (6h-18h)',
                'Trưởng kiếp': selected_tk,
                'Vận hành viên': selected_vhv,
                'Ghi chú': ''
            })
        
        # Xử lý ca đêm
        if available_tk and available_vhv:
            # Ưu tiên người khác với ca ngày để tránh trùng
            available_tk_night = [tk for tk in available_tk if staff_work_count[tk]['total'] < target_shifts]
            available_vhv_night = [vhv for vhv in available_vhv if staff_work_count[vhv]['total'] < target_shifts]
            
            if available_tk_night and available_vhv_night:
                # Sắp xếp theo số ca đêm ít nhất
                available_tk_night.sort(key=lambda x: staff_work_count[x]['night'])
                available_vhv_night.sort(key=lambda x: staff_work_count[x]['night'])
                
                selected_tk_night = available_tk_night[0]
                selected_vhv_night = available_vhv_night[0]
                
                # Kiểm tra ca đêm liên tiếp
                if staff_last_shifts[selected_tk_night]['type'] == 'night' and staff_last_shifts[selected_tk_night]['consecutive'] >= 3:
                    for tk in available_tk_night[1:]:
                        if staff_last_shifts[tk]['type'] != 'night' or staff_last_shifts[tk]['consecutive'] < 3:
                            selected_tk_night = tk
                            break
                
                if staff_last_shifts[selected_vhv_night]['type'] == 'night' and staff_last_shifts[selected_vhv_night]['consecutive'] >= 3:
                    for vhv in available_vhv_night[1:]:
                        if staff_last_shifts[vhv]['type'] != 'night' or staff_last_shifts[vhv]['consecutive'] < 3:
                            selected_vhv_night = vhv
                            break
                
                # Cập nhật thống kê
                staff_work_count[selected_tk_night]['night'] += 1
                staff_work_count[selected_tk_night]['total'] += 1
                staff_work_count[selected_vhv_night]['night'] += 1
                staff_work_count[selected_vhv_night]['total'] += 1
                
                # Cập nhật ca liên tiếp
                if staff_last_shifts[selected_tk_night]['type'] == 'night':
                    staff_last_shifts[selected_tk_night]['consecutive'] += 1
                else:
                    staff_last_shifts[selected_tk_night]['consecutive'] = 1
                staff_last_shifts[selected_tk_night]['type'] = 'night'
                
                if staff_last_shifts[selected_vhv_night]['type'] == 'night':
                    staff_last_shifts[selected_vhv_night]['consecutive'] += 1
                else:
                    staff_last_shifts[selected_vhv_night]['consecutive'] = 1
                staff_last_shifts[selected_vhv_night]['type'] = 'night'
                
                schedule.append({
                    'Ngày': day,
                    'Thứ': calendar.day_name[calendar.weekday(year, month, day)],
                    'Ca': 'Đêm (18h-6h)',
                    'Trưởng kiếp': selected_tk_night,
                    'Vận hành viên': selected_vhv_night,
                    'Ghi chú': ''
                })
    
    return schedule, staff_work_count

with tab2:
    st.subheader("Lịch trực tháng")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🎯 Tạo lịch trực tự động", type="primary"):
            with st.spinner("Đang tạo lịch trực..."):
                # Lấy dữ liệu ngày nghỉ từ session state
                day_off_dict = st.session_state.day_off
                
                # Tạo lịch
                schedule, stats = generate_schedule(month, year, training_day, day_off_dict)
                
                # Lưu vào session state
                st.session_state.schedule_data = schedule
                st.session_state.staff_stats = stats
                st.session_state.schedule_created = True
                
                st.success("✅ Đã tạo lịch trực thành công!")
    
    if st.session_state.schedule_created and st.session_state.schedule_data:
        # Hiển thị lịch
        df_schedule = pd.DataFrame(st.session_state.schedule_data)
        
        # Tô màu cho các loại ca
        def color_ca(val):
            if 'Ngày' in str(val):
                return 'background-color: #e6ffe6'
            elif 'Đêm' in str(val):
                return 'background-color: #ffe6e6'
            elif 'Đào tạo' in str(val):
                return 'background-color: #ffffcc'
            return ''
        
        styled_df = df_schedule.style.applymap(color_ca, subset=['Ca'])
        st.dataframe(styled_df, use_container_width=True, height=800)
        
        # Nút tải xuống
        csv = df_schedule.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Tải lịch trực (CSV)",
            data=csv,
            file_name=f"lich_truc_TBA_500kV_{month}_{year}.csv",
            mime="text/csv"
        )
        
        # Hiển thị thống kê
        st.subheader("📈 Thống kê phân công")
        
        if st.session_state.staff_stats:
            stats_data = []
            for staff, stats in st.session_state.staff_stats.items():
                stats_data.append({
                    'Nhân viên': staff,
                    'Tổng ca': stats['total'],
                    'Ca ngày': stats['day'],
                    'Ca đêm': stats['night'],
                    'Ngày nghỉ': len(st.session_state.day_off.get(staff, [])),
                    'Vai trò': 'Trưởng kiếp' if staff in truong_kiep else 'Vận hành viên'
                })
            
            df_stats = pd.DataFrame(stats_data)
            st.dataframe(df_stats, use_container_width=True)
            
            # Biểu đồ phân bố ca
            st.subheader("📊 Phân bố công việc")
            chart_data = pd.DataFrame({
                'Tên': [s.split()[-1] for s in all_staff],
                'Ca ngày': [st.session_state.staff_stats[s]['day'] for s in all_staff],
                'Ca đêm': [st.session_state.staff_stats[s]['night'] for s in all_staff]
            })
            st.bar_chart(chart_data.set_index('Tên'))
    else:
        st.info("👈 Vui lòng chọn ngày nghỉ cho nhân viên ở Tab 1, sau đó nhấn nút 'Tạo lịch trực tự động'")

with tab3:
    st.subheader("Thống kê tổng quan")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Tổng nhân sự", len(all_staff))
    
    with col2:
        st.metric("Trưởng kiếp", len(truong_kiep))
    
    with col3:
        st.metric("Vận hành viên", len(van_hanh_vien))
    
    with col4:
        st.metric("Ngày đào tạo", f"Ngày {training_day}")
    
    # Hiển thị ngày nghỉ của từng người
    st.subheader("📋 Danh sách ngày nghỉ & hành chính")
    
    off_days_data = []
    for staff in all_staff:
        days_off = st.session_state.day_off.get(staff, [])
        admin_days = st.session_state.get(f'admin_days_{staff}', [])
        
        off_days_data.append({
            'Nhân viên': staff,
            'Số ngày nghỉ': len(days_off),
            'Ngày nghỉ': ', '.join(map(str, sorted(days_off))) if days_off else '-',
            'Số ngày HC': len(admin_days),
            'Ngày HC': ', '.join(map(str, sorted(admin_days))) if admin_days else '-',
            'Vai trò': 'Trưởng kiếp' if staff in truong_kiep else 'VHV'
        })
    
    df_off_days = pd.DataFrame(off_days_data)
    st.dataframe(df_off_days, use_container_width=True)
    
    # Kiểm tra vi phạm
    st.subheader("🔍 Kiểm tra ràng buộc")
    
    violations = []
    warnings = []
    
    # Kiểm tra số ngày nghỉ
    for staff in all_staff:
        days_off = st.session_state.day_off.get(staff, [])
        if len(days_off) > 5:
            violations.append(f"❌ {staff}: Chọn {len(days_off)} ngày nghỉ (vượt quá 5 ngày)")
        
        # Kiểm tra ngày hành chính trùng ngày nghỉ
        admin_days = st.session_state.get(f'admin_days_{staff}', [])
        overlap = set(days_off) & set(admin_days)
        if overlap:
            violations.append(f"❌ {staff}: Ngày hành chính trùng ngày nghỉ: {overlap}")
    
    # Kiểm tra tổng số công nếu đã có lịch
    if st.session_state.schedule_created and st.session_state.staff_stats:
        for staff in all_staff:
            stats = st.session_state.staff_stats[staff]
            if stats['total'] > 18:  # Cho phép ±1 ca so với 17
                warnings.append(f"⚠️ {staff}: Có {stats['total']} ca (mục tiêu: 17)")
    
    if violations:
        st.error("**Vi phạm:**")
        for v in violations:
            st.write(v)
    else:
        st.success("✓ Không có vi phạm về ngày nghỉ")
    
    if warnings:
        st.warning("**Cảnh báo:**")
        for w in warnings:
            st.write(w)

# Footer
st.markdown("---")
st.caption("""
**Hệ thống xếp lịch trực TBA 500kV - Phiên bản 2.0**  
*Thuật toán: Ưu tiên cân bằng công việc, hạn chế ca đêm liên tiếp*
""")