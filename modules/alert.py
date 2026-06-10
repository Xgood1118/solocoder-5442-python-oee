from modules.trend import get_daily_trend
from config import Config
from data.mock_data import get_all_lines, is_holiday
from datetime import date, timedelta
from copy import deepcopy


_alerts = []
_alert_id_counter = 1


def _next_alert_id():
    global _alert_id_counter
    aid = f'alert_{_alert_id_counter:05d}'
    _alert_id_counter += 1
    return aid


def check_continuous_low_oee(line_id=None, end_date=None, consecutive_days=None, threshold=None):
    if consecutive_days is None:
        consecutive_days = Config.ALERT_CONSECUTIVE_DAYS
    if threshold is None:
        threshold = Config.ALERT_OEE_THRESHOLD

    if end_date is None:
        end_date = date.today()
    elif isinstance(end_date, str):
        end_date = date.fromisoformat(end_date)

    if line_id:
        lines = [{'id': line_id}]
    else:
        lines = get_all_lines()

    alert_results = []

    for line in lines:
        lid = line['id']
        daily_trend = get_daily_trend(
            line_id=lid,
            start_date=(end_date - timedelta(days=consecutive_days * 5)).isoformat(),
            end_date=end_date.isoformat(),
        )

        production_days = [d for d in daily_trend if d['has_production']]
        production_days.sort(key=lambda x: x['date'], reverse=True)

        low_days = []
        matched_window = None
        for day in production_days:
            if day['oee'] < threshold:
                low_days.append(day)
                if len(low_days) >= consecutive_days:
                    matched_window = list(low_days)
                    break
            else:
                low_days = []

        if matched_window and len(matched_window) >= consecutive_days:
            matched_window.reverse()
            avg_oee = sum(d['oee'] for d in matched_window) / len(matched_window)
            alert = {
                'id': _next_alert_id(),
                'line_id': lid,
                'line_name': line.get('name', lid),
                'alert_type': 'continuous_low_oee',
                'severity': 'high',
                'message': f"{line.get('name', lid)} 连续 {consecutive_days} 天 OEE 低于 {int(threshold*100)}%",
                'consecutive_days': consecutive_days,
                'threshold': threshold,
                'low_days': [
                    {
                        'date': d['date'],
                        'oee': d['oee'],
                        'availability': d['availability'],
                        'performance': d['performance'],
                        'quality': d['quality'],
                    }
                    for d in matched_window
                ],
                'avg_oee': avg_oee,
                'start_date': matched_window[0]['date'],
                'end_date': matched_window[-1]['date'],
                'detected_at': end_date.isoformat(),
                'status': 'pending',
            }
            alert_results.append(alert)

    return alert_results


def generate_alerts(end_date=None):
    if end_date is None:
        end_date = date.today()
    elif isinstance(end_date, str):
        end_date = date.fromisoformat(end_date)

    new_alerts = check_continuous_low_oee(end_date=end_date)

    for alert in new_alerts:
        existing = [a for a in _alerts if a['line_id'] == alert['line_id']
                    and a['alert_type'] == alert['alert_type']
                    and a['status'] == 'pending']
        if not existing:
            _alerts.append(alert)

    return new_alerts


def list_alerts(status=None, line_id=None, alert_type=None):
    results = deepcopy(_alerts)

    if status:
        results = [a for a in results if a['status'] == status]
    if line_id:
        results = [a for a in results if a['line_id'] == line_id]
    if alert_type:
        results = [a for a in results if a['alert_type'] == alert_type]

    results.sort(key=lambda x: x['detected_at'], reverse=True)
    return results


def get_alert(alert_id):
    for alert in _alerts:
        if alert['id'] == alert_id:
            return deepcopy(alert)
    return None


def acknowledge_alert(alert_id, handler=None):
    for alert in _alerts:
        if alert['id'] == alert_id and alert['status'] == 'pending':
            alert['status'] = 'acknowledged'
            alert['handled_by'] = handler
            alert['acknowledged_at'] = date.today().isoformat()
            return deepcopy(alert)
    return None


def resolve_alert(alert_id, resolution=None, handler=None):
    for alert in _alerts:
        if alert['id'] == alert_id:
            alert['status'] = 'resolved'
            alert['resolution'] = resolution
            alert['resolved_by'] = handler
            alert['resolved_at'] = date.today().isoformat()
            return deepcopy(alert)
    return None


def get_alert_summary():
    total = len(_alerts)
    pending = sum(1 for a in _alerts if a['status'] == 'pending')
    acknowledged = sum(1 for a in _alerts if a['status'] == 'acknowledged')
    resolved = sum(1 for a in _alerts if a['status'] == 'resolved')

    line_counts = {}
    for a in _alerts:
        if a['status'] == 'pending':
            lid = a['line_id']
            if lid not in line_counts:
                line_counts[lid] = 0
            line_counts[lid] += 1

    return {
        'total': total,
        'pending': pending,
        'acknowledged': acknowledged,
        'resolved': resolved,
        'pending_by_line': line_counts,
    }
