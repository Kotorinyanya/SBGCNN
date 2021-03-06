import torch
import torch.nn.functional as F
from torch import nn
from torch.nn import Parameter
from torch_geometric.nn.inits import uniform
from torch_geometric.utils import softmax, remove_self_loops
from torch_scatter import scatter_add

from utils import add_self_loops_with_edge_attr
import torch
from torch.nn import Parameter
import torch.nn.functional as F
from torch_scatter import scatter_add


# class EGATConv(torch.nn.Module):
#     """Adaptive Edge Features Graph Attentional Layer from the `"Adaptive Edge FeaturesGraph Attention Networks (GAT)"
#     <https://arxiv.org/abs/1809.02709`_ paper.
#     Args:
#         in_channels (int): Size of each input sample.
#         out_channels (int): Size of each output sample.
#         heads (int, optional): Number of multi-head-attentions. (default:
#             :obj:`1`)
#         concat (bool, optional): Whether to concat or average multi-head
#             attentions (default: :obj:`True`)
#         negative_slope (float, optional): LeakyRELU angle of the negative
#             slope. (default: :obj:`0.2`)
#         dropout (float, optional): Dropout propbability of the normalized
#             attention coefficients, i.e. exposes each node to a stochastically
#             sampled neighborhood during training. (default: :obj:`0`)
#         bias (bool, optional): If set to :obj:`False`, the layer will not learn
#             an additive bias. (default: :obj:`True`)
#     """
#
#     def __init__(self,
#                  in_channels,
#                  out_channels,
#                  heads=1,
#                  concat=True,
#                  negative_slope=0.2,
#                  dropout=0,
#                  bias=True):
#         super(EGATConv, self).__init__()
#
#         self.in_channels = in_channels
#         self.out_channels = out_channels
#         self.heads = heads
#         self.concat = concat
#         self.negative_slope = negative_slope
#         self.dropout = dropout
#
#         self.weight = Parameter(
#             torch.Tensor(in_channels, heads * out_channels))
#         self.att_weight = Parameter(torch.Tensor(1, heads, 2 * out_channels))
#
#         if bias and concat:
#             self.bias = Parameter(torch.Tensor(out_channels * heads))
#         elif bias and not concat:
#             self.bias = Parameter(torch.Tensor(out_channels))
#         else:
#             self.register_parameter('bias', None)
#
#         self.reset_parameters()
#
#     def reset_parameters(self):
#         size = self.heads * self.in_channels
#         uniform(size, self.weight)
#         uniform(size, self.att_weight)
#         uniform(size, self.bias)
#
#     def forward(self, x, edge_index, edge_attr=None):
#         x = x.unsqueeze(-1) if x.dim() == 1 else x
#         x = torch.mm(x, self.weight)
#         x = x.view(-1, self.heads, self.out_channels)
#
#         # Add self-loops to adjacency matrix.
#         edge_index, edge_attr = remove_self_loops(edge_index, edge_attr)
#         edge_index, edge_attr = add_self_loops_with_edge_attr(edge_index, edge_attr, num_nodes=x.size(0))
#         row, col = edge_index
#
#         # Compute attention coefficients.
#         alpha = torch.cat([x[row], x[col]], dim=-1)
#         alpha = (alpha * self.att_weight).sum(dim=-1)
#         alpha = F.leaky_relu(alpha, self.negative_slope)
#         # This will broadcast edge_attr across all attentions
#         alpha = torch.mul(alpha, edge_attr.float())
#         # alpha = softmax(alpha, edge_index[0], num_nodes=x.size(0))
#
#         # Sample attention coefficients stochastically.
#         dropout = self.dropout if self.training else 0
#         alpha = F.dropout(alpha, p=dropout, training=True)
#
#         # Sum up neighborhoods.
#         out = alpha.view(-1, self.heads, 1) * x[col]
#         out = scatter_add(out, row, dim=0, dim_size=x.size(0))
#
#         if self.concat is True:
#             out = out.view(-1, self.heads * self.out_channels)
#         else:
#             out = out.sum(dim=1) / self.heads
#
#         if self.bias is not None:
#             out = out + self.bias
#
#         return out, edge_index, alpha
#
#     def __repr__(self):
#         return '{}({}, {}, heads={})'.format(self.__class__.__name__,
#                                              self.in_channels,
#                                              self.out_channels, self.heads)

class EGATConv(torch.nn.Module):
    """Adaptive Edge Features Graph Attentional Layer from the `"Adaptive Edge FeaturesGraph Attention Networks (GAT)"
    <https://arxiv.org/abs/1809.02709`_ paper.
    Args:
        in_channels (int): Size of each input sample.
        out_channels (int): Size of each output sample.
        heads (int, optional): Number of multi-head-attentions. (default:
            :obj:`1`)
        concat (bool, optional): Whether to concat or average multi-head
            attentions (default: :obj:`True`)
        negative_slope (float, optional): LeakyRELU angle of the negative
            slope. (default: :obj:`0.2`)
        dropout (float, optional): Dropout propbability of the normalized
            attention coefficients, i.e. exposes each node to a stochastically
            sampled neighborhood during training. (default: :obj:`0`)
        bias (bool, optional): If set to :obj:`False`, the layer will not learn
            an additive bias. (default: :obj:`True`)
    """

    def __init__(self,
                 in_channels,
                 out_channels,
                 heads=1,
                 concat=True,
                 negative_slope=0.2,
                 dropout=0,
                 bias=True):
        super(EGATConv, self).__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.heads = heads
        self.concat = concat
        self.negative_slope = negative_slope
        self.dropout = dropout

        self.drop = nn.Dropout(dropout)

        self.weight = Parameter(
            torch.Tensor(in_channels, heads * out_channels))
        self.att_weight = Parameter(torch.Tensor(1, heads, 2 * out_channels))

        if bias and concat:
            self.bias = Parameter(torch.Tensor(out_channels * heads))
        elif bias and not concat:
            self.bias = Parameter(torch.Tensor(out_channels))
        else:
            self.register_parameter('bias', None)

        self.reset_parameters()

    def reset_parameters(self):
        size = self.heads * self.in_channels
        uniform(size, self.weight)
        uniform(size, self.att_weight)
        uniform(size, self.bias)

    def forward(self, x, edge_index, edge_attr=None, save=False):
        x = x.unsqueeze(-1) if x.dim() == 1 else x
        x = torch.mm(x, self.weight)
        x = x.view(-1, self.heads, self.out_channels)

        # Add self-loops to adjacency matrix.
        edge_index, edge_attr = remove_self_loops(edge_index, edge_attr)
        edge_index, edge_attr = add_self_loops_with_edge_attr(edge_index, edge_attr, num_nodes=x.size(0))
        row, col = edge_index

        # Compute attention coefficients.
        alpha = torch.cat([x[row], x[col]], dim=-1)
        alpha = alpha * self.att_weight

        if save:
            try:
                s_alpha_list = torch.load("s_alpha.pkl")
            except Exception as e:
                s_alpha_list = []
            s_alpha_list.append(alpha.detach().cpu())
            torch.save(s_alpha_list, "s_alpha.pkl")

        alpha = alpha.sum(dim=-1)
        alpha = F.leaky_relu(alpha, self.negative_slope)

        if save:
            try:
                plain_alpha_list = torch.load("plain_alpha.pkl")
            except Exception as e:
                plain_alpha_list = []
            plain_alpha_list.append(alpha.detach().cpu())
            torch.save(plain_alpha_list, "plain_alpha.pkl")

        # This will broadcast edge_attr across all attentions
        alpha = torch.mul(alpha, edge_attr.float())

        if save:
            try:
                alpha_list = torch.load("alpha.pkl")
                edge_index_list = torch.load("edge_index.pkl")
            except Exception as e:
                alpha_list, edge_index_list = [], []
            alpha_list.append(alpha.detach().cpu())
            edge_index_list.append(edge_index.detach().cpu())
            torch.save(alpha_list, "alpha.pkl")
            torch.save(edge_index_list, "edge_index.pkl")

        # Sample attention coefficients stochastically.
        alpha = self.drop(alpha)

        # Sum up neighborhoods.
        out = alpha.view(-1, self.heads, 1) * x[col]
        out = scatter_add(out, row, dim=0, dim_size=x.size(0))

        if self.concat is True:
            out = out.view(-1, self.heads * self.out_channels)
        else:
            out = out.sum(dim=1) / self.heads

        if self.bias is not None:
            out = out + self.bias

        return out, edge_index, alpha

    def __repr__(self):
        return '{}({}, {}, heads={})'.format(self.__class__.__name__,
                                             self.in_channels,
                                             self.out_channels, self.heads)


class MEGATConv(torch.nn.Module):
    # Multi-dimension versiion of EGAT
    """
    Adaptive Edge Features Graph Attentional Layer from the `"Adaptive Edge FeaturesGraph Attention Networks (GAT)"
    <https://arxiv.org/abs/1809.02709`_ paper.

    Args:
        in_channels (int): Size of each input sample.
        out_channels (int): Size of each output sample.
        heads (int, optional): Number of multi-head-attentions. (default:
            :obj:`1`)
        concat (bool, optional): Whether to concat or average multi-head
            attentions (default: :obj:`True`)
        negative_slope (float, optional): LeakyRELU angle of the negative
            slope. (default: :obj:`0.2`)
        dropout (float, optional): Dropout probability of the normalized
            attention coefficients, i.e. exposes each node to a stochastically
            sampled neighborhood during training. (default: :obj:`0`)
        bias (bool, optional): If set to :obj:`False`, the layer will not learn
            an additive bias. (default: :obj:`True`)
        edge_attr_dim (int, required): The dimension of edge features. (default: :obj:`1`)
    """

    def __init__(self,
                 in_channels,
                 out_channels,
                 concat=True,
                 negative_slope=0.2,
                 dropout=0,
                 bias=True,
                 edge_attr_dim=1):
        super(MEGATConv, self).__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.concat = concat
        self.negative_slope = negative_slope
        self.dropout = dropout
        self.edge_attr_dim = edge_attr_dim

        self.weight = nn.Parameter(
            torch.Tensor(in_channels, self.edge_attr_dim * out_channels))
        self.att_weight = nn.Parameter(torch.Tensor(1, edge_attr_dim, 2 * out_channels))

        if bias and concat:
            self.bias = nn.Parameter(torch.Tensor(out_channels * edge_attr_dim))
        elif bias and not concat:
            self.bias = nn.Parameter(torch.Tensor(out_channels))
        else:
            self.register_parameter('bias', None)

        self.reset_parameters()

    def reset_parameters(self):
        size = self.edge_attr_dim * self.in_channels
        uniform(size, self.weight)
        uniform(size, self.att_weight)
        uniform(size, self.bias)

    def forward(self, x, edge_index, edge_attr=None):
        x = x.unsqueeze(-1) if x.dim() == 1 else x
        x = torch.mm(x, self.weight)
        x = x.view(-1, self.edge_attr_dim, self.out_channels)

        row, col = edge_index

        # Compute attention coefficients
        alpha = torch.cat([x[row], x[col]], dim=-1)
        alpha = (alpha * self.att_weight).sum(dim=-1)
        alpha = F.leaky_relu(alpha, self.negative_slope)
        alpha = softmax(alpha, row, num_nodes=x.size(0))
        # This will broadcast edge_attr across all attentions
        alpha = torch.mul(alpha, edge_attr.float())
        alpha = F.normalize(alpha, p=1, dim=1)

        # Sample attention coefficients stochastically.
        dropout = self.dropout if self.training else 0
        alpha = F.dropout(alpha, p=dropout, training=True)

        # Sum up neighborhoods.
        out = alpha.view(-1, self.edge_attr_dim, 1) * x[col]
        out = scatter_add(out, row, dim=0, dim_size=x.size(0))

        if self.concat is True:
            out = out.view(-1, self.out_channels * self.edge_attr_dim)
        else:
            out = out.sum(dim=1) / self.edge_attr_dim

        if self.bias is not None:
            out = out + self.bias

        return out, alpha

    def __repr__(self):
        return '{}({}, {}, edge_attr_dim={})'.format(self.__class__.__name__,
                                                     self.in_channels,
                                                     self.out_channels,
                                                     self.edge_attr_dim
                                                     )
