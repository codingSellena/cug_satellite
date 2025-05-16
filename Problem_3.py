import os
from collections import defaultdict
from matplotlib import pyplot as plt
import ReadInfo
from ReadInfo import Satellite
import math
from Problem_1 import to_date

# Sat0~8观测完成后的任务间最小转换时长
transform_smallest_time = [30, 30, 30, 35, 35, 35, 25, 25, 25]


class Task:
    def __init__(self, name, lo, la, time, score):
        self.name = name
        self.lo = lo
        self.la = la
        self.x, self.y, self.z = self.lonla_topos()
        self.time = time
        self.score = score
        self.state = 0  # 0--未安排该任务，1--已安排该任务

    def lonla_topos(self):
        R = 6371
        # 将经纬度坐标转换到地球球面上的 xyz 坐标（其中，lon 为经度，lat 为纬度）
        lo, la = map(math.radians, [self.lo, self.la])
        self.x = R * math.cos(la) * math.cos(lo)
        self.y = R * math.cos(la) * math.sin(lo)
        self.z = R * math.sin(la)
        return self.x, self.y, self.z

    def __str__(self):
        return (f"Name: {self.name}, Latitude: {self.la},"
                f" Longitude: {self.lo}, Time: {self.time}, Score: {self.score}")


def read_target_info(target_info):
    directory_path = "D:\\Data\\TargetInfo\\"
    # target_info = {key: [] for key in range(1, 6)}
    i = 1
    for filename in os.listdir(directory_path):
        if os.path.isfile(os.path.join(directory_path, filename)) and filename.endswith(".txt"):
            file_path = os.path.join(directory_path, filename)
            with (open(file_path, 'r', encoding='utf-8') as f):
                for line in f:
                    parts = line.split()
                    if len(parts) == 5:
                        target_i = Task(parts[0], float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4]))
                        target_info[i].append(target_i)
                i += 1
    return target_info


def read_sat_info(sat_info):
    """
    :return: 卫星信息
    """
    directory_path = "D:\\Data\\Trace\\"
    # sat_info = {key: [] for key in range(1, 10)}
    i = 0
    for filename in os.listdir(directory_path):
        if os.path.isfile(os.path.join(directory_path, filename)):
            file_path = os.path.join(directory_path, filename)
            with (open(file_path, 'r', encoding='utf-8') as f):
                for line in f:
                    parts = line.split()
                    if len(parts) == 6 and (parts[0] == '1' or parts[0] == '2'):
                        hours, minute, sec = parts[3].split(":")
                        # if hours == "19" and sec == "01.000":
                        #     break
                        sec, millisecond = sec.split('.')
                        total_seconds = int(hours) * 3600 + int(minute) * 60 + int(sec)
                        x, y, z = ReadInfo.global_lonlat_topos(float(parts[4]), float(parts[5]))
                        sat_i = Satellite(latitude=float(parts[4]), longitude=float(parts[5]),
                                          center_x=x, center_y=y, center_z=z, num=i,
                                          sta=int(total_seconds), radius=777.18)
                        sat_info[i].append(sat_i)
        i += 1
    return sat_info


def valid_time_window(start, end, j, satellite_numbers):

    valid_target_per_time = {}
    valid_target_per_time = defaultdict(list)

    valid_target_time_i = {}
    valid_target_time_i = defaultdict(list)

    # 按收益降序排序
    sorted_targets = sorted(target_info[int(j)], reverse=True, key=lambda target: target.score / target.time)

    for i in satellite_numbers:
        valid_target_per_time.clear()
        for satellite in sat_info[int(i)]:
            if satellite.time < start:
                continue
            if satellite.time > end:
                break

            for target in sorted_targets:
                distance = math.sqrt((satellite.center_x - target.x) ** 2 + (satellite.center_y - target.y) ** 2
                                     + (satellite.center_z - target.z) ** 2)
                if distance < satellite.radius:
                    valid_target_per_time[target.name].append(satellite.time)
        for target in sorted_targets:
            if valid_target_per_time[target.name]:
                valid_target_time = merge_time(valid_target_per_time[target.name])
                valid_target_time_i[int(i)].append((target, valid_target_time))
    return valid_target_time_i


def merge_time(times):
    """
            :param times: 一个卫星对一个目标的可见时间
            :return: 可见时间窗口
            """
    merge = []
    start = times[0]
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


def check_busy(busy, task, valid_time, end, need):
    """
    :param busy: 已分配时间片
    :param task: 任务信息
    :param valid_time: 时间窗口
    :param end: 仿真结束时间
    :param need: 任务执行所需时间+卫星转换时长
    :return: 可分配任务执行时间段的开始时间
    """
    # 先求补集，再求交集
    valid_start = -1
    end1 = 0
    start2 = 0
    end2 = end
    i = 0
    j = 0
    bu_result = []
    busy = sorted(busy, key=lambda x: x[1][0])
    for task, busy_time in busy:
        start1, end1 = busy_time
        if start1 > start2:
            if start2 == 0:
                bu_result.append((start2, start1 - 1))
            else:
                bu_result.append((start2 + 1, start1 - 1))
            start2 = end1
    if end1 + 1 < end2:
        bu_result.append((end1 + 1, end2))

    for time in valid_time:
        # 无可用开始时间
        if time[1] - time[0] < task.time:
            continue
        if time[1] < time[0]:
            continue
        # 求busy和（0,86401）的补集,得到空闲时间片
        if not busy:
            valid_start = time[0]
            break
        else:
            busy = sorted(busy, key=lambda x: x[1])
        # 求空闲时间片和有效时间的交集，限制时间长度
        start2 = time[0]
        end2 = time[1]
        for free_time in bu_result:
            start1 = free_time[0]
            end1 = free_time[1]
            if start1 < start2 and end1 - start2 > need:
                valid_start = start2
                break
            elif start1 > start2:
                if end1 < end2 and end1 - start1 > need:
                    valid_start = start1
                    break
                elif end1 > end2 and end2 - start1 > need:
                    valid_start = start1
                    break

    return valid_start


def greedy_allocate_resource(end, valid_time_i, file_handle):
    """
    :param end: 仿真结束时间
    :param valid_time_i: 以卫星序号为键的时间窗口
    :return: 输出到文件和图片
    """
    forpaint = []
    profit = 0
    for key in valid_time_i:
        busy = []
        for task, valid_time in valid_time_i[key]:
            if task.state == 0:
                need = task.time + transform_smallest_time[key]
                valid_time_start = check_busy(busy, task, valid_time, end, need)  # 返回一个可行的任务调度开始时间
                if valid_time_start != -1:
                    profit += task.score
                    file_handle.write(
                        "任务：" + str(task.name) + "  任务时间：" + str(task.time) + "  收益值：" + str(
                            task.score) + "\n")
                    file_handle.write("分配卫星序号：" + str(key) +
                                      " 分配时间片：" + str((valid_time_start, valid_time_start + need)) + "\n")
                    file_handle.write("\n")
                    forpaint.append((task.name, need, valid_time_start))
                    print(profit)
                    # busy里是二元组（目标相关信息，（开始时间，结束时间））
                    busy.append(
                        (task, (valid_time_start, valid_time_start + need)))
                    print(task)
                    print(str(key) + str(
                        (valid_time_start, valid_time_start + need)))
                    task.state = 1
    file_handle.write("得分:" + str(profit))
    file_handle.close()
    return forpaint


def paint(forpaint, j):
    plt.rcParams.update({"font.size": 50})  # 此处必须添加此句代码方可改变标题字体大小
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 替换sans-serif字体
    plt.rcParams['axes.unicode_minus'] = False  # 解决坐标轴负数的负号显示问题
    plt.figure(figsize=(48, 24))
    for data in forpaint:
        plt.barh(data[0], data[1], left=data[2])
    # x_increment = 3600
    # plt.xticks(range(0, x_increment * 20, x_increment),
    #            ["0:00", "1:00", "2:00", "3:00", "4:00", "5:00", "6:00",
    #             "7:00", "8:00", "9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00",
    #             "16:00", "17:00", "18:00", "19:00"])
    plt.xlabel('time/ h')
    plt.ylabel('target ')

    plt.title("TimeWindow  " + str(j))
    plt.show()


# def genetic_algorithm():
#     # 初始化种群
#     # 计算适应度（得分高）
#     # 选择
#     # 杂交
#     # 突变
#     return 0
#
#
# def calc_fitness(individual):
#     profit = 0
#     for target in individual:
#         profit += target.score
#     return profit
#
#
# def select(pop):
#     fit = []
#     for individual in pop:
#         fitness = calc_fitness(individual)
#         fit.append((fitness, individual))
#     fit = sorted(fit, key=lambda x: x[0])
#     parent1 = fit[0]
#     parent2 = fit[1]
#
#
# # def crossover(parent1, parent2):
# #     for dna1 in parent1:
# #         for dna2 in parent2:
# #
# #     return individual


def date_to_num(datetime):
    hours, minutes, seconds = datetime.split(":")
    time = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    return time, hours


# 仿真时间
# 2024-01-01 11:00:00,2024-01-01 12:30:00  Sat0,6 target1
# 2024-01-01 00:00:00,2024-01-01 06:00:00  Sat0,1,2 target2
# 2024-01-01 11:00:00,2024-01-01 15:00:00  Sat0,1,3,4,5 target3
# 2024-01-01 16:00:00,2024-01-01 19:00:00  Sat3,4,5,6,7,8 target4
# 2024-01-01 00:00:00,2024-01-01 12:00:00  Sat0-8 target5

if __name__ == "__main__":
    start_str = input("请输入开始时间（格式：11:00:00）")
    end_str = input("请输入结束时间（格式：11:00:00）")
    start, start_hour = date_to_num(start_str)
    end, end_hour = date_to_num(end_str)
    j = input("请输入目标文件序号：")
    input_str = input("请输入卫星序号（用空格分隔）：")
    satellite_numbers = input_str.split()

    target_info = {key: [] for key in range(1, 6)}
    target_info = read_target_info(target_info)
    sat_info = {key: [] for key in range(0, 9)}
    sat_info = read_sat_info(sat_info)

    valid_target_i = defaultdict(list)
    valid_time_i = valid_time_window(start=start, end=end, j=j, satellite_numbers=satellite_numbers)
    folder = 'output'
    file_handle = open(folder + '\\' + f'simulate_with_target_{str(j)}.txt', 'w', encoding='utf-8')
    forpaint = greedy_allocate_resource(end, valid_time_i, file_handle)
    paint(forpaint, j)
