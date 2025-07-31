#!/usr/bin/env python3
"""
Test Trade Execution with Simulated Signals
Demonstrates complete entry and exit flow with fake market conditions
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from typing import Dict, List

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from src.core.strategy_engine import MultiAssetStrategyEngine, MarketData, SignalType, TradingSignal, MarketRegime
from src.exchange.bybit_client import BybitClient

class TestTradingSimulator:
    def __init__(self):
        self.strategy_engine = MultiAssetStrategyEngine()
        self.bybit_client = BybitClient()
        self.account_balance = 10000.0
        
    def create_fake_bearish_cross_scenario(self, asset: str, price: float) -> MarketData:
        """Create fake market data showing bearish cross conditions"""
        # Simulate bearish cross: EMA240 just crossed below EMA600
        ema_240 = price - 200.0  # EMA240 below current price
        ema_600 = price - 150.0  # EMA600 above EMA240 (bearish cross)
        
        # Force a recent bearish cross by manually adding it
        cross_event = {
            'asset': asset,
            'type': 'BEARISH_CROSS',
            'timestamp': datetime.now(timezone.utc),
            'ema_240': ema_240,
            'ema_600': ema_600
        }
        self.strategy_engine.cross_events[asset].append(cross_event)
        
        return MarketData(
            asset=asset,
            price=price - 250.0,  # Price below both EMAs (perfect short setup)
            ema_240=ema_240,
            ema_600=ema_600,
            volume=1000000.0,
            timestamp=datetime.now(timezone.utc)
        )
    
    def create_fake_exit_scenario(self, asset: str, entry_price: float, exit_type: str) -> float:
        """Create fake exit price scenarios"""
        if exit_type == "take_profit":
            # 6% profit (price dropped 6% from entry)
            return entry_price * (1 - settings.risk.take_profit_pct)
        elif exit_type == "stop_loss":
            # 1.5% loss (price rose 1.5% from entry)  
            return entry_price * (1 + settings.risk.stop_loss_pct)
        elif exit_type == "time_exit":
            # Random exit after time limit
            return entry_price * 0.98  # Small profit
        else:
            return entry_price
    
    async def simulate_trade_entry(self, asset: str, market_price: float) -> Dict:
        """Simulate a complete trade entry"""
        print(f"\n🎯 SIMULATING TRADE ENTRY FOR {asset}")
        print("=" * 60)
        
        # Step 1: Create fake bearish cross scenario
        fake_market_data = self.create_fake_bearish_cross_scenario(asset, market_price)
        
        print(f"📊 Fake Market Conditions Created:")
        print(f"   Current Price: ${fake_market_data.price:.2f}")
        print(f"   EMA240: ${fake_market_data.ema_240:.2f}")
        print(f"   EMA600: ${fake_market_data.ema_600:.2f}")
        print(f"   Setup: BEARISH CROSS with price below both EMAs")
        
        # Step 2: Generate signal
        signal = self.strategy_engine.generate_asset_signal(fake_market_data)
        
        print(f"\n📈 Signal Generated:")
        print(f"   Signal Type: {signal.signal_type.value}")
        print(f"   Reason: {signal.reason}")
        print(f"   Price: ${signal.price:.2f}")
        print(f"   Confidence: {signal.confidence}")
        
        if signal.signal_type != SignalType.ENTER_SHORT:
            print(f"❌ Expected ENTER_SHORT signal, got {signal.signal_type.value}")
            return {}
        
        # Step 3: Calculate position details
        allocation_pct = settings.risk.per_asset_allocation_pct
        leverage = settings.risk.leverage_per_asset
        
        position_value = self.account_balance * allocation_pct
        leveraged_value = position_value * leverage
        asset_quantity = leveraged_value / signal.price
        
        stop_loss_price = signal.price * (1 + settings.risk.stop_loss_pct)
        take_profit_price = signal.price * (1 - settings.risk.take_profit_pct)
        
        print(f"\n💰 Position Calculations:")
        print(f"   Account Balance: ${self.account_balance:,.2f}")
        print(f"   Allocation ({allocation_pct*100}%): ${position_value:.2f}")
        print(f"   Leverage ({leverage}x): ${leveraged_value:.2f}")
        print(f"   Asset Quantity: {asset_quantity:.6f} {asset}")
        print(f"   Entry Price: ${signal.price:.2f}")
        print(f"   Stop Loss: ${stop_loss_price:.2f} (+{settings.risk.stop_loss_pct*100}%)")
        print(f"   Take Profit: ${take_profit_price:.2f} (-{settings.risk.take_profit_pct*100}%)")
        
        # Step 4: Simulate order placement (fake Bybit call)
        print(f"\n📡 SIMULATING Bybit Order Placement:")
        print(f"   Symbol: {asset}USDT")
        print(f"   Side: Sell (SHORT)")
        print(f"   Type: Market")
        print(f"   Quantity: {asset_quantity:.6f}")
        print(f"   Stop Loss: ${stop_loss_price:.2f}")
        print(f"   Take Profit: ${take_profit_price:.2f}")
        
        fake_order_response = {
            'orderId': f'FAKE_{asset}_{int(datetime.now().timestamp())}',
            'symbol': f'{asset}USDT',
            'side': 'Sell',
            'orderType': 'Market',
            'qty': str(asset_quantity),
            'status': 'Filled',
            'avgPrice': str(signal.price)
        }
        
        print(f"   ✅ FAKE Order Response: {fake_order_response['orderId']}")
        print(f"   ✅ Status: {fake_order_response['status']}")
        print(f"   ✅ Avg Fill Price: ${float(fake_order_response['avgPrice']):.2f}")
        
        # Step 5: Update position tracking
        self.strategy_engine.update_position(
            asset=asset,
            in_position=True,
            entry_price=signal.price,
            asset_amount=asset_quantity,
            leveraged_value=leveraged_value
        )
        
        print(f"\n📊 Position Tracking Updated:")
        print(f"   {asset} Position: ACTIVE")
        print(f"   Entry Time: {datetime.now(timezone.utc).strftime('%H:%M:%S')}")
        print(f"   Position Value: ${leveraged_value:.2f}")
        
        return {
            'asset': asset,
            'entry_price': signal.price,
            'quantity': asset_quantity,
            'stop_loss': stop_loss_price,
            'take_profit': take_profit_price,
            'position_value': leveraged_value,
            'order_id': fake_order_response['orderId']
        }
    
    def simulate_trade_exit(self, trade_details: Dict, exit_type: str) -> Dict:
        """Simulate trade exit scenarios"""
        asset = trade_details['asset']
        entry_price = trade_details['entry_price']
        quantity = trade_details['quantity']
        position_value = trade_details['position_value']
        
        print(f"\n🎯 SIMULATING TRADE EXIT FOR {asset} ({exit_type.upper()})")
        print("=" * 60)
        
        # Calculate exit price
        exit_price = self.create_fake_exit_scenario(asset, entry_price, exit_type)
        
        # Calculate P&L (for short position: profit when price goes down)
        price_change = entry_price - exit_price  # Positive = profit for short
        pnl_percentage = (price_change / entry_price) * 100
        pnl_dollar = (price_change / entry_price) * position_value
        
        print(f"📊 Exit Scenario: {exit_type.upper()}")
        print(f"   Entry Price: ${entry_price:.2f}")
        print(f"   Exit Price: ${exit_price:.2f}")
        print(f"   Price Change: ${price_change:.2f} ({pnl_percentage:+.2f}%)")
        print(f"   Position P&L: ${pnl_dollar:+.2f}")
        
        # Simulate exit order
        print(f"\n📡 SIMULATING Exit Order:")
        print(f"   Symbol: {asset}USDT")
        print(f"   Side: Buy (CLOSE SHORT)")
        print(f"   Type: Market")
        print(f"   Quantity: {quantity:.6f}")
        print(f"   Exit Price: ${exit_price:.2f}")
        
        fake_exit_response = {
            'orderId': f'EXIT_{asset}_{int(datetime.now().timestamp())}',
            'symbol': f'{asset}USDT',
            'side': 'Buy', 
            'orderType': 'Market',
            'qty': str(quantity),
            'status': 'Filled',
            'avgPrice': str(exit_price)
        }
        
        print(f"   ✅ FAKE Exit Order: {fake_exit_response['orderId']}")
        print(f"   ✅ Status: {fake_exit_response['status']}")
        print(f"   ✅ Avg Exit Price: ${float(fake_exit_response['avgPrice']):.2f}")
        
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
        
        print(f"\n📊 Trade Summary:")
        print(f"   Trade Result: {'PROFIT' if pnl_dollar > 0 else 'LOSS'}")
        print(f"   P&L Amount: ${pnl_dollar:+.2f}")
        print(f"   P&L Percentage: {pnl_percentage:+.2f}%")
        print(f"   New Balance: ${self.account_balance:,.2f}")
        print(f"   Position Status: CLOSED")
        
        return {
            'exit_type': exit_type,
            'exit_price': exit_price,
            'pnl_dollar': pnl_dollar,
            'pnl_percentage': pnl_percentage,
            'new_balance': self.account_balance
        }

async def run_trade_simulation_tests():
    """Run comprehensive trade simulation tests"""
    print("🧪 MULTI-ASSET TRADE EXECUTION SIMULATION")
    print("=" * 80)
    print("Testing complete entry and exit flows with fake signals")
    
    simulator = TestTradingSimulator()
    
    # Get current market prices for realistic simulation
    try:
        print("\n📊 Getting current market prices for realistic simulation...")
        btc_ticker = await simulator.bybit_client.get_ticker('BTCUSDT')
        eth_ticker = await simulator.bybit_client.get_ticker('ETHUSDT')
        sol_ticker = await simulator.bybit_client.get_ticker('SOLUSDT')
        
        btc_price = float(btc_ticker.get('lastPrice', 118000))
        eth_price = float(eth_ticker.get('lastPrice', 3800))
        sol_price = float(sol_ticker.get('lastPrice', 180))
        
        print(f"Current Market Prices: BTC=${btc_price:.2f}, ETH=${eth_price:.2f}, SOL=${sol_price:.2f}")
        
    except Exception as e:
        print(f"Using default prices due to API error: {e}")
        btc_price, eth_price, sol_price = 118000, 3800, 180
    
    # Test 1: BTC Short Entry + Take Profit Exit
    print(f"\n{'='*80}")
    print("TEST 1: BTC SHORT ENTRY → TAKE PROFIT EXIT")
    print(f"{'='*80}")
    
    btc_trade = await simulator.simulate_trade_entry('BTC', btc_price)
    await asyncio.sleep(1)  # Simulate time passage
    btc_exit = simulator.simulate_trade_exit(btc_trade, 'take_profit')
    
    # Test 2: ETH Short Entry + Stop Loss Exit
    print(f"\n{'='*80}")
    print("TEST 2: ETH SHORT ENTRY → STOP LOSS EXIT")
    print(f"{'='*80}")
    
    eth_trade = await simulator.simulate_trade_entry('ETH', eth_price)
    await asyncio.sleep(1)
    eth_exit = simulator.simulate_trade_exit(eth_trade, 'stop_loss')
    
    # Test 3: SOL Short Entry + Time Exit
    print(f"\n{'='*80}")
    print("TEST 3: SOL SHORT ENTRY → TIME EXIT")
    print(f"{'='*80}")
    
    sol_trade = await simulator.simulate_trade_entry('SOL', sol_price)
    await asyncio.sleep(1)
    sol_exit = simulator.simulate_trade_exit(sol_trade, 'time_exit')
    
    # Final Summary
    print(f"\n{'='*80}")
    print("📊 SIMULATION SUMMARY")
    print(f"{'='*80}")
    
    total_pnl = btc_exit['pnl_dollar'] + eth_exit['pnl_dollar'] + sol_exit['pnl_dollar']
    
    print(f"🎯 All Trade Simulations Completed:")
    print(f"   BTC Trade: {btc_exit['exit_type'].upper()} → ${btc_exit['pnl_dollar']:+.2f}")
    print(f"   ETH Trade: {eth_exit['exit_type'].upper()} → ${eth_exit['pnl_dollar']:+.2f}") 
    print(f"   SOL Trade: {sol_exit['exit_type'].upper()} → ${sol_exit['pnl_dollar']:+.2f}")
    print(f"   Total P&L: ${total_pnl:+.2f}")
    print(f"   Final Balance: ${simulator.account_balance:,.2f}")
    
    print(f"\n✅ Trade execution simulation completed successfully!")
    print(f"📝 This demonstrates the complete flow from signal generation to position management")

if __name__ == "__main__":
    asyncio.run(run_trade_simulation_tests())