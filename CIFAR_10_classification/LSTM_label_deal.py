import jittor as jt
from jittor.optim import Optimizer
from jittor import nn
from jittor import Module
import random
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from jittor.dataset.cifar import CIFAR10
from jittor.dataset import DataLoader
import jittor.transform as trans


class LSTM(Module):
    def __init__(self):
        super(LSTM,self).__init__()
        self.lstm=nn.LSTM(1024,256,batch_first=True,num_layers=6)
        self.relu=nn.Relu()
        self.l1=nn.Linear(256,64)
        self.bn1=nn.BatchNorm(64)
        self.l2=nn.Linear(64,10)
        self.sigmoid=nn.Sigmoid()
    def execute(self,x):
        out,(h_n,c_n)=self.lstm(x)
        out=self.l1(out[-1,:,:])
        out=self.bn1(out)
        out=self.sigmoid(out)
        out=self.l2(out)
        out=self.relu(out)
        out=nn.softmax(out)
        return out


def Label_deal(train_data):
    train_data_loader=DataLoader(train_data,batch_size=32)
    for data in train_data_loader:
        imgs,targets=data
        new_imgs=[]
        new_targets=[]
        for i in range(len(targets)):
            if i%10!=0:
                if targets[i]>=5:
                    new_imgs.append(imgs[i])
                    new_targets.append(targets[i])
                else:
                    new_imgs.append(imgs[i])
                    new_targets.append(targets[i])
        yield new_imgs,new_targets


def train(net,train_data_loader,optimizer,total_train_step,epoch,compose):
    net.train()
    for data in train_data_loader:
        imgs,targets=data
        imgs,targets=jt.Var(imgs),jt.Var(targets)
        imgs,targets=imgs.float32(),targets.float32()
        imgs=imgs.permute(0,3,1,2)
        imgs=compose(imgs)
        imgs=imgs.view(-1,3,32*32)
        outputs=net(imgs)
        loss=nn.cross_entropy_loss(outputs,targets)
        optimizer.step(loss)
        total_train_step+=1
        if total_train_step %50 ==0:
            print('Train Epoch: {} , train_step: {} \tLoss: {:.6f}'.format(
                    epoch, total_train_step, loss.data[0]))

def test(net,test_data_loader,epoch,compose):
    net.eval()
    total_acc = 0
    total_num = 0
    for batch_idx, (inputs, targets) in enumerate(test_data_loader):
        batch_size = 64
        inputs,targets=inputs.permute(0,3,1,2).float32(),targets.float32()
        inputs=compose(inputs)
        inputs=inputs.view(-1,3,32*32)
        outputs = net(inputs)
        pred = np.argmax(outputs.data, axis=1)
        acc = np.sum(targets.data==pred)
        total_acc += acc
        total_num += batch_size
        acc = acc / batch_size
        if batch_idx % 10 == 0:
            print('Test Epoch: {} [{}/{} ({:.0f}%)]\tAcc: {:.6f}'.format(epoch, \
                    batch_idx*batch_size, len(test_data_loader),100. * float(batch_idx)*batch_size / len(test_data_loader), acc))
    print ('Total test acc =', total_acc / total_num)
    return total_acc/total_num

def main():
    net=LSTM()
    train_data=CIFAR10(train=True)
    test_data=CIFAR10(train=False)
    compose=trans.Compose([trans.ImageNormalize((0.485,0.456,0.406),(0.229, 0.224, 0.225))])
    #train_data_loader=DataLoader(train_data,batch_size=64)
    test_data_loader=DataLoader(test_data,batch_size=64)
    learning_rate=0.01
    optimizer=nn.SGD(net.parameters(),lr=learning_rate,momentum=0.9,weight_decay=0.05)
    scheduler = jt.lr_scheduler.StepLR(optimizer, step_size=30, gamma=0.1)
    total_train_step=0
    total_test_step=0
    test_acc=[]
    epochs=100
    for epoch in range(epochs):
        print("epochs:{}".format(epoch+1))
        train_data_loader_dealed=Label_deal(train_data)
        train(net,train_data_loader_dealed,optimizer,total_train_step,epoch+1,compose)
        test_acc.append(test(net, test_data_loader, epoch+1,compose))
        scheduler.step()
        
    plt.plot(test_acc,'r',label="test_acc")
    plt.xlabel("Epochs")
    plt.ylabel("Loss")
    plt.legend()
    plt.show()    
if __name__=="__main__":
    main()