import sys
import torch
from torch import Tensor
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

sad_words = [
    "cry",
    "tears",
    "sad",
    "sorrow",
    "grief",
    "pain",
    "lonely"
]
normal_words = ["happy", "joy", "love", "smile", "cheerful", "excited", "fun"]

all_words = sad_words + normal_words
initial_labels = [1] * len(sad_words) + [0] * len(normal_words)

MAX_WORD_LENGTH = 10


def encode_word(word: str, max_length: int = MAX_WORD_LENGTH) -> list[int]:
    word = word.lower()
    numbers = [ord(char) for char in word]
    if len(numbers) < max_length:
        numbers += [0] * (max_length - len(numbers))
    return numbers[:max_length]


encoded_words = [encode_word(word) for word in all_words]

data = torch.tensor(encoded_words, dtype=torch.float32)
labels = torch.tensor(initial_labels, dtype=torch.long)


class WordDataset(Dataset[tuple[Tensor, Tensor]]):
    def __init__(self, data: Tensor, labels: Tensor) -> None:
        self.data = data
        self.labels = labels

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> tuple[Tensor, Tensor]:
        return self.data[idx], self.labels[idx]


dataset = WordDataset(data, labels)
train_loader = DataLoader(dataset, batch_size=4, shuffle=True)


class Model(nn.Module):
    def __init__(self) -> None:
        super(Model, self).__init__()
        self.fc1 = nn.Linear(MAX_WORD_LENGTH, 16)
        self.fc2 = nn.Linear(16, 8)
        self.fc3 = nn.Linear(8, 2)  # binary classification

    def forward(self, x: Tensor) -> Tensor:
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x


model = Model()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001) # type: ignore


def train(
    model: nn.Module,
    loader: DataLoader[tuple[Tensor, Tensor]],
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    epochs: int = 100,
) -> None:
    for epoch in range(epochs):
        running_loss = 0.0
        for inputs, targets in loader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        print(f"epoch [{epoch+1}/{epochs}], loss: {running_loss / len(loader):.4f}")


train(model, train_loader, criterion, optimizer)

torch.save(model.state_dict(), "sad_words_model.pth")


def load_model() -> nn.Module:
    model = Model()
    model.load_state_dict(torch.load("sad_words_model.pth", weights_only=True))
    model.eval()
    return model


def is_sad(model: nn.Module, word: str) -> bool:
    encoded = encode_word(word)
    # Add batch dimension
    input_tensor = torch.tensor(encoded, dtype=torch.float32).unsqueeze(0)
    with torch.no_grad():
        output = model(input_tensor)
        _, predicted_class = torch.max(output, 1)
    return predicted_class.item() == 1


loaded_model = load_model()

word = sys.argv[1]
result = is_sad(loaded_model, word)

print(f"'{word}' is {"sad" if result else "not sad"}.")
