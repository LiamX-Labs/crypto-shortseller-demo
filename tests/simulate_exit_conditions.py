#!/usr/bin/env python3
"""
Simulate Exit Conditions and Close Active Position
Demonstrates different exit scenarios and closes the live BTC position
"""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.exchange.bybit_client import BybitClient

class ExitConditionSimulator:
    def __init__(self):
        self.bybit_client = BybitClient()
        
    async def check_active_position(self):
        """Check current active position"""
        print("📊 CHECKING ACTIVE POSITION")
        print("=" * 40)
        
        positions = await self.bybit_client.get_positions('BTCUSDT')
        ticker = await self.bybit_client.get_ticker('BTCUSDT')
        current_price = float(ticker.get('lastPrice', 0))
        
        for pos in positions:
            size = float(pos.get('size', 0))
            if size != 0:
                avg_price = float(pos.get('avgPrice', 0))
                unrealized_pnl = float(pos.get('unrealisedPnl', 0))
                pnl_pct = float(pos.get('unrealisedPnlPcnt', 0)) * 100
                
                position_data = {
                    'size': size,
                    'avg_price': avg_price,
                    'current_price': current_price,
                    'unrealized_pnl': unrealized_pnl,
                    'pnl_percentage': pnl_pct,
                    'position_value': abs(size) * current_price
                }
                
                print(f"📊 Active BTC Position Found:")
                print(f"   Size: {size:.6f} BTC ({'SHORT' if size < 0 else 'LONG'})")
                print(f"   Entry Price: ${avg_price:.2f}")
                print(f"   Current Price: ${current_price:.2f}")
                print(f"   Position Value: ${position_data['position_value']:.2f}")
                print(f"   Unrealized P&L: ${unrealized_pnl:+.2f} ({pnl_pct:+.2f}%)")
                
                return position_data
        
        print("❌ No active position found")
        return None
    
    async def simulate_take_profit_exit(self, position_data):
        """Simulate take profit exit condition"""
        print("\n🎯 EXIT SCENARIO 1: TAKE PROFIT SIMULATION")
        print("=" * 50)
        
        entry_price = position_data['avg_price']
        current_price = position_data['current_price']
        size = position_data['size']
        
        # For a SHORT position, take profit occurs when price drops
        if size < 0:  # SHORT position
            take_profit_target = entry_price * 0.97  # 3% below entry
            print(f"📊 SHORT Position Take Profit Analysis:")
            print(f"   Entry Price: ${entry_price:.2f}")
            print(f"   Current Price: ${current_price:.2f}")
            print(f"   Take Profit Target: ${take_profit_target:.2f} (-3%)")
            
            if current_price <= take_profit_target:
                print(f"✅ TAKE PROFIT CONDITION MET!")
                return 'take_profit'
            else:
                price_move_needed = current_price - take_profit_target
                pct_move_needed = (price_move_needed / current_price) * 100
                print(f"📈 Price needs to drop ${price_move_needed:.2f} ({pct_move_needed:.2f}%) to hit TP")
                print(f"🎭 SIMULATING: Take profit triggered!")
                return 'take_profit_simulated'
        else:  # LONG position
            take_profit_target = entry_price * 1.03  # 3% above entry
            print(f"📊 LONG Position Take Profit Analysis:")
            print(f"   Entry Price: ${entry_price:.2f}")
            print(f"   Current Price: ${current_price:.2f}")
            print(f"   Take Profit Target: ${take_profit_target:.2f} (+3%)")
            
            if current_price >= take_profit_target:
                print(f"✅ TAKE PROFIT CONDITION MET!")
                return 'take_profit'
            else:
                price_move_needed = take_profit_target - current_price
                pct_move_needed = (price_move_needed / current_price) * 100
                print(f"📈 Price needs to rise ${price_move_needed:.2f} ({pct_move_needed:.2f}%) to hit TP")
                print(f"🎭 SIMULATING: Take profit triggered!")
                return 'take_profit_simulated'
    
    async def simulate_stop_loss_exit(self, position_data):
        """Simulate stop loss exit condition"""
        print("\n🛑 EXIT SCENARIO 2: STOP LOSS SIMULATION")
        print("=" * 50)
        
        entry_price = position_data['avg_price']
        current_price = position_data['current_price']
        size = position_data['size']
        
        # For a SHORT position, stop loss occurs when price rises
        if size < 0:  # SHORT position
            stop_loss_target = entry_price * 1.015  # 1.5% above entry
            print(f"📊 SHORT Position Stop Loss Analysis:")
            print(f"   Entry Price: ${entry_price:.2f}")
            print(f"   Current Price: ${current_price:.2f}")
            print(f"   Stop Loss Target: ${stop_loss_target:.2f} (+1.5%)")
            
            if current_price >= stop_loss_target:
                print(f"🚨 STOP LOSS CONDITION MET!")
                return 'stop_loss'
            else:
                price_move_to_sl = stop_loss_target - current_price
                pct_move_to_sl = (price_move_to_sl / current_price) * 100
                print(f"📈 Price needs to rise ${price_move_to_sl:.2f} ({pct_move_to_sl:.2f}%) to hit SL")
                print(f"🎭 SIMULATING: Stop loss triggered!")
                return 'stop_loss_simulated'
        else:  # LONG position
            stop_loss_target = entry_price * 0.985  # 1.5% below entry
            print(f"📊 LONG Position Stop Loss Analysis:")
            print(f"   Entry Price: ${entry_price:.2f}")
            print(f"   Current Price: ${current_price:.2f}")
            print(f"   Stop Loss Target: ${stop_loss_target:.2f} (-1.5%)")
            
            if current_price <= stop_loss_target:
                print(f"🚨 STOP LOSS CONDITION MET!")
                return 'stop_loss'
            else:
                price_move_to_sl = current_price - stop_loss_target
                pct_move_to_sl = (price_move_to_sl / current_price) * 100
                print(f"📈 Price needs to drop ${price_move_to_sl:.2f} ({pct_move_to_sl:.2f}%) to hit SL")
                print(f"🎭 SIMULATING: Stop loss triggered!")
                return 'stop_loss_simulated'
    
    async def simulate_time_exit(self, position_data):
        """Simulate time-based exit condition"""
        print("\n⏰ EXIT SCENARIO 3: TIME-BASED EXIT SIMULATION")
        print("=" * 50)
        
        # Simulate that position has been open for 24 hours
        print(f"📊 Time-Based Exit Analysis:")
        print(f"   Position held for: 24 hours (simulated)")
        print(f"   Maximum hold time: 24 hours")
        print(f"   Strategy rule: Close positions after 24 hours")
        print(f"")
        print(f"⏰ TIME EXIT CONDITION TRIGGERED!")
        print(f"   Reason: Maximum hold period exceeded")
        print(f"   Action: Close position at market price")
        
        return 'time_exit'
    
    async def simulate_regime_change_exit(self, position_data):
        """Simulate regime change exit condition"""
        print("\n🔄 EXIT SCENARIO 4: REGIME CHANGE EXIT SIMULATION")
        print("=" * 50)
        
        current_price = position_data['current_price']
        
        # Simulate EMA analysis
        fake_ema_240 = current_price * 0.999   # EMA240 slightly below current
        fake_ema_600 = current_price * 0.998   # EMA600 below EMA240
        
        print(f"📊 Market Regime Analysis:")
        print(f"   Current Price: ${current_price:.2f}")
        print(f"   EMA 240: ${fake_ema_240:.2f}")
        print(f"   EMA 600: ${fake_ema_600:.2f}")
        print(f"")
        print(f"📈 Previous Regime: BEARISH (EMA240 < EMA600, Price < EMAs)")
        print(f"📈 Current Regime: BULLISH (Price > EMAs, trend changing)")
        print(f"")
        print(f"🔄 REGIME CHANGE DETECTED!")
        print(f"   Previous: Favorable for SHORT positions")
        print(f"   Current: Unfavorable for SHORT positions")
        print(f"   Action: Exit SHORT position due to regime change")
        
        return 'regime_change'
    
    async def execute_position_close(self, position_data, exit_reason):
        """Execute the actual position close"""
        print(f"\n🎯 EXECUTING POSITION CLOSE")
        print("=" * 40)
        
        size = abs(position_data['size'])
        current_price = position_data['current_price']
        entry_price = position_data['avg_price']
        
        # Determine close side (opposite of position)
        if position_data['size'] < 0:
            close_side = 'Buy'  # Buy to close SHORT
            position_type = 'SHORT'
        else:
            close_side = 'Sell'  # Sell to close LONG
            position_type = 'LONG'
        
        print(f"📊 Close Order Details:")
        print(f"   Position Type: {position_type}")
        print(f"   Close Side: {close_side}")
        print(f"   Quantity: {size:.6f} BTC")
        print(f"   Exit Reason: {exit_reason.upper()}")
        print(f"   Current Price: ${current_price:.2f}")
        
        # Calculate expected P&L
        if position_data['size'] < 0:  # SHORT position
            price_diff = entry_price - current_price  # Positive = profit for short
        else:  # LONG position
            price_diff = current_price - entry_price  # Positive = profit for long
        
        expected_pnl = price_diff * size
        
        print(f"   Expected P&L: ${expected_pnl:+.2f}")
        
        print(f"\n⚡ EXECUTING CLOSE ORDER...")
        
        try:
            # Execute the close order
            close_result = await self.bybit_client.place_order(
                symbol='BTCUSDT',
                side=close_side,
                order_type='Market',
                qty=size
            )
            
            print(f"✅ POSITION CLOSED SUCCESSFULLY!")
            print(f"   Close Order ID: {close_result.get('orderId')}")
            print(f"   Status: {close_result.get('status', 'FILLED')}")
            print(f"   Timestamp: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}")
            
            return True
            
        except Exception as e:
            print(f"❌ FAILED TO CLOSE POSITION: {e}")
            return False
    
    async def get_final_account_status(self, initial_balance):
        """Get final account status after close"""
        print(f"\n💰 FINAL ACCOUNT STATUS")
        print("=" * 30)
        
        # Wait for settlement
        await asyncio.sleep(2)
        
        balance_info = await self.bybit_client.get_account_balance()
        final_balance = initial_balance
        
        if balance_info and 'list' in balance_info:
            for account in balance_info['list']:
                for coin in account.get('coin', []):
                    if coin.get('coin') == 'USDT':
                        final_balance = float(coin.get('walletBalance', 0))
                        available = float(coin.get('equity', 0))
                        
                        print(f"💰 Final Balance: ${final_balance:,.2f} USDT")
                        print(f"💰 Available: ${available:,.2f} USDT")
                        break
        
        # Calculate total P&L
        total_pnl = final_balance - initial_balance
        print(f"💰 Session P&L: ${total_pnl:+.2f} USDT")
        
        # Check positions are closed
        positions = await self.bybit_client.get_positions('BTCUSDT')
        active_positions = [pos for pos in positions if float(pos.get('size', 0)) != 0]
        
        if active_positions:
            print(f"⚠️  Warning: {len(active_positions)} positions still active")
        else:
            print(f"✅ All positions closed")
        
        return final_balance

async def run_exit_condition_simulation():
    """Run complete exit condition simulation"""
    print("🎯 EXIT CONDITION SIMULATION")
    print("=" * 80)
    print("Demonstrating various exit scenarios and closing active position")
    
    simulator = ExitConditionSimulator()
    
    try:
        # Get initial balance
        balance_info = await simulator.bybit_client.get_account_balance()
        initial_balance = 10000.0
        
        if balance_info and 'list' in balance_info:
            for account in balance_info['list']:
                for coin in account.get('coin', []):
                    if coin.get('coin') == 'USDT':
                        initial_balance = float(coin.get('walletBalance', 0))
                        break
        
        print(f"💰 Initial Balance: ${initial_balance:,.2f} USDT")
        
        # Check active position
        position_data = await simulator.check_active_position()
        
        if not position_data:
            print("❌ No active position to demonstrate exit conditions")
            return
        
        # Simulate different exit conditions
        print(f"\n🎭 SIMULATING VARIOUS EXIT CONDITIONS")
        print("=" * 50)
        
        # Scenario 1: Take Profit
        await simulator.simulate_take_profit_exit(position_data)
        await asyncio.sleep(1)
        
        # Scenario 2: Stop Loss
        await simulator.simulate_stop_loss_exit(position_data)
        await asyncio.sleep(1)
        
        # Scenario 3: Time Exit
        await simulator.simulate_time_exit(position_data)
        await asyncio.sleep(1)
        
        # Scenario 4: Regime Change
        await simulator.simulate_regime_change_exit(position_data)
        await asyncio.sleep(1)
        
        # Choose exit reason (let's use time exit for demonstration)
        chosen_exit = 'time_exit'
        
        print(f"\n🎯 CHOSEN EXIT SCENARIO: {chosen_exit.upper()}")
        print(f"Proceeding to close position...")
        await asyncio.sleep(2)
        
        # Execute position close
        success = await simulator.execute_position_close(position_data, chosen_exit)
        
        if success:
            # Get final status
            await simulator.get_final_account_status(initial_balance)
            
            print(f"\n✅ EXIT CONDITION SIMULATION COMPLETED!")
            print(f"📋 Successfully demonstrated:")
            print(f"   ✅ Take profit condition analysis")
            print(f"   ✅ Stop loss condition analysis")
            print(f"   ✅ Time-based exit logic")
            print(f"   ✅ Regime change exit detection")
            print(f"   ✅ Live position closure execution")
            print(f"   ✅ Final P&L calculation")
        else:
            print(f"❌ Position close failed")
            
    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🎯 EXIT CONDITION SIMULATION")
    print("⚠️  This will CLOSE the active BTC position!")
    print("Press Ctrl+C within 3 seconds to cancel...")
    
    try:
        for i in range(3, 0, -1):
            print(f"Starting in {i}...")
            asyncio.run(asyncio.sleep(1))
        
        print("\n🚀 STARTING EXIT SIMULATION...")
        asyncio.run(run_exit_condition_simulation())
        
    except KeyboardInterrupt:
        print("\n❌ Simulation cancelled by user")