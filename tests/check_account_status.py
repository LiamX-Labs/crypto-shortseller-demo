#!/usr/bin/env python3
"""Quick account status check"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.exchange.bybit_client import BybitClient

async def check_account_status():
    print("🔍 CURRENT ACCOUNT STATUS CHECK")
    print("=" * 40)
    
    client = BybitClient()
    
    try:
        # Get balance
        balance_info = await client.get_account_balance()
        if balance_info and 'list' in balance_info:
            for account in balance_info['list']:
                for coin in account.get('coin', []):
                    if coin.get('coin') == 'USDT':
                        balance = float(coin.get('walletBalance', 0))
                        available = float(coin.get('equity', 0))
                        print(f"💰 Total Balance: ${balance:,.2f} USDT")
                        print(f"💰 Available: ${available:,.2f} USDT")
        
        # Get positions
        print(f"\n📊 Active Positions:")
        positions = await client.get_positions('BTCUSDT')
        
        active_found = False
        for pos in positions:
            size = float(pos.get('size', 0))
            if size != 0:
                active_found = True
                avg_price = float(pos.get('avgPrice', 0))
                unrealized_pnl = float(pos.get('unrealisedPnl', 0))
                pnl_pct = float(pos.get('unrealisedPnlPcnt', 0)) * 100
                
                print(f"   BTC Position: {size:.6f} BTC")
                print(f"   Avg Price: ${avg_price:.2f}")
                print(f"   Unrealized P&L: ${unrealized_pnl:+.2f} ({pnl_pct:+.2f}%)")
        
        if not active_found:
            print("   No active positions")
        
        # Get recent orders
        print(f"\n📋 Recent Orders:")
        orders = await client.get_order_history('BTCUSDT', 3)
        
        if orders:
            for order in orders[:3]:
                symbol = order.get('symbol', 'N/A')
                side = order.get('side', 'N/A')
                qty = order.get('qty', 'N/A')
                price = order.get('avgPrice', order.get('price', 'N/A'))
                status = order.get('orderStatus', 'N/A')
                
                print(f"   {side} {qty} {symbol} at ${price} - {status}")
        else:
            print("   No recent orders")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_account_status())