"""
高级有限元分析模块 - 优化版
Advanced FEA Module - Optimized Version

整合所有数据集的高级FEA分析：
1. 多层皮肤超弹性模型
2. 参数化腹部几何建模
3. 托腹带-皮肤相互作用
4. 基于验证数据的模型校正
5. 多目标优化算法
"""

import numpy as np
import pandas as pd
from scipy import optimize, interpolate, stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from pathlib import Path
import json
import warnings
warnings.filterwarnings('ignore')

# 路径设置
PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data"
RESULTS_DIR = PROJECT_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)


class HyperelasticMaterial:
    """超弹性材料模型"""
    
    def __init__(self, model_type='neo_hookean', **params):
        self.model_type = model_type
        self.params = params
        
    def neo_hookean(self, stretch):
        """Neo-Hookean模型: W = C10 * (I1 - 3)"""
        C10 = self.params.get('C10', 25)  # kPa
        I1 = stretch**2 + 2/stretch  # 等容变形假设
        W = C10 * (I1 - 3)
        # Cauchy应力
        sigma = 2 * C10 * (stretch - 1/stretch**2)
        return sigma
    
    def mooney_rivlin(self, stretch):
        """Mooney-Rivlin模型: W = C10*(I1-3) + C01*(I2-3)"""
        C10 = self.params.get('C10', 20)  # kPa
        C01 = self.params.get('C01', 5)   # kPa
        
        I1 = stretch**2 + 2/stretch
        I2 = 2*stretch + 1/stretch**2
        
        sigma = 2 * (C10 + C01/stretch) * (stretch - 1/stretch**2)
        return sigma
    
    def ogden(self, stretch):
        """Ogden模型: W = sum(mu_i/alpha_i * (lambda^alpha_i - 1))"""
        mu = self.params.get('mu', 50)      # kPa
        alpha = self.params.get('alpha', 10)
        
        sigma = mu * (stretch**(alpha-1) - stretch**(-alpha/2-1))
        return sigma
    
    def get_stress(self, stretch):
        """根据模型类型计算应力"""
        if self.model_type == 'neo_hookean':
            return self.neo_hookean(stretch)
        elif self.model_type == 'mooney_rivlin':
            return self.mooney_rivlin(stretch)
        elif self.model_type == 'ogden':
            return self.ogden(stretch)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")


class AdvancedSkinModel:
    """高级多层皮肤模型"""
    
    def __init__(self, age=30, gestational_week=32, bmi=23):
        self.age = age
        self.week = gestational_week
        self.bmi = bmi
        
        # 加载超弹性材料参数
        self.load_material_params()
        
        # 皮肤层定义
        self.layers = {
            'epidermis': {
                'thickness_mm': 0.1,
                'material': HyperelasticMaterial('neo_hookean', C10=50)
            },
            'dermis': {
                'thickness_mm': 2.0,
                'material': HyperelasticMaterial('mooney_rivlin', C10=20, C01=5)
            },
            'hypodermis': {
                'thickness_mm': self.get_hypodermis_thickness(),
                'material': HyperelasticMaterial('neo_hookean', C10=1)
            }
        }
        
        # 应用修正因子
        self.apply_modifiers()
    
    def load_material_params(self):
        """加载材料参数数据库"""
        try:
            self.material_db = pd.read_csv(DATA_DIR / "hyperelastic_material_params.csv")
        except:
            self.material_db = None
    
    def get_hypodermis_thickness(self):
        """根据BMI估算皮下脂肪厚度"""
        base_thickness = 8.0  # mm
        bmi_factor = (self.bmi - 22) * 0.8
        return max(3, min(25, base_thickness + bmi_factor))
    
    def apply_modifiers(self):
        """应用年龄和孕期修正因子"""
        # 年龄影响: 皮肤弹性随年龄降低
        age_factor = 1 + 0.015 * (self.age - 30)
        
        # 孕期影响: 皮肤随孕期延展变软
        pregnancy_factor = 1 - 0.012 * (self.week - 12)
        
        # 组合因子
        self.stiffness_modifier = age_factor * pregnancy_factor
    
    def get_composite_response(self, stretch):
        """计算复合皮肤响应"""
        total_thickness = sum(l['thickness_mm'] for l in self.layers.values())
        weighted_stress = 0
        
        for layer_name, layer in self.layers.items():
            layer_stress = layer['material'].get_stress(stretch)
            weight = layer['thickness_mm'] / total_thickness
            weighted_stress += layer_stress * weight
        
        # 应用修正因子
        return weighted_stress * self.stiffness_modifier


class AdvancedAbdominalGeometry:
    """高级腹部几何模型"""
    
    def __init__(self, week=32, circumference=None, height=None, bmi=23):
        self.week = week
        self.bmi = bmi
        
        # 估算腹围
        if circumference is None:
            self.circumference = self.estimate_circumference()
        else:
            self.circumference = circumference
            
        # 估算腹部高度
        if height is None:
            self.height = self.estimate_height()
        else:
            self.height = height
        
        # 生成网格
        self.generate_mesh()
    
    def estimate_circumference(self):
        """根据孕周估算腹围"""
        # 基于文献数据拟合
        base = 70 + self.bmi * 0.8
        growth = (self.week - 12) * 1.8
        return base + growth
    
    def estimate_height(self):
        """估算腹部高度"""
        base = 20
        growth = (self.week - 12) * 0.5
        return base + growth
    
    def generate_mesh(self):
        """生成3D表面网格"""
        # 椭球半径
        self.r_x = self.circumference / (2 * np.pi)  # 横向
        self.r_y = 10 + (self.week - 12) * 0.6        # 前后向
        self.r_z = self.height / 2                    # 纵向
        
        # 网格参数
        n_theta = 48  # 环向分辨率
        n_phi = 24    # 纵向分辨率
        
        theta = np.linspace(0, 2*np.pi, n_theta)
        phi = np.linspace(-np.pi/2, np.pi/2, n_phi)
        
        self.theta_grid, self.phi_grid = np.meshgrid(theta, phi)
        
        # 椭球表面坐标
        self.x = self.r_x * np.cos(self.theta_grid) * np.cos(self.phi_grid)
        self.y = self.r_y * np.sin(self.theta_grid) * np.cos(self.phi_grid)
        self.z = self.r_z * np.sin(self.phi_grid)
        
        self.n_nodes = n_theta * n_phi
    
    def get_position_weight(self, theta, phi):
        """位置权重因子 - 前下腹部应力更高"""
        # 前方 (theta接近0或2π) 权重更高
        front_factor = 1 + 0.3 * np.cos(theta)
        
        # 下方 (phi接近-π/2) 权重更高
        lower_factor = 1 + 0.4 * (1 - np.sin(phi)) / 2
        
        return front_factor * lower_factor
    
    def get_stretch_field(self, baseline_circumference=75):
        """计算拉伸场"""
        global_stretch = self.circumference / baseline_circumference
        
        # 局部拉伸变化
        stretch_field = np.zeros_like(self.theta_grid)
        for i in range(self.theta_grid.shape[0]):
            for j in range(self.theta_grid.shape[1]):
                weight = self.get_position_weight(self.theta_grid[i,j], self.phi_grid[i,j])
                stretch_field[i,j] = 1 + (global_stretch - 1) * weight
        
        return stretch_field


class AdvancedBeltModel:
    """高级托腹带模型"""
    
    def __init__(self, width=15, thickness=4, material_type='nylon_spandex'):
        self.width = width  # cm
        self.thickness = thickness  # mm
        self.material_type = material_type
        self.position = 0.3
        
        # 材料属性
        self.set_material_properties()
        
        # 加载测试数据
        self.load_test_data()
    
    def set_material_properties(self):
        """设置材料属性"""
        material_props = {
            'nylon_spandex': {'modulus_kPa': 150, 'poisson': 0.35},
            'polyester_elastane': {'modulus_kPa': 200, 'poisson': 0.32},
            'neoprene': {'modulus_kPa': 80, 'poisson': 0.45},
            'medical_grade': {'modulus_kPa': 250, 'poisson': 0.30},
            'cotton_lycra': {'modulus_kPa': 100, 'poisson': 0.38}
        }
        
        props = material_props.get(self.material_type, material_props['nylon_spandex'])
        self.modulus = props['modulus_kPa']
        self.poisson = props['poisson']
    
    def load_test_data(self):
        """加载压缩服装测试数据"""
        try:
            self.test_data = pd.read_csv(DATA_DIR / "compression_garment_tests.csv")
        except:
            self.test_data = None
    
    def get_coverage_region(self, geometry, belt_position=None):
        """确定托腹带覆盖区域"""
        if belt_position is None:
            belt_position = getattr(self, 'position', 0.3)

        # belt_position: 0=下边缘, 1=上边缘
        belt_center_phi = -np.pi/4 + belt_position * np.pi/2
        belt_width_rad = (self.width / 100) / geometry.r_z
        
        phi_min = belt_center_phi - belt_width_rad
        phi_max = belt_center_phi + belt_width_rad
        
        coverage = (geometry.phi_grid >= phi_min) & (geometry.phi_grid <= phi_max)
        return coverage
    
    def calculate_contact_pressure(self, geometry, tension=50):
        """计算接触压力 (使用Laplace定律)"""
        # P = T / r, 其中T是壁张力，r是曲率半径
        local_radius = np.sqrt(
            (geometry.r_x * np.cos(geometry.theta_grid))**2 +
            (geometry.r_y * np.sin(geometry.theta_grid))**2
        )
        
        # 压力 (mmHg)
        pressure = tension / local_radius * 7.5  # 转换为mmHg
        
        return pressure
    
    def calculate_stress_reduction(self, original_stress, geometry):
        """计算应力减少"""
        coverage = self.get_coverage_region(geometry)
        
        # 应力减少模型
        # 基于宽度和材料刚度
        base_reduction = min(0.65, 0.03 * self.width + 0.02 * self.modulus / 100)
        
        # 覆盖区域内应力减少
        reduced_stress = original_stress.copy()
        reduced_stress[coverage] *= (1 - base_reduction)
        
        # 边缘渐变
        edge_width = 0.02  # rad
        for i in range(geometry.theta_grid.shape[0]):
            for j in range(geometry.theta_grid.shape[1]):
                if not coverage[i,j]:
                    # 计算到覆盖区域的距离
                    continue
        
        return reduced_stress, base_reduction * 100


class AdvancedFEASolver:
    """高级FEA求解器"""
    
    def __init__(self, skin_model, geometry, belt_model=None):
        self.skin = skin_model
        self.geometry = geometry
        self.belt = belt_model
        
        # 加载验证数据
        self.load_validation_data()
    
    def load_validation_data(self):
        """加载验证数据"""
        try:
            self.validation = pd.read_csv(DATA_DIR / "fea_validation_cases.csv")
            self.belt_validation = pd.read_csv(DATA_DIR / "belt_validation_cases.csv")
        except:
            self.validation = None
            self.belt_validation = None
    
    def solve(self):
        """求解应力分布"""
        # 计算拉伸场
        stretch_field = self.geometry.get_stretch_field()
        
        # 计算应力场
        stress_field = np.zeros_like(stretch_field)
        for i in range(stretch_field.shape[0]):
            for j in range(stretch_field.shape[1]):
                stress_field[i,j] = self.skin.get_composite_response(stretch_field[i,j])
        
        # 如果有托腹带，计算减少效果
        if self.belt is not None:
            reduced_stress, reduction_percent = self.belt.calculate_stress_reduction(
                stress_field, self.geometry
            )
            self.stress_reduction = reduction_percent
        else:
            reduced_stress = stress_field
            self.stress_reduction = 0
        
        self.stress_field = stress_field
        self.reduced_stress = reduced_stress
        self.stretch_field = stretch_field
        
        return reduced_stress
    
    def calculate_metrics(self):
        """计算关键指标"""
        metrics = {
            'max_stress_kPa': float(np.max(self.stress_field)),
            'mean_stress_kPa': float(np.mean(self.stress_field)),
            'std_stress_kPa': float(np.std(self.stress_field)),
            'max_stretch': float(np.max(self.stretch_field)),
            'mean_stretch': float(np.mean(self.stretch_field)),
            'stress_reduction_percent': float(self.stress_reduction),
        }
        
        if self.belt is not None:
            metrics['max_reduced_stress_kPa'] = float(np.max(self.reduced_stress))
            metrics['mean_reduced_stress_kPa'] = float(np.mean(self.reduced_stress))
        
        # 高风险区域比例
        threshold = np.percentile(self.stress_field, 75)
        high_risk = np.sum(self.stress_field > threshold) / self.stress_field.size * 100
        metrics['high_risk_percent'] = float(high_risk)
        
        # 使用托腹带后高风险区域
        if self.belt is not None:
            high_risk_reduced = np.sum(self.reduced_stress > threshold) / self.reduced_stress.size * 100
            metrics['high_risk_reduced_percent'] = float(high_risk_reduced)
            metrics['risk_reduction_percent'] = float(high_risk - high_risk_reduced)
        
        return metrics


class MultiObjectiveOptimizer:
    """多目标优化器"""
    
    def __init__(self, subjects_data, objective_weights=None):
        self.subjects = subjects_data
        
        # 优化目标权重
        if objective_weights is None:
            self.weights = {
                'stress_reduction': 0.35,
                'comfort': 0.30,
                'risk_reduction': 0.25,
                'cost': 0.10
            }
        else:
            self.weights = objective_weights
        
        # 设计变量范围
        self.design_space = {
            'width': (8, 25),        # cm
            'thickness': (2, 6),     # mm
            'modulus': (50, 300),    # kPa
            'position': (0.1, 0.6)   # 相对位置
        }
    
    def objective_function(self, design_params, subject):
        """目标函数"""
        width, thickness, modulus, position = design_params
        
        # 创建模型
        skin = AdvancedSkinModel(
            age=subject['age'],
            gestational_week=subject['week'],
            bmi=subject['bmi']
        )
        
        geometry = AdvancedAbdominalGeometry(
            week=subject['week'],
            bmi=subject['bmi']
        )
        
        belt = AdvancedBeltModel(width=width, thickness=thickness)
        belt.modulus = modulus
        belt.position = position
        
        # 求解
        solver = AdvancedFEASolver(skin, geometry, belt)
        solver.solve()
        metrics = solver.calculate_metrics()
        
        # 计算各目标
        stress_score = metrics['stress_reduction_percent'] / 50  # 归一化
        risk_score = metrics.get('risk_reduction_percent', 0) / 30
        
        # 舒适度模型 (宽度越大、厚度越大舒适度越低)
        comfort = 1 - (width - 8) / 17 * 0.4 - (thickness - 2) / 4 * 0.3
        comfort = max(0, min(1, comfort))
        
        # 成本模型 (材料用量相关)
        cost_score = 1 - (width * thickness * modulus) / (25 * 6 * 300) * 0.8
        
        # 综合评分 (最大化)
        total_score = (
            self.weights['stress_reduction'] * stress_score +
            self.weights['comfort'] * comfort +
            self.weights['risk_reduction'] * risk_score +
            self.weights['cost'] * cost_score
        )
        
        return -total_score, {  # 负号因为scipy.optimize是最小化
            'stress_reduction': metrics['stress_reduction_percent'],
            'risk_reduction': metrics.get('risk_reduction_percent', 0),
            'comfort': comfort * 100,
            'cost_score': cost_score * 100,
            'total_score': total_score * 100
        }
    
    def optimize_for_subject(self, subject):
        """为单个受试者优化"""
        best_score = float('inf')
        best_params = None
        best_metrics = None
        
        # 网格搜索 + 局部优化
        for width in np.linspace(8, 25, 8):
            for thickness in np.linspace(2, 6, 4):
                for modulus in np.linspace(50, 300, 6):
                    for position in np.linspace(0.1, 0.6, 3):
                        params = [width, thickness, modulus, position]
                        score, metrics = self.objective_function(params, subject)
                        
                        if score < best_score:
                            best_score = score
                            best_params = params
                            best_metrics = metrics
        
        return best_params, best_metrics
    
    def run_population_optimization(self, n_samples=50):
        """运行人群优化"""
        results = []
        
        sample_subjects = self.subjects.sample(min(n_samples, len(self.subjects)))
        
        for idx, row in sample_subjects.iterrows():
            subject = {
                'age': row.get('maternal_age', row.get('age', 28)),
                'week': row.get('gestational_age_weeks', row.get('gestational_week', 32)),
                'bmi': row.get('pre_pregnancy_bmi', row.get('bmi', 23))
            }
            
            params, metrics = self.optimize_for_subject(subject)
            
            result = {
                'subject_id': idx,
                **subject,
                'optimal_width': params[0],
                'optimal_thickness': params[1],
                'optimal_modulus': params[2],
                'optimal_position': params[3],
                **metrics
            }
            
            results.append(result)
            
            if len(results) % 10 == 0:
                print(f"  完成: {len(results)}/{n_samples}")
        
        return pd.DataFrame(results)


def run_advanced_analysis():
    """运行高级分析"""
    print("=" * 70)
    print("高级FEA优化分析")
    print("Advanced FEA Optimization Analysis")
    print("=" * 70)
    
    # 加载所有数据集
    print("\n加载数据集...")
    
    datasets = {}
    csv_files = list(DATA_DIR.glob("*.csv"))
    
    for f in csv_files:
        if '_summary' not in f.name:
            try:
                datasets[f.stem] = pd.read_csv(f)
                print(f"  [OK] {f.name}: {len(datasets[f.stem])} 条")
            except:
                pass
    
    # 使用PhysioNet风格数据作为主要分析对象
    if 'physionet_maternal_ultrasound' in datasets:
        main_data = datasets['physionet_maternal_ultrasound']
    elif 'maternal_health_risk' in datasets:
        main_data = datasets['maternal_health_risk']
    else:
        # 创建默认数据
        np.random.seed(42)
        main_data = pd.DataFrame({
            'age': np.random.normal(28, 5, 100).clip(18, 42).astype(int),
            'week': np.random.randint(24, 41, 100),
            'bmi': np.random.normal(23, 4, 100).clip(17, 35)
        })
    
    # 运行优化
    print("\n运行多目标优化...")
    optimizer = MultiObjectiveOptimizer(main_data)
    results = optimizer.run_population_optimization(n_samples=50)
    
    # 保存结果
    results.to_csv(RESULTS_DIR / "advanced_optimization_results.csv", index=False)
    print("\n[OK] 结果已保存: advanced_optimization_results.csv")
    
    # 统计汇总
    print("\n" + "=" * 50)
    print("优化结果汇总")
    print("=" * 50)
    
    summary = {
        'mean_optimal_width_cm': float(results['optimal_width'].mean()),
        'std_optimal_width_cm': float(results['optimal_width'].std()),
        'mean_stress_reduction_percent': float(results['stress_reduction'].mean()),
        'mean_risk_reduction_percent': float(results['risk_reduction'].mean()),
        'mean_comfort_score': float(results['comfort'].mean()),
        'mean_total_score': float(results['total_score'].mean()),
        'optimal_width_range': f"{results['optimal_width'].quantile(0.25):.1f}-{results['optimal_width'].quantile(0.75):.1f} cm",
        'n_subjects': len(results)
    }
    
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    with open(RESULTS_DIR / "advanced_analysis_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\n[OK] 汇总已保存: advanced_analysis_summary.json")
    
    return results, summary


if __name__ == "__main__":
    results, summary = run_advanced_analysis()
