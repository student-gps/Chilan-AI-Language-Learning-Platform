# -*- coding: utf-8 -*-
import os
import sys
import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import GroupShuffleSplit
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree

from embedding_provider_cache import EmbeddingProviderCache, MODELS, ensure_utf8_stdout


current_file_path = Path(__file__).resolve()

try:
    from test_cases import test_suites
except ImportError:
    print("❌ 错误：请确保同目录下存在 test_cases.py 文件")
    sys.exit(1)

ensure_utf8_stdout()

TRAIN_TEST_RATIO = 0.3
RANDOM_STATE = 42
TREE_DEPTHS = list(range(1, 7))
TREE_MIN_SAMPLES_LEAF = 4

embedding_service = EmbeddingProviderCache()


def get_embedding(text, model_tag):
    return embedding_service.get_embedding(text, model_tag)


def build_feature_dataframe(eval_mode):
    suite = test_suites[eval_mode]
    rows = []
    total_questions = len(suite)

    print(f"📚 [{eval_mode}] 共 {total_questions} 道题，开始计算五模型相似度...")

    for index, (title, content) in enumerate(suite.items(), start=1):
        print(f"   🧩 [{eval_mode}] 正在处理第 {index}/{total_questions} 题: {title}")
        standard_text = content["standard"]
        standard_vectors = {tag: get_embedding(standard_text, tag) for tag in MODELS}

        total_cases = len(content["cases"])
        for case_index, (test_text, label) in enumerate(content["cases"], start=1):
            print(f"      ✏️ Case {case_index}/{total_cases} | label={label} | answer={test_text[:60]}")
            row = {
                "eval_mode": eval_mode,
                "title": title,
                "standard": standard_text,
                "answer": test_text,
                "label": int(label),
            }
            for tag in MODELS:
                answer_vector = get_embedding(test_text, tag)
                standard_vector = standard_vectors[tag]
                if standard_vector is not None and answer_vector is not None:
                    sim = cosine_similarity([standard_vector], [answer_vector])[0][0]
                    row[tag] = round(float(sim), 6)
                else:
                    row[tag] = np.nan
            rows.append(row)

    df = pd.DataFrame(rows)
    return df.dropna(subset=list(MODELS.keys())).reset_index(drop=True)


def split_train_test(df):
    splitter = GroupShuffleSplit(n_splits=1, test_size=TRAIN_TEST_RATIO, random_state=RANDOM_STATE)
    train_idx, test_idx = next(splitter.split(df, y=df["label"], groups=df["title"]))
    train_df = df.iloc[train_idx].copy()
    test_df = df.iloc[test_idx].copy()
    print(
        f"✂️ 已完成分组切分: train={len(train_df)} | test={len(test_df)} | "
        f"train_titles={train_df['title'].nunique()} | test_titles={test_df['title'].nunique()}"
    )
    return train_df, test_df


def compute_metrics(y_true, preds, probs=None):
    metrics = {
        "accuracy": accuracy_score(y_true, preds),
        "precision": precision_score(y_true, preds, zero_division=0),
        "recall": recall_score(y_true, preds, zero_division=0),
        "f1": f1_score(y_true, preds, zero_division=0),
        "confusion_matrix": confusion_matrix(y_true, preds, labels=[0, 1]).tolist(),
    }
    if probs is not None and len(set(y_true)) > 1:
        metrics["auc"] = roc_auc_score(y_true, probs)
    else:
        metrics["auc"] = np.nan
    return metrics


def find_best_threshold(y_true, scores):
    best = {
        "threshold": 0.5,
        "accuracy": -1.0,
        "precision": 0.0,
        "recall": 0.0,
        "f1": -1.0,
    }
    for threshold in np.arange(0.05, 0.951, 0.005):
        preds = (scores >= threshold).astype(int)
        accuracy = accuracy_score(y_true, preds)
        precision = precision_score(y_true, preds, zero_division=0)
        recall = recall_score(y_true, preds, zero_division=0)
        f1 = f1_score(y_true, preds, zero_division=0)
        if (
            accuracy > best["accuracy"]
            or (accuracy == best["accuracy"] and f1 > best["f1"])
            or (
                accuracy == best["accuracy"]
                and f1 == best["f1"]
                and abs(threshold - 0.5) < abs(best["threshold"] - 0.5)
            )
        ):
            best = {
                "threshold": float(round(threshold, 3)),
                "accuracy": float(accuracy),
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1),
            }
    return best


def evaluate_single_models_same_split(train_df, test_df):
    single_rows = []
    best_tag = None
    best_payload = None

    for tag in MODELS:
        train_scores = train_df[tag].values
        train_labels = train_df["label"].values
        test_scores = test_df[tag].values
        test_labels = test_df["label"].values

        threshold_stats = find_best_threshold(train_labels, train_scores)
        test_preds = (test_scores >= threshold_stats["threshold"]).astype(int)
        test_metrics = compute_metrics(test_labels, test_preds, test_scores)

        payload = {
            "model_tag": tag,
            "threshold": threshold_stats["threshold"],
            "train_accuracy": threshold_stats["accuracy"],
            "train_precision": threshold_stats["precision"],
            "train_recall": threshold_stats["recall"],
            "train_f1": threshold_stats["f1"],
            "test_accuracy": test_metrics["accuracy"],
            "test_precision": test_metrics["precision"],
            "test_recall": test_metrics["recall"],
            "test_f1": test_metrics["f1"],
            "test_auc": test_metrics["auc"],
        }
        single_rows.append(payload)

        if (
            best_payload is None
            or payload["test_accuracy"] > best_payload["test_accuracy"]
            or (
                payload["test_accuracy"] == best_payload["test_accuracy"]
                and payload["test_f1"] > best_payload["test_f1"]
            )
        ):
            best_tag = tag
            best_payload = payload

    return pd.DataFrame(single_rows), best_tag, best_payload


def train_logistic_baseline(train_df, test_df):
    feature_names = list(MODELS.keys())
    X_train = train_df[feature_names].values
    y_train = train_df["label"].values
    X_test = test_df[feature_names].values
    y_test = test_df["label"].values

    model = LogisticRegression(random_state=RANDOM_STATE, max_iter=1000)
    model.fit(X_train, y_train)
    probs = model.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)
    metrics = compute_metrics(y_test, preds, probs)
    return model, metrics


def train_tree_model(train_df, test_df, depth):
    feature_names = list(MODELS.keys())
    X_train = train_df[feature_names].values
    y_train = train_df["label"].values
    X_test = test_df[feature_names].values
    y_test = test_df["label"].values

    model = DecisionTreeClassifier(
        criterion="gini",
        max_depth=depth,
        min_samples_leaf=TREE_MIN_SAMPLES_LEAF,
        random_state=RANDOM_STATE,
    )
    model.fit(X_train, y_train)

    probs = model.predict_proba(X_test)[:, 1]
    preds = model.predict(X_test)
    metrics = compute_metrics(y_test, preds, probs)

    result_df = test_df.copy()
    result_df["tree_score"] = probs
    result_df["pred_label"] = preds
    result_df["result_flag"] = np.where(result_df["pred_label"] == result_df["label"], "✅", "❌")
    return model, result_df, metrics


def get_rule_text(model):
    return export_text(model, feature_names=list(MODELS.keys()), decimals=3)


def plot_tree_rules(model, eval_mode, depth):
    plt.rcParams["font.sans-serif"] = ["SimHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False
    plt.figure(figsize=(20, 8))
    plot_tree(
        model,
        feature_names=list(MODELS.keys()),
        class_names=["错(0)", "对(1)"],
        filled=True,
        rounded=True,
        impurity=False,
        proportion=True,
        fontsize=10,
    )
    plt.title(f"{eval_mode} 决策树规则图 (max_depth={depth})")
    plt.tight_layout()
    plt.show()


def plot_depth_accuracy_curve(depth_df):
    plt.rcParams["font.sans-serif"] = ["SimHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    mode_order = ["English_Evaluation", "Chinese_Evaluation"]

    for ax, eval_mode in zip(axes, mode_order):
        mode_df = depth_df[depth_df["eval_mode"] == eval_mode].copy()
        ax.plot(
            mode_df["tree_max_depth"],
            mode_df["tree_accuracy"],
            marker="o",
            linewidth=2.5,
            color="#2563eb",
            label="Decision Tree",
        )
        logistic_acc = mode_df["logistic_accuracy"].iloc[0]
        single_acc = mode_df["best_single_test_accuracy"].iloc[0]
        single_tag = mode_df["best_single_model"].iloc[0]
        ax.axhline(
            logistic_acc,
            linestyle="--",
            color="#ef4444",
            linewidth=2,
            label=f"Logistic Regression = {logistic_acc:.3f}",
        )
        ax.axhline(
            single_acc,
            linestyle=":",
            color="#16a34a",
            linewidth=2,
            label=f"Best Single ({single_tag}) = {single_acc:.3f}",
        )
        ax.set_title(f"{eval_mode} 树深 vs 测试准确率")
        ax.set_xlabel("max_depth")
        ax.set_ylabel("Accuracy")
        ax.set_xticks(TREE_DEPTHS)
        ax.grid(alpha=0.25, linestyle="--")
        ax.legend(loc="best")

    plt.tight_layout()
    plt.show()


def run_tree_rule_analysis():
    print("🛠️ 规则树模型矩阵加载完成:")
    for tag, model_id in MODELS.items():
        print(f"   - {tag}: {model_id}")

    timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
    excel_path = f"TreeRuleEmbedding_Report_{timestamp}.xlsx"
    summary_rows = []

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        for eval_mode in ["English_Evaluation", "Chinese_Evaluation"]:
            print(f"\n🚀 开始分析: {eval_mode}")
            feature_df = build_feature_dataframe(eval_mode)
            if feature_df.empty:
                print(f"⚠️ {eval_mode} 没有可用数据，跳过。")
                continue

            train_df, test_df = split_train_test(feature_df)
            _, logistic_metrics = train_logistic_baseline(train_df, test_df)
            single_model_df, best_single_tag, best_single_payload = evaluate_single_models_same_split(train_df, test_df)

            print(f"\n[{eval_mode}] Logistic Regression 测试集表现:")
            print(f"  Accuracy: {logistic_metrics['accuracy']:.4f}")
            print(f"  Precision: {logistic_metrics['precision']:.4f}")
            print(f"  Recall: {logistic_metrics['recall']:.4f}")
            print(f"  F1: {logistic_metrics['f1']:.4f}")
            print(f"  AUC: {logistic_metrics['auc']:.4f}" if not np.isnan(logistic_metrics["auc"]) else "  AUC: N/A")
            print(f"\n[{eval_mode}] 同 split 最佳单模型: {best_single_tag}")
            print(f"  阈值: {best_single_payload['threshold']:.3f}")
            print(f"  Test Accuracy: {best_single_payload['test_accuracy']:.4f}")
            print(f"  Test Precision: {best_single_payload['test_precision']:.4f}")
            print(f"  Test Recall: {best_single_payload['test_recall']:.4f}")
            print(f"  Test F1: {best_single_payload['test_f1']:.4f}")
            print(
                f"  Test AUC: {best_single_payload['test_auc']:.4f}"
                if not np.isnan(best_single_payload["test_auc"])
                else "  Test AUC: N/A"
            )

            best_depth = None
            best_tree_model = None
            best_result_df = None
            best_tree_metrics = None
            best_rule_text = ""

            for depth in TREE_DEPTHS:
                print(f"\n🌲 [{eval_mode}] 正在训练规则树模型 (max_depth={depth})...")
                tree_model, result_df, tree_metrics = train_tree_model(train_df, test_df, depth)
                rule_text = get_rule_text(tree_model)

                print(f"[{eval_mode}] depth={depth} 测试集表现:")
                print(f"  Accuracy: {tree_metrics['accuracy']:.4f}")
                print(f"  Precision: {tree_metrics['precision']:.4f}")
                print(f"  Recall: {tree_metrics['recall']:.4f}")
                print(f"  F1: {tree_metrics['f1']:.4f}")
                print(f"  AUC: {tree_metrics['auc']:.4f}" if not np.isnan(tree_metrics["auc"]) else "  AUC: N/A")

                summary_rows.append(
                    {
                        "eval_mode": eval_mode,
                        "tree_max_depth": depth,
                        "tree_min_samples_leaf": TREE_MIN_SAMPLES_LEAF,
                        "logistic_accuracy": logistic_metrics["accuracy"],
                        "logistic_precision": logistic_metrics["precision"],
                        "logistic_recall": logistic_metrics["recall"],
                        "logistic_f1": logistic_metrics["f1"],
                        "logistic_auc": logistic_metrics["auc"],
                        "best_single_model": best_single_tag,
                        "best_single_threshold": best_single_payload["threshold"],
                        "best_single_test_accuracy": best_single_payload["test_accuracy"],
                        "best_single_test_precision": best_single_payload["test_precision"],
                        "best_single_test_recall": best_single_payload["test_recall"],
                        "best_single_test_f1": best_single_payload["test_f1"],
                        "best_single_test_auc": best_single_payload["test_auc"],
                        "tree_accuracy": tree_metrics["accuracy"],
                        "tree_precision": tree_metrics["precision"],
                        "tree_recall": tree_metrics["recall"],
                        "tree_f1": tree_metrics["f1"],
                        "tree_auc": tree_metrics["auc"],
                        "tree_rules": rule_text,
                    }
                )

                if (
                    best_tree_metrics is None
                    or tree_metrics["accuracy"] > best_tree_metrics["accuracy"]
                    or (
                        tree_metrics["accuracy"] == best_tree_metrics["accuracy"]
                        and tree_metrics["f1"] > best_tree_metrics["f1"]
                    )
                ):
                    best_depth = depth
                    best_tree_model = tree_model
                    best_result_df = result_df
                    best_tree_metrics = tree_metrics
                    best_rule_text = rule_text

            print(f"\n[{eval_mode}] 最佳树深 = {best_depth}")
            print(best_rule_text)

            feature_df.to_excel(writer, sheet_name=f"{eval_mode[:3]}_features", index=False)
            train_df.to_excel(writer, sheet_name=f"{eval_mode[:3]}_train", index=False)
            single_model_df.to_excel(writer, sheet_name=f"{eval_mode[:3]}_single_split", index=False)
            best_result_df.to_excel(writer, sheet_name=f"{eval_mode[:3]}_tree_test", index=False)
            pd.DataFrame([{"best_depth": best_depth, "rules": best_rule_text}]).to_excel(
                writer, sheet_name=f"{eval_mode[:3]}_rules", index=False
            )

            print(f"📈 [{eval_mode}] 正在绘制最佳决策树规则图...")
            plot_tree_rules(best_tree_model, eval_mode, best_depth)
            print(f"✅ [{eval_mode}] 分析完成。")

        if summary_rows:
            summary_df = pd.DataFrame(summary_rows)
            summary_df.to_excel(writer, sheet_name="summary", index=False)
            plot_depth_accuracy_curve(summary_df)

    embedding_service.flush(force=True)
    embedding_service.print_stats(prefix="📦 [TreeRule]")
    print(f"\n✅ 决策树规则分析报告已生成: {os.path.abspath(excel_path)}")


if __name__ == "__main__":
    run_tree_rule_analysis()
