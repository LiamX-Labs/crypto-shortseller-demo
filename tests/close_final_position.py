#!/usr/bin/env python3
"""Close any remaining positions"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.exchange.bybit_client import BybitClient

async def close_all_positions():
    client = BybitClient()
    
    print("🔄 CLOSING ALL REMAINING POSITIONS")
    print("=" * 40)
    
    # Check positions
    positions = await client.get_positions('BTCUSDT')
    
    for pos in positions:
        size = float(pos.get('size', 0))
        if size != 0:
            avg_price = float(pos.get('avgPrice', 0))
            unrealized_pnl = float(pos.get('unrealisedPnl', 0))
            
            print(f"📊 Found active position:")
            print(f"   Size: {size:.6f} BTC")
            print(f"   Avg Price: ${avg_price:.2f}")
            print(f"   Unrealized P&L: ${unrealized_pnl:+.2f}")
            
            # Determine close side
            if size > 0:
                close_side = 'Sell'  # Sell to close LONG
                pos_type = 'LONG'
            else:
                close_side = 'Buy'   # Buy to close SHORT
                pos_type = 'SHORT'
                size = abs(size)
            
            print(f"\n⚡ Closing {pos_type} position...")
            print(f"   Side: {close_side}")
            print(f"   Quantity: {size:.6f} BTC")
            
            try:
                result = await client.place_order(
                    symbol='BTCUSDT',
                    side=close_side,
                    order_type='Market',
                    qty=size
                )
                
                print(f"✅ Position closed successfully!")
                print(f"   Order ID: {result.get('orderId')}")
                
            except Exception as e:
                print(f"❌ Failed to close position: {e}")
    
    # Wait and check final status
    await asyncio.sleep(3)
    
    print(f"\n💰 FINAL STATUS CHECK")
    print("-" * 30)
    
    # Check balance
    balance_info = await client.get_account_balance()
    if balance_info and 'list' in balance_info:
        for account in balance_info['list']:
            for coin in account.get('coin', []):
                if coin.get('coin') == 'USDT':
                    balance = float(coin.get('walletBalance', 0))
                    print(f"💰 Final Balance: ${balance:,.2f} USDT")
    
    # Check positions
    final_positions = await client.get_positions('BTCUSDT')
    active_count = sum(1 for pos in final_positions if float(pos.get('size', 0)) != 0)
    
    if active_count == 0:
        print(f"✅ All positions successfully closed")
    else:
        print(f"⚠️  {active_count} positions still active")

if __name__ == "__main__":
    asyncio.run(close_all_positions())