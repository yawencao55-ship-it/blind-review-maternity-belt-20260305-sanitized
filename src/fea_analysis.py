"""
有限元分析模块 - 孕妇托腹带皮肤应力分析
Python-based Finite Element Analysis for Maternity Belt Skin Stress Analysis

本模块使用简化的有限元方法模拟:
1. 孕期腹部皮肤应力分布
2. 托腹带支撑效果
3. 妊娠纹风险区域识别
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Tuple, Dict, List, Optional
import json
from pathlib import Path


@dataclass
class MaterialProperties:
    """材料力学特性"""
    youngs_modulus: float  # 杨氏模量 (kPa)
    poissons_ratio: float  # 泊松比
    thickness: float       # 厚度 (mm)
    name: str = "Unknown"


@dataclass
class SkinLayerModel:
    """皮肤分层模型"""
    epidermis: MaterialProperties
    dermis: MaterialProperties
    hypodermis: MaterialProperties
    
    @classmethod
    def from_literature_data(cls, age: int = 30, pregnancy_week: int = 30):
        """
        基于文献数据创建皮肤模型
        考虑年龄和孕周对皮肤特性的影响
        """
        # 基础值来自文献数据
        # 年龄因素: 年龄增加导致刚度增加 (约每10年增加10%)
        age_factor = 1.0 + (age - 30) * 0.01
        
        # 孕周因素: 孕期皮肤弹性下降 (最多下降30%)
        pregnancy_factor = 1.0 - (pregnancy_week - 12) / 28 * 0.3
        
        epidermis = MaterialProperties(
            youngs_modulus=1100 * age_factor * pregnancy_factor,  # kPa
            poissons_ratio=0.48,
            thickness=0.1,  # mm
            name="Epidermis"
        )
        
        dermis = MaterialProperties(
            youngs_modulus=150 * age_factor * pregnancy_factor,  # kPa
            poissons_ratio=0.48,
            thickness=2.0,  # mm
            name="Dermis"
        )
        
        hypodermis = MaterialProperties(
            youngs_modulus=2.0 * age_factor,  # kPa
            poissons_ratio=0.49,
            thickness=10.0,  # mm
            name="Hypodermis"
        )
        
        return cls(epidermis=epidermis, dermis=dermis, hypodermis=hypodermis)
    
    def get_effective_modulus(self) -> float:
        """计算皮肤的有效杨氏模量（加权平均）"""
        total_thickness = (self.epidermis.thickness + 
                          self.dermis.thickness + 
                          self.hypodermis.thickness)
        
        weighted_modulus = (
            self.epidermis.youngs_modulus * self.epidermis.thickness +
            self.dermis.youngs_modulus * self.dermis.thickness +
            self.hypodermis.youngs_modulus * self.hypodermis.thickness
        ) / total_thickness
        
        return weighted_modulus


class AbdominalGeometry:
    """孕期腹部几何模型"""
    
    def __init__(self, circumference: float = 100, height: float = 30, 
                 gestational_week: int = 30):
        """
        参数:
            circumference: 腹围 (cm)
            height: 腹部高度 (cm)
            gestational_week: 孕周
        """
        self.circumference = circumference
        self.height = height
        self.gestational_week = gestational_week
        
        # 计算腹部半径（简化为椭球体）
        self.radius_x = circumference / (2 * np.pi)  # 横向半径
        self.radius_z = height / 2  # 纵向半径
        
        # 最大凸起半径（妊娠后期增大）
        week_factor = (gestational_week - 12) / 28
        self.radius_y = 10 + 20 * week_factor  # cm
    
    def generate_mesh(self, n_theta: int = 36, n_phi: int = 18) -> Tuple[np.ndarray, np.ndarray]:
        """
        生成腹部表面网格
        返回节点坐标数组和单元连接数组
        """
        theta = np.linspace(0, 2 * np.pi, n_theta)
        phi = np.linspace(0, np.pi, n_phi)
        
        nodes = []
        for p in phi:
            for t in theta:
                x = self.radius_x * np.sin(p) * np.cos(t)
                y = self.radius_y * np.sin(p) * np.sin(t)
                z = self.radius_z * np.cos(p)
                nodes.append([x, y, z])
        
        nodes = np.array(nodes)
        
        # 生成三角形单元
        elements = []
        for i in range(n_phi - 1):
            for j in range(n_theta - 1):
                n1 = i * n_theta + j
                n2 = n1 + 1
                n3 = n1 + n_theta
                n4 = n3 + 1
                
                elements.append([n1, n2, n3])
                elements.append([n2, n4, n3])
        
        elements = np.array(elements)
        
        return nodes, elements
    
    def calculate_surface_area(self) -> float:
        """计算腹部表面积 (cm²)"""
        # 使用近似椭球体表面积公式
        a, b, c = self.radius_x, self.radius_y, self.radius_z
        p = 1.6075
        
        area = 4 * np.pi * ((a**p * b**p + a**p * c**p + b**p * c**p) / 3) ** (1/p)
        
        return area


class SimpleFEASolver:
    """简化的有限元分析求解器"""
    
    def __init__(self, geometry: AbdominalGeometry, skin_model: SkinLayerModel):
        self.geometry = geometry
        self.skin_model = skin_model
        self.nodes = None
        self.elements = None
        self.stress_results = None
        self.strain_results = None
    
    def setup_mesh(self, n_theta: int = 36, n_phi: int = 18):
        """设置网格"""
        self.nodes, self.elements = self.geometry.generate_mesh(n_theta, n_phi)
        return len(self.nodes), len(self.elements)
    
    def calculate_stretch_ratio(self) -> np.ndarray:
        """
        计算每个节点的拉伸比
        基于从初始状态到当前孕周的变化
        """
        # 基线腹围（孕12周）
        baseline_circumference = 85  # cm
        current_circumference = self.geometry.circumference
        
        # 计算拉伸比
        stretch_ratio = current_circumference / baseline_circumference
        
        # 根据位置调整拉伸比（腹部正面和侧面拉伸更大）
        stretch_distribution = np.ones(len(self.nodes))
        
        for i, node in enumerate(self.nodes):
            x, y, z = node
            # 计算到腹部中心线的距离
            r = np.sqrt(x**2 + y**2)
            # 前腹部拉伸更大
            if y > 0:
                stretch_distribution[i] = stretch_ratio * (1 + 0.2 * y / self.geometry.radius_y)
            else:
                stretch_distribution[i] = stretch_ratio * 0.9
        
        return stretch_distribution
    
    def calculate_stress_distribution(self) -> Dict[str, np.ndarray]:
        """
        计算应力分布
        使用简化的膜理论
        """
        if self.nodes is None:
            self.setup_mesh()
        
        stretch_ratio = self.calculate_stretch_ratio()
        E = self.skin_model.get_effective_modulus()  # kPa
        nu = 0.48  # 泊松比
        
        # 计算应力 (简化的线弹性模型)
        # σ = E * (λ - 1) / (1 - ν²)
        stress = np.zeros((len(self.nodes), 3))  # σ_x, σ_y, σ_z
        
        for i, node in enumerate(self.nodes):
            x, y, z = node
            lam = stretch_ratio[i]
            
            # 周向应力（主要应力）
            sigma_theta = E * (lam - 1) / (1 - nu**2)
            
            # 纵向应力（次要应力）
            sigma_z = E * (lam - 1) / (1 - nu**2) * 0.6
            
            # 基于位置调整应力
            # 腹部正前方和下腹部应力最高
            position_factor = 1.0
            if y > 0:  # 前腹部
                position_factor = 1.2
            if z < 0:  # 下腹部
                position_factor *= 1.3
            
            stress[i, 0] = sigma_theta * position_factor  # 周向
            stress[i, 1] = sigma_z * position_factor      # 纵向
            stress[i, 2] = 0  # 径向（假设为0）
        
        # 计算von Mises应力
        von_mises = np.sqrt(
            stress[:, 0]**2 + stress[:, 1]**2 + stress[:, 2]**2 -
            stress[:, 0]*stress[:, 1] - stress[:, 1]*stress[:, 2] - 
            stress[:, 2]*stress[:, 0]
        )
        
        self.stress_results = {
            'circumferential': stress[:, 0],
            'longitudinal': stress[:, 1],
            'radial': stress[:, 2],
            'von_mises': von_mises,
            'stretch_ratio': stretch_ratio
        }
        
        return self.stress_results
    
    def identify_high_risk_regions(self, threshold_percentile: float = 75) -> np.ndarray:
        """
        识别高风险区域（妊娠纹易发区）
        """
        if self.stress_results is None:
            self.calculate_stress_distribution()
        
        von_mises = self.stress_results['von_mises']
        threshold = np.percentile(von_mises, threshold_percentile)
        
        high_risk = von_mises > threshold
        
        return high_risk
    
    def get_statistics(self) -> Dict:
        """获取分析统计数据"""
        if self.stress_results is None:
            self.calculate_stress_distribution()
        
        vm = self.stress_results['von_mises']
        
        return {
            'max_von_mises_stress_kPa': float(np.max(vm)),
            'mean_von_mises_stress_kPa': float(np.mean(vm)),
            'min_von_mises_stress_kPa': float(np.min(vm)),
            'std_von_mises_stress_kPa': float(np.std(vm)),
            'max_stretch_ratio': float(np.max(self.stress_results['stretch_ratio'])),
            'mean_stretch_ratio': float(np.mean(self.stress_results['stretch_ratio'])),
            'high_risk_node_count': int(np.sum(self.identify_high_risk_regions())),
            'total_node_count': len(self.nodes),
            'high_risk_percentage': float(np.mean(self.identify_high_risk_regions()) * 100)
        }


class MaternityBeltModel:
    """托腹带模型"""
    
    def __init__(self, width: float = 15, thickness: float = 3,
                 elastic_modulus: float = 0.5, support_modulus: float = 10):
        """
        参数:
            width: 带宽 (cm)
            thickness: 厚度 (mm)
            elastic_modulus: 弹性织物杨氏模量 (MPa)
            support_modulus: 支撑板杨氏模量 (MPa)
        """
        self.width = width
        self.thickness = thickness
        self.elastic_modulus = elastic_modulus * 1000  # 转换为kPa
        self.support_modulus = support_modulus * 1000  # 转换为kPa
    
    def calculate_support_effect(self, fea_solver: SimpleFEASolver,
                                  belt_position: float = 0.7) -> Dict:
        """
        计算托腹带的支撑效果
        
        参数:
            fea_solver: FEA求解器实例
            belt_position: 托腹带位置 (0=顶部, 1=底部)
        
        返回:
            包含支撑效果数据的字典
        """
        if fea_solver.stress_results is None:
            fea_solver.calculate_stress_distribution()
        
        original_stress = fea_solver.stress_results['von_mises'].copy()
        nodes = fea_solver.nodes
        
        # 确定托腹带覆盖区域
        z_min = fea_solver.geometry.radius_z * (1 - 2 * belt_position)
        z_max = z_min + self.width / fea_solver.geometry.radius_z * 5
        
        # 计算应力减少
        belt_covered = np.zeros(len(nodes), dtype=bool)
        reduced_stress = original_stress.copy()
        
        for i, node in enumerate(nodes):
            x, y, z = node
            
            # 检查是否在托腹带覆盖区域
            if z_min <= z <= z_max and y > -fea_solver.geometry.radius_y * 0.3:
                belt_covered[i] = True
                
                # 计算应力减少比例
                # 基于托腹带刚度和皮肤刚度的比值
                stiffness_ratio = self.elastic_modulus / fea_solver.skin_model.get_effective_modulus()
                
                # 应力减少比例 (最大可减少60%)
                reduction_factor = min(0.6, stiffness_ratio * 0.1)
                
                # 考虑位置因素（前腹部效果更好）
                if y > 0:
                    reduction_factor *= 1.2
                
                reduced_stress[i] = original_stress[i] * (1 - reduction_factor)
        
        # 计算效果指标
        original_mean = np.mean(original_stress[belt_covered])
        reduced_mean = np.mean(reduced_stress[belt_covered])
        stress_reduction_percent = (1 - reduced_mean / original_mean) * 100 if original_mean > 0 else 0
        
        # 计算接触压力 (简化模型)
        contact_pressure = self.elastic_modulus * self.thickness / 1000 * 0.05
        
        # 舒适度评分
        comfort_score = 100 - abs(contact_pressure - 2.5) * 20 - self.thickness * 2
        comfort_score = max(0, min(100, comfort_score))
        
        return {
            'original_mean_stress_kPa': float(original_mean),
            'reduced_mean_stress_kPa': float(reduced_mean),
            'stress_reduction_percent': float(stress_reduction_percent),
            'contact_pressure_kPa': float(contact_pressure),
            'comfort_score': float(comfort_score),
            'covered_node_count': int(np.sum(belt_covered)),
            'coverage_percentage': float(np.mean(belt_covered) * 100),
            'original_stress': original_stress,
            'reduced_stress': reduced_stress,
            'belt_covered_mask': belt_covered
        }


def run_parametric_study(n_subjects: int = 20, n_belt_designs: int = 10) -> pd.DataFrame:
    """
    运行参数化研究
    
    参数:
        n_subjects: 受试者数量
        n_belt_designs: 托腹带设计数量
    
    返回:
        包含所有分析结果的DataFrame
    """
    np.random.seed(42)
    
    results = []
    
    # 生成受试者参数
    ages = np.random.randint(20, 40, n_subjects)
    weeks = np.random.randint(24, 40, n_subjects)
    circumferences = 85 + (weeks - 12) / 28 * 30 + np.random.normal(0, 3, n_subjects)
    
    # 生成托腹带设计参数
    belt_widths = np.linspace(8, 25, n_belt_designs)
    
    for i in range(n_subjects):
        age = ages[i]
        week = weeks[i]
        circ = circumferences[i]
        
        # 创建皮肤模型和几何模型
        skin_model = SkinLayerModel.from_literature_data(age=age, pregnancy_week=week)
        geometry = AbdominalGeometry(circumference=circ, gestational_week=week)
        
        # 创建FEA求解器
        fea_solver = SimpleFEASolver(geometry, skin_model)
        fea_solver.setup_mesh(n_theta=24, n_phi=12)
        
        # 无托腹带的基线分析
        baseline_stats = fea_solver.get_statistics()
        
        for j, width in enumerate(belt_widths):
            # 创建托腹带模型
            belt = MaternityBeltModel(
                width=width,
                thickness=3,
                elastic_modulus=0.5,
                support_modulus=10
            )
            
            # 计算支撑效果
            support_effect = belt.calculate_support_effect(fea_solver)
            
            # 计算妊娠纹风险评分
            original_risk = baseline_stats['high_risk_percentage']
            reduced_risk = original_risk * (1 - support_effect['stress_reduction_percent'] / 100)
            
            results.append({
                'subject_id': f'S{i+1:03d}',
                'age': age,
                'gestational_week': week,
                'abdominal_circumference_cm': circ,
                'belt_design_id': f'D{j+1:03d}',
                'belt_width_cm': width,
                'original_max_stress_kPa': baseline_stats['max_von_mises_stress_kPa'],
                'original_mean_stress_kPa': baseline_stats['mean_von_mises_stress_kPa'],
                'reduced_mean_stress_kPa': support_effect['reduced_mean_stress_kPa'],
                'stress_reduction_percent': support_effect['stress_reduction_percent'],
                'contact_pressure_kPa': support_effect['contact_pressure_kPa'],
                'comfort_score': support_effect['comfort_score'],
                'original_striae_risk_percent': original_risk,
                'reduced_striae_risk_percent': reduced_risk,
                'risk_reduction_percent': original_risk - reduced_risk,
                'coverage_percentage': support_effect['coverage_percentage']
            })
    
    return pd.DataFrame(results)


def main():
    """主函数: 运行有限元分析示例"""
    print("=" * 70)
    print("孕妇托腹带有限元分析")
    print("Python-based FEA for Maternity Belt Optimization")
    print("=" * 70)
    
    # 1. 创建典型孕妇皮肤模型
    print("\n1. 创建皮肤力学模型...")
    skin_model = SkinLayerModel.from_literature_data(age=28, pregnancy_week=32)
    print(f"   表皮杨氏模量: {skin_model.epidermis.youngs_modulus:.1f} kPa")
    print(f"   真皮杨氏模量: {skin_model.dermis.youngs_modulus:.1f} kPa")
    print(f"   皮下组织杨氏模量: {skin_model.hypodermis.youngs_modulus:.1f} kPa")
    print(f"   有效杨氏模量: {skin_model.get_effective_modulus():.1f} kPa")
    
    # 2. 创建腹部几何模型
    print("\n2. 创建腹部几何模型...")
    geometry = AbdominalGeometry(circumference=105, height=30, gestational_week=32)
    print(f"   腹围: {geometry.circumference} cm")
    print(f"   表面积: {geometry.calculate_surface_area():.1f} cm²")
    
    # 3. 运行FEA
    print("\n3. 运行有限元分析...")
    fea_solver = SimpleFEASolver(geometry, skin_model)
    n_nodes, n_elements = fea_solver.setup_mesh(n_theta=36, n_phi=18)
    print(f"   网格节点数: {n_nodes}")
    print(f"   网格单元数: {n_elements}")
    
    stress_results = fea_solver.calculate_stress_distribution()
    stats = fea_solver.get_statistics()
    print(f"\n   无托腹带情况下:")
    print(f"   最大应力: {stats['max_von_mises_stress_kPa']:.2f} kPa")
    print(f"   平均应力: {stats['mean_von_mises_stress_kPa']:.2f} kPa")
    print(f"   高风险区域比例: {stats['high_risk_percentage']:.1f}%")
    
    # 4. 托腹带支撑分析
    print("\n4. 托腹带支撑效果分析...")
    belt = MaternityBeltModel(width=15, thickness=3, elastic_modulus=0.5, support_modulus=10)
    support_effect = belt.calculate_support_effect(fea_solver)
    print(f"   托腹带宽度: {belt.width} cm")
    print(f"   覆盖区域: {support_effect['coverage_percentage']:.1f}%")
    print(f"   应力减少: {support_effect['stress_reduction_percent']:.1f}%")
    print(f"   接触压力: {support_effect['contact_pressure_kPa']:.2f} kPa")
    print(f"   舒适度评分: {support_effect['comfort_score']:.1f}/100")
    
    # 5. 运行参数化研究
    print("\n5. 运行参数化研究...")
    results_df = run_parametric_study(n_subjects=20, n_belt_designs=10)
    
    # 保存结果
    output_path = Path(__file__).parent / "data" / "fea_parametric_results.csv"
    results_df.to_csv(output_path, index=False)
    print(f"   已保存 {len(results_df)} 条分析结果到: {output_path}")
    
    # 6. 分析最优设计
    print("\n6. 最优设计分析...")
    # 综合评分: 风险减少 * 0.5 + 舒适度 * 0.3 + 应力减少 * 0.2
    results_df['optimization_score'] = (
        results_df['risk_reduction_percent'] * 0.5 +
        results_df['comfort_score'] * 0.3 +
        results_df['stress_reduction_percent'] * 0.2
    )
    
    optimal_design = results_df.loc[results_df['optimization_score'].idxmax()]
    print(f"   最优托腹带宽度: {optimal_design['belt_width_cm']:.1f} cm")
    print(f"   应力减少: {optimal_design['stress_reduction_percent']:.1f}%")
    print(f"   风险减少: {optimal_design['risk_reduction_percent']:.1f}%")
    print(f"   舒适度评分: {optimal_design['comfort_score']:.1f}/100")
    print(f"   综合优化评分: {optimal_design['optimization_score']:.1f}")
    
    print("\n" + "=" * 70)
    print("分析完成!")
    print("=" * 70)
    
    return results_df


if __name__ == "__main__":
    main()
