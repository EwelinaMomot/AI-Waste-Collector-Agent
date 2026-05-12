import itertools
import math
import os

import pandas as pd


class DecisionTreeID3:
    def __init__(self):
        self.tree = None
        self.most_common_class = None

    def calculate_entropy(self, data, target_column):
        entropy = 0

        value_counts = data[target_column].value_counts(normalize=True)
        for prob in value_counts:
            if prob > 0:
                entropy -= prob * math.log2(prob)
        return entropy
    
    def calculate_information_gain(self, data, attribute, target_column):
        total_entropy = self.calculate_entropy(data, target_column)
        
        values = data[attribute].value_counts(normalize=True)
        subset_entropy = 0
        for val, prob in values.items():
            subset = data[data[attribute] == val]
            subset_entropy += prob * self.calculate_entropy(subset, target_column)
            
        return total_entropy - subset_entropy
    
    def fit(self, data, features, target_column):
        unique_targets = data[target_column].unique()
        
        # warunki stopu
        if len(unique_targets) == 1:
            return unique_targets[0]
        if len(features) == 0:
            return data[target_column].mode()[0]
        
        # wybór najlepszego atrybutu
        gains = {feat: self.calculate_information_gain(data, feat, target_column) for feat in features}
        best_feature = max(gains, key=gains.get)
        
        tree = {best_feature: {}}
        remaining_features = [f for f in features if f != best_feature]

        for value in data[best_feature].unique():
            subset = data[data[best_feature] == value]
            subtree = self.fit(subset, remaining_features, target_column)
            tree[best_feature][value] = subtree
            
        return tree
    
    def train(self, data, target_column="Decision"):
        features = [col for col in data.columns if col != target_column]
        self.most_common_class = data[target_column].mode()[0]
        self.tree = self.fit(data, features, target_column)

    def predict_row(self, tree, row):
        if not isinstance(tree, dict):
            return tree  # dotarliśmy do liścia z decyzją

        root_node = next(iter(tree))
        if isinstance(row, pd.Series):
            value = row[root_node] if root_node in row.index else None
        else:
            value = row.get(root_node)

        if value in tree[root_node]:
            return self.predict_row(tree[root_node][value], row)
        return self.most_common_class

    def predict(self, current_state):
        if self.tree is None:
            raise RuntimeError("Drzewo nie zostało nauczone (wywołaj train).")
        row = pd.Series(current_state)
        return self.predict_row(self.tree, row)

    def format_tree_lines(self, tree=None, indent="  ", prefix=""):
        if tree is None:
            tree = self.tree
        lines = []
        if tree is None:
            return ["(puste drzewo)"]
        if not isinstance(tree, dict):
            lines.append(f"{prefix}=> {tree}")
            return lines
        root = next(iter(tree))
        lines.append(f"{prefix}[{root}]")
        for value, subtree in sorted(tree[root].items(), key=lambda x: str(x[0])):
            lines.append(f"{prefix}  == {value!r}")
            lines.extend(self.format_tree_lines(subtree, indent, prefix + indent))
        return lines

    def print_tree(self, tree=None, indent=""):
        if tree is None:
            tree = self.tree
            print("\nWYUCZONE DRZEWO DECYZYJNE (ID3):")
        for line in self.format_tree_lines(tree, indent="       ", prefix=""):
            print(line)

    def save_tree_preview(self, file_path):
        d = os.path.dirname(file_path)
        if d:
            os.makedirs(d, exist_ok=True)
        body = "\n".join(
            ["Drzewo decyzyjne ID3 — podgląd struktury", "=" * 50]
            + self.format_tree_lines()
        )
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(body)

    def export_graphviz_dot(self, file_path):
        if self.tree is None:
            raise RuntimeError("Brak drzewa do eksportu.")
        counter = itertools.count()
        nodes = []
        edges = []

        def walk(subtree, parent_id, edge_label):
            if not isinstance(subtree, dict):
                nid = f"n{next(counter)}"
                lab = str(subtree).replace("\\", "\\\\").replace('"', '\\"')
                nodes.append(f'{nid} [label="{lab}", shape=box, style=filled, fillcolor="#c8e6c9"];')
                if parent_id is not None:
                    el = str(edge_label).replace("\\", "\\\\").replace('"', '\\"')
                    edges.append(f'{parent_id} -> {nid} [label="{el}"];')
                return
            root = next(iter(subtree))
            nid = f"n{next(counter)}"
            lab = str(root).replace("\\", "\\\\").replace('"', '\\"')
            nodes.append(f'{nid} [label="{lab}", shape=diamond, style=filled, fillcolor="#fff9c4"];')
            if parent_id is not None:
                el = str(edge_label).replace("\\", "\\\\").replace('"', '\\"')
                edges.append(f'{parent_id} -> {nid} [label="{el}"];')
            for val, child in subtree[root].items():
                walk(child, nid, val)

        walk(self.tree, None, "")
        dot = "digraph ID3 {\n  rankdir=TB;\n" + "\n  ".join(nodes + edges) + "\n}\n"
        d = os.path.dirname(file_path)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(dot)

if __name__ == "__main__":
    try:
        df = pd.read_csv("../data/garbage_truck_data.csv", sep=";")
        print(f"Wczytano zbiór danych: {len(df)} wierszy.")

        ai_model = DecisionTreeID3()
        ai_model.train(df, target_column="Decision")

        ai_model.print_tree()
        os.makedirs("../output", exist_ok=True)
        ai_model.save_tree_preview("../output/decision_tree.txt")
        ai_model.export_graphviz_dot("../output/decision_tree.dot")
        print("Zapisano: ../output/decision_tree.txt, ../output/decision_tree.dot")

    except FileNotFoundError:
        print("Nie znaleziono pliku!")