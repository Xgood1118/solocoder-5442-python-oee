from data.mock_data import production_records, get_all_lines, get_all_products, get_routing, is_holiday
from copy import deepcopy
from datetime import date, timedelta


def list_production_records(line_id=None, product_id=None, shift=None, start_date=None, end_date=None):
    results = deepcopy(production_records)

    if line_id:
        results = [r for r in results if r['line_id'] == line_id]
    if product_id:
        results = [r for r in results if r['product_id'] == product_id]
    if shift:
        results = [r for r in results if r['shift'] == shift]
    if start_date:
        results = [r for r in results if r['date'] >= start_date]
    if end_date:
        results = [r for r in results if r['date'] <= end_date]

    return results


def get_production_record(record_id):
    for r in production_records:
        if r['id'] == record_id:
            return deepcopy(r)
    return None


def aggregate_production_by_dimension(dimension, line_id=None, product_id=None,
                                       shift=None, start_date=None, end_date=None):
    records = list_production_records(line_id, product_id, shift, start_date, end_date)

    groups = {}
    for r in records:
        if dimension == 'line':
            key = r['line_id']
        elif dimension == 'product':
            key = r['product_id']
        elif dimension == 'shift':
            key = r['shift']
        elif dimension == 'date':
            key = r['date']
        elif dimension == 'week':
            d = date.fromisoformat(r['date'])
            key = d.isocalendar()[1]
            key = f'W{key}'
        elif dimension == 'month':
            d = date.fromisoformat(r['date'])
            key = f"{d.year}-{d.month:02d}"
        else:
            key = r['line_id']

        if key not in groups:
            groups[key] = {
                'key': key,
                'total_output': 0,
                'good_output': 0,
                'defect_output': 0,
                'planned_production_minutes': 0,
                'actual_run_minutes': 0,
                'theoretical_output': 0,
                'record_count': 0,
            }

        g = groups[key]
        g['total_output'] += r['total_output']
        g['good_output'] += r['good_output']
        g['defect_output'] += r['defect_output']
        g['planned_production_minutes'] += r['planned_production_minutes']
        g['actual_run_minutes'] += r['actual_run_minutes']
        g['theoretical_output'] += r['theoretical_output']
        g['record_count'] += 1

    return list(groups.values())


def get_shifted_planned_minutes(line_id, shift_key, target_date):
    from config import Config

    shift_config = Config.SHIFTS.get(shift_key, {})
    base_planned = shift_config.get('planned_minutes', 480)
    break_minutes = shift_config.get('break_minutes', 60)

    effective_planned = base_planned - break_minutes

    if isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)

    if is_holiday(target_date):
        effective_planned = max(0, effective_planned - 240)

    return effective_planned


def validate_routing_consistency(product_id, line_id):
    routing = get_routing(product_id, line_id)
    if not routing:
        return {
            'valid': False,
            'issue': '未找到该产品在该产线的工艺路线',
            'cycle_time': None,
        }

    cycle_time = routing.get('cycle_time_minutes')
    if cycle_time is None or cycle_time <= 0:
        return {
            'valid': False,
            'issue': '工艺路线标准工时数据无效',
            'cycle_time': cycle_time,
        }

    return {
        'valid': True,
        'issue': None,
        'cycle_time': cycle_time,
    }
