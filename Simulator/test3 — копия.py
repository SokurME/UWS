import pymurapi as api
import cv2 as cv
import time
import numpy as np
import math

mur = api.mur_init()

# класс для хранения текущего состояния
class AUVContext(object):
    _yaw = 0.0
    _depth = 0.0
    _speed = 0.0
    _side_speed = 0.0
    _timestamp = 0
    _missions = []
    _min_area = math.inf
    _min_yaw = 0.0
    _stabilization_counter = 0
    time = 0

    def __init__(self):
        pass

    def set_min_circle(self, yaw, area):
        if area < self._min_area:
            self._min_area = area
            self._min_yaw = yaw

    def get_min_circle_yaw(self):
        return self._min_yaw

    def get_yaw(self):
        return self._yaw

    def get_depth(self):
        return self._depth

    def get_speed(self):
        return self._speed

    def get_side_speed(self):
        return self._side_speed

    def set_yaw(self, value):
        self._yaw = value

    def set_depth(self, value):
        self._depth = value

    def set_speed(self, value):
        self._speed = value

    def set_side_speed(self, value):
        self._side_speed = value

    def get_stabilization_counter(self):
        return self._stabilization_counter

    def reset_stabilization_counter(self):
        self._stabilization_counter = 0
    
    def yaw_on_line(self, value):
        self._image = value

    def add_stabilization_counter(self):
        self._stabilization_counter += 1

    def check_stabilization(self, timeout = 3):
        if self._stabilization_counter > timeout:
            return True
        else:
            self.add_stabilization_counter()
            return False

    def push_mission(self, mission):
        self._missions.append(mission)

    def push_mission_list(self, missions):
        for mission in missions:
            self.push_mission(mission)

    def pop_mission(self):
        if len(self._missions) != 0:
            return self._missions.pop(0)
        return {}

    def get_missions_length(self):
        return len(self._missions)

    def process(self):
        timestamp = int(round(time.time() * 1000))
        if timestamp - self._timestamp > 16:
            keep_yaw(self._yaw, self._speed)
            keep_depth(self._depth)
            mur.set_motor_power(4, self._side_speed)
            self._timestamp = timestamp
        else:
            time.sleep(0.05)
            
# объект, где будет хранится текущее состояние
context = AUVContext()

# PD-регулятор
class PDRegulator(object):
    _p_gain = 0.0
    _d_gain = 0.0
    _prev_error = 0.0
    _timestamp = 0

    def __init__(self):
        pass

    def set_p_gain(self, value):
        self._p_gain = value

    def set_d_gain(self, value):
        self._d_gain = value

    def process(self, error):
        timestamp = int(round(time.time() * 1000))

        if timestamp == self._timestamp:
            return 0

        output = self._p_gain * error + self._d_gain / (timestamp - self._timestamp) * (error - self._prev_error)
        self._timestamp = timestamp
        self._prev_error = error
        return output
        
# функция для ограничения значения диапазоном
def clamp(value, min_value, max_value):
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value
        
# обнаружение голубой полоски
def find_cyan_line(image):
    contours = find_contours(image, (60, 150, 140), (180, 255, 255))
    if contours:
        for contour in contours:
            area = cv.contourArea(contour)
            if abs(area) < 100:
                continue

            ((_, _), (w, h), _) = cv.minAreaRect(contour)
            aspect_ratio = max(w, h) / min(w, h)

            moments = cv.moments(contour)
            try:
                x = int(moments['m10'] / moments['m00'])
                y = int(moments['m01'] / moments['m00'])
                to_draw = image.copy()
                cv.circle(to_draw, (int(320 / 2), int(240 / 2)), 3, (0, 200, 150), 3)
                cv.circle(to_draw, (x, y), 2, (255, 0, 255), 2)
                cv.imshow("cyan", to_draw)
                cv.waitKey(1)
                return True, x, y, find_rectangle_contour_angle(contour)
            except ZeroDivisionError:
                return False, 0, 0, 0
    return False, 0, 0, 0

# расчёт угла прямоугольника
# для определение отклонения от полоски,
# чтобы затем скорректировать курс
def find_rectangle_contour_angle(contour):
    rectangle = cv.minAreaRect(contour)
    box = cv.boxPoints(rectangle)
    box = np.int0(box)
    edge_first = np.int0((box[1][0] - box[0][0], box[1][1] - box[0][1]))
    edge_second = np.int0((box[2][0] - box[1][0], box[2][1] - box[1][1]))

    edge = edge_first
    if cv.norm(edge_second) > cv.norm(edge_first):
        edge = edge_second

    angle = -((180.0 / math.pi * math.acos(edge[0] / (cv.norm((1, 0)) * cv.norm(edge)))) - 90)
    return angle
    
# стабилизироваться по координатам, а также по углу
# иными словами, расположиться над объектом с заданным направлением
def stabilize_x_y_angle(x, y, angle):
    y_center = y - (240 / 2)
    x_center = x - (320 / 2)

    try:
        length = math.sqrt(x_center ** 2 + y_center ** 2)
        if length < 4.5:
            if context.check_stabilization():
                return True
        else:
            context.reset_stabilization_counter()

        output_forward = stabilize_x_y_angle.forward_regulator.process(y_center)
        output_side = stabilize_x_y_angle.side_regulator.process(x_center)

        output_forward = clamp(int(output_forward), -50, 50)
        output_side = clamp(int(output_side), -50, 50)

        context.set_speed(-output_forward)
        context.set_side_speed(-output_side)

        context.set_yaw(mur.get_yaw() + angle)
    except AttributeError:
        stabilize_x_y_angle.forward_regulator = PDRegulator()
        stabilize_x_y_angle.forward_regulator.set_p_gain(0.5)
        stabilize_x_y_angle.forward_regulator.set_d_gain(0.1)

        stabilize_x_y_angle.side_regulator = PDRegulator()
        stabilize_x_y_angle.side_regulator.set_p_gain(0.5)
        stabilize_x_y_angle.side_regulator.set_d_gain(0.1)
    return False

    
# стабилизироваться над голубой полоской
def stabilize_over_cyan_line():
    found, x, y, angle = find_cyan_line(mur.get_image_bottom())
    
    if found:
        print(x, y, angle)
        if stabilize_x_y_angle(x, y, angle):
            return True
        else:
            return False
            
# функция для установки курса робота
def keep_yaw(yaw_to_set, speed):
    def clamp_angle(angle):
        if angle > 180.0:
            return angle - 360.0
        if angle < -180.0:
            return angle + 360
        return angle
    try:
        error = mur.get_yaw() - yaw_to_set
        error = clamp_angle(error)
        output = keep_yaw.yaw_regulator.process(error)
        mur.set_motor_power(0, clamp(-output + speed, -100, 100))
        mur.set_motor_power(1, clamp(output + speed, -100, 100))
    except AttributeError:
        # создание PD-регулятора, если он отсутствует
        keep_yaw.yaw_regulator = PDRegulator()
        keep_yaw.yaw_regulator.set_p_gain(0.8)
        keep_yaw.yaw_regulator.set_d_gain(0.6)

# функция для установки глубины погружения
def keep_depth(depth_to_set):
    try:
        error = mur.get_depth() - depth_to_set
        output = keep_depth.depth_regulator.process(error)
        output = clamp(output, -100, 100)
        mur.set_motor_power(2, output)
        mur.set_motor_power(3, output)
    except AttributeError:
        keep_depth.depth_regulator = PDRegulator()
        keep_depth.depth_regulator.set_p_gain(45)
        keep_depth.depth_regulator.set_d_gain(5)

            
# поиск на изображении контура по цвету
def find_contours(image, color_low, color_high, approx = cv.CHAIN_APPROX_SIMPLE):
    hsv_image = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    mask = cv.inRange(hsv_image, color_low, color_high)
    contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, approx)
    return contours
            
# двигаться вперёд
def go_forward():
    if (context.get_speed() != 30):
        context.set_speed(30)
        return False
    else:
        return True
    
# основной код, выполняемый при запуске скрипта
if __name__ == "__main__":
    context.set_depth(1.8)
    context.set_yaw(0.0)

    missions = (
        stabilize_over_cyan_line, # стабилизироваться над голубой полоской
        keep_yaw,         
         )
    context.push_mission_list(missions)
    
    while (True):
        mission = context.pop_mission()
     #   print('starting', mission.__name__, '\t\ttime:', context.time)
        while not mission():
            context.process()
            context.time += 1

        if context.get_missions_length() == 0:
            break

    print("done!")

    context.set_speed(0)
    context.set_depth(2.5)

    time.sleep(3)
    
 
    
