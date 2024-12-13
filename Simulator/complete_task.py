import cv2 as cv
import pymurapi as mur
import math
import time
import numpy as np

auv = mur.mur_init()

# диапазоны цветов корзин
green_color = ((45, 50, 50), (75, 255, 255))
yellow_color = ((20, 50, 50), (40, 255, 255))
blue_color = ((130, 50, 50), (180, 255, 255))

# переменные подсчета корзин и подсчета очков корзин
bin_count = 0
finish_count = 0


# класс PD-регулятора
class PD(object):
    _kp = 0.0
    _kd = 0.0
    _prev_error = 0.0
    _timestamp = 1

    def __init__(self):
        pass

    def set_p_gain(self, value):
        self._kp = value

    def set_d_gain(self, value):
        self._kd = value

    def process(self, error):
        timestamp = int(round(time.time() * 1000))

        output = self._kp * error + self._kd / (timestamp - self._timestamp) * (error - self._prev_error)

        self._timestamp = timestamp
        self._prev_error = error
        return output

# функция ограничивающая диапазон значений
def clamp(value, min_v, max_v):
    if value > max_v:
        return max_v
    if value < min_v:
        return min_v
    return value


# функция чтобы плыть прямо после завершения сброса
def go_straight():
    auv.set_motor_power(0, 15)
    auv.set_motor_power(1, 15)
    time.sleep(3)


# функция для сброса сферы
def drop_sphere():
    auv.drop()
    time.sleep(1)
    go_straight()


# функция завершающая попытку
def stop_round(r):
    # движение против или по часовой стрелке
    power = 12 * (1 if (r % 2 == 1) else -1)
    auv.set_motor_power(0, -power)
    auv.set_motor_power(1, power)

    # всплытие
    keep_depth(0.0)
    time.sleep(20)

# функция поддержания глубины
def keep_depth(depth_to_set):
    try:
        error = auv.get_depth() - depth_to_set

        output = keep_depth.regulator.process(error)
        output = clamp(output, -100, 100)
        auv.set_motor_power(2, output)
        auv.set_motor_power(3, output)

    except AttributeError:
        keep_depth.regulator = PD()
        keep_depth.regulator.set_p_gain(20)
        keep_depth.regulator.set_d_gain(12)

# распознавание контуров
def contours_recognize(color, img):
    # изображение с камеры преобразуется в HSV формат
    image_hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    # бинаризация изображения
    image_bin = cv.inRange(image_hsv, color[0], color[1])
    # поиск контура
    contours, _ = cv.findContours(image_bin, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
    return contours
    
    
# функция нахождения синей трубы с помощью нижней камеры
def detect_tube(img):
    contours = contours_recognize(blue_color, img)
    # если контур найден и его площадь удовлетворяет условию
    # то в этом контуре отрисовывается эллипс для нахождения
    # угла отклонения от курса и координаты
    if contours:
        for cont in contours:
            if cv.contourArea(cont) < 300:
                continue

            ellipse = cv.fitEllipse(cont)
            x, y, angle = ellipse
            
            drawing = img.copy()
            rectangle = cv.minAreaRect(cont)
            box = cv.boxPoints(rectangle)
            box = np.int0(box)
            cv.drawContours(drawing, [box], 0, (0,0,255), 3)
            cv.imshow('img', drawing)
            cv.waitKey(1)
        

            return True, x, y, angle

    return False, 0, 0, 0

def turn_left():
    yaw = auv.get_yaw()
    while yaw <= 90: 
        auv.set_motor_power(1, 5)
        yaw = auv.get_yaw()
    auv.set_motor_power(0, 5)
    
# функция для движения вдоль трубы
def yaw_on_line(img):
    speed = 10
    found, x, y, line_yaw = detect_tube(img)
    
    if found:
        try:
            # если курс близок к нулю, то его не надо корректировать
            if (175.0 < line_yaw < 180) or (0 < line_yaw < 5.0):
                auv.set_motor_power(0, speed)
                auv.set_motor_power(1, speed)
                return True

            # корректировка курса
            error = line_yaw
            out = yaw_on_line.regulator.process(error)
            output = clamp(out, -100, 100)

            output_0 = clamp(output + speed, -100, 100)
            output_1 = clamp(-output + speed, -100, 100)

            auv.set_motor_power(0, output_0)
            auv.set_motor_power(1, output_1)

        except AttributeError:
            yaw_on_line.regulator = PD()
            yaw_on_line.regulator.set_p_gain(0.4)
            yaw_on_line.regulator.set_d_gain(0.4)

        except ZeroDivisionError:
            return False

    return False


# стабилизация над трубой по оси x
def stab_on_line(img):
    found, x, y, angle = detect_tube(img)

    if found:
        # нахождение значения отклонения с нижней камеры,
        # разрешение камеры 240 на 320
        x_center = x[0] - (320 / 2)
        try:
            length = abs(x_center)
            # если отклонение не большое, то на четвертый двигатель
            # не надо подавать тягу
            if 0 < length < 2.0:
                auv.set_motor_power(4, 0)
                return True
            if  length < 0:
                print(length)
                turn_left()
            # корректировка положения над трубой
            output_side = stab_on_line.regulator_side.process(x_center)
            output_side = clamp(output_side, -50, 50)
            auv.set_motor_power(4, -output_side)

        except AttributeError:

            stab_on_line.regulator_side = PD()
            stab_on_line.regulator_side.set_p_gain(0.2)
            stab_on_line.regulator_side.set_d_gain(0.4)

        except ZeroDivisionError:
            return False

    return False


# функции поиска корзины по цвету
def find_bin(color, img):
    cnt = contours_recognize(color, img)

    if cnt:
        for c in cnt:
            area = cv.contourArea(c)
            if abs(area) < 100:
                continue
            (x, y), radius = cv.minEnclosingCircle(c)
            
            return True, x, y
            
    return False, 0, 0


# функция стабилизации над корзиной по осям X и Y
def stabilization(color, img):
    found, x, y = find_bin(color, img)
    if found:
        # разрешение нижней камеры 240 на 320
        x_center = x - (320 / 2)
        y_center = y - (240 / 2)

        try:
            # если расстояние от центра камеры до корзины подхлдящее,
            # то возврашается True
            length = math.sqrt(x_center ** 2 + y_center ** 2)

            if length < 25.0:
                auv.set_motor_power(0, 0)
                auv.set_motor_power(1, 0)
                auv.set_motor_power(4, 0)
                return True

            # корректировка положения кад корзиной
            output_forward = stabilization.regulator_forward.process(y_center)
            output_side = stabilization.regulator_side.process(x_center)

            output_forward = clamp(output_forward, -50, 50)
            output_side = clamp(output_side, -50, 50)

            auv.set_motor_power(0, -output_forward)
            auv.set_motor_power(1, -output_forward)
            auv.set_motor_power(4, -output_side)

        except AttributeError:
            stabilization.regulator_forward = PD()
            stabilization.regulator_forward.set_p_gain(0.2)
            stabilization.regulator_forward.set_d_gain(0.4)

            stabilization.regulator_side = PD()
            stabilization.regulator_side.set_p_gain(0.2)
            stabilization.regulator_side.set_d_gain(0.4)

        except ZeroDivisionError:
            return False
    return False


# функция вызываемая тогда, когда аппарат стабилизировался над корзиной
def stable_on_bin(color, img):
    global finish_count
    global bin_count
    # проверка стабилизации по цвету корзины
    stable = stabilization(color, img)
    if stable:
        # прибавление баллов в зависимости от цвета корзины
        if color == green_color:
            finish_count += 1

        elif color == yellow_color:
            finish_count += 2

        # сброс сферы
        drop_sphere()
        # подсчет корзин
        bin_count += 1
        return True
    return False


while True:
    image = auv.get_image_bottom()
    
    
    # поддержание одной глубины
    keep_depth(2.9)    
    # стабилизация над трубой и поддержание курса
    stab_on_line(image)
    yaw_on_line(image)

    # стабилизация над корзиной в зависимости от цвета
    stable_on_bin(yellow_color, image)
    stable_on_bin(green_color, image)

    # если пройдено пять корзин, то надо заканчивать раунд
    if bin_count == 5:
        stop_round(finish_count)

    time.sleep(0.01)
    
    
    
    
