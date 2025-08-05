#!/usr/bin/env python3
"""
Multi-Asset Short Trading System - Main Entry Point
Automated trading system for BTC, ETH, SOL using EMA crossover signals
"""

import asyncio
import logging
import logging.handlers
import signal
import sys
import os
import fcntl
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from src.core.strategy_engine import MultiAssetStrategyEngine, MarketData
from src.exchange.bybit_client import BybitClient
from src.notifications.telegram_bot import telegram_bot, notify_trade_entry, notify_trade_exit, send_daily_report, notify_regime_change

# Configure logging with daily rotation (UTC+0)
def setup_logging():
    """Setup logging with daily rotation using UTC+0 timezone"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.log_level))
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Custom formatter with UTC timezone
    class UTCFormatter(logging.Formatter):
        def formatTime(self, record, datefmt=None):
            dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
            if datefmt:
                return dt.strftime(datefmt)
            return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    formatter = UTCFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Daily rotating file handler (rotates at midnight UTC)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename='logs/trading.log',
        when='midnight',
        interval=1,
        backupCount=30,  # Keep 30 days of logs
        utc=True  # Use UTC for rotation timing
    )
    file_handler.setFormatter(formatter)
    file_handler.suffix = '%Y%m%d'  # Format: trading.log.20250805
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Setup logging
setup_logging()

logger = logging.getLogger(__name__)

class MultiAssetTradingSystem:
    def __init__(self):
        self.strategy_engine = MultiAssetStrategyEngine()
        self.bybit_client = BybitClient()
        self.running = False
        self.assets = settings.get_asset_symbols()
        self.lock_file = None
        self.last_daily_reset = None
        self.account_balance = 0.0  # Cache balance from session startup
        
    async def initialize_system(self):
        """Initialize the trading system"""
        logger.info("🚀 MULTI-ASSET TRADING SYSTEM STARTING")
        logger.info(f"Version: 2.0.0")
        logger.info(f"Testnet Mode: {settings.exchange.testnet}")
        logger.info(f"Assets: {', '.join(self.assets)}")
        
        try:
            # Test exchange connection and cache account balance
            balance_info = await self.bybit_client.get_account_balance()
            if balance_info and 'list' in balance_info:
                for account in balance_info['list']:
                    for coin in account.get('coin', []):
                        if coin.get('coin') == 'USDT':
                            self.account_balance = float(coin.get('walletBalance', 0))
                            break
            else:
                self.account_balance = 10000.0  # Default for testing
            
            logger.info("✅ Exchange connection established")
            logger.info(f"💰 Session Balance: ${self.account_balance:,.2f} USDT")
            
            # Test Telegram connection
            if settings.telegram.enabled:
                telegram_connected = await telegram_bot.test_connection()
                if telegram_connected:
                    logger.info("📱 Telegram bot connected")
                else:
                    logger.warning("⚠️ Telegram bot connection failed")
            else:
                logger.info("📱 Telegram notifications disabled")
            
            # Initialize instrument specifications and set leverage for all assets
            for asset in self.assets:
                symbol = f"{asset}USDT"
                try:
                    # Fetch instrument specifications
                    await self.bybit_client.get_instrument_info(symbol)
                    logger.info(f"✅ {asset}: Instrument specifications loaded")
                    
                    # Set leverage
                    await self.bybit_client.set_leverage(symbol, "10", "10")
                    logger.info(f"✅ {asset}: Leverage set to 10x")
                except Exception as e:
                    logger.warning(f"⚠️ {asset}: Failed to set leverage: {e}")
            
            # Initialize positions
            await self.sync_positions()
            
            logger.info("🎯 System initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            return False
    
    async def sync_positions(self):
        """Synchronize positions with exchange"""
        try:
            for asset in self.assets:
                symbol = f"{asset}USDT"
                positions = await self.bybit_client.get_positions(symbol)
                
                for position in positions:
                    if float(position.get('size', 0)) != 0:
                        self.strategy_engine.update_position(
                            asset=asset,
                            in_position=True,
                            entry_price=float(position.get('avgPrice', 0)),
                            asset_amount=float(position.get('size', 0)),
                            leveraged_value=float(position.get('positionValue', 0))
                        )
                        logger.info(f"📊 {asset}: Synced existing position - Size: {position.get('size')}")
        
        except Exception as e:
            logger.error(f"Failed to sync positions: {e}")
    
    def get_next_5min_close_time(self) -> datetime:
        """Calculate next 5-minute bar close time"""
        now = datetime.now(timezone.utc)
        # Round to next 5-minute interval
        minutes = now.minute
        next_5min = ((minutes // 5) + 1) * 5
        
        if next_5min >= 60:
            next_hour = now.hour + 1
            next_minute = 0
            if next_hour >= 24:
                next_day = now.day + 1
                next_hour = 0
                next_close = now.replace(day=next_day, hour=next_hour, minute=next_minute, second=0, microsecond=0)
            else:
                next_close = now.replace(hour=next_hour, minute=next_minute, second=0, microsecond=0)
        else:
            next_close = now.replace(minute=next_5min, second=0, microsecond=0)
        
        return next_close
    
    async def wait_for_next_5min_close(self):
        """Wait until the next 5-minute bar closes"""
        next_close = self.get_next_5min_close_time()
        now = datetime.now(timezone.utc)
        sleep_seconds = (next_close - now).total_seconds()
        
        if sleep_seconds > 0:
            logger.info(f"⏰ Waiting {sleep_seconds:.0f}s for next 5-min bar close at {next_close.strftime('%H:%M:%S')}")
            await asyncio.sleep(sleep_seconds)
        
        # Wait an additional 2 seconds to ensure the bar is fully closed and available
        await asyncio.sleep(2)
        logger.info("📊 5-minute bar closed - processing signals...")
    
    async def get_market_data(self, asset: str) -> MarketData:
        """Get current market data for asset with 5-minute bars"""
        try:
            symbol = f"{asset}USDT"
            
            # Get 5-minute klines for EMA calculation (need enough for 600 EMA)
            klines = await self.bybit_client.get_klines(symbol, '5', 1000)
            
            if not klines or len(klines) < 600:
                raise ValueError(f"Insufficient 5-minute bar data for {asset} - need 600+ bars, got {len(klines)}")
            
            # Bybit returns klines in reverse chronological order (newest first)
            # Format: [startTime, openPrice, highPrice, lowPrice, closePrice, volume, turnover]
            closes = [float(kline[4]) for kline in reversed(klines)]  # Reverse to get chronological order
            
            # Verify we have proper 5-minute intervals
            latest_bar_time = int(klines[0][0])  # Most recent bar timestamp
            current_time_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
            
            # Check if latest bar is within last 5 minutes (allowing some delay)
            time_diff_minutes = (current_time_ms - latest_bar_time) / (1000 * 60)
            if time_diff_minutes > 10:  # More than 10 minutes old
                logger.warning(f"{asset}: Latest 5-min bar is {time_diff_minutes:.1f} minutes old")
            
            # Use the close price of the most recent completed bar
            current_price = closes[-1]  # Last close price from completed bars
            
            # Calculate EMAs using completed bars only (exclude current incomplete bar if any)
            ema_240 = self.calculate_ema(closes, 240)
            ema_600 = self.calculate_ema(closes, 600)
            
            # Get volume from latest completed bar
            volume = float(klines[0][5])  # Volume of most recent bar
            
            logger.debug(f"{asset}: Processed {len(closes)} 5-min bars - "
                        f"Price: ${current_price:.4f}, EMA240: ${ema_240:.4f}, EMA600: ${ema_600:.4f}")
            
            return MarketData(
                asset=asset,
                price=current_price,
                ema_240=ema_240,
                ema_600=ema_600,
                volume=volume,
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Failed to get market data for {asset}: {e}")
            raise
    
    def calculate_ema(self, prices: list, period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return sum(prices) / len(prices)  # Fallback to SMA if not enough data
        
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period  # Start with SMA
        
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    async def execute_signal(self, signal):
        """Execute trading signal with real-time balance validation"""
        try:
            if signal.signal_type.value != 'ENTER_SHORT':
                return
            
            asset = signal.asset
            symbol = f"{asset}USDT"
            
            # Get real-time account balance for trade validation
            logger.info(f"🔍 {asset}: Checking account balance for trade validation")
            balance_info = await self.bybit_client.get_account_balance()
            current_balance = self.account_balance  # Default to cached balance
            
            if balance_info and 'list' in balance_info:
                for account in balance_info['list']:
                    for coin in account.get('coin', []):
                        if coin.get('coin') == 'USDT':
                            current_balance = float(coin.get('walletBalance', 0))
                            break
            
            logger.info(f"💰 {asset}: Current balance for validation: ${current_balance:,.2f} USDT")
            
            # Calculate position size (7% of balance with 10x leverage)
            allocation_pct = settings.risk.per_asset_allocation_pct
            leverage = settings.risk.leverage_per_asset
            
            position_value = current_balance * allocation_pct
            leveraged_value = position_value * leverage
            
            # Round leveraged value to 2 decimal places for USDT precision
            leveraged_value = round(leveraged_value, 2)
            
            # Calculate quantity based on current price
            raw_quantity = leveraged_value / signal.price
            
            logger.info(f"🔢 {asset}: Target USDT value: ${leveraged_value:.2f}")
            logger.info(f"   Position value: ${position_value:.2f}, Leveraged: ${leveraged_value:.2f}")
            logger.info(f"   Price: ${signal.price:.4f}, Raw quantity: {raw_quantity:.8f}")
            
            # Get corrected quantity that meets exchange requirements
            corrected_quantity = self.bybit_client.calculate_quantity_for_usdt_value(symbol, leveraged_value, signal.price)
            
            if corrected_quantity <= 0:
                logger.error(f"❌ {asset}: Could not calculate valid quantity for ${leveraged_value:.2f} USDT")
                return
            
            # Validate final quantity
            validation = self.bybit_client.validate_order_params(symbol, corrected_quantity, signal.price)
            
            if not validation['valid']:
                logger.error(f"❌ {asset}: Order validation failed: {'; '.join(validation['errors'])}")
                return
            
            asset_quantity = validation['corrected_qty']
            final_usdt_value = asset_quantity * signal.price
            
            logger.info(f"📏 {asset}: Final quantity: {asset_quantity:.8f}")
            logger.info(f"   Final USDT value: ${final_usdt_value:.2f}")
            
            # Calculate stop loss and take profit
            stop_loss_price = signal.price * (1 + settings.risk.stop_loss_pct)  # 1.5% above entry
            take_profit_price = signal.price * (1 - settings.risk.take_profit_pct)  # 6% below entry
            
            # Attempt to place order with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"🎯 {asset}: Placing order attempt {attempt + 1}/{max_retries}")
                    
                    # Place short order
                    result = await self.bybit_client.place_order(
                        symbol=symbol,
                        side='Sell',
                        order_type='Market',
                        qty=asset_quantity,
                        stop_loss=stop_loss_price,
                        take_profit=take_profit_price
                    )
                    
                    # If successful, break out of retry loop
                    break
                    
                except Exception as order_error:
                    logger.error(f"❌ {asset}: Order attempt {attempt + 1} failed: {order_error}")
                    
                    if attempt == max_retries - 1:
                        # Final attempt failed
                        raise order_error
                    
                    # Wait before retry
                    await asyncio.sleep(1)
                    
                    # Re-fetch instrument specs in case they changed
                    await self.bybit_client.get_instrument_info(symbol)
                    
                    # Re-validate with updated specs
                    validation = self.bybit_client.validate_order_params(symbol, raw_quantity, signal.price)
                    if validation['valid']:
                        asset_quantity = validation['corrected_qty']
                    else:
                        logger.error(f"❌ {asset}: Validation still failed after retry: {'; '.join(validation['errors'])}")
                        return
            
            # Update position tracking
            self.strategy_engine.update_position(
                asset=asset,
                in_position=True,
                entry_price=signal.price,
                asset_amount=asset_quantity,
                leveraged_value=leveraged_value
            )
            
            logger.info(f"🎯 {asset}: SHORT position opened")
            logger.info(f"   Price: ${signal.price:.4f}")
            logger.info(f"   Quantity: {asset_quantity:.6f}")
            logger.info(f"   Value: ${leveraged_value:.2f}")
            logger.info(f"   Stop Loss: ${stop_loss_price:.4f}")
            logger.info(f"   Take Profit: ${take_profit_price:.4f}")
            
            # Send Telegram notification
            if settings.telegram.enabled:
                try:
                    await notify_trade_entry(
                        asset=asset,
                        price=signal.price,
                        metadata={
                            'ema_240': signal.metadata.get('ema_240') if signal.metadata else 0,
                            'ema_600': signal.metadata.get('ema_600') if signal.metadata else 0,
                            'regime': signal.metadata.get('regime') if signal.metadata else 'ACTIVE',
                            'stop_loss_pct': settings.risk.stop_loss_pct * 100,
                            'take_profit_pct': settings.risk.take_profit_pct * 100,
                            'quantity': asset_quantity,
                            'leveraged_value': leveraged_value
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to send Telegram entry notification: {e}")
            
        except Exception as e:
            logger.error(f"Failed to execute signal for {signal.asset}: {e}")
    
    async def check_position_exits(self):
        """Check and execute position exits"""
        try:
            for asset in self.assets:
                if not self.strategy_engine.asset_positions[asset]['in_position']:
                    continue
                
                symbol = f"{asset}USDT"
                
                # Get current market data for regime information
                market_data = await self.get_market_data(asset)
                current_price = market_data.price
                current_regime = self.strategy_engine.determine_market_regime(market_data)
                
                # Check exit conditions
                should_exit, exit_reason = self.strategy_engine.should_exit_position(
                    asset, current_price, datetime.now(timezone.utc), current_regime
                )
                
                if should_exit:
                    try:
                        # Close position
                        await self.bybit_client.close_position(symbol)
                        
                        # Get position data for P&L calculation
                        position_data = self.strategy_engine.asset_positions[asset]
                        entry_price = position_data['entry_price']
                        entry_time = position_data['entry_time']
                        
                        # Calculate P&L (for short: profit when price goes down)
                        pnl = (entry_price - current_price) * position_data['asset_amount']
                        pnl_pct = ((entry_price - current_price) / entry_price) * 100
                        
                        # Calculate hold time
                        hold_time = 'N/A'
                        if entry_time:
                            time_held = datetime.now(timezone.utc) - entry_time
                            hours = int(time_held.total_seconds() // 3600)
                            minutes = int((time_held.total_seconds() % 3600) // 60)
                            hold_time = f"{hours}h {minutes}m"
                        
                        # Update position tracking
                        self.strategy_engine.update_position(asset, False)
                        
                        # Apply quick exit cooldown if trade was closed quickly (< 60 minutes)
                        if entry_time:
                            trade_duration_minutes = (datetime.now(timezone.utc) - entry_time).total_seconds() / 60
                            cooldown_applied = self.strategy_engine.apply_quick_exit_cooldown(asset, trade_duration_minutes)
                            if cooldown_applied:
                                logger.info(f"🕒 {asset}: Quick exit cooldown activated - {trade_duration_minutes:.1f}min trade")
                        
                        logger.info(f"🏁 {asset}: Position closed at ${current_price:.4f}")
                        logger.info(f"   P&L: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
                        
                        # Send Telegram notification
                        if settings.telegram.enabled:
                            try:
                                await notify_trade_exit(
                                    asset=asset,
                                    price=current_price,
                                    metadata={
                                        'entry_price': entry_price,
                                        'pnl': pnl,
                                        'pnl_pct': pnl_pct,
                                        'exit_reason': exit_reason,
                                        'hold_time': hold_time
                                    }
                                )
                            except Exception as e:
                                logger.error(f"Failed to send Telegram exit notification: {e}")
                        
                    except Exception as e:
                        logger.error(f"Failed to close position for {asset}: {e}")
                        
        except Exception as e:
            logger.error(f"Error checking position exits: {e}")
    
    async def send_daily_status_update(self, portfolio_summary: Dict[str, Any]):
        """Send daily status update to Telegram"""
        if not settings.telegram.enabled:
            return
        
        try:
            # Calculate daily P&L (simplified - would need historical data for accuracy)
            daily_pnl = 0  # This would need to be calculated from database
            total_trades = 0  # This would need to be calculated from database
            
            status_data = {
                'balance': self.account_balance,  # Use cached session balance
                'active_positions': portfolio_summary['active_positions'],
                'daily_pnl': daily_pnl,
                'total_trades': total_trades,
                'assets_status': portfolio_summary['assets_status']
            }
            
            await send_daily_report(status_data)
            logger.info("📱 Daily status update sent to Telegram")
            
        except Exception as e:
            logger.error(f"Failed to send daily status update: {e}")
    
    async def check_daily_reset(self):
        """Check if daily reset is needed at 00:01 UTC"""
        now_utc = datetime.now(timezone.utc)
        current_date = now_utc.date()
        
        # Check if we need to perform daily reset (at 00:01 UTC)
        if (self.last_daily_reset is None or 
            self.last_daily_reset != current_date and 
            now_utc.hour == 0 and now_utc.minute >= 1):
            
            logger.info("🕐 Daily reset time reached (00:01 UTC) - Performing daily maintenance")
            
            # Reset daily cross counts
            self.strategy_engine.reset_daily_cross_counts()
            
            # Clean up old cross events (keep last 24 hours)
            self.strategy_engine.cleanup_old_cross_events(hours_to_keep=24)
            
            # Update last reset date
            self.last_daily_reset = current_date
            
            # Send daily summary report
            try:
                portfolio_summary = self.strategy_engine.get_portfolio_summary()
                await self.send_daily_status_update(portfolio_summary)
                logger.info("📊 Daily summary report sent")
            except Exception as e:
                logger.error(f"Failed to send daily summary: {e}")
            
            logger.info("✅ Daily reset completed successfully")
    
    async def main_loop(self):
        """Main trading loop - processes on 5-minute bar closes"""
        logger.info("📈 Starting main trading loop - Processing every 5-minute bar close")
        
        # Wait for first 5-minute bar close before starting
        await self.wait_for_next_5min_close()
        
        while self.running:
            try:
                current_time = datetime.now(timezone.utc).strftime('%H:%M:%S')
                logger.info(f"🕐 {current_time} - Processing 5-minute bar close for all assets")
                
                # Check for daily reset at 00:01 UTC
                await self.check_daily_reset()
                
                # Process each asset on the 5-minute bar close
                signals = {}
                for asset in self.assets:
                    try:
                        market_data = await self.get_market_data(asset)
                        signal = self.strategy_engine.generate_asset_signal(market_data)
                        signals[asset] = signal
                        
                        # Check for regime changes
                        regime_change = self.strategy_engine.check_regime_change(market_data)
                        if regime_change['changed'] and settings.telegram.enabled:
                            try:
                                await notify_regime_change(
                                    asset=regime_change['asset'],
                                    price=regime_change['price'],
                                    previous_regime=regime_change['previous_regime'],
                                    current_regime=regime_change['current_regime'],
                                    ema_240=regime_change['ema_240'],
                                    ema_600=regime_change['ema_600']
                                )
                                logger.info(f"📱 {asset}: Regime change notification sent - {regime_change['previous_regime']} → {regime_change['current_regime']}")
                            except Exception as e:
                                logger.error(f"Failed to send regime change notification for {asset}: {e}")
                        
                        # Log market data analysis
                        regime = self.strategy_engine.current_regimes.get(asset, 'UNKNOWN')
                        logger.info(f"📊 {asset}: ${market_data.price:.2f} | EMA240: ${market_data.ema_240:.2f} | "
                                  f"EMA600: ${market_data.ema_600:.2f} | Regime: {regime} | Signal: {signal.signal_type.value}")
                        
                        if signal.reason and signal.signal_type.value != 'NO_ACTION':
                            logger.info(f"   Reason: {signal.reason}")
                        
                    except Exception as e:
                        logger.error(f"Error processing {asset}: {e}")
                        signals[asset] = None
                
                # Execute valid signals
                executed_trades = 0
                for asset, signal in signals.items():
                    if signal and signal.signal_type.value == 'ENTER_SHORT':
                        try:
                            await self.execute_signal(signal)
                            executed_trades += 1
                        except Exception as e:
                            logger.error(f"Failed to execute trade for {asset}: {e}")
                
                # Check for position exits
                await self.check_position_exits()
                
                # Portfolio summary
                portfolio_summary = self.strategy_engine.get_portfolio_summary()
                logger.info(f"📊 Portfolio Summary: {portfolio_summary['active_positions']} active positions")
                
                if portfolio_summary['active_positions'] > 0:
                    logger.info(f"   Total Exposure: ${portfolio_summary['total_exposure']:.2f}")
                    for asset, status in portfolio_summary['assets_status'].items():
                        if status['in_position']:
                            logger.info(f"   {asset}: POSITION ACTIVE")
                
                if executed_trades > 0:
                    logger.info(f"🎯 Executed {executed_trades} new trades this bar")
                
                # Send daily status update at market open times (Tokyo: 00:00, London: 08:00, NYSE: 14:30 UTC)
                current_time = datetime.now(timezone.utc)
                current_hour = current_time.hour
                current_minute = current_time.minute
                
                # Market open times in UTC: Tokyo 00:00, London 08:00, NYSE 14:30
                market_open_times = [
                    (0, 0),    # Tokyo: 00:00 UTC (09:00 JST)
                    (8, 0),    # London: 08:00 UTC (09:00 BST/08:00 GMT)
                    (14, 30)   # NYSE: 14:30 UTC (09:30 EST/EDT)
                ]
                
                if (current_hour, current_minute) in market_open_times and settings.telegram.enabled:
                    market_names = {(0, 0): "Tokyo", (8, 0): "London", (14, 30): "NYSE"}
                    market_name = market_names.get((current_hour, current_minute), "Market")
                    logger.info(f"📊 {market_name} market open - sending status update")
                    await self.send_daily_status_update(portfolio_summary)
                
                # Wait for next 5-minute bar close
                await self.wait_for_next_5min_close()
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(10)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
        self.running = False
    
    def acquire_lock(self):
        """Acquire a file lock to prevent multiple instances"""
        try:
            self.lock_file = open('/tmp/multi_asset_trading.lock', 'w')
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_file.write(str(os.getpid()))
            self.lock_file.flush()
            return True
        except IOError:
            logger.error("🔒 Another instance of the trading system is already running")
            return False

    def release_lock(self):
        """Release the file lock"""
        if self.lock_file:
            try:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                self.lock_file.close()
                os.unlink('/tmp/multi_asset_trading.lock')
            except:
                pass

    async def run(self):
        """Run the trading system"""
        # Acquire lock to prevent multiple instances
        if not self.acquire_lock():
            return
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # Initialize system
            if not await self.initialize_system():
                logger.error("System initialization failed")
                return
            
            self.running = True
            
            # Start main loop
            await self.main_loop()
            
        except Exception as e:
            logger.error(f"System error: {e}")
        finally:
            self.release_lock()
            logger.info("🔴 Multi-Asset Trading System stopped")

async def main():
    """Main entry point"""
    system = MultiAssetTradingSystem()
    await system.run()

if __name__ == "__main__":
    asyncio.run(main())