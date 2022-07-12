from __future__ import print_function
import argparse
import torch
import torch.optim as optim
import torch.nn.functional as F
from torchvision import transforms, datasets
from torch.optim.lr_scheduler import StepLR
from model import CNN

def train(args, model, device, train_loader, optimizer, epoch):
    model.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(device), target.to(device)
        optimizer.zero_grad()
        output = model(data)
        loss = F.nll_loss(output, target) # Negative Log-likelihood loss
        loss.backward()
        optimizer.step()
        if batch_idx % args.log_interval == 0:
            print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(epoch, batch_idx * len(data), len(train_loader.dataset), 100. * batch_idx / len(train_loader), loss.item()))
            if args.dry_run:
                break

def test(model, device, test_loader):
    model.eval()
    test_loss = 0
    correct = 0
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            test_loss += F.nll_loss(output, target, reduction = 'sum').item() # Sum up batch loss
            pred = output.argmax(dim = 1, keepdim = True) # Get the index of the max log-probability
            correct += pred.eq(target.view_as(pred)).sum().item()
            
    test_loss /= len(test_loader.dataset)
    
    print('\nTest set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(test_loss, correct, len(test_loader.dataset), 100. * correct / len(test_loader.dataset)))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'PyTorch MNIST Example')
    parser.add_argument('--batch_size', type = int, default = 64, metavar = 'N', help = 'input batch size for training (default: 64)')
    parser.add_argument('--test-batch-size', type = int, default = 1000, metavar = 'N', help = 'input batch size for testing (default: 1000)')
    parser.add_argument('--epochs', type = int, default = 14, metavar = 'N', help = 'number of epochs to train (default: 14)')
    parser.add_argument('--lr', type = float, default = 1.0, metavar = 'LR', help = 'learning rate (default: 1.0)')
    parser.add_argument('--gamma', type = float, default = 0.7, metavar = 'M', help = 'learning rate step gamma (default: 0.7)')
    parser.add_argument('--no-cuda', action = 'store_true', default = False, help = 'disables cuda training')
    parser.add_argument('-dry-run', action = 'store_true', default = False, help = 'quickly check a single pass')
    parser.add_argument('--seed', type = int, default = 1, metavar = 'S', help = 'random seed (default: 1)')
    parser.add_argument('--log-interval', type = int, default = 10, metavar = 'N', help = 'how many batches to wait before logging training status')
    parser.add_argument('--save-model', action = 'store_true', default = False, help = 'For saving the current model')
    args = parser.parse_args()
    use_cuda = not args.no_cuda and torch.cuda.is_available()
    
    torch.manual_seed(args.seed)
    device = torch.device("cuda" if use_cuda else "cpu")
    
    train_kwargs = {'batch_size': args.batch_size}
    test_kwargs = {'batch_size': args.test_batch_size}
    if use_cuda:
        cuda_kwargs = {'num_workers': 1, 'pin_memory': True, 'shuffle': True}
        train_kwargs.update(cuda_kwargs)
        test_kwargs.update(cuda_kwargs)
    
    transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
    train_dataset = datasets.MNIST('../data', train = True, download = True, transform = transform)
    test_dataset = datasets.MNIST('../data', train = False, transform = transform)
    train_loader = torch.utils.data.DataLoader(train_dataset, **train_kwargs)
    test_loader = torch.utils.data.DataLoader(test_dataset, **test_kwargs)
    
    model = CNN().to(device)
    optimizer = optim.Adadelta(model.parameters(), lr = args.lr)
    scheduler = StepLR(optimizer, step_size = 1, gamma = args.gamma)
    for epoch in range(1, args.epochs + 1):
        train(args, model, device, train_loader, optimizer, epoch)
        test(model, device, test_loader)
        scheduler.step()
    
    if args.save_model:
        torch.save(model.state_dict(), "mnist_cnn.pt")
        
