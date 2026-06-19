import streamlit as st

def render_track_changes_view(errors):
    if not errors:
        st.success("Không phát hiện lỗi nào hoặc toàn bộ lỗi đã được xử lý!")
        return []

    st.subheader("📋 Danh sách Track Changes")
    updated_errors = []
    
    col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns([1, 2, 4, 4, 3])
    col_h1.write("**STT**")
    col_h2.write("**Loại lỗi**")
    col_h3.write("**Nội dung gốc**")
    col_h4.write("**Đề xuất**")
    col_h5.write("**Thao tác**")

    for idx, err in enumerate(errors):
        col1, col2, col3, col4, col5 = st.columns([1, 2, 4, 4, 3])
        col1.write(f"{idx+1}")
        col2.write(f"**{err['loai']}**")
        col3.markdown(f"<span style='color:red; text-decoration:line-through;'>{err['goc']}</span>", unsafe_allow_html=True)
        col4.markdown(f"<span style='color:green; font-weight:bold;'>{err['de_xuat']}</span>", unsafe_allow_html=True)
        
        # Nút bấm xử lý từng lỗi
        action = col5.radio(f"Thao tác {idx+1}", ["Chờ duyệt", "Chấp nhận", "Bỏ qua"], label_visibility="collapsed", key=f"action_{idx}_{err['goc']}")
        
        if action == "Chờ duyệt" or action == "Chấp nhận":
            err['status'] = action
            updated_errors.append(err)
            
    return updated_errors