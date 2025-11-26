import streamlit as st
import pandas as pd
import os

# --- 設定檔案名稱 ---
FILE_NAME = 'inventory.csv'

# --- 1. 讀取與儲存資料的函數 ---
def load_data():
    """讀取庫存資料，如果檔案不存在則建立一個新的"""
    if not os.path.exists(FILE_NAME):
        # 建立預設的空資料表
        df = pd.DataFrame(columns=["商品名稱", "目前數量", "存放位置", "最後更新時間"])
        df.to_csv(FILE_NAME, index=False)
        return df
    else:
        return pd.read_csv(FILE_NAME)

def save_data(df):
    """將資料儲存回 CSV 檔案"""
    df.to_csv(FILE_NAME, index=False)

# --- 2. 應用程式介面設定 ---
st.set_page_config(page_title="公司庫存管理系統", page_icon="📦")
st.title("📦 公司行動庫存管理")

# 載入目前的庫存
df = load_data()

# 建立分頁 (Tabs) 方便手機切換
tab1, tab2, tab3 = st.tabs(["📊 檢視庫存", "➕ 入庫/新增", "➖ 出庫/領料"])

# --- 分頁 1: 檢視庫存 ---
with tab1:
    st.header("目前庫存清單")
    # 加入搜尋功能
    search_term = st.text_input("搜尋商品名稱：")
    
    if search_term:
        # 篩選資料
        display_df = df[df["商品名稱"].str.contains(search_term, case=False)]
    else:
        display_df = df
        
    st.dataframe(display_df, use_container_width=True) # 適配手機寬度
    
    # 顯示總品項數
    st.caption(f"總共有 {len(df)} 項商品")

# --- 分頁 2: 入庫 (新增商品或增加數量) ---
with tab2:
    st.header("入庫作業")
    
    # 選擇操作模式
    action_type = st.radio("選擇類型", ["原有商品補貨", "新增全新商品"])
    
    if action_type == "原有商品補貨":
        if not df.empty:
            item_to_add = st.selectbox("選擇商品", df["商品名稱"].unique())
            qty_to_add = st.number_input("增加數量", min_value=1, value=1)
            
            if st.button("確認補貨"):
                # 找到對應的商品並增加數量
                idx = df[df["商品名稱"] == item_to_add].index[0]
                df.at[idx, "目前數量"] += qty_to_add
                df.at[idx, "最後更新時間"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                save_data(df)
                st.success(f"成功！{item_to_add} 數量已增加 {qty_to_add}。")
                st.rerun() # 重新整理頁面
        else:
            st.warning("目前沒有商品，請先新增全新商品。")
            
    else: # 新增全新商品
        new_name = st.text_input("輸入新商品名稱")
        new_qty = st.number_input("初始數量", min_value=0, value=0)
        new_loc = st.text_input("存放位置 (選填)")
        
        if st.button("建立新商品"):
            if new_name in df["商品名稱"].values:
                st.error("商品已存在！請使用「原有商品補貨」。")
            elif new_name:
                new_row = pd.DataFrame({
                    "商品名稱": [new_name],
                    "目前數量": [new_qty],
                    "存放位置": [new_loc],
                    "最後更新時間": [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")]
                })
                df = pd.concat([df, new_row], ignore_index=True)
                save_data(df)
                st.success(f"已新增商品：{new_name}")
                st.rerun()
            else:
                st.error("請輸入商品名稱")

# --- 分頁 3: 出庫 (減少數量) ---
with tab3:
    st.header("出庫/領料作業")
    
    if not df.empty:
        item_to_remove = st.selectbox("選擇領取商品", df["商品名稱"].unique(), key="remove_select")
        # 取得目前該商品的庫存量
        current_qty = df[df["商品名稱"] == item_to_remove]["目前數量"].values[0]
        st.info(f"目前庫存: {current_qty}")
        
        qty_to_remove = st.number_input("領取數量", min_value=1, max_value=int(current_qty), value=1)
        
        if st.button("確認領取"):
            idx = df[df["商品名稱"] == item_to_remove].index[0]
            df.at[idx, "目前數量"] -= qty_to_remove
            df.at[idx, "最後更新時間"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
            save_data(df)
            st.success(f"成功！已領取 {qty_to_remove} 個 {item_to_remove}。")
            st.rerun()
    else:
        st.write("目前無庫存可領取。")