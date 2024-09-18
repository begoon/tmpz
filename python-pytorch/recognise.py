from pathlib import Path
import torch
import numpy as np
import matplotlib.pyplot as plt

from alphabet import AlphabetRecognitionModel

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

# Example Usage:
# Simulate an 8x8 image (in real use, replace this with actual image data)
sample_image = np.random.rand(8, 8)  # Replace this with actual image data

letter = 25
alphabet = Path("alphabet_26.bin").read_bytes()

alphabet_np = np.frombuffer(alphabet, dtype=np.uint8).reshape(26, 8, 8)
sample_image = alphabet_np[letter]


# Visualize the sample image (optional)
plt.imshow(sample_image, cmap='gray')
plt.title('Input 8x8 Image')
plt.show()

# Recognize the character
recognized_char = recognize_character(sample_image)
print(f"Recognized Character: {recognized_char}")
