"""AirComp 能耗计算逻辑（从蓝本迁移，兼容更多品牌）"""
import pandas as pd
import os

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", 500)
pd.set_option("display.width", 1000)

# 品牌服务系数与加载比例，未列出的品牌使用默认值
service_para_dict = {"阿特拉斯": 1.15, "凯撒": 1.15, "英格索兰": 1.2, "复盛": 1.3}
por_dict = {"阿特拉斯": 0.98, "凯撒": 0.98, "英格索兰": 0.98, "复盛": 0.9}
DEFAULT_SER_P = 1.2
DEFAULT_POR = 0.98
YEAR_RUNNING_TIME = 8000


def _ser_p(brand):
    return service_para_dict.get(brand, DEFAULT_SER_P)


def _por(brand):
    return por_dict.get(brand, DEFAULT_POR)


def calculate_process(air_dict, calc_params: dict | None = None):
    if not air_dict["isFC"]:
        return calculate_it_noneFC(air_dict, calc_params)
    return calculate_it_FC(air_dict, calc_params)


def _get_ser_p(brand, calc_params: dict | None):
    if calc_params and "default_ser_p" in calc_params:
        return float(calc_params["default_ser_p"])
    return _ser_p(brand)


def _get_por(brand, calc_params: dict | None):
    if calc_params and "default_por" in calc_params:
        return float(calc_params["default_por"])
    return _por(brand)


def calculate_it_noneFC(air_dict, calc_params: dict | None = None):
    no, model = air_dict["no"], air_dict["model"]
    run_time, load_time = int(air_dict["run_time"]), int(air_dict["load_time"])
    ori_power, air = int(air_dict["ori_power"]), float(air_dict["air"])
    brand = air_dict["brand"]
    ori_pre, actual_pre = float(air_dict["origin_pre"]), float(air_dict["actucal_pre"])
    ser_p = _get_ser_p(brand, calc_params)
    empty_ratio = float(calc_params["empty_waste_ratio"]) if calc_params and "empty_waste_ratio" in calc_params else 0.4
    pressure_ratio = float(calc_params["pressure_drop_ratio"]) if calc_params and "pressure_drop_ratio" in calc_params else 0.07
    d_val = round(ori_pre - actual_pre, 3)
    empty_waste = round((run_time - load_time) / run_time * empty_ratio * ori_power, 4)
    str_empty_waste = f"({run_time}-{load_time})/{run_time}*{empty_ratio*100:.0f}%*{ori_power}={empty_waste}"
    d_val_waste = round(ori_power * d_val * pressure_ratio, 4)
    str_d_val_waste = f"{ori_power}*({d_val})*{pressure_ratio*100:.0f}%={round(ori_power * d_val * pressure_ratio, 3)}"
    total_waste = round(empty_waste + d_val_waste, 4)
    por = float(round(load_time / run_time, 4))
    actual_energyE = round(
        (float(ori_power) * float(ser_p) * por + empty_waste + d_val_waste) / (air * por), 2
    )
    str_actual_energyE = f"({ori_power}*{ser_p}*{por}+{total_waste})/({air}*{por})={actual_energyE}"
    isFccn = "变频 " if air_dict["isFC"] else "工频"
    return [
        [str(no), model, str(run_time), str(load_time), str(ori_power), str_empty_waste, str_d_val_waste, str(total_waste), str_actual_energyE, round(por * air, 4)],
        [str(ori_power), str(air), str(ori_pre), str(actual_pre), str(model), str(brand)],
        [brand, model, ori_power, isFccn, actual_energyE, round(actual_energyE / 60, 4)],
    ]


def calculate_it_FC(air_dict, calc_params: dict | None = None):
    no, model = air_dict["no"], air_dict["model"]
    run_time, load_time = int(air_dict["run_time"]), int(air_dict["load_time"])
    ori_power, air = int(air_dict["ori_power"]), float(air_dict["air"])
    brand = air_dict["brand"]
    ori_pre, actual_pre = float(air_dict["origin_pre"]), float(air_dict["actucal_pre"])
    ser_p = _get_ser_p(brand, calc_params)
    pressure_ratio = float(calc_params["pressure_drop_ratio"]) if calc_params and "pressure_drop_ratio" in calc_params else 0.07
    d_val = round(ori_pre - actual_pre, 3)
    empty_waste = 0
    str_empty_waste = "0"
    d_val_waste = round(ori_power * d_val * pressure_ratio, 4)
    d_cal_wast_por = 1 - round(d_val * pressure_ratio, 4)
    str_d_val_waste = f"{ori_power}*({d_val})*{pressure_ratio*100:.0f}%={round(ori_power * d_val * pressure_ratio, 3)}"
    total_waste = round(empty_waste + d_val_waste, 4)
    por = _get_por(brand, calc_params)
    actual_energyE = round((float(ori_power) * ser_p * d_cal_wast_por) / (air * por), 2)
    str_actual_energyE = f"({ori_power}*{ser_p}*{d_cal_wast_por})/({air}*{por})={actual_energyE}"
    isFccn = "变频" if air_dict["isFC"] else "工频"
    return [
        [str(no), model, str(run_time), str(load_time), str(ori_power), str_empty_waste, str_d_val_waste, str(total_waste), str_actual_energyE, round(por * air, 4)],
        [str(ori_power), str(air), str(ori_pre), str(actual_pre), str(model), str(brand)],
        [brand, model, ori_power, isFccn, actual_energyE, round(actual_energyE / 60, 4)],
    ]


def originEC_to_dataframe(
    machine1,
    new_machine,
    running_hours_per_year: int = None,
    calc_params: dict | None = None,
):
    if running_hours_per_year is None:
        running_hours_per_year = YEAR_RUNNING_TIME
    no_list, type_list, run_list, load_list, ori_list = [], [], [], [], []
    empty_list, d_list, total_list, actual_list, ori_kw_list = [], [], [], [], []
    ori_pre_list, ori_air_list, act_air_list, act_pre_list = [], [], [], []
    ee_lists = []
    all_year_savings = 0
    ee_dicts = []
    for one in machine1:
        data_list, eq_list, ee_list = calculate_process(one, calc_params)
        tmp_dict = {
            "brand": ee_list[0],
            "model": ee_list[1],
            "ori_power": ee_list[2],
            "air": eq_list[1],
            "isFC": 1 if one["isFC"] else 0,
            "energy_con": ee_list[4],
            "energy_con_min": round(ee_list[4] / 60, 4),
        }
        ee_lists.append(tmp_dict)
        act_air_list.append(data_list[9])
        no_list.append(data_list[0])
        type_list.append(data_list[1])
        run_list.append(data_list[2])
        load_list.append(data_list[3])
        ori_list.append(data_list[4])
        empty_list.append(data_list[5])
        d_list.append(data_list[6])
        total_list.append(data_list[7])
        actual_list.append(data_list[8])
        ori_kw_list.append(eq_list[0])
        ori_pre_list.append(eq_list[2])
        ori_air_list.append(eq_list[1])
        act_pre_list.append(eq_list[3])
    all_table = pd.DataFrame({
        "设备编号": no_list,
        "原设备型号": type_list,
        "运行时间": run_list,
        "加载时间": load_list,
        "额定功率": ori_list,
        "空载浪费": empty_list,
        "工频压降浪费": d_list,
        "总计浪费": total_list,
        "实际比功率": actual_list,
    })
    ori_eq_table = pd.DataFrame({
        "No": no_list,
        "额定功率": ori_kw_list,
        "额定排量": ori_air_list,
        "额定压力": ori_pre_list,
        "实际运行压力": act_pre_list,
        "型号": type_list,
    })

    for i in range(len(ee_lists)):
        saving = round(float(ee_lists[i]["energy_con"]) - float(new_machine[i]["energy_con"]), 4)
        saving_portion = round(saving / float(ee_lists[i]["energy_con"]) * 100, 2)
        saving_per_hour = round(saving * float(act_air_list[i]), 4)
        saving_per_year = round(saving_per_hour * running_hours_per_year)
        all_year_savings += saving_per_year
        ee_lists[i]["saving_portion"] = saving_portion
        ee_lists[i]["saving_per_hour"] = saving_per_hour
        ee_lists[i]["saving_per_year"] = saving_per_year
        new_machine[i]["saving_portion"] = saving_portion
        new_machine[i]["saving_per_hour"] = saving_per_hour
        new_machine[i]["saving_per_year"] = saving_per_year
    for i in range(len(ee_lists)):
        ee_lists[i]["all_year_savings"] = all_year_savings
        new_machine[i]["all_year_savings"] = all_year_savings
        ee_dicts.append(new_machine[i])
        ee_dicts.append(ee_lists[i])
    ee_dicts_output = {
        "品牌": [r["brand"] for r in ee_dicts],
        "型号": [r["model"] for r in ee_dicts],
        "功率": [r["ori_power"] for r in ee_dicts],
        "气量": [r["air"] for r in ee_dicts],
        "控制方式": ["变频" if (r.get("isFC") == 1 or r.get("isFC") is True) else "工频" for r in ee_dicts],
        "实际比功率": [r["energy_con"] for r in ee_dicts],
        "均每立方耗电": [r["energy_con_min"] for r in ee_dicts],
        "节电比例": [r["saving_portion"] for r in ee_dicts],
        "小时节电": [r["saving_per_hour"] for r in ee_dicts],
        "年节电": [r["saving_per_year"] for r in ee_dicts],
        "年总节电": [r["all_year_savings"] for r in ee_dicts],
    }
    ee_pd_da = pd.DataFrame.from_dict(ee_dicts_output, orient="index")
    return all_table, ori_eq_table, ee_pd_da, all_year_savings


def final_results_excel(
    company_name: str,
    machines: list,
    eqs: list,
    output_dir: str,
    running_hours_per_year: int = None,
    calc_params: dict | None = None,
) -> tuple[str, int]:
    """生成 Excel 并返回 (文件路径, 年总节电量 kWh)。"""
    if running_hours_per_year is None:
        running_hours_per_year = YEAR_RUNNING_TIME
    os.makedirs(output_dir, exist_ok=True)
    origin_final_table, origin_eq_table, energy_table, all_year_savings = originEC_to_dataframe(
        machines, eqs, running_hours_per_year=running_hours_per_year, calc_params=calc_params
    )
    safe_name = "".join(c for c in str(company_name) if c not in r'\/:*?"<>|').strip() or "未命名"
    filename = f"{safe_name}_能耗计算概况表.xlsx"
    filepath = os.path.join(output_dir, filename)
    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        origin_eq_table.to_excel(writer, sheet_name="原有设备一览", index=False)
        origin_final_table.to_excel(writer, sheet_name="原有设备能耗", index=False)
        energy_table.to_excel(writer, sheet_name="能效对比")
    return filepath, all_year_savings
