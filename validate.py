import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("OEE System Validation Test")
print("=" * 60)

tests_passed = 0
tests_failed = 0


def test(name, fn):
    global tests_passed, tests_failed
    try:
        fn()
        print(f"  [PASS] {name}")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        import traceback
        traceback.print_exc()
        tests_failed += 1


print("\n1. Testing Data Layer...")


def test_mock_data():
    from data.mock_data import production_lines, products, routing, production_records, downtime_records, holidays
    assert len(production_lines) == 4, f"Expected 4 lines, got {len(production_lines)}"
    assert len(products) == 3, f"Expected 3 products, got {len(products)}"
    assert len(routing) > 0, "No routing data"
    assert len(production_records) > 0, "No production records"
    assert len(downtime_records) > 0, "No downtime records"
    assert len(holidays) > 0, "No holidays"
    print(f"    Production lines: {len(production_lines)}")
    print(f"    Products: {len(products)}")
    print(f"    Production records: {len(production_records)}")
    print(f"    Downtime records: {len(downtime_records)}")
    print(f"    Holidays: {len(holidays)}")


test("Mock data loaded", test_mock_data)

print("\n2. Testing Production Module...")


def test_production_module():
    from modules.production import list_production_records, aggregate_production_by_dimension

    records = list_production_records()
    assert len(records) > 0

    line1_records = list_production_records(line_id='line_01')
    assert len(line1_records) > 0

    by_line = aggregate_production_by_dimension('line')
    assert len(by_line) > 0
    print(f"    Aggregated by line: {len(by_line)} entries")

    by_product = aggregate_production_by_dimension('product')
    assert len(by_product) > 0
    print(f"    Aggregated by product: {len(by_product)} entries")

    by_week = aggregate_production_by_dimension('week')
    assert len(by_week) > 0
    print(f"    Aggregated by week: {len(by_week)} entries")


test("Production module works", test_production_module)

print("\n3. Testing Downtime Module...")


def test_downtime_module():
    from modules.downtime import list_downtime_records, get_downtime_summary, get_downtime_by_category

    records = list_downtime_records()
    assert len(records) > 0

    summary = get_downtime_summary()
    assert summary['total_minutes'] > 0
    print(f"    Total downtime minutes: {summary['total_minutes']}")
    print(f"    Big loss minutes: {summary['big_loss_minutes']}")

    by_cat = get_downtime_by_category()
    assert len(by_cat) > 0
    print(f"    Downtime categories: {len(by_cat)}")


test("Downtime module works", test_downtime_module)

print("\n4. Testing OEE Module...")


def test_oee_module():
    from modules.oee import calculate_oee_for_record, get_oee_by_line, get_oee_by_dimension, get_all_lines_oee
    from data.mock_data import production_records

    oee_result = calculate_oee_for_record(production_records[0])
    assert 'availability' in oee_result
    assert 'performance' in oee_result
    assert 'quality' in oee_result
    assert 'oee' in oee_result
    assert 'oee_color' in oee_result
    assert 0 <= oee_result['oee'] <= 1
    print(f"    Sample OEE: {oee_result['oee']:.2%}")
    print(f"    Availability: {oee_result['availability']:.2%} ({oee_result['availability_color']})")
    print(f"    Performance: {oee_result['performance']:.2%} ({oee_result['performance_color']})")
    print(f"    Quality: {oee_result['quality']:.2%} ({oee_result['quality_color']})")

    line_oee = get_oee_by_line(line_id='line_01')
    assert 'oee' in line_oee
    assert 'oee_grade' in line_oee
    print(f"    Line 01 OEE: {line_oee['oee']:.2%} - Grade: {line_oee['oee_grade_name']}")

    by_dim = get_oee_by_dimension('line')
    assert len(by_dim) > 0

    all_lines = get_all_lines_oee()
    assert len(all_lines) == 4
    print(f"    All lines OEE computed: {len(all_lines)} lines")


test("OEE module works", test_oee_module)

print("\n5. Testing Loss Module (Six Big Losses)...")


def test_loss_module():
    from modules.loss import calculate_six_big_losses, get_loss_pareto, get_big_losses_detail

    six_losses = calculate_six_big_losses()
    assert 'losses' in six_losses
    assert len(six_losses['losses']) == 6
    print(f"    Six Big Losses total: {six_losses['total_loss_minutes']:.1f} min")
    for loss in six_losses['losses']:
        print(f"      - {loss['name']}: {loss['total_minutes']:.1f} min ({loss['percentage']*100:.1f}%)")

    pareto = get_loss_pareto()
    assert 'pareto_items' in pareto
    assert len(pareto['pareto_items']) == 6
    print(f"    Pareto analysis generated")

    big_losses = get_big_losses_detail()
    assert isinstance(big_losses, list)
    print(f"    Big loss categories: {len(big_losses)}")


test("Loss module works", test_loss_module)

print("\n6. Testing Trend Module...")


def test_trend_module():
    from modules.trend import get_daily_trend, get_weekly_comparison, get_monthly_comparison

    daily = get_daily_trend(line_id='line_01', start_date='2026-06-01', end_date='2026-06-10')
    assert len(daily) == 10
    print(f"    Daily trend points: {len(daily)}")

    weekly_comp = get_weekly_comparison(line_id='line_01')
    assert 'reference_week' in weekly_comp
    assert 'compare_week' in weekly_comp
    assert 'comparison' in weekly_comp
    print(f"    Weekly comparison computed")

    monthly_comp = get_monthly_comparison(line_id='line_01')
    assert 'reference_month' in monthly_comp
    print(f"    Monthly comparison computed")


test("Trend module works", test_trend_module)

print("\n7. Testing Alert Module...")


def test_alert_module():
    from modules.alert import check_continuous_low_oee, generate_alerts, get_alert_summary, list_alerts

    alerts = check_continuous_low_oee(end_date='2026-06-10')
    assert isinstance(alerts, list)
    print(f"    Alerts found: {len(alerts)}")
    for alert in alerts:
        print(f"      - {alert['message']}")

    new_alerts = generate_alerts(end_date='2026-06-10')
    assert isinstance(new_alerts, list)

    summary = get_alert_summary()
    assert 'total' in summary
    assert 'pending' in summary
    print(f"    Alert summary: {summary['pending']} pending")

    all_alerts = list_alerts()
    assert isinstance(all_alerts, list)


test("Alert module works", test_alert_module)

print("\n8. Testing Report Module...")


def test_report_module():
    from modules.report import generate_shift_daily_report, generate_workshop_weekly_report, generate_factory_monthly_report, list_available_reports

    types = list_available_reports()
    assert len(types) == 3
    print(f"    Report types: {len(types)}")
    for t in types:
        print(f"      - {t['name']} ({t['audience']})")

    shift_report = generate_shift_daily_report('line_01', 'morning', '2026-06-01')
    assert shift_report['report_type'] == 'shift_daily'
    assert 'oee_summary' in shift_report
    assert 'production' in shift_report
    assert 'downtime' in shift_report
    assert 'loss_pareto' in shift_report
    print(f"    Shift daily report generated: OEE = {shift_report['oee_summary']['oee']:.2%}")

    weekly_report = generate_workshop_weekly_report('车间A', '2026-06-01', '2026-06-07')
    assert weekly_report['report_type'] == 'workshop_weekly'
    assert 'lines' in weekly_report
    assert len(weekly_report['lines']) == 2
    print(f"    Workshop weekly report generated: avg OEE = {weekly_report['summary']['avg_oee']:.2%}")

    monthly_report = generate_factory_monthly_report('2026-06-01')
    assert monthly_report['report_type'] == 'factory_monthly'
    assert 'workshops' in monthly_report
    assert 'lines_ranking' in monthly_report
    print(f"    Factory monthly report generated: avg OEE = {monthly_report['summary']['factory_avg_oee']:.2%}")


test("Report module works", test_report_module)

print("\n9. Testing Boundary Conditions...")


def test_boundary_conditions():
    from modules.oee import validate_planned_time_boundary
    from modules.production import validate_routing_consistency
    from data.mock_data import is_holiday

    boundary_check = validate_planned_time_boundary('line_01', 'morning', '2026-06-01')
    assert 'valid' in boundary_check
    print(f"    Planned time boundary check: {'valid' if boundary_check['valid'] else 'invalid'}")

    routing_ok = validate_routing_consistency('prod_a', 'line_01')
    assert routing_ok['valid'] == True
    print(f"    Routing check (prod_a + line_01): valid, cycle = {routing_ok['cycle_time']} min")

    routing_bad = validate_routing_consistency('prod_x', 'line_99')
    assert routing_bad['valid'] == False
    print(f"    Routing check (invalid): correctly flagged as invalid")

    holiday_check = is_holiday('2026-06-01')
    print(f"    2026-06-01 is holiday: {holiday_check}")


test("Boundary conditions handled", test_boundary_conditions)

print("\n10. Testing Flask App Creation...")


def test_flask_app():
    from app import create_app
    app = create_app()
    assert app is not None
    assert app.config['PORT'] == 5000

    with app.test_client() as client:
        resp = client.get('/api/health')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'ok'
        print(f"    Health check: {data['message']}")

        resp = client.get('/api/oee/all-lines')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) == 4
        print(f"    OEE all-lines endpoint: {len(data)} lines returned")

        resp = client.get('/api/loss/pareto')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'pareto_items' in data
        print(f"    Loss pareto endpoint: works")

        resp = client.get('/api/report/shift-daily?line_id=line_01&shift=morning&date=2026-06-01')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['report_type'] == 'shift_daily'
        print(f"    Shift daily report endpoint: works")

        resp = client.get('/api/alert/check-continuous-low-oee?end_date=2026-06-10')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        print(f"    Alert check endpoint: works")


test("Flask app and endpoints work", test_flask_app)

print("\n" + "=" * 60)
print(f"Test Results: {tests_passed} passed, {tests_failed} failed")
print("=" * 60)

if tests_failed > 0:
    sys.exit(1)
else:
    print("\nAll tests passed! OEE System is ready.")
    sys.exit(0)
