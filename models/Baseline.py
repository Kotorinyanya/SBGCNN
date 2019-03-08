import torch
import torch.nn.functional as F
from torch import nn


class Baseline(torch.nn.Module):

    def __init__(self,
                 data,
                 dropout=0
                 ):
        super(Baseline, self).__init__()
        self.num_nodes = data.num_nodes
        self.num_features = data.num_features
        self.B = data.y.shape[0]
        # self.conv1d = nn.Conv1d(1, 1, kernel_size=self.num_features, stride=self.num_features)
        self.emb1 = nn.Linear(self.num_features - 7, 1)  # for adj
#         self.emb2 = nn.Linear(8, 1)
        self.fc1 = nn.Linear(int(8 * self.num_nodes / self.B), 6)
        # self.bn1 = nn.BatchNorm1d(6)
        self.drop1 = nn.Dropout(dropout)
        # self.fc2 = nn.Linear(8, 6)
        # self.bn2 = nn.BatchNorm1d(6)
        # self.drop2 = nn.Dropout(dropout)
        self.fc3 = nn.Linear(6, 2)

    def forward(self, x, edge_index, edge_attr, y):
        if x.dim() == 3:
            x, edge_index, edge_attr, y = \
                x.squeeze(0), edge_index.squeeze(0), edge_attr.squeeze(0), y.squeeze(0)

        B = y.shape[0]
        x = torch.cat([self.emb1(x[:, 7:]), x[:, :7]], dim=-1)
#         x = self.emb2(x)
        x = x.view(B, -1)
        x = F.elu(self.drop1(self.fc1(x)))
        # x = F.elu(self.drop2(self.bn2(self.fc2(x))))
        x = self.fc3(x)

        reg = torch.tensor([0], dtype=torch.float, device=x.device)
        return x, reg
