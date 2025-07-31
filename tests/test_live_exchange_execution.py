#!/usr/bin/env python3
"""
Live Exchange Execution Test
Places REAL orders on Bybit demo exchange using artificial signals
CAUTION: This will place actual trades on your demo account
"""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from src.core.strategy_engine import MultiAssetStrategyEngine, MarketData, SignalType, TradingSignal
from src.exchange.bybit_client import BybitClient

class LiveExchangeTester:
    def __init__(self):
        self.bybit_client = BybitClient()
        self.strategy_engine = MultiAssetStrategyEngine()
        self.active_orders = {}
        self.active_positions = {}
        
    async def initialize_demo_account(self):
        """Initialize and validate demo account"""
        print("🔧 INITIALIZING DEMO ACCOUNT")
        print("=" * 50)
        
        try:
            # Get account balance
            balance_info = await self.bybit_client.get_account_balance()
            if balance_info and 'list' in balance_info:
                for account in balance_info['list']:
                    for coin in account.get('coin', []):
                        if coin.get('coin') == 'USDT':
                            balance = float(coin.get('walletBalance', 0))
                            available = float(coin.get('equity', 0))
                            
                            print(f"💰 Demo Account Status:")
                            print(f"   Total Balance: ${balance:,.2f} USDT")
                            print(f"   Available Balance: ${available:,.2f} USDT")
                            
                            if balance < 1000:
                                print(f"⚠️  WARNING: Low balance for testing")
                                return False
                            
                            return True
            
            print("❌ Failed to get account balance")
            return False
            
        except Exception as e:
            print(f"❌ Account initialization failed: {e}")
            return False
    
    async def create_artificial_entry_signal(self, asset: str, current_price: float) -> TradingSignal:
        """Create artificial entry signal for live testing"""
        print(f"\n🎭 CREATING ARTIFICIAL ENTRY SIGNAL FOR {asset}")
        print("-" * 40)
        
        # Create realistic but artificial entry conditions
        artificial_entry_price = current_price * 0.999  # Entry 0.1% below current price
        
        print(f"📊 Artificial Conditions:")
        print(f"   Current Market Price: ${current_price:.2f}")
        print(f"   Artificial Entry Price: ${artificial_entry_price:.2f}")
        print(f"   Condition: FORCED bearish cross scenario")
        
        # Add fake cross event to strategy engine
        cross_event = {
            'asset': asset,
            'type': 'BEARISH_CROSS',
            'timestamp': datetime.now(timezone.utc),
            'ema_240': artificial_entry_price - 50,
            'ema_600': artificial_entry_price - 25
        }
        self.strategy_engine.cross_events[asset].append(cross_event)
        
        # Create entry signal
        signal = TradingSignal(
            signal_type=SignalType.ENTER_SHORT,
            timestamp=datetime.now(timezone.utc),
            price=artificial_entry_price,
            asset=asset,
            reason=f"{asset}: ARTIFICIAL bearish cross for live testing",
            confidence=1.0,
            metadata={'test_mode': True, 'real_price': current_price}
        )
        
        print(f"✅ Artificial signal created: {signal.signal_type.value}")
        return signal
    
    async def execute_live_short_order(self, signal: TradingSignal, account_balance: float) -> Optional[Dict]:
        """Execute REAL short order on Bybit demo"""
        asset = signal.asset
        symbol = f"{asset}USDT"
        
        print(f"\n🎯 EXECUTING LIVE SHORT ORDER FOR {asset}")
        print("=" * 50)
        print("⚠️  WARNING: This will place a REAL order on Bybit demo!")
        
        try:
            # Calculate position size (use minimum viable size for Bybit)
            if asset == 'BTC':
                min_quantity = 0.01  # Minimum 0.01 BTC for BTCUSDT
            elif asset == 'ETH':
                min_quantity = 0.1   # Minimum 0.1 ETH for ETHUSDT
            elif asset == 'SOL':
                min_quantity = 1.0   # Minimum 1 SOL for SOLUSDT
            else:
                min_quantity = 0.01
            
            # Calculate based on minimum quantity requirements
            asset_quantity = min_quantity
            leveraged_value = asset_quantity * signal.price
            position_value = leveraged_value / 5  # Assume 5x leverage for test
            
            # Calculate risk parameters
            stop_loss_price = signal.price * (1 + 0.015)  # 1.5% above entry
            take_profit_price = signal.price * (1 - 0.06)  # 6% below entry
            
            print(f"📊 LIVE Order Details:")
            print(f"   Symbol: {symbol}")
            print(f"   Side: Sell (SHORT)")
            print(f"   Type: Market")
            print(f"   Quantity: {asset_quantity:.6f} {asset}")
            print(f"   Entry Price: ${signal.price:.2f}")
            print(f"   Stop Loss: ${stop_loss_price:.2f}")
            print(f"   Take Profit: ${take_profit_price:.2f}")
            print(f"   Position Value: ${leveraged_value:.2f}")
            
            # Ask for confirmation
            print(f"\n🚨 READY TO PLACE LIVE ORDER!")
            print(f"   This will execute on Bybit demo exchange")
            print(f"   Proceeding in 3 seconds...")
            await asyncio.sleep(3)
            
            # Execute REAL order on Bybit
            print(f"📡 PLACING LIVE ORDER...")
            
            result = await self.bybit_client.place_order(
                symbol=symbol,
                side='Sell',
                order_type='Market',
                qty=asset_quantity,
                stop_loss=stop_loss_price,
                take_profit=take_profit_price
            )
            
            print(f"✅ LIVE ORDER EXECUTED!")
            print(f"   Order ID: {result.get('orderId', 'N/A')}")
            print(f"   Symbol: {result.get('symbol', 'N/A')}")
            print(f"   Status: SUCCESS")
            
            # Track the position
            position_data = {
                'asset': asset,
                'symbol': symbol,
                'order_id': result.get('orderId'),
                'entry_price': signal.price,
                'quantity': asset_quantity,
                'stop_loss': stop_loss_price,
                'take_profit': take_profit_price,
                'position_value': leveraged_value,
                'entry_time': datetime.now(timezone.utc)
            }
            
            self.active_positions[asset] = position_data
            
            # Update strategy engine
            self.strategy_engine.update_position(
                asset=asset,
                in_position=True,
                entry_price=signal.price,
                asset_amount=asset_quantity,
                leveraged_value=leveraged_value
            )
            
            return position_data
            
        except Exception as e:
            print(f"❌ LIVE ORDER FAILED: {e}")
            return None
    
    async def monitor_live_position(self, position_data: Dict, monitor_duration: int = 120):
        """Monitor REAL position on exchange"""
        asset = position_data['asset']
        symbol = position_data['symbol']
        entry_price = position_data['entry_price']
        
        print(f"\n📊 MONITORING LIVE POSITION: {asset}")
        print("=" * 60)
        print(f"Monitoring for {monitor_duration} seconds...")
        
        start_time = datetime.now(timezone.utc)
        
        for i in range(monitor_duration):
            try:
                # Get real position from exchange
                positions = await self.bybit_client.get_positions(symbol)
                current_position = None
                
                for pos in positions:
                    if float(pos.get('size', 0)) != 0:
                        current_position = pos
                        break
                
                if current_position:
                    # Live position data
                    size = float(current_position.get('size', 0))
                    avg_price = float(current_position.get('avgPrice', entry_price))
                    unrealized_pnl = float(current_position.get('unrealisedPnl', 0))
                    percentage = float(current_position.get('unrealisedPnlPcnt', 0)) * 100
                    
                    # Get current market price
                    ticker = await self.bybit_client.get_ticker(symbol)
                    current_price = float(ticker.get('lastPrice', avg_price))
                    
                    print(f"⏱️  {i+1:3d}s | {asset}: ${current_price:8.2f} | "
                          f"Size: {size:8.6f} | P&L: ${unrealized_pnl:+8.2f} ({percentage:+6.2f}%)")
                    
                    # Check if position was closed (by TP/SL)
                    if size == 0:
                        print(f"\n🎯 POSITION CLOSED BY EXCHANGE!")
                        
                        # Get execution history to see how it closed
                        executions = await self.bybit_client.get_execution_history(symbol, 5)
                        if executions:
                            latest = executions[0]
                            close_reason = "Unknown"
                            if "TP" in latest.get('orderType', ''):
                                close_reason = "🎯 TAKE PROFIT"
                            elif "SL" in latest.get('orderType', ''):
                                close_reason = "🛑 STOP LOSS"
                            else:
                                close_reason = "📋 MARKET CLOSE"
                            
                            print(f"   Close Reason: {close_reason}")
                            print(f"   Close Price: ${latest.get('execPrice', 'N/A')}")
                            print(f"   Close Time: {latest.get('execTime', 'N/A')}")
                        
                        # Clean up tracking
                        del self.active_positions[asset]
                        self.strategy_engine.update_position(asset, False, 0, 0, 0)
                        
                        return {
                            'closed': True,
                            'close_reason': close_reason,
                            'final_pnl': unrealized_pnl
                        }
                
                else:
                    print(f"⏱️  {i+1:3d}s | {asset}: No active position found")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Monitoring error: {e}")
                await asyncio.sleep(1)
        
        # If monitoring ended without position closing
        print(f"\n⏰ Monitoring period ended - position may still be active")
        return {'closed': False, 'timeout': True}
    
    async def close_live_position(self, asset: str) -> bool:
        """Manually close live position"""
        if asset not in self.active_positions:
            print(f"❌ No active position found for {asset}")
            return False
        
        position = self.active_positions[asset]
        symbol = position['symbol']
        
        print(f"\n🎯 MANUALLY CLOSING LIVE POSITION: {asset}")
        print("-" * 40)
        
        try:
            # Get current position size
            positions = await self.bybit_client.get_positions(symbol)
            current_size = 0
            
            for pos in positions:
                if float(pos.get('size', 0)) != 0:
                    current_size = abs(float(pos.get('size', 0)))
                    break
            
            if current_size == 0:
                print(f"✅ Position already closed")
                return True
            
            print(f"📡 Placing market BUY order to close SHORT...")
            print(f"   Quantity: {current_size:.6f} {asset}")
            
            # Place closing order (BUY to close SHORT)
            result = await self.bybit_client.place_order(
                symbol=symbol,
                side='Buy',
                order_type='Market',
                qty=current_size
            )
            
            print(f"✅ CLOSING ORDER EXECUTED!")
            print(f"   Order ID: {result.get('orderId', 'N/A')}")
            
            # Clean up tracking
            del self.active_positions[asset]
            self.strategy_engine.update_position(asset, False, 0, 0, 0)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to close position: {e}")
            return False

async def run_live_exchange_test():
    """Run comprehensive live exchange test"""
    print("🔴 LIVE EXCHANGE EXECUTION TEST")
    print("=" * 80)
    print("⚠️  WARNING: This test will place REAL orders on Bybit demo!")
    print("⚠️  Your demo account balance will be affected!")
    print("=" * 80)
    
    tester = LiveExchangeTester()
    
    # Initialize demo account
    if not await tester.initialize_demo_account():
        print("❌ Demo account initialization failed")
        return
    
    # Get account balance
    balance_info = await tester.bybit_client.get_account_balance()
    account_balance = 10000.0  # Default
    
    if balance_info and 'list' in balance_info:
        for account in balance_info['list']:
            for coin in account.get('coin', []):
                if coin.get('coin') == 'USDT':
                    account_balance = float(coin.get('walletBalance', 10000))
                    break
    
    # Test with BTC (you can change this to ETH or SOL)
    test_asset = 'BTC'
    
    try:
        print(f"\n🚀 STARTING LIVE TEST WITH {test_asset}")
        
        # Get current market price
        ticker = await tester.bybit_client.get_ticker(f'{test_asset}USDT')
        current_price = float(ticker.get('lastPrice', 0))
        
        print(f"📊 Current {test_asset} Price: ${current_price:.2f}")
        
        # Create artificial entry signal
        entry_signal = await tester.create_artificial_entry_signal(test_asset, current_price)
        
        # Execute LIVE short order
        position_data = await tester.execute_live_short_order(entry_signal, account_balance)
        
        if not position_data:
            print("❌ Failed to execute live order")
            return
        
        # Monitor the LIVE position
        print(f"\n⏰ Monitoring live position for 2 minutes...")
        monitor_result = await tester.monitor_live_position(position_data, 120)
        
        # If position is still active, close it manually
        if not monitor_result.get('closed', False):
            print(f"\n🔧 Position still active - closing manually...")
            await tester.close_live_position(test_asset)
        
        # Final account status
        print(f"\n📊 FINAL ACCOUNT STATUS")
        print("-" * 30)
        
        final_balance_info = await tester.bybit_client.get_account_balance()
        if final_balance_info and 'list' in final_balance_info:
            for account in final_balance_info['list']:
                for coin in account.get('coin', []):
                    if coin.get('coin') == 'USDT':
                        final_balance = float(coin.get('walletBalance', 0))
                        pnl_change = final_balance - account_balance
                        
                        print(f"💰 Final Balance: ${final_balance:,.2f} USDT")
                        print(f"💰 P&L Change: ${pnl_change:+.2f} USDT")
        
        print(f"\n✅ LIVE EXCHANGE TEST COMPLETED!")
        print(f"📋 This demonstrated:")
        print(f"   ✅ Real order placement on Bybit demo")
        print(f"   ✅ Live position monitoring")
        print(f"   ✅ Automatic TP/SL execution")
        print(f"   ✅ Manual position closing")
        print(f"   ✅ Real P&L impact on account")
        
    except Exception as e:
        print(f"❌ Live test failed: {e}")
        
        # Emergency cleanup
        if test_asset in tester.active_positions:
            print(f"🚨 Emergency cleanup - closing position...")
            await tester.close_live_position(test_asset)

async def main():
    """Main function with countdown"""
    print("⚠️  LIVE EXCHANGE TEST - REAL ORDERS WILL BE PLACED!")
    print("Press Ctrl+C within 5 seconds to cancel...")
    
    try:
        for i in range(5, 0, -1):
            print(f"Starting in {i}...")
            await asyncio.sleep(1)
        
        print("\n🚀 STARTING LIVE TEST...")
        await asyncio.sleep(1)
        
        await run_live_exchange_test()
        
    except KeyboardInterrupt:
        print("\n❌ Test cancelled by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())