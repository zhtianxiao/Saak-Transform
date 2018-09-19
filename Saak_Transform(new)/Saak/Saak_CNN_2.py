
import numpy as np
import cPickle
import gzip
from sklearn.decomposition import PCA
from skimage.util.shape import view_as_windows
from time import time
from sklearn import svm
from sklearn.feature_selection import f_classif


def Unsign(train_data):
    filternum = (train_data.shape[3] - 1) / 2
    ta1 = np.concatenate((train_data[:, :, :, :1], train_data[:, :, :, 1:filternum + 1] - train_data[:, :, :, filternum + 1:]), axis=3)
    return ta1.reshape(ta1.shape[0], -1)


def evac_ftest(rep2, label):
    F, p = f_classif(rep2, label)
    low_conf = p > 0.05
    F[low_conf] = 0
    where_are_NaNs = np.isnan(F)
    F[where_are_NaNs] = 0
    return F


def window_process_convolution(train, size):
    train_shape = train.shape
    # test_shape = test.shape

    train_cnt = train_shape[0]
    w, h, d = train_shape[1], train_shape[2], train_shape[3]

    train_window = view_as_windows(train, (1, size, size, d), step=(1, 1, 1, d)).reshape(train_cnt * (w - (size - 1)) * (h - (size - 1)), -1)
    # test_window = view_as_windows(test, (1, size, size, d), step=(1, 1, 1, d)).reshape(test_cnt * (w - (size - 1)) * (h - (size - 1)), -1)
    print("train_window.shape: {}".format(train_window.shape))
    # print("test_window.shape: {}".format(test_window.shape))

    return train_window


def window_process_max_pooling(train, size):
    train_shape = train.shape
    # test_shape = test.shape

    train_cnt = train_shape[0]
    w, h, d = train_shape[1], train_shape[2], train_shape[3]

    train_window = view_as_windows(train, (1, size, size, d), step=(1, size, size, d)).reshape(train_cnt * w / size * h / size, -1)
    # test_window = view_as_windows(test, (1, size, size, d), step=(1, size, size, d)).reshape(test_cnt * w / size * h / size, -1)
    print("train_window.shape: {}".format(train_window.shape))
    # print("test_window.shape: {}".format(test_window.shape))

    return train_window


def convolution(train, components, size):
    # generate sample data and label, change 60000 -> other number (number of images to learn PCA)

    train_shape = train.shape
    # test_shape = test.shape
    train_cnt = train_shape[0]
    w, h, d = train_shape[1], train_shape[2], train_shape[3]
    # use sample to do the DC, AC substraction
    train_window = window_process_convolution(train, size)
    # pca training

    d = train_window.shape[-1]

    train_dc = (np.mean(train_window, axis=1) * (d**0.5)).reshape(-1, 1).reshape(train_cnt, (w - (size - 1)), (h - (size - 1)), 1)
    # test_dc = (np.mean(test_window, axis=1) * (d**0.5)).reshape(-1, 1).reshape(test_cnt, (w - (size - 1)), (h - (size - 1)), 1)

    mean = np.mean(train_window, axis=1).reshape(-1, 1)
    print("mean.shape: {}".format(mean.shape))
    # PCA weight training

    pca = PCA(n_components=components, svd_solver='full')
    pca.fit(train_window - mean)

    train = pca.transform(train_window - mean).reshape(train_cnt, w - (size - 1), h - (size - 1), -1)
    print("train.shape: {}".format(train.shape))
    # mean = np.mean(test_window, axis=1).reshape(-1, 1)
    # print("mean.shape: {}".format(mean.shape))
    # test = pca.transform(test_window - mean).reshape(test_cnt, w - (size - 1), h - (size - 1), -1)
    # print("test.shape: {}".format(test.shape))

    shape = train.shape
    w, h, d = shape[1], shape[2], shape[3]

    train_data = np.zeros((train_cnt, w, h, 1 + d * 2))
    # test_data = np.zeros((test_cnt, w, h, 1 + d * 2))

    train_data[:, :, :, :1] = train_dc[:, :, :, :]
    # test_data[:, :, :, :1] = test_dc[:, :, :, :]
    train_data[:, :, :, 1:1 + d] = train[:, :, :, :].copy()
    train_data[:, :, :, 1 + d:] = -train[:, :, :, :].copy()
    # test_data[:, :, :, 1:1 + d] = test[:, :, :, :].copy()
    # test_data[:, :, :, 1 + d:] = -test[:, :, :, :].copy()
    train_data[train_data < 0] = 0
    # test_data[test_data < 0] = 0

    return train_data


def max_pooling(train, components, size):
    # generate sample data and label, change 60000 -> other number (number of images to learn PCA)

    train_shape = train.shape
    # test_shape = test.shape
    train_cnt = train_shape[0]
    w, h, d = train_shape[1], train_shape[2], train_shape[3]
    # use sample to do the DC, AC substraction
    train_window = window_process_max_pooling(train, size)
    # pca training

    d = train_window.shape[-1]

    train_dc = (np.mean(train_window, axis=1) * (d**0.5)).reshape(-1, 1).reshape(train_cnt, w / size, h / size, 1)
    # test_dc = (np.mean(test_window, axis=1) * (d**0.5)).reshape(-1, 1).reshape(test_cnt, w / size, h / size, 1)

    mean = np.mean(train_window, axis=1).reshape(-1, 1)
    print("mean.shape: {}".format(mean.shape))
    # PCA weight training

    pca = PCA(n_components=components, svd_solver='full')
    pca.fit(train_window - mean)

    train = pca.transform(train_window - mean).reshape(train_cnt, w / size, h / size, -1)
    print("train.shape: {}".format(train.shape))
    # mean = np.mean(test_window, axis=1).reshape(-1, 1)
    # print("mean.shape: {}".format(mean.shape))
    # test = pca.transform(test_window - mean).reshape(test_cnt, w / size, h / size, -1)
    # print("test.shape: {}".format(test.shape))

    shape = train.shape
    w, h, d = shape[1], shape[2], shape[3]

    train_data = np.zeros((train_cnt, w, h, 1 + d * 2))
    # test_data = np.zeros((test_cnt, w, h, 1 + d * 2))

    train_data[:, :, :, :1] = train_dc[:, :, :, :]
    # test_data[:, :, :, :1] = test_dc[:, :, :, :]
    train_data[:, :, :, 1:1 + d] = train[:, :, :, :].copy()
    train_data[:, :, :, 1 + d:] = -train[:, :, :, :].copy()
    # test_data[:, :, :, 1:1 + d] = test[:, :, :, :].copy()
    # test_data[:, :, :, 1 + d:] = -test[:, :, :, :].copy()
    train_data[train_data < 0] = 0
    # test_data[test_data < 0] = 0

    return train_data


def main():

    start_time = time()
    f = gzip.open('./mnist.pkl.gz', 'rb')
    train_set, valid_set, test_set = cPickle.load(f)
    f.close()
    train = np.concatenate((train_set[0], valid_set[0]), 0)
    train_label = np.concatenate((train_set[1], valid_set[1]))
    test = test_set[0]
    test_label = test_set[1]

    train_cnt, test_cnt = train.shape[0], test.shape[0]
    train = train.reshape((train_cnt, 28, 28, 1))
    train = np.lib.pad(train, ((0, 0), (2, 2), (2, 2), (0, 0)), 'constant', constant_values=0)
    test = test.reshape((test_cnt, 28, 28, 1))
    test = np.lib.pad(test, ((0, 0), (2, 2), (2, 2), (0, 0)), 'constant', constant_values=0)

    print('start training')
    train = convolution(train, 3, 3)
    test = convolution(test, 3, 3)
    print("train.shape: {}".format(train.shape))
    print("test.shape: {}".format(test.shape))
    train_data = Unsign(train)
    test_data = Unsign(test)
    print("train_data.shape: {}".format(train_data.shape))
    print("test_data.shape: {}".format(test_data.shape))

    train = max_pooling(train, 1, 3)
    test = max_pooling(test, 1, 3)
    print("train.shape: {}".format(train.shape))
    print("test.shape: {}".format(test.shape))
    train_data = np.concatenate((train_data, Unsign(train)), 1)
    test_data = np.concatenate((test_data, Unsign(test)), 1)
    print("train_data.shape: {}".format(train_data.shape))
    print("test_data.shape: {}".format(test_data.shape))

    train = convolution(train, 3, 3)
    test = convolution(test, 3, 3)
    print("train.shape: {}".format(train.shape))
    print("test.shape: {}".format(test.shape))
    train_data = np.concatenate((train_data, Unsign(train)), 1)
    test_data = np.concatenate((test_data, Unsign(test)), 1)
    print("train_data.shape: {}".format(train_data.shape))
    print("test_data.shape: {}".format(test_data.shape))

    train = max_pooling(train, 4, 2)
    test = max_pooling(test, 4, 2)
    print("train.shape: {}".format(train.shape))
    print("test.shape: {}".format(test.shape))
    train_data = np.concatenate((train_data, Unsign(train)), 1)
    test_data = np.concatenate((test_data, Unsign(test)), 1)
    print("train_data.shape: {}".format(train_data.shape))
    print("test_data.shape: {}".format(test_data.shape))

    train = convolution(train, 6, 4)
    test = convolution(test, 6, 4)
    print("train.shape: {}".format(train.shape))
    print("test.shape: {}".format(test.shape))
    train_data = np.concatenate((train_data, Unsign(train)), 1)
    test_data = np.concatenate((test_data, Unsign(test)), 1)
    print("train_data.shape: {}".format(train_data.shape))
    print("test_data.shape: {}".format(test_data.shape))

    """
    @ F-test
    """
    Eva = evac_ftest(train_data, train_label)
    idx = Eva > np.sort(Eva)[::-1][int(np.count_nonzero(Eva) * 0.3) - 1]
    train_coefficients_f_test = train_data[:, idx]
    test_coefficients_f_test = test_data[:, idx]

    """
    @ PCA to 64
    """
    pca = PCA(svd_solver='full')
    pca.fit(train_coefficients_f_test)
    pca_k = pca.components_
    n_components = 64
    W = pca_k[:n_components, :]
    train_coefficients_pca = np.dot(train_coefficients_f_test, np.transpose(W))
    test_coefficients_pca = np.dot(test_coefficients_f_test, np.transpose(W))

    print ('Numpy training saak coefficients shape: {}'.format(train_data.shape))
    print ('Numpy training F-test coefficients shape: {}'.format(train_coefficients_f_test.shape))
    print ('Numpy training PCA coefficients shape: {}'.format(train_coefficients_pca.shape))
    print ('Numpy testing saak coefficients shape: {}'.format(test_data.shape))
    print ('Numpy testing F-test coefficients shape: {}'.format(test_coefficients_f_test.shape))
    print ('Numpy testing PCA coefficients shape: {}'.format(test_coefficients_pca.shape))

    """
    @ SVM classifier
    # """
    classifier = svm.SVC()
    classifier.fit(train_coefficients_pca, train_label)
    accuracy_train = classifier.score(train_coefficients_pca, train_label)
    accuracy_test = classifier.score(test_coefficients_pca, test_label)

    end_time = time()
    minutes, seconds = divmod(end_time - start_time, 60)
    time_total = {'minute': minutes, 'second': seconds}

    print ("The accuracy of training set is {:.4f}".format(accuracy_train))
    print ("The accuracy of testing set is {:.4f}".format(accuracy_test))
    print ('The total time for classification: %(minute)d minute(s) %(second)d second(s)' % time_total)
    print ('')


if __name__ == "__main__":
    main()
