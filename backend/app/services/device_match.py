"""按需求气量与压力自动匹配供应商设备（见 backend/docs/设备匹配算法设计.md）

用户原有设备为多台时的推荐策略：

方案一：按额定流量匹配
  找与客户设备额定流量接近的供应商设备，满足总气量 ≥ 组合上限，越接近越好。

方案二：按单台目标流量
  单台目标流量 = 组合上限 / 原有设备数量，在供应商里找单台气量最接近的机型，用 n 台，计算总流量。

显示规则：若方案二总流量 > 方案一总流量则只显示方案一；若相等则都显示；否则都显示。
共同约束：供应商额定压力 >= 客户实际压力。
"""
from __future__ import annotations

import math

# 品牌默认加载率（变频时用），与 cal_func 一致
POR_DICT = {"阿特拉斯": 0.98, "凯撒": 0.98, "英格索兰": 0.98, "复盛": 0.9}
DEFAULT_POR = 0.98

MAX_RECOMMEND_UNITS = 6


def _por(brand: str) -> float:
    return POR_DICT.get(brand, DEFAULT_POR)


def demand_q(client_list: list[dict], use_caliber_a: bool = True) -> float:
    """
    需求气量 Q_demand (m³/min)。
    口径 A：按实际加载产气汇总（工频用 load_time/run_time，变频用品牌默认加载率）。
    口径 B：按额定气量汇总。
    """
    if not client_list:
        return 0.0
    total = 0.0
    for c in client_list:
        air = float(c.get("air") or 0)
        if use_caliber_a:
            is_fc = c.get("isFC") in (True, 1, "1")
            if is_fc:
                por = _por((c.get("brand") or "").strip() or "其他")
                total += air * por
            else:
                run = int(c.get("run_time") or 0)
                load = int(c.get("load_time") or 0)
                por = (load / run) if run else 0
                total += air * por
        else:
            total += air
    return round(total, 4)


def demand_p(client_list: list[dict]) -> float:
    """需求压力 P_demand (MPa)：取参与计算的客户机中实际运行压力的最大值。"""
    if not client_list:
        return 0.0
    vals = []
    for c in client_list:
        v = c.get("actual_pre") or c.get("actucal_pre") or c.get("origin_pre") or 0.8
        vals.append(float(v))
    return round(max(vals), 4)


def _supplier_to_dict(supplier) -> dict:
    """将 ORM MachineSupplier 转为 cal_func 所需的 new_eq 项格式。"""
    return {
        "brand": supplier.brand,
        "model": supplier.model,
        "ori_power": int(supplier.ori_power),
        "air": float(supplier.air),
        "isFC": bool(supplier.is_FC),
        "energy_con": float(supplier.energy_con),
        "energy_con_min": float(supplier.energy_con_min),
    }


def _scheme_signature(scheme_list: list[tuple[dict, int]]) -> tuple:
    """用于去重：同一组合（型号+台数）视为相同方案。"""
    return tuple((s.get("brand"), s.get("model"), cnt) for s, cnt in sorted(scheme_list, key=lambda x: (x[0].get("brand") or "", x[0].get("model") or "", -x[1])))


def _greedy_one_scheme(
    candidates: list[dict],
    q_target: float,
    max_units: int,
    sort_key,
) -> list[tuple[dict, int]]:
    """贪心生成一种组合：按 sort_key 排序后依次选机直到总气量 >= q_target。"""
    sorted_c = sorted(candidates, key=sort_key)
    selected: list[tuple[dict, int]] = []
    q_sum = 0.0
    for _ in range(max_units):
        if q_sum >= q_target:
            break
        best = sorted_c[0]
        unit = {k: v for k, v in best.items() if not k.startswith("_")}
        found = False
        for i, (u, cnt) in enumerate(selected):
            if u.get("model") == unit.get("model") and u.get("brand") == unit.get("brand"):
                selected[i] = (u, cnt + 1)
                found = True
                break
        if not found:
            selected.append((unit, 1))
        q_sum += best["_air"]
    return selected


def _greedy_match_flow(
    candidates: list[dict],
    q_target: float,
    max_units: int,
) -> list[tuple[dict, int]]:
    """
    能效优先：按 (能效, 单台气量) 升序，用同一机型多台凑到略高于上限，总气量尽量靠近 q_target。
    """
    def sort_key(x):
        return (x["energy_con"], x.get("_air") or 0)
    return _greedy_one_scheme(candidates, q_target, max_units, sort_key=sort_key)


def _scheme_flow_match(
    client_list: list[dict],
    candidates: list[dict],
    q_target: float,
    n: int,
) -> list[tuple[dict, int]] | None:
    """
    方案一：找与客户设备额定流量接近的供应商设备，总气量 ≥ 组合上限，越接近越好。
    对每个客户（按额定流量），选供应商里单台气量最接近的机型，凑满 n 台且总气量 >= q_target。
    """
    if n == 0 or not candidates:
        return None
    # 客户额定流量列表（用于“接近”匹配）
    client_airs = [float(c.get("air") or 0) for c in client_list]
    # 供应商按单台气量排序，便于找最接近
    sorted_c = sorted(candidates, key=lambda x: (x.get("_air") or 0, x.get("energy_con", 0)))
    def closest_supplier(to_air: float) -> dict:
        return min(sorted_c, key=lambda c: (abs((c.get("_air") or 0) - to_air), c.get("energy_con", 0)))

    # 为尽量总气量接近 q_target：前 n-1 个按客户流量选最接近的供应商，最后 1 个选使总气量 >= q_target 且尽量小的
    slot_order = sorted(range(n), key=lambda i: -(client_airs[i] if i < len(client_airs) else 0))
    chosen: list[dict] = [None] * n
    total = 0.0
    for idx in range(n):
        i = slot_order[idx]
        want_air = client_airs[i] if i < len(client_airs) else (q_target / n)
        if idx < n - 1:
            c = closest_supplier(want_air)
            chosen[i] = c
            total += c.get("_air") or 0
        else:
            need = max(0, q_target - total)
            # 选单台气量 >= need 且最接近 need 的（使总气量尽量接近 q_target）
            best = None
            best_diff = 1e9
            for c in sorted_c:
                air = c.get("_air") or 0
                if air >= need:
                    diff = (total + air) - q_target
                    if diff < best_diff:
                        best_diff = diff
                        best = c
            if best is None:
                best = max(sorted_c, key=lambda x: x.get("_air") or 0)
            chosen[i] = best
            total += best.get("_air") or 0
    if total < q_target:
        return None
    merged: list[tuple[dict, int]] = []
    for c in chosen:
        unit = {k: v for k, v in c.items() if not k.startswith("_")}
        found = False
        for i, (u, cnt) in enumerate(merged):
            if u.get("brand") == unit.get("brand") and u.get("model") == unit.get("model"):
                merged[i] = (u, cnt + 1)
                found = True
                break
        if not found:
            merged.append((unit, 1))
    return merged


def _scheme_by_avg_flow(
    candidates: list[dict],
    q_target: float,
    n: int,
) -> list[tuple[dict, int]] | None:
    """
    方案二：单台目标流量 = 组合上限 / 原有设备数量，在供应商里找单台气量最接近的机型，用 n 台，计算总流量。
    """
    if n == 0 or not candidates:
        return None
    flow_per_unit = q_target / n
    best = min(candidates, key=lambda c: (abs((c.get("_air") or 0) - flow_per_unit), c.get("energy_con", 0)))
    air = best.get("_air") or 0
    unit = {k: v for k, v in best.items() if not k.startswith("_")}
    return [(unit, n)]


def _scheme_two_same(
    candidates: list[dict],
    q_target: float,
    max_overage_ratio: float = 0.2,
) -> list[tuple[dict, int]] | None:
    """
    两台同型：仅 2 台同型号，满足 2*air >= q_target，选过盈最小且不超过上限过多的机型。
    """
    best_scheme = None
    best_overage = 1e9
    best_energy = 1e9
    n = 2
    for c in candidates:
        air = c.get("_air") or 0
        if air <= 0:
            continue
        total = n * air
        if total < q_target:
            continue
        overage = total - q_target
        if total > q_target * (1 + max_overage_ratio):
            continue
        unit = {k: v for k, v in c.items() if not k.startswith("_")}
        scheme = [(unit, n)]
        energy = c.get("energy_con") or 0
        if overage < best_overage or (overage == best_overage and energy < best_energy):
            best_overage = overage
            best_energy = energy
            best_scheme = scheme
    return best_scheme


def _scheme_same_model_multi(
    candidates: list[dict],
    q_target: float,
    max_units: int,
) -> list[tuple[dict, int]] | None:
    """
    同型多台：先满足数量 n <= 原数量（max_units），再满足总气量 n*air >= 组合上限，越接近组合上限越好（过盈最小）。
    """
    best_scheme = None
    best_overage = 1e9
    best_energy = 1e9
    for c in candidates:
        air = c.get("_air") or 0
        if air <= 0:
            continue
        n = min(max_units, max(1, math.ceil(q_target / air)))
        total = n * air
        overage = total - q_target
        if overage < 0:
            continue
        unit = {k: v for k, v in c.items() if not k.startswith("_")}
        scheme = [(unit, n)]
        energy = c.get("energy_con") or 0
        if overage < best_overage or (overage == best_overage and energy < best_energy):
            best_overage = overage
            best_energy = energy
            best_scheme = scheme
    return best_scheme


def _greedy_balanced(
    candidates: list[dict],
    q_target: float,
    max_units: int,
    client_powers: set[int] | None = None,
) -> list[tuple[dict, int]]:
    """
    一大一小：给出该策略下最优组合（可能两台同型也可能一大一小）。
    优先与原先客户机功率相同，再在该压力下使用气量之和 >= 原组合且过盈最小。
    """
    if not candidates:
        return []
    client_powers = client_powers or set()
    selected: list[tuple[dict, int]] = []
    q_sum = 0.0
    for _ in range(max_units):
        if q_sum >= q_target:
            break
        best = None
        best_key = (1, 1e9)  # (同功率优先 0=同, 过盈)
        for c in candidates:
            air = c.get("_air") or 0
            if air <= 0:
                continue
            new_sum = q_sum + air
            if new_sum >= q_target:
                overage = new_sum - q_target
                power_match = 0 if (c.get("ori_power") in client_powers) else 1
                key = (power_match, overage)
                if key < best_key:
                    best_key = key
                    best = c
        if best is None:
            best = min(
                candidates,
                key=lambda x: (
                    0 if (x.get("ori_power") in client_powers) else 1,
                    x.get("_air") or 1e9,
                    x.get("energy_con", 0),
                ),
            )
        unit = {k: v for k, v in best.items() if not k.startswith("_")}
        found = False
        for i, (u, cnt) in enumerate(selected):
            if u.get("model") == unit.get("model") and u.get("brand") == unit.get("brand"):
                selected[i] = (u, cnt + 1)
                found = True
                break
        if not found:
            selected.append((unit, 1))
        q_sum += best["_air"]
    return selected


def recommend_suppliers_multi(
    client_list: list[dict],
    supplier_objs: list,
    margin_ratio: float = 1.1,
    max_units: int = MAX_RECOMMEND_UNITS,
    use_caliber_a: bool = True,
) -> tuple[list[dict], list[tuple[dict, int]], list[dict], str]:
    """
    推荐逻辑：1) 压力 >= 客户实际压力；2) 用供应商设备气量匹配需求，给出多种组合。

    :param client_list: 客户机列表，仅用于汇总需求气量 q_demand、需求压力 p_demand
    :param supplier_objs: 供应商设备（MachineSupplier）列表，其 .air（气量）、.origin_pre（压力）等用于筛选与组合
    :param use_caliber_a: True=按实际用气量（口径 A）作为组合上限，False=按额定用气量（口径 B）作为组合上限
    :return: (new_eq_primary, scheme_primary, schemes_all, summary)
        - new_eq_primary: 主方案展开为与 client_list 等长的列表，供 Excel 使用
        - scheme_primary: 主方案 [(supplier_dict, count), ...]
        - schemes_all: [{"name": "能效优先", "scheme": [{"brand":..., "model":..., "count": n}, ...]}, ...]
        - summary: 文字摘要
    """
    n = len(client_list)
    if n == 0:
        return [], [], [], "无客户机参与计算"

    # 推荐台数不超过用户原有客户机数量
    max_units = min(max_units, n)

    # 需求侧：用户选择的实际/额定用气量即为组合上限，不再乘余量
    q_demand = demand_q(client_list, use_caliber_a=use_caliber_a)
    p_demand = demand_p(client_list)
    q_target = q_demand

    # 供应侧：候选机型的气量、压力等均来自供应商设备表（MachineSupplier）
    # 1) 首先过滤：供应商额定压力 >= 客户实际压力
    candidates = []
    for s in supplier_objs:
        origin_pre = float(s.origin_pre or 0)
        if origin_pre >= p_demand:
            d = _supplier_to_dict(s)
            d["_origin_pre"] = origin_pre
            d["_air"] = float(s.air or 0)  # 供应商设备气量 (m³/min)，用于匹配是否满足 q_target
            candidates.append(d)

    if not candidates:
        return [], [], [], f"无满足压力要求（>={p_demand} MPa）的供应商机型"

    # 2) 方案一：按额定流量匹配；方案二：按单台目标流量。显示规则：方案二总流量>方案一则只显示方案一，否则都显示。
    schemes_with_names: list[tuple[str, list[tuple[dict, int]]]] = []

    def _total_air(scheme):
        total = 0.0
        for u, cnt in scheme:
            for c in candidates:
                if c.get("brand") == u.get("brand") and c.get("model") == u.get("model"):
                    total += (c.get("_air") or 0) * cnt
                    break
        return total

    # 方案一：与客户额定流量接近的供应商组合，总气量 ≥ 组合上限，越接近越好
    scheme1 = _scheme_flow_match(client_list, candidates, q_target, n)
    total1 = _total_air(scheme1) if scheme1 else 1e9

    # 方案二：单台目标流量 = 组合上限/n，找最接近的机型 n 台
    scheme2 = _scheme_by_avg_flow(candidates, q_target, n)
    total2 = _total_air(scheme2) if scheme2 else 0.0

    if scheme1 and total1 >= q_target:
        schemes_with_names.append(("按额定流量匹配", scheme1))
    if scheme2 and total2 >= q_target:
        if total2 > total1:
            pass  # 只显示方案一，不加入方案二
        else:
            schemes_with_names.append(("按单台目标流量", scheme2))

    if not schemes_with_names:
        return [], [], [], "无法生成满足气量要求的组合"

    # 按方案总气量升序排列，最靠近组合上限的排前面，方便用户自选
    schemes_with_names.sort(key=lambda x: _total_air(x[1]))
    scheme_primary = schemes_with_names[0][1]
    flat = []
    for u, cnt in scheme_primary:
        for _ in range(cnt):
            flat.append(u.copy())
    while len(flat) < n and flat:
        flat.append(flat[-1].copy())
    flat = flat[:n]

    def _scheme_total_air(scheme):
        """从 candidates 按 brand+model 查单台气量，计算方案总气量。"""
        total = 0.0
        for u, cnt in scheme:
            for c in candidates:
                if c.get("brand") == u.get("brand") and c.get("model") == u.get("model"):
                    total += (c.get("_air") or 0) * cnt
                    break
        return total

    schemes_all = []
    for name, scheme in schemes_with_names:
        schemes_all.append({
            "name": name,
            "scheme": [{"brand": s.get("brand"), "model": s.get("model"), "count": cnt} for s, cnt in scheme],
            "total_air": round(_scheme_total_air(scheme), 2),
        })
    # 摘要中展示目标气量与各方案总气量，便于核对结论依据
    def _scheme_summary(scheme):
        parts = [f"{cnt}台 {s.get('brand', '')}-{s.get('model', '')}" for s, cnt in scheme]
        total = _scheme_total_air(scheme)
        return ", ".join(parts) + f"（方案总气量 {total:.1f} m³/min）"

    summary = f"需求气量（组合上限）{q_demand} m³/min，需求压力 {p_demand} MPa。推荐方案："
    summary += "；".join(f"{name}：{_scheme_summary(scheme)}" for name, scheme in schemes_with_names)
    return flat, scheme_primary, schemes_all, summary


def recommend_suppliers(
    client_list: list[dict],
    supplier_objs: list,
    margin_ratio: float = 1.1,
    max_units: int = MAX_RECOMMEND_UNITS,
    strategy: str = "efficiency",
) -> tuple[list[dict], list[tuple[dict, int]], str]:
    """
    根据客户机列表与供应商库，生成推荐方案（兼容旧接口，内部调用 recommend_suppliers_multi 取主方案）。
    """
    flat, scheme_primary, _schemes_all, summary = recommend_suppliers_multi(
        client_list, supplier_objs, margin_ratio=margin_ratio, max_units=max_units, use_caliber_a=True
    )
    return flat, scheme_primary, summary


def client_orm_to_dict(client) -> dict:
    """将 MachineClient ORM 转为 cal_func 所需的 machines 项格式。"""
    return {
        "no": client.no,
        "model": client.model,
        "run_time": client.run_time,
        "load_time": client.load_time,
        "ori_power": int(client.ori_power),
        "air": float(client.air),
        "brand": client.brand,
        "isFC": bool(client.is_FC),
        "origin_pre": float(client.origin_pre),
        "actucal_pre": float(client.actual_pre),
    }
