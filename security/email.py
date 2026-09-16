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


async def verification_email(email: str, token: str):
    message = MessageSchema(
        subject="tripware.club / verification mail",
        recipients=[email],
        body=f"""
        Verify your account:

        https://tripware.ru/auth/verify/{token}    
        """,
        subtype="plain"
    )

    fm = FastMail(conf)

    await fm.send_message(message)

async def password_recovery_email(email: str, token: str):
    message = MessageSchema(
        subject="tripware.club / password reset mail",
        recipients=[email],
        body=f"""
            SOMEONE REQUESTED PASSWORD RECOVERY ON YOUR EMAIL

            https://tripware.ru/auth/forgor/verify/{token}    
            
            IF IT WASN'T YOU, THEN IT MEANS THAT SOMEONE IS TRYING TO HACK YOUR TRIPWARE ACCOUNT. PLEASE CONTACT ADMINISTRATION
            
            TRIPWARE.CLUB
            """,
        subtype="plain"
    )

    fm = FastMail(conf)

    await fm.send_message(message)