#!/usr/bin/env python3
"""
Simple BitShares Liquidity Pool Exchange Rate Calculator
Gets pool balances and calculates exchange rate with proper precision
"""

import requests
import json
from decimal import Decimal, getcontext

# Set high precision for calculations
getcontext().prec = 28

def get_pool_data(pool_id="1.19.507"):
    """Get liquidity pool data from BitShares API"""
    
    # Multiple API endpoints to try
    api_urls = [
        "https://api.bts.mobi",
        "https://api.dex.trading", 
        "https://dexnode.net"
    ]
    
    for api_url in api_urls:
        try:
            print(f"Trying API: {api_url}")
            
            # RPC call to get pool object
            payload = {
                "id": 1,
                "method": "call",
                "params": [0, "get_objects", [[pool_id]]]
            }
            
            response = requests.post(
                f"{api_url}/rpc", 
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("result") and len(data["result"]) > 0 and data["result"][0]:
                    print(f"✓ Successfully got data from {api_url}")
                    return data["result"][0]
            
        except Exception as e:
            print(f"✗ Failed {api_url}: {e}")
            continue
    
    print("Failed to get data from any API endpoint")
    return None

def calculate_exchange_rate(pool_data, asset_a_precision=4, asset_b_precision=2):
    """
    Calculate exchange rate between two assets in the pool
    
    Args:
        pool_data: Pool object from BitShares API
        asset_a_precision: Decimal precision for asset A (default: 4 for 1.3.6268)
        asset_b_precision: Decimal precision for asset B (default: 2 for 1.3.6574)
    """
    
    # Extract raw balances
    balance_a_raw = pool_data.get("balance_a", "0")
    balance_b_raw = pool_data.get("balance_b", "0")
    asset_a_id = pool_data.get("asset_a")
    asset_b_id = pool_data.get("asset_b")
    
    print(f"Asset A ID: {asset_a_id}")
    print(f"Asset B ID: {asset_b_id}")
    print(f"Raw Balance A: {balance_a_raw}")
    print(f"Raw Balance B: {balance_b_raw}")
    
    # Convert to actual amounts using precision
    balance_a = Decimal(balance_a_raw) / (Decimal(10) ** asset_a_precision)
    balance_b = Decimal(balance_b_raw) / (Decimal(10) ** asset_b_precision)
    
    print(f"Actual Balance A: {balance_a}")
    print(f"Actual Balance B: {balance_b}")
    
    if balance_a == 0 or balance_b == 0:
        print("Warning: One of the balances is zero!")
        return None, None
    
    # Calculate exchange rates
    # Rate A/B = how much B you get for 1 A
    rate_a_to_b = balance_b / balance_a
    
    # Rate B/A = how much A you get for 1 B  
    rate_b_to_a = balance_a / balance_b
    
    return rate_a_to_b, rate_b_to_a

def main():
    """Main function to get pool data and calculate rates"""
    
    pool_id = "1.19.507"
    
    # Known asset precisions
    asset_a_precision = 4  # for 1.3.6268
    asset_b_precision = 2  # for 1.3.6574
    
    print(f"Getting data for pool {pool_id}")
    print(f"Asset A (1.3.6268) precision: {asset_a_precision}")
    print(f"Asset B (1.3.6574) precision: {asset_b_precision}")
    print("-" * 50)
    
    # Get pool data
    pool_data = get_pool_data(pool_id)
    
    if not pool_data:
        print("Failed to retrieve pool data")
        return
    
    print("-" * 50)
    
    # Calculate exchange rates
    rate_a_to_b, rate_b_to_a = calculate_exchange_rate(
        pool_data, 
        asset_a_precision, 
        asset_b_precision
    )
    
    if rate_a_to_b is None:
        print("Could not calculate exchange rates")
        return
    
    print("-" * 50)
    print("EXCHANGE RATES:")
    print(f"Asset A → Asset B: {rate_a_to_b:.8f}")
    print(f"Asset B → Asset A: {rate_b_to_a:.8f}")
    print("-" * 50)
    
    # Additional pool info
    if "taker_fee_percent" in pool_data:
        print(f"Taker Fee: {pool_data['taker_fee_percent'] / 100}%")
    
    # Constant product (k = x * y)
    k = (Decimal(pool_data.get("balance_a", "0")) / (Decimal(10) ** asset_a_precision)) * \
        (Decimal(pool_data.get("balance_b", "0")) / (Decimal(10) ** asset_b_precision))
    print(f"Constant Product (k): {k}")

    print("-" * 50)
    print("BRIDGE EXCHANGE:")
    
    # Get user input for bridge exchange
    asset_input = input("Enter asset to exchange (XBTSX.WRAM/BTWTY.EOS): ").strip().upper()
    amount_input = Decimal(input("Enter amount to exchange: "))
    
    bridge_rate_multiplier = Decimal("0.975")
    
    if asset_input == "XBTSX.WRAM":
        # XBTSX.WRAM is Asset B (1.3.6574)
        bridge_exchange_rate = rate_b_to_a * bridge_rate_multiplier
        exchanged_amount = amount_input * bridge_exchange_rate
        print(f"Bridge Exchange Rate (XBTSX.WRAM -> BTWTY.EOS): {bridge_exchange_rate:.8f}")
        print(f"Exchanged Amount: {exchanged_amount:.4f} BTWTY.EOS")
        
    elif asset_input == "BTWTY.EOS":
        # BTWTY.EOS is Asset A (1.3.6268)
        bridge_exchange_rate = rate_a_to_b * bridge_rate_multiplier
        exchanged_amount = amount_input * bridge_exchange_rate
        print(f"Bridge Exchange Rate (BTWTY.EOS -> XBTSX.WRAM): {bridge_exchange_rate:.8f}")
        print(f"Exchanged Amount: {exchanged_amount:.2f} XBTSX.WRAM")
        
    else:
        print("Invalid asset entered. Please choose XBTSX.WRAM or BTWTY.EOS.")

def get_single_rate(pool_id="1.19.507", precision_a=4, precision_b=2):
    """Simple function that just returns the exchange rate A/B"""
    pool_data = get_pool_data(pool_id)
    if pool_data:
        balance_a = Decimal(pool_data.get("balance_a", "0")) / (Decimal(10) ** precision_a)
        balance_b = Decimal(pool_data.get("balance_b", "0")) / (Decimal(10) ** precision_b)
        if balance_a > 0:
            return float(balance_b / balance_a)
    return None

if __name__ == "__main__":
    main()