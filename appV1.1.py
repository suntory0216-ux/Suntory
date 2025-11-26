import streamlit as st
import pandas as pd
import os

# --- 設定檔案名稱 ---
FILE_NAME = 'inventory.csv'

# --- 1. 讀取與儲存資料的函數 ---
def load_data():
    """
    讀取庫存資料，如果檔案不存在則建立一個新的。
    新增了 '商品編號' 和 '操作人員' 欄位。
    """
    # 定義所有需要的欄位
    required_cols = ["商品編號", "商品名稱", "目前數量", "存放位置", "最後更新時間", "操作人員"]
    
    if not os.path.exists(FILE_NAME):
        # 建立預設的空資料表
        df = pd.DataFrame(columns=required_cols)
        df.to_csv(FILE_NAME, index=False)
        return df
    else:
        df = pd.read_csv(FILE_NAME)
        # 檢查舊檔案是否缺少新欄位，若缺少則補上
        for col in required_cols:
            if col not in df.columns:
                df[col] = '' 
        # 確保欄位順序正確
        return df[required_cols]

def save_data(df):
    """將資料儲存回 CSV 檔案"""
    df.to_csv(FILE_NAME, index=False)

# --- 2. 應用程式介面設定 ---
st.set_page_config(page_title="公司庫存管理系統 (v2)", page_icon="📦")
st.title("📦 公司行動庫存管理 (v2)")

# 載入目前的庫存
df = load_data()

# 建立分頁 (Tabs) 
tab1, tab2, tab3 = st.tabs(["📊 檢視庫存", "➕ 入庫/新增", "➖ 出庫/領料"])

# --- 分頁 1: 檢視庫存 ---
with tab1:
    st.header("目前庫存清單")
    
    # 加入搜尋功能
    search_term = st.text_input("搜尋商品名稱或編號：")
    
    if search_term:
        # 篩選資料 (同時搜尋名稱和編號)
        mask = df["商品名稱"].str.contains(search_term, case=False) | df["商品編號"].str.contains(search_term, case=False)
        display_df = df[mask]
    else:
        display_df = df
        
    # 只顯示與庫存相關的核心欄位
    st.dataframe(display_df[["商品編號", "商品名稱", "目前數量", "存放位置", "最後更新時間", "操作人員"]], use_container_width=True) 
    
    st.caption(f"總共有 {len(df)} 項商品")

# --- 分頁 2: 入庫 (新增商品或增加數量) ---
with tab2:
    st.header("入庫作業")
    
    # 📌 優化 2: 登記入庫人員
    staff_in = st.text_input("**1. 入庫人員姓名**", key="staff_in_input")

    st.subheader("2. 選擇操作類型")
    action_type = st.radio("選擇類型", ["原有商品補貨", "新增全新商品"], key="in_action_type")
    
    if action_type == "原有商品補貨":
        if not df.empty:
            # 讓使用者選擇商品，顯示商品編號和名稱
            item_options = df.apply(lambda row: f"{row['商品編號']} - {row['商品名稱']}", axis=1).unique()
            selected_item_info = st.selectbox("3. 選擇商品", item_options)
            
            # 從選單中提取商品編號
            selected_id = selected_item_info.split(' - ')[0]
            
            qty_to_add = st.number_input("4. 增加數量", min_value=1, value=1)
            
            if st.button("確認補貨", key="btn_confirm_add"):
                if not staff_in:
                    st.error("請輸入入庫人員姓名！")
                else:
                    # 找到對應的商品 ID
                    idx = df[df["商品編號"] == selected_id].index[0]
                    df.at[idx, "目前數量"] += qty_to_add
                    df.at[idx, "最後更新時間"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                    df.at[idx, "操作人員"] = staff_in # 記錄操作人員
                    
                    save_data(df)
                    st.success(f"✅ 成功！編號 {selected_id} - {df.at[idx, '商品名稱']} 數量已增加 {qty_to_add}。")
                    # 📌 優化 3: 完成後回首頁 (實質是刷新頁面，提示使用者切換)
                    st.info("畫面已刷新，請切換至「檢視庫存」分頁確認最新資料。")
                    st.rerun() 
        else:
            st.warning("目前沒有商品，請先新增全新商品。")
            
    else: # 新增全新商品
        st.subheader("3. 新增商品資訊")
        # 📌 優化 1: 新增商品編號
        new_id = st.text_input("**商品編號** (必須是唯一值)", key="new_id_input")
        new_name = st.text_input("商品名稱")
        new_qty = st.number_input("初始數量", min_value=0, value=0)
        new_loc = st.text_input("存放位置 (選填)")
        
        if st.button("建立新商品", key="btn_create_new"):
            if not staff_in:
                st.error("請輸入入庫人員姓名！")
            elif not new_id:
                st.error("請輸入商品編號！")
            elif new_id in df["商品編號"].values:
                st.error(f"商品編號 {new_id} 已存在！請使用「原有商品補貨」。")
            elif new_name:
                new_row = pd.DataFrame({
                    "商品編號": [new_id],
                    "商品名稱": [new_name],
                    "目前數量": [new_qty],
                    "存放位置": [new_loc],
                    "最後更新時間": [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")],
                    "操作人員": [staff_in]
                })
                df = pd.concat([df, new_row], ignore_index=True)
                save_data(df)
                st.success(f"✅ 已新增商品：編號 {new_id} - {new_name}")
                st.info("畫面已刷新，請切換至「檢視庫存」分頁確認最新資料。")
                st.rerun()
            else:
                st.error("請輸入商品名稱")

# --- 分頁 3: 出庫 (減少數量) ---
with tab3:
    st.header("出庫/領料作業")
    
    # 📌 優化 2: 登記入庫人員
    staff_out = st.text_input("**1. 出庫人員姓名**", key="staff_out_input")

    if not df.empty:
        # 讓使用者選擇商品，顯示商品編號和名稱
        item_options_out = df.apply(lambda row: f"{row['商品編號']} - {row['商品名稱']}", axis=1).unique()
        selected_item_info_out = st.selectbox("2. 選擇領取商品", item_options_out, key="remove_select")
        
        # 從選單中提取商品編號
        selected_id_out = selected_item_info_out.split(' - ')[0]
        
        # 取得目前該商品的庫存量
        current_qty_out = df[df["商品編號"] == selected_id_out]["目前數量"].values[0]
        st.info(f"目前庫存: {current_qty_out}")
        
        qty_to_remove = st.number_input("3. 領取數量", min_value=1, max_value=int(current_qty_out), value=1)
        
        if st.button("確認領取", key="btn_confirm_remove"):
            if not staff_out:
                st.error("請輸入出庫人員姓名！")
            else:
                idx = df[df["商品編號"] == selected_id_out].index[0]
                df.at[idx, "目前數量"] -= qty_to_remove
                df.at[idx, "最後更新時間"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                df.at[idx, "操作人員"] = staff_out # 記錄操作人員
                
                save_data(df)
                st.success(f"✅ 成功！已領取 {qty_to_remove} 個 編號 {selected_id_out} - {df.at[idx, '商品名稱']}。")
                # 📌 優化 3: 完成後回首頁 (實質是刷新頁面，提示使用者切換)
                st.info("畫面已刷新，請切換至「檢視庫存」分頁確認最新資料。")
                st.rerun()
    else:
        st.write("目前無庫存可領取。")