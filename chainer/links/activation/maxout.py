import numpy

import chainer
from chainer.backends import cuda
from chainer.functions.activation import maxout
from chainer import link
from chainer.links.connection import linear


class Maxout(link.Chain):
    """Fully-connected maxout layer.

    Let ``M``, ``P`` and ``N`` be an input dimension, a pool size,
    and an output dimension, respectively.
    For an input vector :math:`x` of size ``M``, it computes

    .. math::

      Y_{i} = \\mathrm{max}_{j} (W_{ij\\cdot}x + b_{ij}).

    Here :math:`W` is a weight tensor of shape ``(M, P, N)``,
    :math:`b` an  optional bias vector of shape ``(M, P)``
    and :math:`W_{ij\\cdot}` is a sub-vector extracted from
    :math:`W` by fixing first and second dimensions to
    :math:`i` and :math:`j`, respectively.
    Minibatch dimension is omitted in the above equation.

    As for the actual implementation, this chain has a
    Linear link with a ``(M * P, N)`` weight matrix and
    an optional ``M * P`` dimensional bias vector.

    Args:
        in_size (int): Dimension of input vectors.
        out_size (int): Dimension of output vectors.
        pool_size (int): Number of channels.
        initialW (:ref:`initializer <initializer>`): Initializer to
            initialize the weight. When it is :class:`numpy.ndarray`,
            its ``ndim`` should be 3.
        initial_bias (:ref:`initializer <initializer>`): Initializer to
            initialize the bias. If ``None``, the bias is omitted.
            When it is :class:`numpy.ndarray`, its ``ndim`` should be 2.

    Attributes:
        linear (~chainer.Link): The Linear link that performs
            affine transformation.

    .. seealso:: :func:`~chainer.functions.maxout`

    .. seealso::
         Goodfellow, I., Warde-farley, D., Mirza, M.,
         Courville, A., & Bengio, Y. (2013).
         Maxout Networks. In Proceedings of the 30th International
         Conference on Machine Learning (ICML-13) (pp. 1319-1327).
         `URL <http://jmlr.org/proceedings/papers/v28/goodfellow13.html>`_
    """

    def __init__(self, in_size, out_size, pool_size,
                 initialW=None, initial_bias=0):
        super(Maxout, self).__init__()

        linear_out_size = out_size * pool_size
        if initialW is not None:
            initialW = initialW.reshape(linear_out_size, in_size)

        if initial_bias is not None:
            if numpy.isscalar(initial_bias):
                dtype = chainer.get_dtype()
                initial_bias = numpy.full(
                    (linear_out_size,), initial_bias, dtype=dtype)
            elif isinstance(initial_bias, (numpy.ndarray, cuda.ndarray)):
                initial_bias = initial_bias.reshape(linear_out_size)
            else:
                raise ValueError(
                    'initial bias must be float, ndarray, or None')

        with self.init_scope():
            self.linear = linear.Linear(
                in_size, linear_out_size,
                nobias=initial_bias is None, initialW=initialW,
                initial_bias=initial_bias)

        self.out_size = out_size
        self.pool_size = pool_size

    def forward(self, x):
        """Applies the maxout layer.

        Args:
            x (~chainer.Variable): Batch of input vectors.

        Returns:
            ~chainer.Variable: Output of the maxout layer.
        """
        y = self.linear(x)
        return maxout.maxout(y, self.pool_size)
