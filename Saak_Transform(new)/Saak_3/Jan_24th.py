
import numpy as np
from sklearn.decomposition import PCA
from skimage.util.shape import view_as_windows
import cPickle
import gzip
from time import time
version = 0


def print_shape(train, test):
    print "train's shape is %s" % str(train.shape)
    print "test's shape is %s" % str(test.shape)


def patch_filter(sample, sample_label, patch_threshold=10000):
    print("sample.shape: {}".format(sample.shape))
    sample_var = np.std(sample, axis=1)
    print("sample_var.shape: {}".format(sample_var.shape))
    max_std = np.max(sample_var)
    print np.max(sample_var)
    sample_filter = sample[sample_var > max_std / patch_threshold]
    sample_label = sample_label[sample_var > max_std / patch_threshold]
    return sample_filter, sample_label


def window_process(train, test, train_label, test_label):
    train_shape = train.shape
    test_shape = test.shape
    print("train_shape: {}".format(train_shape))
    print("test_shape: {}".format(test_shape))

    train_cnt, test_cnt = train_shape[0], test_shape[0]
    w, h, d = train_shape[1], train_shape[2], train_shape[3]

    train_label = np.repeat(train_label, w / 2 * h / 2)
    test_label = np.repeat(test_label, w / 2 * h / 2)
    print("train_labels.shape: {}".format(train_label.shape))
    print("test_labels.shape: {}".format(test_label.shape))

    train_window = view_as_windows(train, (1, 2, 2, d), step=(1, 2, 2, d)).reshape(train_cnt * w / 2 * h / 2, -1)
    test_window = view_as_windows(test, (1, 2, 2, d), step=(1, 2, 2, d)).reshape(test_cnt * w / 2 * h / 2, -1)
    print("train_window: {}".format(train_window.shape))
    print("test_window: {}".format(test_window.shape))

    return train_window, test_window, train_label, test_label


def convolution(train, test, train_label, test_label, stage):
    train_shape = train.shape
    test_shape = test.shape
    train_cnt, test_cnt = train_shape[0], test_shape[0]
    print('train count: {}'.format(train_cnt))
    print('test count: {}'.format(test_cnt))
    w, h, d = train_shape[1], train_shape[2], train_shape[3]
    # use sample to do the DC, AC substraction
    train_window, test_window, train_label, test_label = window_process(train, test, train_label, test_label)
    train_filter, train_label = patch_filter(train_window, train_label)
    # pca training

    d = train_window.shape[-1]
    train_dc = (np.mean(train_window, axis=1) * (d**0.5)).reshape(-1, 1).reshape(train_cnt, w / 2, h / 2, 1)
    test_dc = (np.mean(test_window, axis=1) * (d**0.5)).reshape(-1, 1).reshape(test_cnt, w / 2, h / 2, 1)
    print("train_dc.shape: {}".format(train_dc.shape))
    print("test_dc.shape: {}".format(test_dc.shape))

    mean = np.mean(train_window, axis=1).reshape(-1, 1)
    print("mean.shape: {}".format(mean.shape))

    # PCA weight training
    pca = PCA(n_components=d, svd_solver='full')
    pca.fit(train_window - mean)
    # print("pca.explained_variance_ratio_: ", pca.explained_variance_ratio_[:50])
    # if stage == 1:
    #     f_num = d - 1
    # else:
    #     Energy = np.cumsum(pca.explained_variance_ratio_)
    #     # f_num = np.count_nonzero(Energy < 0.995)
    #     idx = pca.explained_variance_ratio_ > 0.03
    #     f_num = np.count_nonzero(idx)
    #     print f_num, Energy[f_num]
    components_pca = [3, 4, 7, 6, 8]
    f_num = components_pca[stage - 1]
    train = pca.transform(train_window - mean)
    print(train.shape)
    train = train[:, :f_num].reshape(train_cnt, w / 2, h / 2, -1)
    print(train.shape)
    mean = np.mean(test_window, axis=1).reshape(-1, 1)
    print(mean.shape)
    test = pca.transform(test_window - mean)
    print(test.shape)
    test = test[:, :f_num].reshape(test_cnt, w / 2, h / 2, -1)
    print(test.shape)

    shape = train.shape
    w, h, d = shape[1], shape[2], shape[3]

    train_data = np.zeros((train_cnt, w, h, 1 + d * 2))
    test_data = np.zeros((test_cnt, w, h, 1 + d * 2))

    train_data[:, :, :, :1] = train_dc[:, :, :, :]
    test_data[:, :, :, :1] = test_dc[:, :, :, :]
    train_data[:, :, :, 1:d + 1] = train[:, :, :, :].copy()
    train_data[:, :, :, d + 1:] = -train[:, :, :, :].copy()
    test_data[:, :, :, 1:d + 1] = test[:, :, :, :].copy()
    test_data[:, :, :, d + 1:] = -test[:, :, :, :].copy()
    train_data[train_data < 0] = 0
    test_data[test_data < 0] = 0

    return train_data, test_data


def main():

    start_time = time()
    f = gzip.open('./mnist.pkl.gz', 'rb')
    train_set, valid_set, test_set = cPickle.load(f)
    f.close()

    train_all = np.concatenate((train_set[0], valid_set[0]), 0)
    train_label_all = np.concatenate((train_set[1], valid_set[1]))
    test_all = test_set[0]
    test_label = test_set[1]

    train = train_all  # [train_label_all == class_id]
    test = test_all
    train_label = train_label_all  # [train_label_all == class_id]

    train_cnt, test_cnt = train.shape[0], test.shape[0]
    print train_cnt, test_cnt
    train = train.reshape((train_cnt, 28, 28, 1))
    train = np.lib.pad(train, ((0, 0), (2, 2), (2, 2), (0, 0)), 'constant', constant_values=0)
    test = test.reshape((test_cnt, 28, 28, 1))
    test = np.lib.pad(test, ((0, 0), (2, 2), (2, 2), (0, 0)), 'constant', constant_values=0)
    # train_data = np.zeros((train_cnt, 0))
    # test_data = np.zeros((test_cnt, 0))

    print('start training')
    stages = ['first', 'second', 'third', 'fourth', 'fifth']
    test_1 = test[0]
    for k in range(5):
        print("The {} stage: ".format(stages[k]))
        train, test_1 = convolution(train, test_1, train_label, test_label, k + 1)
        print_shape(train, test)
        # save features of each stage (augmented features, when do classfication, you need to converge)
        np.save('./feature/train_before_f_test' + '_' + str(k + 1) + '_v' + str(version) + '.npy', train)
        np.save('./feature/test_before_f_test' + '_' + str(k + 1) + '_v' + str(version) + '.npy', test)

    end_time = time()
    minutes, seconds = divmod(end_time - start_time, 60)
    time_total = {'minute': minutes, 'second': seconds}
    print ('The total time for generating Saak coefficients: %(minute)d minute(s) %(second)d second(s)' % time_total)


if __name__ == "__main__":
    main()