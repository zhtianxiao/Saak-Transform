import numpy as np
import cPickle
import gzip
from time import time
from sklearn import svm
from sklearn.feature_selection import f_classif
from sklearn.feature_selection import SelectPercentile
from sklearn.decomposition import PCA
from skimage.util.shape import view_as_windows
from scipy.stats import entropy


def Unsign(train_data):
    filternum = (train_data.shape[3] - 1) / 2
    ta1 = np.concatenate((train_data[:, :, :, :1], train_data[:, :, :, 1:filternum + 1] - train_data[:, :, :, filternum + 1:]), axis=3)
    return ta1.reshape(ta1.shape[0], -1)


def window_process_2(train, test):
    train_shape = train.shape
    test_shape = test.shape
    print("train_shape: {}".format(train_shape))
    print("test_shape: {}".format(test_shape))

    train_cnt, test_cnt = train_shape[0], test_shape[0]
    w, h, d = train_shape[1], train_shape[2], train_shape[3]

    train_window = view_as_windows(train, (1, 2, 2, d), step=(1, 2, 2, d)).reshape(train_cnt * w / 2 * h / 2, -1)
    test_window = view_as_windows(test, (1, 2, 2, d), step=(1, 2, 2, d)).reshape(test_cnt * w / 2 * h / 2, -1)
    print("train_window: {}".format(train_window.shape))
    print("test_window: {}".format(test_window.shape))

    return train_window, test_window


def convolution_2(train, test, stage):
    train_shape = train.shape
    test_shape = test.shape
    train_cnt, test_cnt = train_shape[0], test_shape[0]
    print('train count: {}'.format(train_cnt))
    print('test count: {}'.format(test_cnt))
    w, h, d = train_shape[1], train_shape[2], train_shape[3]
    # use sample to do the DC, AC substraction
    train_window, test_window = window_process_2(train, test)
    # train_filter, train_label = patch_filter(train_window, train_label)
    # pca training

    d = train_window.shape[-1]
    train_dc = (np.mean(train_window, axis=1) * (d**0.5)).reshape(-1, 1).reshape(train_cnt, w / 2, h / 2, 1)
    test_dc = (np.mean(test_window, axis=1) * (d**0.5)).reshape(-1, 1).reshape(test_cnt, w / 2, h / 2, 1)
    print("train_dc.shape: {}".format(train_dc.shape))
    print("test_dc.shape: {}".format(test_dc.shape))

    mean = np.mean(train_window, axis=1).reshape(-1, 1)
    print("mean.shape: {}".format(mean.shape))

    # PCA weight training
    components_PCA = [3, 4, 7, 6, 8]
    f_num = components_PCA[stage - 1]
    pca = PCA(n_components=d, svd_solver='full', random_state=0)
    pca.fit(train_window - mean)
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

    return train_data, test_data, pca


def convolution_2_pca(train, test, stage, p_c_a):
    train_shape = train.shape
    test_shape = test.shape
    train_cnt, test_cnt = train_shape[0], test_shape[0]
    print('train count: {}'.format(train_cnt))
    print('test count: {}'.format(test_cnt))
    w, h, d = train_shape[1], train_shape[2], train_shape[3]
    # use sample to do the DC, AC substraction
    train_window, test_window = window_process_2(train, test)
    # train_filter, train_label = patch_filter(train_window, train_label)
    # pca training

    d = train_window.shape[-1]
    train_dc = (np.mean(train_window, axis=1) * (d**0.5)).reshape(-1, 1).reshape(train_cnt, w / 2, h / 2, 1)
    test_dc = (np.mean(test_window, axis=1) * (d**0.5)).reshape(-1, 1).reshape(test_cnt, w / 2, h / 2, 1)
    print("train_dc.shape: {}".format(train_dc.shape))
    print("test_dc.shape: {}".format(test_dc.shape))

    mean = np.mean(train_window, axis=1).reshape(-1, 1)
    print("mean.shape: {}".format(mean.shape))

    # PCA weight training
    components_PCA = [3, 4, 7, 6, 8]
    f_num = components_PCA[stage - 1]
    # pca = PCA(n_components=d, svd_solver='full', random_state=0)
    # pca.fit(train_window - mean)
    pca = p_c_a
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
    test_label = test_set[1]

    train_all = np.concatenate((train_set[0], valid_set[0]), 0)
    train_label_all = np.concatenate((train_set[1], valid_set[1]))
    test_all = test_set[0]

    test_probability = np.load('./test_classifier' + '.npy')
    print("test_probability.shape: {}".format(test_probability.shape))
    test_probability = list(test_probability)
    accuracy_test = 0
    clf = []
    confusion_labels = []
    pca = []
    index_test = []
    index = []
    count = 0
    count_test = 0
    correct = 0
    wrong = 0
    right = 0
    test_7_9 = []
    retest = []
    for i in range(10000):
        print(i)
        test_list = test_probability[i]
        max_1 = -(np.sort(-test_list)[0])
        max_2 = -(np.sort(-test_list)[1])
        max_index_1 = np.argsort(-test_list)[0]
        max_index_2 = np.argsort(-test_list)[1]

        if max_1 / max_2 > 10:
            accuracy_test += max_index_1 == test_label[i]

        else:
            right += max_index_1 == test_label[i]
            count += 1
            retest.append(i)
            # element = [min(max_index_1, max_index_2), max(max_index_1, max_index_2)]
            # test_1 = np.load("./coefficients/test" + str(max_index_1) + ".npy")
            # test_2 = np.load("./coefficients/test" + str(max_index_2) + ".npy")
            # if element not in confusion_labels:
            #     # score_1 = []
            #     # score_2 = []
            #     entropy_11 = []
            #     entropy_12 = []
            #     entropy_21 = []
            #     entropy_22 = []
            #     index_1 = []
            #     index_2 = []
            #     data_11 = np.load("./coefficients/train" + str(max_index_1) + str(max_index_1) + ".npy")
            #     data_12 = np.load("./coefficients/train" + str(max_index_1) + str(max_index_2) + ".npy")
            #     data_1 = np.vstack((data_11, data_12))
            #     bins = np.arange(np.amin(data_1), np.amax(data_1), 0.1)
            #     for m in range(data_11.shape[1]):
            #         hist_11, edges_11 = np.histogram(data_11[:, m], bins=bins, density=True)
            #         hist_12, edges_12 = np.histogram(data_12[:, m], bins=bins, density=True)
            #         entropy_11.append(entropy(hist_11))
            #         entropy_12.append(entropy(hist_12))
            #         # score_1.append(abs(entropy(hist_11) - entropy(hist_12)))
            #     # score_1 = np.array(score_1)
            #     entropy_11 = np.array(entropy_11)
            #     entropy_12 = np.array(entropy_12)
            #     rank_11 = np.argsort(entropy_11)[:200]
            #     rank_12 = np.argsort(entropy_12)[:200]
            #     for t in range(200):
            #         if rank_11[t] not in rank_12:
            #             index_1.append(rank_11[t])
            #     for t in range(200):
            #         if rank_12[t] not in rank_11:
            #             index_1.append(rank_12[t])
            #     index_1 = np.array(index_1)
            #     print(index_1.shape)
            #     # count_1 = sum(score_1 > 0)
            #     # print("count_1: {}".format(count_1))
            #     # index_1 = np.argsort(-score_1)[:count_1]
            #     data_1 = data_1[:, index_1]
            #     pca_1 = PCA(n_components=64)
            #     data_1 = pca_1.fit_transform(data_1)

            #     data_21 = np.load("./coefficients/train" + str(max_index_2) + str(max_index_1) + ".npy")
            #     data_22 = np.load("./coefficients/train" + str(max_index_2) + str(max_index_2) + ".npy")
            #     data_2 = np.vstack((data_21, data_22))
            #     bins = np.arange(np.amin(data_2), np.amax(data_2), 0.1)
            #     for m in range(data_21.shape[1]):
            #         hist_21, edges_21 = np.histogram(data_21[:, m], bins=bins, density=True)
            #         hist_22, edges_22 = np.histogram(data_22[:, m], bins=bins, density=True)
            #         entropy_21.append(entropy(hist_21))
            #         entropy_22.append(entropy(hist_22))
            #         # score_2.append(abs(entropy(hist_21) - entropy(hist_22)))
            #     # score_2 = np.array(score_2)
            #     entropy_21 = np.array(entropy_21)
            #     entropy_22 = np.array(entropy_22)
            #     rank_21 = np.argsort(entropy_21)[:200]
            #     rank_22 = np.argsort(entropy_22)[:200]
            #     for t in range(200):
            #         if rank_21[t] not in rank_22:
            #             index_2.append(rank_21[t])
            #     for t in range(200):
            #         if rank_22[t] not in rank_21:
            #             index_2.append(rank_22[t])
            #     index_2 = np.array(index_2)
            #     print(index_2.shape)
            #     # count_2 = sum(score_2 > 0)
            #     # print("count_2: {}".format(count_2))
            #     # index_2 = np.argsort(-score_2)[:count_2]
            #     data_2 = data_2[:, index_2]
            #     pca_2 = PCA(n_components=64)
            #     data_2 = pca_2.fit_transform(data_2)

            #     classifier_1 = svm.SVC(probability=True)
            #     classifier_2 = svm.SVC(probability=True)
            #     classifier_1.fit(data_1, np.concatenate((max_index_1 * np.ones(data_11.shape[0]), max_index_2 * np.ones(data_12.shape[0]))))
            #     classifier_2.fit(data_2, np.concatenate((max_index_1 * np.ones(data_21.shape[0]), max_index_2 * np.ones(data_22.shape[0]))))
            #     confusion_labels.append(element)
            #     clf.append([classifier_1, classifier_2])
            #     pca.append([pca_1, pca_2])
            #     index.append([index_1, index_2])
            # else:
            #     classifier_1 = clf[confusion_labels.index(element)][0]
            #     classifier_2 = clf[confusion_labels.index(element)][1]
            #     pca_1 = pca[confusion_labels.index(element)][0]
            #     pca_2 = pca[confusion_labels.index(element)][1]
            #     index_1 = index[confusion_labels.index(element)][0]
            #     index_2 = index[confusion_labels.index(element)][1]

            # test_pca_1 = test_1[i, index_1].reshape(1, -1)
            # test_pca_2 = test_2[i, index_2].reshape(1, -1)
            # test_pca_1 = pca_1.transform(test_pca_1)
            # test_pca_2 = pca_2.transform(test_pca_2)
            # test_list_1 = np.squeeze(classifier_1.predict_proba(test_pca_1))
            # test_list_2 = np.squeeze(classifier_2.predict_proba(test_pca_2))

            # if max(test_list_1) >= max(test_list_2):
            #     accuracy_test += classifier_1.predict(test_pca_1) == test_label[i]
            #     if classifier_1.predict(test_pca_1) == test_label[i] and max_index_1 != test_label[i]:
            #         correct += 1
            #     if classifier_1.predict(test_pca_1) != test_label[i] and max_index_1 == test_label[i]:
            #         wrong += 1

            # else:
            #     accuracy_test += classifier_2.predict(test_pca_2) == test_label[i]
            #     if classifier_2.predict(test_pca_2) == test_label[i] and max_index_1 != test_label[i]:
            #         correct += 1
            #     if classifier_2.predict(test_pca_2) != test_label[i] and max_index_1 == test_label[i]:
            #         wrong += 1

            # if max_index_1 > max_index_2:
            #     if test_list_1[1] >= test_list_2[0]:
            #         accuracy_test += max_index_1 == test_label[i]
            #     else:
            #         accuracy_test += max_index_2 == test_label[i]
            # else:
            #     if test_list_1[0] >= test_list_2[1]:
            #         accuracy_test += max_index_1 == test_label[i]
            #     else:
            #         accuracy_test += max_index_2 == test_label[i]
    np.save("retest.npy", retest)
    end_time = time()
    minutes, seconds = divmod(end_time - start_time, 60)
    time_total = {'minute': minutes, 'second': seconds}
    print("The number of SVM: {}".format(len(confusion_labels)))
    print("The number images which are needed to be retested: {}".format(count))
    print("The number of right images among retested images: {}".format(right))
    print("Original wrong but now correct: {}".format(correct))
    print("Original correct but now wrong: {}".format(wrong))
    print ("The accuracy of testing set is {}".format(accuracy_test))
    print ('The total time for classification: %(minute)d minute(s) %(second)d second(s)' % time_total)
    print ('')


if __name__ == "__main__":
    main()