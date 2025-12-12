import streamlit as st
import pandas as pd

st.set_page_config(page_title="Xếp lịch trực TBA 500kV", layout="wide")
st.title("🔄 Xếp lịch trực TBA 500kV")
st.write("Ứng dụng đang được khởi tạo...")

# Kiểm tra phiên bản thư viện
st.write(f"Streamlit version: {st.__version__}")
st.write(f"Pandas version: {pd.__version__}")

# Test đơn giản
if st.button("Kiểm tra"):
    st.success("✅ Ứng dụng hoạt động bình thường!")
