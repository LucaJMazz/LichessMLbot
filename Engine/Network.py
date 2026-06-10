import torch
import torch.nn as nn

class ChessEvaluator(nn.Module):
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(69, 256),   # 69 inputs → 256 neurons
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1)      # single score output
        )

    def forward(self, x):
        return self.network(x)

# Create the model
model = ChessEvaluator()
print(model)

# Try it on a fake position (all zeros = empty board)
dummy_input = torch.zeros(1, 69)
score = model(dummy_input)
print(score)  # something random until trained, e.g. tensor([[0.0312]])