from flask import Blueprint, request, jsonify
from modules.report import (
    generate_shift_daily_report,
    generate_workshop_weekly_report,
    generate_factory_monthly_report,
    list_available_reports,
)
from modules.trend import (
    get_daily_trend,
    get_weekly_comparison,
    get_monthly_comparison,
)

report_bp = Blueprint('report', __name__)


@report_bp.route('/types', methods=['GET'])
def report_types():
    results = list_available_reports()
    return jsonify(results)


@report_bp.route('/shift-daily', methods=['GET'])
def shift_daily():
    line_id = request.args.get('line_id')
    shift = request.args.get('shift')
    target_date = request.args.get('date')

    if not line_id or not shift:
        return jsonify({'error': 'line_id and shift are required'}), 400

    result = generate_shift_daily_report(
        line_id=line_id, shift=shift, target_date=target_date
    )
    return jsonify(result)


@report_bp.route('/workshop-weekly', methods=['GET'])
def workshop_weekly():
    workshop = request.args.get('workshop')
    week_start = request.args.get('week_start')
    week_end = request.args.get('week_end')

    if not workshop:
        return jsonify({'error': 'workshop is required'}), 400

    result = generate_workshop_weekly_report(
        workshop=workshop, week_start=week_start, week_end=week_end
    )
    return jsonify(result)


@report_bp.route('/factory-monthly', methods=['GET'])
def factory_monthly():
    month_start = request.args.get('month_start')
    month_end = request.args.get('month_end')

    result = generate_factory_monthly_report(
        month_start=month_start, month_end=month_end
    )
    return jsonify(result)


@report_bp.route('/trend/daily', methods=['GET'])
def daily_trend():
    line_id = request.args.get('line_id')
    product_id = request.args.get('product_id')
    shift = request.args.get('shift')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    result = get_daily_trend(
        line_id=line_id, product_id=product_id, shift=shift,
        start_date=start_date, end_date=end_date
    )
    return jsonify(result)


@report_bp.route('/trend/weekly-comparison', methods=['GET'])
def weekly_comparison():
    line_id = request.args.get('line_id')
    product_id = request.args.get('product_id')
    shift = request.args.get('shift')
    reference_week = request.args.get('reference_week')
    compare_week = request.args.get('compare_week')

    result = get_weekly_comparison(
        line_id=line_id, product_id=product_id, shift=shift,
        reference_week=reference_week, compare_week=compare_week
    )
    return jsonify(result)


@report_bp.route('/trend/monthly-comparison', methods=['GET'])
def monthly_comparison():
    line_id = request.args.get('line_id')
    product_id = request.args.get('product_id')
    shift = request.args.get('shift')
    reference_month = request.args.get('reference_month')
    compare_month = request.args.get('compare_month')

    result = get_monthly_comparison(
        line_id=line_id, product_id=product_id, shift=shift,
        reference_month=reference_month, compare_month=compare_month
    )
    return jsonify(result)
