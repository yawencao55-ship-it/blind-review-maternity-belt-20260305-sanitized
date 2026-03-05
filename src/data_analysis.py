"""
数据分析与可视化模块
Data Analysis and Visualization for Maternity Belt FEA Study

本模块包含:
1. 描述性统计分析
2. 相关性分析
3. 优化分析
4. 结果可视化
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体（如果可用）
try:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
except:
    pass

# 设置绘图风格
plt.style.use('seaborn-v0_8-whitegrid')

# 提高字体大小以保证图在缩小（约4cm宽）时仍可读
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 16
plt.rcParams['axes.titlesize'] = 18
plt.rcParams['axes.labelsize'] = 16
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['legend.fontsize'] = 14
plt.rcParams['figure.titlesize'] = 20

# 输出目录
OUTPUT_DIR = Path(__file__).parent / "results"
OUTPUT_DIR.mkdir(exist_ok=True)
DATA_DIR = Path(__file__).parent / "data"


def load_all_datasets():
    """加载所有数据集"""
    datasets = {}
    
    # 加载各数据集
    csv_files = [
        'maternal_health_risk.csv',
        'skin_biomechanics_literature.csv',
        'pregnancy_striae_studies.csv',
        'textile_mechanical_properties.csv',
        'maternity_belt_clinical_studies.csv',
        'fea_parametric_results.csv'
    ]
    
    for file in csv_files:
        path = DATA_DIR / file
        if path.exists():
            datasets[file.replace('.csv', '')] = pd.read_csv(path)
            print(f"  [OK] 已加载: {file}")
        else:
            print(f"  ✗ 未找到: {file}")
    
    return datasets


def analyze_maternal_health(df: pd.DataFrame):
    """分析孕妇健康风险数据"""
    print("\n" + "=" * 60)
    print("孕妇健康风险数据分析")
    print("=" * 60)
    
    print("\n1. 描述性统计:")
    print(df.describe().round(2).to_string())
    
    print("\n2. 风险等级分布:")
    if 'RiskLevel' in df.columns:
        risk_counts = df['RiskLevel'].value_counts()
        for level, count in risk_counts.items():
            print(f"   {level}: {count} ({count/len(df)*100:.1f}%)")
    
    print("\n3. 年龄与风险关系:")
    if 'Age' in df.columns and 'RiskLevel' in df.columns:
        age_risk = df.groupby('RiskLevel')['Age'].mean()
        for level, age in age_risk.items():
            print(f"   {level} 平均年龄: {age:.1f}")
    
    return df


def analyze_skin_biomechanics(df: pd.DataFrame):
    """分析皮肤生物力学文献数据"""
    print("\n" + "=" * 60)
    print("皮肤生物力学文献数据分析")
    print("=" * 60)
    
    print("\n1. 杨氏模量统计 (kPa):")
    E = df['youngs_modulus_kPa']
    print(f"   最小值: {E.min():.1f}")
    print(f"   最大值: {E.max():.1f}")
    print(f"   中位数: {E.median():.1f}")
    print(f"   平均值: {E.mean():.1f}")
    
    print("\n2. 按测试方法分类:")
    if 'test_method' in df.columns:
        method_stats = df.groupby('test_method')['youngs_modulus_kPa'].agg(['mean', 'count'])
        print(method_stats.round(1).to_string())
    
    print("\n3. 按身体部位分类:")
    if 'body_region' in df.columns:
        region_stats = df.groupby('body_region')['youngs_modulus_kPa'].agg(['mean', 'count'])
        print(region_stats.round(1).to_string())
    
    return df


def analyze_fea_results(df: pd.DataFrame):
    """分析FEA仿真结果"""
    print("\n" + "=" * 60)
    print("有限元分析结果统计")
    print("=" * 60)
    
    print("\n1. 应力减少效果:")
    print(f"   平均应力减少: {df['stress_reduction_percent'].mean():.1f}%")
    print(f"   最大应力减少: {df['stress_reduction_percent'].max():.1f}%")
    print(f"   最小应力减少: {df['stress_reduction_percent'].min():.1f}%")
    
    print("\n2. 托腹带宽度与效果关系:")
    width_effect = df.groupby(df['belt_width_cm'].round(0)).agg({
        'stress_reduction_percent': 'mean',
        'comfort_score': 'mean',
        'risk_reduction_percent': 'mean'
    }).round(2)
    print(width_effect.head(10).to_string())
    
    print("\n3. 孕周与应力关系:")
    week_stress = df.groupby('gestational_week').agg({
        'original_mean_stress_kPa': 'mean',
        'reduced_mean_stress_kPa': 'mean'
    }).round(2)
    print(week_stress.to_string())
    
    # 计算相关性
    print("\n4. 关键变量相关性:")
    corr_vars = ['belt_width_cm', 'stress_reduction_percent', 'comfort_score', 
                 'gestational_week', 'risk_reduction_percent']
    corr_matrix = df[corr_vars].corr()
    print(corr_matrix.round(3).to_string())
    
    return df


def find_optimal_belt_design(df: pd.DataFrame):
    """寻找最优托腹带设计"""
    print("\n" + "=" * 60)
    print("托腹带优化设计分析")
    print("=" * 60)
    
    # 多目标优化: 最大化风险减少和舒适度
    # 创建综合评分
    df['optimization_score'] = (
        df['risk_reduction_percent'] / df['risk_reduction_percent'].max() * 0.4 +
        df['comfort_score'] / 100 * 0.3 +
        df['stress_reduction_percent'] / df['stress_reduction_percent'].max() * 0.3
    ) * 100
    
    # 按托腹带宽度分组找最优
    optimal_per_width = df.groupby(df['belt_width_cm'].round(0)).agg({
        'optimization_score': 'mean',
        'stress_reduction_percent': 'mean',
        'comfort_score': 'mean',
        'risk_reduction_percent': 'mean'
    }).round(2)
    
    print("\n1. 各宽度托腹带的综合评分:")
    print(optimal_per_width.to_string())
    
    # 找到最优宽度
    best_width = optimal_per_width['optimization_score'].idxmax()
    print(f"\n2. 最优托腹带宽度: {best_width} cm")
    print(f"   综合评分: {optimal_per_width.loc[best_width, 'optimization_score']:.1f}/100")
    print(f"   应力减少: {optimal_per_width.loc[best_width, 'stress_reduction_percent']:.1f}%")
    print(f"   舒适度: {optimal_per_width.loc[best_width, 'comfort_score']:.1f}/100")
    print(f"   风险减少: {optimal_per_width.loc[best_width, 'risk_reduction_percent']:.1f}%")
    
    # 回归分析
    print("\n3. 托腹带宽度-效果回归分析:")
    X = df['belt_width_cm'].values.reshape(-1, 1)
    y = df['stress_reduction_percent'].values
    
    reg = LinearRegression()
    reg.fit(X, y)
    
    print(f"   回归系数: {reg.coef_[0]:.4f}")
    print(f"   截距: {reg.intercept_:.4f}")
    print(f"   R2: {r2_score(y, reg.predict(X)):.4f}")
    
    # 孕周分层分析
    print("\n4. 不同孕期的最优设计:")
    df['trimester'] = pd.cut(df['gestational_week'], 
                              bins=[23, 28, 34, 41], 
                              labels=['中期(24-28周)', '晚期前段(29-34周)', '晚期后段(35-40周)'])
    
    trimester_optimal = df.groupby('trimester').apply(
        lambda x: x.loc[x['optimization_score'].idxmax()]
    )[['belt_width_cm', 'optimization_score', 'stress_reduction_percent', 'comfort_score']]
    
    print(trimester_optimal.round(2).to_string())
    
    return df, optimal_per_width


def create_visualizations(datasets: dict, fea_df: pd.DataFrame, optimal_params: pd.DataFrame):
    """创建可视化图表"""
    print("\n" + "=" * 60)
    print("生成可视化图表")
    print("=" * 60)

    def _save_current_fig(stem: str):
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / f"{stem}.png", dpi=300, bbox_inches='tight')
        plt.savefig(OUTPUT_DIR / f"{stem}.pdf", bbox_inches='tight')
        plt.close()
    
    # 图1: 托腹带宽度与效果关系（保留合并版，同时导出拆分子图）
    width_effect = fea_df.groupby(fea_df['belt_width_cm'].round(0)).agg({
        'stress_reduction_percent': ['mean', 'std']
    })
    width_effect.columns = ['mean', 'std']
    comfort_effect = fea_df.groupby(fea_df['belt_width_cm'].round(0))['comfort_score'].mean()
    week_stress = fea_df.groupby('gestational_week').agg({
        'original_mean_stress_kPa': 'mean',
        'reduced_mean_stress_kPa': 'mean'
    })

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    ax1 = axes[0, 0]
    ax1.errorbar(width_effect.index, width_effect['mean'],
                 yerr=width_effect['std'], fmt='o-', capsize=5,
                 color='#2E86AB', linewidth=2, markersize=8)
    ax1.set_xlabel('Belt Width (cm)', fontsize=16)
    ax1.set_ylabel('Stress Reduction (%)', fontsize=16)
    ax1.set_title('(a) Belt Width vs Stress Reduction', fontsize=18, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    ax2 = axes[0, 1]
    ax2.bar(comfort_effect.index, comfort_effect.values, color='#A23B72', alpha=0.7)
    ax2.set_xlabel('Belt Width (cm)', fontsize=16)
    ax2.set_ylabel('Comfort Score', fontsize=16)
    ax2.set_title('(b) Belt Width vs Comfort Score', fontsize=18, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    ax3 = axes[1, 0]
    ax3.plot(optimal_params.index, optimal_params['optimization_score'],
             'g^-', linewidth=2, markersize=10, label='Optimization Score')
    ax3.fill_between(optimal_params.index, 0, optimal_params['optimization_score'],
                     alpha=0.3, color='green')
    ax3.set_xlabel('Belt Width (cm)', fontsize=16)
    ax3.set_ylabel('Optimization Score', fontsize=16)
    ax3.set_title('(c) Multi-objective Optimization Score', fontsize=18, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    ax4 = axes[1, 1]
    ax4.plot(week_stress.index, week_stress['original_mean_stress_kPa'],
             'r--', linewidth=2, label='Without Belt')
    ax4.plot(week_stress.index, week_stress['reduced_mean_stress_kPa'],
             'b-', linewidth=2, label='With Optimal Belt')
    ax4.fill_between(week_stress.index,
                     week_stress['reduced_mean_stress_kPa'],
                     week_stress['original_mean_stress_kPa'],
                     alpha=0.3, color='green', label='Stress Reduction')
    ax4.set_xlabel('Gestational Week', fontsize=16)
    ax4.set_ylabel('Mean Stress (kPa)', fontsize=16)
    ax4.set_title('(d) Stress vs Gestational Week', fontsize=18, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'fig1_optimization_analysis.png', dpi=300, bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / 'fig1_optimization_analysis.pdf', bbox_inches='tight')
    print("  [OK] 已保存: fig1_optimization_analysis.png/pdf")
    plt.close()

    # fig1a
    plt.figure(figsize=(8, 6))
    plt.errorbar(width_effect.index, width_effect['mean'],
                 yerr=width_effect['std'], fmt='o-', capsize=5,
                 color='#2E86AB', linewidth=2, markersize=8)
    plt.xlabel('Belt Width (cm)', fontsize=16)
    plt.ylabel('Stress Reduction (%)', fontsize=16)
    plt.title('(a) Belt Width vs Stress Reduction', fontsize=18, fontweight='bold')
    plt.grid(True, alpha=0.3)
    _save_current_fig('fig1a_stress_reduction')

    # fig1b
    plt.figure(figsize=(8, 6))
    plt.bar(comfort_effect.index, comfort_effect.values, color='#A23B72', alpha=0.7)
    plt.xlabel('Belt Width (cm)', fontsize=16)
    plt.ylabel('Comfort Score', fontsize=16)
    plt.title('(b) Belt Width vs Comfort Score', fontsize=18, fontweight='bold')
    plt.grid(True, alpha=0.3)
    _save_current_fig('fig1b_comfort_score')

    # fig1c
    plt.figure(figsize=(8, 6))
    plt.plot(optimal_params.index, optimal_params['optimization_score'],
             'g^-', linewidth=2, markersize=10, label='Optimization Score')
    plt.fill_between(optimal_params.index, 0, optimal_params['optimization_score'],
                     alpha=0.3, color='green')
    plt.xlabel('Belt Width (cm)', fontsize=16)
    plt.ylabel('Optimization Score', fontsize=16)
    plt.title('(c) Multi-objective Optimization Score', fontsize=18, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    _save_current_fig('fig1c_optimization_score')

    # fig1d
    plt.figure(figsize=(8, 6))
    plt.plot(week_stress.index, week_stress['original_mean_stress_kPa'],
             'r--', linewidth=2, label='Without Belt')
    plt.plot(week_stress.index, week_stress['reduced_mean_stress_kPa'],
             'b-', linewidth=2, label='With Optimal Belt')
    plt.fill_between(week_stress.index,
                     week_stress['reduced_mean_stress_kPa'],
                     week_stress['original_mean_stress_kPa'],
                     alpha=0.3, color='green', label='Stress Reduction')
    plt.xlabel('Gestational Week', fontsize=16)
    plt.ylabel('Mean Stress (kPa)', fontsize=16)
    plt.title('(d) Stress vs Gestational Week', fontsize=18, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    _save_current_fig('fig1d_stress_vs_week')
    
    # 图2: 相关性热力图（保留合并版，同时导出拆分子图）
    fig, ax1 = plt.subplots(1, 1, figsize=(8, 6))
    
    # 2.1 FEA结果相关性
                 'gestational_week', 'risk_reduction_percent', 'age']
    corr_matrix = fea_df[corr_vars].corr()
    
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, 
                ax=ax1, fmt='.2f', square=True,
                xticklabels=['Width', 'Stress Red.', 'Comfort', 'Week', 'Risk Red.', 'Age'],
                yticklabels=['Width', 'Stress Red.', 'Comfort', 'Week', 'Risk Red.', 'Age'])
    ax1.set_title('Correlation Matrix of FEA Results', fontsize=18, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'fig2_correlation_analysis.png', dpi=300, bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / 'fig2_correlation_analysis.pdf', bbox_inches='tight')
    print("  [OK] 已保存: fig2_correlation_analysis.png/pdf")
    plt.close()

    # fig2a
    plt.figure(figsize=(8, 6))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0,
                fmt='.2f', square=True,
                xticklabels=['Width', 'Stress Red.', 'Comfort', 'Week', 'Risk Red.', 'Age'],
                yticklabels=['Width', 'Stress Red.', 'Comfort', 'Week', 'Risk Red.', 'Age'])
    plt.title('Correlation Matrix of Model Outputs', fontsize=18, fontweight='bold')
    _save_current_fig('fig2a_correlation_matrix')


    # 图3: 皮肤力学参数分布（保留合并版，同时导出拆分子图）
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    if 'skin_biomechanics_literature' in datasets:
        skin_df = datasets['skin_biomechanics_literature']
        
        # 3.1 杨氏模量分布
        ax1 = axes[0]
        if 'test_method' in skin_df.columns:
            skin_df_filtered = skin_df[skin_df['youngs_modulus_kPa'] < 5000]
            for method in skin_df_filtered['test_method'].unique():
                subset = skin_df_filtered[skin_df_filtered['test_method'] == method]
                ax1.bar(method, subset['youngs_modulus_kPa'].mean(), 
                       yerr=subset['youngs_modulus_kPa'].std(), alpha=0.7, capsize=5)
        ax1.set_xlabel('Test Method', fontsize=16)
        ax1.set_ylabel("Young's Modulus (kPa)", fontsize=16)
        ax1.set_title('(a) Skin Elastic Modulus by Test Method', fontsize=18, fontweight='bold')
        ax1.tick_params(axis='x', rotation=45)
        
        # 3.2 按身体部位
        ax2 = axes[1]
        if 'body_region' in skin_df.columns:
            skin_df_filtered = skin_df[skin_df['youngs_modulus_kPa'] < 5000]
            region_data = skin_df_filtered.groupby('body_region')['youngs_modulus_kPa'].mean()
            ax2.barh(region_data.index, region_data.values, color='#3498db', alpha=0.7)
        ax2.set_xlabel("Young's Modulus (kPa)", fontsize=16)
        ax2.set_ylabel('Body Region', fontsize=16)
        ax2.set_title('(b) Skin Elastic Modulus by Body Region', fontsize=18, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'fig3_skin_biomechanics.png', dpi=300, bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / 'fig3_skin_biomechanics.pdf', bbox_inches='tight')
    print("  [OK] 已保存: fig3_skin_biomechanics.png/pdf")
    plt.close()

    if 'skin_biomechanics_literature' in datasets:
        skin_df = datasets['skin_biomechanics_literature']
        skin_df_filtered = skin_df[skin_df['youngs_modulus_kPa'] < 5000]

        # fig3a
        plt.figure(figsize=(9, 6))
        if 'test_method' in skin_df_filtered.columns:
            for method in skin_df_filtered['test_method'].unique():
                subset = skin_df_filtered[skin_df_filtered['test_method'] == method]
                plt.bar(method, subset['youngs_modulus_kPa'].mean(),
                        yerr=subset['youngs_modulus_kPa'].std(), alpha=0.7, capsize=5)
        plt.xlabel('Test Method', fontsize=16)
        plt.ylabel("Young's Modulus (kPa)", fontsize=16)
        plt.title('(a) Skin Elastic Modulus by Test Method', fontsize=18, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        _save_current_fig('fig3a_modulus_by_method')

        # fig3b
        plt.figure(figsize=(9, 6))
        if 'body_region' in skin_df_filtered.columns:
            region_data = skin_df_filtered.groupby('body_region')['youngs_modulus_kPa'].mean()
            plt.barh(region_data.index, region_data.values, color='#3498db', alpha=0.7)
        plt.xlabel("Young's Modulus (kPa)", fontsize=16)
        plt.ylabel('Body Region', fontsize=16)
        plt.title('(b) Skin Elastic Modulus by Body Region', fontsize=18, fontweight='bold')
        _save_current_fig('fig3b_modulus_by_region')
    
    # 图4: 妊娠纹风险分析（保留合并版，同时导出拆分子图）
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # 4.1 风险减少分布
    ax1 = axes[0]
    ax1.hist(fea_df['risk_reduction_percent'], bins=20, color='#27ae60', 
             alpha=0.7, edgecolor='black')
    ax1.axvline(fea_df['risk_reduction_percent'].mean(), color='red', 
                linestyle='--', linewidth=2, label=f'Mean: {fea_df["risk_reduction_percent"].mean():.1f}%')
    ax1.set_xlabel('Risk Reduction (%)', fontsize=16)
    ax1.set_ylabel('Frequency', fontsize=16)
    ax1.set_title('(a) Distribution of Striae Risk Reduction', fontsize=18, fontweight='bold')
    ax1.legend()
    
    # 4.2 年龄对风险的影响
    ax2 = axes[1]
    age_risk = fea_df.groupby('age').agg({
        'original_striae_risk_percent': 'mean',
        'reduced_striae_risk_percent': 'mean'
    })
    ax2.fill_between(age_risk.index, age_risk['original_striae_risk_percent'], 
                     alpha=0.5, color='red', label='Original Risk')
    ax2.fill_between(age_risk.index, age_risk['reduced_striae_risk_percent'], 
                     alpha=0.5, color='green', label='Reduced Risk')
    ax2.set_xlabel('Age', fontsize=16)
    ax2.set_ylabel('Striae Risk (%)', fontsize=16)
    ax2.set_title('(b) Age vs Striae Risk', fontsize=18, fontweight='bold')
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'fig4_striae_risk_analysis.png', dpi=300, bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / 'fig4_striae_risk_analysis.pdf', bbox_inches='tight')
    print("  [OK] 已保存: fig4_striae_risk_analysis.png/pdf")
    plt.close()

    # fig4a
    plt.figure(figsize=(8, 6))
    plt.hist(fea_df['risk_reduction_percent'], bins=20, color='#27ae60',
             alpha=0.7, edgecolor='black')
    plt.axvline(fea_df['risk_reduction_percent'].mean(), color='red',
                linestyle='--', linewidth=2,
                label=f"Mean: {fea_df['risk_reduction_percent'].mean():.1f}%")
    plt.xlabel('Risk Reduction (%)', fontsize=16)
    plt.ylabel('Frequency', fontsize=16)
    plt.title('(a) Distribution of Striae Risk Reduction', fontsize=18, fontweight='bold')
    plt.legend()
    _save_current_fig('fig4a_risk_reduction_distribution')

    # fig4b
    plt.figure(figsize=(8, 6))
    age_risk = fea_df.groupby('age').agg({
        'original_striae_risk_percent': 'mean',
        'reduced_striae_risk_percent': 'mean'
    })
    plt.fill_between(age_risk.index, age_risk['original_striae_risk_percent'],
                     alpha=0.5, color='red', label='Original Risk')
    plt.fill_between(age_risk.index, age_risk['reduced_striae_risk_percent'],
                     alpha=0.5, color='green', label='Reduced Risk')
    plt.xlabel('Age', fontsize=16)
    plt.ylabel('Striae Risk (%)', fontsize=16)
    plt.title('(b) Age vs Striae Risk', fontsize=18, fontweight='bold')
    plt.legend()
    _save_current_fig('fig4b_age_vs_risk')
    
    print(f"\n所有图表已保存到: {OUTPUT_DIR}")


def generate_summary_statistics(datasets: dict, fea_df: pd.DataFrame):
    """生成汇总统计报告"""
    
    summary = {
        'analysis_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'),
        'total_datasets': len(datasets),
        'total_records': sum(len(df) for df in datasets.values()),
        
        'fea_analysis': {
            'total_simulations': len(fea_df),
            'unique_subjects': fea_df['subject_id'].nunique(),
            'belt_designs_tested': fea_df['belt_design_id'].nunique(),
            'mean_stress_reduction': fea_df['stress_reduction_percent'].mean(),
            'max_stress_reduction': fea_df['stress_reduction_percent'].max(),
            'mean_risk_reduction': fea_df['risk_reduction_percent'].mean(),
            'mean_comfort_score': fea_df['comfort_score'].mean()
        },
        
        'optimal_design': {
            'belt_width_cm': float(fea_df.groupby('belt_width_cm')['optimization_score'].mean().idxmax()),
            'optimization_score': float(fea_df.groupby('belt_width_cm')['optimization_score'].mean().max())
        }
    }
    
    # 保存JSON报告
    import json
    with open(OUTPUT_DIR / 'analysis_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n分析汇总已保存到: {OUTPUT_DIR / 'analysis_summary.json'}")
    
    return summary


def main():
    """主函数"""
    print("=" * 70)
    print("数据分析与可视化")
    print("Maternity Belt FEA Data Analysis")
    print("=" * 70)
    
    # 1. 加载数据
    print("\n1. 加载数据集...")
    datasets = load_all_datasets()
    
    # 2. 分析各数据集
    if 'maternal_health_risk' in datasets:
        analyze_maternal_health(datasets['maternal_health_risk'])
    
    if 'skin_biomechanics_literature' in datasets:
        analyze_skin_biomechanics(datasets['skin_biomechanics_literature'])
    
    # 3. FEA结果分析
    if 'fea_parametric_results' in datasets:
        fea_df = datasets['fea_parametric_results']
        analyze_fea_results(fea_df)
        fea_df, optimal_params = find_optimal_belt_design(fea_df)
        
        # 4. 创建可视化
        create_visualizations(datasets, fea_df, optimal_params)
        
        # 5. 生成汇总
        generate_summary_statistics(datasets, fea_df)
    else:
        print("警告: 未找到FEA结果数据，跳过相关分析")
    
    print("\n" + "=" * 70)
    print("数据分析完成!")
    print("=" * 70)


if __name__ == "__main__":
    main()
