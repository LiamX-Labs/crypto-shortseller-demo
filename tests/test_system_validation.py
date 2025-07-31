import pytest
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from src.core.strategy_engine import MultiAssetStrategyEngine, MarketData, SignalType
from src.exchange.bybit_client import BybitClient

def test_settings_configuration():
    """Test that settings are properly configured"""
    assert settings.exchange.testnet == True
    assert len(settings.get_asset_symbols()) == 3
    assert 'BTC' in settings.get_asset_symbols()
    assert 'ETH' in settings.get_asset_symbols() 
    assert 'SOL' in settings.get_asset_symbols()
    assert settings.risk.per_asset_allocation_pct == 0.07
    assert settings.risk.leverage_per_asset == 10

def test_strategy_engine_initialization():
    """Test strategy engine initializes correctly"""
    engine = MultiAssetStrategyEngine()
    assert len(engine.assets) == 3
    assert 'BTC' in engine.assets
    assert 'ETH' in engine.assets
    assert 'SOL' in engine.assets
    
    # Test initial state
    for asset in engine.assets:
        assert not engine.asset_positions[asset]['in_position']
        assert asset in engine.current_regimes
        assert asset in engine.cross_events

def test_market_data_processing():
    """Test market data processing"""
    engine = MultiAssetStrategyEngine()
    
    # Create test market data
    market_data = MarketData(
        asset='BTC',
        price=50000.0,
        ema_240=49000.0,
        ema_600=48000.0,
        volume=1000000.0,
        timestamp=None
    )
    
    # Test signal generation (should be NO_ACTION initially)
    signal = engine.generate_asset_signal(market_data)
    assert signal.asset == 'BTC'
    assert signal.signal_type == SignalType.NO_ACTION

def test_ema_cross_detection():
    """Test EMA cross detection logic"""
    engine = MultiAssetStrategyEngine()
    
    # Test bearish cross detection
    # First call - no previous data
    cross1 = engine.detect_ema_cross('BTC', 49000.0, 50000.0)
    assert cross1 is None
    
    # Second call - bearish cross (240 crosses below 600)
    # Previous: 240=49000, 600=50000 (240 < 600)
    # Current: 240=48000, 600=50000 (240 still < 600, no cross)
    cross2 = engine.detect_ema_cross('BTC', 48000.0, 50000.0) 
    assert cross2 is None  # No cross yet
    
    # Third call - simulate actual bearish cross (240 was above, now below)
    # Reset with 240 above 600
    engine.last_ema_values['BTC'] = {'ema_240': 51000.0, 'ema_600': 50000.0}
    # Now cross below
    cross3 = engine.detect_ema_cross('BTC', 49000.0, 50000.0)
    assert cross3 is not None
    assert cross3['type'] == 'BEARISH_CROSS'
    assert cross3['asset'] == 'BTC'

def test_position_tracking():
    """Test position tracking functionality"""
    engine = MultiAssetStrategyEngine()
    
    # Test position update
    engine.update_position(
        asset='BTC',
        in_position=True,
        entry_price=50000.0,
        asset_amount=0.1,
        leveraged_value=50000.0
    )
    
    assert engine.asset_positions['BTC']['in_position'] == True
    assert engine.asset_positions['BTC']['entry_price'] == 50000.0
    assert engine.asset_positions['BTC']['asset_amount'] == 0.1

def test_portfolio_summary():
    """Test portfolio summary generation"""
    engine = MultiAssetStrategyEngine()
    
    # Add a position
    engine.update_position('BTC', True, 50000.0, 0.1, 50000.0)
    
    summary = engine.get_portfolio_summary()
    assert summary['active_positions'] == 1
    assert summary['total_exposure'] == 50000.0
    assert 'BTC' in summary['assets_status']

def test_bybit_client_initialization():
    """Test Bybit client initializes correctly"""
    client = BybitClient()
    assert client.testnet == True
    assert client.base_url == "https://api-testnet.bybit.com"
    assert client.request_interval == 0.1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])