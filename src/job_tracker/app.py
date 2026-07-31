from datetime import date, timedelta

import pandas as pd
import streamlit as st

from job_tracker.database import (
    add_application,
    connect,
    delete_application,
    get_applications,
    initialize_database,
    update_application,
)
from job_tracker.models import Application
from job_tracker.stats import (
    calculate_success_rate,
    calculate_total,
    count_by_status,
)

STATUSES = [
    "検討中",
    "ES",
    "適性検査",
    "面接",
    "内定",
    "不合格",
    "辞退",
]

STATUS_COLORS = {
    "検討中": {"bg": "#f1f3f5", "text": "#495057"},
    "ES": {"bg": "#e7f1ff", "text": "#1769aa"},
    "適性検査": {"bg": "#fff3cd", "text": "#946200"},
    "面接": {"bg": "#f3e8ff", "text": "#7b2cbf"},
    "内定": {"bg": "#dff7e8", "text": "#198754"},
    "不合格": {"bg": "#fde8e8", "text": "#c92a2a"},
    "辞退": {"bg": "#eceff1", "text": "#607d8b"},
}

CUSTOM_CSS = """
<style>
.stApp { background: #ffffff; }
.block-container { max-width: 1180px; padding-top: 2rem; padding-bottom: 3rem; }
[data-testid="stSidebar"] { background: #f7fbff; border-right: 1px solid #dbeafe; }
div[data-testid="stDataFrame"] { border: 1px solid #dbeafe; border-radius: 12px; overflow: hidden; }
div[data-testid="stAlert"] { border-radius: 10px; }

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

.stButton, .stDownloadButton { width: 100%; }
.stButton > button, .stDownloadButton > button {
    width: 100%;
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
"""

def get_upcoming_deadlines(applications, days=7):
    today = date.today()
    limit = today + timedelta(days=days)
    upcoming = []

    for item in applications:
        deadline_value = item.get("deadline")
        if not deadline_value:
            continue

        try:
            deadline = date.fromisoformat(deadline_value)
        except ValueError:
            continue

        if today <= deadline <= limit:
            upcoming.append(
                {
                    "company": item["company"],
                    "position": item["position"],
                    "deadline": deadline,
                    "days_left": (deadline - today).days,
                }
            )

    return upcoming


def render_sidebar_form(conn):
    st.sidebar.header("企業・選考情報を追加")

    with st.sidebar.form("add_form", clear_on_submit=True):
        company = st.text_input("企業名", placeholder="例：株式会社〇〇")
        position = st.text_input("職種・コース", placeholder="例：データアナリスト")
        status = st.selectbox("選考状況", STATUSES)
        applied_date = st.date_input("応募日", value=date.today())

        deadline = st.date_input(
            "締切日",
            value=date.today() + timedelta(days=7),
        )

        notes = st.text_area(
            "メモ",
            placeholder="次回予定、提出物、連絡事項など",
        )

        submitted = st.form_submit_button(
            "追加する",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    if not company.strip() or not position.strip():
        st.sidebar.error("企業名と職種を入力してください。")
        return

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


def main():
    st.set_page_config(
        page_title="就活管理ツール",
        page_icon="📋",
        layout="wide",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    conn = connect()
    initialize_database(conn)

    render_sidebar_form(conn)

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

    apps = get_applications(conn)

    if not apps:
        st.info("まだ応募データがありません。左側のフォームから追加してください。")

    upcoming = get_upcoming_deadlines(apps)

    applied_apps = [
        app for app in apps
        if app["status"] != "検討中"
    ]
    total = len(applied_apps)
    success_rate = calculate_success_rate(apps)
    status_counts = count_by_status(apps)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("応募件数", total)
    m2.metric("内定率", f"{success_rate:.0%}")
    m3.metric("面接中", status_counts.get("面接", 0))
    m4.metric("7日以内の締切", len(upcoming))

    st.divider()

    if upcoming:
        st.subheader("直近の締切")

        for item in sorted(upcoming, key=lambda value: value["deadline"]):
            if item["days_left"] == 0:
                days_text = "本日締切"
            else:
                days_text = f"あと{item['days_left']}日"

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

        selected_statuses = filter_col.multiselect(
            "ステータス絞り込み",
            STATUSES,
        )

        keyword = search_col.text_input(
            "キーワード検索",
            placeholder="企業名や職種で検索",
        )

        filtered = apps

        if selected_statuses:
            filtered = [
                item
                for item in filtered
                if item["status"] in selected_statuses
            ]

        if keyword:
            word = keyword.lower()
            filtered = [
                item
                for item in filtered
                if word in item["company"].lower()
                or word in item["position"].lower()
            ]

        if not apps:
            st.info("応募データを追加すると、ここに一覧が表示されます。")

        elif not filtered:
            st.warning("条件に合うデータが見つかりません。")

        else:
            df = pd.DataFrame(filtered)[
                [
                    "id",
                    "company",
                    "position",
                    "status",
                    "applied_date",
                    "deadline",
                    "notes",
                ]
            ]

            df.columns = [
                "ID",
                "企業名",
                "職種",
                "ステータス",
                "応募日",
                "締切日",
                "メモ",
            ]

            # この色分けは一覧だけで使うので、ここでまとめて指定する
            def status_style(value):
                colors = STATUS_COLORS.get(
                    value,
                    {"bg": "#f2f2f2", "text": "#555"},
                )
                return (
                    f"background-color: {colors['bg']}; "
                    f"color: {colors['text']}; "
                    "font-weight: 700; border-radius: 6px;"
                )

            styled_df = df.style.map(
                status_style,
                subset=["ステータス"],
            )
            styled_df = styled_df.set_properties(
                subset=["ID", "企業名"],
                **{"text-align": "center"},
            )

            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
            )

            csv_data = df.to_csv(index=False).encode("utf-8-sig")

            st.download_button(
                "CSV形式でダウンロード",
                data=csv_data,
                file_name="jobs.csv",
                mime="text/csv",
                use_container_width=True,
            )

        st.divider()
        st.subheader("データの編集")

        if apps:
            edit_options = {
                f'{item["company"]} / {item["position"]}（ID:{item["id"]}）':
                    item
                for item in apps
            }

            selected_edit_label = st.selectbox(
                "編集する項目を選択",
                options=list(edit_options.keys()),
                key="edit_application_selector",
            )
            selected_edit = edit_options[selected_edit_label]

            current_status = selected_edit["status"]
            status_index = (
                STATUSES.index(current_status)
                if current_status in STATUSES
                else 0
            )

            current_applied_date = date.fromisoformat(
                selected_edit["applied_date"]
            )

            current_deadline = (
                date.fromisoformat(selected_edit["deadline"])
                if selected_edit.get("deadline")
                else current_applied_date + timedelta(days=7)
            )

            with st.form("edit_application_form"):
                edit_company = st.text_input(
                    "企業名",
                    value=selected_edit["company"],
                )
                edit_position = st.text_input(
                    "職種・コース",
                    value=selected_edit["position"],
                )
                edit_status = st.selectbox(
                    "選考状況",
                    options=STATUSES,
                    index=status_index,
                    key="edit_status",
                )
                edit_applied_date = st.date_input(
                    "応募日",
                    value=current_applied_date,
                    key="edit_applied_date",
                )

                has_deadline = st.checkbox(
                    "締切日を設定する",
                    value=selected_edit.get("deadline") is not None,
                    key="edit_has_deadline",
                )

                edit_deadline_value = st.date_input(
                    "締切日",
                    value=current_deadline,
                    key="edit_deadline",
                )

                edit_notes = st.text_area(
                    "メモ",
                    value=selected_edit.get("notes") or "",
                    placeholder="次回予定、提出物、連絡事項など",
                )

                update_submitted = st.form_submit_button(
                    "変更を保存",
                    type="primary",
                    use_container_width=True,
                )

            if update_submitted:
                if not edit_company.strip():
                    st.error("企業名を入力してください。")
                elif not edit_position.strip():
                    st.error("職種・コースを入力してください。")
                else:
                    updated_application = Application(
                        company=edit_company.strip(),
                        position=edit_position.strip(),
                        status=edit_status,
                        applied_date=edit_applied_date,
                        deadline=(
                            edit_deadline_value
                            if has_deadline
                            else None
                        ),
                        notes=edit_notes.strip(),
                    )

                    update_application(
                        conn,
                        selected_edit["id"],
                        updated_application,
                    )
                    st.success("選考情報を更新しました。")
                    st.rerun()
        else:
            st.info("編集できるデータがありません。")

        st.subheader("データの削除")

        delete_options = {}

        for item in apps:
            label = (
                f"{item['company']} "
                f"({item['position']}) "
                f"- ID:{item['id']}"
            )
            delete_options[label] = item["id"]

        selected_item = st.selectbox(
            "削除する項目を選択",
            options=list(delete_options.keys()),
        )

        confirmed = st.checkbox(
            "削除する内容を確認しました"
        )

        delete_clicked = st.button(
            "選択した項目を削除",
            type="secondary",
            disabled=not confirmed,
            use_container_width=True,
        )

        if delete_clicked:
            delete_application(
                conn,
                delete_options[selected_item],
            )
            st.success("削除しました。")
            st.rerun()

    with tab_stats:
        st.subheader("応募データの集計")

        if not apps:
            st.info("応募データを追加すると、集計グラフが表示されます。")
        else:
            data = pd.DataFrame(apps)
            data["applied_date"] = pd.to_datetime(data["applied_date"])
            data["応募月"] = data["applied_date"].dt.strftime("%Y-%m")

            status_data = data["status"].value_counts().reset_index()
            status_data.columns = ["選考状況", "件数"]

            monthly_data = data.groupby("応募月").size().reset_index(name="件数")

            chart_left, chart_right = st.columns(2)

            with chart_left:
                st.markdown("#### 選考状況別の応募件数")
                st.bar_chart(
                    status_data.set_index("選考状況"),
                    use_container_width=True,
                )

            with chart_right:
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
