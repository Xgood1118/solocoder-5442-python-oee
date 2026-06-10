from data.mock_data import downtime_records
from copy import deepcopy
from config import Config


def list_downtime_records(line_id=None, category=None, shift=None,
                          start_date=None, end_date=None, is_big_loss=None):
    results = deepcopy(downtime_records)

    if line_id:
        results = [r for r in results if r['line_id'] == line_id]
    if category:
        results = [r for r in results if r['category'] == category]
    if shift:
        results = [r for r in results if r['shift'] == shift]
    if start_date:
        results = [r for r in results if r['date'] >= start_date]
    if end_date:
        results = [r for r in results if r['date'] <= end_date]
    if is_big_loss is not None:
        results = [r for r in results if r['is_big_loss'] == is_big_loss]

    return results


def get_downtime_record(record_id):
    for r in downtime_records:
        if r['id'] == record_id:
            return deepcopy(r)
    return None


def get_downtime_by_category(line_id=None, shift=None, start_date=None, end_date=None):
    records = list_downtime_records(line_id=line_id, shift=shift,
                                    start_date=start_date, end_date=end_date)

    category_totals = {}
    for cat_key, cat_info in Config.DOWNTIME_CATEGORIES.items():
        category_totals[cat_key] = {
            'category': cat_key,
            'name': cat_info['name'],
            'six_big_loss': cat_info['six_big_loss'],
            'total_minutes': 0,
            'count': 0,
            'big_loss_count': 0,
            'big_loss_minutes': 0,
        }

    for r in records:
        cat = r['category']
        if cat in category_totals:
            category_totals[cat]['total_minutes'] += r['duration_minutes']
            category_totals[cat]['count'] += 1
            if r['is_big_loss']:
                category_totals[cat]['big_loss_count'] += 1
                category_totals[cat]['big_loss_minutes'] += r['duration_minutes']

    result = list(category_totals.values())
    result.sort(key=lambda x: x['total_minutes'], reverse=True)
    return result


def get_downtime_summary(line_id=None, shift=None, start_date=None, end_date=None):
    records = list_downtime_records(line_id=line_id, shift=shift,
                                    start_date=start_date, end_date=end_date)

    total_minutes = sum(r['duration_minutes'] for r in records)
    big_loss_minutes = sum(r['duration_minutes'] for r in records if r['is_big_loss'])
    small_loss_minutes = total_minutes - big_loss_minutes

    return {
        'total_minutes': total_minutes,
        'total_count': len(records),
        'big_loss_minutes': big_loss_minutes,
        'big_loss_count': sum(1 for r in records if r['is_big_loss']),
        'small_loss_minutes': small_loss_minutes,
        'small_loss_count': sum(1 for r in records if not r['is_big_loss']),
    }


def get_big_loss_root_causes(line_id=None, start_date=None, end_date=None):
    records = list_downtime_records(line_id=line_id, start_date=start_date,
                                    end_date=end_date, is_big_loss=True)

    causes = {}
    for r in records:
        rc = r.get('root_cause') or '未记录'
        if rc not in causes:
            causes[rc] = {'root_cause': rc, 'total_minutes': 0, 'count': 0}
        causes[rc]['total_minutes'] += r['duration_minutes']
        causes[rc]['count'] += 1

    result = list(causes.values())
    result.sort(key=lambda x: x['total_minutes'], reverse=True)
    return result


def aggregate_downtime_by_dimension(dimension, line_id=None, category=None,
                                    shift=None, start_date=None, end_date=None):
    records = list_downtime_records(line_id=line_id, category=category, shift=shift,
                                    start_date=start_date, end_date=end_date)

    groups = {}
    from datetime import date
    for r in records:
        if dimension == 'line':
            key = r['line_id']
        elif dimension == 'category':
            key = r['category']
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
                'total_minutes': 0,
                'count': 0,
                'big_loss_minutes': 0,
                'big_loss_count': 0,
            }

        g = groups[key]
        g['total_minutes'] += r['duration_minutes']
        g['count'] += 1
        if r['is_big_loss']:
            g['big_loss_minutes'] += r['duration_minutes']
            g['big_loss_count'] += 1

    return list(groups.values())
