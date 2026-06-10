from modules.production import list_production_records, aggregate_production_by_dimension
from modules.downtime import get_downtime_summary, get_downtime_by_category
from utils.common import get_color_level, get_oee_grade, format_percent
from data.mock_data import get_routing, get_all_lines
from config import Config
from datetime import date, timedelta


def calculate_oee_for_record(prod_record):
    planned_minutes = prod_record['planned_production_minutes']
    actual_run_minutes = prod_record['actual_run_minutes']
    total_output = prod_record['total_output']
    good_output = prod_record['good_output']
    theoretical_output = prod_record['theoretical_output']

    if planned_minutes <= 0:
        availability = 0
    else:
        availability = actual_run_minutes / planned_minutes

    if theoretical_output <= 0:
        performance = 0
    else:
        performance = total_output / theoretical_output

    if total_output <= 0:
        quality = 0
    else:
        quality = good_output / total_output

    oee = availability * performance * quality

    return {
        'availability': availability,
        'performance': performance,
        'quality': quality,
        'oee': oee,
        'availability_color': get_color_level(availability),
        'performance_color': get_color_level(performance),
        'quality_color': get_color_level(quality),
        'oee_color': get_color_level(oee),
    }


def calculate_oee_aggregated(records):
    if not records:
        return {
            'availability': 0,
            'performance': 0,
            'quality': 0,
            'oee': 0,
            'availability_color': 'red',
            'performance_color': 'red',
            'quality_color': 'red',
            'oee_color': 'red',
            'record_count': 0,
        }

    total_planned = sum(r['planned_production_minutes'] for r in records)
    total_run = sum(r['actual_run_minutes'] for r in records)
    total_output = sum(r['total_output'] for r in records)
    total_good = sum(r['good_output'] for r in records)
    total_theoretical = sum(r['theoretical_output'] for r in records)

    if total_planned <= 0:
        availability = 0
    else:
        availability = total_run / total_planned

    if total_theoretical <= 0:
        performance = 0
    else:
        performance = total_output / total_theoretical

    if total_output <= 0:
        quality = 0
    else:
        quality = total_good / total_output

    oee = availability * performance * quality

    grade = get_oee_grade(oee)

    return {
        'availability': availability,
        'performance': performance,
        'quality': quality,
        'oee': oee,
        'availability_color': get_color_level(availability),
        'performance_color': get_color_level(performance),
        'quality_color': get_color_level(quality),
        'oee_color': get_color_level(oee),
        'oee_grade': grade['grade'],
        'oee_grade_name': grade['name'],
        'oee_grade_desc': grade['description'],
        'record_count': len(records),
    }


def get_oee_by_line(line_id=None, start_date=None, end_date=None, shift=None, product_id=None):
    records = list_production_records(
        line_id=line_id, product_id=product_id, shift=shift,
        start_date=start_date, end_date=end_date
    )
    return calculate_oee_aggregated(records)


def get_oee_by_dimension(dimension, line_id=None, product_id=None,
                         shift=None, start_date=None, end_date=None):
    agg_data = aggregate_production_by_dimension(
        dimension=dimension, line_id=line_id, product_id=product_id,
        shift=shift, start_date=start_date, end_date=end_date
    )

    results = []
    for item in agg_data:
        if item['planned_production_minutes'] <= 0:
            availability = 0
        else:
            availability = item['actual_run_minutes'] / item['planned_production_minutes']

        if item['theoretical_output'] <= 0:
            performance = 0
        else:
            performance = item['total_output'] / item['theoretical_output']

        if item['total_output'] <= 0:
            quality = 0
        else:
            quality = item['good_output'] / item['total_output']

        oee = availability * performance * quality
        grade = get_oee_grade(oee)

        results.append({
            'key': item['key'],
            'availability': availability,
            'performance': performance,
            'quality': quality,
            'oee': oee,
            'availability_color': get_color_level(availability),
            'performance_color': get_color_level(performance),
            'quality_color': get_color_level(quality),
            'oee_color': get_color_level(oee),
            'oee_grade': grade['grade'],
            'oee_grade_name': grade['name'],
            'total_output': item['total_output'],
            'good_output': item['good_output'],
        })

    return results


def get_oee_detail(line_id, product_id=None, shift=None, start_date=None, end_date=None):
    records = list_production_records(
        line_id=line_id, product_id=product_id, shift=shift,
        start_date=start_date, end_date=end_date
    )

    oee_summary = calculate_oee_aggregated(records)
    downtime_summary = get_downtime_summary(
        line_id=line_id, shift=shift, start_date=start_date, end_date=end_date
    )
    downtime_by_category = get_downtime_by_category(
        line_id=line_id, shift=shift, start_date=start_date, end_date=end_date
    )

    return {
        'line_id': line_id,
        'oee_summary': oee_summary,
        'downtime_summary': downtime_summary,
        'downtime_by_category': downtime_by_category,
        'record_count': len(records),
    }


def get_all_lines_oee(start_date=None, end_date=None):
    lines = get_all_lines()
    results = []

    for line in lines:
        line_oee = get_oee_by_line(
            line_id=line['id'], start_date=start_date, end_date=end_date
        )
        line_oee['line_id'] = line['id']
        line_oee['line_name'] = line['name']
        line_oee['workshop'] = line['workshop']
        results.append(line_oee)

    results.sort(key=lambda x: x['oee'], reverse=True)
    return results


def validate_planned_time_boundary(line_id, shift_key, target_date):
    from modules.production import get_shifted_planned_minutes

    records = list_production_records(
        line_id=line_id, shift=shift_key, start_date=target_date, end_date=target_date
    )

    if not records:
        return {
            'valid': False,
            'issue': '该班次无生产记录，无法验证计划时间',
            'planned_minutes': None,
            'actual_minutes': None,
        }

    record = records[0]
    expected_planned = get_shifted_planned_minutes(line_id, shift_key, target_date)
    actual_planned = record['planned_production_minutes']

    diff = abs(expected_planned - actual_planned)
    is_valid = diff <= 5

    return {
        'valid': is_valid,
        'issue': None if is_valid else f'计划生产时间偏差 {diff} 分钟，可能存在班次交接时间定义不清',
        'expected_planned_minutes': expected_planned,
        'actual_planned_minutes': actual_planned,
        'diff_minutes': diff,
    }
