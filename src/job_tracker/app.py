from datetime import date, timedelta

import pandas as pd
import streamlit as st

from job_tracker.database import (
    add_application,
    connect,
    delete_application,
    get_applications,
    initialize_database,
)
from job_tracker.models import Application
from job_tracker.stats import (
    calculate_success_rate,
    calculate_total,
    count_by_status,
)

STATUSES = ["検討中", "応募済み", "書類選考", "面接", "通過", "内定", "不合格"]

STATUS_COLORS = {
    "検討中":   {"bg": "#eef1f4", "text": "#5b6773"},
    "応募済み": {"bg": "#e5f0ff", "text": "#1d5fd6"},
    "書類選考": {"bg": "#f1ecff", "text": "#6d3fd1"},
    "面接":     {"bg": "#fff2df", "text": "#c4741a"},
    "通過":     {"bg": "#e1faf6", "text": "#0f9c88"},
    "内定":     {"bg": "#e3f9e9", "text": "#1a8f4c"},
    "不合格":   {"bg": "#fdecec", "text": "#c53c33"},
}


def apply_custom_style():
    st.markdown(
        """
        <style>
        .stApp { background: #ffffff; }
        .block-container { max-width: 1180px; padding-top: 2rem; padding-bottom: 3rem; }
        [data-testid="stSidebar"] { background: #f7fbff; border-right: 1px solid #dbeafe; }
        div[data-testid="stDataFrame"] { border: 1px solid #dbeafe; border-radius: 12px; overflow: hidden; }
        div[data-testid="stAlert"] { border-radius: 10px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <style>
        .hero-banner {
            background: linear-gradient(120deg, #2554d9 0%, #2878e8 55%, #249fc5 100%);
            padding: 28px 32px;
            border-radius: 20px;
            box-shadow: 0 16px 34px rgba(37, 84, 217, .18);
            margin-bottom: 1.5rem;
        }
        .hero-label {
            color: #d8efff;
            font-weight: 700;
            font-size: .78rem;
            letter-spacing: .12em;
            margin-bottom: .45rem;
        }
        .hero-title {
            color: #fff;
            font-size: 2rem;
            font-weight: 750;
            line-height: 1.25;
            margin-bottom: .55rem;
        }
        .hero-subtitle { color: #edf7ff; font-size: .96rem; margin: 0; }

        [data-testid="stMetric"] {
            background: #fff;
            border: 1px solid #dbeafe;
            border-radius: 15px;
            padding: 16px 18px;
            box-shadow: 0 8px 20px rgba(30, 90, 160, .07);
        }
        [data-testid="stMetricLabel"] { color: #55789a; font-weight: 600; }
        [data-testid="stMetricValue"] { color: #173d7a; font-weight: 750; }

        .deadline-box {
            background: linear-gradient(90deg, #eef7ff 0%, #f8fcff 100%);
            border: 1px solid #cfe7fa;
            border-left: 5px solid #288ee8;
            border-radius: 11px;
            padding: 12px 16px;
            margin-bottom: 9px;
            color: #173b63;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <style>
        .stButton, .stDownloadButton { width: 100%; }
        .stButton > button, .stDownloadButton > button {
            min-height: 2.8rem;
            padding: .65rem 1.1rem;
            background: linear-gradient(135deg, #2356d8 0%, #2878e8 55%, #25a9d6 100%);
            color: #fff;
            border: none;
            border-radius: 10px;
            font-weight: 700;
            font-size: .95rem;
            white-space: nowrap;
            box-shadow: 0 5px 14px rgba(35, 86, 216, .22);
            transition: transform .18s, filter .18s;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            transform: translateY(-1px);
            filter: brightness(1.05);
        }
        .stButton > button:disabled, .stDownloadButton > button:disabled {
            background: #dce9f8;
            color: #7795b4;
            cursor: not-allowed;
        }

        .stTabs [data-baseweb="tab-list"] { gap: 1.4rem; border-bottom: 1px solid #dbeafe; }
        .stTabs [data-baseweb="tab"] { color: #6d8eaa; font-weight: 650; }
        .stTabs [aria-selected="true"] { color: #2356d8; }
        .stTabs [data-baseweb="tab-highlight"] { background-color: #2878e8; height: 3px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_upcoming_deadlines(applications, days=7):
    # deadline未設定はスキップ
    today = date.today()
    limit = today + timedelta(days=days)
    result = []
    for item in applications:
        raw = item.get("deadline")
        if not raw:
            continue
        d = date.fromisoformat(raw)
        if not (today <= d <= limit):
            continue
        result.append({
            "company": item["company"],
            "position": item["position"],
            "deadline": d,
            "days_left": (d - today).days,
        })
    return result


def style_status_column(df):
    def _badge(value):
        colors = STATUS_COLORS.get(value, {"bg": "#f2f2f2", "text": "#555"})
        return (
            f"background-color: {colors['bg']}; "
            f"color: {colors['text']}; "
            "font-weight: 700; border-radius: 6px;"
        )
    styled = df.style.map(_badge, subset=["ステータス"])
    styled = styled.set_properties(subset=["ID", "企業名"], **{"text-align": "center"})
    return styled


def main():
    st.set_page_config(page_title="就活管理ツール", page_icon="📋", layout="wide")
    apply_custom_style()

    conn = connect()
    initialize_database(conn)

    st.sidebar.header("新しい応募を追加")

    with st.sidebar.form("add_form", clear_on_submit=True):
        company = st.text_input("企業名", placeholder="例：株式会社〇〇")
        position = st.text_input("職種・コース", placeholder="例：データアナリスト")
        status = st.selectbox("選考状況", STATUSES)
        applied_date = st.date_input("応募日", value=date.today())

        use_deadline = st.checkbox("締切日を設定する")
        deadline = None
        if use_deadline:
            deadline = st.date_input("締切日", value=date.today() + timedelta(days=7))

        notes = st.text_area("メモ", placeholder="説明会、面接、提出物など")
        submitted = st.form_submit_button("追加する", type="primary", use_container_width=True)

    if submitted:
        if not company.strip() or not position.strip():
            st.sidebar.error("企業名と職種を入力してください。")
        else:
            application = Application(
                company=company.strip(),
                position=position.strip(),
                status=status,
                applied_date=applied_date,
                deadline=deadline,
                notes=notes.strip(),
            )
            add_application(conn, application)
            st.sidebar.success("追加しました。")
            st.rerun()

    st.markdown(
        """
        <div class="hero-banner">
            <div class="hero-label">CAREER DASHBOARD</div>
            <div class="hero-title">選考状況をひと目で管理</div>
            <p class="hero-subtitle">
                応募企業、選考ステータス、締切をまとめて確認できます。
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    applications = get_applications(conn)

    if not applications:
        st.info("まだ応募データがありません。左側のフォームから追加してください。")

    total = calculate_total(applications)
    success_rate = calculate_success_rate(applications)
    status_counts = count_by_status(applications)
    upcoming = get_upcoming_deadlines(applications)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("応募件数", total)
    m2.metric("通過・内定率", f"{success_rate:.0%}")
    m3.metric("面接中", status_counts.get("面接", 0))
    m4.metric("7日以内の締切", len(upcoming))

    st.divider()

    if upcoming:
        st.subheader("直近の締切")
        for item in sorted(upcoming, key=lambda v: v["deadline"]):
            days_text = "本日締切" if item["days_left"] == 0 else f"あと{item['days_left']}日"
            st.markdown(
                f"""
                <div class="deadline-box">
                    <b>{item["company"]}</b> / {item["position"]}<br>
                    締切：{item["deadline"].strftime("%Y/%m/%d")}（{days_text}）
                </div>
                """,
                unsafe_allow_html=True,
            )

    tab_list, tab_stats = st.tabs(["応募一覧", "統計・分析"])

    with tab_list:
        st.subheader("一覧・編集")

        filter_col, search_col = st.columns([1, 2])
        selected_statuses = filter_col.multiselect("ステータス絞り込み", STATUSES)
        keyword = search_col.text_input("キーワード検索", placeholder="企業名や職種で検索")

        filtered = applications
        if selected_statuses:
            filtered = [item for item in filtered if item["status"] in selected_statuses]

        if keyword:
            word = keyword.lower()
            matched = []
            for item in filtered:
                if word in item["company"].lower() or word in item["position"].lower():
                    matched.append(item)
            filtered = matched

        if not applications:
            st.info("応募データを追加すると、ここに一覧が表示されます。")
        elif not filtered:
            st.warning("条件に合うデータが見つかりません。")
        else:
            df = pd.DataFrame(filtered)[
                ["id", "company", "position", "status", "applied_date", "deadline", "notes"]
            ]
            df.columns = ["ID", "企業名", "職種", "ステータス", "応募日", "締切日", "メモ"]

            st.dataframe(style_status_column(df), use_container_width=True, hide_index=True)

            csv_data = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "CSV形式でダウンロード",
                data=csv_data,
                file_name="jobs.csv",
                mime="text/csv",
                use_container_width=True,
            )

            st.divider()
            st.subheader("データの削除")

            delete_options = {
                f"{item['company']} ({item['position']}) - ID:{item['id']}": item["id"]
                for item in applications
            }
            selected_item = st.selectbox("削除する項目を選択", options=list(delete_options.keys()))
            confirmed = st.checkbox("削除する内容を確認しました")

            delete_clicked = st.button(
                "選択した項目を削除",
                type="secondary",
                disabled=not confirmed,
                use_container_width=True,
            )

            if delete_clicked:
                delete_application(conn, delete_options[selected_item])
                st.success("削除しました。")
                st.rerun()

    with tab_stats:
        st.subheader("応募データの集計")

        if not applications:
            st.info("応募データを追加すると、集計グラフが表示されます。")
        else:
            all_data = pd.DataFrame(applications)
            all_data["applied_date"] = pd.to_datetime(all_data["applied_date"])
            all_data["応募月"] = all_data["applied_date"].dt.strftime("%Y-%m")

            status_data = all_data["status"].value_counts().reset_index()
            status_data.columns = ["選考状況", "件数"]

            monthly_data = all_data.groupby("応募月").size().reset_index(name="件数")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 選考状況別の応募件数")
                st.bar_chart(
                    status_data.set_index("選考状況"),
                    use_container_width=True,
                )

            with col2:
                st.markdown("#### 月別応募件数")
                st.line_chart(
                    monthly_data.set_index("応募月"),
                    use_container_width=True,
                )

            st.markdown("#### 選考状況サマリー")
            st.dataframe(
                status_data,
                use_container_width=True,
                hide_index=True,
            )

    conn.close()


if __name__ == "__main__":
    main()
