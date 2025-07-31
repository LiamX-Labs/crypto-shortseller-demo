#!/usr/bin/env python3
"""
Test Bot Token Validity
Tests if the Telegram bot token is valid without sending messages
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

async def test_bot_token():
    """Test if bot token is valid"""
    print("🤖 TELEGRAM BOT TOKEN TEST")
    print("=" * 30)
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    
    if not bot_token:
        print("❌ No bot token found in environment variables")
        return
    
    print(f"✅ Bot token found ({len(bot_token)} characters)")
    print(f"Token starts with: {bot_token[:10]}...")
    
    try:
        from telegram import Bot
        
        bot = Bot(token=bot_token)
        
        print("\n📡 Testing bot connection...")
        
        # Get bot info
        bot_info = await bot.get_me()
        
        print("✅ Bot connection successful!")
        print(f"   Bot Name: {bot_info.first_name}")
        print(f"   Username: @{bot_info.username}")
        print(f"   Bot ID: {bot_info.id}")
        print(f"   Can Join Groups: {bot_info.can_join_groups}")
        print(f"   Can Read All Group Messages: {bot_info.can_read_all_group_messages}")
        print(f"   Supports Inline Queries: {bot_info.supports_inline_queries}")
        
        print("\n🎉 Bot token is valid and working!")
        print("\n📋 Next Steps:")
        print("1. Create a Telegram channel for your trading community")
        print("2. Add your bot as an administrator to the channel")
        print("3. Add TELEGRAM_CHANNEL_ID to your .env file")
        print("4. Run full integration test")
        
        print("\n💡 For testing, you can:")
        print("- Send the bot a direct message")
        print("- Use your user chat ID as TELEGRAM_CHANNEL_ID for testing")
        print("- Create a test channel and get its ID")
        
    except Exception as e:
        print(f"❌ Bot connection failed: {e}")
        
        if "Unauthorized" in str(e):
            print("   → Invalid bot token")
        elif "Network" in str(e) or "timeout" in str(e).lower():
            print("   → Network connectivity issue")
        else:
            print("   → Unexpected error")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bot_token())