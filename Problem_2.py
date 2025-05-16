import math
from time import sleep
from matplotlib.ticker import MultipleLocator

from Problem_1 import to_date
import ReadInfo
from ReadInfo import Satellite
import os
import matplotlib.pyplot as plt
import tkinter as tk

per_rect_list = {key: [] for key in range(0, 86401)}
R = 6371


class Point:
    def __init__(self, lo, la):
        # self.la, self.lo = map(math.radians, [la, lo])
        self.la = la
        self.lo = lo
        self.x, self.y, self.z = ReadInfo.global_lonlat_topos(la, lo)
        # self.s = math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)  # 模长

    def __str__(self):
        return f"x:{self.x},y:{self.y},z:{self.z}"


class Rectangle:
    def __init__(self, left0, right0, left1, right1, area):
        """
        rectangle:{
                    [left0.right0],
                    [left1,right1]
                   }
        """
        self.left0 = left0
        self.left1 = left1
        self.right0 = right0
        self.right1 = right1
        self.color = None
        self.area = area
        self.state = 0
        # self.points = (self.left0, self.right0, self.left1, self.right1)

    def __str__(self):
        return f"left0: {self.left0}, left1: {self}, " \
               f"right0: {self.right0}, right1: {self.right1}, " f"面积: {self.area}"


# 将一个矩形变成四个矩形
def split_rectangle_area(rectangle_area):
    """
    :param rectangle_area: 要分割的矩形信息
    :return: 细化后的四个矩形信息
    """
    # sum_area=0
    lo1, lo2, la1, la2 = (rectangle_area.left0.lo, rectangle_area.right0.lo,
                          rectangle_area.left1.la, rectangle_area.left0.la)

    new_rectangle_point = []
    new_point_center = Point((rectangle_area.left0.lo + rectangle_area.right0.lo) / 2,
                             (rectangle_area.left0.la + rectangle_area.left1.la) / 2)
    new_point_01 = Point((rectangle_area.left0.lo + rectangle_area.right0.lo) / 2, rectangle_area.left0.la)
    new_point_02 = Point(rectangle_area.left0.lo, (rectangle_area.left0.la + rectangle_area.left1.la) / 2)
    new_point_13 = Point(rectangle_area.right0.lo, (rectangle_area.right0.la + rectangle_area.right1.la) / 2)
    new_point_23 = Point((rectangle_area.left1.lo + rectangle_area.right1.lo) / 2, rectangle_area.left1.la)

    # 从左往右，从上往下
    # 1
    area = calc_area(lo1, (lo1 + lo2) / 2, (la2 + la1) / 2, la2)
    new_rectangle_point.append(Rectangle(rectangle_area.left0, new_point_01, new_point_02,
                                         new_point_center, area))
    # 2

    area = calc_area((lo1 + lo2) / 2, lo2, (la2 + la1) / 2, la2)
    new_rectangle_point.append(Rectangle(new_point_01, rectangle_area.right0, new_point_center,
                                         new_point_13, area))
    # 3

    area = calc_area(lo1, (lo1 + lo2) / 2,la1, (la2 + la1) / 2)
    new_rectangle_point.append(Rectangle(new_point_02, new_point_center, rectangle_area.left1,
                                         new_point_23, area))
    # 4
    area = calc_area((lo1 + lo2)/2, lo2,la1, (la2 + la1) / 2)
    new_rectangle_point.append(Rectangle(new_point_center, new_point_13, new_point_23,
                                         rectangle_area.right1, area))

    # 返回包含了四个矩形信息的列表
    return new_rectangle_point


def calc_area(lo1, lo2, la1, la2):
    """
    :param lo1, lo2, la1, la2:从小到大、从经度到纬度
    :return: 矩形面积
    """
    lo1, lo2, la1, la2 = map(math.radians,
                             [lo1, lo2, la1, la2])
    return R * R * (math.cos(la1) - math.cos(la2)) * (lo2 - lo1)


def cal_coverage_rate(satellites, rectangle_area, queue):
    """
    :param satellites: 九个卫星圆信息
    :param rectangle_area: 总矩形信息
    :param queue: 矩形队列
    :return:
    """
    # 检查一个矩形的四个点是否都在观测范围内
    valid_rect = []
    # stack = []
    new_queue = []
    coverage_rate = 0

    area0 = rectangle_area.area * 0.001
    accum_yellow = rectangle_area.area
    for m in range(0, len(queue)):
        rectangle = queue[m]
        # 是，填充为绿色，否则调用split函数分割矩形再入栈
        i = 0
        for satellite in satellites:
            j = check_points_valid(rectangle, satellite)
            if j > i:
                i = j
            if i == 4:
                break
        # if rectangle.color is None or rectangle.color == 'yellow':
        if i == 4:
            temp = Rectangle(rectangle.left0, rectangle.right0, rectangle.left1, rectangle.right1, rectangle.area)
            accum_yellow -= rectangle.area
            coverage_rate += rectangle.area
            temp.color = 'green'
            rectangle.state = 1
            valid_rect.append(temp)
        elif i == 0:
            temp = Rectangle(rectangle.left0, rectangle.right0, rectangle.left1, rectangle.right1, rectangle.area)
            accum_yellow -= rectangle.area
            temp.color = 'red'
            valid_rect.append(temp)
        else:
            temp = Rectangle(rectangle.left0, rectangle.right0, rectangle.left1, rectangle.right1, rectangle.area)
            # 不确定的网格面积之和与总面积之比小于0.1%
            temp.color = 'yellow'
            valid_rect.append(temp)
            new_queue.append(temp)
        m += 1

    while new_queue:
        if accum_yellow < area0:
            break
        i = 0
        rect = new_queue[0]
        new_queue.remove(rect)
        for satellite in satellites:
            j = check_points_valid(rect, satellite)
            if j > i:
                i = j
            if i == 4:
                break
        if i == 4:
            accum_yellow -= rect.area
            coverage_rate += rect.area
            rect.color = 'green'
            valid_rect.append(rect)
        elif i == 0:
            accum_yellow -= rect.area
            rect.color = 'red'
            valid_rect.append(rect)
        else:
            # 不确定的网格面积之和与总面积之比小于0.1%
            rect.color = 'yellow'
            valid_rect.append(rect)
            if rect.area < 0.5 * area0:
                continue
            if rect and accum_yellow > area0:  # accum_yellow>area0
                new_rectangle = split_rectangle_area(rect)
                new_queue.append(new_rectangle[0])
                new_queue.append(new_rectangle[1])
                new_queue.append(new_rectangle[2])
                new_queue.append(new_rectangle[3])
            else:
                break

    if coverage_rate:
        coverage_rate /= rectangle_area.area
        coverage_rate *= 100  # 百分率
        print(str(satellites[1].time) + " " + str(coverage_rate))
        return satellites[1].time, coverage_rate, valid_rect
    else:
        return satellites[1].time, 0, valid_rect


def check_points_valid(rectangle, satellite):
    """
    :param rectangle: 矩形信息
    :param satellite: 卫星圆信息
    :return: 覆盖点个数
    """
    i = 0
    if (cal_distance(rectangle.left0.lo, rectangle.left0.la,
                     satellite.longitude, satellite.latitude)
            <= satellite.radius):
        i += 1
    if (cal_distance(rectangle.left1.lo, rectangle.left1.la,
                     satellite.longitude, satellite.latitude)
            <= satellite.radius):
        i += 1
    if (cal_distance(rectangle.right0.lo, rectangle.right0.la,
                     satellite.longitude, satellite.latitude)
            <= satellite.radius):
        i += 1
    if (cal_distance(rectangle.right1.lo, rectangle.right1.la,
                     satellite.longitude, satellite.latitude)
            <= satellite.radius):
        i += 1
    return i


def cal_distance(lo1, la1, lo2, la2):
    x1, y1, z1 = ReadInfo.global_lonlat_topos(la1, lo1)
    x2, y2, z2 = ReadInfo.global_lonlat_topos(la2, lo2)
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2)


def read_sat_info():
    directory_path = "D:\\Data\\SatelliteInfo"
    satellite_list = {key: [] for key in range(0, 86401)}  # 为字典类型，键为卫星序号，值为覆盖时间列表
    num = -1
    for filename in os.listdir(directory_path):
        sat = 0
        if os.path.isfile(os.path.join(directory_path, filename)) and filename.endswith(".txt"):
            file_path = os.path.join(directory_path, filename)
            # 每24*3600+1 = 86401个对应一个卫星一天覆盖的区域,
            # +1是因为从00:00到23:59为24*3600,还有第二天的00:00
            with (open(file_path, 'r', encoding='utf-8') as file):
                num += 1
                i = 0
                for line in file:
                    part = line.split()
                    # print(line)
                    if i == 1:
                        i += 1
                        fore_point_la = float(part[1])
                        temp = (float(part[0]) + 360) % 360
                        fore_point_lo = temp
                    elif i == 11:
                        i += 1
                        behind_point_la = float(part[1])
                        temp = (float(part[0]) + 360) % 360
                        behind_point_lo = temp
                        x1, y1, z1 = ReadInfo.global_lonlat_topos(behind_point_la, behind_point_lo)
                        x2, y2, z2 = ReadInfo.global_lonlat_topos(fore_point_la, fore_point_lo)
                        d = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2)

                        satellite = Satellite(d / 2, sat, longitude=(fore_point_lo + behind_point_lo) / 2,
                                              latitude=(fore_point_la + behind_point_la) / 2, num=num
                                              , center_x=(x1 + x2) / 2, center_y=(y1 + y2) / 2,
                                              center_z=(z1 + z2) / 2)

                        satellite_list[sat].append(satellite)
                        sat += 1
                    elif i > 20:
                        i = 0
                        d = 0
                    else:
                        i += 1
    return satellite_list


def draw_line(time_list, accum_cover_rate):
    # 设置全局字体属性（可选）
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
    plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号
    plt.rcParams.update({"font.size": 25})  # 此处必须添加此句代码方可改变标题字体大小
    plt.figure(figsize=(36, 12))
    y_major_locator = MultipleLocator(10)
    # 把y轴的刻度间隔设置为10，并存在变量里
    x_axis_data = []
    y_axis_data = []
    plt.title("卫星对区域的覆盖率曲线图")
    # 把y轴的主刻度设置为10的倍数
    for t, cover_rate in time_list:
        x_axis_data.append(t)
        y_axis_data.append(cover_rate)
    plt.plot(x_axis_data, y_axis_data, 'b--', label='coverage_rate', linewidth=1)
    plt.plot(x_axis_data, accum_cover_rate, 'r--', label='accum_cover_rate', linewidth=1)
    ax = plt.gca()
    ax.yaxis.set_major_locator(y_major_locator)
    plt.legend()
    plt.xticks([10800, 21600, 32400, 43200, 54000, 64800, 75600, 86400],
               ["3:00", "6:00", "9:00", "12:00", "15:00", "18:00", "21:00", "24:00"])
    # plt.slim(0, 20000)
    plt.xlabel('时间')
    plt.ylabel('覆盖率/ %')
    plt.show()


paused = True
t = 0


def play():
    global paused
    paused = not paused
    if not paused:
        loop()


def loop():
    global t
    global paused
    if not paused and t < 86400:
        for rectangle in per_rect_list[int(t)]:
            canvas.create_rectangle((rectangle.left0.lo - 55) * 5, (rectangle.left0.la + 30) * 5,
                                    (rectangle.right1.lo - 55) * 5,
                                    (rectangle.right1.la + 30) * 5, fill=rectangle.color)
        # root.update()
        # sleep(0.2)
        t += 60
        if t > 86400:
            print("finish")
        # print(t)
        root.after(1, loop)


def on_value_changed():
    time = current_value.get()
    if t < 86400:
        for rectangle in per_rect_list[int(time)]:
            canvas.create_rectangle((rectangle.left0.lo - 55) * 5, (rectangle.left0.la + 30) * 5,
                                    (rectangle.right1.lo - 55) * 5,
                                    (rectangle.right1.la + 30) * 5, fill=rectangle.color)


def on_slider_change(event):
    time = slider.get()
    if t < 86400:
        for rectangle in per_rect_list[int(time)]:
            canvas.create_rectangle((rectangle.left0.lo - 55) * 5, (rectangle.left0.la + 30) * 5,
                                    (rectangle.right1.lo - 55) * 5,
                                    (rectangle.right1.la + 30) * 5, fill=rectangle.color)


def write_output(valid_time_list):
    folder = 'C:\\Users\\l0ading\\PycharmProjects\\satellite\\output'
    with open(folder + '\\'"in_time_result.txt", 'w', encoding='utf-8') as f:
        f.write("        时间                         覆盖率%                       累计覆盖率% \n ")
        for time, coverage_rate, accum_coverage_rate in valid_time_list:
            datetime = to_date(time)
            f.write(str(datetime) + "            " + str(coverage_rate))
            f.write("                    " + str(per_accum_coverage_rate[time]))
            f.write("\n")


def init_queue(rectangle_area):
    """
    :param rectangle_area:矩形区域信息
    :return: 将初始矩形分割成512个网格
    """
    queue = [rectangle_area]
    while len(queue) < 512:
        new_rectangle = split_rectangle_area(queue[0])
        queue.append(new_rectangle[0])
        queue.append(new_rectangle[1])
        queue.append(new_rectangle[2])
        queue.append(new_rectangle[3])
        queue.remove(queue[0])
    return queue


def calc_accum_rate(queue):
    """
    :param queue: 队列信息
    :return: 累积覆盖率
    """
    accum_coverage_rate = 0
    for rect in queue:
        if rect.state == 1:
            accum_coverage_rate += rect.area
    accum_coverage_rate /= rectangle_area.area
    accum_coverage_rate *= 100
    return accum_coverage_rate


if __name__ == '__main__':
    area = calc_area(75, 135, 0, 55)
    print(area)

    rectangle_area = Rectangle(Point(75, 55), Point(135, 55), Point(75, 0), Point(135, 0), area)
    satellite_list = read_sat_info()
    valid_time_list = []  # 用于将覆盖率不为0的时间写入文件
    time_list = []
    # per_rect_list={key:[] for key in range(0,86400)}
    per_rect_list = []

    # 变量
    max_coverage_rate = 0
    per_accum_coverage_rate = []

    queue = init_queue(rectangle_area)
    for i in range(0, len(satellite_list)):  # len(satellite_list)
        valid_time, coverage_rate, valid_rect = cal_coverage_rate(satellites=satellite_list[i],
                                                                  rectangle_area=rectangle_area, queue=queue)
        time_list.append((valid_time, coverage_rate))
        per_rect_list.append(valid_rect)
        accum_coverage_rate = 0

        if coverage_rate:
            if coverage_rate > max_coverage_rate:
                max_coverage_rate = coverage_rate
                max_time = valid_time
            valid_time_list.append((valid_time, coverage_rate, accum_coverage_rate))

        accum_coverage_rate = calc_accum_rate(queue)
        per_accum_coverage_rate.append(accum_coverage_rate)

    print(max_coverage_rate)
    print(max_time)
    draw_line(time_list, per_accum_coverage_rate)
    write_output(valid_time_list)
    """
    gui界面
    """
    root = tk.Tk()
    root.title("Rectangle")

    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)
    canvas = tk.Canvas(root, width=500, height=500)
    canvas.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")  # row=0, column=0 表示第1行第一列

    start_button = tk.Button(root, text="开始/暂停", command=play, activebackground='blue')
    start_button.grid(row=1, column=0, padx=10, pady=10)

    current_value = tk.StringVar()
    spinbox = tk.Spinbox(root, from_=0, to=86400, increment=1, textvariable=current_value, command=on_value_changed)
    spinbox.grid(row=2, column=0, padx=10, pady=10, sticky="ew")  # row=1, column=0 表示第2行第一列

    slider = tk.Scale(root, from_=0, to=86400, orient=tk.HORIZONTAL, command=on_slider_change)
    slider.grid(row=3, column=0, padx=10, pady=10, sticky="ew")  # row=1, column=0 表示第2行第一列

    root.mainloop()
    #
    # print(merge_result)
