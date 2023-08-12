from math import sqrt
import json
import math


class Polygon:
    def __init__(self, data: dict|int, from_local: bool=False):
    # def __init__(self):
        '''
        Может буду что-то передавать, может надо, может нет, типа сразу при создании передавать направление, исходные координаты, все экземпляры углов...
        Может на всё это навешаю сеттеры/геттеры и через эти методы манипулировать
        '''
        # type: ignore
        # db = DB("Data/Input/DataInput6.json")
        # db = {'Answer': 'I have not get any data'}    # На всякий случай, если совсем ничего не передадут и нечего читать будет. Мб это раньше надо в АПИ самой проверку делать и возвращать там что-то
        if from_local:
            db = DB(f"Data/Input/DataInput{data}.json")
        else:
            db = data
        
        self.all_data = db.get_all_data()   # type: ignore
        self.measured_angles = self.all_data.get('aPoints') 
        self.bearing_angle = self.all_data.get('bearingAngle')
        self.bearing_angle = BearingAngle(self.bearing_angle.get('Deg'), self.bearing_angle.get('Min'), self.bearing_angle.get('Sec')) # type: ignore
        self.all_distance = [point.get('HorDist') for point in self.measured_angles[:-1]]    # type: ignore
        self.initial_coords = [(d.get("X"), d.get("Y")) for d in self.all_data.get('coords')]   # type: ignore
        self.sum_theoretical_coordinate_increments = (self.initial_coords[1][0] - self.initial_coords[0][0],
                                                      self.initial_coords[1][1] - self.initial_coords[0][1])
        self.angles = {i: Angle(d.get('Deg'), d.get('Min'), d.get('Sec')) for i, d in enumerate(self.measured_angles)} # type: ignore
        self.theoretical_sum_angles = self.calc_sum_of_theoretical_angles()  # теоретическая сумма углов, нужно будет рассчитывать, когда заполнится массив углов
        self.practical_sum_angles = self.calc_sum_of_practice_angles(self.angles)  # практическая сумма углов, просто посчитать сумму углов в массиве
        self.difference = Angle(DD=(self.theoretical_sum_angles.DD - self.practical_sum_angles.DD))  # Невязка
        self.fixed_angles = self.angles.copy()
        self.permissible_discrepancy = self.calc_permissible_discrepancy(len(self.angles))
        
        if self.difference.DD <= self.permissible_discrepancy.DD:
            self.calc_and_send_amendment(self.difference)   # Вызов функции изменит углы в fixed_angles, если невязка получилась допустимой. Если она получится недопустимой... Вся прога рухнет, надо подумать, как обойти это, и как по-другому передавать эту ошибку
        else:
            raise ArithmeticError(f"Невязка получилась недопустимой, нужно делать перезамеры \nДопустимая: {self.permissible_discrepancy}\nВычисленная: {self.difference}")
        
        if self.calc_sum_of_practice_angles(self.fixed_angles).DD != self.theoretical_sum_angles.DD:    # Избыточная проверка, но на всякий случай пусть будет. Задаться вопросом, как лучше сделать такую ошибку в несколько строк
            raise ArithmeticError(f'''Исправленные горизонтальные углы не равны теоретическим
Теория: {self.theoretical_sum_angles}
Практика исправленная: {self.calc_sum_of_practice_angles(self.fixed_angles)}''')
        
        self.all_bearing_angles = self.calc_all_bearing_angles(self.bearing_angle, list(self.fixed_angles.values()))
        
        if self.bearing_angle.DD != self.all_bearing_angles[-1].DD:
            raise ArithmeticError("Последний вычисленный дир. угол не сошёлся с исходным, надо бы что-то сделать")
        
        self.practice_coordinate_increments, self.sum_calculated_coordinate_increments, self.difference_increments, self.difference_abs, self.difference_relative, self.coordinate_increment_correct, self.sum_corrected_coordinate_increments, self.all_coords = self.calc_coordinate_increments()
        
        # self.all_points = [Point(self.fixed_angles.get(i), self.all_distance[i], self.all_bearing_angles[i]) for i in range(len(self.angles))]    # type: ignore
    
    
    def get_help_side(self) -> str:
        '''
        В зависимости от того, какие снимались Левые/Правые углы по ходу движения и в какую часовую сторону шёл полигон надо вычислить вспомогательную сторону, что б понимать, по какой формуле вычислять теоретическую сумму горизонтальных углов.
        '''
        direction_of_circling = self.all_data.get('direction_of_circling')
        side_of_angles = self.all_data.get('side_of_angles')
        help_side = "Not calc"
        
        if direction_of_circling == 'right' and side_of_angles == 'right' or direction_of_circling == 'left' and side_of_angles == 'left': 
            help_side = 'inner'
        elif direction_of_circling == 'right' and side_of_angles == 'left' or direction_of_circling == 'left' and side_of_angles == 'right':
            help_side = 'outer'
        
        return help_side
    
    
    def calc_sum_of_theoretical_angles(self):
        '''
        Рассчитываю теоретическую сумму гор. углов исходя из количества пунктов, где были взяты измерения углов и исходя из того, какие углы это получились, внешние или внутренние
        '''
        
        n =  len(self.angles)
        help_side = self.get_help_side()
        res = 180 * (n - 2) if help_side == 'inner' else 180 * (n + 2)
        
        return Angle(DD=res)
        
    
    def calc_sum_of_practice_angles(self, angles):
        '''
        Расситываю практическую сумму гор. углов. Считаю в DD
        '''
        
        sum_angles = sum([a.DD for a in angles.values()])
        
        return Angle(DD=sum_angles)
    
    
    def calc_permissible_discrepancy(self, n: int, accuracy: int = 30):
        ''' Посчитать допустимую невязку хода.
        Она зависит от ПРИБОРА, которым измеряют (двойная точность прибора) и от количества углов. Вдруг понадобится менять значение - я напишу параметр, но задам дефолтное значение 1 МИНУТУ, это для Т30. От того, какую величину пишут, будет зависеть то, в какой величине получается допуск. Если 1 минута, значит допуск в минутах, иначе в секундах. '''
        # res = Angle(DD=((2 * Angle(0, 0, 30).DD) * sqrt(n)))
        
        return Angle(DD=((2 * Angle(0, 0, 30).DD) * sqrt(n)))
    
    
    def calc_and_send_amendment(self, difference):
        '''
        В этой функции сравниваю невязку с количеством углов и принимаю решение - каким методом раскидывать невязку.
        Попарвка как будто не должна быть меньше точности измерения горизонтальных углов... Т.е. как будто тоже от прибора зависит О_о
        Грубо говоря, если измеряли с помощью 2Т30, то не имеет смысла вкидывать поправку 2" и даже 1", но просто на данном этапе это довольно простой вариант.
        '''
        
        sort_perim = dict(sorted(self.angles.items(), key=lambda x: x[1].DD, reverse=True))
        
        one_sec = Angle(0, 0, 1).DD
        correction_in_each_corner = difference.DD / len(self.angles)
        
        
        if abs(correction_in_each_corner) < one_sec and difference.DD != 0:
            ''' Если секунд меньше чем количество углов (значит в сравнении получится величина меньше чем одна секунда) - надо раскидать по одной секунде начиная с бОльшего по величине угла в полигоне '''
            sort_index_angles = list(sort_perim.keys())
            for i in range(abs(int(difference.DD / one_sec))):
                ''' Посчитано сколько раз надо раскидать одну секунду в углы и раскидывается '''
                self.fixed_angles[sort_index_angles[i]] += one_sec if difference.DD > 0 else -one_sec
            
            # Попробовать на исходных данных, где не надо будет из этого условия раскидывать. И проверить там, где большая невязка, что б она сразу за одно условие не раскидалась
            new_diffrerence = Angle(DD=(self.theoretical_sum_angles.DD - self.calc_sum_of_practice_angles(self.fixed_angles).DD))  # Невязка
            self.calc_and_send_amendment(new_diffrerence)
        elif abs(correction_in_each_corner) > one_sec:
            ''' Сначала поровну раскидаю секунды, а потом снова вызову эту функцию для проверки
            Во избежании неправильной раскидки я буду вычислять сколько градусов надо вкидывать через обычное деление, получу DD, а после сделаю из него угол и и возьму DD уже из угла, чаще всего он будет меньше, чем получилось при делении.
            '''
            
            need_correct = Angle(DD=correction_in_each_corner)
            for i in self.fixed_angles:
                self.fixed_angles[i] += need_correct.DD
            
            new_diffrerence = Angle(DD=(self.theoretical_sum_angles.DD - self.calc_sum_of_practice_angles(self.fixed_angles).DD))  # Невязка
            self.calc_and_send_amendment(new_diffrerence)
        else: ...
            # print("3", difference, "Невязку не надо раскидывать")
            # print("Sum of fixed ang", self.calc_sum_of_practice_angles(self.fixed_angles))
    
    
    def calc_all_bearing_angles(self, start_bearing, correct_angles): #side: str ='right'):
        '''Посчитать все дирекционные углы, исходя из того, какой начальный дир.угол и какие исправленные углы были получены. Учитывается сторона, с который проводились вычисления относительно хода полигона.'''
        
        previous_bearing = start_bearing
        bearingAngles = []  # Возможно чтобы не создавать такие списки и не возвращать их потом, делают генераторы?
        side = self.all_data.get('side_of_angles')
        # print(previous_bearing, type(previous_bearing))
        # print(correct_angles[0])
        
        for ang in correct_angles:
            match side:
                case "right":
                    present_bearing = previous_bearing + 180.0 - ang.DD  # type: ignore
                case "left":
                    present_bearing = previous_bearing - 180.0 + ang.DD  # type: ignore
            bearingAngles.append(present_bearing)   # type: ignore
            previous_bearing = present_bearing      # type: ignore
        
        return bearingAngles
    
    
    def calc_coordinate_increments(self):
        perimetr = sum(self.all_distance)
        # print(self.all_bearing_angles)
        # print(self.all_distance)
        
        coordinate_increments = [(math.cos(math.radians(self.all_bearing_angles[i].DD)) * self.all_distance[i], 
                                  math.sin(math.radians(self.all_bearing_angles[i].DD)) * self.all_distance[i]) 
                                 for i in range(len(self.all_distance))]
        
        sum_calculated_coordinate_increments = (sum([d[0] for d in coordinate_increments]), 
                                                sum([d[1] for d in coordinate_increments]))          # Просто просуммировал вычисленыне приращения
        
        difference_increments = (self.sum_theoretical_coordinate_increments[0] - sum_calculated_coordinate_increments[0], 
                                 self.sum_theoretical_coordinate_increments[1] - sum_calculated_coordinate_increments[1])  # Теория - практика, что б в следующих вычислениях не пришлось брать невязку с обратным знаком...
        
        difference_abs = math.hypot(difference_increments[0], difference_increments[1]) # fабс По моему вычисление квадрата суммы переменных
        difference_relative = (difference_abs / perimetr, 1 / (difference_abs / perimetr)) # fотн Сразу перевёл в удобный вариант масштаба, там всё зависит от разряда теодолитного хода, вот относительно разряда не должно превышать это число. Типа если это условие будет выполняться, то можно приступать к вычислению исправленных приращений координат. Возможно в будущем надо будет придумать эту проверку. ❓ Если число получается больше 0.0005 (это первый разряд или технический? у нас так же на первом курсе было. В интернете написано, что 1й разряд 1:2000, 2й разряд 1:1000), например, 0.00019, то значит это хорошо
        assert difference_relative[0] <= 1 / 2000, f"Относительная невязка не меньше 1:2000, что является допуском линейной невязки для теодолитного хода 1го разряда, что-то сделать с этим надо. По идее только перемерять расстояния в поле?\nВот вычисленные значения: {difference_relative}"
        
        coordinate_increment_correct = [(coordinate_increments[i][0] + (difference_increments[0] * self.all_distance[i] / perimetr),
                                         coordinate_increments[i][1] + (difference_increments[1] * self.all_distance[i] / perimetr)) 
                                        for i in range(len(coordinate_increments))]
        
        sum_corrected_coordinate_increments = (sum([c[0] for c in coordinate_increment_correct]),
                                           sum([c[1] for c in coordinate_increment_correct]))
        
        assert tuple([round(n, 3) for n in sum_corrected_coordinate_increments]) == tuple([round(n, 3) for n in self.sum_theoretical_coordinate_increments]), f"Исправленные приращения координат не равны теоретическим, надо проверить...\nТеория: {self.sum_theoretical_coordinate_increments}\nПрактика исправленная: {sum_corrected_coordinate_increments}"
        
        all_coords = self.calc_all_coordinates(coordinate_increment_correct)
        
        assert all_coords[-1] == self.initial_coords[-1], f'Вычисленные координаты конечной точки не равны переданной конечной, надо проверить вычисления.\nПереданные: {self.initial_coords[-1]}\nВычисленные: {all_coords[-1]}'
            
        return coordinate_increments, sum_calculated_coordinate_increments, difference_increments, difference_abs, difference_relative, coordinate_increment_correct, sum_corrected_coordinate_increments, all_coords
    
    
    def calc_all_coordinates(self, increment_correct) -> list[tuple[float, float]]:
        '''Посчитаю все координаты, которые надо посчитать, объединю с исходными и верну в скрипт для передачи'''
        
        prev_coord = self.initial_coords[0]
        # Поиск разрядности цифр после запятой в исходных данных
        discharge = str(prev_coord[0])
        discharge = len(discharge[discharge.find('.')+1:])
        coords = [self.initial_coords[0]]   # Или возможно этого делать не надо, т.к. на фронт я хотел бы возвращать только те координаты, которые вычислялись... Или пофиг?
        
        for inc in increment_correct:
            calculated_coords = (prev_coord[0] + inc[0], prev_coord[1] + inc[1])    # Я тут получаю координату точки и сразу округляю и дальше передаю округлённое значение... Хотя так делать не следует, считать будто надо без округлённых значений, уже потом для сравнения и вывода координат всё округлить. Осталось ввести атрибут, который будет отвечать за то, до какого разряда надо округлять. Либо автоматом это научиться проверять на основании переданных координат
            coords.append(calculated_coords)
            prev_coord = calculated_coords
        
        coords = [(round(tup[0], discharge), round(tup[1], discharge)) for tup in coords]
        
        return coords


class Angle:
    def __init__(self, D: int=0, M: int=0, S: int=0, DD: float|None=None):
        '''
        Происходит инициализация угла и горизонтальное проложение до следующего угла
        Передаётся градус, минута, секунда и дистанция до следующего пункта
        
        Возможно надо накинуть проверку передаваемых аргументов, что б они не были сверхнормы, что б не допускать ошибочнопереданных чисел
        '''
        if DD:
            self.DD = DD
            # self.DD = round(DD, 12)    # Вычисления будут идти без округлений. Из этих вычислений будут получаться ДМС. Округление навесил из-за суммы углов.
            self.convert_to_DMS()
            self.DD = self.convert_to_DD()  # А уже после получения ДМС пересчитаю ДД, что б всё верно хранилось, без лишней херни
        else:
            self.D = D
            self.M = M
            self.S = S
            self.DD = self.convert_to_DD()
    
    @property
    def D(self):
        return self._D
    
    @D.setter
    def D(self, D):
        self._D = D
    
    @property
    def M(self):
        return self._M
    
    @M.setter
    def M(self, M):
        if M >= 60:
            self._M = M % 60
            self._D += M // 60
        else:
            self._M = M
    
    @property
    def S(self):
        return self._S
    
    @S.setter
    def S(self, S):
        if S >= 60:
            self._S = S % 60
            self.M += S // 60
        else:
            self._S = S
    
    @property
    def DD(self):
        return self._DD
    
    @DD.setter
    def DD(self, DD):
        self._DD = DD
    
    
    def convert_to_DD(self) -> float:
        ''' из гр/мин/сек раскладываю в десятичный угол без округления, что б не запортачить дальнейшие вычисления '''
        
        return self.D + self.M / 60 + self.S / 3600
    
    
    def __add__(self, angle_DD: float):
        if not isinstance(angle_DD, float):
            raise ArithmeticError("Правый операнд должен быть типом float")
        
        return Angle(DD=self.DD + angle_DD)
    
    
    def __sub__(self, angle_DD: float):
        if not isinstance(angle_DD, float):
            raise ArithmeticError("Правый операнд должен быть типом float")
        
        return Angle(DD=self.DD - angle_DD)
    
    
    def __str__(self):
        return f'{self.D}°{self.M}\'{self.S}"'
    
    
    def __repr__(self):
        ''' Чтобы и при обычном печатании списка, где находятся эти углы печаталось красиво '''
        
        return f'{self.D}°{self.M}\'{self.S}"'
    
    
    def convert_to_DMS(self):
        ''' 
        из десятичного угла получается гр/мин/сек 
        '''
        
        DD = self.DD
        self.D = int(DD)
        self.M = int((DD - self.D) * 60)
        self.S = int(round((DD - self.D - self.M / 60) * 3600, 0))


class BearingAngle(Angle):
    ''' 
    Новый класс для дир. угла. Он должен быть не больше 360° 
    '''
    
    @property
    def DD(self):
        return self._DD
    
    @DD.setter
    def DD(self, DD):
        if DD > 360:
            self._DD = DD - 360
        elif DD < 0:
            self._DD = DD + 360
        else:
            self._DD = DD
    
    
    def __add__(self, angle_DD: float):
        if not isinstance(angle_DD, float):
            raise ArithmeticError("Правый операнд должен быть типом float")
        
        return BearingAngle(DD=self.DD + angle_DD)
    
    
    def __sub__(self, angle_DD: float):
        if not isinstance(angle_DD, float):
            raise ArithmeticError("Правый операнд должен быть типом float")
        
        return BearingAngle(DD=self.DD - angle_DD)


class Coords:
    def __init__(self, x: float, y: float):
        self.X = x
        self.Y = y
    
    @property
    def X(self):
        return self._x
    
    @X.setter
    def X(self, value: float):
        self._x = value
    
    @property
    def Y(self):
        return self._y
    
    @Y.setter
    def Y(self, value: float):
        self._y = value
    
    
    def __str__(self):
        return f'({self.X}м, {self.X}м)'


    def __repr__(self):
        return f'({self.X}м, {self.X}м)'


class Point:
    ID = 0
    
    def __init__(self, angle: Angle, distance: float, bearing_angle: BearingAngle):
        ''' Точка стояния. На ней измерен горизонтальный угол, дистанция, возможно дир. угол. И возможно координаты уже известны 
        Все точки нумеруются, начиная от нуля (вторая исходная точка, после неё должна идти сразу 1), последняя точка по счёту должна будет быть первой исходной
        От первой на вторую исходную точку известна сторона и дир.угол 
        Тут должна будет быть проверка на то, что на точке стояния угол не может быть больше 360 градусов, иначе генерить ошибку'''
        
        self.id = Point.ID
        self.angle = angle
        self.distance = distance
        self.bearing_angle = bearing_angle
        
        Point.ID += 1
        
    @property
    def bearing_angle(self):
        if hasattr(self, '_bearing_angle'):
            return self._bearing_angle
    
    @bearing_angle.setter
    def bearing_angle(self, angle: BearingAngle):
        self._bearing_angle = angle
    
    @property
    def coords(self):
        if hasattr(self, '_coords'):
            return self._coords
    
    @coords.setter
    def coords(self, coords):
        self._coords = coords
    
    # Написать все варианты шаблонов для печатанья в словарике и просто вызывать именно ту строку, которая подходит, по увеличению будет идти, если вообще смысл есть.
    def __str__(self):
        match self.bearing_angle:
            case bearing if bearing:
                return f'|{self.angle}, {self.distance}м, {bearing}|'
            case _:
                return f'|{self.angle}, {self.distance}м|'
        
        # return f'{self.angle}, {self.distance}м, {self.a}'


    def __repr__(self):
        match self.bearing_angle:
            case bearing if bearing:
                return f'|{self.angle}, {self.distance}м, {bearing}|'
            case _:
                return f'|{self.angle}, {self.distance}м|'


class DB:
    def __init__(self, path: str):
        '''
        Инициализирую "соединение" с уловной БД, передаю туда путь до файла с input данными
        ?поработать тут с объектом Path?
        Отсюда я буду вызывать что-то типа p = Polygon(3, True), при получении данных и тут же будет метод отдачи данных, его конвертация в нужный вид и передача на фронт и всякое такое
        '''
        
        self.path = path

    
    def get_all_data(self) -> dict:
        '''
        Прочитаю JSON, отдам все данные в переменную, это будет словарик, по идее?
        '''
        
        with open(self.path, "r", encoding="utf-8") as f:
            return json.loads(f.read())
    
    
        
        


if __name__ == '__main__':
    p = Polygon(5, True)
    ...