# Maximum Entropy Generators for Energy-Based Models
## Code accompanying the ICML submission


All experiments have tensorboard visualizations for samples / density / train curves etc.

1. To run the toy data experiments:
```
python scripts/train/ebm_toy.py --dataset swissroll --save_path logs/swissroll
```

2. To run the discrete mode collapse experiment:
```
python scripts/train/ebm_mnist.py --save_path logs/mnist_3 --n_stack 3
```

3. To run the CIFAR image generation experiment:
```
python scripts/train/ebm_cifar.py --save_path logs/cifar
```

To run the MCMC evalulations on CIFAR data:
```
python scripts/test/eval_metrics_cifar --load_path logs/cifar --n_samples 50000 --mcmc_iters 5 --temp .01
```

4. To run the CelebA image generation experiments:
```
python scripts/train/ebm_celeba.py --save_path logs/celeba
```
