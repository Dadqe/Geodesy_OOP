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
        self.initial_coords = self.all_data.get('coords')
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
    
    
    def calc_next_bearing(self, prev_bearing: float, corrected_angle: float, side: str ='right') -> float:
        '''Буду передавать предыдущий дирекционный угол и исправленный горизонтальный угол на пункте. Возвращать вычисленный дирекционный угол. Буду использовать это в цикле для добавления в список. Возможно использовать side что б использовать разные формулы для добавления исправленного горизонтального угла с различным знаком'''
        
        bearing = 0
        
        if side == 'right':
            if prev_bearing + 180 - corrected_angle < 0:
                bearing = prev_bearing + 180 - corrected_angle + 360
            elif prev_bearing + 180 - corrected_angle > 360:
                bearing = prev_bearing + 180 - corrected_angle - 360
            else:
                bearing = prev_bearing + 180 - corrected_angle
        elif side == 'left':
            if prev_bearing - 180 + corrected_angle < 0:
                bearing = prev_bearing - 180 + corrected_angle + 360
            elif prev_bearing - 180 + corrected_angle > 360:
                bearing = prev_bearing - 180 + corrected_angle - 360
            else:
                bearing = prev_bearing - 180 + corrected_angle
        
        return bearing


class Angle:
    def __init__(self, D: int=0, M: int=0, S: int=0, DD: float|None=None):
        '''
        Происходит инициализация угла и горизонтальное проложение до следующего угла
        Передаётся градус, минута, секунда и дистанция до следующего пункта
        
        Возможно надо накинуть проверку передаваемых аргументов, что б они не были сверхнормы, что б не допускать ошибочнопереданных чисел
        '''
        if DD:
            self.DD = round(DD, 12)    # Вычисления будут идти без округлений. Из этих вычислений будут получаться ДМС. Округление навесил из-за суммы углов.
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


class Point:
    ID = 0
    
    def __init__(self, angle: Angle, distance: float):
        ''' Точка стояния. На ней измерен горизонтальный угол, дистанция, возможно дир. угол. И возможно координаты уже известны 
        Все точки нумеруются, начиная от нуля (вторая исходная точка, после неё должна идти сразу 1), последняя точка по счёту должна будет быть первой исходной
        От первой на вторую исходную точку известна сторона и дир.угол 
        Тут должна будет быть проверка на то, что на точке стояния угол не может быть больше 360 градусов, иначе генерить ошибку'''
        
        self.id = Point.ID
        self.angle = angle
        self.distance = distance
        
        Point.ID += 1
        
    @property
    def bearing_angle(self):
        if hasattr(self, '_bearing_angle'):
            return self._bearing_angle
        # else:
        #     return None
    
    @bearing_angle.setter
    def bearing_angle(self, angle: BearingAngle):
        self._bearing_angle = angle
    
    
    def __str__(self):
        # match self.a:
        match self.bearing_angle:
            case bearing if bearing:
                return f'{self.angle}, {self.distance}м, {bearing}'
            case _:
                return f'{self.angle}, {self.distance}м'
        
        # return f'{self.angle}, {self.distance}м, {self.a}'


    def __repr__(self):
        return f'{self.angle}, {self.distance}м'


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
    # p = Polygon(3, True)
    # Проверяю раскидку невязки
    # print(p.angles)
    # print(p.sort_perim)
    # print(p.theoretical_sum_angles)
    # print(p.practical_sum_angles)
    # print(p.difference)
    # p.calc_and_send_amendment(p.difference)
    # print(p.fixed_angles)
    # a = Angle(0, 3, 0)
    # a1 = Angle(0, 3, 1)
    # a2 = Angle(0, -3, -1)
    # print(-a.DD)
    # print(a)
    # a += a1.DD if p.difference.DD > 0 else -a1.DD
    # print(a)
    # b = Angle(2939, 59, 50)
    # b += Angle(0, 0, 10).DD
    # print(b)
    # print(p.fixed_angles)
    
    # one = Angle(0, 0, 50)
    
    # print(one)
    # two = one + Angle(0, 0, 10).DD
    # print(two)
    
    # print(p.bearing_angle)
    
    # a = Angle(DD=375)
    b = BearingAngle(DD=350)
    b += Angle(35, 0, 0).DD
    
    # print(b.DD)
    
    # c = Point(a, 100)
    # c.bearing_angle = b
    # print(c)
    
    # c1 = Point(b, 100)
    # print(c1)
    
    ...