from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

li = load_iris()

# print('特征值', li.data)
# print('目标值', li.target)

x_train, x_test, y_train, y_test = train_test_split(li.data,
                                                    li.target,
                                                    test_size=0.25)
print('训练集特征值和目标值', x_train, y_train)
print('测试集特征值和目标值', x_test, y_test)

