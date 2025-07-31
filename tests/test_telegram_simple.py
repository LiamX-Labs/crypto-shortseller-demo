#!/usr/bin/env python3
"""
Simple Telegram Test - Non-interactive
Tests message formatting and connection if keys available
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_telegram_simple():
    """Simple Telegram test"""
    print("🤖 TELEGRAM INTEGRATION TEST")
    print("=" * 40)
    
    # Test message formatting first (works without keys)
    print("\n📝 Testing message formatting...")
    
    try:
        from src.notifications.telegram_bot import TelegramCommunityBot, TradingNotification
        
        bot = TelegramCommunityBot()
        
        # Test entry message format
        notification = TradingNotification(
            message_type='entry',
            asset='BTC',
            price=42350.75,
            signal_type='SHORT',
            timestamp=datetime.now(timezone.utc),
            metadata={
                'ema_240': 42400.25,
                'ema_600': 42450.50,
                'regime': 'ACTIVE',
                'stop_loss_pct': 1.5,
                'take_profit_pct': 6.0
            }
        )
        
        entry_message = bot.format_trade_entry_message(notification)
        print("✅ Entry message format:")
        print("-" * 30)
        print(entry_message)
        
        # Test exit message format
        exit_notification = TradingNotification(
            message_type='exit',
            asset='BTC',
            price=39850.25,
            signal_type='SHORT',
            timestamp=datetime.now(timezone.utc),
            metadata={
                'entry_price': 42350.75,
                'pnl': 41.25,
                'pnl_pct': 5.9,
                'exit_reason': 'Take Profit Hit',
                'hold_time': '4h 23m'
            }
        )
        
        exit_message = bot.format_trade_exit_message(exit_notification)
        print("\n✅ Exit message format:")
        print("-" * 30)
        print(exit_message)
        
        # Test daily report format
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
        
        status_message = bot.format_system_status_message(status_data)
        print("\n✅ Daily report format:")
        print("-" * 30)
        print(status_message)
        
        print("\n🎉 Message formatting test completed!")
        
    except Exception as e:
        print(f"❌ Message formatting test failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test connection if keys are available
    print("\n📱 Testing bot connection...")
    
    try:
        from config.settings import settings
        
        if settings.telegram.enabled:
            print(f"✅ Telegram configured:")
            print(f"   Bot Token: {'✅ Present' if settings.telegram.bot_token else '❌ Missing'}")
            print(f"   Channel ID: {'✅ Present' if settings.telegram.channel_id else '❌ Missing'}")
            print(f"   Admin Chat: {'✅ Present' if settings.telegram.admin_chat_id else '⚠️ Optional'}")
            
            # Test connection
            connection_ok = await bot.test_connection()
            if connection_ok:
                print("✅ Bot connection successful!")
                
                # Test sending one message
                print("\n📤 Sending test message...")
                from src.notifications.telegram_bot import notify_market_alert
                
                await notify_market_alert(
                    asset="TEST",
                    price=12345.67,
                    alert_type="System Test",
                    description="This is a test message from the Multi-Asset Trading System. Telegram integration is working correctly!"
                )
                print("✅ Test message sent successfully!")
                
            else:
                print("❌ Bot connection failed")
                print("   Check your bot token and channel permissions")
        else:
            print("⚠️ Telegram not configured")
            print("   Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID to .env file")
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_telegram_simple())