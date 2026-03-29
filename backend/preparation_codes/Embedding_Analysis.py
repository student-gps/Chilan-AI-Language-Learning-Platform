# -*- coding: utf-8 -*-
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
import google.generativeai as genai
from zai import ZhipuAiClient
import voyageai
import dashscope
import datetime
from pathlib import Path  
from dotenv import load_dotenv
# 测试secret
current_file_path = Path(__file__).resolve()
backend_dir = current_file_path.parent.parent
env_path = backend_dir / ".env"

load_dotenv(dotenv_path=env_path)

# 导入测试用例
try:
    from test_cases import test_suites
except ImportError:
    print("❌ 错误：请确保同目录下存在 test_cases.py 文件")
    sys.exit(1)

# 强制 UTF-8 环境
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ================= 🚀 配置区 (改为从 ENV 读取) =================
# 读取 API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY")
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY")
ALI_API_KEY = os.getenv("ALI_API_KEY")

# 🌟 定义评测模型矩阵 (ID 全部由 ENV 控制)
# 如果 ENV 中没写，则使用你代码中原来的默认值作为兜底
MODELS = {
    "OA-Large": os.getenv("EMBED_OPENAI_MODEL_ID", "text-embedding-3-large"),
    "Gemini": os.getenv("EMBED_GEMINI_MODEL_ID", "gemini-embedding-001"),
    "ZP-3": os.getenv("EMBED_ZHIPU_MODEL_ID", "embedding-3"), # 建议在 env 增加此项
    "Voyage-4": os.getenv("EMBED_VOYAGE_MODEL_ID", "voyage-4-large"), # 建议在 env 增加此项
    "Ali": os.getenv("EMBED_ALI_MODEL_ID", "text-embedding-v4")
}

# --- 打印当前运行配置 (可选，方便调试) ---
print(f"🛠️  模型矩阵加载完成:")
for tag, m_id in MODELS.items():
    print(f"   - {tag}: {m_id}")

# ================= 初始化所有客户端 =================
client_oa = OpenAI(api_key=OPENAI_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)
client_zp = ZhipuAiClient(api_key=ZHIPUAI_API_KEY)
client_vo = voyageai.Client(api_key=VOYAGE_API_KEY)
dashscope.api_key = ALI_API_KEY

def get_embedding(text, model_tag):
    try:
        name = MODELS[model_tag]
        if "OA" in model_tag:
            return client_oa.embeddings.create(input=[text], model=name).data[0].embedding
        elif "Gemini" in model_tag:
            m_path = f"models/{name}" if not name.startswith("models/") else name
            return genai.embed_content(model=m_path, content=text, task_type="similarity")['embedding']
        elif "ZP" in model_tag:
            return client_zp.embeddings.create(model=name, input=[text]).data[0].embedding
        elif "Voyage" in model_tag:
            # Voyage 4 指定 2048 维度
            resp = client_vo.embed([text], model=name, output_dimension=2048)
            return resp.embeddings[0]
        elif "Ali" in model_tag:
            resp = dashscope.TextEmbedding.call(
                model=name,
                input=[text]
            )
            if resp.status_code == 200:
                return resp.output['embeddings'][0]['embedding']
            raise RuntimeError(f"{resp.code}: {resp.message}")
    except Exception as e:
        print(f"⚠️ 获取 {model_tag} ({MODELS[model_tag]}) 失败! 错误信息: {e}")
        return None

def run_analysis():
    all_dfs = []
    modes = ["English_Evaluation", "Chinese_Evaluation"]
    
    for mode in modes:
        print(f"\n🔍 正在开始 [{mode}] 维度的多模型深度对比...")
        suite = test_suites[mode]
        results = []
        
        for title, data in suite.items():
            std_txt = data["standard"]
            # 预抓取各家标准答案向量
            std_vecs = {tag: get_embedding(std_txt, tag) for tag in MODELS}
            
            for test_txt, score in data["cases"]:
                row = {"维度": mode, "题目": title, "标准": std_txt, "学生答案": test_txt, "人工评分": score}
                for tag in MODELS:
                    t_vec = get_embedding(test_txt, tag)
                    if std_vecs[tag] and t_vec:
                        sim = cosine_similarity([std_vecs[tag]], [t_vec])[0][0]
                        row[tag] = round(float(sim), 4)
                results.append(row)
        
        df_mode = pd.DataFrame(results)
        all_dfs.append(df_mode)
        
        # 实时生成五路对比图
        plot_model_ranges(df_mode, mode)

    # 汇总导出 Excel
    full_df = pd.concat(all_dfs)
    timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
    filename = f"Full_{len(MODELS)}Models_Report_{timestamp}.xlsx"
    full_df.to_excel(filename, index=False)
    print(f"\n✅ 全量评测圆满完成！报告已生成: {os.path.abspath(filename)}")

def plot_model_ranges(df, mode):
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False

    model_tags = list(MODELS.keys())
    fig, axes = plt.subplots(1, len(model_tags), figsize=(7.5 * len(model_tags), 8), sharey=True)
    if len(model_tags) == 1:
        axes = [axes]

    for i, tag in enumerate(model_tags):
        ax = axes[i]
        # 1. 绘制散点
        sns.stripplot(ax=ax, data=df, x='人工评分', y=tag, hue='人工评分', 
                      palette="viridis", size=7, jitter=0.2, alpha=0.5, legend=False)
        
        # 2. 计算区间统计
        stats = df.groupby('人工评分')[tag].agg(['min', 'max', 'mean']).reset_index()
        
        for _, row in stats.iterrows():
            grade = row['人工评分']
            g_min, g_max, g_mean = row['min'], row['max'], row['mean']
            
            # 绘制垂直区间线
            ax.vlines(x=grade-1, ymin=g_min, ymax=g_max, color='black', linewidth=2.5, alpha=0.7)
            ax.hlines(y=[g_min, g_max], xmin=grade-1.1, xmax=grade-0.9, color='black', linewidth=2.5)
            
            # 标注 Max/Min 值
            ax.text(grade-1.15, g_max, f'Max:{g_max:.3f}', ha='right', va='center', fontsize=9, color='#d62728', fontweight='bold')
            ax.text(grade-1.15, g_min, f'Min:{g_min:.3f}', ha='right', va='center', fontsize=9, color='#1f77b4', fontweight='bold')
            # 标注平均分
            ax.plot(grade-1, g_mean, marker='D', color='white', markeredgecolor='black', markersize=7)

        ax.set_title(f"模型: {tag}\n({MODELS[tag]})", fontsize=12, fontweight='bold')
        ax.set_xticks([0, 1, 2, 3])
        ax.set_xticklabels(['1分(错)', '2分', '3分', '4分'])
        ax.grid(axis='y', linestyle='--', alpha=0.3)

    plt.suptitle(f"{len(model_tags)}路语义边界压力测试 - {mode}\n(通过 .env 动态配置模型版本)", fontsize=22, y=1.05)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_analysis()
