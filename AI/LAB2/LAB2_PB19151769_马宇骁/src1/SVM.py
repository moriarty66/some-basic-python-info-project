import numpy as np
import cvxopt #用于求解线性规划
from process_data import load_and_process_data
from evaluation import get_micro_F1,get_macro_F1,get_acc


#根据指定类别main_class生成1/-1标签
def svm_label(labels,main_class):
    new_label=[]
    for i in range(len(labels)):
        if labels[i]==main_class:
            new_label.append(1)
        else:
            new_label.append(-1)
    return np.array(new_label)

# 实现线性回归
class SupportVectorMachine:

    '''参数初始化 
    lr: 梯度更新的学习率
    Lambda: L2范数的系数
    epochs: 更新迭代的次数
    '''
    def __init__(self,kernel,C,Epsilon):
        self.kernel=kernel
        self.C = C
        self.Epsilon=Epsilon

    '''KERNEL用于计算两个样本x1,x2的核函数'''
    def KERNEL(self, x1, x2, kernel='Poly', d=2, sigma=1):
        #d是多项式核的次数,sigma为Gauss核的参数
        K = 0
        if kernel == 'Gauss':
            K = np.exp(-(np.sum((x1 - x2) ** 2)) / (2 * sigma ** 2))
        elif kernel == 'Linear':
            K = np.dot(x1,x2)
        elif kernel == 'Poly':
            K = np.dot(x1,x2) ** d
        else:
            print('No support for this kernel')
        return K

    '''
    根据训练数据train_data,train_label（均为np数组）求解svm,并对test_data进行预测,返回预测分数，即svm使用符号函数sign之前的值
    train_data的shape=(train_num,train_dim),train_label的shape=(train_num,) train_num为训练数据的数目，train_dim为样本维度
    预测结果的数据类型应为np数组，shape=(test_num,1) test_num为测试数据的数目
    '''
    def fit(self,train_data,train_label,test_data):
        '''
        需要你实现的部分
        '''
        X = train_data
        y = train_label
        row, col = np.shape(X)
        K = np.zeros((row, row))

        for i in range(row):
            for j in range(row):
                K[i,j] = self.KERNEL(X[i], X[j])
        P = cvxopt.matrix(np.outer(y, y) * K)
        q = cvxopt.matrix(np.ones(row) * -1)
        A = cvxopt.matrix(np.ones(row) * y, (1, row))
        b = cvxopt.matrix(0.0)

        tmp1 = np.diag(np.ones(row) * -1)
        tmp2 = np.diag(np.ones(row))
        G = cvxopt.matrix(np.vstack((tmp1, tmp2)))
        tmp1 = np.zeros(row)
        tmp2 = np.ones(row) * self.C
        h = cvxopt.matrix(np.hstack((tmp1, tmp2)))


        solution = cvxopt.solvers.qp(P, q, G, h, A, b)
        a = np.ravel(solution['x'])

        sv = a > self.Epsilon
        index = np.arange(len(a))[sv]

        self.a = a[sv]
        self.sv_x = X[sv]  # sv's data
        self.sv_y = y[sv]  # sv's labels

        if self.kernel == 'Linear':
            self.w = np.zeros(col)
            for i in range(len(self.a)):
                self.w += self.a[i] * self.sv_y[i] * self.sv_x[i]
        else:
            self.w = None

        self.b = 0
        for n in range(len(self.a)):
            self.b += self.sv_y[n]
            self.b -= np.sum(self.a * self.sv_y * K[index[n]][index])
        self.b /= len(self.a)

        if self.kernel == 'Linear':
            ak = np.dot(test_data, self.w) + self.b
            ak = ak.reshape(-1, 1)
            return ak
        else:
            predict = np.zeros(len(test_data))
            for i in range(len(test_data)):
                s = 0
                for a, sv_y, sv_ in zip(self.a, self.sv_y, self.sv_x):
                    s += a * sv_y * self.KERNEL(test_data[i], sv_)
                predict[i] = s
            return np.array(predict + self.b).reshape(-1, 1)


def main():
    # 加载训练集和测试集
    Train_data,Train_label,Test_data,Test_label=load_and_process_data()
    Train_label=[label[0] for label in Train_label]
    Test_label=[label[0] for label in Test_label]
    train_data=np.array(Train_data)
    test_data=np.array(Test_data)
    test_label=np.array(Test_label).reshape(-1,1)
    #类别个数
    num_class=len(set(Train_label))


    #kernel为核函数类型，可能的类型有'Linear'/'Poly'/'Gauss'
    #C为软间隔参数；
    #Epsilon为拉格朗日乘子阈值，低于此阈值时将该乘子设置为0
    kernel='Poly'
    C = 1
    Epsilon=10e-5
    #生成SVM分类器
    SVM=SupportVectorMachine(kernel,C,Epsilon)

    predictions = []
    #one-vs-all方法训练num_class个二分类器
    for k in range(1,num_class+1):
        #将第k类样本label置为1，其余类别置为-1
        train_label=svm_label(Train_label,k)
        # 训练模型，并得到测试集上的预测结果
        prediction=SVM.fit(train_data,train_label,test_data)
        predictions.append(prediction)
    predictions=np.array(predictions)
    #one-vs-all, 最终分类结果选择最大score对应的类别
    pred=np.argmax(predictions,axis=0)+1
    print(pred)
    # 计算准确率Acc及多分类的F1-score
    print("Acc: "+str(get_acc(test_label,pred)))
    print("macro-F1: "+str(get_macro_F1(test_label,pred)))
    print("micro-F1: "+str(get_micro_F1(test_label,pred)))


main()
