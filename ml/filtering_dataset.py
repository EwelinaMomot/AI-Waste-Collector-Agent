import pandas as pd

df = pd.read_csv('../data/garbage_truck_data_notbalanced.csv', sep=';')

classes = df['Decision'].unique()
num_classes = len(classes)

samples_per_class = 200 // num_classes

balanced_data = []

for cls in classes:
    # Wybieramy wszystkie wiersze dla danej decyzji
    class_df = df[df['Decision'] == cls]
    
    # Sprawdzamy czy mamy wystarczającą liczbę wierszy
    if len(class_df) >= samples_per_class:
        # Losujemy dokładnie wymaganą liczbę próbek
        sampled_df = class_df.sample(n=samples_per_class, random_state=42)
    else:
        # Jeśli klasa ma mniej wierszy, bierzemy wszystko co jest
        print(f"Ostrzeżenie: Klasa {cls} ma tylko {len(class_df)} wierszy.")
        sampled_df = class_df
        
    balanced_data.append(sampled_df)

#Łączenie w jeden zbiór i ewentualne dopełnienie do równych 200 jeśli brakuje
df_final = pd.concat(balanced_data).sample(frac=1, random_state=42).reset_index(drop=True)

#Zapisanie do pliku końcowego
df_final.to_csv('../data/garbage_truck_data.csv', index=False, sep=';')

print(f"Zbiór zbalansowany gotowy, liczba wierszy: {len(df_final)}")
print("Podział decyzji w pliku:\n", df_final['Decision'].value_counts())