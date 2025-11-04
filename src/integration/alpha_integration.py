"""
ShortSeller Strategy - Alpha Infrastructure Integration
Integrates with shared PostgreSQL and Redis services
"""

import sys
import os
from pathlib import Path
import logging
from datetime import datetime
from typing import Dict, Optional

# Add shared library to path
alpha_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(alpha_root))

from shared.alpha_db_client import AlphaDBClient, create_client_order_id

logger = logging.getLogger(__name__)


class ShortSellerAlphaIntegration:
    """
    Integration layer between ShortSeller strategy and Alpha infrastructure.

    Responsibilities:
    - Write all fills to PostgreSQL (trading.fills)
    - Update position state in Redis
    - Track performance metrics
    - Send heartbeats to bot registry
    """

    def __init__(self, bot_id: str = 'shortseller_001'):
        """
        Initialize integration with Alpha infrastructure.

        Args:
            bot_id: Bot identifier (default: 'shortseller_001')
        """
        self.bot_id = bot_id
        self.db_client = None
        self._initialize_db_client()

    def _initialize_db_client(self):
        """Initialize database client with retry logic."""
        try:
            # ShortSeller uses Redis DB 0 (per integration spec)
            self.db_client = AlphaDBClient(bot_id=self.bot_id, redis_db=0)
            logger.info(f"✅ Alpha infrastructure integration initialized for {self.bot_id}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Alpha integration: {e}")
            logger.warning("⚠️ Strategy will continue without database integration")
            self.db_client = None

    def is_connected(self) -> bool:
        """Check if database integration is active."""
        return self.db_client is not None

    # ========================================
    # FILL TRACKING
    # ========================================

    def record_fill(
        self,
        symbol: str,
        side: str,
        exec_price: float,
        exec_qty: float,
        order_id: str,
        close_reason: str,
        commission: float = 0.0,
        exec_time: datetime = None
    ) -> bool:
        """
        Record a fill to PostgreSQL.

        This is called after EVERY order execution.

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'Buy' or 'Sell'
            exec_price: Execution price
            exec_qty: Execution quantity
            order_id: Bybit order ID
            close_reason: Why executed ('entry', 'trailing_stop', etc.)
            commission: Fee paid
            exec_time: Execution time (defaults to now)

        Returns:
            True if successful, False otherwise
        """
        if not self.db_client:
            logger.debug("Database integration not available, skipping fill recording")
            return False

        try:
            # Create properly formatted client_order_id
            client_order_id = create_client_order_id(self.bot_id, close_reason)

            # Write to PostgreSQL
            self.db_client.write_fill(
                symbol=symbol,
                side=side,
                exec_price=exec_price,
                exec_qty=exec_qty,
                order_id=order_id,
                client_order_id=client_order_id,
                close_reason=close_reason,
                commission=commission,
                exec_time=exec_time
            )

            logger.info(f"📊 Fill recorded to PostgreSQL: {symbol} {side} {exec_qty} @ {exec_price} (reason: {close_reason})")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to record fill: {e}")
            return False

    # ========================================
    # POSITION STATE (Redis)
    # ========================================

    def update_position(
        self,
        symbol: str,
        size: float,
        side: str = None,
        avg_price: float = None,
        unrealized_pnl: float = None
    ):
        """
        Update position state in Redis.

        This is read by trading loops and monitoring systems.

        Args:
            symbol: Trading pair
            size: Position size (0 = flat)
            side: 'Buy' (long), 'Sell' (short), or None
            avg_price: Average entry price
            unrealized_pnl: Current unrealized P&L
        """
        if not self.db_client:
            return

        try:
            self.db_client.update_position_redis(
                symbol=symbol,
                size=size,
                side=side,
                avg_price=avg_price,
                unrealized_pnl=unrealized_pnl
            )

            logger.debug(f"📊 Redis position updated: {symbol} = {size}")

        except Exception as e:
            logger.error(f"❌ Failed to update Redis position: {e}")

    def get_position(self, symbol: str) -> Optional[Dict]:
        """
        Get current position from Redis.

        Args:
            symbol: Trading pair

        Returns:
            Position dict or None
        """
        if not self.db_client:
            return None

        try:
            return self.db_client.get_position_redis(symbol)
        except Exception as e:
            logger.error(f"❌ Failed to get Redis position: {e}")
            return None

    # ========================================
    # HEARTBEAT & STATUS
    # ========================================

    def send_heartbeat(self):
        """Send heartbeat to bot registry."""
        if not self.db_client:
            return

        try:
            self.db_client.update_heartbeat()
            logger.debug(f"💓 Heartbeat sent for {self.bot_id}")
        except Exception as e:
            logger.debug(f"Failed to send heartbeat: {e}")

    def update_equity(self, equity: float):
        """Update current equity in bot registry."""
        if not self.db_client:
            return

        try:
            self.db_client.update_equity(equity)
            logger.debug(f"💰 Equity updated: ${equity:,.2f}")
        except Exception as e:
            logger.debug(f"Failed to update equity: {e}")

    # ========================================
    # PERFORMANCE QUERIES
    # ========================================

    def get_daily_pnl(self, days: int = 1) -> float:
        """Get P&L for last N days."""
        if not self.db_client:
            return 0.0

        try:
            return self.db_client.get_daily_pnl(days)
        except:
            return 0.0

    def get_trade_count_today(self) -> int:
        """Get number of trades today."""
        if not self.db_client:
            return 0

        try:
            return self.db_client.get_trade_count_today()
        except:
            return 0

    # ========================================
    # CLEANUP
    # ========================================

    def close(self):
        """Close database connections."""
        if self.db_client:
            try:
                self.db_client.close()
                logger.info(f"Alpha integration closed for {self.bot_id}")
            except:
                pass


# Singleton instance for easy import
_integration = None


def get_integration(bot_id: str = 'shortseller_001') -> ShortSellerAlphaIntegration:
    """
    Get singleton integration instance.

    Args:
        bot_id: Bot identifier

    Returns:
        ShortSellerAlphaIntegration instance
    """
    global _integration
    if _integration is None:
        _integration = ShortSellerAlphaIntegration(bot_id=bot_id)
    return _integration
