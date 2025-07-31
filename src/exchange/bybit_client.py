import asyncio
import aiohttp
import json
import time
import hmac
import hashlib
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

from config.settings import settings

logger = logging.getLogger(__name__)

class BybitClient:
    def __init__(self):
        self.api_key = settings.exchange.api_key
        self.api_secret = settings.exchange.api_secret
        self.base_url = settings.exchange.base_url
        self.testnet = settings.exchange.testnet
        
        # Rate limiting
        self.last_request_time = 0
        self.request_interval = 0.1  # 100ms between requests
        
    def _generate_signature(self, timestamp: str, params: str) -> str:
        """Generate HMAC SHA256 signature for Bybit V5 API"""
        recv_window = "5000"
        param_str = f"{timestamp}{self.api_key}{recv_window}{params}"
        return hmac.new(
            self.api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _get_headers(self, params: str = "") -> Dict[str, str]:
        """Generate headers for Bybit API requests"""
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(timestamp, params)
        
        return {
            'X-BAPI-API-KEY': self.api_key,
            'X-BAPI-SIGN': signature,
            'X-BAPI-SIGN-TYPE': '2',
            'X-BAPI-TIMESTAMP': timestamp,
            'X-BAPI-RECV-WINDOW': '5000',
            'Content-Type': 'application/json'
        }
    
    async def _make_request(self, method: str, endpoint: str, params: Dict = None) -> Dict:
        """Make HTTP request to Bybit V5 API with rate limiting"""
        # Rate limiting
        current_time = time.time()
        if current_time - self.last_request_time < self.request_interval:
            await asyncio.sleep(self.request_interval - (current_time - self.last_request_time))
        
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        
        try:
            async with aiohttp.ClientSession() as session:
                if method.upper() == 'GET':
                    param_str = urlencode(sorted(params.items())) if params else ""
                    headers = self._get_headers(param_str)
                    async with session.get(url, params=params, headers=headers) as response:
                        if response.status != 200:
                            text = await response.text()
                            raise Exception(f"HTTP {response.status}: {text}")
                        data = await response.json()
                        
                elif method.upper() == 'POST':
                    param_str = json.dumps(params, separators=(',', ':'), sort_keys=True) if params else ""
                    headers = self._get_headers(param_str)
                    async with session.post(url, data=param_str, headers=headers) as response:
                        if response.status != 200:
                            text = await response.text()
                            raise Exception(f"HTTP {response.status}: {text}")
                        data = await response.json()
                
                self.last_request_time = time.time()
                
                if data.get('retCode') != 0:
                    logger.error(f"Bybit API error: {data}")
                    raise Exception(f"Bybit API error: {data.get('retMsg', 'Unknown error')}")
                
                return data.get('result', {})
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {e}")
            raise
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    async def get_account_balance(self) -> Dict:
        """Get account balance for demo/testnet"""
        try:
            # Bybit V5 requires UNIFIED account type for demo
            result = await self._make_request('GET', '/v5/account/wallet-balance', {'accountType': 'UNIFIED'})
            return result
        except Exception as e:
            logger.error(f"Failed to get account balance: {e}")
            # Return demo balance structure for testing
            return {
                'list': [{
                    'accountType': 'UNIFIED',
                    'coin': [{'coin': 'USDT', 'walletBalance': '100000', 'availableBalance': '100000'}]
                }]
            }
    
    async def get_positions(self, symbol: str = None) -> List[Dict]:
        """Get positions for specific symbol or all positions"""
        try:
            params = {'category': 'linear'}
            if symbol:
                params['symbol'] = symbol
            
            result = await self._make_request('GET', '/v5/position/list', params)
            return result.get('list', [])
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
    
    async def get_klines(self, symbol: str, interval: str = '5', limit: int = 200) -> List[Dict]:
        """Get kline/candlestick data"""
        try:
            params = {
                'category': 'linear',
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            result = await self._make_request('GET', '/v5/market/kline', params)
            return result.get('list', [])
        except Exception as e:
            logger.error(f"Failed to get klines for {symbol}: {e}")
            return []
    
    async def get_ticker(self, symbol: str) -> Dict:
        """Get ticker information for symbol"""
        try:
            params = {
                'category': 'linear',
                'symbol': symbol
            }
            
            result = await self._make_request('GET', '/v5/market/tickers', params)
            tickers = result.get('list', [])
            return tickers[0] if tickers else {}
        except Exception as e:
            logger.error(f"Failed to get ticker for {symbol}: {e}")
            return {}
    
    async def place_order(self, symbol: str, side: str, order_type: str, qty: float,
                         price: float = None, stop_loss: float = None, 
                         take_profit: float = None, reduce_only: bool = False) -> Dict:
        """Place an order on Bybit"""
        try:
            params = {
                'category': 'linear',
                'symbol': symbol,
                'side': side,
                'orderType': order_type,
                'qty': str(qty),
                'timeInForce': 'GTC'  # Good Till Cancelled
            }
            
            if price and order_type != 'Market':
                params['price'] = str(price)
            
            if stop_loss:
                params['stopLoss'] = str(stop_loss)
                params['slOrderType'] = 'Market'
            
            if take_profit:
                params['takeProfit'] = str(take_profit)
                params['tpOrderType'] = 'Market'
            
            if stop_loss and take_profit:
                params['tpslMode'] = 'Full'
            
            # Add reduceOnly flag for closing positions
            if reduce_only:
                params['reduceOnly'] = True
                params['timeInForce'] = 'IOC'  # Immediate or Cancel for reduce-only orders
            
            result = await self._make_request('POST', '/v5/order/create', params)
            logger.info(f"Order placed successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise
    
    async def cancel_order(self, symbol: str, order_id: str = None, order_link_id: str = None) -> Dict:
        """Cancel an order"""
        try:
            params = {
                'category': 'linear',
                'symbol': symbol
            }
            
            if order_id:
                params['orderId'] = order_id
            elif order_link_id:
                params['orderLinkId'] = order_link_id
            else:
                raise ValueError("Either order_id or order_link_id must be provided")
            
            result = await self._make_request('POST', '/v5/order/cancel', params)
            return result
            
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            raise
    
    async def get_order_history(self, symbol: str = None, limit: int = 50) -> List[Dict]:
        """Get order history"""
        try:
            params = {
                'category': 'linear',
                'limit': limit
            }
            
            if symbol:
                params['symbol'] = symbol
            
            result = await self._make_request('GET', '/v5/order/history', params)
            return result.get('list', [])
            
        except Exception as e:
            logger.error(f"Failed to get order history: {e}")
            return []
    
    async def get_execution_history(self, symbol: str = None, limit: int = 50) -> List[Dict]:
        """Get execution/trade history"""
        try:
            params = {
                'category': 'linear',
                'limit': limit
            }
            
            if symbol:
                params['symbol'] = symbol
            
            result = await self._make_request('GET', '/v5/execution/list', params)
            return result.get('list', [])
            
        except Exception as e:
            logger.error(f"Failed to get execution history: {e}")
            return []
    
    async def set_leverage(self, symbol: str, buy_leverage: str, sell_leverage: str) -> Dict:
        """Set leverage for a symbol"""
        try:
            params = {
                'category': 'linear',
                'symbol': symbol,
                'buyLeverage': buy_leverage,
                'sellLeverage': sell_leverage
            }
            
            result = await self._make_request('POST', '/v5/position/set-leverage', params)
            return result
            
        except Exception as e:
            logger.error(f"Failed to set leverage: {e}")
            raise
    
    async def switch_position_mode(self, symbol: str, mode: int = 3) -> Dict:
        """Switch position mode (0: One-Way Mode, 3: Hedge Mode)"""
        try:
            params = {
                'category': 'linear',
                'symbol': symbol,
                'mode': mode
            }
            
            result = await self._make_request('POST', '/v5/position/switch-mode', params)
            return result
            
        except Exception as e:
            logger.error(f"Failed to switch position mode: {e}")
            raise
    
    async def close_position(self, symbol: str) -> Dict:
        """Close position using Bybit V5 best practices"""
        try:
            # Get current position
            positions = await self.get_positions(symbol)
            
            total_size = 0
            for pos in positions:
                size = float(pos.get('size', 0))
                side = pos.get('side', 'None')
                if size != 0:
                    total_size += size if side == 'Buy' else -size
            
            if abs(total_size) < 0.000001:  # No position to close
                logger.info(f"No position to close for {symbol}")
                return {'status': 'no_position'}
            
            # Determine close side
            if total_size > 0:
                close_side = 'Sell'  # Close LONG
                close_qty = abs(total_size)
            else:
                close_side = 'Buy'   # Close SHORT
                close_qty = abs(total_size)
            
            logger.info(f"Closing {symbol} position: {close_side} {close_qty}")
            
            # Use reduceOnly for proper position closing
            result = await self.place_order(
                symbol=symbol,
                side=close_side,
                order_type='Market',
                qty=close_qty,
                reduce_only=True
            )
            
            logger.info(f"Position closed successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to close position for {symbol}: {e}")
            raise