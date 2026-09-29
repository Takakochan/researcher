import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

from .config import Config


def send_report(config: Config, to: str, subject: str, report_path: Path) -> None:
    """レポートを本文と添付ファイル (.md) の両方に入れてメール送信"""
    missing = [
        name
        for name, value in (
            ("SMTP_HOST", config.smtp_host),
            ("SMTP_USER", config.smtp_user),
            ("SMTP_PASSWORD", config.smtp_password),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(f".env に次の値を設定してください: {', '.join(missing)}")

    report = report_path.read_text(encoding="utf-8")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config.mail_from or config.smtp_user
    msg["To"] = to
    msg.set_content(report)
    msg.add_attachment(
        report.encode("utf-8"),
        maintype="text",
        subtype="markdown",
        filename=report_path.name,
    )

    context = ssl.create_default_context()
    if config.smtp_port == 465:
        with smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, context=context) as smtp:
            smtp.login(config.smtp_user, config.smtp_password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(config.smtp_host, config.smtp_port) as smtp:
            smtp.starttls(context=context)
            smtp.login(config.smtp_user, config.smtp_password)
            smtp.send_message(msg)
