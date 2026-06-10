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
                'cycle_x_output': 0,
                'record_count': 0,
            }

        g = groups[key]
        g['total_output'] += r['total_output']
        g['good_output'] += r['good_output']
        g['defect_output'] += r['defect_output']
        g['planned_production_minutes'] += r['planned_production_minutes']
        g['actual_run_minutes'] += r['actual_run_minutes']
        g['theoretical_output'] += r['theoretical_output']
        g['cycle_x_output'] += (r.get('cycle_time_minutes', 0) or 0) * r['total_output']
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


def detect_routing_inconsistencies(line_id=None, start_date=None, end_date=None, tolerance_percent=5):
    from data.mock_data import get_routing as _get_routing

    records = list_production_records(
        line_id=line_id, start_date=start_date, end_date=end_date
    )

    inconsistencies = []
    seen_keys = set()

    for r in records:
        key = (r['product_id'], r['line_id'])
        if key in seen_keys:
            continue
        seen_keys.add(key)

        expected = _get_routing(r['product_id'], r['line_id'])
        expected_cycle = expected.get('cycle_time_minutes') if expected else None
        actual_cycle = r.get('cycle_time_minutes')

        if expected_cycle is None:
            inconsistencies.append({
                'product_id': r['product_id'],
                'line_id': r['line_id'],
                'issue': '产品-产线组合在工艺路线表中不存在，可能是换产线后未同步更新工艺路线',
                'expected_cycle_time': None,
                'actual_cycle_time': actual_cycle,
                'deviation_percent': None,
            })
            continue

        if actual_cycle is None:
            inconsistencies.append({
                'product_id': r['product_id'],
                'line_id': r['line_id'],
                'issue': '生产记录缺少标准工时数据',
                'expected_cycle_time': expected_cycle,
                'actual_cycle_time': None,
                'deviation_percent': None,
            })
            continue

        if expected_cycle <= 0:
            deviation = 100
        else:
            deviation = abs(actual_cycle - expected_cycle) / expected_cycle * 100

        if deviation > tolerance_percent:
            inconsistencies.append({
                'product_id': r['product_id'],
                'line_id': r['line_id'],
                'issue': f'实际使用节拍与工艺路线表偏差 {deviation:.1f}%，超过容差 {tolerance_percent}%，可能换产线或工艺更新未同步',
                'expected_cycle_time': expected_cycle,
                'actual_cycle_time': actual_cycle,
                'deviation_percent': round(deviation, 2),
            })

    return inconsistencies


def verify_downtime_consistency(line_id=None, shift=None, start_date=None, end_date=None):
    from modules.downtime import get_downtime_summary

    records = list_production_records(
        line_id=line_id, shift=shift, start_date=start_date, end_date=end_date
    )

    if not records:
        return {
            'valid': True,
            'total_planned_minutes': 0,
            'total_actual_run_minutes': 0,
            'sum_downtime_from_records': 0,
            'downtime_from_downtime_table': 0,
            'diff_minutes': 0,
            'mismatch_records': [],
            'note': '无生产记录',
        }

    total_planned = sum(r['planned_production_minutes'] for r in records)
    total_run = sum(r['actual_run_minutes'] for r in records)
    dt_sum_from_prod = sum(r.get('total_downtime_minutes', 0) for r in records)

    dt_summary = get_downtime_summary(
        line_id=line_id, shift=shift, start_date=start_date, end_date=end_date
    )
    dt_from_table = dt_summary['total_minutes']

    expected_run = total_planned - dt_sum_from_prod
    diff_run = total_run - expected_run

    mismatch_records = []
    for r in records:
        record_dt = r.get('total_downtime_minutes', None)
        expected_run_in_record = r['planned_production_minutes'] - (record_dt or 0)
        diff = r['actual_run_minutes'] - expected_run_in_record
        if abs(diff) > 0.5:
            mismatch_records.append({
                'record_id': r['id'],
                'date': r['date'],
                'shift': r['shift'],
                'line_id': r['line_id'],
                'product_id': r['product_id'],
                'planned': r['planned_production_minutes'],
                'downtime_in_record': record_dt,
                'expected_run': expected_run_in_record,
                'actual_run': r['actual_run_minutes'],
                'diff_minutes': round(diff, 2),
            })

    overall_diff = (total_planned - total_run) - dt_from_table

    return {
        'valid': abs(overall_diff) < 0.5 and len(mismatch_records) == 0,
        'total_planned_minutes': total_planned,
        'total_actual_run_minutes': total_run,
        'sum_downtime_from_production_records': dt_sum_from_prod,
        'downtime_from_downtime_table': dt_from_table,
        'expected_run_from_planned_minus_downtime_table': total_planned - dt_from_table,
        'overall_diff_minutes': round(overall_diff, 2),
        'mismatch_record_count': len(mismatch_records),
        'mismatch_records': mismatch_records[:50],
    }
