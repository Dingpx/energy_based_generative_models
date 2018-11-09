import matplotlib.pyplot as plt
from pathlib import Path
import argparse
import os
import time
import numpy as np

import torch

from utils import save_samples_energies
from data.toy import inf_train_gen
from networks.toy import Generator, EnergyModel
from train_functions import train_wgan_generator, train_wgan_discriminator


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--save_path', required=True)

    parser.add_argument('--input_dim', type=int, default=2)
    parser.add_argument('--z_dim', type=int, default=2)
    parser.add_argument('--dim', type=int, default=512)

    parser.add_argument('--critic_iters', type=int, default=5)
    parser.add_argument('--lamda', type=float, default=.1)

    parser.add_argument('--batch_size', type=int, default=256)
    parser.add_argument('--iters', type=int, default=100000)
    parser.add_argument('--n_points', type=int, default=1600)
    parser.add_argument('--log_interval', type=int, default=100)
    parser.add_argument('--save_interval', type=int, default=1000)

    args = parser.parse_args()
    return args


args = parse_args()
root = Path(args.save_path)

#################################################
# Create Directories
#################################################
if root.exists():
    os.system('rm -rf %s' % str(root))

os.makedirs(str(root))
os.system('mkdir -p %s' % str(root / 'models'))
os.system('mkdir -p %s' % str(root / 'images'))
#################################################

itr = inf_train_gen(args.dataset, args.batch_size)
netG = Generator(args.input_dim, args.z_dim, args.dim).cuda()
netD = EnergyModel(args.input_dim, args.dim).cuda()

params = {'lr': 1e-4, 'betas': (0.5, 0.9)}
optimizerD = torch.optim.Adam(netD.parameters(), **params)
optimizerG = torch.optim.Adam(netG.parameters(), **params)

#################################################
# Dump Original Data
#################################################
orig_data = itr.__next__()
plt.clf()
plt.scatter(orig_data[:, 0], orig_data[:, 1])
plt.savefig(root / 'images/orig.png')
##################################################

start_time = time.time()
d_costs = []
for iters in range(args.iters):
    train_wgan_generator(netG, netD, optimizerG, args)

    for i in range(args.critic_iters):
        x_real = torch.from_numpy(itr.__next__()).cuda()
        train_wgan_discriminator(
            x_real, netG, netD, optimizerD,
            args, d_costs
        )

    if iters % args.log_interval == 0:
        print('Train Iter: {}/{} ({:.0f}%)\t'
              'D_costs: {} Time: {:5.3f}'.format(
                  iters, args.iters,
                  (args.log_interval * iters) / args.iters,
                  np.asarray(d_costs).mean(0),
                  (time.time() - start_time) / args.log_interval
              ))
        save_samples_energies(netG, netD, args)

        d_costs = []
        start_time = time.time()

    if iters % args.save_interval == 0:
        torch.save(
            netG.state_dict(),
            root / 'models/netG.pt'
        )
        torch.save(
            netD.state_dict(),
            root / 'models/netD.pt'
        )
