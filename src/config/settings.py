"""
Configuration settings for the Network Migration Automation project.
Uses pydantic-settings for environment variable management.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class WIDSettings(BaseSettings):
    """WID (Web Ingeniería) connection settings."""
    base_url: str = Field(default="https://wid.claro.com.ar", alias="WID_BASE_URL")
    username: str = Field(default="", alias="WID_USERNAME")
    password: str = Field(default="", alias="WID_PASSWORD")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class JarvisSettings(BaseSettings):
    """Jarvis API connection settings."""
    base_url: str = Field(default="", alias="JARVIS_BASE_URL")
    api_key: str = Field(default="", alias="JARVIS_API_KEY")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class SAPSettings(BaseSettings):
    """SAP connection settings."""
    base_url: str = Field(default="", alias="SAP_BASE_URL")
    username: str = Field(default="", alias="SAP_USERNAME")
    password: str = Field(default="", alias="SAP_PASSWORD")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class FlowoneSettings(BaseSettings):
    """Flowone connection settings."""
    base_url: str = Field(default="", alias="FLOWONE_BASE_URL")
    username: str = Field(default="", alias="FLOWONE_USERNAME")
    password: str = Field(default="", alias="FLOWONE_PASSWORD")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class AppSettings(BaseSettings):
    """General application settings."""
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    headless_browser: bool = Field(default=True, alias="HEADLESS_BROWSER")
    data_dir: str = Field(default="data")
    
    # Sub-settings
    wid: WIDSettings = Field(default_factory=WIDSettings)
    jarvis: JarvisSettings = Field(default_factory=JarvisSettings)
    sap: SAPSettings = Field(default_factory=SAPSettings)
    flowone: FlowoneSettings = Field(default_factory=FlowoneSettings)
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> AppSettings:
    """Get cached application settings."""
    return AppSettings()
