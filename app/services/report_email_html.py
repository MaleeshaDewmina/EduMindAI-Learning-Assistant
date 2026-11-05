"""Responsive, safe HTML layout for EduMind AI progress reports."""
from html import escape
from urllib.parse import urlsplit


def tile(label, value):
    return f"""<td width="50%" style="padding:6px;"><table role="presentation" width="100%" style="background:#f3f5ff;border:1px solid #e4e8f5;border-radius:12px;"><tr><td style="padding:17px 15px 4px;color:#282c79;font:bold 27px Arial,sans-serif;">{int(value)}</td></tr><tr><td style="padding:0 15px 17px;color:#596781;font:12px Arial,sans-serif;">{escape(label)}</td></tr></table></td>"""


def report_email_html(student, report, recipient_role, public_url=""):
    lecturer = recipient_role == "lecturer"
    title = "Student learning progress" if lecturer else "Your learning progress"
    person = escape(str(student.full_name)) if lecturer else "you"
    percent = max(0.0, min(100.0, float(report["completion"])))
    filled = round(percent)
    base = (public_url or "").rstrip("/")
    parsed = urlsplit(base)
    url = None
    if parsed.scheme == "https" and parsed.netloc and not parsed.username and not parsed.password and parsed.path in ("", "/") and not parsed.query and not parsed.fragment:
        path = f"/lecturer/students/{int(student.user_id)}" if lecturer else "/progress/"
        url = base + path
    button = (
        f'<tr><td align="center" style="padding:16px;"><a href="{escape(url, quote=True)}" style="background:#5645dd;color:#ffffff;text-decoration:none;padding:14px 22px;border-radius:9px;font:bold 14px Arial,sans-serif;">View progress dashboard</a></td></tr>'
        if url else ""
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EduMind AI progress report</title></head>
<body style="background:#eef1fa;margin:0;padding:0;color:#1b2852;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:24px 10px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid #e4e8f4;">
<tr><td style="background:#292e79;padding:29px;color:#ffffff;font:bold 22px Arial,sans-serif;">&#10022; EduMind AI <span style="float:right;color:#b9f4e7;font:11px Arial,sans-serif;">PROGRESS REPORT</span></td></tr>
<tr><td style="padding:28px 29px 14px;">
<p style="color:#5645dd;font:bold 11px Arial,sans-serif;letter-spacing:1px;margin:0;">{"AUTHORISED LECTURER COPY" if lecturer else "PERSONAL LEARNING REPORT"}</p>
<h1 style="font:bold 27px/33px Arial,sans-serif;margin:10px 0;color:#192754;">{escape(title)}</h1>
<p style="color:#5d6982;font:14px/22px Arial,sans-serif;">A clear snapshot of study tasks and recent EduMind AI activity.</p>
<p style="color:#5d6982;font:13px Arial,sans-serif;">Student: <strong>{person}</strong></p>
</td></tr>
<tr><td style="padding:0 22px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr>{tile("Total study tasks", report["total"])}{tile("Completed", report["completed"])}</tr>
<tr>{tile("Pending", report["pending"])}{tile("Overdue", report["overdue"])}</tr>
</table></td></tr>
<tr><td style="padding:24px 29px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td style="font:bold 15px Arial,sans-serif;">Task completion</td><td align="right" style="font:bold 17px Arial,sans-serif;color:#5645dd;">{percent:.1f}%</td></tr>
<tr><td colspan="2" style="padding-top:10px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#e9ecf7;border-radius:6px;overflow:hidden;"><tr><td width="{filled}%" bgcolor="#5645dd" style="height:10px;font-size:1px;">&nbsp;</td><td width="{100-filled}%" style="height:10px;font-size:1px;">&nbsp;</td></tr></table></td></tr>
</table></td></tr>
<tr><td style="background:#f6f8fe;padding:26px 29px;border-top:1px solid #e8ebf6;">
<h2 style="font:bold 17px Arial,sans-serif;color:#212d69;margin:0 0 18px;">Activity in the last 7 days</h2>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td width="50%" style="font:bold 25px Arial,sans-serif;color:#292e79;">{int(report["activity_events"])}<div style="font:12px Arial,sans-serif;color:#5d6982;margin-top:6px;">Recorded events</div></td>
<td width="50%" style="font:bold 25px Arial,sans-serif;color:#292e79;">{int(report["active_days"])} / 7<div style="font:12px Arial,sans-serif;color:#5d6982;margin-top:6px;">Active days</div></td></tr></table>
<p style="border-top:1px solid #e5eaf5;padding-top:15px;margin:20px 0 0;color:#53637d;font:13px Arial,sans-serif;">Behavioural activity indicator: <strong>{float(report["indicator"]):.1f}%</strong></p>
</td></tr>{button}
<tr><td style="padding:22px 29px;color:#65738b;font:12px/19px Arial,sans-serif;">The indicator reflects recorded application activity, not a validated psychological measure or a grade. Chat history, uploads, questionnaire answers and private comments are excluded.</td></tr>
<tr><td align="center" style="background:#f1f3fa;padding:18px;color:#68748e;font:12px Arial,sans-serif;">EduMind AI &middot; Learn with intention.<div style="margin-top:6px;font-size:11px;">Requested from your learning account.</div></td></tr>
</table></td></tr></table></body></html>"""