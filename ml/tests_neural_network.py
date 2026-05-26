import torch
from PIL import Image
from torchvision import transforms, datasets
from neural_network_classification import NeuralNetwork
from pathlib import Path
from torch.utils.data import DataLoader

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

transform = transforms.Compose([
    transforms.Resize((128,128)),
    transforms.ToTensor(),
])

#Wczytywanie danych testowych
test_data = datasets.ImageFolder(root='dataset_images/test', transform=transform)

BASE_DIR = Path(__file__).resolve().parent.parent
sample_photo = BASE_DIR / 'dataset_images' / 'test' / 'plastik_metal' / 'plastic219.jpg'

classes = test_data.classes 
test_loader = DataLoader(test_data, batch_size=32, shuffle=False)

#Bezpieczna Inicjalizacja i załadowanie modelu na odpowiednie urządzenie
model = NeuralNetwork().to(device)
model.load_state_dict(torch.load('trained_neural_network.pth', map_location=device, weights_only=True))
model.eval() 
print(f"Sieć załadowana na {device} i gotowa do pracy!")

def test_single_photo(photo_url, trained_model, class_names):
    """Funkcja sprawdzająca tylko jedno konkretne zdjęcie"""
    
    photo = Image.open(photo_url).convert('RGB')
    # 3. Zgodność - wysyłamy obrazek na to samo urządzenie
    transformed_photo = transform(photo).unsqueeze(0).to(device)
    
    with torch.no_grad():
        outputs = trained_model(transformed_photo)
        
    predicted_class_id = outputs.argmax(dim=1).item() 
    decision = class_names[predicted_class_id]
    
    print(f"Decyzja Agenta: Wykryto odpad typu '{decision}'.")
    return 


def check_model_accuracy(trained_model, test_dataloader):
    """Funkcja analizująca cały zbiór testowy w poszukiwaniu skuteczności %"""
    
    correct_predictions = 0
    total_images = 0
    
    print("\nRozpoczynam testowanie na całym zbiorze...")
    
    with torch.no_grad():
        for images, labels in test_dataloader:
            
            # 4. Zgodność - wysyłamy paczki danych na to samo urządzenie
            images, labels = images.to(device), labels.to(device)
            
            outputs = trained_model(images)
            predicted_classes = outputs.argmax(dim=1)
            
            total_images += labels.size(0) 
            correct_predictions += (predicted_classes == labels).sum().item() 

    accuracy = (correct_predictions / total_images) * 100
    
    print("-" * 40)
    print("WYNIKI TESTU:")
    print(f"Przeanalizowano zdjęć: {total_images}")
    print(f"Poprawne decyzje: {correct_predictions}")
    print(f"SKUTECZNOŚĆ SIECI: {accuracy:.2f}%")
    print("-" * 40)
    
    return 


if __name__ == "__main__":
    test_single_photo(str(sample_photo), model, classes)
    check_model_accuracy(model, test_loader)