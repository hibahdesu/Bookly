from fastapi import APIRouter, Depends, status
from src.auth.schemas import UserCreateModel, UserModel, UserLoginModel, UserBooksModel, EmailModel, PasswordResetRequestModel
from .service import UserService
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.exceptions import HTTPException
from .utils import create_access_token, decode_token, verify_password, create_url_safe_token, decode_url_safe_token
from fastapi.responses import JSONResponse
from datetime import timedelta
from .dependencies import RefreshTokenBearer, AccessTokenBearer, get_current_user, RoleChecker
from src.db.redis import add_jti_to_blocklist
from datetime import datetime
from src.errors import UserAlreadyExists, UserNotFound, InvalidCredentials, InvalidToken
from src.mail import mail, create_message
from src.config import Config
from src.db.main import get_session




auth_router = APIRouter()
user_service = UserService()
role_checker = RoleChecker(['admin', 'user'])


REFRESH_TOKEN_EXPIRY = 2


@auth_router.post('/send_mail')
async def send_mail(emails:EmailModel):
    emails = emails.addresses

    html = """
    <html>
    <head>
        <style>
            .container {
                font-family: Arial, sans-serif;
                padding: 20px;
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 8px;
                max-width: 600px;
                margin: auto;
            }
            h1 {
                color: #2c3e50;
            }
            p {
                font-size: 16px;
                color: #333;
            }
            .button {
                display: inline-block;
                padding: 10px 20px;
                margin-top: 20px;
                font-size: 16px;
                background-color: #3498db;
                color: white;
                text-decoration: none;
                border-radius: 5px;
            }
            .footer {
                margin-top: 30px;
                font-size: 12px;
                color: #888;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📚 Welcome to Bookly!</h1>
            <p>Thank you for joining <strong>Bookly</strong> – 
            your go-to app for discovering and enjoying amazing books.</p>
            
            <p>Here's what you can do with Bookly:</p>
            <ul>
                <li>🔍 Explore a vast library of books</li>
                <li>💾 Save your favorites</li>
                <li>📝 Write reviews and connect with other readers</li>
            </ul>

            <p>We're excited to have you on board. If you ever need help, 
            our support team is just an email away.</p>
            
            <a class="button" href="https://booklyapp.com" target="_blank">Start Reading</a>

            <div class="footer">
                <p>If you did not sign up for Bookly, please ignore this message.</p>
                <p>Contact us at support@booklyapp.com</p>
            </div>
        </div>
    </body>
    </html>
    """

    message = create_message(
        recipients=emails,
        subject="📚 Welcome to Bookly!",
        body=html
    )

    await mail.send_message(message)

    return {"message": "Email sent successfully"}

@auth_router.post('/signup',  status_code=status.HTTP_201_CREATED)
async def create_user_account(user_data: UserCreateModel, session: AsyncSession = Depends(get_session)):
    email = user_data.email

    user_exists = await user_service.user_exists(email, session)

    if user_exists:
        raise UserAlreadyExists()
        # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User with email already exist")
    
    new_user = await user_service.create_user(user_data, session)

    token = create_url_safe_token({"email": email})

    link = f'http://{Config.DOMAIN}/api/v1/auth/verify/{token}'

    html_message = f"""
    <html>
    <head>
    <style>
        .container {{
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            padding: 30px;
            border-radius: 8px;
            max-width: 600px;
            margin: auto;
            color: #333;
        }}
        .content {{
            background-color: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
        }}
        p {{
            font-size: 16px;
            line-height: 1.5;
        }}
        .button {{
            display: inline-block;
            padding: 12px 25px;
            margin-top: 20px;
            background-color: #3498db;
            color: #fff;
            text-decoration: none;
            font-size: 16px;
            border-radius: 5px;
        }}
        .footer {{
            font-size: 12px;
            color: #888;
            margin-top: 30px;
            text-align: center;
        }}
    </style>
    </head>
    <body>
        <div class="container">
            <div class="content">
                <h1>Verify Your Email</h1>
                <p>Hi there,</p>
                <p>Thanks for signing up! To complete your registration, please verify your email by clicking the button below:</p>
                
                <a href="{link}" class="button" target="_blank">Verify Email</a>

                <p>If the button doesn't work, copy and paste the following URL into your browser:</p>
                <p><a href="{link}" target="_blank">{link}</a></p>
            </div>

            <div class="footer">
                <p>You received this email because you signed up for Bookly.</p>
                <p>If you didn't sign up, please ignore this message.</p>
            </div>
        </div>
    </body>
    </html>
"""

    
    message = create_message(
        recipients=[email],
        subject="📚 Verify Your Email",
        body=html_message
    )

    await mail.send_message(message)


    return {
        "message": "Account Created! Check email to verify your account",
        "user": new_user
    }

@auth_router.get('/verify/{token}')
async def verify_user_account(token:str, session:AsyncSession= Depends(get_session)):
    token_data = decode_url_safe_token(token)

    user_email = token_data.get('email')

    if user_email:
        user = await user_service.get_user_by_email(user_email, session)

        if not user:
            raise UserNotFound()
        
        await user_service.update_user(user, {'is_verified': True}, session)

        return JSONResponse(content={
            "message": "Account Verified Successfully.",
        },
        status_code=status.HTTP_200_OK
        )
    
    return JSONResponse(content={
        "message": "Error occured during verification"
    },
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )



@auth_router.post('/login')
async def login_users(login_data: UserLoginModel, session: AsyncSession = Depends(get_session)):
    email = login_data.email
    password = login_data.password

    user = await user_service.get_user_by_email(email, session)

    if user is not None:
        password_valid = verify_password(password, user.password_hash)

        if password_valid:
            access_token = create_access_token(
                user_data = {
                    "email": user.email,
                    "user_uid": str(user.uid),
                    "role": user.role
                }
            )

            refresh_token = create_access_token(
                user_data = {
                    "email": user.email,
                    "user_uid": str(user.uid)
                },
                refresh=True,
                expiry=timedelta(days=REFRESH_TOKEN_EXPIRY)
            )


            return JSONResponse(
                content={
                    "message": "Login Successful",

                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {
                        "email": user.email,
                        "uid": str(user.uid)
                    }
                }
            )
        
    # raise HTTPException(
    #     status_code=status.HTTP_403_FORBIDDEN,
    #     detail='Invalid Email Or Password'
    # )
    raise InvalidCredentials()


@auth_router.get('/refresh_token')
async def get_new_access_token(token_details: dict = Depends(RefreshTokenBearer())):
    expiry_timestamp = token_details['exp']

    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
        new_access_token = create_access_token(
            user_data=token_details['user']
        )

        return JSONResponse(content={
            "access_token": new_access_token
        })

    # raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
    #                     detail="Invalid or expired token")
    raise InvalidToken()


@auth_router.get('/me', response_model=UserBooksModel)
async def get_current_user(user = Depends(get_current_user),
                           _bool=Depends(role_checker)):
    return user


@auth_router.get('/logout')
async def revooke_token(token_details: dict=Depends(AccessTokenBearer())):

    jti = token_details['jti'] 

    await add_jti_to_blocklist(jti)

    return JSONResponse(
        content={
            "message": "loged out successfully"
        },
        status_code=status.HTTP_200_OK
    )



"""
1. provide the email -> password reset request
2. send password reset link
3. reset password -> password reset confirmation
"""

@auth_router.post('/password-reset-request')
async def password_reset_request(email_data: PasswordResetRequestModel):
    email = email_data.email

    token = create_url_safe_token({"email": email})

    link = f'http://{Config.DOMAIN}/api/v1/auth/password-reset-confirm/{token}'

    html_message = f"""
                <html>
                <head>
                <style>
                    .container {{
                        font-family: Arial, sans-serif;
                        background-color: #f4f4f4;
                        padding: 30px;
                        border-radius: 8px;
                        max-width: 600px;
                        margin: auto;
                        color: #333;
                    }}
                    .content {{
                        background-color: #ffffff;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    h1 {{
                        color: #2c3e50;
                    }}
                    p {{
                        font-size: 16px;
                        line-height: 1.5;
                    }}
                    .button {{
                        display: inline-block;
                        padding: 12px 25px;
                        margin-top: 20px;
                        background-color: #e67e22;
                        color: #fff;
                        text-decoration: none;
                        font-size: 16px;
                        border-radius: 5px;
                    }}
                    .footer {{
                        font-size: 12px;
                        color: #888;
                        margin-top: 30px;
                        text-align: center;
                    }}
                </style>
                </head>
                <body>
                    <div class="container">
                        <div class="content">
                            <h1>Password Reset Request</h1>
                            <p>Hi there,</p>
                            <p>We received a request to reset your password for your <strong>Bookly</strong> account.</p>
                            <p>If you made this request, click the button below to reset your password:</p>
                            
                            <a href="{link}" class="button" target="_blank">Reset Password</a>

                            <p>If the button doesn’t work, copy and paste this URL into your browser:</p>
                            <p><a href="{link}" target="_blank">{link}</a></p>

                            <p>If you didn’t request a password reset, you can safely ignore this email.</p>
                        </div>

                        <div class="footer">
                            <p>This message was sent by Bookly • support@booklyapp.com</p>
                        </div>
                    </div>
                </body>
                </html>
                """

    message = create_message(
        recipients=[email],
        subject="📚 Reset Your Password",
        body=html_message
    )

    await mail.send_message(message)


    return JSONResponse(
        content={
            "message": "Please check your email for instructions to reset your password"
        },
        status_code=status.HTTP_200_OK
        
    )
        
    
