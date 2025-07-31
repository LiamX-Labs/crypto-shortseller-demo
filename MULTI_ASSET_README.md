# Multi-Asset Short Trading System

A sophisticated automated trading system for shorting Bitcoin, Ethereum, and Solana based on EMA crossover signals with advanced portfolio management, risk controls, and cooldown mechanisms.

## Features

- **Multi-Asset Strategy**: Simultaneous trading of BTC, ETH, SOL using 240/600 EMA crosses
- **Portfolio Management**: Unified 7% allocation per asset with coordinated risk management
- **Independent Regime Detection**: Asset-specific market condition analysis
- **Dynamic Position Sizing**: 7% of balance per asset with 10x leverage (210% total exposure)
- **Advanced Risk Management**: 
  - 1.5% stop loss per position
  - 6% take profit per position
  - Portfolio-level daily loss limits
  - Drawdown-based position reduction
- **Asset-Specific Cooldowns**: Independent anti-whipsaw protection per cryptocurrency
- **Real-time Execution**: Multi-asset WebSocket connections for instant market data
- **Portfolio Dashboard**: Real-time monitoring across all positions and assets
- **Comprehensive Notifications**: Multi-channel alerts for trades, risks, and system status
- **Graceful Shutdown**: Proper signal handling for containerized environments

## Architecture

```
multiasset-trading-system/
├── README.md
├── requirements.txt
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── config/
│   ├── __init__.py
│   ├── settings.py           # Global configuration
│   ├── strategy_params.py    # Multi-asset strategy parameters
│   ├── exchange_config.py    # Exchange API configurations
│   └── logging_config.py     # Logging setup
│
├── src/
│   ├── __init__.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── strategy_engine.py      # Multi-asset strategy execution
│   │   ├── position_manager.py     # Portfolio position tracking
│   │   ├── risk_manager.py         # Portfolio risk controls
│   │   ├── regime_detector.py      # Per-asset market regime analysis
│   │   └── cooldown_manager.py     # Multi-asset cooldown logic
│   │
│   ├── exchange/
│   │   ├── __init__.py
│   │   ├── base_exchange.py        # Abstract exchange interface
│   │   ├── bybit_client.py         # Bybit API for all assets
│   │   ├── order_manager.py        # Multi-asset order execution
│   │   └── market_data.py          # Real-time data feeds (BTC/ETH/SOL)
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── data_manager.py         # Multi-asset data collection
│   │   ├── indicators.py           # Technical indicators per asset
│   │   ├── database.py             # PostgreSQL operations
│   │   └── cache_manager.py        # Redis caching for portfolio data
│   │
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── performance_tracker.py  # Portfolio P&L and metrics
│   │   ├── alerting.py             # Multi-asset notification system
│   │   ├── dashboard.py            # Portfolio web dashboard
│   │   └── health_check.py         # System health monitoring
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py               # Enhanced logging utilities
│   │   ├── validators.py           # Input validation
│   │   ├── calculations.py         # Portfolio mathematical functions
│   │   └── helpers.py              # General utilities
│   │
│   └── api/
│       ├── __init__.py
│       ├── routes.py               # REST API endpoints
│       ├── websocket.py            # WebSocket handlers
│       └── auth.py                 # API authentication
│
├── scripts/
│   ├── deploy.sh                   # Multi-service deployment
│   ├── start_trading.py            # System startup
│   ├── stop_trading.py             # Graceful shutdown
│   ├── backup_data.py              # Portfolio data backup
│   └── migration.py                # Database migrations
│
├── tests/
│   ├── __init__.py
│   ├── test_multi_asset_strategy.py  # Multi-asset strategy tests
│   ├── test_portfolio_manager.py     # Portfolio management tests
│   ├── test_exchange.py              # Exchange integration tests
│   ├── test_risk_manager.py          # Risk management tests
│   └── fixtures/                     # Test data and fixtures
│
├── docs/
│   ├── setup.md                    # Installation guide
│   ├── configuration.md            # Multi-asset configuration guide
│   ├── api_reference.md            # API documentation
│   └── troubleshooting.md          # Common issues
│
├── logs/
│   ├── trading.log                 # Main trading logs
│   ├── errors.log                  # Error logs
│   ├── orders.log                  # Multi-asset order logs
│   ├── portfolio.log               # Portfolio-level events
│   └── system.log                  # System events
│
├── data/
│   ├── backups/                    # Database backups
│   ├── exports/                    # Trade exports
│   └── cache/                      # Redis cache files
│
└── deployment/
    ├── Dockerfile
    ├── kubernetes/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   └── configmap.yaml
    └── terraform/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

## Quick Start

### 1. Prerequisites

- Python 3.11 or higher
- Bybit API credentials (testnet recommended for testing)
- Docker and Docker Compose
- PostgreSQL 14+ and Redis 6+
- Minimum 8GB RAM for multi-asset processing

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd multiasset-trading-system

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

1. Copy the example configuration:
```bash
cp config/.env.example config/.env
```

2. Set up your API credentials:
```bash
# Option 1: Environment variables
export BYBIT_API_KEY="your-api-key"
export BYBIT_API_SECRET="your-api-secret"
export BYBIT_TESTNET="true"

# Database configuration
export POSTGRES_HOST="localhost"
export POSTGRES_DB="multiasset_trading"
export POSTGRES_USER="trading_user"
export POSTGRES_PASSWORD="secure_password"

export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export REDIS_DB="0"

# Option 2: .env file
echo "BYBIT_API_KEY=your-api-key" >> .env
echo "BYBIT_API_SECRET=your-api-secret" >> .env
echo "BYBIT_TESTNET=true" >> .env
```

3. Edit `config/strategy_params.py` to adjust multi-asset strategy parameters

4. (Optional) Set up Telegram notifications:
```bash
# Add Telegram bot token and chat ID to environment
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"

# Or add to .env file
echo "TELEGRAM_BOT_TOKEN=your-bot-token" >> .env
echo "TELEGRAM_CHAT_ID=your-chat-id" >> .env
```

### 4. Database Setup

```bash
# Start database services
docker-compose up -d postgres redis

# Run database migrations
python scripts/migration.py

# Verify database setup
python -c "from src.data.database import verify_connection; verify_connection()"
```

### 5. Running the System

#### Local Development
```bash
python scripts/start_trading.py --config config/development.yaml
```

#### Using Docker (Recommended)
```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs for all services
docker-compose logs -f

# View specific service logs
docker-compose logs -f trading-system
docker-compose logs -f postgres
docker-compose logs -f redis

# Stop the system
docker-compose down
```

#### Production Deployment
```bash
# Deploy to production
docker-compose -f docker-compose.prod.yml up -d

# Monitor system health
docker-compose exec trading-system python scripts/health_check.py
```

## Configuration Guide

### Multi-Asset Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `assets` | BTC,ETH,SOL | Trading pairs to monitor |
| `per_asset_allocation` | 0.07 | 7% of balance per asset |
| `leverage_per_asset` | 10 | 10x leverage per position |
| `max_portfolio_exposure` | 2.1 | 210% maximum total exposure |
| `stop_loss_pct` | 0.015 | 1.5% stop loss per position |
| `take_profit_pct` | 0.06 | 6% take profit per position |
| `cross_threshold_per_asset` | 12 | Max daily EMA crosses per asset |

### Portfolio Risk Management

The system implements multiple layers of portfolio risk management:

1. **Per-Asset Allocation**: 7% of balance allocated to each cryptocurrency
2. **Leverage Control**: 10x leverage per asset (configurable)
3. **Portfolio Exposure**: Maximum 210% of account balance (3 assets × 70%)
4. **Stop Loss**: Automatic 1.5% stop loss on every position
5. **Daily Loss Limit**: Stops trading after 5% portfolio daily loss
6. **Drawdown Protection**: Reduces positions at 15% drawdown, stops at 20%

### Asset-Specific Cooldown System

Prevents overtrading through intelligent per-asset cooldowns:

- **Quick Exit**: 1-hour cooldown per asset if position closes in < 1 hour
- **Loss Streak**: 2-hour cooldown per asset after 3 consecutive losses
- **High Frequency**: 30-min cooldown per asset if > 5 trades per hour
- **Daily Limit**: 4-hour cooldown per asset after 10 trades per day
- **Global Cooldown**: 4-hour system-wide pause on portfolio drawdown

## Portfolio Dashboard

Access the real-time portfolio dashboard at `http://localhost:8080` (when running locally).

### Dashboard Features

- **Portfolio Overview**: Combined P&L across all assets
- **Asset Performance**: Individual BTC, ETH, SOL performance
- **Risk Metrics**: Current exposure, drawdown, correlation analysis
- **Active Positions**: Real-time position monitoring
- **Trade History**: Complete audit trail of all executions
- **System Health**: Resource usage and connectivity status

### API Endpoints

- `GET /api/v1/portfolio/status` - Portfolio health and metrics
- `GET /api/v1/portfolio/positions` - All active positions
- `GET /api/v1/portfolio/performance` - Performance metrics
- `GET /api/v1/assets/{asset}/trades` - Asset-specific trade history
- `POST /api/v1/emergency-stop` - Emergency stop all trading
- `POST /api/v1/assets/{asset}/toggle` - Enable/disable asset trading

## Multi-Asset Notifications

The system supports comprehensive notifications across multiple channels.

### Setup

1. **Telegram Bot Setup** (Same as single-asset):
   - Message @BotFather on Telegram
   - Use `/newbot` command and follow instructions
   - Save the bot token and configure chat ID

2. **Discord Webhook** (Optional):
   - Create Discord webhook URL
   - Add to environment variables

### Enhanced Notification Types

- **Portfolio Startup**: System initialization with multi-asset status
- **Trade Signals**: Entry/exit signals with asset identification
- **Portfolio Updates**: Combined P&L and exposure metrics
- **Risk Alerts**: Portfolio-level and per-asset risk events
- **Correlation Alerts**: High correlation warnings between assets
- **System Health**: Multi-service status and performance alerts

### Portfolio Startup Notification Format
```
🚀 MULTI-ASSET SYSTEM STARTED

Version: 2.0.0
Portfolio Balance: $15,247.83
Total Exposure: 147.2% ($22,451.23)

📊 Asset Status:
• BTC: ACTIVE (Balance: $5,082.61)
• ETH: ACTIVE (Balance: $5,082.61) 
• SOL: COOLDOWN (Balance: $5,082.61)

Daily Crosses: BTC(4), ETH(2), SOL(7)
Started: 15:30:45 UTC

💼 Multi-Asset Portfolio Trading System
```

## API Setup

### Bybit Configuration for Multi-Asset

1. **Enhanced API Permissions**:
   - Read access for all assets
   - Trade permissions for BTCUSDT, ETHUSDT, SOLUSDT
   - Position and order management access
   - **No withdrawal permissions** (security best practice)

2. **Rate Limit Considerations**:
   - Multi-asset systems require higher rate limits
   - Configure request throttling in `config/exchange_config.py`
   - Monitor API usage across all assets

### Security Best Practices

- **Asset-Specific API Keys**: Use separate keys per asset if available
- **IP Whitelisting**: Whitelist production server IPs
- **Permission Minimization**: Only enable required permissions
- **Key Rotation**: Implement automated key rotation
- **Environment Isolation**: Separate testnet/mainnet configurations

## Monitoring

### Enhanced Logging

The system generates detailed logs across multiple dimensions:

- `logs/portfolio_YYYYMMDD.log` - Portfolio-level events and decisions
- `logs/btc_YYYYMMDD.log` - Bitcoin-specific trading activity  
- `logs/eth_YYYYMMDD.log` - Ethereum-specific trading activity
- `logs/sol_YYYYMMDD.log` - Solana-specific trading activity
- `logs/system_YYYYMMDD.log` - System health and performance
- `logs/errors_YYYYMMDD.log` - Error tracking and debugging

### Portfolio Performance Metrics

Track comprehensive portfolio performance:

- **Total Portfolio P&L**: Combined performance across all assets
- **Asset Attribution**: Individual contribution to portfolio returns  
- **Risk Metrics**: Portfolio volatility, Sharpe ratio, maximum drawdown
- **Correlation Analysis**: Inter-asset relationship monitoring
- **Exposure Tracking**: Real-time leverage and position sizing
- **Trade Efficiency**: Execution quality across all assets

### Grafana Dashboard (Production)

Production deployments include comprehensive monitoring:

1. **Access**: Grafana at `http://localhost:3000` (admin/admin)
2. **Dashboards**:
   - Portfolio Overview
   - Per-Asset Performance  
   - Risk Management Metrics
   - System Health & Resources
   - Trade Execution Analytics

## Troubleshooting

### Common Multi-Asset Issues

1. **Database Connection Errors**
   - Check PostgreSQL service status
   - Verify connection parameters in `.env`
   - Ensure database migrations completed

2. **Redis Cache Issues**
   - Verify Redis service is running
   - Check Redis connection parameters
   - Clear cache if corrupted: `redis-cli FLUSHDB`

3. **Asset-Specific Connection Problems**
   - Check API credentials and permissions
   - Verify network connectivity to Bybit
   - Review rate limiting configuration

4. **Portfolio Synchronization Issues**
   - Run position sync: `python scripts/sync_positions.py`
   - Check exchange vs. internal position discrepancies
   - Review portfolio state in database

5. **Memory/Performance Issues**
   - Monitor system resources for multi-asset processing
   - Adjust worker thread configuration
   - Consider vertical scaling for high-frequency operations

### Debug Mode

Run with enhanced debugging:
```bash
python scripts/start_trading.py --config config/development.yaml --log-level DEBUG --debug-assets BTC,ETH,SOL
```

### Asset-Specific Debugging

Debug individual assets:
```bash
# Debug only BTC trading
python scripts/start_trading.py --assets BTC --debug

# Debug ETH and SOL coordination  
python scripts/start_trading.py --assets ETH,SOL --debug
```

## Backtesting

Run comprehensive multi-asset backtests:

```bash
# Full portfolio backtest
python scripts/backtest.py --start 2024-01-01 --end 2024-12-31 --assets BTC,ETH,SOL

# Individual asset comparison
python scripts/backtest.py --start 2024-01-01 --end 2024-12-31 --compare-assets

# Portfolio optimization
python scripts/optimize_portfolio.py --start 2024-01-01 --end 2024-12-31
```

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Test specific components
pytest tests/test_multi_asset_strategy.py
pytest tests/test_portfolio_manager.py
pytest tests/test_risk_manager.py

# Integration tests
pytest tests/integration/ -v
```

### Code Quality

```bash
# Format code
black src/ tests/ scripts/

# Check style
flake8 src/ tests/ scripts/

# Type checking
mypy src/

# Security audit
bandit -r src/
```

### Performance Testing

```bash
# Load testing for multi-asset processing
python scripts/load_test.py --assets BTC,ETH,SOL --duration 300

# Memory profiling
python -m memory_profiler scripts/start_trading.py
```

## Production Deployment

### Recommended Infrastructure

#### Single-Server Deployment
- **CPU**: 4 cores minimum (2GHz+)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 100GB SSD for database and logs
- **Network**: Low-latency connection (<50ms to Bybit)
- **OS**: Ubuntu 22.04 LTS

#### High-Availability Deployment
- **Load Balancer**: NGINX with SSL termination
- **Application Servers**: 2+ instances for redundancy
- **Database**: PostgreSQL with streaming replication
- **Cache**: Redis Cluster for high availability
- **Monitoring**: Prometheus + Grafana + AlertManager

### Kubernetes Deployment

```bash
# Create namespace
kubectl create namespace multiasset-trading

# Deploy database services
kubectl apply -f deployment/kubernetes/database/

# Deploy trading system
kubectl apply -f deployment/kubernetes/

# Monitor deployment
kubectl get pods -n multiasset-trading -w

# View logs
kubectl logs -f deployment/trading-system -n multiasset-trading
```

### Security Hardening

```bash
# Server setup with security hardening
sudo apt update && sudo apt upgrade -y
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# Install fail2ban
sudo apt install fail2ban -y

# Configure automatic security updates
sudo apt install unattended-upgrades -y
```

## Risk Disclaimer

**IMPORTANT**: Multi-asset cryptocurrency trading involves substantial risk of loss and is not suitable for every investor. The simultaneous exposure to multiple volatile assets can amplify both gains and losses.

### Enhanced Risk Considerations

- **Correlation Risk**: During market stress, asset correlations can spike to 1.0
- **Leverage Risk**: 210% portfolio exposure amplifies all movements
- **System Risk**: Multi-asset complexity increases technical failure points
- **Liquidity Risk**: Simultaneous exits across assets may face slippage
- **Capital Requirements**: Minimum $10,000 recommended for effective diversification

### Usage Guidelines

- Always test thoroughly on testnet with all assets before live deployment
- Start with smaller position sizes to understand system behavior
- Monitor correlation metrics closely during volatile periods
- Maintain adequate reserves for margin calls across all positions
- Never risk more than you can afford to lose across the entire portfolio

## Contributing

Contributions to the multi-asset trading system are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/enhanced-portfolio-management`)
3. Make your changes with comprehensive tests
4. Add documentation for new features
5. Submit a pull request with detailed description

### Development Guidelines

- Follow existing code patterns for multi-asset processing
- Add tests for both individual assets and portfolio interactions
- Update documentation for configuration changes
- Consider performance implications of multi-asset operations

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check the `/docs` folder for detailed guides
- **Community**: Join our Discord server for multi-asset trading discussions
- **Professional Support**: Available for enterprise deployments

## Changelog

### v2.0.0 (Current)
- **New**: Multi-asset support for BTC, ETH, SOL
- **Enhanced**: Portfolio-level risk management and position coordination
- **Added**: Asset-specific cooldown mechanisms
- **Improved**: Database schema for multi-asset data storage
- **Added**: Comprehensive portfolio dashboard and monitoring
- **Enhanced**: Docker deployment with multi-service orchestration

### v2.0.1 (Planned)
- **Feature**: Additional cryptocurrency pairs (AVAX, MATIC, ADA)
- **Enhancement**: Machine learning regime detection
- **Improvement**: Advanced correlation analysis and hedging
- **Addition**: Options integration for portfolio hedging

---

**Portfolio Management**: Sophisticated multi-asset position coordination  
**Risk Control**: Enhanced portfolio-level risk management  
**Scalability**: Support for additional cryptocurrency pairs  
**Remember**: Diversification does not eliminate the risk of loss. Always practice responsible portfolio management and maintain adequate risk controls across all positions.