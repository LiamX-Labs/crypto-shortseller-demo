#!/usr/bin/env python3
"""
Test script to validate quantity calculations and Bybit API requirements
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal
from src.exchange.bybit_client import BybitClient

def test_quantity_rounding():
    """Test quantity rounding logic"""
    client = BybitClient()
    
    # Mock instrument specs for testing
    test_specs = {
        'BTCUSDT': {
            'symbol': 'BTCUSDT',
            'min_order_qty': 0.001,
            'max_order_qty': 1000.0,
            'qty_step': 0.001,
            'min_notional': 5.0,
            'price_tick': 0.1,
            'status': 'Trading'
        },
        'ETHUSDT': {
            'symbol': 'ETHUSDT', 
            'min_order_qty': 0.01,
            'max_order_qty': 10000.0,
            'qty_step': 0.01,
            'min_notional': 5.0,
            'price_tick': 0.01,
            'status': 'Trading'
        },
        'SOLUSDT': {
            'symbol': 'SOLUSDT',
            'min_order_qty': 0.1,
            'max_order_qty': 100000.0,
            'qty_step': 0.1,
            'min_notional': 5.0,
            'price_tick': 0.001,
            'status': 'Trading'
        }
    }
    
    # Cache the mock specs
    client.instrument_specs = test_specs
    
    print("🧪 Testing Quantity Rounding and Validation")
    print("=" * 50)
    
    # Test scenarios based on actual log data
    test_cases = [
        # BTC test cases
        {
            'symbol': 'BTCUSDT',
            'price': 118000.0,
            'balance': 9987.61,
            'allocation_pct': 0.07,
            'leverage': 10
        },
        # ETH test cases  
        {
            'symbol': 'ETHUSDT',
            'price': 3800.0,
            'balance': 9987.61,
            'allocation_pct': 0.07,
            'leverage': 10
        },
        # SOL test cases
        {
            'symbol': 'SOLUSDT',
            'price': 177.0,
            'balance': 9987.61,
            'allocation_pct': 0.07,
            'leverage': 10
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📊 Test Case {i}: {test_case['symbol']}")
        print("-" * 30)
        
        # Calculate raw quantity (same logic as trading system)
        position_value = test_case['balance'] * test_case['allocation_pct']
        leveraged_value = position_value * test_case['leverage']
        raw_quantity = leveraged_value / test_case['price']
        
        print(f"💰 Balance: ${test_case['balance']:,.2f}")
        print(f"📈 Position Value: ${position_value:.2f}")
        print(f"🔢 Leveraged Value: ${leveraged_value:.2f}")
        print(f"⚖️  Raw Quantity: {raw_quantity:.8f}")
        
        # Test quantity rounding
        rounded_qty = client.round_quantity(test_case['symbol'], raw_quantity)
        print(f"✅ Rounded Quantity: {rounded_qty:.8f}")
        
        # Test validation
        validation = client.validate_order_params(test_case['symbol'], raw_quantity, test_case['price'])
        
        print(f"🔍 Validation Result:")
        print(f"   Valid: {validation['valid']}")
        print(f"   Corrected Qty: {validation['corrected_qty']:.8f}")
        
        if validation['errors']:
            print(f"   ❌ Errors: {validation['errors']}")
        if validation['warnings']:
            print(f"   ⚠️  Warnings: {validation['warnings']}")
        
        # Calculate notional value
        notional = validation['corrected_qty'] * test_case['price']
        print(f"💵 Notional Value: ${notional:.2f}")
        
        # Check if this meets minimum requirements
        specs = test_specs[test_case['symbol']]
        meets_min_notional = notional >= specs['min_notional']
        print(f"✅ Meets Min Notional ({specs['min_notional']}): {meets_min_notional}")

def test_edge_cases():
    """Test edge cases that might cause issues"""
    client = BybitClient()
    
    # Mock specs with edge case values
    client.instrument_specs['TESTUSDT'] = {
        'symbol': 'TESTUSDT',
        'min_order_qty': 1.0,
        'max_order_qty': 100.0,
        'qty_step': 0.5,
        'min_notional': 10.0,
        'price_tick': 0.01,
        'status': 'Trading'
    }
    
    print("\n\n🧪 Testing Edge Cases")
    print("=" * 50)
    
    edge_cases = [
        {'qty': 0.3, 'price': 50.0, 'desc': 'Quantity below minimum'},
        {'qty': 1.7, 'price': 50.0, 'desc': 'Quantity between steps (should round down)'},
        {'qty': 150.0, 'price': 50.0, 'desc': 'Quantity above maximum'},
        {'qty': 0.8, 'price': 5.0, 'desc': 'Below minimum notional value'},
    ]
    
    for i, case in enumerate(edge_cases, 1):
        print(f"\n🔍 Edge Case {i}: {case['desc']}")
        print(f"   Input: qty={case['qty']}, price=${case['price']}")
        
        validation = client.validate_order_params('TESTUSDT', case['qty'], case['price'])
        
        print(f"   Valid: {validation['valid']}")
        print(f"   Corrected Qty: {validation['corrected_qty']}")
        print(f"   Errors: {validation['errors']}")

if __name__ == "__main__":
    test_quantity_rounding()
    test_edge_cases()
    print("\n✅ All tests completed!")