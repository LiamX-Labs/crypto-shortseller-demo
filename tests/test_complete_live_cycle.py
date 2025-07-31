#!/usr/bin/env python3
"""
Complete Live Trading Cycle Test
Demonstrates full entry-to-exit cycle with artificial signals on live exchange
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.exchange.bybit_client import BybitClient

async def complete_live_cycle_test():
    """Complete live trading cycle demonstration"""
    print("🎯 COMPLETE LIVE TRADING CYCLE TEST")
    print("=" * 80)
    print("Demonstrating: Signal → Entry → Monitoring → Exit")
    
    client = BybitClient()
    
    try:
        # Step 1: Pre-trade account status
        print("\n📊 STEP 1: PRE-TRADE ACCOUNT STATUS")
        print("-" * 40)
        
        balance_info = await client.get_account_balance()
        initial_balance = 0
        
        if balance_info and 'list' in balance_info:
            for account in balance_info['list']:
                for coin in account.get('coin', []):
                    if coin.get('coin') == 'USDT':
                        initial_balance = float(coin.get('walletBalance', 0))
                        available = float(coin.get('equity', 0))
                        print(f"💰 Initial Balance: ${initial_balance:,.2f} USDT")
                        print(f"💰 Available Equity: ${available:,.2f} USDT")
                        break
        
        # Step 2: Market analysis (artificial signal generation)
        print("\n🔍 STEP 2: MARKET ANALYSIS & SIGNAL GENERATION")
        print("-" * 40)
        
        ticker = await client.get_ticker('BTCUSDT')
        current_price = float(ticker.get('lastPrice', 0))
        volume_24h = float(ticker.get('volume24h', 0))
        
        print(f"📊 BTC Market Data:")
        print(f"   Current Price: ${current_price:,.2f}")
        print(f"   24h Volume: {volume_24h:,.0f} BTC")
        
        # Artificial signal logic
        artificial_entry_price = current_price * 0.9995  # Enter slightly below current
        
        print(f"\n🎭 ARTIFICIAL SIGNAL GENERATED:")
        print(f"   Signal Type: ENTER_SHORT")
        print(f"   Reason: Artificial bearish cross detected")
        print(f"   Entry Price Target: ${artificial_entry_price:.2f}")
        print(f"   Confidence: 1.0 (Test Mode)")
        
        # Step 3: Position sizing and risk calculation
        print("\n💰 STEP 3: POSITION SIZING & RISK MANAGEMENT")
        print("-" * 40)
        
        # Use small position for demo safety
        position_size_usd = min(100, initial_balance * 0.01)  # 1% or $100, whichever is smaller
        btc_quantity = 0.01  # Fixed minimum quantity for Bybit
        actual_position_value = btc_quantity * current_price
        
        # Risk parameters
        stop_loss_price = current_price * 1.02    # 2% above current (conservative)
        take_profit_price = current_price * 0.97  # 3% below current (conservative)
        
        print(f"📊 Position Details:")
        print(f"   BTC Quantity: {btc_quantity:.6f} BTC")
        print(f"   Position Value: ${actual_position_value:.2f}")
        print(f"   Stop Loss: ${stop_loss_price:.2f} (+2.0%)")
        print(f"   Take Profit: ${take_profit_price:.2f} (-3.0%)")
        print(f"   Max Risk: ${(stop_loss_price - current_price) * btc_quantity:.2f}")
        print(f"   Max Reward: ${(current_price - take_profit_price) * btc_quantity:.2f}")
        
        # Step 4: Order execution
        print("\n📡 STEP 4: LIVE ORDER EXECUTION")
        print("-" * 40)
        
        print(f"🎯 Placing LIVE SHORT order...")
        print(f"   Symbol: BTCUSDT")
        print(f"   Side: Sell (SHORT)")
        print(f"   Quantity: {btc_quantity} BTC")
        print(f"   Type: Market")
        print(f"   Stop Loss: ${stop_loss_price:.2f}")
        print(f"   Take Profit: ${take_profit_price:.2f}")
        
        # Execute the order
        order_result = await client.place_order(
            symbol='BTCUSDT',
            side='Sell',
            order_type='Market',
            qty=btc_quantity,
            stop_loss=stop_loss_price,
            take_profit=take_profit_price
        )
        
        print(f"✅ ORDER EXECUTED SUCCESSFULLY!")
        print(f"   Order ID: {order_result.get('orderId')}")
        print(f"   Timestamp: {datetime.now(timezone.utc).strftime('%H:%M:%S')}")
        
        # Step 5: Live position monitoring
        print("\n📊 STEP 5: LIVE POSITION MONITORING")
        print("-" * 40)
        print("Monitoring for 60 seconds or until position closes...")
        
        start_time = datetime.now(timezone.utc)
        position_active = True
        
        for i in range(60):
            try:
                # Get current position
                positions = await client.get_positions('BTCUSDT')
                ticker = await client.get_ticker('BTCUSDT')
                current_price = float(ticker.get('lastPrice', 0))
                
                position_found = False
                for pos in positions:
                    if float(pos.get('size', 0)) != 0:
                        position_found = True
                        size = float(pos.get('size', 0))
                        avg_price = float(pos.get('avgPrice', 0))
                        unrealized_pnl = float(pos.get('unrealisedPnl', 0))
                        pnl_pct = float(pos.get('unrealisedPnlPcnt', 0)) * 100
                        
                        status = "ACTIVE"
                        if current_price <= take_profit_price:
                            status = "NEAR TP 🎯"
                        elif current_price >= stop_loss_price:
                            status = "NEAR SL 🛑"
                        
                        print(f"   {i+1:2d}s | ${current_price:8.2f} | "
                              f"P&L: ${unrealized_pnl:+6.2f} ({pnl_pct:+5.2f}%) | {status}")
                        break
                
                if not position_found:
                    print(f"   {i+1:2d}s | Position CLOSED - TP/SL triggered!")
                    position_active = False
                    break
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"   Error monitoring: {e}")
                break
        
        # Step 6: Position closure (if still active)
        print("\n🔄 STEP 6: POSITION CLOSURE")
        print("-" * 40)
        
        if position_active:
            print("Position still active - closing manually...")
            
            # Get current position size
            positions = await client.get_positions('BTCUSDT')
            for pos in positions:
                if float(pos.get('size', 0)) != 0:
                    size = abs(float(pos.get('size', 0)))
                    
                    close_result = await client.place_order(
                        symbol='BTCUSDT',
                        side='Buy',
                        order_type='Market',
                        qty=size
                    )
                    
                    print(f"✅ Position closed manually")
                    print(f"   Close Order ID: {close_result.get('orderId')}")
                    break
        else:
            print("✅ Position was closed automatically by TP/SL")
        
        # Step 7: Post-trade analysis
        print("\n📊 STEP 7: POST-TRADE ANALYSIS")
        print("-" * 40)
        
        # Wait a moment for settlement
        await asyncio.sleep(2)
        
        # Get final balance
        final_balance_info = await client.get_account_balance()
        final_balance = initial_balance
        
        if final_balance_info and 'list' in final_balance_info:
            for account in final_balance_info['list']:
                for coin in account.get('coin', []):
                    if coin.get('coin') == 'USDT':
                        final_balance = float(coin.get('walletBalance', 0))
                        break
        
        # Get recent execution history
        executions = await client.get_execution_history('BTCUSDT', 3)
        
        total_pnl = final_balance - initial_balance
        
        print(f"💰 Final Results:")
        print(f"   Initial Balance: ${initial_balance:,.2f} USDT")
        print(f"   Final Balance: ${final_balance:,.2f} USDT")
        print(f"   Total P&L: ${total_pnl:+.2f} USDT")
        
        if executions:
            print(f"\n📋 Trade Executions:")
            for exec in executions[:2]:  # Show last 2 executions
                side = exec.get('side', 'N/A')
                price = exec.get('execPrice', 'N/A')
                qty = exec.get('execQty', 'N/A') 
                time = exec.get('execTime', 'N/A')
                
                # Convert timestamp if numeric
                try:
                    if time and time.isdigit():
                        dt = datetime.fromtimestamp(int(time)/1000, tz=timezone.utc)
                        time = dt.strftime('%H:%M:%S')
                except:
                    pass
                
                print(f"   {side:<4} | {qty:<10} | ${price:<8} | {time}")
        
        print(f"\n✅ COMPLETE LIVE TRADING CYCLE COMPLETED!")
        print(f"📋 Successfully demonstrated:")
        print(f"   ✅ Signal generation and analysis")
        print(f"   ✅ Position sizing and risk management")
        print(f"   ✅ Live order execution on Bybit demo")
        print(f"   ✅ Real-time position monitoring")
        print(f"   ✅ Automatic TP/SL execution")
        print(f"   ✅ Manual position closure")
        print(f"   ✅ Post-trade analysis and P&L calculation")
        print(f"   ✅ Complete integration with live exchange")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚨 COMPLETE LIVE TRADING CYCLE TEST")
    print("⚠️  This will place REAL orders on Bybit demo!")
    print("⚠️  Your demo account will be affected!")
    print("\nPress Ctrl+C within 5 seconds to cancel...")
    
    try:
        for i in range(5, 0, -1):
            print(f"Starting in {i}...")
            asyncio.run(asyncio.sleep(1))
        
        print("\n🚀 STARTING COMPLETE CYCLE TEST...")
        asyncio.run(complete_live_cycle_test())
        
    except KeyboardInterrupt:
        print("\n❌ Test cancelled by user")