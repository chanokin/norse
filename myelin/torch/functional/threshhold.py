import torch
import torch.jit

from .heaviside import heaviside
from .superspike import super_fn
import numpy as np


class HeaviErfc(torch.autograd.Function):
    """Approximation of the heaviside step function as

    h(x,k) = 1/2 + 1/2 erfc(k x)

    where erfc is the error function.
    """

    @staticmethod
    def forward(ctx, x, k):
        ctx.save_for_backward(x, k)
        return heaviside(x)  # 0.5 + 0.5 * torch.erfc(k * x)

    @staticmethod
    def backward(ctx, dy):
        x, k, = ctx.saved_tensors
        derfc = (2 * torch.exp(-k.pow(2) * x.pow(2))) / (torch.tensor(np.pi).sqrt())
        return derfc * dy, None


heavi_erfc_fn = HeaviErfc.apply


class HeaviTanh(torch.autograd.Function):
    """Approximation of the heaviside step function as

    h(x,k) = 1/2 + 1/2 tanh(k x)
    """

    @staticmethod
    def forward(ctx, x, k):
        ctx.save_for_backward(x, k)
        return heaviside(x)  # 0.5 + 0.5 * torch.tanh(k * x)

    @staticmethod
    def backward(ctx, dy):
        x, k, = ctx.saved_tensors
        dtanh = 1 - (x * k).tanh().pow(2)
        return dy * dtanh, None


heavi_tanh_fn = HeaviTanh.apply


class Logistic(torch.autograd.Function):
    """Approximation of the heaviside step function as

    h(x,k) = 1/2 + 1/2 tanh(k x)
    """

    @staticmethod
    def forward(ctx, x, k):
        ctx.save_for_backward(x, k)
        p = 0.5 + 0.5 * torch.tanh(k * x)
        return torch.distributions.bernoulli.Bernoulli(probs=p).sample()

    @staticmethod
    def backward(ctx, dy):
        x, k, = ctx.saved_tensors
        dtanh = 1 - (x * k).tanh().pow(2)
        return dy * dtanh, None


logistic_fn = Logistic.apply


class HeaviCirc(torch.autograd.Function):
    """Approximation of the heaviside step function as

    h(x,epsilon) = 1/2 + 1/2 x / (x^2 + alpha^2)^{1/2}
    """

    @staticmethod
    def forward(ctx, x, alpha):
        ctx.save_for_backward(x, alpha)
        return heaviside(x)  # 0.5 + 0.5 * (x / (x.pow(2) + alpha ** 2).sqrt())

    @staticmethod
    def backward(ctx, dy):
        x, alpha, = ctx.saved_tensors

        return (
            dy
            * (
                -(x.pow(2) / (2 * (alpha ** 2 + x.pow(2)).pow(1.5)))
                + 1 / (2 * (alpha ** 2 + x.pow(2)).sqrt())
            )
            * 2
            * alpha,
            torch.zeros_like(x),
        )


heavi_circ_fn = HeaviCirc.apply


class CircDist(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x, alpha):
        ctx.save_for_backward(x, alpha)
        return torch.distributions.bernoulli.Bernoulli(
            0.5 + 0.5 * (x / (x.pow(2) + alpha ** 2).sqrt())
        ).sample()

    @staticmethod
    def backward(ctx, dy):
        x, alpha, = ctx.saved_tensors
        return (
            dy
            * (
                -(x.pow(2) / (2 * (alpha ** 2 + x.pow(2)).pow(1.5)))
                + 1 / (2 * (alpha ** 2 + x.pow(2)).sqrt())
            )
            * 2
            * alpha,
            None,
        )


circ_dist_fn = CircDist.apply


class HeaviTent(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x, alpha):
        ctx.save_for_backward(x, alpha)
        return heaviside(x)

    @staticmethod
    def backward(ctx, dy):
        x, alpha, = ctx.saved_tensors
        return torch.relu(1 - torch.abs(x)) * alpha * dy, None


heavi_tent_fn = HeaviTent.apply


def threshhold(x: torch.Tensor, method: str, alpha: float) -> torch.Tensor:
    if method == "heaviside":
        return heaviside(x)
    elif method == "super":
        return super_fn(x, alpha)
    elif method == "tanh":
        return heavi_tanh_fn(x, alpha)
    elif method == "tent":
        return heavi_tent_fn(x, alpha)
    elif method == "circ":
        return heavi_circ_fn(x, alpha)
    elif method == "logistic":
        return logistic_fn(x, alpha)
