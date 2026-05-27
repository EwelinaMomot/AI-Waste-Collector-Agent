import random
import torch
from PIL import Image
from torchvision import transforms, datasets

from ml.neural_network_classification import NeuralNetwork

#dodalam mapowanie bo ktos zrobil literowke w nazwie folderu 
DATASET_TO_GAME = {"zamieszane": "zmieszane"}
GAME_TO_DATASET = {"zmieszane": "zamieszane"}


class TrashClassifier:

    def __init__(self, model_path="trained_neural_network.pth", dataset_path="dataset_images/test"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.transform = transforms.Compose([
            transforms.Resize((128, 128)),
            transforms.ToTensor(),
        ])

        self.dataset = datasets.ImageFolder(root=dataset_path, transform=self.transform)
        self.classes = self.dataset.classes  # np. ['bio', 'papier', 'plastik_metal', 'szklo', 'zamieszane']

        self.images_by_class = {}
        for img_path, class_idx in self.dataset.samples:
            class_name = self.classes[class_idx]
            self.images_by_class.setdefault(class_name, []).append(img_path)

        self.model = NeuralNetwork().to(self.device)
        self.model.load_state_dict(
            torch.load(model_path, map_location=self.device, weights_only=True)
        )
        self.model.eval()
        print(f"TrashClassifier załadowany na {self.device}, klasy: {self.classes}")

    def classify(self, image_path):
        photo = Image.open(image_path).convert("RGB")
        tensor = self.transform(photo).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(tensor)

        predicted_idx = outputs.argmax(dim=1).item()
        dataset_class = self.classes[predicted_idx]

        # Mapowanie nazwy datasetu na nazwę gry
        return DATASET_TO_GAME.get(dataset_class, dataset_class)

    def get_random_image(self, game_trash_type, match_probability=0.75):
        dataset_type = GAME_TO_DATASET.get(game_trash_type, game_trash_type)

        if random.random() < match_probability and dataset_type in self.images_by_class:
            # Losujemy zdjęcie pasujące do typu
            return random.choice(self.images_by_class[dataset_type])
        else:
            # Losujemy zdjęcie z INNEJ kategorii
            other_types = [t for t in self.images_by_class if t != dataset_type]
            if other_types:
                chosen_type = random.choice(other_types)
                return random.choice(self.images_by_class[chosen_type])
            # jeśli nie ma innych kategorii
            return random.choice(self.images_by_class[dataset_type])
