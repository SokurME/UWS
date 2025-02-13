import cv2
import numpy as np
import math
import time
import pymurapi as mur
import pymurapi as mur

# диапазон цветов обломков
colors_dict = {
    'red': ((160, 50, 50), (180, 255, 255)),
    'yellow': ((20, 50, 50), (40, 255, 255)),
    'green': ((45, 50, 50),(75, 255, 255)),
}
    
# шрифт
font = cv2.FONT_HERSHEY_PLAIN   
# списки для записи имен фигур и для записи распознанных чисел в таблице
storage = []
digits = []
# переменные для подсчета распознанных фигур
triangles = 0
circles = 0
squares = 0
# определение начала и конца миссии
start = False
finish = False

# путь к файлам для распознавания цифр
samples = np.loadtxt('C:\\nto_final_task\\data\\generalsamples.data', np.float32)
# ПОМЕНЯЙТЕ ПУТИ!
responses = np.loadtxt('C:\\nto_final_task\\data\\generalresponses.data', np.float32)

responses = responses.reshape((responses.size, 1))
# распознавание цифр 
model = cv2.ml.KNearest_create()
model.train(samples, cv2.ml.ROW_SAMPLE, responses)


# поиск контура по цвету
def find_contours(img, color):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
    contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours
    

# поиск фигуры по цвету и подпись этих фигур соответственно таблице
def detect_shape(drawing, cnt, num, color):
    global font
    area = cv2.contourArea(cnt)
    if area < 500:
        return
    # описанная окружность
    (circle_x, circle_y), circle_radius = cv2.minEnclosingCircle(cnt)
    circle_area = circle_radius ** 2 * math.pi
    # описанный прямоугольник (с вращением)
    rectangle = cv2.minAreaRect(cnt)
    # получение контура описанного прямоугольника
    box = cv2.boxPoints(rectangle)
    box = np.int0(box)
    # вычисление площади и соотношения сторон прямоугольника
    rectangle_area = cv2.contourArea(box)
    rect_w, rect_h = rectangle[1][0], rectangle[1][1]
    aspect_ratio = max(rect_w, rect_h) / min(rect_w, rect_h)
    # описанный треугольник
    try:
        triangle = cv2.minEnclosingTriangle(cnt)[1]
        triangle = np.int0(triangle)
        triangle_area = cv2.contourArea(triangle)
    except:
        triangle_area = 0
    # заполнение словаря, который будет содержать площади каждой из описанных фигур
    shapes_areas = {
        'circle': circle_area,
        'square' if aspect_ratio < 1.25 else 'rectangle': rectangle_area,         
        'triangle': triangle_area,
    }
    # заполнение аналогичного словаря, который будет содержать
    # разницу между площадью контора и площадью каждой из фигур
    diffs = {
        name: abs(area - shapes_areas[name]) for name in shapes_areas
    }
    
    # получение имени фигуры с наименьшей разницой площади
    shape_name = min(diffs, key=diffs.get)
    
    # получение высоты, для того, чтобы игнорировать желтые границы трубы
    _, _, _, h = cv2.boundingRect(cnt)
    
    # поиск координат x, y для написания текста
    moments = cv2.moments(cnt)
    
    try:
       
        x = int(moments['m10'] / moments['m00'])
        y = int(moments['m01'] / moments['m00'])
        
        # фигуры (кроме прямоугольников и фигур высотой больше 90) подписываются в соответствии с классом из таблицы
        if shape_name != 'rectangle' and h < 90:
            if shape_name == 'square': shape = shape_name + ' ' + num[0]
            if shape_name == 'triangle': shape = shape_name + ' ' + num[1]
            if shape_name == 'circle': shape = shape_name + ' ' + num[2]
                
            cv2.putText(drawing, color, (x-29, y-28), font, 1, (  0,  0,  0), 3, cv2.LINE_AA)
            cv2.putText(drawing, color, (x-30, y-27), font, 1, (255,255,255), 1, cv2.LINE_AA)
            
            cv2.putText(drawing, shape, (x-30, y+32), font, 1, (  0,  0,  0), 3, cv2.LINE_AA)
            cv2.putText(drawing, shape, (x-31, y+31), font, 1, (255,255,255), 1, cv2.LINE_AA)
            
            # если фигура проходит экран в районе низа экрана, то ее значения возвращаются для записи в список storage
        if 400 < y < 420:
            print(shape_name)
            return shape_name
            
    except ZeroDivisionError:
        pass


# функция для подсчета фигур, исходя из записанного списка storage
def count_shapes(shape_store):
    global triangles
    global squares
    global circles
    # если в списке половина элементов 
    # принадлежат какой-то из фигур, то к кол-ву этих фигур +1
    
    if shape_store.count('triangle') > 2: triangles += 1    
    if shape_store.count('square') > 2: squares += 1         
    if shape_store.count('circle') > 2: circles += 1


# распознавание цифр из таблицы на старте
def digits_recognize(img):
    three_strings = []
    # поиск контуров
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_mask = cv2.adaptiveThreshold(img_hsv, 255, 1, 1, 45, 10)
    contours, hierarchy = cv2.findContours(img_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(img, contours, 0, (0,255,0), 3)
    for cnt in contours:
        area = cv2.contourArea(cnt)
        # ограничение контуров по площади
        if  area > 300:
            [x, y, w, h] = cv2.boundingRect(cnt)
            # ограничение по высоте
            if 25 < h < 70:
                # поиск цифры
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
                roi = img_mask[y:y + h, x:x + w]
                roismall = cv2.resize(roi, (10, 10))
                roismall = roismall.reshape((1, 100))
                roismall = np.float32(roismall)
                retval, results, neigh_resp, dists = model.findNearest(roismall, k=1)
                string = str(int((results[0][0])))

                
                # три распознанных числа записываются в список и эти значения возвращаются
                three_strings.append(string)               
                if len(three_strings) == 3:
                    return three_strings
                    


while(True):
     drawing = auv.get_image_bottom()
    
       # распознавание цифр до "старта" миссии
     if start != True:
            # выравнивание перспективы
            pts1 = np.float32([[280, 0], [640, 0],
                       [340, 480], [640, 480]])
            
            pts2 = np.float32([[0, 0], [640, 0],
                       [0, 480], [640, 480]])
        
            matrix = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(drawing, matrix, (640, 480))
            # распознавание цифр
            digits = digits_recognize(result)
            cv2.imshow('digits', result)
            
            if digits != None:
                digits.reverse()
                print('square:', digits[0], ' triangle:', digits[1], ' circle:', digits[2])
                start = True
        
        # старт миссии    
     if start and finish != True:
        
            # поиск квадратов, треугольников и кругов по словарю цветов
            for name in colors_dict:
                contours = find_contours(drawing, colors_dict[name])
            
                if not contours:
                    continue
            
                for cnt in contours:
                    shape_name = detect_shape(drawing, cnt, digits, name)
                
                       # запись в список фигур всех найденных фигур, кроме прямоугольников и нулевых значений
                    if shape_name is not None and shape_name != 'rectangle':
                        storage.append(shape_name)
                        
                    
                       # если кол-во эл-ов списка равно 6, то происходит подсчет фигур в списке
                    if len(storage) == 6:
                        count_shapes(storage)
                       # затем список очищается
                        storage.clear()
                    
                       # если посчитано больше пяти фигур, то миссия завершена
                    if triangles + squares + circles > 5:
                        finish = True
    
     if finish:
            print('\nsquares:  ', squares, '\ntriangles:', triangles,'\ncircles:  ', circles)
       
        # вывод текста с подсчетом фигур
            cv2.putText(drawing, 'squares: ' + str(squares), (290, 390), font, 1, (0,0,0), 3, cv2.LINE_AA) 
            cv2.putText(drawing, 'squares: ' + str(squares), (291, 389), font, 1, (255, 255, 255), 1, cv2.LINE_AA) 
            cv2.putText(drawing, 'triangles: ' + str(triangles), (290, 410), font, 1, (0,0,0), 3, cv2.LINE_AA)    
            cv2.putText(drawing, 'triangles: ' + str(triangles), (291, 409), font, 1, (255, 255, 255), 1, cv2.LINE_AA) 
            cv2.putText(drawing, 'circles: ' + str(circles), (290, 430), font, 1, (0,0,0), 3, cv2.LINE_AA)
            cv2.putText(drawing, 'circles: ' + str(circles), (291, 429), font, 1, (255, 255, 255), 1, cv2.LINE_AA)
    
                
            cv2.imshow("draw", drawing)
            cv2.waitKey(1)
 
     else:
        break
    
     time.sleep(0.03)
    
  
  
