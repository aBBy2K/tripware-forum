from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from config import MAIL_USERNAME, MAIL_PASSWORD

conf = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_FROM=MAIL_USERNAME,
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

async def _safe_send(email, head, body):
    try:
        await notification_email(email, head, body)
    except Exception as e:
        print(f"[MAIL]: Failed to send email: {e}")

async def send_email(subject: str, body: str, email: str):
    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=body,
        subtype="plain"
    )

    fm = FastMail(conf)

    await fm.send_message(message)

async def notification_email(email: str, head: str, body: str):
    message = MessageSchema(
        subject="tripware.club / new notification",
        recipients=[email],
        body=f"""
            {head}
            
            {body}
            
            TRIPWARE.CLUB
            """,
            subtype="plain"
        )
    
    fm = FastMail(conf)
    
    await fm.send_message(message)