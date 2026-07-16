from Dataset import ChessEvalDataset
from torch.utils.data import DataLoader

dataset = ChessEvalDataset("evals.jsonl")

loader = DataLoader(
    dataset,
    batch_size=256,
    shuffle=True
)

model = ChessEvalStreamDataset() 

for boards, targets in loader:
    # Feed boards into the model
    predictions = model(boards)
    # Compare predictions to targets
    ...