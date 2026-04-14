from pathlib import Path
import os
from dotenv import load_dotenv
import cloudinary
from django.contrib.auth import get_user_model




# ---------------- BASE DIR ---------------- #
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------- LOAD ENV (FIXED) ---------------- #
from dotenv import load_dotenv


load_dotenv()  # 🔥 ALWAYS load .env properly
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


# ---------------- SECURITY ---------------- #
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")

DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = ['getspeakhub.org', 'www.getspeakhub.org', '.onrender.com']


# ---------------- APPLICATIONS ---------------- #
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'speakproject.apps.SpeakprojectConfig',
    'reminders',
    'cloudinary',
    'cloudinary_storage',

]


# ---------------- MIDDLEWARE ---------------- #
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ---------------- URL CONFIG ---------------- #
ROOT_URLCONF = 'Speak.urls'


# ---------------- TEMPLATES ---------------- #
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',

                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# ---------------- DATABASE ---------------- #
import dj_database_url
import os

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# ---------------- PASSWORD VALIDATION ---------------- #
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
]


# ---------------- INTERNATIONAL ---------------- #
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True
USE_TZ = True


# ---------------- STATIC ---------------- #
import os

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# ---------------- MEDIA ---------------- #
import os

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'


# ---------------- DEFAULT PK ---------------- #
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---------------- LOGIN / LOGOUT ---------------- #
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'


# ---------------- RAZORPAY (FINAL FIX) ---------------- #
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

# 🔥 FALLBACK (FOR DEBUGGING ONLY)
if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    print("⚠️ Using fallback Razorpay keys")
    RAZORPAY_KEY_ID = "rzp_test_replace_me"
    RAZORPAY_KEY_SECRET = "replace_me"


# ---------------- AGORA ---------------- #
AGORA_APP_ID = os.getenv("AGORA_APP_ID", "")
AGORA_APP_CERTIFICATE = os.getenv("AGORA_APP_CERTIFICATE", "")


# ---------------- EMAIL ---------------- #
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = os.getenv("SENDGRID_API_KEY")
DEFAULT_FROM_EMAIL = 'speakappplatform@gmail.com'

# ---------------- SESSION ---------------- #
SESSION_COOKIE_AGE = 86400


# ---------------- SECURITY ---------------- #
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:8000']


# ---------------- DEBUG PRINT ---------------- #
if DEBUG:
    print("\n🔧 DEBUG MODE ACTIVE")
    print("📦 BASE DIR:", BASE_DIR)
    print("🔑 RAZORPAY KEY:", RAZORPAY_KEY_ID)
    print("🔐 RAZORPAY SECRET:", RAZORPAY_KEY_SECRET)
    print("🎥 AGORA:", AGORA_APP_ID)
    
    
