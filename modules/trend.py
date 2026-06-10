from modules.oee import get_oee_by_dimension, calculate_oee_aggregated
from modules.production import list_production_records
from datetime import date, timedelta
from utils.common import format_percent
from data.mock_data import is_holiday


def get_daily_trend(line_id=None, product_id=None, shift=None,
                    start_date=None, end_date=None):
    if not start_date or not end_date:
        end = date.today()
        start = end - timedelta(days=6)
    else:
        if isinstance(start_date, str):
            start = date.fromisoformat(start_date)
        else:
            start = start_date
        if isinstance(end_date, str):
            end = date.fromisoformat(end_date)
        else:
            end = end_date

    daily_data = get_oee_by_dimension(
        dimension='date', line_id=line_id, product_id=product_id,
        shift=shift, start_date=start_date, end_date=end_date
    )

    data_map = {item['key']: item for item in daily_data}

    trend = []
    current = start
    while current <= end:
        date_str = current.isoformat()
        if date_str in data_map:
            day_data = data_map[date_str]
            trend.append({
                'date': date_str,
                'oee': day_data['oee'],
                'availability': day_data['availability'],
                'performance': day_data['performance'],
                'quality': day_data['quality'],
                'oee_color': day_data['oee_color'],
                'has_production': True,
                'is_holiday': is_holiday(current),
            })
        else:
            trend.append({
                'date': date_str,
                'oee': 0,
                'availability': 0,
                'performance': 0,
                'quality': 0,
                'oee_color': 'gray',
                'has_production': False,
                'is_holiday': is_holiday(current),
            })
        current += timedelta(days=1)

    return trend


def get_weekly_comparison(line_id=None, product_id=None, shift=None,
                          reference_week=None, compare_week=None):
    if not reference_week:
        today = date.today()
        ref_start = today - timedelta(days=today.weekday() + 7)
        ref_end = ref_start + timedelta(days=6)
    else:
        ref_start, ref_end = _week_range(reference_week)

    if not compare_week:
        comp_start = ref_start - timedelta(days=7)
        comp_end = comp_start + timedelta(days=6)
    else:
        comp_start, comp_end = _week_range(compare_week)

    ref_oee = _get_period_oee(line_id, product_id, shift, ref_start.isoformat(), ref_end.isoformat())
    comp_oee = _get_period_oee(line_id, product_id, shift, comp_start.isoformat(), comp_end.isoformat())

    oee_diff = ref_oee['oee'] - comp_oee['oee']
    avail_diff = ref_oee['availability'] - comp_oee['availability']
    perf_diff = ref_oee['performance'] - comp_oee['performance']
    qual_diff = ref_oee['quality'] - comp_oee['quality']

    return {
        'reference_week': {
            'start': ref_start.isoformat(),
            'end': ref_end.isoformat(),
            'oee': ref_oee['oee'],
            'availability': ref_oee['availability'],
            'performance': ref_oee['performance'],
            'quality': ref_oee['quality'],
        },
        'compare_week': {
            'start': comp_start.isoformat(),
            'end': comp_end.isoformat(),
            'oee': comp_oee['oee'],
            'availability': comp_oee['availability'],
            'performance': comp_oee['performance'],
            'quality': comp_oee['quality'],
        },
        'comparison': {
            'oee_diff': oee_diff,
            'oee_diff_percent': format_percent(oee_diff),
            'oee_trend': 'up' if oee_diff > 0 else 'down' if oee_diff < 0 else 'flat',
            'availability_diff': avail_diff,
            'performance_diff': perf_diff,
            'quality_diff': qual_diff,
        },
    }


def get_monthly_comparison(line_id=None, product_id=None, shift=None,
                           reference_month=None, compare_month=None):
    if not reference_month:
        today = date.today()
        ref_start = date(today.year, today.month, 1)
        ref_end = today
    else:
        ref_start, ref_end = _month_range(reference_month)

    if not compare_month:
        comp_year = ref_start.year
        comp_month = ref_start.month - 1
        if comp_month <= 0:
            comp_month = 12
            comp_year -= 1
        comp_start, comp_end = _month_range(f"{comp_year}-{comp_month:02d}")
    else:
        comp_start, comp_end = _month_range(compare_month)

    ref_oee = _get_period_oee(line_id, product_id, shift, ref_start.isoformat(), ref_end.isoformat())
    comp_oee = _get_period_oee(line_id, product_id, shift, comp_start.isoformat(), comp_end.isoformat())

    oee_diff = ref_oee['oee'] - comp_oee['oee']
    avail_diff = ref_oee['availability'] - comp_oee['availability']
    perf_diff = ref_oee['performance'] - comp_oee['performance']
    qual_diff = ref_oee['quality'] - comp_oee['quality']

    return {
        'reference_month': {
            'start': ref_start.isoformat(),
            'end': ref_end.isoformat(),
            'oee': ref_oee['oee'],
            'availability': ref_oee['availability'],
            'performance': ref_oee['performance'],
            'quality': ref_oee['quality'],
        },
        'compare_month': {
            'start': comp_start.isoformat(),
            'end': comp_end.isoformat(),
            'oee': comp_oee['oee'],
            'availability': comp_oee['availability'],
            'performance': comp_oee['performance'],
            'quality': comp_oee['quality'],
        },
        'comparison': {
            'oee_diff': oee_diff,
            'oee_diff_percent': format_percent(oee_diff),
            'oee_trend': 'up' if oee_diff > 0 else 'down' if oee_diff < 0 else 'flat',
            'availability_diff': avail_diff,
            'performance_diff': perf_diff,
            'quality_diff': qual_diff,
        },
    }


def _get_period_oee(line_id, product_id, shift, start_date, end_date):
    records = list_production_records(
        line_id=line_id, product_id=product_id, shift=shift,
        start_date=start_date, end_date=end_date
    )
    return calculate_oee_aggregated(records)


def _week_range(week_str):
    if isinstance(week_str, int):
        week_num = week_str
        year = date.today().year
    else:
        parts = week_str.split('-W')
        if len(parts) == 2:
            year = int(parts[0])
            week_num = int(parts[1])
        else:
            year = date.today().year
            week_num = int(week_str.replace('W', ''))

    jan4 = date(year, 1, 4)
    start = jan4 - timedelta(days=jan4.isoweekday() - 1)
    start = start + timedelta(weeks=week_num - 1)
    end = start + timedelta(days=6)
    return start, end


def _month_range(month_str):
    parts = month_str.split('-')
    year = int(parts[0])
    month = int(parts[1])

    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    return start, end
