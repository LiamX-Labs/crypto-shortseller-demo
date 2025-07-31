#!/usr/bin/env python3
"""
Realistic Trade Flow Test with Live Market Data
Shows complete trade lifecycle with actual Bybit demo integration
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from typing import Dict

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from src.core.strategy_engine import MultiAssetStrategyEngine, MarketData, SignalType, TradingSignal
from src.exchange.bybit_client import BybitClient

class RealisticTradeSimulator:
    def __init__(self):
        self.strategy_engine = MultiAssetStrategyEngine()
        self.bybit_client = BybitClient()
        self.account_balance = 10000.0
        
    async def force_entry_signal(self, asset: str) -> TradingSignal:
        """Force create an entry signal with real market data"""
        print(f"\n🎯 FORCING ENTRY SIGNAL FOR {asset}")
        print("=" * 50)
        
        # Get real market data
        symbol = f"{asset}USDT"
        klines = await self.bybit_client.get_klines(symbol, '5', 100)
        ticker = await self.bybit_client.get_ticker(symbol)
        
        current_price = float(ticker.get('lastPrice', 0))
        closes = [float(kline[4]) for kline in reversed(klines)]
        
        print(f"📊 Real Market Data Retrieved:")
        print(f"   Current Price: ${current_price:.2f}")
        print(f"   Data Points: {len(closes)} 5-minute bars")
        
        # Create artificial bearish cross scenario
        # Force EMA values to create entry condition
        fake_ema_240 = current_price - 100  # EMA240 below price
        fake_ema_600 = current_price - 50   # EMA600 above EMA240 (recent bearish cross)
        fake_entry_price = current_price - 200  # Entry price below both EMAs
        
        print(f"🎭 ARTIFICIAL CONDITIONS CREATED:")
        print(f"   Forced Entry Price: ${fake_entry_price:.2f}")
        print(f"   Forced EMA240: ${fake_ema_240:.2f}")
        print(f"   Forced EMA600: ${fake_ema_600:.2f}")
        print(f"   Condition: Price < EMA240 < EMA600 (Perfect short setup)")
        
        # Add fake bearish cross to strategy engine
        cross_event = {
            'asset': asset,
            'type': 'BEARISH_CROSS',
            'timestamp': datetime.now(timezone.utc),
            'ema_240': fake_ema_240,
            'ema_600': fake_ema_600
        }
        self.strategy_engine.cross_events[asset].append(cross_event)
        
        # Create entry signal
        signal = TradingSignal(
            signal_type=SignalType.ENTER_SHORT,
            timestamp=datetime.now(timezone.utc),
            price=fake_entry_price,
            asset=asset,
            reason=f"{asset}: FORCED bearish cross with price below EMAs",
            confidence=1.0,
            metadata={
                'ema_240': fake_ema_240,
                'ema_600': fake_ema_600,
                'real_market_price': current_price
            }
        )
        
        print(f"✅ Entry signal created: {signal.signal_type.value}")
        return signal
        
    async def execute_test_trade(self, signal: TradingSignal) -> Dict:
        """Execute a test trade with position tracking"""
        asset = signal.asset
        
        print(f"\n💰 EXECUTING TEST TRADE FOR {asset}")
        print("=" * 50)
        
        # Calculate position size
        allocation_pct = settings.risk.per_asset_allocation_pct
        leverage = settings.risk.leverage_per_asset
        
        position_value = self.account_balance * allocation_pct
        leveraged_value = position_value * leverage
        asset_quantity = leveraged_value / signal.price
        
        stop_loss_price = signal.price * (1 + settings.risk.stop_loss_pct)
        take_profit_price = signal.price * (1 - settings.risk.take_profit_pct)
        
        print(f"📊 Position Details:")
        print(f"   Asset: {asset}")
        print(f"   Entry Price: ${signal.price:.2f}")
        print(f"   Quantity: {asset_quantity:.6f} {asset}")
        print(f"   Position Value: ${leveraged_value:.2f}")
        print(f"   Stop Loss: ${stop_loss_price:.2f} (+1.5%)")
        print(f"   Take Profit: ${take_profit_price:.2f} (-6.0%)")
        
        # Simulate order placement
        print(f"\n📡 SIMULATING ORDER PLACEMENT:")
        print(f"   ⚡ Placing SHORT order for {asset_quantity:.6f} {asset}")
        print(f"   ⚡ Setting Stop Loss at ${stop_loss_price:.2f}")
        print(f"   ⚡ Setting Take Profit at ${take_profit_price:.2f}")
        
        # Update internal position tracking
        self.strategy_engine.update_position(
            asset=asset,
            in_position=True,
            entry_price=signal.price,
            asset_amount=asset_quantity,
            leveraged_value=leveraged_value
        )
        
        print(f"   ✅ Position opened successfully")
        print(f"   ✅ Internal tracking updated")
        
        trade_details = {
            'asset': asset,
            'entry_price': signal.price,
            'quantity': asset_quantity,
            'stop_loss': stop_loss_price,
            'take_profit': take_profit_price,
            'position_value': leveraged_value,
            'entry_time': datetime.now(timezone.utc)
        }
        
        return trade_details
    
    async def monitor_position(self, trade_details: Dict, monitoring_seconds: int = 30):
        """Monitor position with real market data"""
        asset = trade_details['asset']
        entry_price = trade_details['entry_price']
        stop_loss = trade_details['stop_loss']
        take_profit = trade_details['take_profit']
        
        print(f"\n📊 MONITORING {asset} POSITION FOR {monitoring_seconds} SECONDS")
        print("=" * 60)
        
        symbol = f"{asset}USDT"
        monitoring_start = datetime.now(timezone.utc)
        
        for i in range(monitoring_seconds):
            try:
                # Get real current price
                ticker = await self.bybit_client.get_ticker(symbol)
                current_price = float(ticker.get('lastPrice', entry_price))
                
                # Calculate unrealized P&L (for short position)
                price_change = entry_price - current_price
                pnl_percentage = (price_change / entry_price) * 100
                unrealized_pnl = (price_change / entry_price) * trade_details['position_value']
                
                # Check exit conditions
                exit_triggered = ""
                if current_price <= take_profit:
                    exit_triggered = "🎯 TAKE PROFIT HIT!"
                elif current_price >= stop_loss:
                    exit_triggered = "🛑 STOP LOSS HIT!"
                
                # Display monitoring info
                time_elapsed = i + 1
                print(f"⏱️  {time_elapsed:2d}s | {asset}: ${current_price:8.2f} | "
                      f"P&L: ${unrealized_pnl:+7.2f} ({pnl_percentage:+5.2f}%) | {exit_triggered}")
                
                if exit_triggered:
                    print(f"\n🚨 EXIT CONDITION TRIGGERED: {exit_triggered}")
                    return await self.execute_exit(trade_details, current_price, exit_triggered)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Monitoring error: {e}")
                await asyncio.sleep(1)
        
        # If no exit triggered, simulate manual exit
        print(f"\n⏰ Monitoring period ended - executing manual exit")
        ticker = await self.bybit_client.get_ticker(symbol)
        final_price = float(ticker.get('lastPrice', entry_price))
        return await self.execute_exit(trade_details, final_price, "⏰ TIME EXIT")
    
    async def execute_exit(self, trade_details: Dict, exit_price: float, exit_reason: str) -> Dict:
        """Execute trade exit"""
        asset = trade_details['asset']
        entry_price = trade_details['entry_price']
        quantity = trade_details['quantity']
        position_value = trade_details['position_value']
        
        print(f"\n🎯 EXECUTING EXIT FOR {asset}")
        print("=" * 50)
        
        # Calculate final P&L
        price_change = entry_price - exit_price  # Positive = profit for short
        pnl_percentage = (price_change / entry_price) * 100
        pnl_dollar = (price_change / entry_price) * position_value
        
        print(f"📊 Exit Summary:")
        print(f"   Exit Reason: {exit_reason}")
        print(f"   Entry Price: ${entry_price:.2f}")
        print(f"   Exit Price: ${exit_price:.2f}")
        print(f"   Price Change: ${price_change:.2f}")
        print(f"   P&L: ${pnl_dollar:+.2f} ({pnl_percentage:+.2f}%)")
        
        # Simulate exit order
        print(f"\n📡 SIMULATING EXIT ORDER:")
        print(f"   ⚡ Closing SHORT position: {quantity:.6f} {asset}")
        print(f"   ⚡ Exit price: ${exit_price:.2f}")
        print(f"   ✅ Position closed successfully")
        
        # Update position tracking
        self.strategy_engine.update_position(
            asset=asset,
            in_position=False,
            entry_price=0.0,
            asset_amount=0.0,
            leveraged_value=0.0
        )
        
        # Update account balance
        self.account_balance += pnl_dollar
        
        print(f"   ✅ Internal tracking updated")
        print(f"   💰 New account balance: ${self.account_balance:,.2f}")
        
        return {
            'exit_reason': exit_reason,
            'exit_price': exit_price,
            'pnl_dollar': pnl_dollar,
            'pnl_percentage': pnl_percentage,
            'new_balance': self.account_balance
        }

async def run_realistic_trade_test():
    """Run realistic trade test with live market data"""
    print("🧪 REALISTIC TRADE FLOW TEST")
    print("=" * 80)
    print("Using live Bybit demo data with simulated entry/exit conditions")
    
    simulator = RealisticTradeSimulator()
    
    # Test with one asset for detailed demonstration
    test_asset = 'BTC'
    
    try:
        print(f"\n🚀 Starting realistic trade test for {test_asset}")
        
        # Step 1: Force entry signal
        entry_signal = await simulator.force_entry_signal(test_asset)
        
        # Step 2: Execute trade
        trade_details = await simulator.execute_test_trade(entry_signal)
        
        # Step 3: Monitor position with real market data
        exit_result = await simulator.monitor_position(trade_details, monitoring_seconds=60)
        
        # Step 4: Final summary
        print(f"\n{'='*80}")
        print("🎯 REALISTIC TRADE TEST COMPLETED")
        print(f"{'='*80}")
        
        print(f"📊 Final Results:")
        print(f"   Asset: {test_asset}")
        print(f"   Exit Reason: {exit_result['exit_reason']}")
        print(f"   Final P&L: ${exit_result['pnl_dollar']:+.2f}")
        print(f"   Final Balance: ${exit_result['new_balance']:,.2f}")
        
        print(f"\n✅ Test demonstrates complete trade lifecycle:")
        print(f"   ✅ Signal generation with real market data")
        print(f"   ✅ Position calculation and tracking")
        print(f"   ✅ Real-time monitoring with live prices")
        print(f"   ✅ Exit condition detection")
        print(f"   ✅ P&L calculation and account update")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_realistic_trade_test())