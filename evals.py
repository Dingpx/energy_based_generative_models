import torch
import torch.nn.functional as F
import numpy as np
from tqdm import tqdm
from StackedMNIST.train_classifier import Net
from scipy.misc import imsave
import os
from pathlib import Path


def KLD(p, q):
    if 0 in q:
        raise ValueError
    return sum(_p * np.log(_p/_q) for (_p, _q) in zip(p, q) if _p != 0)


class ModeCollapseEval(object):
    def __init__(self, n_stack, z_dim):
        self.classifier = Net().cuda()
        self.classifier.load_state_dict(torch.load('StackedMNIST/pretrained_classifier.pt'))
        self.n_stack = n_stack
        self.n_samples = 26 * 10 ** n_stack
        self.z_dim = z_dim

    def count_modes(self, netG):
        counts = np.zeros([10] * self.n_stack)
        n_batches = max(1, self.n_samples // 1000)
        for i in tqdm(range(n_batches)):
            with torch.no_grad():
                z = torch.randn(1000, self.z_dim).cuda()
                x_fake = netG(z) * .5 + .5
                x_fake = x_fake.view(-1, 1, 28, 28)
                classes = F.softmax(self.classifier(x_fake), -1).max(1)[1]
                classes = classes.view(1000, self.n_stack).cpu().numpy()

                for line in classes:
                    counts[tuple(line)] += 1

        n_modes = 10 ** self.n_stack
        true_data = np.ones(n_modes) / float(n_modes)
        print("No. of modes captured: ", len(np.where(counts > 0)[0]))
        counts = counts.flatten() / counts.sum()
        print('Reverse KL: ', KLD(counts, true_data))


def tf_inception_score(netG, z_dim=128, n_samples=5000):
    netG.eval()
    from inception_score import get_inception_score
    all_samples = []
    for i in tqdm(range(n_samples // 100)):
        samples_100 = torch.randn(100, z_dim).cuda()
        all_samples.append(
            netG(samples_100).detach().cpu().numpy()
        )

    all_samples = np.concatenate(all_samples, axis=0)
    netG.train()
    return get_inception_score(all_samples)


def tf_fid(netG, save_dir='/Tmp/kumarrit/cifar_samples/', n_samples=5000):
    netG.eval()
    all_samples = []
    for i in tqdm(range(n_samples // 100)):
        samples_100 = torch.randn(100, 128).cuda()
        all_samples.append(
            netG(samples_100).detach().cpu().numpy()
        )

    all_samples = np.concatenate(all_samples, axis=0)
    all_samples = (((all_samples * .5) + .5) * 255).astype('int32')

    root = Path(save_dir)
    if root.exists():
        os.system('rm -rf %s' % save_dir)
        os.makedirs(str(root))

    for i in tqdm(range(all_samples.shape[0])):
        imsave(root / ('image_%d.png' % i), all_samples[i].transpose(1, 2, 0))
    netG.train()
    return os.system('python TTUR/fid.py %s ./TTUR/fid_stats_cifar10_train.npz --gpu 0' % str(root))
