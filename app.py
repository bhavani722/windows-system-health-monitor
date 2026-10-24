
import csv
import os
import json
import platform
from datetime import datetime
from io import BytesIO

import pandas as pd
import psutil
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Windows Health Monitor",
    page_icon="💻",
    layout="wide"
)


# --------------------------------------------------
# LOGIN SYSTEM
# --------------------------------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.markdown("""
    <style>
    .login-title {
        text-align: center;
        font-size: 30px;
        font-weight: 700;
        color: #2563eb;
        margin-bottom: 8px;
    }

    .login-subtitle {
        text-align: center;
        color: #64748b;
        margin-bottom: 25px;
    }

    div[data-testid="stForm"] {
        padding: 25px;
        border: 1px solid #dbeafe;
        border-radius: 16px;
        background-color: rgba(59, 130, 246, 0.04);
    }

    div[data-testid="stFormSubmitButton"] button {
        width: 100%;
        background: linear-gradient(90deg, #2563eb, #4f46e5);
        color: white;
        border: none;
        border-radius: 10px;
        height: 45px;
        font-size: 16px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

    st.write("")
    left, center, right = st.columns([1, 1.3, 1])

    with center:
        st.markdown(
            '<div class="login-title">'
            '💻 Windows Health Monitor</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="login-subtitle">'
            'Sign in to monitor your system</div>',
            unsafe_allow_html=True
        )

        with st.form("login_form"):
            username = st.text_input("👤 Username")
            password = st.text_input(
                "🔑 Password",
                type="password"
            )

            submitted = st.form_submit_button(
                "🔐 Login to Dashboard",
                width="stretch"
            )

            if submitted:
                if username == "admin" and password == "admin123":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid username or password")

    st.stop()


# --------------------------------------------------
# CSV FILES
# --------------------------------------------------

history_file = "system_health_history.csv"
alert_file = "system_alert_history.csv"

if not os.path.exists(history_file):
    with open(history_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Timestamp", "CPU Usage",
            "RAM Usage", "Disk Usage"
        ])

if not os.path.exists(alert_file):
    with open(alert_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Timestamp", "Component", "Usage (%)",
            "Threshold (%)", "Alert Message"
        ])

if "active_alerts" not in st.session_state:
    st.session_state.active_alerts = set()


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

st.sidebar.title("💻 Health Monitor")
st.sidebar.caption("Windows System Monitoring")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "📊 Performance History",
        "🚨 Alert History",
        "📄 Reports"
    ],
    key="main_navigation"
)

st.sidebar.divider()
st.sidebar.subheader("⚙️ Alert Thresholds")

cpu_limit = st.sidebar.slider(
    "CPU Threshold (%)", 50, 100, 80,
    key="cpu_threshold"
)

ram_limit = st.sidebar.slider(
    "RAM Threshold (%)", 50, 100, 80,
    key="ram_threshold"
)

disk_limit = st.sidebar.slider(
    "Disk Threshold (%)", 50, 100, 90,
    key="disk_threshold"
)

st.sidebar.divider()
st.sidebar.info("Monitoring refreshes every 5 seconds.")

if st.sidebar.button("🚪 Logout", width="stretch"):
    st.session_state.logged_in = False
    st.rerun()


# --------------------------------------------------
# AUTOMATIC REFRESH
# --------------------------------------------------

st_autorefresh(
    interval=5000,
    limit=None,
    key="health_monitor_refresh"
)


# --------------------------------------------------
# BROWSER NOTIFICATIONS
# --------------------------------------------------

def show_browser_notification(title, message):
    safe_title = json.dumps(title)
    safe_message = json.dumps(message)

    st.components.v1.html(
        f"""
        <script>
        const title = {safe_title};
        const message = {safe_message};

        if ("Notification" in window) {{
            if (Notification.permission === "granted") {{
                new Notification(title, {{ body: message }});
            }} else if (Notification.permission === "default") {{
                Notification.requestPermission();
            }}
        }}
        </script>
        """,
        height=0
    )


# --------------------------------------------------
# COLLECT SYSTEM READINGS
# --------------------------------------------------

cpu = psutil.cpu_percent(interval=1)
ram = psutil.virtual_memory()
disk = psutil.disk_usage("C:\\")

now = datetime.now()

with open(history_file, "a", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([
        now.strftime("%Y-%m-%d %H:%M:%S"),
        cpu,
        ram.percent,
        disk.percent
    ])


# --------------------------------------------------
# DETECT AND SAVE NEW ALERTS
# --------------------------------------------------

current_alerts = []

if cpu >= cpu_limit:
    current_alerts.append((
        "CPU", cpu, cpu_limit,
        f"High CPU usage: {cpu:.1f}%"
    ))

if ram.percent >= ram_limit:
    current_alerts.append((
        "RAM", ram.percent, ram_limit,
        f"High RAM usage: {ram.percent:.1f}%"
    ))

if disk.percent >= disk_limit:
    current_alerts.append((
        "Disk", disk.percent, disk_limit,
        f"High disk usage: {disk.percent:.1f}%"
    ))

previous_alerts = st.session_state.active_alerts

new_alerts = [
    alert for alert in current_alerts
    if alert[0] not in previous_alerts
]

for component, usage, threshold, message in new_alerts:
    with open(alert_file, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            now.strftime("%Y-%m-%d %H:%M:%S"),
            component,
            usage,
            threshold,
            message
        ])

    show_browser_notification(
        f"{component} Health Alert",
        message
    )

st.session_state.active_alerts = {
    alert[0] for alert in current_alerts
}


# --------------------------------------------------
# DASHBOARD PAGE
# --------------------------------------------------

if page == "🏠 Dashboard":

    st.title("💻 Windows System Health Monitor")
    st.write("Real-time monitoring of your computer")
    st.divider()

    st.subheader("🖥️ System Information")

    info1, info2 = st.columns(2)

    with info1:
        st.write("Operating System:", platform.system())
        st.write("Computer Name:", platform.node())

    with info2:
        st.write("OS Version:", platform.version())
        st.write(
            "Monitoring Time:",
            now.strftime("%d-%m-%Y %H:%M:%S")
        )

    st.divider()

    st.subheader("📊 System Performance")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("CPU Usage", f"{cpu:.1f}%")

    with col2:
        st.metric("RAM Usage", f"{ram.percent:.1f}%")

    with col3:
        st.metric("C Drive Usage", f"{disk.percent:.1f}%")

    st.divider()

    st.subheader("💚 Overall System Health")

    if not current_alerts:
        st.success("SYSTEM STATUS: HEALTHY")
    else:
        st.error(
            "SYSTEM STATUS: WARNING - "
            "High resource usage detected"
        )

    st.subheader("System Health Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "CPU Status",
            "HIGH" if cpu >= cpu_limit else "NORMAL"
        )

    with col2:
        st.metric(
            "RAM Status",
            "HIGH" if ram.percent >= ram_limit else "NORMAL"
        )

    with col3:
        st.metric(
            "Disk Status",
            "HIGH" if disk.percent >= disk_limit else "NORMAL"
        )

    st.divider()

    st.subheader("🧪 Alert Testing")

    if st.button("Test CPU Alert"):
        st.warning("TEST ALERT: High CPU usage detected!")

    st.divider()

    st.subheader("🚨 Current Health Alerts")

    if cpu >= cpu_limit:
        st.warning(f"High CPU usage: {cpu:.1f}%")
    else:
        st.success(f"CPU usage is normal: {cpu:.1f}%")

    if ram.percent >= ram_limit:
        st.warning(f"High RAM usage: {ram.percent:.1f}%")
    else:
        st.success(f"RAM usage is normal: {ram.percent:.1f}%")

    if disk.percent >= disk_limit:
        st.error(f"High disk usage: {disk.percent:.1f}%")
    else:
        st.success(f"Disk usage is normal: {disk.percent:.1f}%")

    st.divider()

    st.subheader("Recent System Readings")

    history = pd.read_csv(history_file)

    st.dataframe(
        history.tail(10),
        width="stretch"
    )


# --------------------------------------------------
# PERFORMANCE HISTORY PAGE
# --------------------------------------------------

elif page == "📊 Performance History":

    st.title("📊 Performance History")
    st.write("Review recent CPU, RAM and disk usage.")

    history = pd.read_csv(history_file)

    if not history.empty:
        st.subheader("System Health Records")

        st.dataframe(
            history.tail(100),
            width="stretch"
        )

        st.subheader("📈 System Performance Trends")

        chart_data = history.tail(100).copy()
        chart_data["Timestamp"] = pd.to_datetime(
            chart_data["Timestamp"]
        )

        chart_data = chart_data.set_index("Timestamp")

        st.line_chart(
            chart_data[
                ["CPU Usage", "RAM Usage", "Disk Usage"]
            ],
            y_label="Usage (%)"
        )
    else:
        st.info("No system history available yet.")


# --------------------------------------------------
# ALERT HISTORY PAGE
# --------------------------------------------------

elif page == "🚨 Alert History":

    st.title("🚨 Alert History")
    st.write("View alerts recorded by the monitoring system.")

    alert_history = pd.read_csv(alert_file)

    if not alert_history.empty:
        st.dataframe(
            alert_history.tail(100),
            width="stretch"
        )
    else:
        st.info("No alerts recorded yet.")

    st.divider()
    st.subheader("Alert History Management")

    if st.button("🗑️ Clear Alert History"):
        with open(alert_file, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                "Timestamp", "Component", "Usage (%)",
                "Threshold (%)", "Alert Message"
            ])

        st.session_state.active_alerts = set()
        st.success("Alert history cleared successfully!")
        st.rerun()


# --------------------------------------------------
# REPORTS PAGE
# --------------------------------------------------

elif page == "📄 Reports":

    st.title("📄 System Health Reports")
    st.write("Download system readings and alert reports.")

    with open(history_file, "rb") as file:
        st.download_button(
            "📥 Download System Health Report (CSV)",
            data=file,
            file_name="system_health_report.csv",
            mime="text/csv",
            width="stretch"
        )

    with open(alert_file, "rb") as file:
        st.download_button(
            "📥 Download Alert History Report (CSV)",
            data=file,
            file_name="alert_history_report.csv",
            mime="text/csv",
            width="stretch"
        )

    st.divider()
    st.subheader("📑 PDF Health Report")


    def create_pdf_report():
        buffer = BytesIO()

        pdf = SimpleDocTemplate(
            buffer,
            pagesize=A4
        )

        styles = getSampleStyleSheet()
        content = []

        content.append(
            Paragraph(
                "Windows System Health Report",
                styles["Title"]
            )
        )

        content.append(Spacer(1, 20))

        content.append(
            Paragraph(
                f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}",
                styles["Normal"]
            )
        )

        content.append(Spacer(1, 15))

        report_data = [
            ["Component", "Usage", "Threshold", "Status"],
            [
                "CPU", f"{cpu:.1f}%", f"{cpu_limit}%",
                "HIGH" if cpu >= cpu_limit else "NORMAL"
            ],
            [
                "RAM", f"{ram.percent:.1f}%", f"{ram_limit}%",
                "HIGH" if ram.percent >= ram_limit else "NORMAL"
            ],
            [
                "Disk", f"{disk.percent:.1f}%", f"{disk_limit}%",
                "HIGH" if disk.percent >= disk_limit else "NORMAL"
            ]
        ]

        report_table = Table(report_data)

        report_table.setStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 8),
        ])

        content.append(report_table)
        content.append(Spacer(1, 20))

        content.append(
            Paragraph(
                "Recent Alert History",
                styles["Heading2"]
            )
        )

        alerts = pd.read_csv(alert_file).tail(10)

        if not alerts.empty:
            alert_data = [
                ["Timestamp", "Component", "Usage", "Message"]
            ]

            for _, row in alerts.iterrows():
                alert_data.append([
                    str(row["Timestamp"]),
                    str(row["Component"]),
                    f'{float(row["Usage (%)"]):.1f}%',
                    str(row["Alert Message"])
                ])

            alert_table = Table(
                alert_data,
                repeatRows=1,
                colWidths=[110, 65, 55, 220]
            )

            alert_table.setStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])

            content.append(alert_table)
        else:
            content.append(
                Paragraph(
                    "No alert history available.",
                    styles["Normal"]
                )
            )

        pdf.build(content)
        buffer.seek(0)

        return buffer.getvalue()


    st.download_button(
        "📄 Download PDF Health Report",
        data=create_pdf_report(),
        file_name="windows_health_report.pdf",
        mime="application/pdf",
        width="stretch"
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Windows System Health Monitoring and Alert System "
    "using Python | Local system monitoring"
)
