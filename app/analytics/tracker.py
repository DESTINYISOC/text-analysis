import time
from datetime import datetime, date
from collections import defaultdict

class AnalyticsTracker:
    def __init__(self):
        self.daily_stats = defaultdict(lambda: defaultdict(int))
        self.request_logs = []
    
    def track_request(self, user_id: str, endpoint: str, 
                     text_length: int, processing_time: float):
        """Track an API request"""
        today = date.today()
        
        # Update daily stats
        self.daily_stats[today][user_id] += 1
        
        # Log request
        log_entry = {
            'timestamp': datetime.utcnow(),
            'user_id': user_id,
            'endpoint': endpoint,
            'text_length': text_length,
            'processing_time': processing_time,
            'status': 'success'
        }
        self.request_logs.append(log_entry)
        
        # Keep only last 1000 logs
        if len(self.request_logs) > 1000:
            self.request_logs = self.request_logs[-1000:]
    
    def get_user_stats(self, user_id: str) -> dict:
        """Get statistics for a specific user"""
        today = date.today()
        user_stats = {
            'requests_today': self.daily_stats[today][user_id],
            'total_requests': sum(stats[user_id] for stats in self.daily_stats.values()),
            'average_processing_time': 0,
            'favorite_endpoint': None
        }
        
        # Calculate averages
        user_logs = [log for log in self.request_logs if log['user_id'] == user_id]
        if user_logs:
            user_stats['average_processing_time'] = (
                sum(log['processing_time'] for log in user_logs) / len(user_logs)
            )
            
            # Find most used endpoint
            from collections import Counter
            endpoint_counts = Counter(log['endpoint'] for log in user_logs)
            user_stats['favorite_endpoint'] = endpoint_counts.most_common(1)[0][0]
        
        return user_stats
    
    def get_system_stats(self) -> dict:
        """Get overall system statistics"""
        today = date.today()
        
        return {
            'total_requests_today': sum(self.daily_stats[today].values()),
            'total_requests_all_time': sum(sum(stats.values()) for stats in self.daily_stats.values()),
            'active_users_today': len(self.daily_stats[today]),
            'average_response_time': self._calculate_average_response_time(),
            'requests_by_endpoint': self._get_requests_by_endpoint()
        }
    
    def _calculate_average_response_time(self) -> float:
        if not self.request_logs:
            return 0
        recent_logs = self.request_logs[-100:]  # Last 100 requests
        return sum(log['processing_time'] for log in recent_logs) / len(recent_logs)
    
    def _get_requests_by_endpoint(self) -> dict:
        from collections import Counter
        endpoint_counts = Counter(log['endpoint'] for log in self.request_logs[-1000:])
        return dict(endpoint_counts)