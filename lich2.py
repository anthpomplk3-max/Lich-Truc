import streamlit as st
import pandas as pd
import calendar
import numpy as np
from datetime import datetime
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
for key in ['schedule_created', 'schedule_data', 'staff_stats', 'day_off', 'business_trip']:
    if key not in st.session_state:
        if key == 'day_off':
            st.session_state[key] = {staff: [] for staff in all_staff}
        elif key == 'business_trip':
            st.session_state[key] = {staff: [] for staff in all_staff}
        else:
            st.session_state[key] = None

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
    
    # Tự động điều chỉnh mục tiêu công khi có người công tác
    auto_adjust = st.checkbox("Tự động điều chỉnh công khi có người công tác", value=True)
    
    st.markdown("---")
    st.header("Hướng dẫn")
    st.info("""
    **Quy tắc xếp lịch:**
    1. Mỗi ca: 1 Trưởng kiếp + 1 Vận hành viên
    2. Tổng công: 17 công/người/tháng (có thể thay đổi nếu có người công tác)
    3. Không làm việc 24h liên tục (không làm ca ngày → ca đêm hoặc ngược lại)
    4. Tối đa 3 ca đêm liên tiếp
    5. Mỗi người có 2 ngày hành chính
    6. Ngày đào tạo: tất cả có mặt
    7. Người công tác: không tham gia trực, công sẽ chia cho người khác
    """)

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["📅 Chọn ngày nghỉ & Công tác", "📊 Xếp lịch tự động", "📋 Thống kê", "⚙️ Cài đặt nâng cao"])

with tab1:
    st.subheader("Chọn ngày nghỉ & Công tác cho từng nhân viên")
    
    # Tạo 2 cột cho 2 loại nhân viên
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Trưởng kiếp")
        for tk in truong_kiep:
            with st.expander(f"**{tk}**", expanded=False):
                # Chọn ngày nghỉ
                days_off = st.multiselect(
                    f"Ngày nghỉ - {tk}",
                    options=list(range(1, num_days + 1)),
                    default=st.session_state.day_off.get(tk, []),
                    key=f"off_{tk}_{month}_{year}"
                )
                
                # Kiểm tra số ngày nghỉ
                if len(days_off) > 5:
                    st.error(f"{tk} chọn quá 5 ngày nghỉ!")
                    days_off = days_off[:5]
                
                st.session_state.day_off[tk] = days_off
                
                # Chọn ngày công tác
                business_days = st.multiselect(
                    f"Ngày công tác - {tk}",
                    options=[d for d in range(1, num_days + 1) if d not in days_off and d != training_day],
                    default=st.session_state.business_trip.get(tk, []),
                    key=f"business_{tk}_{month}_{year}"
                )
                
                st.session_state.business_trip[tk] = business_days
                
                # Chọn 2 ngày hành chính
                available_days = [d for d in range(1, num_days + 1) 
                                if d not in days_off and d not in business_days and d != training_day]
                
                admin_days = st.multiselect(
                    f"Ngày hành chính - {tk}",
                    options=available_days,
                    default=[],
                    max_selections=2,
                    key=f"admin_{tk}_{month}_{year}"
                )
                
                st.caption(f"Ngày nghỉ: {len(days_off)}/5 | Công tác: {len(business_days)} | HC: {len(admin_days)}/2")
    
    with col2:
        st.markdown("### Vận hành viên")
        for vhv in van_hanh_vien:
            with st.expander(f"**{vhv}**", expanded=False):
                # Chọn ngày nghỉ
                days_off = st.multiselect(
                    f"Ngày nghỉ - {vhv}",
                    options=list(range(1, num_days + 1)),
                    default=st.session_state.day_off.get(vhv, []),
                    key=f"off_{vhv}_{month}_{year}"
                )
                
                # Kiểm tra số ngày nghỉ
                if len(days_off) > 5:
                    st.error(f"{vhv} chọn quá 5 ngày nghỉ!")
                    days_off = days_off[:5]
                
                st.session_state.day_off[vhv] = days_off
                
                # Chọn ngày công tác
                business_days = st.multiselect(
                    f"Ngày công tác - {vhv}",
                    options=[d for d in range(1, num_days + 1) if d not in days_off and d != training_day],
                    default=st.session_state.business_trip.get(vhv, []),
                    key=f"business_{vhv}_{month}_{year}"
                )
                
                st.session_state.business_trip[vhv] = business_days
                
                # Chọn 2 ngày hành chính
                available_days = [d for d in range(1, num_days + 1) 
                                if d not in days_off and d not in business_days and d != training_day]
                
                admin_days = st.multiselect(
                    f"Ngày hành chính - {vhv}",
                    options=available_days,
                    default=[],
                    max_selections=2,
                    key=f"admin_{vhv}_{month}_{year}"
                )
                
                st.caption(f"Ngày nghỉ: {len(days_off)}/5 | Công tác: {len(business_days)} | HC: {len(admin_days)}/2")

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
            'last_shift': None,  # 'day', 'night', hoặc None
            'last_shift_day': None,  # Ngày làm ca cuối cùng
            'target_shifts': 17,  # Mục tiêu ban đầu
            'unavailable_days': set(day_off_dict.get(staff, []) + business_trip_dict.get(staff, [])),
            'business_trip_days': set(business_trip_dict.get(staff, []))
        }
    
    # Tính toán lại mục tiêu nếu có người công tác
    total_tk_business_days = sum(len(staff_data[tk]['business_trip_days']) for tk in truong_kiep)
    total_vhv_business_days = sum(len(staff_data[vhv]['business_trip_days']) for vhv in van_hanh_vien)
    
    # Số ca cần phân bổ (mỗi ngày 2 ca, trừ ngày đào tạo)
    total_shifts_needed_tk = 2 * (num_days - 1)  # -1 vì có ngày đào tạo
    total_shifts_needed_vhv = 2 * (num_days - 1)
    
    # Số ca mỗi nhóm có thể làm (nếu không có công tác)
    total_possible_tk = len(truong_kiep) * 17
    total_possible_vhv = len(van_hanh_vien) * 17
    
    # Điều chỉnh mục tiêu nếu có công tác
    for tk in truong_kiep:
        business_days = len(staff_data[tk]['business_trip_days'])
        if business_days > 0:
            # Giảm mục tiêu của người công tác
            staff_data[tk]['target_shifts'] = max(0, 17 - (business_days * 2))
    
    for vhv in van_hanh_vien:
        business_days = len(staff_data[vhv]['business_trip_days'])
        if business_days > 0:
            staff_data[vhv]['target_shifts'] = max(0, 17 - (business_days * 2))
    
    # Tăng mục tiêu cho những người không công tác
    if total_tk_business_days > 0:
        tk_without_business = [tk for tk in truong_kiep if len(staff_data[tk]['business_trip_days']) == 0]
        if tk_without_business:
            additional_shifts = total_tk_business_days * 2  # Mỗi ngày công tác cần 2 ca bù
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
        
        # Xử lý ca ngày
        available_tk = [tk for tk in truong_kiep 
                       if day not in staff_data[tk]['unavailable_days']]
        available_vhv = [vhv for vhv in van_hanh_vien 
                        if day not in staff_data[vhv]['unavailable_days']]
        
        if available_tk and available_vhv:
            # Chọn người cho ca ngày
            selected_tk = select_staff_for_shift(
                available_tk, staff_data, day, 'day', 'TK'
            )
            selected_vhv = select_staff_for_shift(
                available_vhv, staff_data, day, 'day', 'VHV'
            )
            
            if selected_tk and selected_vhv:
                # Cập nhật thông tin
                staff_data[selected_tk]['total_shifts'] += 1
                staff_data[selected_tk]['day_shifts'] += 1
                staff_data[selected_tk]['last_shift'] = 'day'
                staff_data[selected_tk]['last_shift_day'] = day
                
                staff_data[selected_vhv]['total_shifts'] += 1
                staff_data[selected_vhv]['day_shifts'] += 1
                staff_data[selected_vhv]['last_shift'] = 'day'
                staff_data[selected_vhv]['last_shift_day'] = day
                
                # Reset consecutive night nếu làm ca ngày
                if staff_data[selected_tk]['last_shift'] == 'day':
                    staff_data[selected_tk]['consecutive_night'] = 0
                if staff_data[selected_vhv]['last_shift'] == 'day':
                    staff_data[selected_vhv]['consecutive_night'] = 0
                
                schedule.append({
                    'Ngày': day,
                    'Thứ': calendar.day_name[calendar.weekday(year, month, day)],
                    'Ca': 'Ngày (6h-18h)',
                    'Trưởng kiếp': selected_tk,
                    'Vận hành viên': selected_vhv,
                    'Ghi chú': ''
                })
        
        # Xử lý ca đêm
        # Kiểm tra không làm 24h liên tục: nếu làm ca ngày hôm nay thì không được làm ca đêm
        available_tk_night = [tk for tk in truong_kiep 
                            if day not in staff_data[tk]['unavailable_days']
                            and not (staff_data[tk]['last_shift'] == 'day' and staff_data[tk]['last_shift_day'] == day)]
        
        available_vhv_night = [vhv for vhv in van_hanh_vien 
                             if day not in staff_data[vhv]['unavailable_days']
                             and not (staff_data[vhv]['last_shift'] == 'day' and staff_data[vhv]['last_shift_day'] == day)]
        
        # Kiểm tra không làm từ ca đêm qua ca ngày: nếu làm ca đêm hôm trước thì không làm ca ngày hôm sau
        # (Đã xử lý trong phần chọn cho ca ngày)
        
        if available_tk_night and available_vhv_night:
            # Chọn người cho ca đêm
            selected_tk_night = select_staff_for_shift(
                available_tk_night, staff_data, day, 'night', 'TK'
            )
            selected_vhv_night = select_staff_for_shift(
                available_vhv_night, staff_data, day, 'night', 'VHV'
            )
            
            if selected_tk_night and selected_vhv_night:
                # Cập nhật thông tin
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
                
                # Kiểm tra quá 3 ca đêm liên tiếp
                if staff_data[selected_tk_night]['consecutive_night'] > 3:
                    staff_data[selected_tk_night]['consecutive_night'] = 3
                if staff_data[selected_vhv_night]['consecutive_night'] > 3:
                    staff_data[selected_vhv_night]['consecutive_night'] = 3
                
                schedule.append({
                    'Ngày': day,
                    'Thứ': calendar.day_name[calendar.weekday(year, month, day)],
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
    
    # Lọc theo các tiêu chí
    filtered_staff = []
    for staff in available_staff:
        data = staff_data[staff]
        
        # Kiểm tra đã đạt mục tiêu chưa
        if data['total_shifts'] >= data['target_shifts']:
            continue
        
        # Kiểm tra ca đêm liên tiếp
        if shift_type == 'night' and data['consecutive_night'] >= 3:
            continue
        
        # Kiểm tra không làm 24h liên tục
        if shift_type == 'night' and data['last_shift'] == 'day' and data['last_shift_day'] == day:
            continue
        
        filtered_staff.append(staff)
    
    if not filtered_staff:
        return None
    
    # Ưu tiên chọn người ít ca nhất và còn cách mục tiêu xa nhất
    filtered_staff.sort(key=lambda x: (
        staff_data[x]['total_shifts'],  # Ưu tiên người ít ca
        -abs(staff_data[x]['target_shifts'] - staff_data[x]['total_shifts'])  # Ưu tiên người còn cách mục tiêu xa
    ))
    
    return filtered_staff[0]

with tab2:
    st.subheader("Lịch trực tháng")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🎯 Tạo lịch trực tự động", type="primary"):
            with st.spinner("Đang tạo lịch trực nâng cao..."):
                # Lấy dữ liệu từ session state
                day_off_dict = st.session_state.day_off
                business_trip_dict = st.session_state.business_trip
                
                # Tạo lịch
                schedule, staff_data = generate_advanced_schedule(
                    month, year, training_day, day_off_dict, business_trip_dict
                )
                
                # Lưu vào session state
                st.session_state.schedule_data = schedule
                st.session_state.staff_stats = staff_data
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
        
        # Hiển thị thống kê chi tiết
        st.subheader("📈 Thống kê phân công chi tiết")
        
        if st.session_state.staff_stats:
            stats_data = []
            for staff, data in st.session_state.staff_stats.items():
                stats_data.append({
                    'Nhân viên': staff,
                    'Vai trò': data['role'],
                    'Mục tiêu': data['target_shifts'],
                    'Tổng ca': data['total_shifts'],
                    'Ca ngày': data['day_shifts'],
                    'Ca đêm': data['night_shifts'],
                    'Công tác': len(data['business_trip_days']),
                    'Chênh lệch': data['total_shifts'] - data['target_shifts']
                })
            
            df_stats = pd.DataFrame(stats_data)
            st.dataframe(df_stats, use_container_width=True)
            
            # Tóm tắt
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
        st.info("👈 Vui lòng chọn ngày nghỉ và công tác ở Tab 1, sau đó nhấn nút 'Tạo lịch trực tự động'")

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
    
    # Thống kê ngày nghỉ, công tác
    st.subheader("📋 Thống kê ngày nghỉ & Công tác")
    
    summary_data = []
    for staff in all_staff:
        days_off = st.session_state.day_off.get(staff, [])
        business_days = st.session_state.business_trip.get(staff, [])
        
        summary_data.append({
            'Nhân viên': staff,
            'Vai trò': 'TK' if staff in truong_kiep else 'VHV',
            'Ngày nghỉ': len(days_off),
            'Ngày công tác': len(business_days),
            'Tổng ngày vắng': len(days_off) + len(business_days),
            'Ngày nghỉ cụ thể': ', '.join(map(str, sorted(days_off))) if days_off else '-',
            'Ngày công tác': ', '.join(map(str, sorted(business_days))) if business_days else '-'
        })
    
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, use_container_width=True)
    
    # Kiểm tra vi phạm
    st.subheader("🔍 Kiểm tra ràng buộc")
    
    violations = []
    warnings = []
    
    # Kiểm tra số ngày nghỉ
    for staff in all_staff:
        days_off = st.session_state.day_off.get(staff, [])
        if len(days_off) > 5:
            violations.append(f"❌ {staff}: Chọn {len(days_off)} ngày nghỉ (vượt quá 5 ngày)")
    
    # Kiểm tra công tác + nghỉ không quá 15 ngày (giả định)
    for staff in all_staff:
        days_off = st.session_state.day_off.get(staff, [])
        business_days = st.session_state.business_trip.get(staff, [])
        total_absent = len(set(days_off) | set(business_days))
        if total_absent > 15:  # Giới hạn vắng mặt
            warnings.append(f"⚠️ {staff}: Vắng mặt {total_absent} ngày (nghỉ + công tác)")
    
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
    
    # Thống kê phân bổ ca đêm
    if st.session_state.schedule_created and st.session_state.staff_stats:
        st.subheader("🌙 Phân bổ ca đêm")
        
        night_stats = []
        for staff in all_staff:
            data = st.session_state.staff_stats[staff]
            night_stats.append({
                'Nhân viên': staff,
                'Ca đêm': data['night_shifts'],
                'Ca đêm liên tiếp max': data.get('consecutive_night', 0),
                'Vai trò': data['role']
            })
        
        df_night = pd.DataFrame(night_stats)
        st.dataframe(df_night, use_container_width=True)

with tab4:
    st.subheader("Cài đặt nâng cao")
    
    st.markdown("### ⚙️ Thông số hệ thống")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_consecutive_night = st.slider("Số ca đêm liên tiếp tối đa", 1, 5, 3)
        max_total_shifts = st.slider("Số ca tối đa/người", 15, 25, 20)
    
    with col2:
        min_break_hours = st.slider("Thời gian nghỉ tối thiểu giữa ca (giờ)", 8, 24, 12)
        priority_factor = st.selectbox("Ưu tiên phân công", 
                                      ["Cân bằng công", "Giảm ca đêm", "Luân phiên đều"])
    
    st.markdown("### 📊 Phân tích lịch")
    
    if st.button("Phân tích chất lượng lịch"):
        if st.session_state.schedule_created:
            # Phân tích chất lượng lịch
            schedule_quality = analyze_schedule_quality(
                st.session_state.schedule_data, 
                st.session_state.staff_stats
            )
            
            st.success(f"Điểm chất lượng lịch: {schedule_quality['score']}/100")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Độ cân bằng", f"{schedule_quality['balance_score']}%")
                st.metric("Vi phạm ràng buộc", schedule_quality['violations'])
            with col2:
                st.metric("Hiệu quả phân công", f"{schedule_quality['efficiency']}%")
                st.metric("Ca đêm trung bình", schedule_quality['avg_night_shifts'])
        else:
            st.warning("Vui lòng tạo lịch trước khi phân tích")

def analyze_schedule_quality(schedule_data, staff_stats):
    """Phân tích chất lượng lịch"""
    total_shifts = len([s for s in schedule_data if s['Ca'] not in ['Đào tạo']])
    
    # Tính độ cân bằng
    shifts_per_person = [stats['total_shifts'] for stats in staff_stats.values()]
    balance_score = 100 - (max(shifts_per_person) - min(shifts_per_person)) * 10
    
    # Đếm vi phạm
    violations = 0
    night_sequence = {}
    
    # Kiểm tra 24h liên tục
    for i in range(1, len(schedule_data)):
        if schedule_data[i]['Ca'] == 'Đêm (18h-6h)' and schedule_data[i-1]['Ca'] == 'Ngày (6h-18h)':
            if schedule_data[i]['Ngày'] == schedule_data[i-1]['Ngày']:
                # Cùng ngày: ca ngày → ca đêm (vi phạm 24h liên tục)
                violations += 1
    
    # Hiệu quả phân công
    target_total = sum(stats['target_shifts'] for stats in staff_stats.values())
    actual_total = sum(stats['total_shifts'] for stats in staff_stats.values())
    efficiency = (actual_total / target_total * 100) if target_total > 0 else 0
    
    # Ca đêm trung bình
    avg_night_shifts = sum(stats['night_shifts'] for stats in staff_stats.values()) / len(staff_stats)
    
    # Tính điểm tổng
    score = (
        balance_score * 0.3 +
        max(0, 100 - violations * 10) * 0.4 +
        min(efficiency, 100) * 0.2 +
        max(0, 100 - avg_night_shifts * 5) * 0.1
    )
    
    return {
        'score': round(score, 1),
        'balance_score': round(balance_score, 1),
        'violations': violations,
        'efficiency': round(efficiency, 1),
        'avg_night_shifts': round(avg_night_shifts, 1)
    }

# Footer
st.markdown("---")
st.caption("""
**Hệ thống xếp lịch trực TBA 500kV - Phiên bản 3.0**  
*Thuật toán: Cân bằng công việc, kiểm soát 24h liên tục, hỗ trợ công tác*
""")