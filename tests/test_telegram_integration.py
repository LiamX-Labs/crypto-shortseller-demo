#!/usr/bin/env python3
"""
Test Telegram Integration for Multi-Asset Trading System
Demonstrates community-focused trading notifications
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.notifications.telegram_bot import telegram_bot, notify_trade_entry, notify_trade_exit, send_daily_report, notify_market_alert

async def test_telegram_integration():
    """Test all Telegram notification features"""
    print("🤖 TESTING TELEGRAM INTEGRATION")
    print("=" * 50)
    
    # Test 1: Bot Connection
    print("\n📱 Testing bot connection...")
    connection_ok = await telegram_bot.test_connection()
    
    if not connection_ok:
        print("❌ Telegram bot connection failed!")
        print("Please check your TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID environment variables")
        return
    
    print("✅ Telegram bot connected successfully!")
    
    # Test 2: Trade Entry Notification
    print("\n🎯 Testing trade entry notification...")
    try:
        await notify_trade_entry(
            asset="BTC",
            price=42350.75,
            metadata={
                'ema_240': 42400.25,
                'ema_600': 42450.50,
                'regime': 'ACTIVE',
                'stop_loss_pct': 1.5,
                'take_profit_pct': 6.0,
                'quantity': 0.0165,
                'leveraged_value': 700.00
            }
        )
        print("✅ Trade entry notification sent!")
        await asyncio.sleep(2)
        
    except Exception as e:
        print(f"❌ Trade entry notification failed: {e}")
    
    # Test 3: Trade Exit Notification
    print("\n🏁 Testing trade exit notification...")
    try:
        await notify_trade_exit(
            asset="BTC",  
            price=39850.25,
            metadata={
                'entry_price': 42350.75,
                'pnl': 41.25,
                'pnl_pct': 5.9,
                'exit_reason': 'Take Profit Hit',
                'hold_time': '4h 23m'
            }
        )
        print("✅ Trade exit notification sent!")
        await asyncio.sleep(2)
        
    except Exception as e:
        print(f"❌ Trade exit notification failed: {e}")
    
    # Test 4: Market Alert
    print("\n⚠️ Testing market alert...")
    try:
        await notify_market_alert(
            asset="ETH",
            price=2650.30,
            alert_type="EMA Cross Approaching",
            description="EMA240 is approaching EMA600 crossover. Price declining below both EMAs. Monitor for potential SHORT signal within next 2-3 bars."
        )
        print("✅ Market alert sent!")
        await asyncio.sleep(2)
        
    except Exception as e:
        print(f"❌ Market alert failed: {e}")
    
    # Test 5: Daily Status Report
    print("\n📊 Testing daily status report...")
    try:
        status_data = {
            'balance': 10247.83,
            'active_positions': 2,
            'daily_pnl': 124.65,
            'total_trades': 5,
            'assets_status': {
                'BTC': {'regime': 'ACTIVE', 'in_position': True, 'recent_crosses': 1},
                'ETH': {'regime': 'INACTIVE', 'in_position': False, 'recent_crosses': 0},
                'SOL': {'regime': 'ACTIVE', 'in_position': True, 'recent_crosses': 2}
            }
        }
        
        await send_daily_report(status_data)
        print("✅ Daily status report sent!")
        await asyncio.sleep(2)
        
    except Exception as e:
        print(f"❌ Daily status report failed: {e}")
    
    # Test 6: Emergency Alert
    print("\n🚨 Testing emergency alert...")
    try:
        await telegram_bot.send_emergency_alert(
            "TEST ALERT: System connectivity issue detected. All positions being monitored manually. This is a test message."
        )
        print("✅ Emergency alert sent!")
        await asyncio.sleep(2)
        
    except Exception as e:
        print(f"❌ Emergency alert failed: {e}")
    
    print("\n🎉 TELEGRAM INTEGRATION TEST COMPLETED!")
    print("Check your Telegram channel for all the test messages")
    print("\n📋 Message Types Tested:")
    print("   ✅ Trade Entry Signals")
    print("   ✅ Trade Exit Results") 
    print("   ✅ Market Alerts")
    print("   ✅ Daily Status Reports")
    print("   ✅ Emergency Alerts")
    print("   ✅ Bot Connection Test")
    print("\n🎯 Your trading community will receive professional,")
    print("   informative notifications for all trading activity!")

async def test_message_formatting():
    """Test message formatting without sending"""
    print("\n📝 TESTING MESSAGE FORMATTING")
    print("=" * 40)
    
    # Test entry message format
    print("\n🎯 Sample Trade Entry Message:")
    print("-" * 30)
    
    from src.notifications.telegram_bot import TradingNotification
    
    notification = TradingNotification(
        message_type='entry',
        asset='SOL',
        price=125.67,
        signal_type='SHORT',
        timestamp=datetime.now(timezone.utc),
        metadata={
            'ema_240': 126.80,
            'ema_600': 127.45,
            'regime': 'ACTIVE',
            'stop_loss_pct': 1.5,
            'take_profit_pct': 6.0
        }
    )
    
    entry_message = telegram_bot.format_trade_entry_message(notification)
    print(entry_message)
    
    # Test exit message format
    print("\n\n🏁 Sample Trade Exit Message:")
    print("-" * 30)
    
    exit_notification = TradingNotification(
        message_type='exit',
        asset='SOL',
        price=118.23,
        signal_type='SHORT',
        timestamp=datetime.now(timezone.utc),
        metadata={
            'entry_price': 125.67,
            'pnl': 7.44,
            'pnl_pct': 5.92,
            'exit_reason': 'Take Profit Target',
            'hold_time': '6h 15m'
        }
    )
    
    exit_message = telegram_bot.format_trade_exit_message(exit_notification)
    print(exit_message)

if __name__ == "__main__":
    print("🤖 TELEGRAM INTEGRATION TEST SUITE")
    print("=" * 60)
    print("This will test all Telegram notification features")
    print("Make sure your .env file has:")
    print("  - TELEGRAM_BOT_TOKEN=your_bot_token")
    print("  - TELEGRAM_CHANNEL_ID=your_channel_id") 
    print("  - TELEGRAM_ADMIN_CHAT_ID=your_admin_chat_id (optional)")
    print()
    
    choice = input("Choose test mode:\n1. Full integration test (sends messages)\n2. Format test only (no messages sent)\n3. Both\nEnter choice (1/2/3): ")
    
    if choice == "1":
        asyncio.run(test_telegram_integration())
    elif choice == "2":
        asyncio.run(test_message_formatting())
    elif choice == "3":
        asyncio.run(test_message_formatting())
        print("\n" + "="*60)
        asyncio.run(test_telegram_integration())
    else:
        print("Invalid choice. Exiting.")