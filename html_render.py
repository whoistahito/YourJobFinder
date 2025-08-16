import datetime
import random

# Design tokens (aligned with app theme)
BRAND_PRIMARY = "#6366f1"  # brand-500
BRAND_PRIMARY_DARK = "#4f46e5"  # brand-600
DARK_TEXT = "#111827"
SUBTEXT = "#4b5563"
SOFT_BG = "#f5f4f8"  # site soft-ui background
CARD_BG = "#ffffff"
BORDER = "#e2e8f0"
DOT_COLOR = "#d4d4dd"

# Small 6x6 dot grid png (1px dot) base64 to mimic site subtle dot pattern (safe fallback: background-color only)
DOT_GRID_DATA_URI = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFklEQVQoU2NkYGD4z0AEYBxVSFUBAQB1TgmdOQk2kQAAAABJRU5ErkJggg=="
)

# Friendly dynamic greetings (kept minimal emoji for deliverability)
greetings = [
    "Here are some curated roles we found for you today.",
    "Fresh matches just in – take a quick scan.",
    "A focused batch of potential fits for your criteria.",
    "Today’s refined set of opportunities for you.",
    "Your monitored roles update has arrived.",
]


def get_welcome_message():
    """Welcome email (sent immediately after user creates first alert).
    Refactored to align with on-site soft glass aesthetic.
    Adjusted copy: focuses on expectation setting (no extra alert CTA).
    """
    return f"""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <meta name="color-scheme" content="light dark" />
  <meta name="supported-color-schemes" content="light dark" />
  <title>Welcome – Your Job Finder</title>
  <!--[if mso]><style type="text/css">body, table, td {{font-family: Arial, Helvetica, sans-serif !important;}}</style><![endif]-->
  <style>
    :root {{ color-scheme: light dark; supported-color-schemes: light dark; }}
    body {{ margin:0; padding:0; background:{SOFT_BG}; -webkit-font-smoothing:antialiased; }}
    .outer {{ background:{SOFT_BG}; }}
    .card {{ background:{CARD_BG}; border-radius:24px; box-shadow:0 4px 18px -4px rgba(0,0,0,0.08),0 2px 4px -1px rgba(0,0,0,0.06); }}
    .hero-bg {{ background:{CARD_BG}; background-image: radial-gradient(circle at 25% 20%, {BRAND_PRIMARY}1F, transparent 65%), radial-gradient(circle at 85% 70%, #38bdf81e, transparent 70%); }}
    .pill {{ display:inline-block; background:{DARK_TEXT}; color:#fff !important; font-size:11px; letter-spacing:1px; text-transform:uppercase; font-weight:600; padding:6px 14px; border-radius:999px; text-decoration:none; }}
    .section-h2 {{ margin:0 0 18px 0; font-size:16px; line-height:1.35; font-weight:600; color:{DARK_TEXT}; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif; }}
    .list-bullet td {{ font-size:13px; line-height:1.5; color:{SUBTEXT}; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif; padding:0 0 10px 0; }}
    @media (prefers-color-scheme: dark) {{
      body, .outer {{ background:#0f1115 !important; }}
      .card {{ background:#1c1f26 !important; box-shadow:0 0 0 1px #252a33 inset !important; }}
      .hero-bg {{ background:#1c1f26 !important; background-image:radial-gradient(circle at 25% 20%, {BRAND_PRIMARY_DARK}33, transparent 65%), radial-gradient(circle at 85% 70%, #38bdf833, transparent 70%) !important; }}
      h1,h2,h3 {{ color:#f1f5f9 !important; }}
      p, .muted, .list-bullet td {{ color:#cbd5e1 !important; }}
      .pill {{ background:{BRAND_PRIMARY_DARK} !important; }}
    }}
  </style>
</head>
<body>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="outer">
    <tr>
      <td align="center" style="padding:36px 14px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:640px;" class="card">
          <!-- Hero -->
          <tr>
            <td class="hero-bg" style="padding:54px 44px 46px 44px; border-radius:24px 24px 0 0;">
              <span class="pill">Welcome</span>
              <h1 style="margin:26px 0 14px 0; font-size:34px; line-height:1.05; font-weight:700; letter-spacing:-0.5px; color:{DARK_TEXT}; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">Monitoring started</h1>
              <p style="margin:0; font-size:16px; line-height:1.55; max-width:520px; color:{SUBTEXT}; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">Your alert is active. We continuously scan credible sources and surface only roles that closely fit what you entered—at most one concise email on days a real match exists.</p>
            </td>
          </tr>
          <!-- What we track -->
          <tr>
            <td style="padding:40px 44px 4px 44px;">
              <h2 class="section-h2">What drives your matches</h2>
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="list-bullet">
                <tr><td>• Role focus & related titles</td></tr>
                <tr><td>• Job type preference</td></tr>
                <tr><td>• Location / remote setting</td></tr>
                <tr><td>• Posting recency & basic quality filters</td></tr>
              </table>
              <p style="margin:8px 0 0 0; font-size:12px; line-height:1.5; color:#6b7280; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">Duplicates, expired and obvious low‑quality listings are removed upstream.</p>
            </td>
          </tr>
          <!-- What happens next -->
          <tr>
            <td style="padding:34px 44px 4px 44px;">
              <h2 class="section-h2">What to expect</h2>
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="list-bullet">
                <tr><td>• First relevant batch often within 24 hours (no email if nothing fits)</td></tr>
                <tr><td>• Each message: a small set of high‑fit roles only</td></tr>
                <tr><td>• Frequency naturally adapts—quiet when market is quiet</td></tr>
              </table>
            </td>
          </tr>
          <!-- Control -->
          <tr>
            <td style="padding:34px 44px 6px 44px;">
              <h2 class="section-h2">Your control</h2>
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="list-bullet">
                <tr><td>• Create an additional alert later to compare broader or narrower scope</td></tr>
                <tr><td>• One‑click unsubscribe link in every email</td></tr>
                <tr><td>• Reply paths are disabled—reach us via the site contact page</td></tr>
              </table>
              <p style="margin:10px 0 0 0; font-size:13px; line-height:1.55; color:{SUBTEXT}; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">Tip: Keep role wording specific. Add a second alert later if you also want a broader sweep.</p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding:42px 32px 48px 32px; border-top:1px solid {BORDER};">
              <p style="margin:0 0 8px 0; font-size:12px; line-height:1.5; color:#6b7280; text-align:center; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">© 2025 Your Job Finder • Educational project</p>
              <p style="margin:0; font-size:11px; line-height:1.5; color:#94a3b8; text-align:center; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">You’re receiving this because you created an alert. Adjust or unsubscribe any time.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def create_job_card(row):
    """Creates an individual job card (table block) aligned with theme.

    Expected keys in row: title, company, location, date_posted, is_remote, job_url, new_badge (optional)
    """
    if isinstance(row['date_posted'], datetime.date):
        posted_date = row['date_posted'].strftime("%b %d, %Y")
    else:
        posted_date = 'This Week'

    new_badge = ''
    if row.get('new_badge', False):
        new_badge = (
            f'<span style="display:inline-block;background:#ecfdf5;color:#065f46;font-size:11px;font-weight:600;line-height:1;padding:6px 10px;border-radius:999px;">NEW</span>'
        )

    remote_badge = ''
    if row.get('is_remote'):
        remote_badge = (
            f'<span style="display:inline-block;background:#eef2ff;color:{BRAND_PRIMARY_DARK};font-size:11px;font-weight:500;line-height:1;padding:6px 10px;border-radius:999px;margin-left:6px;">Remote</span>'
        )

    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:0 0 18px 0; border-collapse:separate;">
      <tr>
        <td style="background:#ffffff;border:1px solid {BORDER};border-radius:18px;padding:20px 22px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;vertical-align:top;">
                <h3 style="margin:0 0 6px 0;font-size:17px;line-height:1.35;color:{DARK_TEXT};font-weight:600;">{row['title']}</h3>
                <p style="margin:0 0 6px 0;font-size:14px;line-height:1.4;color:{SUBTEXT};font-weight:500;">{row['company']}</p>
                <p style="margin:0 0 12px 0;font-size:13px;line-height:1.55;color:#6b7280;">📍 {row['location']}<br />🕒 Posted: {posted_date}</p>
                <div style="margin:0 0 14px 0;">{new_badge}{remote_badge}</div>
                <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td bgcolor="{BRAND_PRIMARY_DARK}" style="border-radius:999px;">
                      <a href="{row['job_url']}" style="display:inline-block;padding:11px 20px;font-size:14px;font-weight:600;color:#ffffff;text-decoration:none;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">View Details ↗</a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
    '''


def get_html_template(html_content, email, position, location):
    """Nightly / daily batch email containing job cards.

    Args:
        html_content: Concatenated job card HTML blocks.
        email: Recipient email.
        position: Target position string.
        location: Target location string.
    """
    unsubscribe_url = "https://yourjobfinder.website/unsubscribe/process"
    return f'''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <meta name="color-scheme" content="light dark" />
  <meta name="supported-color-schemes" content="light dark" />
  <title>Your Job Matches</title>
  <!--[if mso]><style type="text/css">body, table, td {{font-family: Arial, Helvetica, sans-serif !important;}}</style><![endif]-->
  <style>
    :root {{ color-scheme: light dark; supported-color-schemes: light dark; }}
    body {{ margin:0; padding:0; background:{SOFT_BG}; -webkit-font-smoothing:antialiased; }}
    .outer {{ background:{SOFT_BG}; }}
    .card {{ background:{CARD_BG}; border-radius:28px; box-shadow:0 8px 28px -8px rgba(0,0,0,0.08); }}
    .header {{ background:{CARD_BG}; background-image:radial-gradient(circle at 25% 22%, {BRAND_PRIMARY}22, transparent 65%), radial-gradient(circle at 80% 70%, #38bdf81e, transparent 70%); }}
    .badge {{ display:inline-block; background:{DARK_TEXT}; color:#fff !important; font-size:11px; letter-spacing:1px; text-transform:uppercase; font-weight:600; padding:6px 14px; border-radius:999px; }}
    .tips {{ background:#ffffff; border:1px solid {BORDER}; border-radius:18px; }}
    a {{ color:{BRAND_PRIMARY_DARK}; }}
    @media (prefers-color-scheme: dark) {{
      body, .outer {{ background:#0f1115 !important; }}
      .card {{ background:#1c1f26 !important; box-shadow:0 0 0 1px #252a33 inset !important; }}
      .header {{ background:#1c1f26 !important; background-image:radial-gradient(circle at 25% 22%, {BRAND_PRIMARY_DARK}40, transparent 65%), radial-gradient(circle at 80% 70%, #38bdf845, transparent 70%) !important; }}
      h1,h2,h3 {{ color:#f1f5f9 !important; }}
      p, .muted {{ color:#cbd5e1 !important; }}
      .tips {{ background:#242a33 !important; border-color:#334155 !important; }}
      a {{ color:{BRAND_PRIMARY} !important; }}
    }}
  </style>
</head>
<body>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="outer">
    <tr>
      <td align="center" style="padding:34px 14px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:640px;" class="card">
          <!-- Header -->
          <tr>
            <td class="header" style="padding:46px 46px 42px 46px; border-radius:28px 28px 0 0;">
              <span class="badge">Daily Batch</span>
              <h1 style="margin:26px 0 12px 0; font-size:28px; line-height:1.2; font-weight:700; letter-spacing:-0.5px; color:#111827; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">Curated Matches</h1>
              <p style="margin:0; font-size:15px; line-height:1.55; max-width:420px; font-weight:500; color:{SUBTEXT}; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">Focused roles for <span style="color:{DARK_TEXT};">{position or 'your role'}</span>{(' · ' + location) if location else ''}</p>
            </td>
          </tr>
          <!-- Intro -->
          <tr>
            <td style="padding:32px 46px 12px 46px;">
              <p style="margin:0 0 24px 0; font-size:15px; line-height:1.55; color:{SUBTEXT}; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">{random.choice(greetings)}</p>
            </td>
          </tr>
          <!-- Job Cards -->
          <tr>
            <td style="padding:0 46px 4px 46px;">{html_content}</td>
          </tr>
          <!-- Tips -->
            <tr>
              <td style="padding:10px 46px 40px 46px;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="tips">
                  <tr>
                    <td style="padding:18px 22px;">
                      <p style="margin:0 0 6px 0; font-size:13px; line-height:1.5; font-weight:600; color:{DARK_TEXT}; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">Why you got these</p>
                      <p style="margin:0; font-size:12px; line-height:1.55; color:#6b7280; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">Matched on role semantics, location / remoteness, recency & source quality. Tune further by creating an additional alert with narrower scope.</p>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          <!-- Footer inside card -->
          <tr>
            <td style="padding:34px 32px 46px 32px; border-top:1px solid {BORDER};">
              <p style="margin:0 0 14px 0; font-size:13px; line-height:1.55; color:#6b7280; text-align:center; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">Prefer fewer emails? Create a second alert tuned differently and compare signal.</p>
              <p style="margin:0 0 16px 0; font-size:12px; line-height:1.5; color:#94a3b8; text-align:center; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">Sent to {email}. If this is incorrect, adjust by making a new alert.</p>
              <p style="margin:0; font-size:12px; line-height:1.5; color:#94a3b8; text-align:center; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
                <a href="{unsubscribe_url}?email={email}&position={position}&location={location}" style="color:{BRAND_PRIMARY_DARK}; text-decoration:none; font-weight:600;">Unsubscribe</a>
                <span style="color:#cbd5e1;"> • </span>
                <a href="https://yourjobfinder.website/terms" style="color:{BRAND_PRIMARY_DARK}; text-decoration:none; font-weight:600;">Terms</a>
                <span style="color:#cbd5e1;"> • </span>
                <a href="https://yourjobfinder.website/contact" style="color:{BRAND_PRIMARY_DARK}; text-decoration:none; font-weight:600;">Contact</a>
              </p>
            </td>
          </tr>
        </table>
        <!-- Legal line -->
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:640px;">
          <tr>
            <td align="center" style="padding:20px 8px 12px 8px;">
              <p style="margin:0; font-size:11px; line-height:1.5; color:#94a3b8; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">© 2025 Your Job Finder. Educational project – do not reply.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
    '''