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
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        [data-testid="stMetric"] {
            background: rgba(245, 247, 250, 0.85);
            border: 1px solid rgba(120, 120, 120, 0.18);
            border-radius: 14px;
            padding: 18px;
        }

        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(120, 120, 120, 0.18);
        }

        .app-subtitle {
            color: #6b7280;
            font-size: 1rem;
            margin-top: -0.7rem;
            margin-bottom: 1.5rem;
        }

        .deadline-warning {
            border-left: 5px solid #f59e0b;
            background: rgba(245, 158, 11, 0.10);
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 10px;
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

    deadline_count = 0
    today = date.today()
    next_week = today + timedelta(days=7)

    for item in applications:
        deadline_value = item.get("deadline")

        if deadline_value:
            deadline_date = date.fromisoformat(deadline_value)

            if today <= deadline_date <= next_week:
                deadline_count += 1

    column1, column2, column3, column4 = st.columns(4)

    column1.metric("応募件数", total)
    column2.metric("通過・内定率", f"{success_rate:.0%}")
    column3.metric("面接中", status_counts.get("面接", 0))
    column4.metric("7日以内の締切", deadline_count)


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


def render_visual_theme() -> None:
    """温暖な旅の手帳をイメージしたテーマを適用する。"""

    st.markdown(
        """
        <style>
        /*
        ==========================================
        My Career Journey
        Warm Minimalism × Soft Adventure
        ==========================================
        */

        :root {
            color-scheme: light dark;
        }

        .stApp {
            background-color: var(--st-background-color);
            background-image:
                radial-gradient(
                    circle at 88% 8%,
                    rgba(198, 142, 91, 0.09),
                    transparent 27rem
                ),
                radial-gradient(
                    circle at 12% 82%,
                    rgba(126, 145, 108, 0.08),
                    transparent 25rem
                ),
                repeating-linear-gradient(
                    0deg,
                    transparent,
                    transparent 4px,
                    rgba(116, 91, 68, 0.012) 5px
                );
        }

        .block-container {
            max-width: 1240px;
            padding-top: 2.2rem;
            padding-bottom: 4rem;
        }

        /*
        Header
        */

        [data-testid="stHeader"] {
            background:
                color-mix(
                    in srgb,
                    var(--st-background-color) 88%,
                    transparent
                );
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
        }

        /*
        Sidebar — 手帳の表紙
        */

        [data-testid="stSidebar"] {
            background:
                linear-gradient(
                    180deg,
                    color-mix(
                        in srgb,
                        var(--st-secondary-background-color) 96%,
                        #d5b58c 4%
                    ),
                    var(--st-secondary-background-color)
                );
            border-right:
                1px solid
                color-mix(
                    in srgb,
                    var(--st-text-color) 12%,
                    transparent
                );
            box-shadow: 12px 0 35px rgba(73, 55, 40, 0.045);
        }

        [data-testid="stSidebar"] .block-container {
            padding-top: 2rem;
        }

        /*
        Hero — 旅の手帳の最初のページ
        */

        .dashboard-hero {
            position: relative;
            overflow: hidden;
            min-height: 260px;
            padding: 2.45rem 2.6rem;
            margin-bottom: 1.8rem;
            border:
                1px solid
                color-mix(
                    in srgb,
                    var(--st-text-color) 10%,
                    transparent
                );
            border-radius: 30px;
            background:
                radial-gradient(
                    circle at 92% 14%,
                    rgba(255, 247, 220, 0.62),
                    transparent 30%
                ),
                linear-gradient(
                    135deg,
                    #d58b69 0%,
                    #bd765c 42%,
                    #87946f 100%
                );
            box-shadow:
                0 22px 55px rgba(84, 59, 42, 0.14),
                inset 0 1px 0 rgba(255, 255, 255, 0.28);
            color: #fffaf1;
        }

        .dashboard-hero::before {
            content: "";
            position: absolute;
            inset: 0;
            opacity: 0.13;
            pointer-events: none;
            background-image:
                repeating-linear-gradient(
                    8deg,
                    transparent,
                    transparent 5px,
                    rgba(255, 255, 255, 0.18) 6px
                );
        }

        .dashboard-hero::after {
            content: "✦";
            position: absolute;
            top: 1.25rem;
            right: 1.6rem;
            color: rgba(255, 244, 198, 0.72);
            font-size: 2rem;
            transform: rotate(12deg);
        }

        .dashboard-hero__content {
            position: relative;
            z-index: 2;
            max-width: 650px;
        }

        .dashboard-hero__eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            margin-bottom: 0.75rem;
            padding: 0.35rem 0.72rem;
            border:
                1px solid
                rgba(255, 255, 255, 0.25);
            border-radius: 999px;
            background: rgba(255, 250, 241, 0.11);
            color: rgba(255, 250, 241, 0.92);
            font-size: 0.72rem;
            font-weight: 750;
            letter-spacing: 0.13em;
        }

        .dashboard-hero h1 {
            margin: 0;
            padding: 0;
            color: #fffaf1;
            font-family:
                Georgia,
                "Hiragino Mincho ProN",
                "Yu Mincho",
                serif;
            font-size: clamp(2.15rem, 4vw, 3.2rem);
            font-weight: 700;
            letter-spacing: -0.035em;
            line-height: 1.12;
        }

        .dashboard-hero__subtitle {
            max-width: 620px;
            margin: 0.85rem 0 0;
            color: rgba(255, 250, 241, 0.88);
            font-size: 1rem;
            line-height: 1.75;
        }

        /*
        旅のルート
        */

        .journey-path {
            position: relative;
            z-index: 2;
            display: grid;
            grid-template-columns:
                minmax(74px, 1fr)
                1fr
                minmax(74px, 1fr)
                1fr
                minmax(74px, 1fr)
                1fr
                minmax(74px, 1fr);
            align-items: start;
            max-width: 720px;
            margin-top: 2rem;
        }

        .journey-stop {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.38rem;
            text-align: center;
        }

        .journey-node {
            display: grid;
            place-items: center;
            width: 36px;
            height: 36px;
            border:
                2px solid
                rgba(255, 250, 241, 0.82);
            border-radius: 50%;
            background: rgba(91, 74, 55, 0.20);
            box-shadow:
                0 4px 12px rgba(71, 51, 37, 0.12);
            color: #fff8df;
            font-size: 0.95rem;
        }

        .journey-node--goal {
            border-color: #ffe7a4;
            background: #c7a45c;
            color: #fffaf1;
        }

        .journey-label {
            color: rgba(255, 250, 241, 0.90);
            font-size: 0.72rem;
            font-weight: 650;
            white-space: nowrap;
        }

        .journey-line {
            height: 2px;
            margin-top: 17px;
            background-image:
                repeating-linear-gradient(
                    90deg,
                    rgba(255, 250, 241, 0.66) 0,
                    rgba(255, 250, 241, 0.66) 8px,
                    transparent 8px,
                    transparent 14px
                );
        }

        /*
        旅の言葉
        */

        .journey-quote {
            display: flex;
            align-items: center;
            gap: 0.65rem;
            margin: -0.25rem 0 1.35rem;
            padding: 0.8rem 1rem;
            border-left: 3px solid #b68a57;
            border-radius: 0 14px 14px 0;
            background:
                color-mix(
                    in srgb,
                    var(--st-secondary-background-color) 82%,
                    transparent
                );
            color:
                color-mix(
                    in srgb,
                    var(--st-text-color) 82%,
                    #70543b 18%
                );
            font-family:
                Georgia,
                "Hiragino Mincho ProN",
                "Yu Mincho",
                serif;
            font-size: 0.94rem;
            font-style: italic;
        }

        /*
        KPI カード — 紙のカード
        */

        div[data-testid="stMetric"] {
            min-height: 132px;
            padding: 1.15rem 1.25rem;
            border:
                1px solid
                color-mix(
                    in srgb,
                    var(--st-text-color) 10%,
                    transparent
                );
            border-radius: 22px;
            background:
                linear-gradient(
                    145deg,
                    color-mix(
                        in srgb,
                        var(--st-secondary-background-color) 97%,
                        #f4dfbd 3%
                    ),
                    var(--st-secondary-background-color)
                );
            box-shadow:
                0 10px 28px rgba(73, 54, 38, 0.075),
                inset 0 1px 0 rgba(255, 255, 255, 0.36);
            transition:
                transform 180ms ease,
                box-shadow 180ms ease;
        }

        div[data-testid="stMetric"]:hover {
            transform: translateY(-4px) rotate(-0.15deg);
            box-shadow:
                0 18px 36px rgba(104, 75, 48, 0.13),
                inset 0 1px 0 rgba(255, 255, 255, 0.42);
        }

        div[data-testid="stMetricLabel"] {
            color:
                color-mix(
                    in srgb,
                    var(--st-text-color) 70%,
                    #7d6a58 30%
                );
            font-size: 0.87rem;
            font-weight: 650;
        }

        div[data-testid="stMetricValue"] {
            color:
                color-mix(
                    in srgb,
                    var(--st-text-color) 88%,
                    #65513e 12%
                );
            font-family:
                Georgia,
                "Hiragino Mincho ProN",
                "Yu Mincho",
                serif;
            font-size: 2.05rem;
            font-weight: 700;
        }

        /*
        タブ
        */

        div[data-testid="stTabs"] button {
            padding: 0.7rem 1.15rem;
            border-radius: 999px;
            font-weight: 650;
        }

        div[data-testid="stTabs"] button[aria-selected="true"] {
            background:
                color-mix(
                    in srgb,
                    var(--st-primary-color) 13%,
                    transparent
                );
        }

        /*
        表・アラート
        */

        div[data-testid="stDataFrame"] {
            overflow: hidden;
            border:
                1px solid
                color-mix(
                    in srgb,
                    var(--st-text-color) 10%,
                    transparent
                );
            border-radius: 20px;
            background: var(--st-secondary-background-color);
            box-shadow:
                0 12px 30px rgba(74, 57, 42, 0.06);
        }

        div[data-testid="stAlert"] {
            border:
                1px solid
                color-mix(
                    in srgb,
                    var(--st-text-color) 8%,
                    transparent
                );
            border-radius: 18px;
            background:
                color-mix(
                    in srgb,
                    var(--st-secondary-background-color) 91%,
                    transparent
                );
            box-shadow:
                0 7px 20px rgba(74, 57, 42, 0.045);
        }

        /*
        フォーム
        */

        div[data-baseweb="select"] > div,
        div[data-testid="stTextInputRootElement"],
        div[data-testid="stDateInput"] > div,
        div[data-testid="stTextArea"] textarea {
            border-radius: 14px;
            background:
                color-mix(
                    in srgb,
                    var(--st-secondary-background-color) 95%,
                    transparent
                );
        }

        /*
        ボタン
        */

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 999px;
            font-weight: 680;
            transition:
                transform 160ms ease,
                box-shadow 160ms ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            transform: translateY(-2px);
        }

        .stButton > button[kind="primary"] {
            border: none;
            background:
                linear-gradient(
                    135deg,
                    #b96f52,
                    #8c9872
                );
            color: #fffaf1;
            box-shadow:
                0 8px 20px rgba(148, 96, 65, 0.23);
        }

        .stButton > button[kind="primary"]:hover {
            color: #fffaf1;
            box-shadow:
                0 12px 26px rgba(148, 96, 65, 0.31);
        }

        /*
        区切り線
        */

        hr {
            border-color:
                color-mix(
                    in srgb,
                    var(--st-text-color) 9%,
                    transparent
                ) !important;
        }

        /*
        Footer
        */

        .journey-footer {
            margin-top: 1rem;
            padding: 1rem;
            color:
                color-mix(
                    in srgb,
                    var(--st-text-color) 60%,
                    transparent
                );
            text-align: center;
            font-size: 0.82rem;
            letter-spacing: 0.02em;
        }

        /*
        Mobile
        */

        @media (max-width: 760px) {
            .dashboard-hero {
                min-height: auto;
                padding: 1.7rem 1.4rem;
                border-radius: 23px;
            }

            .journey-path {
                grid-template-columns:
                    minmax(55px, 1fr)
                    0.55fr
                    minmax(55px, 1fr)
                    0.55fr
                    minmax(55px, 1fr)
                    0.55fr
                    minmax(55px, 1fr);
            }

            .journey-label {
                font-size: 0.62rem;
            }

            .journey-node {
                width: 31px;
                height: 31px;
            }

            .journey-line {
                margin-top: 15px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )



def render_dashboard_header() -> None:
    """求職活動を旅に見立てたヒーローセクションを表示する。"""

    st.markdown(
        """
        <section class="dashboard-hero">
            <div class="dashboard-hero__content">
                <div class="dashboard-hero__eyebrow">
                    ✦ MY CAREER JOURNEY
                </div>

                <h1>未来へ続く、私の旅。</h1>

                <p class="dashboard-hero__subtitle">
                    一つひとつの応募は、新しい場所へ向かう小さな一歩。
                    企業、選考、締切、そして旅の途中で得た気づきを、
                    自分だけの手帳に残していきましょう。
                </p>

                <div class="journey-path">
                    <div class="journey-stop">
                        <span class="journey-node">✎</span>
                        <span class="journey-label">準備</span>
                    </div>

                    <div class="journey-line"></div>

                    <div class="journey-stop">
                        <span class="journey-node">✉</span>
                        <span class="journey-label">応募</span>
                    </div>

                    <div class="journey-line"></div>

                    <div class="journey-stop">
                        <span class="journey-node">⌁</span>
                        <span class="journey-label">面接</span>
                    </div>

                    <div class="journey-line"></div>

                    <div class="journey-stop">
                        <span class="journey-node journey-node--goal">★</span>
                        <span class="journey-label">内定</span>
                    </div>
                </div>
            </div>
        </section>

        <div class="journey-quote">
            🧭 The road unfolds one gentle step at a time.
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

    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1240px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .dashboard-hero {
            padding: 2rem 2.2rem;
            margin-bottom: 1.6rem;
            border-radius: 24px;
            background:
                linear-gradient(
                    135deg,
                    rgba(30, 64, 175, 0.96),
                    rgba(14, 116, 144, 0.90)
                );
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.16);
            color: white;
        }

        .dashboard-hero__eyebrow {
            margin-bottom: 0.6rem;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.18em;
            opacity: 0.78;
        }

        .dashboard-hero h1 {
            margin: 0;
            padding: 0;
            color: white;
            font-size: 2.35rem;
            line-height: 1.2;
        }

        .dashboard-hero p {
            max-width: 720px;
            margin: 0.75rem 0 0;
            color: rgba(255, 255, 255, 0.88);
            font-size: 1rem;
            line-height: 1.7;
        }

        div[data-testid="stMetric"] {
            min-height: 128px;
            padding: 1.15rem 1.25rem;
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.78);
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.07);
        }

        div[data-testid="stMetricLabel"] {
            font-size: 0.88rem;
            font-weight: 600;
        }

        div[data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 750;
        }

        div[data-testid="stTabs"] button {
            padding-left: 1.15rem;
            padding-right: 1.15rem;
            font-weight: 650;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid rgba(148, 163, 184, 0.20);
            border-radius: 16px;
            overflow: hidden;
        }

        div[data-testid="stAlert"] {
            border-radius: 14px;
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 12px;
            font-weight: 650;
        }

        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(148, 163, 184, 0.20);
        }

        [data-testid="stSidebar"] .block-container {
            padding-top: 2rem;
        }

        @media (max-width: 760px) {
            .dashboard-hero {
                padding: 1.5rem;
                border-radius: 18px;
            }

            .dashboard-hero h1 {
                font-size: 1.9rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    render_visual_theme()
    render_dashboard_header()

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
        render_application_table(connection, applications)

    with statistics_tab:
        render_statistics(applications)

    st.divider()
    st.markdown(
        """
        <div class="journey-footer">
            Made with ☕ for every brave journey.<br>
            My Career Journey · Powered by Job Tracker
        </div>
        """,
        unsafe_allow_html=True,
    )

    connection.close()
