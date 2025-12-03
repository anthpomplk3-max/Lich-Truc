import streamlit as st
import pandas as pd
import calendar
import numpy as np
from datetime import datetime
from collections import defaultdict, deque
import random

# Tiêu đề ứng dụng
st.set_page_config(page_title="Xếp lịch trực TBA 500kV", layout="wide")
st.title("🔄 Xếp lịch trực TBA 500kV - Giao diện ngang")
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
if 'horizontal_schedule' not in st.session_state:
    st.session_state.horizontal_schedule = None
if 'day_off' not in st.session_state:
    st.session_state.day_off = {staff: [] for staff in all_staff}
if 'business_trip' not in st.session_state:
    st.session_state.business_trip = {staff: [] for staff in all_staff}

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
    st.header("Cài đặt phân công")
    auto_adjust = st.checkbox("Tự động điều chỉnh công khi có người công tác", value=True)
    
    st.markdown("---")
    st.header("Hướng dẫn")
    st.info("""
    **Quy tắc xếp lịch:**
    1. Mỗi ca: 1 Trưởng kiếp + 1 Vận hành viên
    2. Tổng công: 17 công/người/tháng
    3. Không làm việc 24h liên tục
    4. Tối đa 3 ca đêm liên tiếp
    5. Mỗi người có 2 ngày hành chính
    6. Ngày đào tạo: tất cả có mặt
    7. Người công tác: không tham gia trực
    """)

# Hàm chuyển đổi lịch sang dạng ngang
def convert_to_horizontal_schedule(schedule_data, num_days, year, month):
    """Chuyển lịch trực từ dạng dọc sang dạng ngang"""
    horizontal_data = {}
    
    # Khởi tạo cấu trúc dữ liệu
    for day in range(1, num_days + 1):
        day_key = f"Ngày {day}"
        horizontal_data[day_key] = {
            'Ca ngày (N) - TK': '',
            'Ca ngày (N) - VHV': '',
            'Ca đêm (Đ) - TK': '',
            'Ca đêm (Đ) - VHV': '',
            'Ghi chú': ''
        }
    
    # Điền dữ liệu vào bảng ngang
    for schedule in schedule_data:
        day = schedule['Ngày']
        shift_type = schedule['Ca']
        
        if shift_type == 'Đào tạo':
            horizontal_data[f"Ngày {day}"]['Ghi chú'] = 'ĐÀO TẠO'
            horizontal_data[f"Ngày {day}"]['Ca ngày (N) - TK'] = 'TẤT CẢ'
            horizontal_data[f"Ngày {day}"]['Ca ngày (N) - VHV'] = 'TẤT CẢ'
            horizontal_data[f"Ngày {day}"]['Ca đêm (Đ) - TK'] = 'TẤT CẢ'
            horizontal_data[f"Ngày {day}"]['Ca đêm (Đ) - VHV'] = 'TẤT CẢ'
        elif 'Ngày' in shift_type:
            horizontal_data[f"Ngày {day}"]['Ca ngày (N) - TK'] = schedule['Trưởng kiếp']
            horizontal_data[f"Ngày {day}"]['Ca ngày (N) - VHV'] = schedule['Vận hành viên']
        elif 'Đêm' in shift_type:
            horizontal_data[f"Ngày {day}"]['Ca đêm (Đ) - TK'] = schedule['Trưởng kiếp']
            horizontal_data[f"Ngày {day}"]['Ca đêm (Đ) - VHV'] = schedule['Vận hành viên']
    
    # Chuyển đổi sang DataFrame
    df_horizontal = pd.DataFrame(horizontal_data).T
    
    # Thêm cột Thứ
    days_of_week = []
    for day in range(1, num_days + 1):
        weekday = calendar.day_name[calendar.weekday(year, month, day)]
        # Viết tắt tên thứ
        vietnamese_days = {
            'Monday': 'T2', 'Tuesday': 'T3', 'Wednesday': 'T4',
            'Thursday': 'T5', 'Friday': 'T6', 'Saturday': 'T7', 'Sunday': 'CN'
        }
        days_of_week.append(vietnamese_days.get(weekday, weekday))
    
    df_horizontal.insert(0, 'Thứ', days_of_week)
    df_horizontal.index.name = 'Ngày'
    
    return df_horizontal

# Thuật toán xếp lịch nâng cao
def generate_advanced_schedule(month, year, training_day, day_off_dict, business_trip_dict):
    """Tạo lịch trực tự động với các ràng buộc nâng cao"""
    num_days = calendar.monthrange(year, month)[1]
    schedule = []
    
    # Khởi tạo dữ liệu nhân viên
    staff_data = {}
    for staff in all_staff:
        staff_data[staff] = {
            'role': 'TK' if staff in truong_kiep else 'VHV',
            'total_shifts': 0,
            'day_shifts': 0,
            'night_shifts': 0,
            'consecutive_night': 0,
            'last_shift': None,
            'last_shift_day': None,
            'target_shifts': 17,
            'unavailable_days': set(day_off_dict.get(staff, []) + business_trip_dict.get(staff, [])),
            'business_trip_days': set(business_trip_dict.get(staff, []))
        }
    
    # Điều chỉnh mục tiêu nếu có người công tác
    for tk in truong_kiep:
        business_days = len(staff_data[tk]['business_trip_days'])
        if business_days > 0:
            staff_data[tk]['target_shifts'] = max(0, 17 - (business_days * 2))
    
    for vhv in van_hanh_vien:
        business_days = len(staff_data[vhv]['business_trip_days'])
        if business_days > 0:
            staff_data[vhv]['target_shifts'] = max(0, 17 - (business_days * 2))
    
    # Tăng mục tiêu cho những người không công tác
    total_tk_business_days = sum(len(staff_data[tk]['business_trip_days']) for tk in truong_kiep)
    total_vhv_business_days = sum(len(staff_data[vhv]['business_trip_days']) for vhv in van_hanh_vien)
    
    if total_tk_business_days > 0:
        tk_without_business = [tk for tk in truong_kiep if len(staff_data[tk]['business_trip_days']) == 0]
        if tk_without_business:
            additional_shifts = total_tk_business_days * 2
            per_person_additional = max(1, additional_shifts // len(tk_without_business))
            for tk in tk_without_business:
                staff_data[tk]['target_shifts'] = min(20, 17 + per_person_additional)
    
    if total_vhv_business_days > 0:
        vhv_without_business = [vhv for vhv in van_hanh_vien if len(staff_data[vhv]['business_trip_days']) == 0]
        if vhv_without_business:
            additional_shifts = total_vhv_business_days * 2
            per_person_additional = max(1, additional_shifts // len(vhv_without_business))
            for vhv in vhv_without_business:
                staff_data[vhv]['target_shifts'] = min(20, 17 + per_person_additional)
    
    # Tạo lịch cho từng ngày
    for day in range(1, num_days + 1):
        if day == training_day:
            weekday_name = calendar.day_name[calendar.weekday(year, month, day)]
            schedule.append({
                'Ngày': day,
                'Thứ': weekday_name,
                'Ca': 'Đào tạo',
                'Trưởng kiếp': 'Tất cả',
                'Vận hành viên': 'Tất cả',
                'Ghi chú': 'Đào tạo nội bộ'
            })
            continue
        
        # Xử lý ca ngày
        available_tk = [tk for tk in truong_kiep 
                       if day not in staff_data[tk]['unavailable_days']]
        available_vhv = [vhv for vhv in van_hanh_vien 
                        if day not in staff_data[vhv]['unavailable_days']]
        
        if available_tk and available_vhv:
            selected_tk = select_staff_for_shift(
                available_tk, staff_data, day, 'day', 'TK'
            )
            selected_vhv = select_staff_for_shift(
                available_vhv, staff_data, day, 'day', 'VHV'
            )
            
            if selected_tk and selected_vhv:
                staff_data[selected_tk]['total_shifts'] += 1
                staff_data[selected_tk]['day_shifts'] += 1
                staff_data[selected_tk]['last_shift'] = 'day'
                staff_data[selected_tk]['last_shift_day'] = day
                
                staff_data[selected_vhv]['total_shifts'] += 1
                staff_data[selected_vhv]['day_shifts'] += 1
                staff_data[selected_vhv]['last_shift'] = 'day'
                staff_data[selected_vhv]['last_shift_day'] = day
                
                if staff_data[selected_tk]['last_shift'] == 'day':
                    staff_data[selected_tk]['consecutive_night'] = 0
                if staff_data[selected_vhv]['last_shift'] == 'day':
                    staff_data[selected_vhv]['consecutive_night'] = 0
                
                weekday_name = calendar.day_name[calendar.weekday(year, month, day)]
                schedule.append({
                    'Ngày': day,
                    'Thứ': weekday_name,
                    'Ca': 'Ngày (6h-18h)',
                    'Trưởng kiếp': selected_tk,
                    'Vận hành viên': selected_vhv,
                    'Ghi chú': ''
                })
        
        # Xử lý ca đêm
        available_tk_night = [tk for tk in truong_kiep 
                            if day not in staff_data[tk]['unavailable_days']
                            and not (staff_data[tk]['last_shift'] == 'day' and staff_data[tk]['last_shift_day'] == day)]
        
        available_vhv_night = [vhv for vhv in van_hanh_vien 
                             if day not in staff_data[vhv]['unavailable_days']
                             and not (staff_data[vhv]['last_shift'] == 'day' and staff_data[vhv]['last_shift_day'] == day)]
        
        if available_tk_night and available_vhv_night:
            selected_tk_night = select_staff_for_shift(
                available_tk_night, staff_data, day, 'night', 'TK'
            )
            selected_vhv_night = select_staff_for_shift(
                available_vhv_night, staff_data, day, 'night', 'VHV'
            )
            
            if selected_tk_night and selected_vhv_night:
                staff_data[selected_tk_night]['total_shifts'] += 1
                staff_data[selected_tk_night]['night_shifts'] += 1
                staff_data[selected_tk_night]['last_shift'] = 'night'
                staff_data[selected_tk_night]['last_shift_day'] = day
                staff_data[selected_tk_night]['consecutive_night'] += 1
                
                staff_data[selected_vhv_night]['total_shifts'] += 1
                staff_data[selected_vhv_night]['night_shifts'] += 1
                staff_data[selected_vhv_night]['last_shift'] = 'night'
                staff_data[selected_vhv_night]['last_shift_day'] = day
                staff_data[selected_vhv_night]['consecutive_night'] += 1
                
                if staff_data[selected_tk_night]['consecutive_night'] > 3:
                    staff_data[selected_tk_night]['consecutive_night'] = 3
                if staff_data[selected_vhv_night]['consecutive_night'] > 3:
                    staff_data[selected_vhv_night]['consecutive_night'] = 3
                
                weekday_name = calendar.day_name[calendar.weekday(year, month, day)]
                schedule.append({
                    'Ngày': day,
                    'Thứ': weekday_name,
                    'Ca': 'Đêm (18h-6h)',
                    'Trưởng kiếp': selected_tk_night,
                    'Vận hành viên': selected_vhv_night,
                    'Ghi chú': ''
                })
    
    return schedule, staff_data

def select_staff_for_shift(available_staff, staff_data, day, shift_type, role):
    """Chọn nhân viên phù hợp cho ca làm việc"""
    if not available_staff:
        return None
    
    filtered_staff = []
    for staff in available_staff:
        data = staff_data[staff]
        
        if data['total_shifts'] >= data['target_shifts']:
            continue
        
        if shift_type == 'night' and data['consecutive_night'] >= 3:
            continue
        
        if shift_type == 'night' and data['last_shift'] == 'day' and data['last_shift_day'] == day:
            continue
        
        filtered_staff.append(staff)
    
    if not filtered_staff:
        return None
    
    filtered_staff.sort(key=lambda x: (
        staff_data[x]['total_shifts'],
        -abs(staff_data[x]['target_shifts'] - staff_data[x]['total_shifts'])
    ))
    
    return filtered_staff[0]

# Tạo tabs - ĐẶT TRƯỚC KHI SỬ DỤNG
tab1, tab2, tab3, tab4 = st.tabs([
    "📅 Chọn ngày nghỉ & Công tác", 
    "📊 Xếp lịch tự động", 
    "📋 Thống kê", 
    "📱 Xem lịch ngang"
])

with tab1:
    st.subheader("Chọn ngày nghỉ & Công tác cho từng nhân viên")
    
    # Tạo 2 cột cho 2 loại nhân viên
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Trưởng kiếp")
        for tk in truong_kiep:
            with st.expander(f"**{tk}**", expanded=False):
                days_off = st.multiselect(
                    f"Ngày nghỉ - {tk}",
                    options=list(range(1, num_days + 1)),
                    default=st.session_state.day_off.get(tk, []),
                    key=f"off_{tk}_{month}_{year}"
                )
                
                if len(days_off) > 5:
                    st.error(f"{tk} chọn quá 5 ngày nghỉ!")
                    days_off = days_off[:5]
                
                st.session_state.day_off[tk] = days_off
                
                business_days = st.multiselect(
                    f"Ngày công tác - {tk}",
                    options=[d for d in range(1, num_days + 1) if d not in days_off and d != training_day],
                    default=st.session_state.business_trip.get(tk, []),
                    key=f"business_{tk}_{month}_{year}"
                )
                
                st.session_state.business_trip[tk] = business_days
                
                st.caption(f"Ngày nghỉ: {len(days_off)}/5 | Công tác: {len(business_days)}")
    
    with col2:
        st.markdown("### Vận hành viên")
        for vhv in van_hanh_vien:
            with st.expander(f"**{vhv}**", expanded=False):
                days_off = st.multiselect(
                    f"Ngày nghỉ - {vhv}",
                    options=list(range(1, num_days + 1)),
                    default=st.session_state.day_off.get(vhv, []),
                    key=f"off_{vhv}_{month}_{year}"
                )
                
                if len(days_off) > 5:
                    st.error(f"{vhv} chọn quá 5 ngày nghỉ!")
                    days_off = days_off[:5]
                
                st.session_state.day_off[vhv] = days_off
                
                business_days = st.multiselect(
                    f"Ngày công tác - {vhv}",
                    options=[d for d in range(1, num_days + 1) if d not in days_off and d != training_day],
                    default=st.session_state.business_trip.get(vhv, []),
                    key=f"business_{vhv}_{month}_{year}"
                )
                
                st.session_state.business_trip[vhv] = business_days
                
                st.caption(f"Ngày nghỉ: {len(days_off)}/5 | Công tác: {len(business_days)}")

with tab2:
    st.subheader("Tạo lịch trực tự động")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🎯 Tạo lịch trực tự động", type="primary", use_container_width=True):
            with st.spinner("Đang tạo lịch trực nâng cao..."):
                day_off_dict = st.session_state.day_off
                business_trip_dict = st.session_state.business_trip
                
                schedule, staff_data = generate_advanced_schedule(
                    month, year, training_day, day_off_dict, business_trip_dict
                )
                
                # Tạo lịch ngang
                horizontal_schedule = convert_to_horizontal_schedule(schedule, num_days, year, month)
                
                # Lưu vào session state
                st.session_state.schedule_data = schedule
                st.session_state.staff_stats = staff_data
                st.session_state.horizontal_schedule = horizontal_schedule
                st.session_state.schedule_created = True
                
                st.success("✅ Đã tạo lịch trực thành công!")
    
    if st.session_state.schedule_created and st.session_state.schedule_data:
        st.subheader("Lịch trực dạng dọc (chi tiết)")
        df_schedule = pd.DataFrame(st.session_state.schedule_data)
        
        # Hiển thị bảng với màu sắc đơn giản
        st.dataframe(df_schedule, use_container_width=True, height=400)
        
        # Nút tải xuống
        csv = df_schedule.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Tải lịch trực (CSV)",
            data=csv,
            file_name=f"lich_truc_TBA_500kV_{month}_{year}.csv",
            mime="text/csv",
            use_container_width=True
        )

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
    
    if st.session_state.schedule_created and st.session_state.staff_stats:
        st.subheader("📈 Thống kê phân công chi tiết")
        
        stats_data = []
        for staff, data in st.session_state.staff_stats.items():
            stats_data.append({
                'Nhân viên': staff,
                'Vai trò': data['role'],
                'Mục tiêu': data['target_shifts'],
                'Tổng ca': data['total_shifts'],
                'Ca ngày (N)': data['day_shifts'],
                'Ca đêm (Đ)': data['night_shifts'],
                'Công tác': len(data['business_trip_days']),
                'Chênh lệch': data['total_shifts'] - data['target_shifts']
            })
        
        df_stats = pd.DataFrame(stats_data)
        st.dataframe(df_stats, use_container_width=True)
        
        st.subheader("📊 Tóm tắt phân công")
        col1, col2, col3, col4 = st.columns(4)
        
        total_shifts = sum(data['total_shifts'] for data in st.session_state.staff_stats.values())
        total_target = sum(data['target_shifts'] for data in st.session_state.staff_stats.values())
        total_business = sum(len(data['business_trip_days']) for data in st.session_state.staff_stats.values())
        
        with col1:
            st.metric("Tổng số ca", total_shifts)
        with col2:
            st.metric("Tổng mục tiêu", total_target)
        with col3:
            st.metric("Ngày công tác", total_business)
        with col4:
            diff = total_shifts - total_target
            st.metric("Chênh lệch", diff, delta_color="normal" if diff == 0 else "inverse")
    else:
        st.info("👈 Vui lòng tạo lịch trực ở Tab 2")

with tab4:
    st.subheader("📱 Lịch trực dạng ngang (N - Ngày, Đ - Đêm)")
    
    if st.session_state.schedule_created and st.session_state.horizontal_schedule is not None:
        # Hiển thị lịch ngang với màu sắc
        df_horizontal = st.session_state.horizontal_schedule
        
        # Tạo một bản sao để hiển thị
        display_df = df_horizontal.copy()
        
        # Hiển thị với CSS đơn giản
        st.markdown("""
        <style>
        .horizontal-scroll {
            overflow-x: auto;
            white-space: nowrap;
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 20px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="horizontal-scroll">', unsafe_allow_html=True)
        
        # Hiển thị DataFrame với chiều cao tự động
        st.dataframe(
            display_df,
            use_container_width=True,
            height=min(400, 100 + len(display_df) * 35)
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Hiển thị chú thích
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **Ký hiệu:**
            - **N**: Ca ngày (6h-18h)
            - **Đ**: Ca đêm (18h-6h)
            - **TK**: Trưởng kiếp
            - **VHV**: Vận hành viên
            - **T7**: Thứ 7
            - **CN**: Chủ nhật
            """)
        
        with col2:
            st.markdown("""
            **Ghi chú:**
            - "TẤT CẢ": Ngày đào tạo
            - Ô trống: Không có phân công
            - Mỗi cột là một ngày trong tháng
            """)
        
        # Nút tải xuống lịch ngang
        st.markdown("---")
        csv_horizontal = df_horizontal.to_csv(encoding='utf-8-sig')
        st.download_button(
            label="📥 Tải lịch ngang (CSV)",
            data=csv_horizontal,
            file_name=f"lich_truc_ngang_TBA_500kV_{month}_{year}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("👈 Vui lòng tạo lịch trực ở Tab 2 trước")

# Footer
st.markdown("---")
st.caption("""
**Hệ thống xếp lịch trực TBA 500kV - Phiên bản 4.0 - Giao diện ngang**  
*Hiển thị đầy đủ 30 ngày với ca ngày (N) và ca đêm (Đ)*
""")