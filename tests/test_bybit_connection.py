#!/usr/bin/env python3
"""
Test Bybit Demo API Connection
"""

import asyncio
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from src.exchange.bybit_client import BybitClient

async def test_bybit_connection():
    """Test connection to Bybit demo API"""
    print("🔧 Testing Bybit Demo API Connection")
    print(f"API URL: {settings.exchange.base_url}")
    print(f"API Key: {settings.exchange.api_key[:8]}...")
    print(f"Demo Mode: {'.env' in settings.exchange.base_url}")
    
    client = BybitClient()
    
    try:
        print("\n📊 Testing Account Balance...")
        balance = await client.get_account_balance()
        print(f"✅ Balance Response: {balance}")
        
        print("\n📈 Testing Market Data (BTCUSDT)...")
        ticker = await client.get_ticker('BTCUSDT')
        print(f"✅ BTC Price: ${ticker.get('lastPrice', 'N/A')}")
        
        print("\n📊 Testing Klines (BTCUSDT)...")
        klines = await client.get_klines('BTCUSDT', '5', 10)
        print(f"✅ Klines Count: {len(klines)} candles")
        if klines:
            latest = klines[0]
            print(f"   Latest: Open=${latest[1]}, High=${latest[2]}, Low=${latest[3]}, Close=${latest[4]}")
        
        print("\n🎯 Testing Positions...")
        positions = await client.get_positions('BTCUSDT')
        print(f"✅ Positions: {len(positions)} found")
        
        print("\n🔧 Testing Leverage Setting...")
        try:
            leverage_result = await client.set_leverage('BTCUSDT', '10', '10')
            print(f"✅ Leverage Set: {leverage_result}")
        except Exception as e:
            print(f"⚠️ Leverage Setting: {e}")
        
        print("\n🎉 All API tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ API Test Failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_bybit_connection())
    if not success:
        sys.exit(1)