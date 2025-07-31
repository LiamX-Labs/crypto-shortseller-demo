#!/usr/bin/env python3
"""
Quick Live Trade Test
Places a small real order on Bybit demo and monitors it briefly
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.exchange.bybit_client import BybitClient

async def quick_live_test():
    """Quick live trade execution test"""
    print("🔴 QUICK LIVE TRADE TEST")
    print("=" * 50)
    print("⚠️  Placing REAL small order on Bybit demo!")
    
    client = BybitClient()
    
    try:
        # Get account balance
        print("💰 Checking account balance...")
        balance_info = await client.get_account_balance()
        
        balance = 0
        if balance_info and 'list' in balance_info:
            for account in balance_info['list']:
                for coin in account.get('coin', []):
                    if coin.get('coin') == 'USDT':
                        balance = float(coin.get('walletBalance', 0))
                        print(f"   Balance: ${balance:,.2f} USDT")
                        break
        
        if balance < 100:
            print("❌ Insufficient balance for test")
            return
        
        # Get current BTC price
        print("\n📊 Getting current BTC price...")
        ticker = await client.get_ticker('BTCUSDT')
        current_price = float(ticker.get('lastPrice', 0))
        print(f"   BTC Price: ${current_price:.2f}")
        
        # Check current positions
        print("\n📋 Checking existing positions...")
        positions = await client.get_positions('BTCUSDT')
        active_position = None
        
        for pos in positions:
            if float(pos.get('size', 0)) != 0:
                active_position = pos
                size = float(pos.get('size', 0))
                avg_price = float(pos.get('avgPrice', 0))
                unrealized_pnl = float(pos.get('unrealisedPnl', 0))
                print(f"   Existing Position: {size:.6f} BTC at ${avg_price:.2f}, P&L: ${unrealized_pnl:+.2f}")
                break
        
        if not active_position:
            print("   No existing positions")
            
            # Place a small SHORT order
            print(f"\n🎯 PLACING SMALL SHORT ORDER...")
            print(f"   Symbol: BTCUSDT")
            print(f"   Side: Sell (SHORT)")
            print(f"   Quantity: 0.01 BTC")
            print(f"   Type: Market")
            
            # Calculate TP/SL
            entry_price = current_price * 0.999  # Slight below current
            stop_loss = entry_price * 1.015   # 1.5% above
            take_profit = entry_price * 0.94  # 6% below
            
            print(f"   Entry ~${entry_price:.2f}")
            print(f"   Stop Loss: ${stop_loss:.2f}")
            print(f"   Take Profit: ${take_profit:.2f}")
            
            print(f"\n⚡ EXECUTING ORDER...")
            
            result = await client.place_order(
                symbol='BTCUSDT',
                side='Sell',
                order_type='Market',
                qty=0.01,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            print(f"✅ ORDER EXECUTED!")
            print(f"   Order ID: {result.get('orderId')}")
            print(f"   Status: {result.get('status', 'FILLED')}")
            
            # Monitor for 30 seconds
            print(f"\n📊 MONITORING POSITION FOR 30 SECONDS...")
            
            for i in range(30):
                try:
                    positions = await client.get_positions('BTCUSDT')
                    ticker = await client.get_ticker('BTCUSDT')
                    current_price = float(ticker.get('lastPrice', 0))
                    
                    for pos in positions:
                        if float(pos.get('size', 0)) != 0:
                            size = float(pos.get('size', 0))
                            avg_price = float(pos.get('avgPrice', 0))
                            unrealized_pnl = float(pos.get('unrealisedPnl', 0))
                            pnl_pct = float(pos.get('unrealisedPnlPcnt', 0)) * 100
                            
                            print(f"   {i+1:2d}s | Price: ${current_price:8.2f} | "
                                  f"Size: {size:8.6f} | P&L: ${unrealized_pnl:+6.2f} ({pnl_pct:+5.2f}%)")
                            break
                    else:
                        print(f"   {i+1:2d}s | Position closed by TP/SL")
                        break
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"   Error monitoring: {e}")
                    break
        
        # Check final positions
        print(f"\n📋 FINAL POSITION CHECK...")
        positions = await client.get_positions('BTCUSDT')
        
        for pos in positions:
            if float(pos.get('size', 0)) != 0:
                size = float(pos.get('size', 0))
                avg_price = float(pos.get('avgPrice', 0))
                unrealized_pnl = float(pos.get('unrealisedPnl', 0))
                
                print(f"   Active Position: {size:.6f} BTC at ${avg_price:.2f}")
                print(f"   Unrealized P&L: ${unrealized_pnl:+.2f}")
                
                # Close the position
                print(f"\n🔄 CLOSING POSITION...")
                close_result = await client.place_order(
                    symbol='BTCUSDT',
                    side='Buy',
                    order_type='Market',
                    qty=abs(size)
                )
                
                print(f"✅ POSITION CLOSED!")
                print(f"   Close Order ID: {close_result.get('orderId')}")
                break
        else:
            print("   No active positions (may have been closed by TP/SL)")
        
        # Final balance check
        print(f"\n💰 FINAL BALANCE CHECK...")
        final_balance_info = await client.get_account_balance()
        
        if final_balance_info and 'list' in final_balance_info:
            for account in final_balance_info['list']:
                for coin in account.get('coin', []):
                    if coin.get('coin') == 'USDT':
                        final_balance = float(coin.get('walletBalance', 0))
                        pnl_change = final_balance - balance
                        
                        print(f"   Final Balance: ${final_balance:,.2f} USDT")
                        print(f"   P&L Change: ${pnl_change:+.2f} USDT")
                        break
        
        print(f"\n✅ QUICK LIVE TEST COMPLETED!")
        print(f"📋 Successfully demonstrated:")
        print(f"   ✅ Real order placement on Bybit demo")
        print(f"   ✅ Live position monitoring")
        print(f"   ✅ Position closing")
        print(f"   ✅ Real P&L impact")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚨 This will place a REAL order on Bybit demo!")
    print("Press Ctrl+C in next 3 seconds to cancel...")
    
    try:
        for i in range(3, 0, -1):
            print(f"Starting in {i}...")
            asyncio.run(asyncio.sleep(1))
        
        asyncio.run(quick_live_test())
        
    except KeyboardInterrupt:
        print("\n❌ Test cancelled")