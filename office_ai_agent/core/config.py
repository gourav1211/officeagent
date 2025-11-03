from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


def _parse_bool(val: Optional[str], default: bool = False) -> bool:
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "on"}


def _parse_int(val: Optional[str], default: int) -> int:
    try:
        return int(val) if val is not None else default
    except Exception:
        return default


def _parse_float(val: Optional[str], default: float) -> float:
    try:
        return float(val) if val is not None else default
    except Exception:
        return default


@dataclass
class LLMConfig:
    provider: str = "gemini"
    model: str = "gemini-1.5-pro"
    temperature: float = 0.7
    gemini_api_key: Optional[str] = None


@dataclass
class FeatureToggles:
    enable_powerpoint: bool = True
    enable_word: bool = True
    enable_excel: bool = True
    enable_outlook: bool = False
    enable_teams: bool = False


@dataclass
class ServerConfig:
    api_port: int = 8765
    web_port: Optional[int] = None  # not used by server.py


@dataclass
class MonitoringConfig:
    log_level: str = "INFO"
    sentry_dsn: Optional[str] = None
    log_file: Optional[str] = None


@dataclass
class AppFlags:
    debug: bool = False
    development: bool = True


@dataclass
class Config:
    llm: LLMConfig = field(default_factory=LLMConfig)
    features: FeatureToggles = field(default_factory=FeatureToggles)
    server: ServerConfig = field(default_factory=ServerConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    flags: AppFlags = field(default_factory=AppFlags)

    # ----------------------------- Load/Save ------------------------------
    @staticmethod
    def _load_dotenv_if_available() -> None:
        try:  # optional
            from dotenv import load_dotenv  # type: ignore

            load_dotenv()  # loads .env in CWD if present
        except Exception:
            pass

    @staticmethod
    def _find_config_file() -> Optional[Path]:
        candidates = [
            Path.cwd() / "config.json",
            Path.cwd() / "office_ai_agent.json",
            Path.home() / ".office_ai_agent" / "config.json",
        ]
        for p in candidates:
            if p.exists() and p.is_file():
                return p
        return None

    @staticmethod
    def _apply_dict(cfg: "Config", data: Dict[str, Any]) -> None:
        # Shallow update for nested dataclasses if matching keys exist
        if "llm" in data and isinstance(data["llm"], dict):
            for k, v in data["llm"].items():
                if hasattr(cfg.llm, k):
                    setattr(cfg.llm, k, v)
        if "features" in data and isinstance(data["features"], dict):
            for k, v in data["features"].items():
                if hasattr(cfg.features, k):
                    setattr(cfg.features, k, bool(v))
        if "server" in data and isinstance(data["server"], dict):
            for k, v in data["server"].items():
                if hasattr(cfg.server, k):
                    setattr(cfg.server, k, v)
        if "monitoring" in data and isinstance(data["monitoring"], dict):
            for k, v in data["monitoring"].items():
                if hasattr(cfg.monitoring, k):
                    setattr(cfg.monitoring, k, v)
        if "flags" in data and isinstance(data["flags"], dict):
            for k, v in data["flags"].items():
                if hasattr(cfg.flags, k):
                    setattr(cfg.flags, k, bool(v))

    @classmethod
    def load(cls, strict: bool = False) -> "Config":
        """Load configuration from .env (optional), JSON file (optional), and env vars.

        Precedence (lowest to highest): defaults < JSON file < env vars.
        If `strict` and provider is gemini, require GEMINI_API_KEY.
        """
        cls._load_dotenv_if_available()

        cfg = cls()

        # JSON config (optional)
        cfg_file = cls._find_config_file()
        if cfg_file is not None:
            try:
                data = json.loads(cfg_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    cls._apply_dict(cfg, data)
            except Exception:
                pass

        # Env overrides
        llm_provider = os.getenv("LLM_PROVIDER")
        if llm_provider:
            cfg.llm.provider = llm_provider.strip().lower()
        model = os.getenv("LLM_MODEL")
        if model:
            cfg.llm.model = model
        cfg.llm.temperature = _parse_float(os.getenv("LLM_TEMPERATURE"), cfg.llm.temperature)
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            cfg.llm.gemini_api_key = gemini_key

        cfg.features.enable_powerpoint = _parse_bool(os.getenv("ENABLE_POWERPOINT"), cfg.features.enable_powerpoint)
        cfg.features.enable_word = _parse_bool(os.getenv("ENABLE_WORD"), cfg.features.enable_word)
        cfg.features.enable_excel = _parse_bool(os.getenv("ENABLE_EXCEL"), cfg.features.enable_excel)
        cfg.features.enable_outlook = _parse_bool(os.getenv("ENABLE_OUTLOOK"), cfg.features.enable_outlook)
        cfg.features.enable_teams = _parse_bool(os.getenv("ENABLE_TEAMS"), cfg.features.enable_teams)

        cfg.server.api_port = _parse_int(os.getenv("API_PORT"), cfg.server.api_port)
        wp = os.getenv("WEB_PORT")
        cfg.server.web_port = _parse_int(wp, cfg.server.web_port or 0) if wp else cfg.server.web_port

        ll = os.getenv("LOG_LEVEL")
        if ll:
            cfg.monitoring.log_level = ll.upper()
        sd = os.getenv("SENTRY_DSN")
        if sd:
            cfg.monitoring.sentry_dsn = sd
        lf = os.getenv("LOG_FILE")
        if lf:
            cfg.monitoring.log_file = lf

        cfg.flags.debug = _parse_bool(os.getenv("DEBUG"), cfg.flags.debug)
        cfg.flags.development = _parse_bool(os.getenv("DEVELOPMENT"), cfg.flags.development)

        if strict:
            cfg.validate()
        return cfg

    def validate(self) -> None:
        if self.llm.provider == "gemini" and not (self.llm.gemini_api_key and self.llm.gemini_api_key.strip()):
            raise ValueError("GEMINI_API_KEY is required for provider=gemini")

    # ----------------------------- Utilities ------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def save_config(self, path: Optional[os.PathLike] | Optional[str] = None) -> Path:
        if path is None:
            path = Path.cwd() / "config.json"
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return p
