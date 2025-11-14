from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str
    SUPABASE_JWT_AUDIENCE: str = "authenticated"

    # Storage
    STORAGE_BUCKET: str = "uploads"

    # App
    ENV: str = "dev"
    API_PREFIX: str = "/api"
    VERSION: str = "0.1.0"

    #ML
    ML_BASE_URL: str = ""      # empty => use stub
    ML_API_KEY: str = ""       # optional shared key

    class Config:
        env_file = ".env"

settings = Settings()

