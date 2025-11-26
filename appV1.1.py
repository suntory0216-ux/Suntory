import streamlit as st
import pandas as pd
import os

# --- 設定檔案名稱 ---
FILE_NAME = 'inventory.csv'
# 📌 新增日誌檔案名稱
LOG_FILE_NAME = 'log.csv'

# --- 1. 讀取與儲存資料的函數 (庫存) ---
def load_data():
    """讀取庫存資料，如果檔案不存在則建立一個新的。"""
    required_cols = ["商品編號", "商品名稱", "目前數量", "存放位置", "最後更新時間", "操作人員"]
    
    if not os.path.exists(FILE_NAME):
        df = pd.DataFrame(columns=required_cols)
        df.to_csv(FILE_NAME, index=False)
        return df
    else:
        df = pd.read_csv(FILE_NAME)
        for col in required_cols:
            if col not in df.columns:
                df[col] = '' 
        return df[required_cols]

def save_data(df):
    """將資料儲存回 CSV 檔案"""
    df.to_csv(FILE_NAME, index=False)

# --- 2. 讀取與儲存資料的函數 (日誌) ---
def load_log_data():
    """讀取操作日誌資料，如果檔案不存在則建立一個新的。"""
    log_cols = ["時間", "商品編號", "商品名稱", "操作類型", "數量變動", "操作人員"]
    if not os.path.exists(LOG_FILE_NAME):
        df_log = pd.DataFrame(columns=log_cols)
        df_log.to_csv(LOG_FILE_NAME, index=False)
        return df_log
    # 讀取時確保所有欄位都是字串類型，避免 CSV 讀取錯誤
    return pd.read_csv(LOG_FILE_NAME, dtype=str)

def write_log(item_id, item_name, operation, change_qty, staff):
    """將一筆新的操作紀錄寫入 log.csv"""
    # 數量變動欄位，入庫為正數，出庫為負數
    new_log = pd.DataFrame({
        "時間": [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")],
        "商品編號": [item_id],
        "商品名稱": [item_name],
        "操作類型": [operation],
        "數量變動": [str(change_qty)], # 確保寫入 log 時為字串
        "操作人員": [staff]
    })
    # 使用 mode='a' (append) 附加到檔案末尾，header=False 避免重複寫入標題
    new_log.to_csv(LOG_FILE_NAME, mode='a', header=False, index=False) 

# --- 3. 應用程式介面設定 ---
st.set_page_config(page_title="公司庫存管理系統 (v3)", page_icon="📦")
st.title("📦 公司行動庫存管理 (v3)")

# 載入目前的庫存
df = load_data()

# 📌 新增分頁
tab1, tab2, tab3, tab4 = st.tabs(["📊 檢視庫存", "➕ 入庫/新增", "➖ 出庫/領料", "📜 操作紀錄"])

# --- 分頁 1: 檢視庫存 (不變) ---
with tab1:
    st.header("目前庫存清單")
    
    search_term = st.text_input("搜尋商品名稱或編號：")
    
    if search_term:
        mask = df["商品名稱"].str.contains(search_term, case=False) | df["商品編號"].str.contains(search_term, case=False)
        display_df = df[mask]
    else:
        display_df = df
        
    st.dataframe(display_df[["商品編號", "商品名稱", "目前數量", "存放位置", "最後更新時間", "操作人員"]], use_container_width=True) 
    
    st.caption(f"總共有 {len(df)} 項商品")

# --- 分頁 2: 入庫 (新增 log 紀錄) ---
with tab2:
    st.header("入庫作業")
    
    staff_in = st.text_input("**1. 入庫人員姓名**", key="staff_in_input")

    st.subheader("2. 選擇操作類型")
    action_type = st.radio("選擇類型", ["原有商品補貨", "新增全新商品"], key="in_action_type")
    
    if action_type == "原有商品補貨":
        if not df.empty:
            item_options = df.apply(lambda row: f"{row['商品編號']} - {row['商品名稱']}", axis=1).unique()
            selected_item_info = st.selectbox("3. 選擇商品", item_options)
            
            selected_id = selected_item_info.split(' - ')[0]
            item_name_to_add = selected_item_info.split(' - ')[1] # 取得名稱
            
            qty_to_add = st.number_input("4. 增加數量", min_value=1, value=1)
            
            if st.button("確認補貨", key="btn_confirm_add"):
                if not staff_in:
                    st.error("請輸入入庫人員姓名！")
                else:
                    # 1. 更新庫存
                    idx = df[df["商品編號"] == selected_id].index[0]
                    df.at[idx, "目前數量"] += qty_to_add
                    df.at[idx, "最後更新時間"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                    df.at[idx, "操作人員"] = staff_in 
                    save_data(df)
                    
                    # 2. 📌 寫入操作紀錄
                    write_log(selected_id, item_name_to_add, "入庫補貨", qty_to_add, staff_in)
                    
                    st.success(f"✅ 成功！編號 {selected_id} - {item_name_to_add} 數量已增加 {qty_to_add}。")
                    st.info("畫面已刷新，請切換至「操作紀錄」分頁或「檢視庫存」確認最新資料。")
                    st.rerun() 
        else:
            st.warning("目前沒有商品，請先新增全新商品。")
            
    else: # 新增全新商品
        st.subheader("3. 新增商品資訊")
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
                # 1. 更新庫存
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
                
                # 2. 📌 寫入操作紀錄
                write_log(new_id, new_name, "入庫新增", new_qty, staff_in)
                
                st.success(f"✅ 已新增商品：編號 {new_id} - {new_name}")
                st.info("畫面已刷新，請切換至「操作紀錄」分頁或「檢視庫存」確認最新資料。")
                st.rerun()
            else:
                st.error("請輸入商品名稱")

# --- 分頁 3: 出庫 (新增 log 紀錄) ---
with tab3:
    st.header("出庫/領料作業")
    
    staff_out = st.text_input("**1. 出庫人員姓名**", key="staff_out_input")

    if not df.empty:
        item_options_out = df.apply(lambda row: f"{row['商品編號']} - {row['商品名稱']}", axis=1).unique()
        selected_item_info_out = st.selectbox("2. 選擇領取商品", item_options_out, key="remove_select")
        
        selected_id_out = selected_item_info_out.split(' - ')[0]
        item_name_to_remove = selected_item_info_out.split(' - ')[1] # 取得名稱

        current_qty_out = df[df["商品編號"] == selected_id_out]["目前數量"].values[0]
        st.info(f"目前庫存: {current_qty_out}")
        
        qty_to_remove = st.number_input("3. 領取數量", min_value=1, max_value=int(current_qty_out), value=1)
        
        if st.button("確認領取", key="btn_confirm_remove"):
            if not staff_out:
                st.error("請輸入出庫人員姓名！")
            else:
                # 1. 更新庫存
                idx = df[df["商品編號"] == selected_id_out].index[0]
                df.at[idx, "目前數量"] -= qty_to_remove
                df.at[idx, "最後更新時間"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                df.at[idx, "操作人員"] = staff_out 
                save_data(df)
                
                # 2. 📌 寫入操作紀錄 (數量變動為負數)
                write_log(selected_id_out, item_name_to_remove, "出庫領料", -qty_to_remove, staff_out)

                st.success(f"✅ 成功！已領取 {qty_to_remove} 個 編號 {selected_id_out} - {item_name_to_remove}。")
                st.info("畫面已刷新，請切換至「操作紀錄」分頁或「檢視庫存」確認最新資料。")
                st.rerun()
    else:
        st.write("目前無庫存可領取。")


# --- 📌 分頁 4: 操作紀錄 ---
with tab4:
    st.header("📜 操作歷史紀錄")
    df_log = load_log_data()

    if not df_log.empty:
        # 依照時間降序排列 (最新紀錄在前)
        df_log['時間'] = pd.to_datetime(df_log['時間'])
        df_log_sorted = df_log.sort_values(by="時間", ascending=False)
        
        # 顯示全部日誌
        st.dataframe(df_log_sorted, use_container_width=True)
        st.caption(f"總共有 {len(df_log)} 筆操作紀錄 (最新資料已在頂部)")
    else:
        st.info("目前尚無任何操作紀錄。請先進行入庫或出庫作業。")
