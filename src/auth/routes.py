from fastapi import APIRouter, Depends, status
from src.auth.schemas import UserCreateModel, UserModel, UserLoginModel, UserBooksModel, EmailModel
from .service import UserService
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.exceptions import HTTPException
from .utils import create_access_token, decode_token, verify_password
from fastapi.responses import JSONResponse
from datetime import timedelta
from .dependencies import RefreshTokenBearer, AccessTokenBearer, get_current_user, RoleChecker
from src.db.redis import add_jti_to_blocklist
from datetime import datetime
from src.errors import UserAlreadyExists, UserNotFound, InvalidCredentials, InvalidToken
from src.mail import mail, create_message




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

@auth_router.post('/signup', response_model=UserModel, status_code=status.HTTP_201_CREATED)
async def create_user_account(user_data: UserCreateModel, session: AsyncSession = Depends(get_session)):
    email = user_data.email

    user_exists = await user_service.user_exists(email, session)

    if user_exists:
        raise UserAlreadyExists()
        # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User with email already exist")
    
    new_user = await user_service.create_user(user_data, session)

    return new_user

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

