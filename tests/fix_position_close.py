#!/usr/bin/env python3
"""
Fix Position Closing Issues - Bybit V5 Compliant
Properly close positions according to Bybit V5 API documentation
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.exchange.bybit_client import BybitClient

async def fix_position_management():
    """Fix position management according to Bybit V5 docs"""
    print("🔧 FIXING POSITION MANAGEMENT - Bybit V5 Compliant")
    print("=" * 60)
    
    client = BybitClient()
    
    try:
        # Step 1: Check current position mode
        print("📋 STEP 1: Checking Position Mode")
        print("-" * 30)
        
        # In Bybit V5, we need to check position mode first
        # For linear perpetuals, position mode affects how positions are managed
        
        positions = await client.get_positions('BTCUSDT')
        
        print(f"Current positions for BTCUSDT:")
        total_size = 0
        
        for pos in positions:
            size = float(pos.get('size', 0))
            side = pos.get('side', 'None')
            avg_price = float(pos.get('avgPrice', 0))
            unrealized_pnl = float(pos.get('unrealisedPnl', 0))
            position_idx = pos.get('positionIdx', '0')
            
            if size != 0:
                print(f"   Position {position_idx}: {side} {size:.6f} BTC at ${avg_price:.2f}, P&L: ${unrealized_pnl:+.2f}")
                total_size += size if side == 'Buy' else -size
        
        print(f"   Net Position: {total_size:.6f} BTC")
        
        if total_size == 0:
            print("✅ No positions to close")
            return
        
        # Step 2: Set position mode to One-Way Mode (mode=0) for easier management
        print(f"\n📋 STEP 2: Setting Position Mode")
        print("-" * 30)
        
        try:
            mode_result = await client.switch_position_mode('BTCUSDT', mode=0)
            print(f"✅ Position mode set to One-Way Mode")
        except Exception as e:
            print(f"⚠️  Position mode setting: {e}")
            # Continue anyway, might already be in correct mode
        
        # Step 3: Close position using the correct method
        print(f"\n📋 STEP 3: Closing Position Properly")
        print("-" * 30)
        
        if total_size > 0:
            # We have a LONG position (net positive), need to SELL to close
            close_side = 'Sell'
            close_qty = abs(total_size)
            position_type = 'LONG'
        else:
            # We have a SHORT position (net negative), need to BUY to close
            close_side = 'Buy'
            close_qty = abs(total_size)
            position_type = 'SHORT'
        
        print(f"Position to close: {position_type} {close_qty:.6f} BTC")
        print(f"Close order: {close_side} {close_qty:.6f} BTC")
        
        # Method 1: Try using reduceOnly flag (Bybit V5 approach)
        print(f"\n⚡ Attempting close with reduceOnly=true...")
        
        try:
            close_result = await client._make_request('POST', '/v5/order/create', {
                'category': 'linear',
                'symbol': 'BTCUSDT',
                'side': close_side,
                'orderType': 'Market',
                'qty': str(close_qty),
                'reduceOnly': True,  # This is key for closing positions
                'timeInForce': 'IOC'  # Immediate or Cancel
            })
            
            print(f"✅ Close order executed with reduceOnly!")
            print(f"   Order ID: {close_result.get('orderId')}")
            
        except Exception as e:
            print(f"❌ ReduceOnly method failed: {e}")
            
            # Method 2: Try manual calculation and close
            print(f"\n⚡ Attempting manual close calculation...")
            
            try:
                close_result = await client.place_order(
                    symbol='BTCUSDT',
                    side=close_side,
                    order_type='Market',
                    qty=close_qty
                )
                
                print(f"✅ Manual close order executed!")
                print(f"   Order ID: {close_result.get('orderId')}")
                
            except Exception as e2:
                print(f"❌ Manual close also failed: {e2}")
                
                # Method 3: Cancel all open orders and try again
                print(f"\n⚡ Attempting to cancel orders and retry...")
                
                try:
                    # Cancel all open orders first
                    await client._make_request('POST', '/v5/order/cancel-all', {
                        'category': 'linear',
                        'symbol': 'BTCUSDT'
                    })
                    
                    await asyncio.sleep(1)
                    
                    # Try close again
                    close_result = await client._make_request('POST', '/v5/order/create', {
                        'category': 'linear',
                        'symbol': 'BTCUSDT',
                        'side': close_side,
                        'orderType': 'Market',
                        'qty': str(close_qty),
                        'timeInForce': 'IOC'
                    })
                    
                    print(f"✅ Close order executed after cleanup!")
                    print(f"   Order ID: {close_result.get('orderId')}")
                    
                except Exception as e3:
                    print(f"❌ All close methods failed: {e3}")
                    print(f"📋 Manual intervention may be required")
        
        # Step 4: Verify closure
        print(f"\n📋 STEP 4: Verification")
        print("-" * 30)
        
        await asyncio.sleep(3)  # Wait for settlement
        
        # Check final positions
        final_positions = await client.get_positions('BTCUSDT')
        final_balance_info = await client.get_account_balance()
        
        final_total_size = 0
        for pos in final_positions:
            size = float(pos.get('size', 0))
            side = pos.get('side', 'None')
            if size != 0:
                final_total_size += size if side == 'Buy' else -size
        
        if abs(final_total_size) < 0.000001:  # Account for floating point precision
            print(f"✅ All positions successfully closed!")
        else:
            print(f"⚠️  Remaining position: {final_total_size:.6f} BTC")
        
        # Final balance
        if final_balance_info and 'list' in final_balance_info:
            for account in final_balance_info['list']:
                for coin in account.get('coin', []):
                    if coin.get('coin') == 'USDT':
                        balance = float(coin.get('walletBalance', 0))
                        print(f"💰 Final Balance: ${balance:,.2f} USDT")
        
        print(f"\n📚 Bybit V5 Position Management Notes:")
        print(f"   ✅ Use reduceOnly=true for closing positions")
        print(f"   ✅ One-Way Mode simplifies position management")
        print(f"   ✅ IOC timeInForce for immediate execution")
        print(f"   ✅ Cancel conflicting orders before closing")
        
    except Exception as e:
        print(f"❌ Position fix failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_position_management())