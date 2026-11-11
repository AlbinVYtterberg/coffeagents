"""Sending (SMTP) and receiving (POP3) mail for our account.

Server details come from smtp.md; our address and mailbox port (the
"Extension" column) come from we.md.
"""
import poplib
import re
import smtplib
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import parseaddr
from pathlib import Path

from store import read_table

ROOT = Path(__file__).parent


def _mail_config() -> dict:
    text = (ROOT / "smtp.md").read_text(encoding="utf-8")
    host = re.search(r"IP:\s*([\d.]+)", text).group(1)
    smtp_port = int(re.search(r":(\d+)\s+SMTP", text).group(1))
    password = re.search(r"^user:(\S+)", text, re.MULTILINE).group(1)
    name, address, extension = read_table("we.md")[0]
    return {
        "host": host,
        "smtp_port": smtp_port,
        "pop_port": int(extension),
        "pop_user": "user",
        "pop_password": password,
        "name": name,
        "address": address.lower(),
    }


CONFIG = _mail_config()
OUR_NAME = CONFIG["name"]
OUR_ADDRESS = CONFIG["address"]


def send_mail(to: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"] = f"{OUR_NAME} <{OUR_ADDRESS}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(CONFIG["host"], CONFIG["smtp_port"], timeout=30) as smtp:
        smtp.send_message(msg)


def fetch_new_mail(seen: set[str]) -> list[dict]:
    """Return messages whose POP3 UIDL is not in `seen`. Nothing is deleted."""
    pop = poplib.POP3(CONFIG["host"], CONFIG["pop_port"], timeout=30)
    try:
        pop.user(CONFIG["pop_user"])
        pop.pass_(CONFIG["pop_password"])
        messages = []
        for line in pop.uidl()[1]:
            number, uid = line.decode().split(maxsplit=1)
            if uid in seen:
                continue
            raw = b"\n".join(pop.retr(int(number))[1])
            msg = BytesParser(policy=policy.default).parsebytes(raw)
            body_part = msg.get_body(preferencelist=("plain", "html"))
            messages.append({
                "uid": uid,
                "sender": parseaddr(msg.get("From", ""))[1].lower(),
                "subject": str(msg.get("Subject", "")),
                "date": str(msg.get("Date", "")),
                "body": body_part.get_content() if body_part else "",
            })
        return messages
    finally:
        pop.quit()
