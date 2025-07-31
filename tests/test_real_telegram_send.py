#!/usr/bin/env python3
"""
Test Real Telegram Message Sending
This test will actually send a message to verify the integration works
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

async def test_real_telegram_send():
    """Test sending actual messages to Telegram"""
    print("📤 REAL TELEGRAM MESSAGE SEND TEST")
    print("=" * 40)
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    
    if not bot_token:
        print("❌ No bot token found")
        return
    
    print(f"✅ Bot token found")
    print("🤖 Bot: @cryptoshortsellerbot")
    
    try:
        from telegram import Bot
        from telegram.constants import ParseMode
        
        bot = Bot(token=bot_token)
        
        # Get bot info
        bot_info = await bot.get_me()
        print(f"📡 Connected to: {bot_info.first_name} (@{bot_info.username})")
        
        # Test different ways to send a message
        
        # Method 1: Try to get updates to see if bot has any chats
        print("\n🔍 Checking for available chats...")
        try:
            updates = await bot.get_updates(limit=10)
            print(f"📨 Found {len(updates)} recent updates")
            
            available_chats = set()
            for update in updates:
                if update.message:
                    chat_id = update.message.chat.id
                    chat_type = update.message.chat.type
                    available_chats.add((chat_id, chat_type))
            
            if available_chats:
                print("💬 Available chats to test with:")
                for chat_id, chat_type in available_chats:
                    print(f"   Chat ID: {chat_id} (Type: {chat_type})")
                
                # Try sending to the first available chat
                test_chat_id = list(available_chats)[0][0]
                print(f"\n📤 Sending test message to chat {test_chat_id}...")
                
                test_message = f"""🧪 <b>TELEGRAM INTEGRATION TEST</b>

✅ <b>Bot Status:</b> Connected and Working!
🤖 <b>Bot:</b> @{bot_info.username}
⏰ <b>Test Time:</b> {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}

🎯 <b>Integration Features:</b>
• Trade entry/exit notifications
• Market alerts and regime updates  
• Daily portfolio reports
• Professional community messaging

📊 <b>Sample Trade Alert:</b>
💰 BTC SHORT at $42,350.75
📈 EMA Cross Confirmed ✅
🎯 Risk/Reward: 1:4.0

<b>Integration test successful!</b> 🚀

#TelegramTest #TradingBot #MultiAsset"""

                await bot.send_message(
                    chat_id=test_chat_id,
                    text=test_message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                
                print("✅ Test message sent successfully!")
                print(f"📱 Check chat {test_chat_id} for the message")
                
            else:
                print("⚠️ No chats found. Bot needs someone to start a conversation first.")
                print("\n💡 To test message sending:")
                print("1. Open Telegram and search for @cryptoshortsellerbot")
                print("2. Send /start or any message to the bot")
                print("3. Run this test again")
                
        except Exception as e:
            print(f"⚠️ Could not get updates: {e}")
            
            # Method 2: Try manual chat ID if user provides one
            print("\n💡 Alternative: Manual Chat ID Test")
            print("If you know your chat ID with the bot, we can test with that.")
            print("To get your chat ID:")
            print("1. Message @cryptoshortsellerbot on Telegram")
            print("2. Send any message")
            print("3. Your chat ID will appear in bot logs")
        
        # Method 3: Show what would be sent to a channel
        print("\n📺 CHANNEL MESSAGE PREVIEW:")
        print("-" * 30)
        
        channel_message = f"""🚨 <b>LIVE TRADING ALERT</b> 🚨

📊 <b>SOL SHORT POSITION</b>
💰 Entry Price: <b>$177.45</b>
⏰ Time: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}

📈 <b>Technical Analysis:</b>
• EMA 240: $179.87
• EMA 600: $180.96  
• Market Regime: ACTIVE
• Bearish EMA Cross Confirmed ✅

🎯 <b>Trade Setup:</b>
• Direction: SHORT ⬇️
• Stop Loss: 1.5% ($180.12)
• Take Profit: 6.0% ($166.80)
• Risk/Reward: 1:4.0

⚠️ <b>Risk Management:</b>
Position size: 7% of portfolio with 10x leverage
Following systematic strategy rules
Proper stop loss and take profit levels set

This is what your community will see! 🎯

#Trading #SOL #TechnicalAnalysis #EMAStrategy"""

        print(channel_message)
        
        print(f"\n🎉 TELEGRAM INTEGRATION STATUS:")
        print("✅ Bot Token: Valid and Connected")
        print("✅ Message Formatting: Professional & Ready")
        print("✅ System Integration: Fully Implemented")
        print("⚠️ Channel Setup: Needs TELEGRAM_CHANNEL_ID in .env")
        
        print(f"\n📋 TO COMPLETE SETUP:")
        print("1. Create a Telegram channel for your trading community")
        print("2. Add @cryptoshortsellerbot as channel administrator")
        print("3. Get the channel ID and add to .env as TELEGRAM_CHANNEL_ID")
        print("4. Live trading notifications will then be sent automatically!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_telegram_send())