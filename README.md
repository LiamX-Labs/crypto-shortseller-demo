# Multi-Asset Short Trading System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Bybit API V5](https://img.shields.io/badge/Bybit-API%20V5-orange.svg)](https://bybit-exchange.github.io/docs/v5/intro)

An automated cryptocurrency trading system that executes short positions on Bitcoin (BTC), Ethereum (ETH), and Solana (SOL) using EMA crossover signals on Bybit exchange.

## 🚀 Features

- **Multi-Asset Trading**: Simultaneous trading across BTC, ETH, and SOL
- **EMA Crossover Strategy**: Uses 240/600 EMA crossovers for signal generation
- **Risk Management**: Built-in stop-loss, take-profit, and position sizing
- **Real-time Monitoring**: Live market data processing on 5-minute intervals
- **Telegram Integration**: Trade notifications and system status updates
- **Bybit Integration**: Full V5 API support with testnet capability
- **Quantity Validation**: Automatic precision rounding and order validation
- **Error Recovery**: Robust retry logic and error handling

## 📋 Strategy Overview

### Signal Generation
- **Bearish Cross**: EMA240 crosses below EMA600
- **Entry Condition**: Price below both EMAs + Active market regime
- **Exit Conditions**: 24-hour max hold time or regime change

### Risk Management
- **Position Size**: 7% of balance per asset with 10x leverage
- **Stop Loss**: 1.5% above entry price
- **Take Profit**: 6% below entry price
- **Maximum Exposure**: 21% of total balance (3 assets × 7%)

### Market Regime Detection
- **ACTIVE**: Price < EMA240 < EMA600 (bearish alignment)
- **INACTIVE**: Price above EMAs or bullish alignment
- **Cross Limits**: Maximum 12 crosses per asset per 24 hours

## 🛠️ Installation

### Prerequisites
- Python 3.12+
- PostgreSQL (optional, for data storage)
- Redis (optional, for caching)
- Bybit API credentials

### Clone Repository
```bash
git clone <repository-url>
cd multiasset
```

### Install Dependencies
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### Environment Configuration
Create a `.env` file in the project root:

```env
# Bybit API Configuration
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_api_secret_here
BYBIT_TESTNET=true  # Set to false for live trading
BYBIT_DEMO=false    # Set to true for demo trading

# Risk Management
ASSET_ALLOCATION_PCT=0.07    # 7% per asset
LEVERAGE_PER_ASSET=10        # 10x leverage
STOP_LOSS_PCT=0.015          # 1.5% stop loss
TAKE_PROFIT_PCT=0.06         # 6% take profit
MAX_DAILY_LOSS_PCT=0.05      # 5% daily loss limit
MAX_PORTFOLIO_DRAWDOWN_PCT=0.20  # 20% max drawdown
MAX_PORTFOLIO_EXPOSURE=2.1   # 210% max exposure

# Telegram Notifications (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=your_channel_id
TELEGRAM_ADMIN_CHAT_ID=your_admin_chat_id

# Database Configuration (Optional)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=multiasset_trading
POSTGRES_USER=trading_user
POSTGRES_PASSWORD=secure_password

# Redis Configuration (Optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# System Configuration
LOG_LEVEL=INFO
DEBUG_MODE=false
MAX_WORKERS=4
```

## 🏃‍♂️ Usage

### Start Trading System
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Run the trading system
python scripts/start_trading.py
```

### Testing Mode
For testing without real money:
```bash
# Set testnet mode in .env file
BYBIT_TESTNET=true
BYBIT_DEMO=true  # Optional: Use demo environment
```

### Manual Testing
```bash
# Test quantity validation
python tests/test_quantity_validation.py

# Test Bybit connection
python tests/test_bybit_connection.py

# Test Telegram integration
python tests/test_telegram_integration.py
```

## 📊 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Market Data   │────│  Strategy Engine │────│  Order Manager  │
│   (Bybit API)   │    │  (EMA Analysis)  │    │  (Position Mgmt)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       │
         │                        │                       │
         ▼                        ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Store    │    │   Notifications  │    │   Risk Manager  │
│ (PostgreSQL)    │    │  (Telegram Bot)  │    │  (Stop/Take)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
multiasset/
├── src/
│   ├── core/
│   │   └── strategy_engine.py     # Main trading strategy logic
│   ├── exchange/
│   │   └── bybit_client.py        # Bybit API integration
│   └── notifications/
│       └── telegram_bot.py        # Telegram notifications
├── config/
│   └── settings.py                # Configuration management
├── scripts/
│   └── start_trading.py           # Main entry point
├── tests/
│   ├── test_quantity_validation.py
│   ├── test_bybit_connection.py
│   └── test_telegram_integration.py
├── logs/
│   └── trading.log                # System logs
├── data/                          # Historical data storage
├── docs/                          # Documentation
├── requirements.txt               # Python dependencies
├── docker-compose.yml            # Docker configuration
├── .env.example                  # Environment template
└── README.md                     # This file
```

## 🔧 Configuration

### Asset Configuration
Modify `config/settings.py` to adjust trading assets:

```python
self.assets = [
    AssetConfig('BTC', 0.07, 10, True),   # Symbol, allocation%, leverage, enabled
    AssetConfig('ETH', 0.07, 10, True),
    AssetConfig('SOL', 0.07, 10, True)
]
```

### Risk Parameters
Adjust risk settings in `.env` file or `config/settings.py`:

- `ASSET_ALLOCATION_PCT`: Percentage of balance per asset (default: 7%)
- `LEVERAGE_PER_ASSET`: Leverage multiplier (default: 10x)
- `STOP_LOSS_PCT`: Stop loss percentage (default: 1.5%)
- `TAKE_PROFIT_PCT`: Take profit percentage (default: 6%)

## 📈 Monitoring & Logging

### Log Files
- **Main Log**: `logs/trading.log`
- **Error Log**: System errors and API failures
- **Trade Log**: All entry/exit transactions

### Telegram Notifications
Configure Telegram bot for real-time updates:
- Trade entries and exits
- System status updates
- Error alerts
- Daily performance reports

### Key Metrics
- Portfolio balance and P&L
- Active positions count
- Signal generation frequency
- Order execution success rate

## 🚨 Risk Warnings

⚠️ **IMPORTANT DISCLAIMERS:**

1. **Financial Risk**: Cryptocurrency trading involves substantial risk of loss
2. **Testnet First**: Always test thoroughly on testnet before live trading
3. **API Security**: Keep API keys secure and use IP restrictions
4. **Monitoring Required**: System requires active monitoring
5. **No Guarantees**: Past performance doesn't guarantee future results

## 🔧 Troubleshooting

### Common Issues

**"Qty invalid" Errors**
- ✅ Fixed in latest version with automatic quantity validation
- System automatically rounds quantities to meet exchange requirements

**Connection Failures**
```bash
# Check API credentials
python tests/test_bybit_connection.py

# Verify network connectivity
ping api-testnet.bybit.com
```

**Missing Dependencies**
```bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

### Debug Mode
Enable detailed logging:
```env
LOG_LEVEL=DEBUG
DEBUG_MODE=true
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is for educational and research purposes. The authors are not responsible for any financial losses incurred through the use of this system. Always:

- Test on testnet first
- Start with small amounts
- Monitor positions actively
- Understand the risks involved
- Comply with local regulations

## 📞 Support

For issues and questions:
- Check the [documentation](docs/)
- Review [troubleshooting](#troubleshooting) section
- Open an issue on GitHub

---

**Happy Trading! 🚀📈**