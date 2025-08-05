import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import json
from dataclasses import dataclass

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class TradingNotification:
    message_type: str  # 'entry', 'exit', 'regime_change', 'status'
    asset: str
    price: float
    signal_type: str
    timestamp: datetime
    metadata: Dict[str, Any] = None

class TelegramCommunityBot:
    """
    Telegram bot for sending trading notifications to a community channel
    Designed to address a trading community with professional, informative messages
    """
    
    def __init__(self):
        self.bot_token = settings.telegram.bot_token
        self.channel_id = settings.telegram.channel_id
        self.admin_chat_id = settings.telegram.admin_chat_id
        self.bot = None
        self.enabled = bool(self.bot_token and self.channel_id)
        
        if self.enabled:
            self.bot = Bot(token=self.bot_token)
            logger.info("🤖 Telegram bot initialized")
        else:
            logger.warning("⚠️ Telegram bot disabled - missing token or channel ID")
    
    async def test_connection(self) -> bool:
        """Test bot connection and permissions"""
        if not self.enabled:
            return False
            
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"✅ Telegram bot connected: @{bot_info.username}")
            
            # Test message to admin if configured
            if self.admin_chat_id:
                await self.bot.send_message(
                    chat_id=self.admin_chat_id,
                    text="🤖 <b>Multi-Asset Trading Bot Online</b>\n\nBot successfully connected and ready to send community notifications.",
                    parse_mode=ParseMode.HTML
                )
            
            return True
            
        except TelegramError as e:
            logger.error(f"❌ Telegram connection failed: {e}")
            return False
    
    def format_trade_entry_message(self, notification: TradingNotification) -> str:
        """Format trade entry message for community"""
        metadata = notification.metadata or {}
        
        # Get EMA values and other indicators
        ema_240 = metadata.get('ema_240', 0)
        ema_600 = metadata.get('ema_600', 0)
        regime = metadata.get('regime', 'UNKNOWN')
        
        # Calculate risk levels
        stop_loss_pct = metadata.get('stop_loss_pct', 1.5)
        take_profit_pct = metadata.get('take_profit_pct', 6.0)
        
        message = f"""🚨 <b>TRADE SIGNAL ALERT</b> 🚨

📊 <b>{notification.asset} SHORT POSITION</b>
💰 Entry Price: <b>${notification.price:,.2f}</b>
⏰ Time: {notification.timestamp.strftime('%H:%M:%S UTC')}

📈 <b>Technical Analysis:</b>
• EMA 240: ${ema_240:,.2f}
• EMA 600: ${ema_600:,.2f}
• Market Regime: {regime}
• Bearish EMA Cross Confirmed ✅

🎯 <b>Trade Setup:</b>
• Direction: SHORT ⬇️
• Stop Loss: {stop_loss_pct}% (${notification.price * (1 + stop_loss_pct/100):,.2f})
• Take Profit: {take_profit_pct}% (${notification.price * (1 - take_profit_pct/100):,.2f})
• Risk/Reward: 1:{take_profit_pct/stop_loss_pct:.1f}

⚠️ <b>Risk Management:</b>
Position size according to portfolio allocation rules
Maximum exposure per asset maintained
Always use proper risk management

#Trading #{notification.asset} #TechnicalAnalysis #EMAStrategy"""

        return message
    
    def format_trade_exit_message(self, notification: TradingNotification) -> str:
        """Format trade exit message for community"""
        metadata = notification.metadata or {}
        
        entry_price = metadata.get('entry_price', 0)
        pnl = metadata.get('pnl', 0)
        pnl_pct = metadata.get('pnl_pct', 0)
        exit_reason = metadata.get('exit_reason', 'Strategy Exit')
        hold_time = metadata.get('hold_time', '0')
        
        # Determine if win or loss
        profit_emoji = "🟢" if pnl > 0 else "🔴"
        result_text = "PROFIT" if pnl > 0 else "LOSS"
        
        message = f"""🏁 <b>POSITION CLOSED</b> {profit_emoji}

📊 <b>{notification.asset} SHORT POSITION</b>
💰 Exit Price: <b>${notification.price:,.2f}</b>
⏰ Time: {notification.timestamp.strftime('%H:%M:%S UTC')}

📈 <b>Trade Summary:</b>
• Entry Price: ${entry_price:,.2f}
• Exit Price: ${notification.price:,.2f}
• Hold Time: {hold_time}
• Exit Reason: {exit_reason}

💸 <b>P&L Result:</b>
• Absolute P&L: <b>${pnl:+,.2f} USDT</b>
• Percentage: <b>{pnl_pct:+.2f}%</b>
• Result: <b>{result_text}</b> {profit_emoji}

📊 <b>Community Stats:</b>
Another trade completed using our systematic approach
Keep following risk management principles!

#TradeUpdate #{notification.asset} #Results #{result_text}"""

        return message
    
    
    def format_system_status_message(self, status_data: Dict[str, Any]) -> str:
        """Format system status update for community"""
        
        balance = status_data.get('balance', 0)
        active_positions = status_data.get('active_positions', 0)
        daily_pnl = status_data.get('daily_pnl', 0)
        total_trades = status_data.get('total_trades', 0)
        
        # Asset regimes
        asset_status = status_data.get('assets_status', {})
        
        regime_summary = []
        cooldown_summary = []
        
        for asset, data in asset_status.items():
            regime = data.get('regime', 'UNKNOWN')
            emoji = "🟢" if regime == 'ACTIVE' else "🔴"
            regime_summary.append(f"{emoji} {asset}: {regime}")
            
            # Check cooldown status
            cooldown_status = data.get('cooldown_status', {})
            if cooldown_status.get('in_cooldown', False):
                cooldown_summary.append(
                    f"🕒 {asset}: {cooldown_status['reason']} "
                    f"({cooldown_status['remaining_formatted']} remaining)"
                )
        
        message = f"""📊 <b>DAILY TRADING REPORT</b>

💰 <b>Portfolio Status:</b>
• Account Balance: ${balance:,.2f} USDT
• Active Positions: {active_positions}
• Daily P&L: ${daily_pnl:+,.2f} USDT
• Total Trades Today: {total_trades}

📈 <b>Market Regimes:</b>
{chr(10).join(regime_summary)}

{f'''🕒 <b>Asset Cooldowns:</b>
{chr(10).join(cooldown_summary)}

''' if cooldown_summary else ''}🎯 <b>Strategy Update:</b>
Multi-asset EMA crossover system running smoothly
Monitoring BTC, ETH, SOL for bearish signals
Following systematic approach with proper risk management

Keep following the community for live trade updates!

#DailyReport #Trading #MultiAsset #Strategy"""

        return message
    
    def format_regime_change_message(self, notification: TradingNotification) -> str:
        """Format regime change notification for community"""
        metadata = notification.metadata or {}
        
        previous_regime = metadata.get('previous_regime', 'UNKNOWN')
        current_regime = metadata.get('current_regime', 'UNKNOWN')
        ema_240 = metadata.get('ema_240', 0)
        ema_600 = metadata.get('ema_600', 0)
        
        # Determine emoji and message tone based on regime change
        if current_regime == 'ACTIVE':
            status_emoji = "🟢"
            change_emoji = "📈"
            status_text = "FAVORABLE FOR SHORTING"
            description = "Market conditions now optimal for short position opportunities"
        else:
            status_emoji = "🔴"
            change_emoji = "📉"
            status_text = "UNFAVORABLE FOR SHORTING"
            description = "Market conditions no longer optimal for shorting"
        
        message = f"""📊 <b>REGIME CHANGE ALERT</b> {change_emoji}

{status_emoji} <b>{notification.asset} - {status_text}</b>
💰 Current Price: <b>${notification.price:,.2f}</b>
⏰ Time: {notification.timestamp.strftime('%H:%M:%S UTC')}

🔄 <b>Regime Update:</b>
• Previous: {previous_regime}
• Current: <b>{current_regime}</b>

📈 <b>Technical Context:</b>
• EMA 240: ${ema_240:,.2f}
• EMA 600: ${ema_600:,.2f}
• Price Position: {"Below both EMAs" if current_regime == 'ACTIVE' else "Above EMAs"}

📝 <b>Impact:</b>
{description}

🎯 <b>Strategy Note:</b>
{"Monitor for potential SHORT signals" if current_regime == 'ACTIVE' else "Reduced shorting opportunities"}

#{notification.asset} #RegimeChange #MarketConditions #Strategy"""

        return message
    
    async def send_trade_notification(self, notification: TradingNotification):
        """Send trade notification to community channel"""
        if not self.enabled:
            logger.debug("Telegram notifications disabled")
            return
        
        try:
            # Format message based on type
            if notification.message_type == 'entry':
                message = self.format_trade_entry_message(notification)
            elif notification.message_type == 'exit':
                message = self.format_trade_exit_message(notification)
            elif notification.message_type == 'regime_change':
                message = self.format_regime_change_message(notification)
            else:
                logger.warning(f"Unknown notification type: {notification.message_type}")
                return
            
            # Send to community channel
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            
            logger.info(f"📱 Telegram notification sent: {notification.message_type} for {notification.asset}")
            
        except TelegramError as e:
            logger.error(f"❌ Failed to send Telegram notification: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error sending notification: {e}")
    
    async def send_system_status(self, status_data: Dict[str, Any]):
        """Send system status update"""
        if not self.enabled:
            return
        
        try:
            message = self.format_system_status_message(status_data)
            
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            
            logger.info("📱 System status sent to Telegram")
            
        except TelegramError as e:
            logger.error(f"❌ Failed to send system status: {e}")
    
    async def send_emergency_alert(self, message: str):
        """Send emergency alert to both channel and admin"""
        if not self.enabled:
            return
        
        alert_message = f"""🚨 <b>EMERGENCY ALERT</b> 🚨

⚠️ <b>System Alert:</b>
{message}

⏰ Time: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}

Please check system status immediately!

#Emergency #SystemAlert"""
        
        try:
            # Send to channel
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=alert_message,
                parse_mode=ParseMode.HTML
            )
            
            # Send to admin if configured
            if self.admin_chat_id:
                await self.bot.send_message(
                    chat_id=self.admin_chat_id,
                    text=alert_message,
                    parse_mode=ParseMode.HTML
                )
            
            logger.critical(f"🚨 Emergency alert sent via Telegram")
            
        except TelegramError as e:
            logger.error(f"❌ Failed to send emergency alert: {e}")

# Global instance
telegram_bot = TelegramCommunityBot()

# Helper functions for easy integration
async def notify_trade_entry(asset: str, price: float, metadata: Dict[str, Any] = None):
    """Helper function to notify trade entry"""
    notification = TradingNotification(
        message_type='entry',
        asset=asset,
        price=price,
        signal_type='SHORT',
        timestamp=datetime.now(timezone.utc),
        metadata=metadata
    )
    await telegram_bot.send_trade_notification(notification)

async def notify_trade_exit(asset: str, price: float, metadata: Dict[str, Any] = None):
    """Helper function to notify trade exit"""
    notification = TradingNotification(
        message_type='exit',
        asset=asset,
        price=price,
        signal_type='SHORT',
        timestamp=datetime.now(timezone.utc),
        metadata=metadata
    )
    await telegram_bot.send_trade_notification(notification)


async def notify_regime_change(asset: str, price: float, previous_regime: str, current_regime: str, 
                              ema_240: float, ema_600: float):
    """Helper function to notify regime change"""
    notification = TradingNotification(
        message_type='regime_change',
        asset=asset,
        price=price,
        signal_type='REGIME_CHANGE',
        timestamp=datetime.now(timezone.utc),
        metadata={
            'previous_regime': previous_regime,
            'current_regime': current_regime,
            'ema_240': ema_240,
            'ema_600': ema_600
        }
    )
    await telegram_bot.send_trade_notification(notification)

async def send_daily_report(status_data: Dict[str, Any]):
    """Helper function to send daily status report"""
    await telegram_bot.send_system_status(status_data)