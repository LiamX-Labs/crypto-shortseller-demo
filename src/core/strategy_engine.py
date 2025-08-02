#!/usr/bin/env python3
"""
Multi-Asset Strategy Engine
Handles EMA crossover signals and position management
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SignalType(Enum):
    NO_ACTION = "NO_ACTION"
    ENTER_SHORT = "ENTER_SHORT"
    EXIT_POSITION = "EXIT_POSITION"

class MarketRegime(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

@dataclass
class MarketData:
    asset: str
    price: float
    ema_240: float
    ema_600: float
    volume: float
    timestamp: datetime

@dataclass
class TradingSignal:
    asset: str
    signal_type: SignalType
    price: float
    reason: str = ""
    metadata: Optional[Dict[str, Any]] = None

class MultiAssetStrategyEngine:
    def __init__(self):
        self.asset_positions = {
            'BTC': {'in_position': False, 'entry_price': 0, 'asset_amount': 0, 'leveraged_value': 0, 'entry_time': None},
            'ETH': {'in_position': False, 'entry_price': 0, 'asset_amount': 0, 'leveraged_value': 0, 'entry_time': None},
            'SOL': {'in_position': False, 'entry_price': 0, 'asset_amount': 0, 'leveraged_value': 0, 'entry_time': None}
        }
        self.current_regimes = {
            'BTC': MarketRegime.ACTIVE,
            'ETH': MarketRegime.ACTIVE, 
            'SOL': MarketRegime.ACTIVE
        }
        self.previous_cross_states = {
            'BTC': None,
            'ETH': None,
            'SOL': None
        }
        
    def update_position(self, asset: str, in_position: bool, entry_price: float = 0, 
                       asset_amount: float = 0, leveraged_value: float = 0):
        """Update position tracking for an asset"""
        if asset in self.asset_positions:
            self.asset_positions[asset].update({
                'in_position': in_position,
                'entry_price': entry_price,
                'asset_amount': asset_amount,
                'leveraged_value': leveraged_value,
                'entry_time': datetime.now(timezone.utc) if in_position else None
            })
            logger.info(f"📊 {asset}: Position updated - In Position: {in_position}")
    
    def determine_market_regime(self, market_data: MarketData) -> MarketRegime:
        """Determine if market is in active or inactive regime based on EMA positioning"""
        # Market is ACTIVE when price is between the EMAs
        # Market is INACTIVE when price is above both EMAs or below both EMAs
        
        price = market_data.price
        ema_240 = market_data.ema_240
        ema_600 = market_data.ema_600
        
        # Determine EMA bounds
        upper_ema = max(ema_240, ema_600)
        lower_ema = min(ema_240, ema_600)
        
        # Price between EMAs = ACTIVE
        if lower_ema <= price <= upper_ema:
            regime = MarketRegime.ACTIVE
        else:
            # Price outside EMAs = INACTIVE
            regime = MarketRegime.INACTIVE
        
        # Update regime tracking
        self.current_regimes[market_data.asset] = regime
        
        return regime
    
    def detect_ema_cross(self, market_data: MarketData) -> Optional[str]:
        """Detect EMA240/EMA600 crossover"""
        asset = market_data.asset
        ema_240 = market_data.ema_240
        ema_600 = market_data.ema_600
        
        # Determine current cross state
        if ema_240 > ema_600:
            current_state = "bullish"  # EMA240 above EMA600
        else:
            current_state = "bearish"  # EMA240 below EMA600
        
        # Check for cross
        previous_state = self.previous_cross_states.get(asset)
        
        if previous_state is None:
            # First time checking this asset
            self.previous_cross_states[asset] = current_state
            return None
        
        if previous_state != current_state:
            # Cross detected
            self.previous_cross_states[asset] = current_state
            if current_state == "bearish":
                logger.info(f"🔽 {asset}: Bearish EMA cross detected (EMA240 below EMA600)")
                return "bearish_cross"
            else:
                logger.info(f"🔼 {asset}: Bullish EMA cross detected (EMA240 above EMA600)")
                return "bullish_cross"
        
        # No cross
        return None
    
    def generate_asset_signal(self, market_data: MarketData) -> TradingSignal:
        """Generate trading signal for a single asset"""
        asset = market_data.asset
        
        # Determine market regime
        regime = self.determine_market_regime(market_data)
        
        # Detect EMA cross
        cross_type = self.detect_ema_cross(market_data)
        
        # Check if already in position
        in_position = self.asset_positions[asset]['in_position']
        
        # Signal generation logic
        if in_position:
            # Already in position - check for exit conditions in separate method
            return TradingSignal(
                asset=asset,
                signal_type=SignalType.NO_ACTION,
                price=market_data.price,
                reason="In position - exit conditions checked separately",
                metadata={
                    'ema_240': market_data.ema_240,
                    'ema_600': market_data.ema_600,
                    'regime': regime.value,
                    'cross_type': cross_type
                }
            )
        
        # Not in position - check for entry conditions
        if cross_type == "bearish_cross" and regime == MarketRegime.ACTIVE:
            return TradingSignal(
                asset=asset,
                signal_type=SignalType.ENTER_SHORT,
                price=market_data.price,
                reason="Bearish EMA cross in ACTIVE market regime",
                metadata={
                    'ema_240': market_data.ema_240,
                    'ema_600': market_data.ema_600,
                    'regime': regime.value,
                    'cross_type': cross_type
                }
            )
        
        # No signal conditions met
        return TradingSignal(
            asset=asset,
            signal_type=SignalType.NO_ACTION,
            price=market_data.price,
            reason=f"No entry conditions met - Regime: {regime.value}, Cross: {cross_type or 'None'}",
            metadata={
                'ema_240': market_data.ema_240,
                'ema_600': market_data.ema_600,
                'regime': regime.value,
                'cross_type': cross_type
            }
        )
    
    def should_exit_position(self, asset: str, current_price: float, current_time: datetime) -> bool:
        """Check if position should be exited based on strategy rules"""
        if not self.asset_positions[asset]['in_position']:
            return False
        
        position = self.asset_positions[asset]
        entry_price = position['entry_price']
        entry_time = position['entry_time']
        
        # Calculate P&L percentage (for short positions: profit when price goes down)
        pnl_pct = ((entry_price - current_price) / entry_price) * 100
        
        # Time-based exit (24 hours max hold)
        if entry_time and (current_time - entry_time) > timedelta(hours=24):
            logger.info(f"🕐 {asset}: Time-based exit after 24 hours")
            return True
        
        # Stop loss (1.5% loss for short)
        if pnl_pct <= -1.5:
            logger.info(f"🛑 {asset}: Stop loss triggered at {pnl_pct:.2f}%")
            return True
        
        # Take profit (6% profit for short)
        if pnl_pct >= 6.0:
            logger.info(f"🎯 {asset}: Take profit triggered at {pnl_pct:.2f}%")
            return True
        
        return False
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get summary of current portfolio state"""
        active_positions = sum(1 for pos in self.asset_positions.values() if pos['in_position'])
        total_exposure = sum(pos['leveraged_value'] for pos in self.asset_positions.values() if pos['in_position'])
        
        assets_status = {}
        for asset, position in self.asset_positions.items():
            assets_status[asset] = {
                'in_position': position['in_position'],
                'regime': self.current_regimes[asset].value,
                'entry_price': position['entry_price'] if position['in_position'] else None,
                'leveraged_value': position['leveraged_value'] if position['in_position'] else 0
            }
        
        return {
            'active_positions': active_positions,
            'total_exposure': total_exposure,
            'assets_status': assets_status
        }