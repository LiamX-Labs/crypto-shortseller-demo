-- Multi-Asset Trading System Database Initialization
-- Create necessary tables for the trading system

-- Create schema for better organization
CREATE SCHEMA IF NOT EXISTS trading;

-- Set default search path
SET search_path TO trading, public;

-- Create trades table
CREATE TABLE IF NOT EXISTS trading.trades (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,  -- 'buy' or 'sell'
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    order_id VARCHAR(100) UNIQUE,
    exchange_order_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    strategy VARCHAR(50) DEFAULT 'ema_crossover',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP WITH TIME ZONE,
    pnl DECIMAL(20, 8) DEFAULT 0,
    fees DECIMAL(20, 8) DEFAULT 0,
    notes TEXT
);

-- Create positions table
CREATE TABLE IF NOT EXISTS trading.positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,  -- 'long' or 'short'
    size DECIMAL(20, 8) NOT NULL,
    avg_price DECIMAL(20, 8) NOT NULL,
    unrealized_pnl DECIMAL(20, 8) DEFAULT 0,
    realized_pnl DECIMAL(20, 8) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'open',  -- 'open', 'closed'
    opened_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP WITH TIME ZONE,
    stop_loss DECIMAL(20, 8),
    take_profit DECIMAL(20, 8),
    leverage INTEGER DEFAULT 1
);

-- Create market_data table for storing price data
CREATE TABLE IF NOT EXISTS trading.market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    open_price DECIMAL(20, 8) NOT NULL,
    high_price DECIMAL(20, 8) NOT NULL,
    low_price DECIMAL(20, 8) NOT NULL,
    close_price DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(20, 8) NOT NULL,
    interval VARCHAR(10) NOT NULL,  -- '1m', '5m', '1h', etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp, interval)
);

-- Create signals table for strategy signals
CREATE TABLE IF NOT EXISTS trading.signals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(20) NOT NULL,  -- 'long', 'short', 'close'
    strength DECIMAL(5, 4) DEFAULT 1.0,  -- Signal strength 0-1
    price DECIMAL(20, 8) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    strategy VARCHAR(50) DEFAULT 'ema_crossover',
    indicators JSONB,  -- Store indicator values
    executed BOOLEAN DEFAULT FALSE,
    execution_id INTEGER REFERENCES trading.trades(id)
);

-- Create account_balance table for tracking balance history
CREATE TABLE IF NOT EXISTS trading.account_balance (
    id SERIAL PRIMARY KEY,
    total_balance DECIMAL(20, 8) NOT NULL,
    available_balance DECIMAL(20, 8) NOT NULL,
    equity DECIMAL(20, 8) NOT NULL,
    margin_used DECIMAL(20, 8) DEFAULT 0,
    unrealized_pnl DECIMAL(20, 8) DEFAULT 0,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create risk_metrics table
CREATE TABLE IF NOT EXISTS trading.risk_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    total_pnl DECIMAL(20, 8) DEFAULT 0,
    max_drawdown DECIMAL(10, 4) DEFAULT 0,
    win_rate DECIMAL(5, 4) DEFAULT 0,
    profit_factor DECIMAL(10, 4) DEFAULT 0,
    sharpe_ratio DECIMAL(10, 4) DEFAULT 0,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    UNIQUE(date)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_trades_symbol_timestamp ON trading.trades(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trading.trades(status);
CREATE INDEX IF NOT EXISTS idx_positions_symbol_status ON trading.positions(symbol, status);
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp ON trading.market_data(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_market_data_interval ON trading.market_data(interval);
CREATE INDEX IF NOT EXISTS idx_signals_symbol_timestamp ON trading.signals(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_signals_executed ON trading.signals(executed);

-- Grant permissions to trading user
GRANT ALL PRIVILEGES ON SCHEMA trading TO trading_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA trading TO trading_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA trading TO trading_user;

-- Insert initial data (optional)
INSERT INTO trading.account_balance (total_balance, available_balance, equity) 
VALUES (10000.00, 10000.00, 10000.00) 
ON CONFLICT DO NOTHING;

-- Create a view for active positions
CREATE OR REPLACE VIEW trading.active_positions AS
SELECT 
    p.*,
    (SELECT COUNT(*) FROM trading.trades t WHERE t.symbol = p.symbol AND t.timestamp > p.opened_at) as trade_count
FROM trading.positions p 
WHERE p.status = 'open';

-- Create a view for daily performance
CREATE OR REPLACE VIEW trading.daily_performance AS
SELECT 
    DATE(timestamp) as trade_date,
    COUNT(*) as total_trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
    SUM(pnl) as total_pnl,
    AVG(pnl) as avg_pnl,
    MAX(pnl) as max_win,
    MIN(pnl) as max_loss
FROM trading.trades 
WHERE status = 'filled' 
GROUP BY DATE(timestamp)
ORDER BY trade_date DESC;

-- Add comments for documentation
COMMENT ON TABLE trading.trades IS 'All executed trades with their details';
COMMENT ON TABLE trading.positions IS 'Current and historical positions';
COMMENT ON TABLE trading.market_data IS 'Historical price data for analysis';
COMMENT ON TABLE trading.signals IS 'Trading signals generated by strategies';
COMMENT ON TABLE trading.account_balance IS 'Account balance history';
COMMENT ON TABLE trading.risk_metrics IS 'Daily risk and performance metrics';