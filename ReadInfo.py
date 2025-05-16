import os
import math


class Target:
    def __init__(self, name, lo, la):
        self.name = name  # 地名
        self.longitude = lo  # 经度
        self.latitude = la  # 纬度

    def __str__(self):
        return f"Name: {self.name}, Latitude: {self.latitude}, Longitude: {self.longitude}"


def read_target_file(filename):
    target_list = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                part = line.split()
                if len(part) == 3:
                    try:
                        name = part[0]
                        temp = (float(part[1]) + 360) % 360
                        lo = float(temp)
                        la = float(part[2])
                        target = Target(name, lo, la)
                        target_list.append(target)
                    except ValueError:
                        print("Invalid")
    return target_list


class Satellite:
    def __init__(self, radius=0.0, sta=0, longitude=0.0, latitude=0.0, center_x=0.0, center_y=0.0, center_z=0.0, num=0):
        self.time = sta
        self.center_y = center_y
        self.center_x = center_x
        self.center_z = center_z
        self.longitude = longitude
        self.latitude = latitude
        self.radius = radius
        # self.lonlat_topos()
        self.num = num

    """
    def lonlat_topos(self):
        R = 1
        # 将经纬度坐标转换到地球球面上的 xyz 坐标（其中，lon 为经度，lat 为纬度）
        self.center_x = R*math.cos(self.latitude) * math.cos(self.longitude)
        self.center_y = R*math.cos(self.latitude) * math.sin(self.longitude)
        self.center_z = R*math.sin(self.latitude)
    """

    def __str__(self):
        return f"center_x: {self.center_x}, center_y: {self.center_y}," \
               f"radius: {self.radius}, longitude: {self.longitude}, latitude: {self.latitude}"


# 将经纬度坐标转换到单位球面上的 xy 坐标（其中，lon 为经度，lat 为纬度）
def global_lonlat_topos(latitude, longitude):
    latitude, longitude = map(math.radians, [latitude, longitude])
    R = 6371
    x = R * math.cos(latitude) * math.cos(longitude)
    y = R * math.cos(latitude) * math.sin(longitude)
    z = R * math.sin(latitude)
    return x, y, z


def read_satellite_file():
    directory_path = "D:\\Data\\SatelliteInfo"

    satellite_list = []
    num = -1
    for filename in os.listdir(directory_path):
        sat = 0
        if os.path.isfile(os.path.join(directory_path, filename)) and filename.endswith(".txt"):
            file_path = os.path.join(directory_path, filename)
            # 每24*3600+1 = 86401个对应一个卫星一天覆盖的区域,
            # +1是因为从00:00到23:59为24*3600,还有第二天的00:00

            with (open(file_path, 'r', encoding='utf-8') as f):
                num += 1
                i = 0
                for line in f:
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
                        # fore_latitude_rad, fore_longitude_rad, behind_latitude_rad, behind_longitude_rad = map(
                        #  math.radians, [fore_point_la, fore_point_lo, behind_point_la, behind_point_lo])
                        x1, y1, z1 = global_lonlat_topos(behind_point_la, behind_point_lo)
                        x2, y2, z2 = global_lonlat_topos(fore_point_la, fore_point_lo)
                        d = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2)
                        # print(d/2)
                        # print(str((x1+x2)/2)+" "+str((y1+y2)/2)+"  "+str((z1+z2)/2))
                        satellite = Satellite(d / 2, sat, longitude=(fore_point_lo + behind_point_lo) / 2,
                                              latitude=(fore_point_la + behind_point_la) / 2, num=num
                                              , center_x=(x1 + x2) / 2, center_y=(y1 + y2) / 2, center_z=(z1 + z2) / 2)

                        satellite_list.append(satellite)
                        sat += 1
                        # print(satellite)
                    elif i > 20:
                        i = 0
                        d = 0
                    else:
                        i += 1
    # print(sat)
    return satellite_list


if __name__ == "__main__":
    satellite_list = read_satellite_file()
    # for satellite in satellite_list:
    #  print(satellite)
    # list = {(259.6234369809845, 7.127690837081347),
    #         (255.4404955237949, 5.726330337135493),
    #         (254.0408442700897, 4.324969837189639),
    #         (253.22703283685058, 2.923609337243784),
    #         (252.78567479991366, 1.52224883729793),
    #         (252.64497219019384, 0.1208883373520742),
    #         (252.78602961324285, -1.2804721625937798),
    #         (253.2276971299826, -2.6818326625396343),
    #         (254.04171512407595, -4.08319316248549),
    #         (255.4413679133661, -5.484553662431344),
    #         (259.6234443474301, -6.8859141623771984),
    #         (263.8623272892994, -5.484553662431344),
    #         (265.26198007858954, -4.08319316248549),
    #         (266.07599807268286, -2.6818326625396343),
    #         (266.5176655894227, -1.2804721625937798),
    #         (266.6587230124716, 0.1208883373520742),
    #         (266.5180204027518, 1.52224883729793),
    #         (266.0766623658149, 2.923609337243784),
    #         (265.2628509325758, 4.324969837189639),
    #         (263.8631996788706, 5.726330337135493),
    #         (259.6234369809845, 7.127690837081347)
    #         }
    # list = {(75, 0), (135, 0), (75, 55), (135, 55)}

    # for point in list:
    # x, y, z = global_lonlat_topos(point[1], point[0])
    # delta = (x -0.035)**2 +(y - 6.52) **2 +(z - 0.65) **2-0.65**2
    #  delta1 = (point[0] - 259) ** 2 + (point[1] - 0.5) ** 2 - 6.5 * 6.5
    # print(str((x, y, z)) + " " + str((point[0], point[1])) + "    ")
    # print(delta1)
    # print("\n")

    # target_list = read_target_file('D:\\Data\\target.txt') for item in target_list: print(item) print(math.sqrt((
    # -0.2840938204738526 + 0.35241290219331206) ** 2 + (0.6002673626664524 - 0.7446058945398571) ** 2 + (
    # 0.7476428254761975 + 0.5668925896359787) ** 2))
