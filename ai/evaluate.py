import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
LABEL_NAMES = ["ALERT", "DROWSY"]

def evaluate_model(model, X_test, y_test, threshold=0.5):
    """Đánh giá model trên tập test, trả về dict các chỉ số"""
    classes = list(model.classes_)
    proba = model.predict_proba(X_test)[:, classes.index(1)] if 1 in classes else np.zeros(len(X_test))
    y_pred = (proba >= threshold).astype(int)
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
    return {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, pos_label = 1, zero_division = 0),
        "recall": recall_score(y_test, y_pred, pos_label = 1, zero_division = 0),
        "f1": f1_score(y_test, y_pred, pos_label = 1, zero_division = 0),
        "confusion_matrix": cm.tolist(),
        "report": classification_report(
            y_test, y_pred, labels = [0,1], target_names = LABEL_NAMES, zero_division = 0
        ),
    }
def print_report(metrics):
    """In kết quả cho người đọc"""
    print("Kết quả đánh giá")
    print(f"Accuracy: {metrics['accuracy']:.3f}")
    print(f"Precision: {metrics['precision']:.3f}  (DROWSY)")
    print(f"Recall   : {metrics['recall']:.3f}  (DROWSY)")
    print(f"F1       : {metrics['f1']:.3f}  (DROWSY)")
    print("Confusion matrix [[TN, FP], [FN, TP]]:")
    for row in metrics["confusion_matrix"]:
        print("  ", row)
    print(metrics["report"])