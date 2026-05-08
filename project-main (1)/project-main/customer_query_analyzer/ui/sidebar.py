import io
import os
import streamlit as st
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER


def latency_stats() -> dict:
    lats = st.session_state.latencies
    if not lats:
        return None
    return {
        "avg": round(sum(lats) / len(lats)),
        "min": min(lats),
        "max": max(lats),
    }


def build_pdf() -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    story  = []

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Normal"],
        fontSize=16,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0058A3"),
        spaceAfter=4,
    )
    sub_style = ParagraphStyle(
        "ReportSub",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica",
        textColor=colors.HexColor("#99A0AA"),
        spaceAfter=8,
    )
    sec_hdr_style = ParagraphStyle(
        "SecHdr",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#333333"),
        spaceAfter=5,
    )

    story.append(Paragraph("Customer Query Analyzer — Session Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#D8E3EC")))
    story.append(Spacer(1, 6 * mm))

    # ── Session Summary ──────────────────────────────────────────────────────
    story.append(Paragraph("SESSION SUMMARY", sec_hdr_style))

    total = st.session_state.total_queries
    neg   = st.session_state.sentiment_counts["negative"]
    neu   = st.session_state.sentiment_counts["neutral"]
    pos   = st.session_state.sentiment_counts["positive"]
    sec   = st.session_state.security_count
    low   = st.session_state.lowconf_count
    ls    = latency_stats()

    summary_rows = [
        ["Total Queries",        str(total), "Security Alerts", str(sec)],
        ["Session Sentiment",    "",         "Low Confidence",  str(low)],
        ["  Negative",           str(neg),   "",                ""],
        ["  Neutral",            str(neu),   "",                ""],
        ["  Positive",           str(pos),   "",                ""],
    ]
    if ls:
        summary_rows += [
            ["Avg Latency", f"{ls['avg']} ms", "Min Latency", f"{ls['min']} ms"],
            ["Max Latency", f"{ls['max']} ms", "",            ""],
        ]

    cw = [60 * mm, 30 * mm, 60 * mm, 30 * mm]
    summary_tbl = Table(summary_rows, colWidths=cw)
    summary_tbl.setStyle(TableStyle([
        ("FONTNAME",   (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",   (2, 0), (2, -1), "Helvetica-Bold"),
        ("TEXTCOLOR",  (0, 0), (0, -1), colors.HexColor("#555566")),
        ("TEXTCOLOR",  (2, 0), (2, -1), colors.HexColor("#555566")),
        ("TEXTCOLOR",  (1, 0), (1,  0), colors.HexColor("#0058A3")),
        ("TEXTCOLOR",  (1, 2), (1,  2), colors.HexColor("#CC2200")),
        ("TEXTCOLOR",  (1, 3), (1,  3), colors.HexColor("#666677")),
        ("TEXTCOLOR",  (1, 4), (1,  4), colors.HexColor("#1A7A2A")),
        ("TEXTCOLOR",  (3, 0), (3,  0), colors.HexColor("#CC2200")),
        ("TEXTCOLOR",  (3, 1), (3,  1), colors.HexColor("#A06000")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#E8EEF5")),
        ("PADDING",    (0, 0), (-1, -1), 4),
    ]))
    story.append(summary_tbl)
    story.append(Spacer(1, 7 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#D8E3EC")))
    story.append(Spacer(1, 5 * mm))

    # ── Query History ────────────────────────────────────────────────────────
    story.append(Paragraph("QUERY HISTORY", sec_hdr_style))
    story.append(Spacer(1, 2 * mm))

    headers = ["#", "Time", "Query", "Intent", "Conf.", "Sentiment", "Status", "Latency", "Feedback"]
    table_rows = [headers]
    for i, entry in enumerate(st.session_state.history_log, 1):
        table_rows.append([
            str(i),
            entry.get("Time",       ""),
            entry.get("Query",      ""),
            entry.get("Intent",     ""),
            entry.get("Confidence", ""),
            entry.get("Sentiment",  ""),
            entry.get("Status",     ""),
            entry.get("Latency",    ""),
            entry.get("Feedback",   ""),
        ])

    # landscape A4 usable width ≈ 267 mm
    hist_col_widths = [10*mm, 22*mm, 72*mm, 52*mm, 15*mm, 22*mm, 18*mm, 20*mm, 18*mm]
    hist_tbl = Table(table_rows, colWidths=hist_col_widths, repeatRows=1)

    ts = [
        ("FONTNAME",        (0, 0), (-1,  0), "Helvetica-Bold"),
        ("FONTSIZE",        (0, 0), (-1, -1), 8),
        ("BACKGROUND",      (0, 0), (-1,  0), colors.HexColor("#0058A3")),
        ("TEXTCOLOR",       (0, 0), (-1,  0), colors.white),
        ("ALIGN",           (0, 0), ( 0, -1), "CENTER"),
        ("ALIGN",           (4, 0), ( 4, -1), "CENTER"),
        ("ROWBACKGROUNDS",  (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
        ("GRID",            (0, 0), (-1, -1), 0.5, colors.HexColor("#D8E3EC")),
        ("PADDING",         (0, 0), (-1, -1), 4),
        ("VALIGN",          (0, 0), (-1, -1), "TOP"),
    ]
    for i, entry in enumerate(st.session_state.history_log, 1):
        sent = entry.get("Sentiment", "")
        if sent == "Negative":
            ts += [("TEXTCOLOR", (5, i), (5, i), colors.HexColor("#CC2200")),
                   ("FONTNAME",  (5, i), (5, i), "Helvetica-Bold")]
        elif sent == "Positive":
            ts += [("TEXTCOLOR", (5, i), (5, i), colors.HexColor("#1A7A2A")),
                   ("FONTNAME",  (5, i), (5, i), "Helvetica-Bold")]

    hist_tbl.setStyle(TableStyle(ts))
    story.append(hist_tbl)

    doc.build(story)
    return buffer.getvalue()


def render_sidebar(_defaults: dict) -> str:
    """
    Renders the full sidebar.
    Returns the API key entered by the user (or loaded from secrets).
    """
    with st.sidebar:
        user_email = st.session_state.get("user", {}).get("email", "")
        st.markdown(
            f"""
            <div style='padding:6px 0 12px 0; border-bottom:1px solid #C0CDD8; margin-bottom:2px;'>
                <div style='font-size:0.95rem;font-weight:700;color:#333333;font-family:Oswald,sans-serif;letter-spacing:0.5px;'>QUERY ANALYZER</div>
                <div style='font-size:0.62rem;color:#99A0AA;margin-top:2px;font-family:Roboto Mono,monospace;'>BERT + GROQ ENGINE</div>
                <div style='font-size:0.65rem;color:#1A7A2A;margin-top:6px;font-family:Roboto Mono,monospace;
                            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:190px;'
                     title='{user_email}'>
                    ✓ {user_email}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("⎋ Sign Out", use_container_width=True, key="_signout"):
            st.session_state.user = None
            st.rerun()

        st.markdown(
            "<div style='height:1px;background:#D8E3EC;margin:10px 0;'></div>",
            unsafe_allow_html=True,
        )

        # ── API Key ──────────────────────────────────────
        st.markdown("<div class='sb-sec'>▸ API KEY (GROQ)</div>", unsafe_allow_html=True)

        api_key   = ""
        _on_cloud = (
            os.environ.get("STREAMLIT_SHARING_MODE") or
            os.path.exists("/mount/src")
        )

        if _on_cloud:
            try:
                api_key = st.secrets["GROQ_API_KEY"]
                st.markdown(
                    "<div style='font-size:0.69rem;color:#1A7A2A;margin-bottom:8px;font-family:Roboto Mono,monospace;'>"
                    "✓ KEY LOADED FROM SECRETS</div>",
                    unsafe_allow_html=True,
                )
            except Exception:
                api_key = ""

        if not api_key:
            api_key = st.text_input(
                "api_key_input",
                label_visibility="collapsed",
                type="password",
                placeholder="Paste your Groq API key...",
            )
            if api_key:
                masked = (
                    api_key[:4] + "x" * min(len(api_key) - 8, 10) + api_key[-4:]
                    if len(api_key) > 8
                    else "x" * len(api_key)
                )
                st.markdown(
                    f"<div style='font-size:0.69rem;color:#1A7A2A;margin:-2px 0 6px 0;font-family:Roboto Mono,monospace;'>"
                    f"✓ KEY SET: {masked}</div>",
                    unsafe_allow_html=True,
                )

        st.markdown(
            "<div style='font-size:0.68rem;color:#99A0AA;margin:4px 0 8px 0;font-family:Roboto Mono,monospace;'>"
            "FREE · <a href='https://console.groq.com' style='color:#0058A3;text-decoration:none;'>"
            "CONSOLE.GROQ.COM</a></div>",
            unsafe_allow_html=True,
        )

        # ── Session Stats ────────────────────────────────
        st.markdown(
            "<div style='height:1px;background:#D8E3EC;margin:10px 0;'></div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='sb-sec'>▸ SESSION STATS</div>", unsafe_allow_html=True)

        total = st.session_state.total_queries
        neg   = st.session_state.sentiment_counts["negative"]
        neu   = st.session_state.sentiment_counts["neutral"]
        pos   = st.session_state.sentiment_counts["positive"]
        sec   = st.session_state.security_count
        low   = st.session_state.lowconf_count
        ls    = latency_stats()

        rows = [
            ("TOTAL QUERIES",   str(total), "#0058A3"),
            ("NEGATIVE",        str(neg),   "#CC2200"),
            ("NEUTRAL",         str(neu),   "#666677"),
            ("POSITIVE",        str(pos),   "#1A7A2A"),
            ("SECURITY ALERTS", str(sec),   "#CC2200"),
            ("LOW CONFIDENCE",  str(low),   "#A06000"),
        ]
        if ls:
            rows += [
                ("AVG LATENCY", f"{ls['avg']} ms", "#0058A3"),
                ("MIN LATENCY", f"{ls['min']} ms", "#1A7A2A"),
                ("MAX LATENCY", f"{ls['max']} ms", "#CC2200"),
            ]

        for label, val, color in rows:
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;"
                f"font-size:0.76rem;padding:4px 0;border-bottom:1px solid #EEF3FA;font-family:Roboto Mono,monospace;'>"
                f"<span style='color:#99A0AA;'>{label}</span>"
                f"<span style='font-weight:700;color:{color};'>{val}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # ── Download + Clear ─────────────────────────────
        st.markdown(
            "<div style='height:1px;background:#D8E3EC;margin:12px 0;'></div>",
            unsafe_allow_html=True,
        )

        if st.session_state.history_log:
            pdf_data = build_pdf()
            st.download_button(
                label="⬇ Download History (PDF)",
                data=pdf_data,
                file_name=f"queries_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

        if st.button("✕ Clear Conversation", use_container_width=True):
            for k, v in _defaults.items():
                if isinstance(v, dict):   st.session_state[k] = v.copy()
                elif isinstance(v, list): st.session_state[k] = []
                else:                     st.session_state[k] = v
            st.rerun()

    return api_key
