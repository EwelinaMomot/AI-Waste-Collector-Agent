import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from pathlib import Path

#Przygotowanie zdjęć
transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
])

train_data = datasets.ImageFolder(root='dataset_images/train', transform=transform)
test_data = datasets.ImageFolder(root='dataset_images/test', transform=transform)

train_loader = DataLoader(train_data, batch_size=32, shuffle=True)
classes = train_data.classes 

#Automatyczne wykrycie i użycie karty graficznej (GPU), co drastycznie przyspieszy naukę
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.model = nn.Sequential(
            #analizuje proste krawędzie (wymiar obrazu: 128x128)
            nn.Conv2d(3, 16, kernel_size=3, padding=1), 
            nn.ReLU(),           
            nn.MaxPool2d(2),     # redukcja danych -> 64x64
            
            #analizuje tekstury i wzory (np. matowość papieru)
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),     # redukcja danych -> 32x32

            #analizuje skomplikowane kształty (np. gwint butelki)
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),     # redukcja danych -> 16x16
            
            nn.Flatten(),        # Spłaszczamy obraz z macierzy do jednego wymiaru
            
            #klasyfikacja
            # Wymiar to: 64 filtry * obrazek 16x16
            nn.Linear(64 * 16 * 16, 128), 
            nn.ReLU(),
            nn.Linear(128, 5),            # Ostateczna decyzja na 5 klas
            nn.LogSoftmax(dim=-1)         # Zwraca prawdopodobieństwa 
        )

    def forward(self, x):
        return self.model(x)

# Inicjalizacja sieci i wysłanie jej do pamięci odpowiedniego układu (CPU/GPU)
neuralNetwork = NeuralNetwork().to(device)

def train_neural_network():
    optimizer = torch.optim.SGD(neuralNetwork.parameters(), lr=0.01) # alg trenujacy - dlugosc kroku to 0.01
    criterion = nn.NLLLoss() # oblicza błąd (uzyskany wynik do oczekiwanego)
    n_epochs = 35 

    print(f"Rozpoczynam uczenie (Urządzenie: {device})...")
    
    # Pętla ucząca
    for epoch in range(n_epochs):
        neuralNetwork.train()
        running_loss = 0.0
        
        for images, labels in train_loader:
            # Wysyłamy zdjęcia do tego samego układu pamięci co sieć
            images, labels = images.to(device), labels.to(device)
            
            optimizer.zero_grad()            # czyszczenie pamięci 
            result = neuralNetwork(images)   # ustalenie wyniku
            blad = criterion(result, labels) # obliczenie błędu 
            blad.backward()                  # nauka na błędach 
            optimizer.step()                 # aktualizacja wag 
            
            running_loss += blad.item()
            
        sredni_blad = running_loss / len(train_loader)
        print(f"Zakończono rundę {epoch + 1}/{n_epochs} | Średni błąd (Loss): {sredni_blad:.4f}")

    #zapisuje wytrenowana siec
    torch.save(neuralNetwork.state_dict(), 'trained_neural_network.pth')
    print("Zapisano wyuczoną sieć na dysku!")

#Ukrywamy wywołanie, żeby plik z testami go nie uruchamiał podczas importu
if __name__ == "__main__":
    train_neural_network()