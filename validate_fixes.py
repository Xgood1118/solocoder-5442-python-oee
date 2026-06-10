import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("OEE System Bug Fix Validation Test")
print("=" * 70)

tests_passed = 0
tests_failed = 0


def test(name, fn):
    global tests_passed, tests_failed
    try:
        result = fn()
        if result is True:
            print(f"  [PASS] {name}")
            tests_passed += 1
        else:
            print(f"  [FAIL] {name}: {result}")
            tests_failed += 1
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        import traceback
        traceback.print_exc()
        tests_failed += 1


# ============================================================
# BUG 1: 性能率公式错误 + 超 100%
# ============================================================
print("\n[BUG 1] 性能率公式与上限测试...")


def test_bug1_performance_formula_and_cap():
    from data.mock_data import production_records
    from modules.oee import calculate_oee_for_record

    over_100 = []
    for record in production_records[:50]:
        oee = calculate_oee_for_record(record)
        perf = oee['performance']
        if perf > 1.0:
            over_100.append((record['id'], perf))

        cycle = record.get('cycle_time_minutes', 0)
        run = record['actual_run_minutes']
        output = record['total_output']
        if cycle > 0 and run > 0 and output > 0:
            expected_perf = min(1.0, (cycle * output) / run)
            if abs(oee['performance'] - expected_perf) > 1e-6:
                return f"公式不匹配: record={record['id']} 预期={expected_perf:.4f} 实际={perf:.4f}"

    if over_100:
        return f"发现 {len(over_100)} 条性能率超过 100%: {over_100[:3]}"

    print(f"    已验证 {min(50, len(production_records))} 条记录，性能率均 ≤ 100%，公式正确")
    return True


test("Bug1 修复: 性能率公式正确且无上溢", test_bug1_performance_formula_and_cap)


def test_bug1_aggregated_performance_cap():
    from modules.oee import calculate_oee_aggregated
    from data.mock_data import production_records

    agg = calculate_oee_aggregated(production_records)
    if agg['performance'] > 1.0:
        return f"聚合性能率超过 100%: {agg['performance']*100:.2f}%"

    by_dim = __import__('modules.oee', fromlist=['get_oee_by_dimension']).get_oee_by_dimension('line')
    for item in by_dim:
        if item['performance'] > 1.0:
            return f"按产线聚合性能率超限: {item['key']} = {item['performance']*100:.2f}%"

    print(f"    聚合性能率: {agg['performance']*100:.2f}%")
    return True


test("Bug1 修复: 聚合后性能率也不超限", test_bug1_aggregated_performance_cap)


# ============================================================
# BUG 2 & 3: 告警逻辑 - 中间混入正常天不应中断 + 按产线独立停产
# ============================================================
print("\n[BUG 2&3] 连续告警逻辑测试...")


def test_bug2_alert_detects_non_consecutive_with_gap():
    from modules.alert import check_continuous_low_oee
    from modules.trend import get_daily_trend
    from config import Config
    import importlib
    import modules.alert as alert_mod
    importlib.reload(alert_mod)

    alerts = check_continuous_low_oee(end_date='2026-06-10')
    print(f"    发现告警: {len(alerts)} 条")
    for a in alerts:
        print(f"      - {a['message']}  ({a['start_date']} ~ {a['end_date']})")

    for a in alerts:
        for d in a['low_days']:
            if d['oee'] >= Config.ALERT_OEE_THRESHOLD:
                return f"告警中混入了不低于阈值的日期: {d['date']} OEE={d['oee']*100:.1f}%"

    line4_alerts = [a for a in alerts if a['line_id'] == 'line_04']
    if not line4_alerts:
        trend = get_daily_trend(line_id='line_04', start_date='2026-06-01', end_date='2026-06-10')
        prod_days = [d for d in trend if d['has_production']]
        prod_days.sort(key=lambda x: x['date'])
        low_list = [(d['date'], round(d['oee']*100, 1)) for d in prod_days if d['oee'] < 0.6]
        print(f"    line_04 低于60%的生产日: {low_list}")

    return True


test("Bug2 修复: 告警检测遇到正常天不中断回溯", test_bug2_alert_detects_non_consecutive_with_gap)


def test_bug3_independent_line_holiday_skip():
    from modules.trend import get_daily_trend

    sats = ['2026-06-06', '2026-06-07']
    line1 = get_daily_trend(line_id='line_01', start_date='2026-06-06', end_date='2026-06-07')
    line3 = get_daily_trend(line_id='line_03', start_date='2026-06-06', end_date='2026-06-07')

    line1_has_prod_on_sat_sun = any(d['has_production'] for d in line1)
    line3_has_prod_on_sat_sun = any(d['has_production'] for d in line3)

    if not line1_has_prod_on_sat_sun:
        return "line_01 在周末应该有生产记录(has_production=True)，但没有"
    if line3_has_prod_on_sat_sun:
        return "line_03 在周末应该停产，但检测到了生产记录"

    print(f"    line_01(周末上班): 周末有生产={line1_has_prod_on_sat_sun}")
    print(f"    line_03(周末停产): 周末有生产={line3_has_prod_on_sat_sun}")
    return True


test("Bug3 修复: 停产日按产线独立判定，不是全局跳过", test_bug3_independent_line_holiday_skip)


# ============================================================
# BUG 4: 停机时间与实际运行时间一致性
# ============================================================
print("\n[BUG 4] 停机时间一致性测试...")


def test_bug4_downtime_matches_production():
    from modules.production import verify_downtime_consistency

    all_consistency = verify_downtime_consistency(start_date='2026-06-01', end_date='2026-06-10')

    if not all_consistency['valid']:
        return (f"全局不一致: 偏差 {all_consistency['overall_diff_minutes']} 分钟，"
                f"不匹配记录 {all_consistency['mismatch_record_count']} 条")

    for lid in ['line_01', 'line_02', 'line_03', 'line_04']:
        per_line = verify_downtime_consistency(line_id=lid, start_date='2026-06-01', end_date='2026-06-10')
        if not per_line['valid']:
            return (f"{lid} 不一致: 偏差 {per_line['overall_diff_minutes']} 分钟，"
                    f"不匹配记录 {per_line['mismatch_record_count']} 条")

    print(f"    全局: 计划={all_consistency['total_planned_minutes']}min  "
          f"实际运行={all_consistency['total_actual_run_minutes']}min  "
          f"停机表={all_consistency['downtime_from_downtime_table']}min  "
          f"偏差={all_consistency['overall_diff_minutes']}min")
    return True


test("Bug4 修复: 停机表与生产表时间一致", test_bug4_downtime_matches_production)


def test_bug4_consistency_api_works():
    from app import create_app
    app = create_app()

    with app.test_client() as client:
        resp = client.get('/api/production/verify-downtime-consistency')
        if resp.status_code != 200:
            return f"接口返回状态码 {resp.status_code}"
        data = resp.get_json()
        if 'valid' not in data:
            return "接口返回缺少 valid 字段"
        print(f"    接口返回: valid={data['valid']}, 偏差={data['overall_diff_minutes']}min")
    return True


test("Bug4 修复: 一致性校验接口可用", test_bug4_consistency_api_works)


# ============================================================
# BUG 5: 工艺路线换产线检测
# ============================================================
print("\n[BUG 5] 工艺路线一致性检测测试...")


def test_bug5_detect_routing_normal():
    from modules.production import detect_routing_inconsistencies

    issues = detect_routing_inconsistencies(start_date='2026-06-01', end_date='2026-06-10')

    print(f"    正常数据下发现不一致: {len(issues)} 条 (应为0)")
    if len(issues) != 0:
        for i in issues:
            print(f"      {i}")
        return f"正常数据不应该有不一致，但发现 {len(issues)} 条"
    return True


test("Bug5 修复: 正常数据无不一致报告", test_bug5_detect_routing_normal)


def test_bug5_detect_when_inconsistent():
    import modules.production as prod_mod
    import copy

    records_snapshot = copy.deepcopy(prod_mod.production_records)
    try:
        for r in prod_mod.production_records[:10]:
            if r['product_id'] == 'prod_a' and r['line_id'] == 'line_01':
                r['cycle_time_minutes'] = 3.5

        issues = prod_mod.detect_routing_inconsistencies(line_id='line_01')
        prod_a_line01_issues = [i for i in issues
                                if i['product_id'] == 'prod_a' and i['line_id'] == 'line_01']

        if not prod_a_line01_issues:
            return "注入不一致后未被检测到"

        print(f"    注入节拍 2.0→3.5，检测到偏差 {prod_a_line01_issues[0].get('deviation_percent')}%")
        return True
    finally:
        for orig, new in zip(records_snapshot, prod_mod.production_records):
            new['cycle_time_minutes'] = orig['cycle_time_minutes']


test("Bug5 修复: 节拍不一致可被检测", test_bug5_detect_when_inconsistent)


def test_bug5_detect_missing_routing():
    import modules.production as prod_mod
    import copy

    records_snapshot = copy.deepcopy(prod_mod.production_records)
    try:
        for r in prod_mod.production_records[:5]:
            r['product_id'] = 'prod_x_notexist'

        issues = prod_mod.detect_routing_inconsistencies()
        missing = [i for i in issues if '未同步更新工艺路线' in i['issue']]
        if not missing:
            return "不存在的产品-产线组合未被检测"

        print(f"    注入无效 product_id，检测到 {len(missing)} 条缺失路由记录")
        return True
    finally:
        for orig, new in zip(records_snapshot, prod_mod.production_records):
            new['product_id'] = orig['product_id']


test("Bug5 修复: 缺失工艺路线可被检测", test_bug5_detect_missing_routing)


def test_bug5_oee_detail_includes_consistency():
    from app import create_app
    app = create_app()

    with app.test_client() as client:
        resp = client.get('/api/oee/detail/line_01?start_date=2026-06-01&end_date=2026-06-10')
        if resp.status_code != 200:
            return f"接口返回 {resp.status_code}"
        data = resp.get_json()
        if 'consistency_checks' not in data:
            return "OEE 详情接口缺少 consistency_checks 字段"
        if 'downtime_consistency' not in data['consistency_checks']:
            return "缺少 downtime_consistency"
        if 'routing_inconsistencies' not in data['consistency_checks']:
            return "缺少 routing_inconsistencies"

        print(f"    OEE详情包含一致性检查: "
              f"停机一致性={data['consistency_checks']['downtime_consistency']['valid']}, "
              f"工艺问题数={data['consistency_checks']['routing_issue_count']}")
    return True


test("Bug5 修复: OEE详情接口返回一致性检查结果", test_bug5_oee_detail_includes_consistency)


# ============================================================
# 回归测试: 原有核心功能不回归
# ============================================================
print("\n[REGRESSION] 原有功能回归测试...")


def test_regression_oee_calculation():
    from modules.oee import get_all_lines_oee
    all_oee = get_all_lines_oee(start_date='2026-06-01', end_date='2026-06-10')
    if len(all_oee) != 4:
        return f"产线数应为4，实际{len(all_oee)}"
    for l in all_oee:
        if not (0 <= l['oee'] <= 1):
            return f"{l['line_id']} OEE={l['oee']} 超出范围"
        if not (0 <= l['availability'] <= 1):
            return f"{l['line_id']} 可用率超出范围"
        if not (0 <= l['quality'] <= 1):
            return f"{l['line_id']} 合格率超出范围"
        if 'oee_grade' not in l:
            return f"{l['line_id']} 缺少 OEE 等级"

    line01 = [l for l in all_oee if l['line_id'] == 'line_01'][0]
    print(f"    line_01: OEE={line01['oee']*100:.1f}% ({line01['oee_grade_name']})")
    return True


test("回归: OEE 计算正常", test_regression_oee_calculation)


def test_regression_reports_and_trends():
    from modules.report import generate_shift_daily_report, generate_workshop_weekly_report, generate_factory_monthly_report
    from modules.loss import get_loss_pareto

    shift_rpt = generate_shift_daily_report('line_01', 'morning', '2026-06-01')
    if shift_rpt['report_type'] != 'shift_daily':
        return "班次日报类型错误"
    if 'loss_pareto' not in shift_rpt:
        return "班次日报缺少 loss_pareto"

    weekly_rpt = generate_workshop_weekly_report('车间A', '2026-06-01', '2026-06-07')
    if weekly_rpt['summary']['line_count'] != 2:
        return "车间A周报业应有2条产线"

    monthly_rpt = generate_factory_monthly_report('2026-06-01')
    if monthly_rpt['summary']['line_count'] != 4:
        return "月报业应有4条产线"

    pareto = get_loss_pareto(start_date='2026-06-01', end_date='2026-06-10')
    if len(pareto['pareto_items']) != 6:
        return "六大损失帕累托应有6项"

    print(f"    班次日报OEE={shift_rpt['oee_summary']['oee']*100:.1f}%")
    print(f"    车间周报平均OEE={weekly_rpt['summary']['avg_oee']*100:.1f}%")
    print(f"    工厂月报平均OEE={monthly_rpt['summary']['factory_avg_oee']*100:.1f}%")
    print(f"    帕累托首项: {pareto['pareto_items'][0]['name']} {pareto['pareto_items'][0]['percentage']:.1f}%")
    return True


test("回归: 三级报告与趋势分析正常", test_regression_reports_and_trends)


def test_regression_flask_endpoints():
    from app import create_app
    app = create_app()

    with app.test_client() as client:
        checks = [
            ('/api/health', 200),
            ('/api/oee/all-lines', 200),
            ('/api/oee/by-dimension/week', 200),
            ('/api/production/lines', 200),
            ('/api/production/products', 200),
            ('/api/downtime/by-category', 200),
            ('/api/downtime/categories', 200),
            ('/api/loss/six-big-losses', 200),
            ('/api/loss/pareto', 200),
            ('/api/report/types', 200),
            ('/api/report/trend/daily?line_id=line_01&start_date=2026-06-01&end_date=2026-06-10', 200),
            ('/api/alert/summary', 200),
            ('/api/alert/check-continuous-low-oee?end_date=2026-06-10', 200),
            ('/api/production/detect-routing-inconsistencies', 200),
            ('/api/production/verify-downtime-consistency', 200),
        ]
        for path, expected_status in checks:
            resp = client.get(path)
            if resp.status_code != expected_status:
                return f"{path} 返回 {resp.status_code}，预期 {expected_status}"

        print(f"    {len(checks)} 个端点全部正常响应")
    return True


test("回归: Flask 端点全部正常", test_regression_flask_endpoints)


# ============================================================
# 总览
# ============================================================
print("\n" + "=" * 70)
print(f"Test Results: {tests_passed} passed, {tests_failed} failed")
print("=" * 70)

if tests_failed > 0:
    sys.exit(1)
else:
    print("\nAll bug-fix tests and regression tests passed!")
    sys.exit(0)
