from pyparsing import nums
from collections import defaultdict
import ReadInfo
import math

import matplotlib.pyplot as plt


def to_date(time):
    hours = time // 3600
    remainder = time % 3600
    minutes = remainder // 60
    seconds = remainder % 60
    time_str = "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)
    datetime = "2024/1/1 " + time_str
    if (hours == 24):
        datetime = "2024/1/2 00:00:00"
    return datetime


def merge_datetime(categories):
    """
    :param categories: 以目标为键，卫星序号和时间为值的类
    :return: 输出10个文件，包含了23个目标在十个卫星下的可见时间窗口和二重时间窗口
    """
    folder = 'output'
    file_index = 1
    file_handle = open(folder + '\\' + f'output_{file_index}.txt', 'w', encoding='utf-8')
    # sat_interval = [[0 for _ in range(23)] for _ in range(9)]  # size->10*23
    # interval = []
    # datetime_interval = []
    forpaint = []

    target_num_interval = {}
    target_num_interval = defaultdict(list)
    j = 0

    for target, groups in categories.items():
        num_intervals = []  # 还未转化成日期的有效观测时间（循环内对每个目标有效）
        file_handle.write(f"Target: {target}\n")
        times = {key: [] for key in range(1, 10)}  # 为字典类型，键为卫星序号，值为覆盖时间列表
        for group in groups:
            times[group.satellite_num].append(group.time)
        # 进行区间合并
        for i in range(1, 10):
            file_handle.write("%d号卫星\n" % i)
            if times[i]:
                intervals = merge_time(times[i])
                num_intervals.append(intervals)
                for interval in intervals:
                    datetime_start = to_date(interval[0])
                    datetime_end = to_date(interval[1])
                    # datetime_interval.append((datetime_start, datetime_end))
                    sum = interval[1] - interval[0]
                    forpaint.append((target, sum, interval[0]))
                    target_num_interval[target].append((interval[0], interval[1]))
                    file_handle.write(f"Valid Time: {(datetime_start, datetime_end)},   Sum:{sum}\n")
                file_handle.write(f"\n")

        j += 1

        # 对单个目标不同卫星观测时间求交集（二重覆盖时间）
        file_handle.write(f"Target: {target}\n")
        intersection_interval = intersection_intervals(num_intervals)

        for interval in intersection_interval:
            if interval:
                for time in interval:
                    time_start = to_date(time[0])
                    time_end = to_date(time[1])
                    res_sum = time[1] - time[0]
                    file_handle.write(f"Time: {(time_start, time_end)},   Sum:{res_sum}\n")
        file_handle.write("\n")

        # 更换新的生成文件
        file_handle.close()
        file_index += 1
        if file_index < 25:
            file_handle = open(folder + '\\' + f'output_{file_index}.txt', 'w', encoding='utf-8')
    # print(sat_interval)
    calc_time_intervals(target_num_interval, folder)
    paint(forpaint)
    file_handle.close()


def calc_time_intervals(target_num_interval, folder):
    """
    :param target_num_interval:  目标点的所有时间窗口
    :return: 时间间隙
    """
    file_index = 1
    # 求并集，求补集
    result = {}
    result = defaultdict(list)
    for target in target_num_interval.keys():
        file_handle = open(folder + '\\' + f'output_{file_index}.txt', 'a', encoding='utf-8')
        target_num_interval[target] = sorted(target_num_interval[target], key=lambda x: x[0])
        for interval in target_num_interval[target]:
            # result中最后一个区间的右值>=新区间的左值，说明两个区间有重叠
            if result[target] and result[target][-1][1] >= interval[0]:
                # 将result中最后一个区间更新为合并之后的新区间
                new_end = max(result[target][-1][1], interval[1])
                s, e = result[target].pop()
                result[target].append((s, new_end))  # 合并
            else:
                result[target].append(interval)

        end1 = 0
        start2 = 0
        end2 = 86400
        i = 0
        j = 0
        bu_result = []
        for new_interval in result[target]:
            start1, end1 = new_interval
            if start1 > start2:
                if start2 == 0:
                    bu_result.append((start2, start1 - 1))
                else:
                    bu_result.append((start2 + 1, start1 - 1))
                start2 = end1
        if end1 + 1 < end2:
            bu_result.append((end1 + 1, end2))
        max_interval = 0
        max_intervals = (0, 0)
        accum_sum = 0
        for interval in bu_result:
            start, end = interval
            sum = end - start
            accum_sum += sum
            start = to_date(start)
            end = to_date(end)
            if sum > max_interval:
                max_interval = sum
                max_intervals = (start, end)
            file_handle.write(f"Interval: {(start, end)}\n")
        file_handle.write(
            f"最大时间空隙为:{max_intervals}，最大时间空隙大小为：{max_interval}，平均时间空隙大小为:{accum_sum / len(bu_result)}")
        file_index += 1


def merge_time(times):
    """
    :param times: 一个卫星对一个目标的可见时间
    :return: 可见时间窗口
    """
    merge = []
    start = times[0]
    start1 = 0
    end = start
    for time in times[1:]:
        if time == end + 1:
            end = time
        else:
            if start == end:
                continue
            merge.append((start, end))
            start = time
            end = time
    if start != end:
        merge.append((start, end))
    return merge


def intersection_intervals(intervals):
    """
    :param intervals: 一个目标对应所有卫星星座的有效观测时间
    :return: 二重覆盖时间间隔
    """
    intersections = []
    for j in range(len(intervals)):
        for i in range(j + 1, len(intervals)):
            intersection_interval = smaller_intersection_interval(intervals[i], intervals[j])
            if intersection_interval:
                intersections.append(intersection_interval)
    return intersections


def smaller_intersection_interval(intervals_A, intervals_B):
    """
    :param intervals_A: 卫星A对目标的时间窗口
    :param intervals_B: 卫星B对目标的时间窗口
    :return: 二重覆盖时间窗口
    """
    if not intervals_A or not intervals_B:
        return None
    # 升序排序，起始时间相同时结束时间小的在前
    intervals_A.sort(key=lambda x: (x[0], -x[1]))
    intervals_B.sort(key=lambda x: (x[0], -x[1]))
    res = []
    i = 0
    j = 0
    while i < len(intervals_A) and j < len(intervals_B):
        a1, a2 = intervals_A[i][0], intervals_A[i][1]
        b1, b2 = intervals_B[j][0], intervals_B[j][1]
        if b2 >= a1 and a2 >= b1:
            res.append([max(a1, b1), min(a2, b2)])
        if b2 < a2:
            j += 1
        else:
            i += 1
    return res


class Valid:
    def __init__(self, time, satellite_num, target):
        self.time = time
        self.satellite_num = satellite_num
        self.target = target

    def __str__(self):
        return f"Satellite: {self.satellite_num}, Time: {self.time}, target: {self.target}"


def valid_timewindow():
    """
    :return: 未合并的有效时间窗口
    """
    # valids = []
    # 对每个目标，每个卫星
    categories = defaultdict(list)
    for target in target_list:
        categories[target.name] = []
        target_x, target_y, target_z = ReadInfo.global_lonlat_topos(target.latitude, target.longitude)

        for i, satellite in enumerate(satellite_list):
            distance = math.sqrt((target_x - satellite.center_x) ** 2 + (target_y - satellite.center_y) ** 2
                                 + (target_z - satellite.center_z) ** 2)
            # print(distance)

            if distance <= satellite.radius:
                valid = Valid(satellite.time, i // 86401 + 1, target.name)
                categories[target.name].append(valid)
                # valids.append(valid)
                # print(valid)

    # for valid in valids:
    # categories[valid.target].append(valid)
    merge_datetime(categories)


def paint(forpaint):
    plt.rcParams.update({"font.size": 25})  # 此处必须添加此句代码方可改变标题字体大小
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 替换sans-serif字体
    plt.rcParams['axes.unicode_minus'] = False  # 解决坐标轴负数的负号显示问题
    plt.figure(figsize=(36, 12))
    plt.xticks([10800, 21600, 32400, 43200, 54000, 64800, 75600, 86400],
               ["3:00", "6:00", "9:00", "12:00", "15:00", "18:00", "21:00", "24:00"])
    for data in forpaint:
        plt.barh(data[0], data[1], left=data[2])
    plt.title("TimeWindow")
    plt.show()


if __name__ == "__main__":
    target_list = ReadInfo.read_target_file('D:\\Data\\target.txt')
    satellite_list = ReadInfo.read_satellite_file()
    valid_timewindow()
