# Multi-Asset Short Trading System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Bybit API V5](https://img.shields.io/badge/Bybit-API%20V5-orange.svg)](https://bybit-exchange.github.io/docs/v5/intro)

A sophisticated automated cryptocurrency trading system that executes short positions on Bitcoin (BTC), Ethereum (ETH), and Solana (SOL) using EMA crossover signals with advanced risk management, regime-based exits, cooldown mechanisms, and real-time notifications.

## 🚀 Features

### Core Trading System
- **Multi-Asset Trading**: Simultaneous trading across BTC, ETH, and SOL
- **EMA Crossover Strategy**: Uses 240/600 EMA crossovers for signal generation
- **Real-time Processing**: Live market data analysis on 5-minute bar intervals
- **Precision Order Management**: Automatic quantity validation and rounding

### Advanced Risk Management
- **Dynamic Position Sizing**: 7% allocation per asset with 10x leverage
- **Multi-Level Exit Strategy**: Stop-loss (1.5%), take-profit (6%), time-based (24h)
- **Regime-Based Exits**: Automatic position closure when market conditions deteriorate
- **Quick Exit Cooldown**: 1-hour trading pause after positions closed within 60 minutes
- **Daily Cross Limits**: Maximum 12 EMA crosses per asset per day

### Market Analysis & Intelligence
- **Market Regime Detection**: ACTIVE/INACTIVE states based on price-EMA positioning
- **Real-time Notifications**: Regime changes, trade entries/exits, cooldown status
- **Trade Duration Tracking**: Complete position lifecycle monitoring without exchange queries
- **Portfolio Analytics**: Comprehensive exposure and performance tracking

### Notifications & Monitoring
- **Telegram Integration**: Professional trading notifications with technical analysis
- **Status Reporting**: Daily portfolio summaries with regime and cooldown status
- **Alert System**: 15-minute cooldowns prevent notification spam
- **Error Recovery**: Robust retry logic and comprehensive error handling

### Exchange Integration
- **Bybit V5 API**: Full support with testnet/demo/live environments
- **Order Precision**: Automatic compliance with exchange quantity requirements
- **Connection Resilience**: Built-in retry mechanisms and connection monitoring

## 📋 How The System Works

### 1. Market Data Processing
The system continuously monitors market data on 5-minute intervals:
- **Data Collection**: Real-time price, volume, and EMA calculations from Bybit
- **EMA Calculation**: 240-period (20 hours) and 600-period (50 hours) EMAs
- **Cross Detection**: Identifies when price crosses below EMAs or EMAs cross each other

### 2. Market Regime Analysis
**ACTIVE Regime** (Favorable for shorting):
- Price < EMA240 < EMA600 (perfect bearish alignment)
- System actively looks for short entry opportunities

**INACTIVE Regime** (Unfavorable for shorting):
- Price above one or both EMAs
- Existing positions automatically closed via regime-based exit
- New positions blocked until regime becomes ACTIVE again

### 3. Signal Generation & Entry Logic
**Entry Requirements** (ALL must be met):
- ✅ Market regime is ACTIVE
- ✅ Price crossed below EMA240 or EMA600 recently (within 15 minutes)
- ✅ Asset not currently in position
- ✅ Asset not in cooldown period
- ✅ Daily cross limit not exceeded (< 12 crosses per day)

**Position Sizing**:
- 7% of account balance allocated per asset
- 10x leverage applied (70% exposure per asset)
- Maximum 21% total exposure across all assets (3 × 7%)

### 4. Exit Strategy (Hierarchical Priority)
**1. Regime-Based Exit** (Highest Priority):
- Immediate closure when regime changes from ACTIVE → INACTIVE
- Protects against holding positions in unfavorable conditions

**2. Time-Based Exit**:
- Maximum 24-hour hold time per position
- Prevents indefinite position holding

**3. Stop Loss**:
- 1.5% loss threshold above entry price (for shorts)
- Risk management safety net

**4. Take Profit**:
- 6% profit target below entry price (for shorts)
- Systematic profit realization

### 5. Cooldown Mechanisms
**Quick Exit Cooldown**:
- Triggered when positions closed within 60 minutes
- 1-hour trading pause for that specific asset
- Prevents overtrading and poor timing patterns

**Alert Cooldowns**:
- 15-minute minimum between similar notifications
- Prevents notification spam during volatile periods

### 6. Real-time Monitoring & Notifications
**Telegram Notifications**:
- 📊 **Regime Changes**: ACTIVE ↔ INACTIVE transitions with technical context
- 🎯 **Trade Entries**: Complete setup analysis with EMA values and reasoning  
- 🏁 **Trade Exits**: P&L results, hold time, and exit reason
- 🕒 **Cooldown Status**: When assets enter/exit cooldown periods
- 📈 **Daily Reports**: Portfolio status, regime summary, active cooldowns

**Status Tracking**:
- Trade duration monitoring without exchange API calls
- Portfolio exposure and risk metrics
- Cross frequency and cooldown status per asset

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
│   (Bybit API)   │    │ (Multi-Asset)    │    │ (Position Mgmt) │
│  • 5min bars    │    │ • EMA Analysis   │    │ • Quantity Val. │
│  • Real-time    │    │ • Regime Detect  │    │ • Order Exec.   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       │
         │                        ▼                       │
         │              ┌──────────────────┐              │
         │              │ Cooldown Manager │              │
         │              │ • Quick Exit     │              │
         │              │ • Alert Limits   │              │
         │              │ • Cross Tracking │              │
         │              └──────────────────┘              │
         │                        │                       │
         ▼                        ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Store    │    │   Notifications  │    │   Risk Manager  │
│ (PostgreSQL)    │    │  (Telegram Bot)  │    │ • Regime Exits  │
│ • Trades        │    │ • Regime Changes │    │ • Stop Loss     │
│ • Performance   │    │ • Trade Updates  │    │ • Take Profit   │
│ • Metrics       │    │ • Daily Reports  │    │ • Time Limits   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Data Flow
1. **Market Data**: 5-minute bars collected from Bybit API
2. **EMA Calculation**: 240/600 period EMAs computed in real-time  
3. **Regime Detection**: Price-EMA positioning determines market state
4. **Signal Generation**: Entry/exit signals generated based on multiple criteria
5. **Cooldown Checks**: Quick exit and alert cooldowns prevent overtrading
6. **Risk Management**: Multi-level exit strategy with regime-based priority
7. **Order Execution**: Precision-validated orders sent to exchange
8. **Notifications**: Real-time updates via Telegram with technical analysis
9. **Performance Tracking**: Trade duration, P&L, and portfolio metrics

## 📁 Project Structure

```
multiasset/
├── src/
│   ├── core/
│   │   └── strategy_engine.py     # Multi-asset strategy engine with regime detection
│   ├── exchange/
│   │   └── bybit_client.py        # Bybit V5 API integration with precision handling
│   ├── notifications/
│   │   └── telegram_bot.py        # Professional trading notifications
│   └── utils/
│       └── trade_duration_tracker.py # Trade duration analysis from logs
├── config/
│   └── settings.py                # Multi-asset configuration management
├── scripts/
│   └── start_trading.py           # Main trading system entry point
├── tests/
│   ├── test_quantity_validation.py   # Order precision validation tests
│   ├── test_bybit_connection.py      # Exchange connectivity tests
│   ├── test_telegram_integration.py  # Notification system tests
│   ├── test_trade_execution.py       # Trading logic tests
│   └── test_system_validation.py     # End-to-end system tests
├── logs/
│   └── multi_asset_*.log          # Daily rotating logs with trade history
├── data/                          # Historical data and performance metrics
├── docs/                          # Comprehensive system documentation
├── requirements.txt               # Python dependencies
├── docker-compose.yml            # Multi-service Docker configuration
├── init-db.sql                   # Database schema initialization
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git ignore rules (excludes docs/)
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

## 📈 Monitoring & Notifications

### Comprehensive Logging System
- **Daily Rotating Logs**: `logs/multi_asset_YYYY-MM-DD.log`
- **Trade Lifecycle**: Complete entry/exit tracking with durations
- **Performance Metrics**: P&L, win rates, hold times, cooldown events
- **System Health**: Connection status, error recovery, API response times

### Professional Telegram Integration
The system sends detailed, professional trading notifications:

**📊 Regime Change Alerts**:
```
📊 REGIME CHANGE ALERT 📈

🟢 BTC - FAVORABLE FOR SHORTING
💰 Current Price: $45,250.00
⏰ Time: 14:23:15 UTC

🔄 Regime Update:
• Previous: INACTIVE
• Current: ACTIVE

📈 Technical Context:
• EMA 240: $45,400.00
• EMA 600: $45,550.00
• Price Position: Below both EMAs

📝 Impact:
Market conditions now optimal for short position opportunities

🎯 Strategy Note:
Monitor for potential SHORT signals
```

**🎯 Trade Entry Notifications**:
```
🚨 TRADE SIGNAL ALERT 🚨

📊 BTC SHORT POSITION
💰 Entry Price: $42,350.75
⏰ Time: 10:45:30 UTC

📈 Technical Analysis:
• EMA 240: $42,400.25
• EMA 600: $42,450.50
• Market Regime: ACTIVE
• Bearish EMA Cross Confirmed ✅

🎯 Trade Setup:
• Direction: SHORT ⬇️
• Stop Loss: 1.5% ($43,005.01)
• Take Profit: 6.0% ($39,809.71)
• Risk/Reward: 1:4.0
```

**🏁 Trade Exit Notifications**:
```
🏁 POSITION CLOSED 🟢

📊 BTC SHORT POSITION
💰 Exit Price: $40,125.50
⏰ Time: 16:22:45 UTC

📈 Trade Summary:
• Entry Price: $42,350.75
• Exit Price: $40,125.50
• Hold Time: 5h 37m
• Exit Reason: Take Profit

💸 P&L Result:
• Absolute P&L: +$365.25 USDT
• Percentage: +5.25%
• Result: PROFIT 🟢
```

**📈 Daily Status Reports**:
```
📊 DAILY TRADING REPORT

💰 Portfolio Status:
• Account Balance: $10,247.83 USDT
• Active Positions: 1
• Daily P&L: +$125.50 USDT
• Total Trades Today: 3

📈 Market Regimes:
🟢 BTC: ACTIVE
🔴 ETH: INACTIVE
🟢 SOL: ACTIVE

🕒 Asset Cooldowns:
🕒 ETH: Quick Exit (23m remaining)

🎯 Strategy Update:
Multi-asset EMA crossover system running smoothly
Monitoring BTC, ETH, SOL for bearish signals
Following systematic approach with proper risk management
```

### Real-time System Monitoring
- **Trade Duration Tracking**: Position lifecycle without exchange API calls
- **Cooldown Status**: Quick exit and alert cooldown monitoring
- **Portfolio Analytics**: Real-time exposure, regime status, cross frequency
- **Performance Metrics**: Win rates, average hold times, profit factors

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
- ✅ Fixed with automatic precision validation and rounding
- System ensures all orders comply with exchange requirements
- Smart quantity calculation based on balance and leverage settings

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

## 🎯 System Highlights

This sophisticated multi-asset trading system provides:

- **🤖 Fully Automated Trading**: No manual intervention required
- **🧠 Intelligent Market Analysis**: Real-time regime detection and adaptation  
- **🛡️ Advanced Risk Management**: Multi-layered protection with regime-based exits
- **⏰ Smart Cooldown System**: Prevents overtrading and poor timing patterns
- **📱 Professional Notifications**: Comprehensive Telegram integration
- **📊 Complete Transparency**: Full trade lifecycle tracking and reporting
- **🔧 Enterprise-Grade**: Robust error handling and connection resilience

**Built for serious cryptocurrency traders who demand systematic, disciplined, and transparent automated trading with institutional-quality risk management.**

**Happy Trading! 🚀📈**