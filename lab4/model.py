import torch
import torch.nn as nn
import torch.nn.functional as F


class _BNReluConv(nn.Sequential):    
    def __init__(self, num_maps_in, num_maps_out, k=3, bias=True):
        """
        num_maps_in: number of input channels for the conv layer
        num_maps_out: number of output channels for the conv layer/ number of filters of the conv layer
        k: kernel size of the conv layer
        bias: if True, the batch normalization layer will have learnable affine parameters (scale and shift).
        """
        super(_BNReluConv, self).__init__()
        # YOUR CODE HERE
        self.append(torch.nn.BatchNorm2d(num_maps_in, affine=bias))
        self.append(torch.nn.ReLU())
        self.append(torch.nn.Conv2d(num_maps_in, num_maps_out, kernel_size=k))

class SimpleMetricEmbedding(nn.Module):
    def __init__(self, input_channels, emb_size=32):
        super().__init__()
        self.emb_size = emb_size
        # YOUR CODE HERE
        self.unit_1 = _BNReluConv(input_channels, emb_size, k=3)
        self.maxpool_1 = torch.nn.MaxPool2d(kernel_size=3, stride=2)
        self.unit_2 = _BNReluConv(emb_size, emb_size, k=3)
        self.maxpool_2 = torch.nn.MaxPool2d(kernel_size=3, stride=2)
        self.unit_3 = _BNReluConv(emb_size, emb_size, k=3)
        self.global_avg = nn.AvgPool2d(kernel_size=2)
        self.margin = 1
        

    def get_features(self, img):
        """
            Returns tensor with dimensions BATCH_SIZE, EMB_SIZE,
            img is tensor of dimenstions BATCH_SIZE, C, H, W -> (B, 1, 28, 28) for MNIST
        """ 
        # YOUR CODE HERE
        x = self.unit_1(img)
        x = self.maxpool_1(x)
        x = self.unit_2(x)
        x = self.maxpool_2(x)
        x = self.unit_3(x)
        x = self.global_avg(x)
        shape=x.shape # should be (B, EMB_SIZE, 1, 1) after global avg
        x=x.reshape(shape[0], shape[1]) #reshape to (B, EMB_SIZE)
        return x

    def loss(self, anchor, positive, negative):
        a_x = self.get_features(anchor)  # (B,E)
        p_x = self.get_features(positive) # (B,E)
        n_x = self.get_features(negative) # (B,E)
        # YOUR CODE HERE 
        distance_ap = torch.norm(a_x - p_x, p=2, dim=1) # (B,)Distance between anchor and positive
        distance_an = torch.norm(a_x - n_x, p=2, dim=1)  # (B,) Distance between anchor and negative
        loss = torch.clamp(distance_ap - distance_an + self.margin, min=0.0) #(B,)
        loss=loss.mean() #prosjek po B-u, skalar
        return loss