#!/usr/bin/env python3
"""
Test 5-minute bar processing and timing
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from src.exchange.bybit_client import BybitClient
from scripts.start_trading import MultiAssetTradingSystem

async def test_5min_bar_timing():
    """Test 5-minute bar timing calculations"""
    print("🕐 Testing 5-minute bar timing logic")
    
    system = MultiAssetTradingSystem()
    
    # Test next 5-minute close calculation
    for i in range(5):
        now = datetime.now(timezone.utc)
        next_close = system.get_next_5min_close_time()
        
        print(f"Current time: {now.strftime('%H:%M:%S')}")
        print(f"Next 5-min close: {next_close.strftime('%H:%M:%S')}")
        print(f"Wait time: {(next_close - now).total_seconds():.0f} seconds")
        print("---")
        
        # Simulate waiting a bit
        await asyncio.sleep(1)

async def test_5min_bar_data():
    """Test 5-minute bar data retrieval and processing"""
    print("\n📊 Testing 5-minute bar data processing")
    
    client = BybitClient()
    
    for asset in ['BTC', 'ETH', 'SOL']:
        try:
            symbol = f"{asset}USDT"
            
            # Get 5-minute klines
            klines = await client.get_klines(symbol, '5', 20)  # Get last 20 bars
            
            print(f"\n{asset} - Last 5 bars (5-minute intervals):")
            print("Time                | Open      | High      | Low       | Close     | Volume")
            print("-" * 80)
            
            for i, kline in enumerate(klines[:5]):  # Show first 5 (most recent)
                timestamp = int(kline[0])
                dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
                
                print(f"{dt.strftime('%H:%M:%S %Y-%m-%d')} | "
                      f"${float(kline[1]):8.2f} | "
                      f"${float(kline[2]):8.2f} | "
                      f"${float(kline[3]):8.2f} | "
                      f"${float(kline[4]):8.2f} | "
                      f"{float(kline[5]):8.0f}")
            
            # Verify 5-minute intervals
            if len(klines) >= 2:
                time1 = int(klines[0][0])
                time2 = int(klines[1][0])
                interval_minutes = (time1 - time2) / (1000 * 60)
                print(f"✅ Interval verification: {interval_minutes:.0f} minutes between bars")
                
                if interval_minutes == 5:
                    print(f"✅ {asset}: Correct 5-minute intervals confirmed")
                else:
                    print(f"❌ {asset}: Expected 5-minute intervals, got {interval_minutes}")
            
        except Exception as e:
            print(f"❌ Error processing {asset}: {e}")

async def test_ema_calculation():
    """Test EMA calculation with 5-minute data"""
    print("\n📈 Testing EMA calculation with 5-minute bars")
    
    system = MultiAssetTradingSystem()
    
    try:
        # Test with BTC data
        market_data = await system.get_market_data('BTC')
        
        print(f"BTC Market Data from 5-minute bars:")
        print(f"  Current Price: ${market_data.price:.2f}")
        print(f"  EMA 240 (20 hours): ${market_data.ema_240:.2f}")
        print(f"  EMA 600 (50 hours): ${market_data.ema_600:.2f}")
        print(f"  Volume: {market_data.volume:,.0f}")
        print(f"  Timestamp: {market_data.timestamp}")
        
        # Check EMA relationship
        if market_data.ema_240 > market_data.ema_600:
            print("📊 EMA240 > EMA600 (Potential bullish trend)")
        else:
            print("📊 EMA240 < EMA600 (Potential bearish trend)")
            
        # Check price position relative to EMAs
        if market_data.price < market_data.ema_240 and market_data.price < market_data.ema_600:
            print("📊 Price below both EMAs (Bearish conditions)")
        elif market_data.price > market_data.ema_240 and market_data.price > market_data.ema_600:
            print("📊 Price above both EMAs (Bullish conditions)")
        else:
            print("📊 Price between EMAs (Mixed conditions)")
            
    except Exception as e:
        print(f"❌ Error in EMA test: {e}")

async def main():
    """Run all 5-minute bar tests"""
    print("🧪 5-Minute Bar Processing Tests")
    print("=" * 50)
    
    await test_5min_bar_timing()
    await test_5min_bar_data()
    await test_ema_calculation()
    
    print("\n✅ All 5-minute bar tests completed!")

if __name__ == "__main__":
    asyncio.run(main())