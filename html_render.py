import datetime
import random

greetings = [
    "Here are some exciting job opportunities we found for you! 🚀",
    "Great news! Check out these potential job matches for you! 🎉",
    "We’ve found some jobs that might interest you. Take a look! 👀",
    "Explore these job openings tailored for you! 🔍",
    "Here's a list of jobs that could be your next big opportunity! 🌟",
    "These jobs caught our attention. We hope they pique yours too! 📌",
    "Discover these job possibilities that align with your criteria! 📈",
    "Look at the career opportunities we’ve gathered for you! 🗂️",
    "Unlock your potential with these job listings we found! 🔑",
    "We’ve curated these job options just for you. Happy exploring! 😊"
]


def get_welcome_message():
    return """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <meta name="color-scheme" content="light dark" />
  <meta name="supported-color-schemes" content="light dark" />
  <title>Welcome to Your Job Finder</title>
  <!--[if mso]>
  <style type="text/css">body, table, td {font-family: Arial, Helvetica, sans-serif !important;}</style>
  <![endif]-->
  <style>
    :root { color-scheme: light dark; supported-color-schemes: light dark; }
    @media (prefers-color-scheme: dark) {
      body, .email-outer { background:#0f1115 !important; }
      .email-card { background:#1c1f26 !important; box-shadow:0 0 0 1px #262b33 inset !important; }
      .email-header { background:linear-gradient(135deg,#312e81,#4338ca,#6366f1) !important; }
      .email-card h1, .email-card h2, .email-card h3 { color:#f1f5f9 !important; }
      .email-card p, .email-text { color:#cbd5e1 !important; }
      .job-card { background:#242a33 !important; border-color:#334155 !important; }
      .badge-light { background:#334155 !important; color:#e2e8f0 !important; }
      .btn-primary { background:#6366f1 !important; color:#ffffff !important; }
      .tips-box { background:#1e2530 !important; border-color:#334155 !important; }
      a { color:#818cf8 !important; }
      .footer-line { color:#64748b !important; }
    }
  </style>
</head>
<body class="email-body" style="margin:0;padding:0;background-color:#F3F4F6;-webkit-font-smoothing:antialiased;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" class="email-outer" style="background:#f3f4f6;">
    <tr>
      <td align="center" style="padding:32px 12px;">
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" class="email-card" style="max-width:640px;background:#ffffff;border-radius:20px;overflow:hidden;box-shadow:0 8px 28px -6px rgba(0,0,0,0.08);">
          <!-- Hero -->
          <tr>
            <td class="email-header" style="background:linear-gradient(135deg,#ffffff 0%,#eef2ff 60%,#e0f7ff 100%);padding:52px 40px 40px 40px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td align="left" style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
                    <div style="display:inline-block;background:#111827;color:#ffffff;font-size:11px;letter-spacing:1px;text-transform:uppercase;font-weight:600;padding:6px 14px;border-radius:999px;">Welcome</div>
                    <h1 style="margin:24px 0 14px 0;font-size:32px;line-height:1.15;font-weight:700;color:#111827;letter-spacing:-0.5px;">Your Job <span style="color:#4F46E5;">Finder</span> Starts Now</h1>
                    <p style="margin:0;font-size:16px;line-height:1.55;color:#4B5563;max-width:520px;">We scan fresh listings daily and send you a focused, noise‑free batch that matches what you told us. No dashboards to babysit. Just high‑fit leads in your inbox.</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <!-- Criteria Summary -->
          <tr>
            <td style="padding:40px 40px 8px 40px;">
              <h2 style="margin:0 0 20px 0;font-size:20px;line-height:1.3;color:#111827;font-weight:600;">What We'll Use To Match Roles</h2>
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td valign="top" width="50%" style="padding:0 16px 24px 0;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td style="font-size:24px;line-height:1;padding-right:12px;">💼</td>
                        <td style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;font-size:14px;color:#374151;font-weight:500;">Role Focus</td>
                      </tr>
                    </table>
                  </td>
                  <td valign="top" width="50%" style="padding:0 0 24px 16px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td style="font-size:24px;line-height:1;padding-right:12px;">⭐</td>
                        <td style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;font-size:14px;color:#374151;font-weight:500;">Job Type</td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <tr>
                  <td valign="top" width="50%" style="padding:0 16px 24px 0;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td style="font-size:24px;line-height:1;padding-right:12px;">📍</td>
                        <td style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;font-size:14px;color:#374151;font-weight:500;">Location / Remote</td>
                      </tr>
                    </table>
                  </td>
                  <td valign="top" width="50%" style="padding:0 0 24px 16px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td style="font-size:24px;line-height:1;padding-right:12px;">⏱️</td>
                        <td style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;font-size:14px;color:#374151;font-weight:500;">Freshness Window</td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
              <p style="margin:4px 0 0 0;font-size:12px;line-height:1.5;color:#6B7280;">We ignore obvious duplicates, expired listings and low quality scraps.</p>
            </td>
          </tr>
          <!-- CTA -->
          <tr>
            <td align="center" style="padding:40px 40px 8px 40px;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td class="btn-primary" bgcolor="#4F46E5" style="border-radius:999px;">
                    <a href="https://yourjobfinder.website" target="_blank" style="display:inline-block;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;padding:14px 30px;">Create Another Alert →</a>
                  </td>
                </tr>
              </table>
              <p style="margin:28px 0 0 0;font-size:14px;line-height:1.5;color:#4B5563;max-width:520px;">First tailored batch hits your inbox within 24h. You can pause or unsubscribe any time—no questions.</p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding:40px 28px 48px 28px;border-top:1px solid #E5E7EB;">
              <p class="footer-line" style="margin:0 0 8px 0;font-size:12px;line-height:1.5;color:#6B7280;text-align:center;">© 2025 Your Job Finder • Educational project</p>
              <p class="footer-line" style="margin:0;font-size:11px;line-height:1.5;color:#9CA3AF;text-align:center;">You’re receiving this because you created an alert.</p>
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
    """
    Creates an HTML job card from a pandas DataFrame row.

    Expected columns in row:
    - title: str
    - company: str
    - location: str
    - date_posted: datetime or str
    - is_remote: bool
    - job_url: str
    - new_badge: bool (optional)
    """
    # Convert date to proper format if it's a string or datetime
    if isinstance(row['date_posted'], datetime.date):
        posted_date = row['date_posted'].strftime("%b %d, %Y")
    else:
        posted_date = 'This Week'

    # New badge HTML - only show if is_new is True
    new_badge = ''
    if row.get('new_badge', False):
        new_badge = ('<span class="badge-light" style="display:inline-block;background:#DCFCE7;color:#166534;font-size:11px;'
                     'font-weight:600;line-height:1;padding:6px 12px;border-radius:999px;">NEW</span>')

    # Remote badge - only show if remote is True
    remote_badge = ''
    if row['is_remote']:
        remote_badge = ('<span class="badge-light" style="display:inline-block;background:#EEF2FF;color:#4F46E5;font-size:11px;'
                         'font-weight:500;line-height:1;padding:6px 12px;border-radius:999px;margin-left:8px;">Remote</span>')

    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:0 0 20px 0;border-collapse:separate;">
      <tr>
        <td class="job-card" style="background:#F8FAFF;border:1px solid #E5E7EB;border-radius:16px;padding:20px 22px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;vertical-align:top;">
                <h3 style="margin:0 0 8px 0;font-size:17px;line-height:1.35;color:#1F2937;font-weight:600;">{row['title']}</h3>
                <p style="margin:0 0 6px 0;font-size:14px;line-height:1.4;color:#374151;font-weight:500;">{row['company']}</p>
                <p style="margin:0 0 12px 0;font-size:13px;line-height:1.5;color:#6B7280;">📍 {row['location']}<br />🕒 Posted: {posted_date}</p>
                <div style="margin:0 0 16px 0;">{new_badge}{remote_badge}</div>
                <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td class="btn-primary" bgcolor="#4F46E5" style="border-radius:10px;">
                      <a href="{row['job_url']}" style="display:inline-block;padding:12px 20px;font-size:14px;font-weight:600;color:#ffffff;text-decoration:none;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">View Details →</a>
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
    """
    Creates the complete HTML email template with the job cards content.

    Args:
        html_content (str): The concatenated job cards HTML
        email (str): The recipient's username/email
        position (str) : preferred job position
        location (str) : preferred job location
    Returns:
        str: Complete HTML email template
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
    @media (prefers-color-scheme: dark) {{{{
      body, .email-outer {{ background:#0f1115 !important; }}
      .email-card {{ background:#1c1f26 !important; box-shadow:0 0 0 1px #262b33 inset !important; }}
      .email-header {{ background:linear-gradient(125deg,#312e81,#4338ca,#6366f1) !important; }}
      .email-card h1, .email-card h2, .email-card h3 {{ color:#f1f5f9 !important; }}
      .email-card p, .email-text {{ color:#cbd5e1 !important; }}
      .job-card {{ background:#242a33 !important; border-color:#334155 !important; }}
      .badge-light {{ background:#334155 !important; color:#e2e8f0 !important; }}
      .btn-primary {{ background:#6366f1 !important; color:#ffffff !important; }}
      .tips-box {{ background:#1e2530 !important; border-color:#334155 !important; }}
      a {{ color:#818cf8 !important; }}
      .footer-line {{ color:#64748b !important; }}
    }}}}
  </style>
</head>
<body class="email-body" style="margin:0;padding:0;background-color:#F3F4F6;-webkit-font-smoothing:antialiased;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="email-outer" style="background:#F3F4F6;">
    <tr>
      <td align="center" style="padding:32px 12px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="email-card" style="max-width:640px;background:#ffffff;border-radius:24px;overflow:hidden;box-shadow:0 8px 28px -8px rgba(0,0,0,0.1);">
          <!-- Header -->
          <tr>
            <td class="email-header" style="background:linear-gradient(125deg,#4F46E5 0%,#6366F1 60%,#60A5FA 115%);padding:44px 40px 46px 40px;">
              <h1 style="margin:0;font-size:26px;line-height:1.2;font-weight:700;color:#ffffff;letter-spacing:-0.5px;">Your Curated Matches</h1>
              <p style="margin:14px 0 0 0;font-size:15px;line-height:1.5;color:#E0E7FF;max-width:420px;font-weight:500;">Fresh roles filtered for <span style="color:#ffffff;">{position or 'your role'}</span> {(' · ' + location) if location else ''}</p>
              <p style="margin:10px 0 0 0;font-size:12px;letter-spacing:0.5px;text-transform:uppercase;color:rgba(255,255,255,0.75);font-weight:600;">Daily Batch</p>
            </td>
          </tr>
          <!-- Intro -->
          <tr>
            <td style="padding:32px 40px 8px 40px;">
              <p class="email-text" style="margin:0 0 24px 0;font-size:15px;line-height:1.55;color:#4B5563;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">{random.choice(greetings)}</p>
            </td>
          </tr>
          <!-- Job Cards -->
          <tr>
            <td style="padding:0 40px 8px 40px;">{html_content}</td>
          </tr>
          <!-- Tips -->
          <tr>
            <td style="padding:8px 40px 32px 40px;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" class="tips-box" style="background:#F8FAFF;border:1px solid #E5E7EB;border-radius:16px;">
                <tr>
                  <td style="padding:18px 22px;">
                    <p style="margin:0 0 8px 0;font-size:13px;line-height:1.5;color:#374151;font-weight:600;">Why you got these</p>
                    <p style="margin:0;font-size:12px;line-height:1.55;color:#6B7280;">Matched on: role keywords, location/remoteness, recency & basic quality filters. Improve accuracy by narrowing your criteria or creating a second alert.</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding:32px 28px 44px 28px;border-top:1px solid #E5E7EB;">
              <p class="footer-line" style="margin:0 0 16px 0;font-size:13px;line-height:1.55;color:#6B7280;text-align:center;">Prefer fewer emails? Create a second alert tuned differently and compare signal.</p>
              <p class="footer-line" style="margin:0 0 18px 0;font-size:12px;line-height:1.5;color:#9CA3AF;text-align:center;">This was sent to {email}. If this looks wrong you can adjust by making a new alert.</p>
              <p class="footer-line" style="margin:0;font-size:12px;line-height:1.5;color:#9CA3AF;text-align:center;">
                <a href="{unsubscribe_url}?email={email}&position={position}&location={location}" style="color:#4F46E5;text-decoration:none;font-weight:600;">Unsubscribe</a>
                <span style="color:#D1D5DB;"> • </span>
                <a href="https://yourjobfinder.website/terms" style="color:#4F46E5;text-decoration:none;font-weight:600;">Terms</a>
                <span style="color:#D1D5DB;"> • </span>
                <a href="https://yourjobfinder.website/contact" style="color:#4F46E5;text-decoration:none;font-weight:600;">Contact</a>
              </p>
            </td>
          </tr>
        </table>
        <!-- Legal Line -->
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width:640px;">
          <tr>
            <td style="padding:20px 8px 10px 8px;" align="center">
              <p class="footer-line" style="margin:0;font-size:11px;line-height:1.5;color:#9CA3AF;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">© 2025 Your Job Finder. Educational project – do not reply.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
    '''