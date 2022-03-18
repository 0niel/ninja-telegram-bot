from envparse import env

TELEGRAM_TOKEN = env.str("TELEGRAM_TOKEN", default="")
SENTRY_URL = env.str("SENTRY_URL", default="")
POSTGRES_URI = env.str("POSTGRES_URI", default="postgres://postgres:oniel@localhost:5432/postgres")
MIREA_NINJA_GROUP_ID = env.int("MIREA_NINJA_GROUP_ID", default=-1001570749726)
