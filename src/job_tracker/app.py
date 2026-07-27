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
from job_tracker.stats import calculate_success_rate, calculate_total, count_by_status


STATUSES = [
    "検討中",
    "応募済み",
    "書類選考",
    "面接",
    "通過",
    "内定",
    "不合格",
]


def apply_custom_style() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1200px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
        }

        [data-testid="stSidebar"] {
            background: #fafaf9;
            border-right: 1px solid #e5e7eb;
        }

        .app-subtitle {
            color: #6b7280;
            font-size: 0.95rem;
            margin-top: -0.4rem;
            margin-bottom: 2rem;
        }

        .deadline-warning {
            border-left: 5px solid #f59e0b;
            background: #fffbeb;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 10px;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            overflow: hidden;
        }

        div[data-testid="stAlert"] {
            border-radius: 10px;
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 8px;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_add_form(connection) -> None:
    st.sidebar.header("➕ 新しい応募を追加")

    with st.sidebar.form("application_form", clear_on_submit=True):
        company = st.text_input(
            "企業名",
            placeholder="例：株式会社〇〇",
        )
        position = st.text_input(
            "職種・コース",
            placeholder="例：データアナリスト",
        )
        status = st.selectbox("選考状況", STATUSES)
        applied_date = st.date_input("応募日", value=date.today())

        use_deadline = st.checkbox("締切日を設定する")
        deadline = None

        if use_deadline:
            deadline = st.date_input(
                "締切日",
                value=date.today() + timedelta(days=7),
            )

        notes = st.text_area(
            "メモ",
            placeholder="説明会、面接、提出物など",
        )

        submitted = st.form_submit_button(
            "応募情報を追加",
            width='stretch',
            type="primary",
        )

    if submitted:
        if not company.strip():
            st.sidebar.error("企業名を入力してください。")
        elif not position.strip():
            st.sidebar.error("職種・コースを入力してください。")
        else:
            application = Application(
                company=company.strip(),
                position=position.strip(),
                status=status,
                applied_date=applied_date,
                deadline=deadline,
                notes=notes.strip(),
            )
            add_application(connection, application)
            st.sidebar.success("応募情報を追加しました。")
            st.rerun()


def render_metrics(applications: list[dict]) -> None:
    total = calculate_total(applications)
    success_rate = calculate_success_rate(applications)
    status_counts = count_by_status(applications)

    today = date.today()
    next_week = today + timedelta(days=7)

    deadline_count = sum(
        1
        for item in applications
        if item.get("deadline")
        and today <= date.fromisoformat(item["deadline"]) <= next_week
    )

    metrics = [
        ("応募件数", total),
        ("通過・内定率", f"{success_rate:.0%}"),
        ("面接中", status_counts.get("面接", 0)),
        ("7日以内の締切", deadline_count),
    ]

    columns = st.columns(len(metrics))

    for column, (label, value) in zip(columns, metrics):
        column.metric(label, value)


def render_deadline_alerts(applications: list[dict]) -> None:
    today = date.today()
    next_week = today + timedelta(days=7)

    upcoming = []

    for item in applications:
        deadline_value = item.get("deadline")

        if not deadline_value:
            continue

        deadline_date = date.fromisoformat(deadline_value)

        if today <= deadline_date <= next_week:
            upcoming.append(
                {
                    "company": item["company"],
                    "position": item["position"],
                    "deadline": deadline_date,
                    "days_left": (deadline_date - today).days,
                }
            )

    if not upcoming:
        return

    st.subheader("⏰ 締切アラート")

    for item in sorted(upcoming, key=lambda value: value["deadline"]):
        days_left = item["days_left"]

        if days_left == 0:
            remaining_text = "本日締切"
        else:
            remaining_text = f"あと{days_left}日"

        st.markdown(
            f"""
            <div class="deadline-warning">
                <strong>{item["company"]}</strong>
                ／ {item["position"]}<br>
                締切：{item["deadline"].strftime("%Y/%m/%d")}
                （{remaining_text}）
            </div>
            """,
            unsafe_allow_html=True,
        )







def render_application_table(
    connection,
    applications: list[dict],
) -> None:
    st.subheader("📋 応募一覧")

    filter_column1, filter_column2 = st.columns([1, 2])

    with filter_column1:
        selected_statuses = st.multiselect(
            "選考状況で絞り込み",
            options=STATUSES,
            default=[],
        )

    with filter_column2:
        keyword = st.text_input(
            "企業名・職種を検索",
            placeholder="キーワードを入力",
        )

    filtered = applications

    if selected_statuses:
        filtered = [
            item
            for item in filtered
            if item["status"] in selected_statuses
        ]

    if keyword.strip():
        normalized_keyword = keyword.strip().lower()
        filtered = [
            item
            for item in filtered
            if normalized_keyword in item["company"].lower()
            or normalized_keyword in item["position"].lower()
        ]

    if not filtered:
        st.info("条件に一致する応募情報がありません。")
        return

    dataframe = pd.DataFrame(filtered)

    display_dataframe = dataframe[
        [
            "id",
            "company",
            "position",
            "status",
            "applied_date",
            "deadline",
            "notes",
        ]
    ].copy()

    display_dataframe.columns = [
        "ID",
        "企業名",
        "職種・コース",
        "選考状況",
        "応募日",
        "締切日",
        "メモ",
    ]

    status_labels = {
        "検討中": "⚪ 検討中",
        "応募済み": "🔵 応募済み",
        "書類選考": "🟣 書類選考",
        "書類通過": "🟦 書類通過",
        "通過": "🟢 通過",
        "一次面接": "🟠 一次面接",
        "二次面接": "🟠 二次面接",
        "最終面接": "🟡 最終面接",
        "面接": "🟠 面接",
        "面接中": "🟠 面接中",
        "内定": "🟢 内定",
        "不合格": "🔴 不合格",
        "辞退": "⚫ 辞退",
    }

    display_dataframe["選考状況"] = (
        display_dataframe["選考状況"]
        .map(status_labels)
        .fillna(display_dataframe["選考状況"])
    )

    applied_dates = pd.to_datetime(
        display_dataframe["応募日"],
        errors="coerce",
    )
    display_dataframe["応募日"] = applied_dates.dt.strftime("%Y/%m/%d")
    display_dataframe["応募日"] = display_dataframe["応募日"].fillna("")

    today = pd.Timestamp.today().normalize()

    def format_deadline(value: object) -> str:
        if pd.isna(value) or value in ("", "None"):
            return ""

        deadline = pd.to_datetime(value, errors="coerce")

        if pd.isna(deadline):
            return ""

        deadline = deadline.normalize()
        remaining_days = (deadline - today).days
        date_text = deadline.strftime("%Y/%m/%d")

        if remaining_days < 0:
            return f"🔴 {date_text}（{abs(remaining_days)}日超過）"
        if remaining_days == 0:
            return f"🚨 {date_text}（本日締切）"
        if remaining_days == 1:
            return f"🟠 {date_text}（明日締切）"
        if remaining_days <= 7:
            return f"🟡 {date_text}（あと{remaining_days}日）"

        return f"📅 {date_text}（あと{remaining_days}日）"

    display_dataframe["締切日"] = display_dataframe["締切日"].apply(
        format_deadline
    )

    display_dataframe["メモ"] = (
        display_dataframe["メモ"]
        .fillna("")
        .replace("None", "")
    )

    st.dataframe(
        display_dataframe,
        width="stretch",
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn(width="small"),
            "企業名": st.column_config.TextColumn(width="medium"),
            "職種・コース": st.column_config.TextColumn(width="medium"),
            "選考状況": st.column_config.TextColumn(width="small"),
            "応募日": st.column_config.TextColumn(width="small"),
            "締切日": st.column_config.TextColumn(width="medium"),
            "メモ": st.column_config.TextColumn(width="large"),
        },
    )

    csv_data = display_dataframe.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="CSV形式でダウンロード",
        data=csv_data,
        file_name="job_applications.csv",
        mime="text/csv",
    )

    st.divider()
    st.subheader("🗑 応募情報を削除")

    application_options = {
        f'{item["company"]}｜{item["position"]}｜{item["status"]}': item["id"]
        for item in applications
    }

    selected_application = st.selectbox(
        "削除する応募情報",
        options=list(application_options.keys()),
    )

    confirm_delete = st.checkbox("削除内容を確認しました")

    if st.button(
        "選択した応募を削除",
        disabled=not confirm_delete,
    ):
        application_id = application_options[selected_application]
        delete_application(connection, application_id)
        st.success("応募情報を削除しました。")
        st.rerun()


def render_statistics(applications: list[dict]) -> None:
    st.subheader("📊 統計・分析")

    if not applications:
        st.info("分析する応募情報がありません。")
        return

    dataframe = pd.DataFrame(applications)
    dataframe["applied_date"] = pd.to_datetime(dataframe["applied_date"])
    dataframe["応募月"] = dataframe["applied_date"].dt.strftime("%Y-%m")

    status_counts = (
        dataframe["status"]
        .value_counts()
        .rename_axis("選考状況")
        .reset_index(name="件数")
    )

    monthly_counts = (
        dataframe.groupby("応募月")
        .size()
        .reset_index(name="応募件数")
        .sort_values("応募月")
    )

    chart_column1, chart_column2 = st.columns(2)

    with chart_column1:
        st.markdown("#### 選考状況別の応募件数")
        st.bar_chart(
            status_counts.set_index("選考状況"),
            width='stretch',
        )

    with chart_column2:
        st.markdown("#### 月別応募件数")
        st.line_chart(
            monthly_counts.set_index("応募月"),
            width='stretch',
        )

    st.markdown("#### 選考状況サマリー")
    st.dataframe(
        status_counts,
        width='stretch',
        hide_index=True,
    )

def render_app() -> None:
    st.set_page_config(
        page_title="Job Tracker",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    apply_custom_style()

    connection = connect()
    initialize_database(connection)

    render_add_form(connection)

    st.title("📋 就職活動管理ツール")
    st.markdown(
        '<p class="app-subtitle">'
        "応募企業、選考状況、締切を一元管理するためのWebアプリケーション"
        "</p>",
        unsafe_allow_html=True,
    )

    applications = get_applications(connection)

    render_metrics(applications)

    st.divider()

    if not applications:
        st.info(
            "まだ応募情報がありません。"
            "左側のフォームから最初の応募情報を追加してください。"
        )
        connection.close()
        return

    render_deadline_alerts(applications)

    list_tab, statistics_tab = st.tabs(
        ["応募情報", "統計・分析"]
    )

    with list_tab:
        render_application_table(
            connection,
            applications,
        )

    with statistics_tab:
        render_statistics(applications)

    connection.close()
