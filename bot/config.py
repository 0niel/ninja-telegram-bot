from envparse import env

TELEGRAM_TOKEN = env.str(
    "TELEGRAM_TOKEN", default="")
SENTRY_URL = env.str("SENTRY_URL", default="")
POSTGRES_URI = env.str(
    "POSTGRES_URI", default="postgres://postgres:oniel@localhost/postgres")
MIREA_NINJA_GROUP_ID = env.int("MIREA_NINJA_GROUP_ID", default=-567317308)
YANDEX_IAM_TOKEN = env.str(
    "YANDEX_IAM_TOKEN", default="")
YANDEX_FOLDER_ID = env.str("YANDEX_FOLDER_ID", default="")
