import pymurapi as api
import cv2 as cv
import time
import numpy as np
import math

mur = api.mur_init()

# предопределеные диапазоны цветов (HSV)
colors = {
    'green': ((45, 50, 50), (75, 255, 255)),
    'blue': ((130, 50, 50), (140, 255, 255)),
    'cyan': ((80, 50, 50), (100, 255, 255)),
    'orange': ((15, 50, 50), (30, 255, 255)),
    'red': ((0, 50, 50), (15, 255, 255)),
    'magenta': ((100, 50, 50), (160, 255, 255)),
}

# соответствие формы объекта к цвету (согласно заданию)
tag_shape_to_color = {
    'triangle': 'green',
    'square': 'orange',
    'circle': 'cyan',
}


# функция для ограничения значения диапазоном
def clamp(value, min_value, max_value):
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value

# функция для расчёта угла между точками
def angle_between(p1, p2):
    xDiff = p2[0] - p1[0]
    yDiff = p2[1] - p1[1]
    return math.degrees(math.atan2(yDiff, xDiff) - (np.pi / 2))

# функция для расчёта расстояния от центра до точки
def length_from_center(x, y):
    return math.sqrt(x ** 2 + y ** 2)

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

context = AUVContext()

# разворот на 90 градусов
def translate_to_90():
    yaw = mur.get_yaw() + 90
    if yaw < -180:
        yaw += 360
    if yaw > 180:
        yaw -= 360
    context.set_yaw(yaw)
    return True

# разворот на 180 градусов
def translate_to_180():
    yaw = mur.get_yaw() + 180
    if yaw < -180:
        yaw += 360
    if yaw > 180:
        yaw -= 360
    context.set_yaw(yaw)
    return True

# функция для отображения контура в окне (для отладки)
def show_contours(image, contours):
    image_to_show = image.copy()
    if contours:
        for contour in contours:
            cv.drawContours(image_to_show, [contour], -1, (0, 50, 150), 2)
    cv.imshow("", image_to_show)
    cv.waitKey(1)

# бездействие
def dummy():
    return False

# произвести выстрел
def shoot():
    if (context.get_speed() != 0):
        context.set_speed(0)
        return False
    else:
        mur.shoot()
        time.sleep(0.5)
        return True

# движение вперёд
def go_forward():
    if (context.get_speed() != 15):
        context.set_speed(15)
        return False
    else:
        return True

# движение назад
def go_back():
    if (context.get_speed() != -2.5):
        context.set_speed(-2.5)
        return False
    else:
        return True

# ожидание 5 секунд
def wait():
    time.sleep(5)
    return True

# ожидание 3 секунды
def wait_short():
    time.sleep(3)
    return True

# ожидание 12 секунд
def wait_long():
    time.sleep(12)
    return True

# прекратить движение
def stop():
    if (context.get_speed() != 0):
        context.set_speed(0)
        return False
    else:
        return True

# вспылтие на поверхность
def surface():
    mur.set_motor_power(2, 50)
    mur.set_motor_power(3, 50)
    time.sleep(5)
    return True

# стабилизировать курс и глубину
def stabilize():
    yaw = mur.get_yaw()
    depth = mur.get_depth()

    if abs(yaw - context.get_yaw()) < 1 and abs(depth - context.get_depth()) < 0.3:
        if context.check_stabilization(timeout=5):
            return True
    else:
        context.reset_stabilization_counter()
    return False

# поиск контура по цвету
def find_contours(image, color, approx = cv.CHAIN_APPROX_SIMPLE):
    hsv_image = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    mask = cv.inRange(hsv_image, color[0], color[1])
    contours, _ = cv.findContours(mask, cv.RETR_CCOMP, approx)
    return contours

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

# определение цвета из списка возможных.
# рассчитывается площадь контура для каждого из цветов,
# а затем выбирается цвет по наибольшему контуру
def detect_color(available_colors):
    image = mur.get_image_bottom()
    hsv_image = cv.cvtColor(image, cv.COLOR_BGR2HSV)

    areas = {}

    for color in available_colors:
        mask = cv.inRange(hsv_image, colors[color][0], colors[color][1])
        contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)

        biggest_area = 0

        if contours:
            for contour in contours:
                area = cv.contourArea(contour)
                if area > biggest_area:
                    biggest_area = area

        areas[color] = biggest_area

    color = sorted(areas, key=areas.get, reverse=True)[0]

    if (areas[color] > 5):
        return color
    else:
        return False

# определение направления стрелки
def detect_arrow_angle(image, contour):
    (arrow_center_x, arrow_center_y), radius = cv.minEnclosingCircle(contour)
    moments = cv.moments(contour)

    to_draw = image.copy()
    
    cv.circle(to_draw, (int(arrow_center_x), int(arrow_center_y)), 1, (255, 0, 255), 2)
    cv.circle(to_draw, (int(arrow_center_x), int(arrow_center_y)), int(radius), (255, 0, 255), 2)

    try:
        arrow_direction_x = int(moments['m10'] / moments['m00'])
        arrow_direction_y = int(moments['m01'] / moments['m00'])

        cv.circle(to_draw, (arrow_direction_x, arrow_direction_y), 1, (255, 0, 255), 2)
        cv.imshow("", to_draw)
        cv.waitKey(1)

        arrow_angle = (angle_between((arrow_direction_x, arrow_direction_y), (arrow_center_x, arrow_center_y)))
        context.set_yaw(mur.get_yaw() + arrow_angle)

        target_x = arrow_center_x - (320 / 2)
        target_y = arrow_center_y - (240 / 2)
        length = math.sqrt(target_x ** 2 + target_y ** 2)

        return arrow_angle, target_x, target_y, length
    except:
        return False, False, False, False

# стабилизироваться над стрелкой (с учетом направления стрелки)
def stabilize_on_arrow(color):
    image = mur.get_image_bottom()

    contours = find_contours(image, color, cv.CHAIN_APPROX_SIMPLE)

    if contours:
        for contour in contours:
            (arrow_angle, target_x, target_y, length) = detect_arrow_angle(image, contour)

            if arrow_angle != False:
                try:
                    output_forward = stabilize_on_arrow.forward_regulator.process(target_y)
                    output_side = stabilize_on_arrow.side_regulator.process(target_x)

                    output_forward = clamp(int(output_forward), -50, 50)
                    output_side = clamp(int(output_side), -50, 50)

                    context.set_speed(-output_forward)
                    context.set_side_speed(-output_side)

                    if abs(arrow_angle) < 2 and length < 7:
                        if context.check_stabilization(timeout=2):
                            return True
                    else:
                        context.reset_stabilization_counter()

                except AttributeError:
                    stabilize_on_arrow.forward_regulator = PDRegulator()
                    stabilize_on_arrow.forward_regulator.set_p_gain(0.5)
                    stabilize_on_arrow.forward_regulator.set_d_gain(0.1)

                    stabilize_on_arrow.side_regulator = PDRegulator()
                    stabilize_on_arrow.side_regulator.set_p_gain(0.5)
                    stabilize_on_arrow.side_regulator.set_d_gain(0.1)

    return False

# стабилизироваться по координатам, а также по углу
def stabilize_x_y_angle(x, y, angle):
    y_center = y - (240 / 2)
    x_center = x - (320 / 2)

    try:
        length = math.sqrt(x_center ** 2 + y_center ** 2)
        if length < 2.0:
            if context.check_stabilization(timeout=10):
                return True
        else:
            context.reset_stabilization_counter()

        output_forward = stabilize_x_y_angle.forward_regulator.process(y_center)
        output_side = stabilize_x_y_angle.side_regulator.process(x_center)

        output_forward = clamp(int(output_forward), -10, 10)
        output_side = clamp(int(output_side), -10, 10)

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

# обнаружение полоски определенного цвета
def find_line(image, color):
    contours = find_contours(image, color)
    if contours:
        for contour in contours:
            area = cv.contourArea(contour)
            if abs(area) < 300:
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
                cv.imshow("", to_draw)
                cv.waitKey(1)
                return True, x, y, find_rectangle_contour_angle(contour)
            except ZeroDivisionError:
                return False, 0, 0, 0
    return False, 0, 0, 0

# обнаружение объекта определенного цвета
def find_colored_object(image, color):
    contours = find_contours(image, color)
    if contours:
        for contour in contours:
            area = cv.contourArea(contour)
            if abs(area) < 50:
                continue

            ((_, _), (w, h), _) = cv.minAreaRect(contour)

            moments = cv.moments(contour)

            try:
                x = int(moments['m10'] / moments['m00'])
                y = int(moments['m01'] / moments['m00'])
                to_draw = image.copy()
                cv.circle(to_draw, (int(320 / 2), int(240 / 2)), 3, (0, 200, 150), 3)
                cv.circle(to_draw, (x, y), 2, (255, 0, 255), 2)
                cv.imshow("", to_draw)
                cv.waitKey(1)
                return True, x, y, area
            except ZeroDivisionError:
                return False, 0, 0, 0
    return False, 0, 0, 0

# стабилизироваться над полоской
def stabilize_over_line(color):
    found, x, y, angle = find_line(mur.get_image_bottom(), color)
    
    if found:
        if stabilize_x_y_angle(x, y, angle):
            return True
        else:
            return False

# стабилизироваться над кубом
def stabilize_over_box():
    if (context.get_depth() != 3.1):
        context.set_depth(3.1)
        return False

    found, x, y, area = find_line(mur.get_image_bottom(), colors['green'])
    
    if found:
        if stabilize_x_y_angle(x, y + 7, 0):
            return True
        else:
            return False

# обнаружение круга
def find_circle(image, color):
    contours = find_contours(image, color)

    if contours:
        for contour in contours:
            area = cv.contourArea(contour)
            if abs(area) < 400:
                continue

            ((_, _), (w, h), _) = cv.minAreaRect(contour)
            (_, _), radius = cv.minEnclosingCircle(contour)
            rectangle_area = w * h
            circle_area = radius ** 2 * math.pi
            aspect_ratio = w / h

            if 0.85 <= aspect_ratio <= 1.15:
                if rectangle_area > circle_area:
                    moments = cv.moments(contour)
                    try:
                        x = int(moments['m10'] / moments['m00'])
                        y = int(moments['m01'] / moments['m00'])

                        to_draw = image.copy()
                        cv.circle(to_draw, (x, y), int(radius), (255, 0, 255), 2)
                        cv.imshow("", to_draw)
                        cv.waitKey(1)
                        return True, x, y, area
                    except ZeroDivisionError:
                        return False, 0, 0, 0
    return False, 0, 0, 0

# стабилизироваться над кругом
def stabilize_over_circle(color):
    found, x, y, angle = find_circle(mur.get_image_bottom(), color)
    
    if found:
        if stabilize_x_y_angle(x, y, 0):
            return True
        else:
            return False
            
# обнаружение голубой полоски
def find_magenta_line(image):
    contours = find_contours(image, colors['magenta'])
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
    
# стабилизироваться над голубой полоской
def stabilize_over_magenta_line():
    found, x, y, angle = find_magenta_line(mur.get_image_bottom())
    
    if found:
        print(x, y, angle)
        if stabilize_x_y_angle(x, y, angle):
            return True
        else:
            return False   
 
# определение формы объекта определенного цвета
def detect_shape(image, color):
    contours = find_contours(image, color)

    if contours:
        for contour in contours:
            to_draw = image.copy()

            tag_area = cv.contourArea(contour)
            if (tag_area < 100):
                continue

            # после того, как найден контур подходящего цвета,
            # нужно подсчитать площади вписанных в него
            # треугольника, квадрата и круга.
            # форма объекта определяется по наибольшему
            # совпадению площади вписанной фигуры.

            (circle_x, circle_y), circle_radius = cv.minEnclosingCircle(contour)
            circle_area = circle_radius ** 2 * math.pi

            rectangle = cv.minAreaRect(contour)
            box = cv.boxPoints(rectangle)
            box = np.int0(box)
            rectangle_area = cv.contourArea(box)

            triangle = cv.minEnclosingTriangle(contour)[1]
            triangle = np.int0(triangle)
            triangle_area = cv.contourArea(triangle)

            cv.circle(to_draw, (int(circle_x), int(circle_y)), int(circle_radius), (255, 0, 255), 1)
            cv.drawContours(to_draw, [box], 0,(0,150,255),1)
            cv.drawContours(to_draw, [triangle], 0,(0,0,0),1)

            areas = {
                'circle': circle_radius ** 2 * math.pi,
                'square': cv.contourArea(box),
                'triangle': cv.contourArea(triangle),
            }

            tag_shapes = list(areas.keys())
            shapes_areas = np.array(list(areas.values()))
            difference = abs(shapes_areas - tag_area)
            arg = np.argmin(difference)
            tag_shape = tag_shapes[arg]

            cv.imshow("", to_draw)
            cv.waitKey(1)

            return tag_shape

    return False

# распознать навигационную метку
def detect_tag_shape():
    image = mur.get_image_bottom()
    tag_shape = detect_shape(image, colors['magenta'])
    if tag_shape != False:
        context.tag_shape = tag_shape
        # в соответствии с условиями задания,
        # определяем цвет стрелки, по которой
        # нужно следовать
        context.first_arrow_color = colors[tag_shape_to_color[tag_shape]]
        print(tag_shape, '- follow', tag_shape_to_color[tag_shape], 'arrow')
        return True
    else:
        return False
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
    contours = contours_recognize(colors['magenta'], img)
    # если контур найден и его площадь удовлетворяет условию
    # то в этом контуре отрисовывается эллипс для нахождения
    # угла отклонения от курса и координаты
    if contours:
        for cont in contours:
            if cv.contourArea(cont) < 300:
                continue

            ellipse = cv.fitEllipse(cont)
            x, y, angle = ellipse

            return True, x, y, angle

    return False, 0, 0, 0


# функция для движения вдоль трубы
def yaw_on_line():
    img = mur.get_image_bottom()
    speed = 10
    found, x, y, line_yaw = detect_tube(img)
    
    if found:
        try:
            # если курс близок к нулю, то его не надо корректировать
            print(line_yaw)
            if (175.0 < line_yaw < 180) or (0 < line_yaw < 5.0):
                mur.set_motor_power(0, speed)
                mur.set_motor_power(1, speed)
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
            keep_yaw.yaw_regulator = PDRegulator()
            keep_yaw.yaw_regulator.set_p_gain(0.8)
            keep_yaw.yaw_regulator.set_d_gain(0.6)

        except ZeroDivisionError:
            return False

    return False


# стабилизация над трубой по оси x
def stab_on_line():
    img = mur.get_image_bottom()
    found, x, y, angle = detect_tube(img)

    if found:
        # нахождение значения отклонения с нижней камеры,
        # разрешение камеры 240 на 320
        x_center = x[0] - (320 / 2)
        try:
            length = abs(x_center)
            # если отклонение не большое, то на четвертый двигатель
            # не надо подавать тягу
            if length < 15.0:
                mur.set_motor_power(4, 0)
                return True

            # корректировка положения над трубой
            output_side = stab_on_line.regulator_side.process(x_center)
            output_side = clamp(output_side, -50, 50)
            mur.set_motor_power(4, -output_side)

        except AttributeError:

                stabilize_on_arrow.forward_regulator = PDRegulator()
                stabilize_on_arrow.forward_regulator.set_p_gain(0.5)
                stabilize_on_arrow.forward_regulator.set_d_gain(0.1)

                stabilize_on_arrow.side_regulator = PDRegulator()
                stabilize_on_arrow.side_regulator.set_p_gain(0.5)
                stabilize_on_arrow.side_regulator.set_d_gain(0.1)

        except ZeroDivisionError:
            return False

    return False
    
# стабилизироваться на первой стрелкой, по которой
# нужно следовать (используя ранее определенный цвет)
def stabilize_on_first_arrow():
    return stabilize_on_arrow(context.first_arrow_color)

# обнаружение орандевого круга
def find_orange_circle():
    image = mur.get_image_bottom()
    found, x, y, area = find_circle(image, colors['orange'])

    if found:
        return True
    else:
        return False

# стабилизироваться над оранжевым кругом
def stabilize_over_orange_circle():
    return stabilize_over_circle(colors['orange'])

# установить подходящую глубину
# для захвата куба манипулятором
def set_grabbing_depth():
    mur.open_grabber()

    if (context.get_depth() != 3.62):
        context.set_depth(3.62)
        return False
    else:
        return True

# схватить куб
def grab_box():
    mur.close_grabber()
    return True

# отпустить куб
def ungrab_box():
    mur.open_grabber()
    return True

# определить цвет полоски
def detect_line_color():
    color = detect_color(line_color)
    if color:
        context.line_color = color
        return True
    else:
        return False

# установить обычную глубину (после захвата куба)
def set_default_depth():
    if (context.get_depth() != 3.0):
        context.set_depth(3.0)
        return False
    else:
        return True

# обнаружение синей корзины (круглой формы)
def find_blue_bin():
    image = mur.get_image_bottom()
    found, x, y, area = find_circle(image, colors['blue'])

    if found:
        return True
    else:
        return False

# стабилизироваться над синей корзиной
def stabilize_over_blue_bin():
    return stabilize_over_circle(colors['blue'])

# стабилизироваться над второй полоской (ранее определенный цвет)
def stabilize_over_magenta_line1():
    context.set_depth(3.0)
    return stabilize_over_line(colors['magenta'])

# стабилизироваться над второй стрелкой
def stabilize_on_second_arrow():
    return stabilize_on_arrow(colors[context.line_color])

# основной код, выполняемый при запуске скрипта
if __name__ == "__main__":
    keep_depth(3.0)
  #  context.set_depth(3.0)
   # context.set_yaw(0.0)

    # определим подзадачи нашей миссии

    # для того, чтобы добраться до платформы с кубом, нужно:
  #  go_to_box_platform = (
   #     stab_on_line,
  #      yaw_on_line,
        
       # stabilize_over_magenta_line,
   #     context.set_yaw(90.0),
  #    stabilize,
        
    #    translate_to_90,
          # определить маршрут по навигационной метке
     #   stabilize_on_first_arrow,    # стабилизироваться над первой стрелкой
  #      go_forward,                  # двигаться вперёд
  #  )

    # поиск и захват куба
 #   find_and_grab_box = (
  #      find_orange_circle,          # обнаружить оранжевый круг (мы все еще движемся)
   #     stabilize_over_orange_circle,# стабилизироваться над этим кругом
    #    stabilize_over_box,          # найдя круг, можно найти и стабилизироваться над кубом
     #   stabilize,                   # окончательно стабилизируем своё положение перед захватом
      #  set_grabbing_depth,          # погружаемся ближе к кубу
      #  wait_short,                  # ожидание 3 секунды
      #  stabilize,                   # стабилизируем положение
      #  wait_short,                  #
      #  grab_box,                    # захват куба манипулятором
      #  wait_short,                  #
      #  set_default_depth,           # принимаем нормальную глубину
      #  go_forward,                  # двигаемся вперед
      #  stabilize,                   # стабилизируем курс и глубину
      #  wait_short,                  #
      #  stop,                        # останавливаем движение после 3 секунд
   # )

    # найти корзину и бросить куб
    #find_bin_and_throw_box = (
    #    detect_line_color,           # определяем цвет полоски (для определения маршрута)
    #    stabilize_over_line,  # стабилизируемся над нужной полоской (определенного цвета)
    #    go_forward,                  # двигаемся вперёд
    #    find_blue_bin,               # находим синуюю корзину
    #    stabilize_over_blue_bin,     # стабилизируемся над корзиной
    #    ungrab_box,                  # отпускаем куб, чтобы он упал в корзину
    #)

    # добраться до последней платформы (над которой обруч)
    #go_to_final_platform = (
    #    go_forward,                  # двигаемся вперёд
    #    wait_short,                  # ожидание 3 секунды
    #    stop,                        # остановка движения
     #   stabilize,                   # стабилизируем положение
     #   stabilize_on_second_arrow,   # стабилизируемся над второй стрелкой (цвет был ранее определен)
     #   go_forward,                  # двигаемся вперед
     #   find_orange_circle,          # находим оранжевый круг
     #   stabilize_over_orange_circle,# стабилизируемся над этим кругом
     #   stabilize,                   # окончательно стабилизируем курс
    #)

  #  missions = (
 #       *go_to_box_platform,         # сначала нужно добраться до платформы с кубом
   #     *find_and_grab_box,          # затем найти и схватить куб
   #     *find_bin_and_throw_box,     # найти корзину и отпустить куб
   #     *go_to_final_platform,       # добраться до последнй платформы
   #     surface,                     # и в конце всплыть
   # )

    # задаем список действий миссий
  #  context.push_mission_list(missions)

    print("start")

    # в цикле проходим каждое действие для выполнения миссии,
    # а также выводим в консоль отладочную информацию
    while (True):
   #     mission = context.pop_mission()
      #  print('starting', mission.__name__, '\ttime:', context.time)
       
        stab_on_line()
    #    translate_to_90()
        keep_yaw(0.0, 30)
        yaw_on_line()
        
       # stabilize_over_magenta_line,
        
  #    stabilize,
        
    #    translate_to_90,
          # определить маршрут по навигационной метке
     #   stabilize_on_first_arrow,    # стабилизироваться над первой стрелкой
        go_forward,                  # двигаться вперёд
    
   #     while not mission():
   #         context.process()
  #          context.time += 1

  #      if context.get_missions_length() == 0:
 #           break

    print("done!")

    context.set_speed(0)
    context.set_depth(3.0)

    time.sleep(3)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    #
    
    
    
    
