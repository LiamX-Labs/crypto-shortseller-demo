#!/usr/bin/env python3
"""
Trade Duration Tracker - Extract trade durations from logs without exchange queries
"""

import re
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class TradeDurationTracker:
    """Extract and track trade durations from log files"""
    
    def __init__(self, log_file_path: str = None):
        self.log_file_path = log_file_path or self.find_latest_log_file()
        
    def find_latest_log_file(self) -> str:
        """Find the most recent log file"""
        log_dir = Path("logs")
        if not log_dir.exists():
            return None
        
        log_files = list(log_dir.glob("multi_asset_*.log"))
        if not log_files:
            return None
        
        # Get the most recent log file
        latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
        return str(latest_log)
    
    def parse_trade_events_from_logs(self) -> Dict[str, List[Dict]]:
        """Parse trade entry/exit events from log files"""
        if not self.log_file_path or not Path(self.log_file_path).exists():
            logger.warning("Log file not found for trade duration analysis")
            return {}
        
        trade_events = {'BTC': [], 'ETH': [], 'SOL': []}
        
        # Regex patterns for trade events
        entry_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*🎯 (\w+): SHORT position opened at \$([0-9,]+\.\d+)'
        exit_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*🏁 (\w+): Position closed at \$([0-9,]+\.\d+)'
        
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # Check for trade entries
                    entry_match = re.search(entry_pattern, line)
                    if entry_match:
                        timestamp_str, asset, price = entry_match.groups()
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                        timestamp = timestamp.replace(tzinfo=timezone.utc)
                        
                        trade_events[asset].append({
                            'type': 'entry',
                            'timestamp': timestamp,
                            'price': float(price.replace(',', '')),
                            'raw_line': line.strip()
                        })
                    
                    # Check for trade exits
                    exit_match = re.search(exit_pattern, line)
                    if exit_match:
                        timestamp_str, asset, price = exit_match.groups()
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                        timestamp = timestamp.replace(tzinfo=timezone.utc)
                        
                        trade_events[asset].append({
                            'type': 'exit',
                            'timestamp': timestamp,
                            'price': float(price.replace(',', '')),
                            'raw_line': line.strip()
                        })
                        
        except Exception as e:
            logger.error(f"Error parsing log file: {e}")
        
        return trade_events
    
    def calculate_completed_trade_durations(self) -> Dict[str, List[Dict]]:
        """Calculate durations for completed trades from logs"""
        trade_events = self.parse_trade_events_from_logs()
        completed_trades = {'BTC': [], 'ETH': [], 'SOL': []}
        
        for asset in trade_events:
            events = sorted(trade_events[asset], key=lambda x: x['timestamp'])
            
            # Match entries with exits
            open_positions = []
            
            for event in events:
                if event['type'] == 'entry':
                    open_positions.append(event)
                elif event['type'] == 'exit' and open_positions:
                    # Match with most recent entry (FIFO)
                    entry_event = open_positions.pop(0)
                    duration = event['timestamp'] - entry_event['timestamp']
                    
                    # Format duration
                    total_seconds = int(duration.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    
                    completed_trades[asset].append({
                        'entry_time': entry_event['timestamp'],
                        'exit_time': event['timestamp'],
                        'entry_price': entry_event['price'],
                        'exit_price': event['price'],
                        'duration': duration,
                        'duration_formatted': f"{hours}h {minutes}m",
                        'duration_hours': duration.total_seconds() / 3600,
                        'pnl_pct': ((entry_event['price'] - event['price']) / entry_event['price']) * 100
                    })
        
        return completed_trades
    
    def get_trade_statistics(self) -> Dict[str, Dict]:
        """Get comprehensive trade duration statistics"""
        completed_trades = self.calculate_completed_trade_durations()
        stats = {}
        
        for asset in completed_trades:
            trades = completed_trades[asset]
            if not trades:
                stats[asset] = {'total_trades': 0}
                continue
            
            durations_hours = [trade['duration_hours'] for trade in trades]
            pnl_pcts = [trade['pnl_pct'] for trade in trades]
            
            stats[asset] = {
                'total_trades': len(trades),
                'avg_duration_hours': sum(durations_hours) / len(durations_hours),
                'min_duration_hours': min(durations_hours),
                'max_duration_hours': max(durations_hours),
                'avg_pnl_pct': sum(pnl_pcts) / len(pnl_pcts),
                'win_rate': len([pnl for pnl in pnl_pcts if pnl > 0]) / len(pnl_pcts) * 100,
                'recent_trades': trades[-5:]  # Last 5 trades
            }
        
        return stats

def demo_trade_duration_tracking():
    """Demonstrate trade duration tracking capabilities"""
    print("📊 TRADE DURATION TRACKING DEMO")
    print("=" * 50)
    
    tracker = TradeDurationTracker()
    
    if not tracker.log_file_path:
        print("❌ No log file found for analysis")
        return
    
    print(f"📄 Analyzing log file: {tracker.log_file_path}")
    
    # Get completed trade statistics
    stats = tracker.get_trade_statistics()
    
    for asset in ['BTC', 'ETH', 'SOL']:
        print(f"\n📈 {asset} Trade Duration Statistics:")
        if stats[asset]['total_trades'] == 0:
            print("   No completed trades found")
            continue
            
        print(f"   Total Trades: {stats[asset]['total_trades']}")
        print(f"   Average Duration: {stats[asset]['avg_duration_hours']:.2f}h")
        print(f"   Min Duration: {stats[asset]['min_duration_hours']:.2f}h")
        print(f"   Max Duration: {stats[asset]['max_duration_hours']:.2f}h")
        print(f"   Average P&L: {stats[asset]['avg_pnl_pct']:+.2f}%")
        print(f"   Win Rate: {stats[asset]['win_rate']:.1f}%")

if __name__ == "__main__":
    demo_trade_duration_tracking()