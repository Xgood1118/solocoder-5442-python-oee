from modules.oee import get_oee_by_line, get_oee_by_dimension, get_all_lines_oee
from modules.downtime import get_downtime_summary, get_downtime_by_category
from modules.production import aggregate_production_by_dimension
from modules.loss import get_loss_pareto
from modules.alert import generate_alerts, list_alerts
from utils.common import get_oee_grade, format_percent
from data.mock_data import get_all_lines
from datetime import date, timedelta
from config import Config


def generate_shift_daily_report(line_id, shift, target_date=None):
    if target_date is None:
        target_date = date.today()
    elif isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)

    date_str = target_date.isoformat()

    oee = get_oee_by_line(
        line_id=line_id, shift=shift, start_date=date_str, end_date=date_str
    )

    downtime_summary = get_downtime_summary(
        line_id=line_id, shift=shift, start_date=date_str, end_date=date_str
    )

    downtime_categories = get_downtime_by_category(
        line_id=line_id, shift=shift, start_date=date_str, end_date=date_str
    )

    production_agg = aggregate_production_by_dimension(
        dimension='product', line_id=line_id, shift=shift,
        start_date=date_str, end_date=date_str
    )

    pareto = get_loss_pareto(
        line_id=line_id, shift=shift, start_date=date_str, end_date=date_str
    )

    line_info = next((l for l in get_all_lines() if l['id'] == line_id), {})

    grade = get_oee_grade(oee['oee'])

    return {
        'report_type': 'shift_daily',
        'report_level': '班组长',
        'line_id': line_id,
        'line_name': line_info.get('name', line_id),
        'workshop': line_info.get('workshop', ''),
        'shift': shift,
        'shift_name': Config.SHIFTS.get(shift, {}).get('name', shift),
        'date': date_str,
        'weekday': target_date.strftime('%A'),
        'oee_summary': {
            'oee': oee['oee'],
            'oee_color': oee['oee_color'],
            'oee_grade': grade['grade'],
            'oee_grade_name': grade['name'],
            'availability': oee['availability'],
            'availability_color': oee['availability_color'],
            'performance': oee['performance'],
            'performance_color': oee['performance_color'],
            'quality': oee['quality'],
            'quality_color': oee['quality_color'],
        },
        'production': {
            'products': [
                {
                    'product_id': p['key'],
                    'total_output': p['total_output'],
                    'good_output': p['good_output'],
                    'defect_output': p['defect_output'],
                }
                for p in production_agg
            ],
            'total_output': sum(p['total_output'] for p in production_agg),
            'total_good': sum(p['good_output'] for p in production_agg),
        },
        'downtime': downtime_summary,
        'downtime_categories': downtime_categories,
        'loss_pareto': pareto,
        'generated_at': date.today().isoformat(),
    }


def generate_workshop_weekly_report(workshop, week_start=None, week_end=None):
    if week_start is None:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
    elif isinstance(week_start, str):
        week_start = date.fromisoformat(week_start)
    if week_end is None:
        week_end = week_start + timedelta(days=6)
    elif isinstance(week_end, str):
        week_end = date.fromisoformat(week_end)

    lines = [l for l in get_all_lines() if l.get('workshop') == workshop]

    line_reports = []
    for line in lines:
        oee = get_oee_by_line(
            line_id=line['id'],
            start_date=week_start.isoformat(),
            end_date=week_end.isoformat(),
        )
        downtime = get_downtime_summary(
            line_id=line['id'],
            start_date=week_start.isoformat(),
            end_date=week_end.isoformat(),
        )
        grade = get_oee_grade(oee['oee'])

        line_reports.append({
            'line_id': line['id'],
            'line_name': line['name'],
            'oee': oee['oee'],
            'oee_color': oee['oee_color'],
            'oee_grade': grade['grade'],
            'oee_grade_name': grade['name'],
            'availability': oee['availability'],
            'performance': oee['performance'],
            'quality': oee['quality'],
            'downtime_minutes': downtime['total_minutes'],
            'downtime_count': downtime['total_count'],
        })

    line_reports.sort(key=lambda x: x['oee'], reverse=True)

    avg_oee = sum(l['oee'] for l in line_reports) / len(line_reports) if line_reports else 0
    avg_availability = sum(l['availability'] for l in line_reports) / len(line_reports) if line_reports else 0
    avg_performance = sum(l['performance'] for l in line_reports) / len(line_reports) if line_reports else 0
    avg_quality = sum(l['quality'] for l in line_reports) / len(line_reports) if line_reports else 0

    pareto = get_loss_pareto(
        start_date=week_start.isoformat(),
        end_date=week_end.isoformat(),
    )

    weekly_alerts = list_alerts()
    weekly_alerts = [a for a in weekly_alerts
                     if week_start.isoformat() <= a['detected_at'] <= week_end.isoformat()]

    grade = get_oee_grade(avg_oee)

    return {
        'report_type': 'workshop_weekly',
        'report_level': '车间主任',
        'workshop': workshop,
        'week_start': week_start.isoformat(),
        'week_end': week_end.isoformat(),
        'summary': {
            'line_count': len(lines),
            'avg_oee': avg_oee,
            'avg_oee_color': grade['grade'] == 'world_class' and 'green' or grade['grade'] == 'excellent' and 'green' or grade['grade'] == 'average' and 'yellow' or 'red',
            'avg_oee_grade': grade['grade'],
            'avg_oee_grade_name': grade['name'],
            'avg_availability': avg_availability,
            'avg_performance': avg_performance,
            'avg_quality': avg_quality,
        },
        'lines': line_reports,
        'loss_pareto': pareto,
        'alerts': {
            'count': len(weekly_alerts),
            'items': weekly_alerts,
        },
        'generated_at': date.today().isoformat(),
    }


def generate_factory_monthly_report(month_start=None, month_end=None):
    if month_start is None:
        today = date.today()
        month_start = date(today.year, today.month, 1)
    elif isinstance(month_start, str):
        month_start = date.fromisoformat(month_start)

    if month_end is None:
        if month_start.month == 12:
            month_end = date(month_start.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(month_start.year, month_start.month + 1, 1) - timedelta(days=1)
    elif isinstance(month_end, str):
        month_end = date.fromisoformat(month_end)

    lines = get_all_lines()
    workshops = set(l.get('workshop', '') for l in lines)

    line_reports = []
    for line in lines:
        oee = get_oee_by_line(
            line_id=line['id'],
            start_date=month_start.isoformat(),
            end_date=month_end.isoformat(),
        )
        grade = get_oee_grade(oee['oee'])
        line_reports.append({
            'line_id': line['id'],
            'line_name': line['name'],
            'workshop': line.get('workshop', ''),
            'oee': oee['oee'],
            'oee_grade': grade['grade'],
            'oee_grade_name': grade['name'],
            'availability': oee['availability'],
            'performance': oee['performance'],
            'quality': oee['quality'],
        })

    line_reports.sort(key=lambda x: x['oee'], reverse=True)

    workshop_reports = {}
    for ws in workshops:
        ws_lines = [l for l in line_reports if l['workshop'] == ws]
        if ws_lines:
            avg_oee = sum(l['oee'] for l in ws_lines) / len(ws_lines)
            grade = get_oee_grade(avg_oee)
            workshop_reports[ws] = {
                'workshop': ws,
                'line_count': len(ws_lines),
                'avg_oee': avg_oee,
                'oee_grade': grade['grade'],
                'oee_grade_name': grade['name'],
            }

    factory_avg_oee = sum(l['oee'] for l in line_reports) / len(line_reports) if line_reports else 0
    factory_avg_avail = sum(l['availability'] for l in line_reports) / len(line_reports) if line_reports else 0
    factory_avg_perf = sum(l['performance'] for l in line_reports) / len(line_reports) if line_reports else 0
    factory_avg_qual = sum(l['quality'] for l in line_reports) / len(line_reports) if line_reports else 0

    grade = get_oee_grade(factory_avg_oee)

    pareto = get_loss_pareto(
        start_date=month_start.isoformat(),
        end_date=month_end.isoformat(),
    )

    monthly_alerts = list_alerts()
    monthly_alerts = [a for a in monthly_alerts
                      if month_start.isoformat() <= a['detected_at'] <= month_end.isoformat()]

    return {
        'report_type': 'factory_monthly',
        'report_level': '厂长',
        'month': f"{month_start.year}-{month_start.month:02d}",
        'month_start': month_start.isoformat(),
        'month_end': month_end.isoformat(),
        'summary': {
            'workshop_count': len(workshops),
            'line_count': len(lines),
            'factory_avg_oee': factory_avg_oee,
            'factory_avg_oee_grade': grade['grade'],
            'factory_avg_oee_grade_name': grade['name'],
            'factory_avg_availability': factory_avg_avail,
            'factory_avg_performance': factory_avg_perf,
            'factory_avg_quality': factory_avg_qual,
            'world_class_count': sum(1 for l in line_reports if l['oee_grade'] == 'world_class'),
            'excellent_count': sum(1 for l in line_reports if l['oee_grade'] == 'excellent'),
            'average_count': sum(1 for l in line_reports if l['oee_grade'] == 'average'),
            'poor_count': sum(1 for l in line_reports if l['oee_grade'] == 'poor'),
        },
        'workshops': list(workshop_reports.values()),
        'lines_ranking': line_reports,
        'loss_pareto': pareto,
        'alerts': {
            'total_count': len(monthly_alerts),
            'pending_count': sum(1 for a in monthly_alerts if a['status'] == 'pending'),
        },
        'generated_at': date.today().isoformat(),
    }


def list_available_reports():
    return [
        {'type': 'shift_daily', 'name': '班次日报', 'audience': '班组长', 'level': 1},
        {'type': 'workshop_weekly', 'name': '车间周报', 'audience': '车间主任', 'level': 2},
        {'type': 'factory_monthly', 'name': '工厂月报', 'audience': '厂长', 'level': 3},
    ]
