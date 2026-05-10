import pandas as pd
import math

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
            return tree # dotarliśmy do liścia z decyzją
        
        root_node = next(iter(tree))
        value = row.get(root_node)
        
        if value in tree[root_node]:
            return self.predict_row(tree[root_node][value], row)
        else:
            return self.most_common_class
        
    def print_tree(self, tree=None, indent=""):
        if tree is None:
            tree = self.tree
            print("\nWYUCZONE DRZEWO DECYZYJNE:")
            
        if not isinstance(tree, dict):
            print(f"{indent}⏩ DECYZJA: {tree}")
            return
            
        root = next(iter(tree))
        print(f"{indent}❓ SPRAWDŹ ATRYBUT: [{root}]")
        for value, subtree in tree[root].items():
            print(f"{indent}   ➖ {root} == {value}:")
            self.print_tree(subtree, indent + "       ")

if __name__ == "__main__":
    try:
        df = pd.read_csv('../data/garbage_truck_data.csv', sep=';')
        print(f"Wczytano zbiór danych: {len(df)} wierszy.")
        
        ai_model = DecisionTreeID3()
        ai_model.train(df, target_column="Decision")
        
        ai_model.print_tree()
        
    except FileNotFoundError:
        print("Nie znaleziono pliku!")