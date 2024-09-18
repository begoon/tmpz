from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from pathlib import Path
import torch
import numpy as np
import matplotlib.pyplot as plt

class AlphabetDataset(Dataset):
    def __init__(self, data, labels):
        self.data = data
        self.labels = labels

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx], self.labels[idx]

alphabet_26 = Path("alphabet_26.bin").read_bytes()
alphabet_26_np = np.frombuffer(alphabet_26, dtype=np.uint8).reshape(26, 64)
print(alphabet_26_np.shape)



# Example: 26 characters (A-Z), each represented by a flattened 8x8 matrix (64 features)
# In practice, replace this with real data loading and preprocessing.
dataset_sz = 1000

data = torch.rand((dataset_sz, 64))  # 1000 images of size 8x8 (64 flattened pixels)
# data = torch.from_numpy(alphabet_26_np).float()  # Load the alphabet data
print(data.shape)

labels = torch.randint(0, 26, (dataset_sz,))  # Labels are integers from 0 to 25 representing A-Z

# Creating the dataset and dataloaders
dataset = AlphabetDataset(data, labels)
train_loader = DataLoader(dataset, batch_size=32, shuffle=True)

# Step 2: Define the model
class AlphabetRecognitionModel(nn.Module):
    def __init__(self):
        super(AlphabetRecognitionModel, self).__init__()
        self.fc1 = nn.Linear(64, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 26)   # output layer: 26 classes for A-Z
    
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x

model = AlphabetRecognitionModel()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Step 4: Train the model
def train(model, loader, criterion, optimizer, epochs=10):
    for epoch in range(epochs):
        running_loss = 0.0
        for inputs, targets in loader:
            optimizer.zero_grad()  # Zero the parameter gradients
            outputs = model(inputs)  # Forward pass
            loss = criterion(outputs, targets)  # Compute loss
            loss.backward()  # Backward pass
            optimizer.step()  # Optimize the model parameters

            running_loss += loss.item()
        print(f"Epoch [{epoch + 1}/{epochs}], Loss: {running_loss / len(loader):.4f}")

train(model, train_loader, criterion, optimizer)
torch.save(model.state_dict(), 'alphabet_model.pth')

def evaluate(model, loader):
    correct = 0
    total = 0
    with torch.no_grad():
        for inputs, targets in loader:
            outputs = model(inputs)
            _, predicted = torch.max(outputs.data, 1)
            total += targets.size(0)
            correct += (predicted == targets).sum().item()
    
    print(f'Accuracy: {100 * correct / total:.2f}%')


# Load the trained model (assuming the model is already trained and saved)
# model = AlphabetRecognitionModel()  # Initialize the model
# model.load_state_dict(torch.load('alphabet_model.pth'))  # Load the saved model
# model.eval()  # Set the model to evaluation mode

# For this example, we'll assume the model is already trained as per the previous code.
# Create an instance and load state if needed:
model = AlphabetRecognitionModel()
model.eval()

# Function to recognize the character from an 8x8 image
def recognize_character(image_8x8):
    """
    Function to recognize a character from an 8x8 image using the trained model.

    Args:
    - image_8x8 (numpy array or torch tensor): 8x8 grayscale image (flattened or unflattened)

    Returns:
    - recognized_char (str): The recognized character (A-Z)
    """
    # Preprocessing: Flatten the 8x8 image to a 1D vector of size 64 if not already flattened
    if image_8x8.shape == (8, 8):
        image_flat = image_8x8.flatten()  # Convert 8x8 to 64 length vector
    else:
        image_flat = image_8x8  # Assume already flattened
    
    # Convert to a PyTorch tensor and add batch dimension
    image_tensor = torch.tensor(image_flat, dtype=torch.float32).unsqueeze(0)

    # Perform inference
    with torch.no_grad():
        output = model(image_tensor)
        _, predicted_class = torch.max(output, 1)

    # Convert predicted class (index 0-25) to corresponding alphabet letter (A-Z)
    recognized_char = chr(predicted_class.item() + ord('A'))

    return recognized_char

letter = 25
alphabet = Path("alphabet_26.bin").read_bytes()

alphabet_np = np.frombuffer(alphabet, dtype=np.uint8).reshape(26, 8, 8)
sample_image = alphabet_np[letter]


plt.imshow(sample_image, cmap='gray')
plt.title('Input 8x8 Image')
plt.show()

recognized_char = recognize_character(sample_image)
print(f"Recognized Character: {recognized_char}")
