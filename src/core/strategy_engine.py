#!/usr/bin/env python3
"""
Multi-Asset Strategy Engine
Handles EMA crossover signals and position management
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
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

class AlertType(Enum):
    VOLUME_SPIKE = "Volume Spike"
    PRICE_MOVEMENT = "Price Movement"
    VOLATILITY_INCREASE = "Volatility Increase"
    EMA_CONVERGENCE = "EMA Convergence"
    REGIME_CHANGE = "Regime Change"

@dataclass
class MarketAlert:
    asset: str
    alert_type: AlertType
    price: float
    description: str
    severity: str  # "LOW", "MEDIUM", "HIGH"
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

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
        self.previous_prices = {
            'BTC': None,
            'ETH': None,
            'SOL': None
        }
        self.previous_emas = {
            'BTC': {'ema_240': None, 'ema_600': None},
            'ETH': {'ema_240': None, 'ema_600': None},
            'SOL': {'ema_240': None, 'ema_600': None}
        }
        self.recent_cross_events = {
            'BTC': [],
            'ETH': [],
            'SOL': []
        }
        self.daily_cross_count = {
            'BTC': 0,
            'ETH': 0,
            'SOL': 0
        }
        self.cross_threshold = 12
        
        # Market alert tracking
        self.previous_regimes = {
            'BTC': None,
            'ETH': None,
            'SOL': None
        }
        self.price_history = {
            'BTC': [],
            'ETH': [],
            'SOL': []
        }
        self.volume_history = {
            'BTC': [],
            'ETH': [],
            'SOL': []
        }
        self.recent_alerts = {
            'BTC': [],
            'ETH': [],
            'SOL': []
        }
        self.alert_cooldown_minutes = 15  # Minimum time between similar alerts
        
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
        # Market is ACTIVE when price is below BOTH EMAs (favorable for shorting)
        # Market is INACTIVE when price is above one or both EMAs
        
        price = market_data.price
        ema_240 = market_data.ema_240
        ema_600 = market_data.ema_600
        
        # Check for ACTIVE regime: price below both EMAs
        if price < ema_240 and price < ema_600:
            regime = MarketRegime.ACTIVE
        else:
            regime = MarketRegime.INACTIVE
        
        # Update regime tracking
        self.current_regimes[market_data.asset] = regime
        
        return regime
    
    def detect_price_ema_crosses(self, market_data: MarketData) -> list:
        """Detect price crossing below EMAs (price-EMA crosses)"""
        asset = market_data.asset
        current_price = market_data.price
        current_ema_240 = market_data.ema_240
        current_ema_600 = market_data.ema_600
        
        cross_events = []
        
        # Get previous data
        previous_price = self.previous_prices.get(asset)
        previous_ema_240 = self.previous_emas[asset]['ema_240']
        previous_ema_600 = self.previous_emas[asset]['ema_600']
        
        # Store current data for next iteration
        self.previous_prices[asset] = current_price
        self.previous_emas[asset]['ema_240'] = current_ema_240
        self.previous_emas[asset]['ema_600'] = current_ema_600
        
        # Skip first iteration (no previous data)
        if previous_price is None or previous_ema_240 is None or previous_ema_600 is None:
            return cross_events
        
        # Price vs EMA240 cross detection
        was_price_above_240 = previous_price > previous_ema_240
        is_price_below_240 = current_price < current_ema_240
        
        if was_price_above_240 and is_price_below_240:
            cross_event = {
                'asset': asset,
                'type': 'PRICE_BELOW_EMA240',
                'timestamp': market_data.timestamp,
                'price': current_price,
                'ema': current_ema_240
            }
            cross_events.append(cross_event)
            self.recent_cross_events[asset].append(cross_event)
            self.daily_cross_count[asset] += 1
            logger.info(f"🔽 {asset}: Price crossed below EMA240 - Price: ${current_price:.2f}, EMA240: ${current_ema_240:.2f}")
        
        # Price vs EMA600 cross detection
        was_price_above_600 = previous_price > previous_ema_600
        is_price_below_600 = current_price < current_ema_600
        
        if was_price_above_600 and is_price_below_600:
            cross_event = {
                'asset': asset,
                'type': 'PRICE_BELOW_EMA600',
                'timestamp': market_data.timestamp,
                'price': current_price,
                'ema': current_ema_600
            }
            cross_events.append(cross_event)
            self.recent_cross_events[asset].append(cross_event)
            self.daily_cross_count[asset] += 1
            logger.info(f"🔽 {asset}: Price crossed below EMA600 - Price: ${current_price:.2f}, EMA600: ${current_ema_600:.2f}")
        
        return cross_events
    
    def update_market_data_history(self, market_data: MarketData):
        """Update price and volume history for market analysis"""
        asset = market_data.asset
        
        # Update price history (keep last 20 data points)
        self.price_history[asset].append(market_data.price)
        if len(self.price_history[asset]) > 20:
            self.price_history[asset].pop(0)
        
        # Update volume history (keep last 20 data points)
        self.volume_history[asset].append(market_data.volume)
        if len(self.volume_history[asset]) > 20:
            self.volume_history[asset].pop(0)
    
    def is_alert_on_cooldown(self, asset: str, alert_type: AlertType) -> bool:
        """Check if similar alert is still on cooldown"""
        now = datetime.now(timezone.utc)
        cooldown_threshold = now - timedelta(minutes=self.alert_cooldown_minutes)
        
        for alert in self.recent_alerts[asset]:
            if (alert.alert_type == alert_type and 
                alert.timestamp > cooldown_threshold):
                return True
        return False
    
    def add_alert(self, alert: MarketAlert):
        """Add alert to recent alerts tracking"""
        asset = alert.asset
        self.recent_alerts[asset].append(alert)
        
        # Keep only last 10 alerts per asset
        if len(self.recent_alerts[asset]) > 10:
            self.recent_alerts[asset].pop(0)
    
    def detect_market_alerts(self, market_data: MarketData) -> List[MarketAlert]:
        """Detect various market alert conditions"""
        alerts = []
        asset = market_data.asset
        
        # Update historical data
        self.update_market_data_history(market_data)
        
        # 1. Regime Change Alert
        current_regime = self.determine_market_regime(market_data)
        previous_regime = self.previous_regimes.get(asset)
        
        if (previous_regime is not None and 
            previous_regime != current_regime and
            not self.is_alert_on_cooldown(asset, AlertType.REGIME_CHANGE)):
            
            severity = "HIGH" if current_regime == MarketRegime.ACTIVE else "MEDIUM"
            description = f"Market regime changed from {previous_regime.value} to {current_regime.value}. "
            
            if current_regime == MarketRegime.ACTIVE:
                description += "Asset now favorable for shorting opportunities."
            else:
                description += "Asset no longer in optimal shorting conditions."
            
            alert = MarketAlert(
                asset=asset,
                alert_type=AlertType.REGIME_CHANGE,
                price=market_data.price,
                description=description,
                severity=severity,
                timestamp=datetime.now(timezone.utc),
                metadata={
                    'previous_regime': previous_regime.value,
                    'current_regime': current_regime.value,
                    'ema_240': market_data.ema_240,
                    'ema_600': market_data.ema_600
                }
            )
            alerts.append(alert)
            self.add_alert(alert)
        
        # Update previous regime
        self.previous_regimes[asset] = current_regime
        
        # 2. Significant Price Movement Alert
        if len(self.price_history[asset]) >= 3:
            recent_prices = self.price_history[asset][-3:]
            price_change_pct = ((recent_prices[-1] - recent_prices[0]) / recent_prices[0]) * 100
            
            if (abs(price_change_pct) > 2.0 and  # 2% movement in 3 bars (15 minutes)
                not self.is_alert_on_cooldown(asset, AlertType.PRICE_MOVEMENT)):
                
                direction = "dropped" if price_change_pct < 0 else "surged"
                severity = "HIGH" if abs(price_change_pct) > 4.0 else "MEDIUM"
                
                description = (f"Price {direction} {abs(price_change_pct):.1f}% in last 15 minutes. "
                              f"From ${recent_prices[0]:.2f} to ${recent_prices[-1]:.2f}. "
                              f"Monitor for potential trading opportunities.")
                
                alert = MarketAlert(
                    asset=asset,
                    alert_type=AlertType.PRICE_MOVEMENT,
                    price=market_data.price,
                    description=description,
                    severity=severity,
                    timestamp=datetime.now(timezone.utc),
                    metadata={
                        'price_change_pct': price_change_pct,
                        'start_price': recent_prices[0],
                        'end_price': recent_prices[-1],
                        'timeframe': '15min'
                    }
                )
                alerts.append(alert)
                self.add_alert(alert)
        
        # 3. Volume Spike Alert
        if len(self.volume_history[asset]) >= 5:
            recent_volumes = self.volume_history[asset][-5:]
            current_volume = recent_volumes[-1]
            avg_volume = sum(recent_volumes[:-1]) / len(recent_volumes[:-1])
            
            if (current_volume > avg_volume * 2.0 and  # 2x average volume
                not self.is_alert_on_cooldown(asset, AlertType.VOLUME_SPIKE)):
                
                volume_increase = ((current_volume - avg_volume) / avg_volume) * 100
                severity = "HIGH" if volume_increase > 300 else "MEDIUM"
                
                description = (f"Volume spike detected: {volume_increase:.0f}% above recent average. "
                              f"Current: {current_volume:,.0f}, Average: {avg_volume:,.0f}. "
                              f"Increased market activity may indicate opportunity.")
                
                alert = MarketAlert(
                    asset=asset,
                    alert_type=AlertType.VOLUME_SPIKE,
                    price=market_data.price,
                    description=description,
                    severity=severity,
                    timestamp=datetime.now(timezone.utc),
                    metadata={
                        'current_volume': current_volume,
                        'average_volume': avg_volume,
                        'volume_increase_pct': volume_increase
                    }
                )
                alerts.append(alert)
                self.add_alert(alert)
        
        # 4. EMA Convergence Alert
        ema_diff_pct = abs(market_data.ema_240 - market_data.ema_600) / market_data.ema_600 * 100
        
        if (ema_diff_pct < 0.5 and  # EMAs within 0.5% of each other
            not self.is_alert_on_cooldown(asset, AlertType.EMA_CONVERGENCE)):
            
            description = (f"EMA convergence detected: EMA240 and EMA600 within {ema_diff_pct:.2f}%. "
                          f"EMA240: ${market_data.ema_240:.2f}, EMA600: ${market_data.ema_600:.2f}. "
                          f"Potential breakout setup forming.")
            
            alert = MarketAlert(
                asset=asset,
                alert_type=AlertType.EMA_CONVERGENCE,
                price=market_data.price,
                description=description,
                severity="MEDIUM",
                timestamp=datetime.now(timezone.utc),
                metadata={
                    'ema_240': market_data.ema_240,
                    'ema_600': market_data.ema_600,
                    'ema_diff_pct': ema_diff_pct
                }
            )
            alerts.append(alert)
            self.add_alert(alert)
        
        return alerts
    
    def has_recent_price_ema_cross(self, asset: str, window_minutes: int = 5) -> bool:
        """Check if asset has recent price-EMA cross within specified window"""
        now = datetime.now(timezone.utc)
        recent_crosses = [
            event for event in self.recent_cross_events[asset]
            if (now - event['timestamp']).total_seconds() <= window_minutes * 60
        ]
        return len(recent_crosses) > 0
    
    def generate_asset_signal(self, market_data: MarketData) -> TradingSignal:
        """Generate trading signal for a single asset"""
        asset = market_data.asset
        
        # Determine market regime
        regime = self.determine_market_regime(market_data)
        
        # Detect price-EMA crosses
        cross_events = self.detect_price_ema_crosses(market_data)
        
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
                    'cross_events': cross_events
                }
            )
        
        # Check market regime first (primary condition)
        if regime != MarketRegime.ACTIVE:
            return TradingSignal(
                asset=asset,
                signal_type=SignalType.NO_ACTION,
                price=market_data.price,
                reason=f"Market regime not active - Regime: {regime.value}",
                metadata={
                    'ema_240': market_data.ema_240,
                    'ema_600': market_data.ema_600,
                    'regime': regime.value,
                    'cross_events': cross_events
                }
            )
        
        # Check daily cross limit
        if self.daily_cross_count[asset] >= self.cross_threshold:
            return TradingSignal(
                asset=asset,
                signal_type=SignalType.NO_ACTION,
                price=market_data.price,
                reason=f"Daily cross limit exceeded ({self.daily_cross_count[asset]}/{self.cross_threshold})",
                metadata={
                    'ema_240': market_data.ema_240,
                    'ema_600': market_data.ema_600,
                    'regime': regime.value,
                    'cross_events': cross_events
                }
            )
        
        # Check for recent price-EMA cross (entry trigger)
        if not self.has_recent_price_ema_cross(asset, window_minutes=5):
            return TradingSignal(
                asset=asset,
                signal_type=SignalType.NO_ACTION,
                price=market_data.price,
                reason="No recent price-EMA cross detected",
                metadata={
                    'ema_240': market_data.ema_240,
                    'ema_600': market_data.ema_600,
                    'regime': regime.value,
                    'cross_events': cross_events
                }
            )
        
        # All conditions met - generate entry signal
        cross_types = [event['type'] for event in cross_events]
        return TradingSignal(
            asset=asset,
            signal_type=SignalType.ENTER_SHORT,
            price=market_data.price,
            reason=f"Price-EMA cross in ACTIVE regime - Crosses: {cross_types}",
            metadata={
                'ema_240': market_data.ema_240,
                'ema_600': market_data.ema_600,
                'regime': regime.value,
                'cross_events': cross_events
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
    
    def reset_daily_cross_counts(self):
        """Reset daily cross counts (call at start of each day)"""
        for asset in self.daily_cross_count:
            self.daily_cross_count[asset] = 0
        logger.info("📊 Daily cross counts reset for all assets")
    
    def cleanup_old_cross_events(self, hours_to_keep: int = 24):
        """Clean up old cross events and alerts to prevent memory buildup"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_to_keep)
        
        for asset in self.recent_cross_events:
            # Clean cross events
            initial_count = len(self.recent_cross_events[asset])
            self.recent_cross_events[asset] = [
                event for event in self.recent_cross_events[asset]
                if event['timestamp'] > cutoff_time
            ]
            cleaned_count = initial_count - len(self.recent_cross_events[asset])
            if cleaned_count > 0:
                logger.info(f"🧹 {asset}: Cleaned {cleaned_count} old cross events")
            
            # Clean old alerts
            initial_alert_count = len(self.recent_alerts[asset])
            self.recent_alerts[asset] = [
                alert for alert in self.recent_alerts[asset]
                if alert.timestamp > cutoff_time
            ]
            cleaned_alert_count = initial_alert_count - len(self.recent_alerts[asset])
            if cleaned_alert_count > 0:
                logger.info(f"🧹 {asset}: Cleaned {cleaned_alert_count} old market alerts")
    
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
                'leveraged_value': position['leveraged_value'] if position['in_position'] else 0,
                'daily_crosses': self.daily_cross_count[asset],
                'recent_cross_events': len(self.recent_cross_events[asset]),
                'recent_alerts': len(self.recent_alerts[asset])
            }
        
        return {
            'active_positions': active_positions,
            'total_exposure': total_exposure,
            'assets_status': assets_status
        }