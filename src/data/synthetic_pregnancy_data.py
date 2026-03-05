"""
基于文献数据生成孕期皮肤力学特性模拟数据集
Generate Synthetic Pregnancy Skin Biomechanics Dataset

参考文献来源:
1. NIH - Skin Mechanical Properties Studies
2. Journal of Biomechanics - Pregnancy Skin Mechanics
3. Clinical measurements from maternity studies
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path
import os

def generate_pregnancy_skin_dataset(n_subjects: int = 100, random_seed: int = 42) -> pd.DataFrame:
    """
    生成孕期皮肤力学特性数据集
    
    参数:
        n_subjects: 模拟受试者数量
        random_seed: 随机种子确保可重复性
    
    返回:
        包含皮肤力学特性的DataFrame
    """
    np.random.seed(random_seed)
    
    # 基础受试者信息
    data = {
        'subject_id': [f'S{i:04d}' for i in range(1, n_subjects + 1)],
        'age': np.random.normal(28, 5, n_subjects).clip(18, 45).astype(int),
        'gestational_week': np.random.choice(range(12, 41), n_subjects),
        'pre_pregnancy_bmi': np.random.normal(23, 4, n_subjects).clip(16, 35),
        'weight_gain_kg': np.random.normal(12, 4, n_subjects).clip(5, 25),
    }
    
    # 孕期阶段分类
    data['trimester'] = np.where(data['gestational_week'] < 14, 1,
                         np.where(data['gestational_week'] < 28, 2, 3))
    
    # 腹部围度变化（cm）- 基于孕周
    baseline_circumference = np.random.normal(85, 8, n_subjects)
    week_factor = (data['gestational_week'] - 12) / 28
    data['abdominal_circumference_cm'] = baseline_circumference + week_factor * 30 + np.random.normal(0, 3, n_subjects)
    
    # 皮肤厚度（mm）- 分层
    data['epidermis_thickness_mm'] = np.random.normal(0.1, 0.02, n_subjects).clip(0.05, 0.15)
    data['dermis_thickness_mm'] = np.random.normal(2.0, 0.4, n_subjects).clip(1.5, 3.0)
    data['hypodermis_thickness_mm'] = np.random.normal(10, 3, n_subjects).clip(5, 20)
    
    # 皮肤弹性参数 - 杨氏模量（kPa）
    # 孕期皮肤弹性下降
    elasticity_reduction = 1 - 0.3 * week_factor  # 最多下降30%
    data['skin_youngs_modulus_kPa'] = (
        np.random.normal(150, 40, n_subjects) * elasticity_reduction
    ).clip(50, 300)
    
    # 泊松比
    data['skin_poissons_ratio'] = np.random.normal(0.48, 0.02, n_subjects).clip(0.45, 0.50)
    
    # 皮肤拉伸比
    data['skin_stretch_ratio'] = 1 + 0.4 * week_factor + np.random.normal(0, 0.05, n_subjects)
    
    # 妊娠纹风险评分（0-100）
    risk_factors = (
        0.3 * (data['age'] < 25).astype(float) +  # 年轻女性风险高
        0.2 * (data['pre_pregnancy_bmi'] > 25).astype(float) +  # BMI高风险高
        0.3 * week_factor +  # 孕周越大风险越高
        0.2 * (data['weight_gain_kg'] > 15).astype(float)  # 体重增加过多
    )
    data['striae_risk_score'] = (risk_factors * 100 + np.random.normal(0, 10, n_subjects)).clip(0, 100)
    
    # 是否已出现妊娠纹
    data['has_striae'] = (data['striae_risk_score'] > 50 + np.random.normal(0, 15, n_subjects)).astype(int)
    
    # 皮肤应力测量（kPa） - 腹部不同区域
    data['max_stress_upper_abdomen_kPa'] = np.random.normal(3.0, 1.0, n_subjects).clip(0.5, 8.0)
    data['max_stress_lower_abdomen_kPa'] = np.random.normal(4.5, 1.5, n_subjects).clip(1.0, 10.0)
    data['max_stress_lateral_kPa'] = np.random.normal(2.5, 0.8, n_subjects).clip(0.3, 6.0)
    
    return pd.DataFrame(data)


def generate_belt_design_parameters(n_designs: int = 50, random_seed: int = 42) -> pd.DataFrame:
    """
    生成托腹带设计参数数据集
    
    参数:
        n_designs: 设计方案数量
        random_seed: 随机种子
    
    返回:
        包含托腹带设计参数的DataFrame
    """
    np.random.seed(random_seed)
    
    data = {
        'design_id': [f'D{i:03d}' for i in range(1, n_designs + 1)],
        
        # 几何参数
        'belt_width_cm': np.random.uniform(8, 25, n_designs),
        'belt_thickness_mm': np.random.uniform(2, 6, n_designs),
        'support_panel_width_cm': np.random.uniform(10, 30, n_designs),
        'support_panel_height_cm': np.random.uniform(8, 20, n_designs),
        
        # 材料参数
        'elastic_fabric_modulus_MPa': np.random.uniform(0.1, 2.0, n_designs),
        'support_panel_modulus_MPa': np.random.uniform(5, 50, n_designs),
        
        # 结构参数
        'num_support_ribs': np.random.randint(0, 6, n_designs),
        'rib_spacing_cm': np.random.uniform(2, 8, n_designs),
        
        # 穿戴位置
        'position_below_belly_cm': np.random.uniform(0, 10, n_designs),
    }
    
    return pd.DataFrame(data)


def generate_fea_simulation_results(
    skin_data: pd.DataFrame, 
    belt_data: pd.DataFrame,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    生成有限元分析模拟结果
    
    参数:
        skin_data: 皮肤特性数据
        belt_data: 托腹带设计参数
        random_seed: 随机种子
    
    返回:
        包含FEA模拟结果的DataFrame
    """
    np.random.seed(random_seed)
    
    results = []
    
    for _, skin in skin_data.iterrows():
        for _, belt in belt_data.iterrows():
            # 简化的应力计算模型
            # 实际FEA会更复杂，这里提供合理的估计值
            
            # 托腹带的支撑效果取决于其刚度和宽度
            support_effectiveness = (
                belt['elastic_fabric_modulus_MPa'] * 0.3 +
                belt['support_panel_modulus_MPa'] * 0.05 +
                belt['belt_width_cm'] * 0.01
            )
            
            # 应力减少百分比
            stress_reduction_ratio = min(0.6, support_effectiveness * 0.1)
            
            # 压力分布计算
            contact_pressure = (
                belt['support_panel_modulus_MPa'] * 0.1 * 
                (1 - belt['belt_width_cm'] / 30)
            )
            
            # 舒适度评分（基于压力和分布均匀性）
            comfort_score = 100 - abs(contact_pressure - 2.5) * 20 - belt['belt_thickness_mm'] * 2
            comfort_score = max(0, min(100, comfort_score))
            
            # 最大应力计算（考虑托腹带支撑）
            reduced_stress_upper = skin['max_stress_upper_abdomen_kPa'] * (1 - stress_reduction_ratio * 0.7)
            reduced_stress_lower = skin['max_stress_lower_abdomen_kPa'] * (1 - stress_reduction_ratio)
            reduced_stress_lateral = skin['max_stress_lateral_kPa'] * (1 - stress_reduction_ratio * 0.5)
            
            # 预防妊娠纹效果评估
            prevention_score = (
                stress_reduction_ratio * 50 +
                (comfort_score / 100) * 30 +
                (contact_pressure < 4) * 20
            )
            
            results.append({
                'subject_id': skin['subject_id'],
                'design_id': belt['design_id'],
                'gestational_week': skin['gestational_week'],
                'original_stress_kPa': skin['max_stress_lower_abdomen_kPa'],
                'reduced_stress_kPa': reduced_stress_lower,
                'stress_reduction_percent': stress_reduction_ratio * 100,
                'contact_pressure_kPa': contact_pressure,
                'comfort_score': comfort_score,
                'prevention_effectiveness_score': prevention_score,
                'original_striae_risk': skin['striae_risk_score'],
                'reduced_striae_risk': max(0, skin['striae_risk_score'] - prevention_score * 0.5),
            })
    
    return pd.DataFrame(results)


def save_datasets(output_dir: str = 'data'):
    """
    生成并保存所有数据集
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("正在生成孕期皮肤力学数据集...")
    skin_data = generate_pregnancy_skin_dataset(n_subjects=100)
    skin_data.to_csv(output_path / 'pregnancy_skin_biomechanics.csv', index=False)
    print(f"  已保存: pregnancy_skin_biomechanics.csv ({len(skin_data)} 条记录)")
    
    print("正在生成托腹带设计参数数据集...")
    belt_data = generate_belt_design_parameters(n_designs=50)
    belt_data.to_csv(output_path / 'belt_design_parameters.csv', index=False)
    print(f"  已保存: belt_design_parameters.csv ({len(belt_data)} 条记录)")
    
    print("正在生成FEA模拟结果数据集...")
    # 为避免数据量过大，随机采样
    skin_sample = skin_data.sample(n=20, random_state=42)
    belt_sample = belt_data.sample(n=10, random_state=42)
    fea_results = generate_fea_simulation_results(skin_sample, belt_sample)
    fea_results.to_csv(output_path / 'fea_simulation_results.csv', index=False)
    print(f"  已保存: fea_simulation_results.csv ({len(fea_results)} 条记录)")
    
    print("\n数据集生成完成!")
    print(f"所有文件保存在: {output_path.absolute()}")
    
    return skin_data, belt_data, fea_results


if __name__ == '__main__':
    save_datasets()
