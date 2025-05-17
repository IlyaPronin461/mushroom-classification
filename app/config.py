import logging
from pydantic_settings import BaseSettings
from logging.config import dictConfig


class Settings(BaseSettings):
    gdrive_file_ids: dict = {
        "config.json": "1VMpENG-GP1FS2KpZKmws_xTL8C2hjz-5",
        "model.safetensors": "1hlK4Lpj1QxqQV0-AYDJuMzKdGndUuq5A",
        "preprocessor_config.json": "1iMCKQVDvZVOcRwC2iZioktDLFbTb-vSm",
        "metadata.json": "1YzRyyuSkjfPLsze0ERQmW37g4WwKMAzH"
    }

    class Config:
        protected_namespaces = ('settings_',)


# Настройка логирования
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    },
    "loggers": {
        "app": {
            "handlers": ["default"],
            "level": "DEBUG", # INFO или DEBUG
            "propagate": False
        },
        "gdown": {
            "handlers": ["default"],
            "level": "WARNING"
        }
    }
}

dictConfig(LOG_CONFIG)
logger = logging.getLogger("app")

settings = Settings()