import os
from typing import List, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class AssetConfig:
    symbol: str
    allocation_pct: float
    leverage: int
    stop_loss_pct: float
    take_profit_pct: float
    trailing_stop_pct: float
    trailing_activation_pct: float
    enabled: bool = True
    
@dataclass
class ExchangeConfig:
    api_key: str
    api_secret: str
    testnet: bool
    base_url: str = ""
    
@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str
    username: str
    password: str
    
@dataclass
class RedisConfig:
    host: str
    port: int
    db: int
    password: str = ""
    
@dataclass
class RiskConfig:
    per_asset_allocation_pct: float
    leverage_per_asset: int
    stop_loss_pct: float
    take_profit_pct: float
    max_daily_loss_pct: float
    max_portfolio_drawdown_pct: float
    max_total_exposure_pct: float

@dataclass
class TelegramConfig:
    bot_token: str
    channel_id: str
    admin_chat_id: str = ""
    enabled: bool = False

class Settings:
    def __init__(self):
        # Exchange Configuration (Bybit)
        # Support for testnet, demo, and live environments
        env_mode = os.getenv('BYBIT_TESTNET', 'true').lower()
        demo_mode = os.getenv('BYBIT_DEMO', 'false').lower() == 'true'
        
        if demo_mode:
            base_url = "https://api-demo.bybit.com"
        elif env_mode == 'true':
            base_url = "https://api-testnet.bybit.com"
        else:
            base_url = "https://api.bybit.com"
            
        self.exchange = ExchangeConfig(
            api_key=os.getenv('BYBIT_API_KEY', ''),
            api_secret=os.getenv('BYBIT_API_SECRET', ''),
            testnet=env_mode == 'true',
            base_url=base_url
        )
        
        # Database Configuration
        self.database = DatabaseConfig(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(os.getenv('POSTGRES_PORT', '5432')),
            database=os.getenv('POSTGRES_DB', 'multiasset_trading'),
            username=os.getenv('POSTGRES_USER', 'trading_user'),
            password=os.getenv('POSTGRES_PASSWORD', 'secure_password')
        )
        
        # Redis Configuration
        self.redis = RedisConfig(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=int(os.getenv('REDIS_DB', '0')),
            password=os.getenv('REDIS_PASSWORD', '')
        )
        
        # Multi-Asset Configuration with individual risk parameters
        self.assets = [
            AssetConfig('BTC', 0.07, 10, 0.01, 0.03, 0.01, 0.02, True),  # 1% SL, 3% TP, 1% trailing at 2% profit
            AssetConfig('ETH', 0.07, 10, 0.015, 0.045, 0.02, 0.02, True),  # 1.5% SL, 4.5% TP, 2% trailing at 2% profit
            AssetConfig('SOL', 0.07, 10, 0.015, 0.06, 0.02, 0.03, True)   # 1.5% SL, 6% TP, 2% trailing at 3% profit
        ]
        
        # Risk Management Configuration
        self.risk = RiskConfig(
            per_asset_allocation_pct=float(os.getenv('ASSET_ALLOCATION_PCT', '0.07')),
            leverage_per_asset=int(os.getenv('LEVERAGE_PER_ASSET', '10')),
            stop_loss_pct=float(os.getenv('STOP_LOSS_PCT', '0.015')),
            take_profit_pct=float(os.getenv('TAKE_PROFIT_PCT', '0.06')),
            max_daily_loss_pct=float(os.getenv('MAX_DAILY_LOSS_PCT', '0.05')),
            max_portfolio_drawdown_pct=float(os.getenv('MAX_PORTFOLIO_DRAWDOWN_PCT', '0.20')),
            max_total_exposure_pct=float(os.getenv('MAX_PORTFOLIO_EXPOSURE', '2.1'))
        )
        
        # System Configuration
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        self.max_workers = int(os.getenv('MAX_WORKERS', '4'))
        
        # Web Interface
        self.web_host = os.getenv('WEB_HOST', '0.0.0.0')
        self.web_port = int(os.getenv('WEB_PORT', '8080'))
        
        # Telegram Configuration
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        channel_id = os.getenv('TELEGRAM_CHANNEL_ID', '')
        admin_chat_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID', '')
        
        self.telegram = TelegramConfig(
            bot_token=bot_token,
            channel_id=channel_id,
            admin_chat_id=admin_chat_id,
            enabled=bool(bot_token and channel_id)
        )
        
        # Other Notifications
        self.discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL', '')
        
    def get_enabled_assets(self) -> List[AssetConfig]:
        return [asset for asset in self.assets if asset.enabled]
    
    def get_asset_symbols(self) -> List[str]:
        return [asset.symbol for asset in self.get_enabled_assets()]
    
    def get_bybit_symbols(self) -> List[str]:
        return [f"{asset.symbol}USDT" for asset in self.get_enabled_assets()]
    
    def get_asset_config(self, symbol: str) -> AssetConfig:
        """Get configuration for specific asset"""
        for asset in self.assets:
            if asset.symbol == symbol:
                return asset
        raise ValueError(f"Asset {symbol} not found in configuration")
    
    def get_asset_risk_params(self, symbol: str) -> Dict[str, float]:
        """Get risk parameters for specific asset"""
        asset_config = self.get_asset_config(symbol)
        return {
            'stop_loss_pct': asset_config.stop_loss_pct,
            'take_profit_pct': asset_config.take_profit_pct,
            'trailing_stop_pct': asset_config.trailing_stop_pct,
            'trailing_activation_pct': asset_config.trailing_activation_pct
        }

# Global settings instance
settings = Settings()