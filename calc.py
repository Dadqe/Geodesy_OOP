from math import sqrt
import json
import math


class Polygon1:
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
        self.initial_coords = self.all_data.get('coords')
        self.help_side = self.get_help_side()   # ?Может это и не надо в атрибут прям вычислять, а лучше при вычислении теоретической суммы горизонтальных углов вычислить разок и всё.
        
        # self.angles = [Angle(d.get('Deg'), d.get('Min'), d.get('Sec'), d.get('HorDist')) for d in self.measured_angles]   # type: ignore # Будет храниться список углов, экземпляры Angle
        self.angles = {i: Angle(d.get('Deg'), d.get('Min'), d.get('Sec'), d.get('HorDist')) for i, d in enumerate(self.measured_angles)} # type: ignore
        self.theoretical_sum_angles = self.calc_sum_of_theoretical_angles()  # теоретическая сумма углов, нужно будет рассчитывать, когда заполнится массив углов
        self.practical_sum_angles = self.calc_sum_of_practice_angles(self.angles)  # практическая сумма углов, просто посчитать сумму углов в массиве
        self.difference = Angle(DD=(self.theoretical_sum_angles.DD - self.practical_sum_angles.DD))  # Невязка
        # self.difference = Angle(DD=self.difference.DD * 4) # Для тестов бОльших значений невязки для метода calc_and_send_amendment. После отладки закомментить/удалить
        
        self.sort_perim = dict(sorted(self.angles.items(), key=lambda x: x[1].DD, reverse=True))
        self.fixed_angles = self.angles.copy()
        
        self.c = 0  # поправку посчитать
        self.d = 0  # может почситать невязку для угла
        
    
    
    
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
    
    
    def calc_and_send_amendment(self, difference):
        '''
        В этой функции сравниваю невязку с количеством углов и принимаю решение - каким методом раскидывать невязку.
        '''
        
        one_sec = Angle(0, 0, 1).DD
        correction_in_each_corner = difference.DD / len(self.angles)   # Считаю в DD какой угол надо раскидывать в каждый угол.
        
        # print(difference.DD / one_sec)
        if correction_in_each_corner < one_sec and difference.DD != 0:
            ''' Если секунд меньше чем количество углов (значит в сравнении получится величина меньше чем одна секунда) - надо раскидать по одной секунде начиная с бОльшего по величине угла в полигоне '''
            print("1", difference)
            sort_index_angles = list(self.sort_perim.keys())
            
            for i in range(int(difference.DD / one_sec)):
                ''' Посчитано сколько раз надо раскидать одну секунду в углы и раскидывается '''
                # print("old", self.fixed_angles[sort_index_angles[i]])
                self.fixed_angles[sort_index_angles[i]] += one_sec
                # print("new", self.fixed_angles[sort_index_angles[i]])
            
            # Попробовать на исходных данных, где не надо будет из этого условия раскидывать. И проверить там, где большая невязка, что б она сразу за одно условие не раскидалась
            print("Вызываю ещё раз функцию раскидки поправок")
            new_diffrerence = Angle(DD=(self.theoretical_sum_angles.DD - self.calc_sum_of_practice_angles(self.fixed_angles).DD))  # Невязка
            self.calc_and_send_amendment(new_diffrerence)
        elif correction_in_each_corner > one_sec:
            ''' Сначала поровну раскидаю секунды, а потом снова вызову эту функцию для проверки
            Во избежании неправильной раскидки я буду вычислять сколько градусов надо вкидывать через обычное деление, получу DD, а после сделаю из него угол и и возьму DD уже из угла, чаще всего он будет меньше, чем получилось при делении.
            '''
            print("2", difference)
            
            need_correct = Angle(DD=correction_in_each_corner)
            for i in self.fixed_angles:
                self.fixed_angles[i] += need_correct.DD
            
            print("Вызываю ещё раз функцию раскидки поправок")
            new_diffrerence = Angle(DD=(self.theoretical_sum_angles.DD - self.calc_sum_of_practice_angles(self.fixed_angles).DD))  # Невязка
            self.calc_and_send_amendment(new_diffrerence)
            
        else:
            print("3", difference, "Невязку не надо раскидывать")
            print(self.calc_sum_of_practice_angles(self.fixed_angles))
        

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
        self.initial_coords = self.all_data.get('coords')
        self.help_side = self.get_help_side()   # ?Может это и не надо в атрибут прям вычислять, а лучше при вычислении теоретической суммы горизонтальных углов вычислить разок и всё.
        
        # self.angles = [Angle(d.get('Deg'), d.get('Min'), d.get('Sec'), d.get('HorDist')) for d in self.measured_angles]   # type: ignore # Будет храниться список углов, экземпляры Angle
        self.angles = {i: Angle(d.get('Deg'), d.get('Min'), d.get('Sec')) for i, d in enumerate(self.measured_angles)} # type: ignore
        self.theoretical_sum_angles = self.calc_sum_of_theoretical_angles()  # теоретическая сумма углов, нужно будет рассчитывать, когда заполнится массив углов
        self.practical_sum_angles = self.calc_sum_of_practice_angles(self.angles)  # практическая сумма углов, просто посчитать сумму углов в массиве
        self.difference = Angle(DD=(self.theoretical_sum_angles.DD - self.practical_sum_angles.DD))  # Невязка
        # self.difference = Angle(DD=self.difference.DD * 4) # Для тестов бОльших значений невязки для метода calc_and_send_amendment. После отладки закомментить/удалить
        
        self.sort_perim = dict(sorted(self.angles.items(), key=lambda x: x[1].DD, reverse=True))
        self.fixed_angles = self.angles.copy()
        
        self.c = 0  # поправку посчитать
        self.d = 0  # может почситать невязку для угла
        
    
    
    
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
    
    
    def calc_and_send_amendment(self, difference):
        '''
        В этой функции сравниваю невязку с количеством углов и принимаю решение - каким методом раскидывать невязку.
        '''
        
        one_sec = Angle(0, 0, 1).DD
        correction_in_each_corner = difference.DD / len(self.angles)
        
        if abs(correction_in_each_corner) < one_sec and difference.DD != 0:
            ''' Если секунд меньше чем количество углов (значит в сравнении получится величина меньше чем одна секунда) - надо раскидать по одной секунде начиная с бОльшего по величине угла в полигоне '''
            print("1", difference)
            sort_index_angles = list(self.sort_perim.keys())
            print(abs(int(difference.DD / one_sec)))
            for i in range(abs(int(difference.DD / one_sec))):
                ''' Посчитано сколько раз надо раскидать одну секунду в углы и раскидывается '''
                # print("old", self.fixed_angles[sort_index_angles[i]])
                self.fixed_angles[sort_index_angles[i]] += one_sec if difference.DD > 0 else -one_sec
                # print("new", self.fixed_angles[sort_index_angles[i]])
            
            # Попробовать на исходных данных, где не надо будет из этого условия раскидывать. И проверить там, где большая невязка, что б она сразу за одно условие не раскидалась
            print("Вызываю ещё раз функцию раскидки поправок")
            new_diffrerence = Angle(DD=(self.theoretical_sum_angles.DD - self.calc_sum_of_practice_angles(self.fixed_angles).DD))  # Невязка
            self.calc_and_send_amendment(new_diffrerence)
            # print("new dif", new_diffrerence)
        elif abs(correction_in_each_corner) > one_sec:
            ''' Сначала поровну раскидаю секунды, а потом снова вызову эту функцию для проверки
            Во избежании неправильной раскидки я буду вычислять сколько градусов надо вкидывать через обычное деление, получу DD, а после сделаю из него угол и и возьму DD уже из угла, чаще всего он будет меньше, чем получилось при делении.
            '''
            print("2", difference)
            
            need_correct = Angle(DD=correction_in_each_corner)
            for i in self.fixed_angles:
                self.fixed_angles[i] += need_correct.DD
            
            print("Вызываю ещё раз функцию раскидки поправок")
            new_diffrerence = Angle(DD=(self.theoretical_sum_angles.DD - self.calc_sum_of_practice_angles(self.fixed_angles).DD))  # Невязка
            self.calc_and_send_amendment(new_diffrerence)
            # print("new dif", new_diffrerence)
            
        else:
            print("3", difference, "Невязку не надо раскидывать")
            print(self.calc_sum_of_practice_angles(self.fixed_angles))


class Angle:
    def __init__(self, D: int=0, M: int=0, S: int=0, DD: float|None=None):
        '''
        Происходит инициализация угла и горизонтальное проложение до следующего угла
        Передаётся градус, минута, секунда и дистанция до следующего пункта
        
        Возможно надо накинуть проверку передаваемых аргументов, что б они не были сверхнормы, что б не допускать ошибочнопереданных чисел
        '''
        if DD:
            self.DD = DD    # Вычисления будут идти без округлений. Из этих вычислений будут получаться ДМС
            self.D, self.M, self.S = self.convert_to_DMS(self.DD)
            self.DD = self.convert_to_DD()  # А уже после получения ДМС пересчитаю ДД, что б всё верно хранилось, без лишней херни
        else:
            self.D = D
            self.M = M
            self.S = S
            self.DD = self.convert_to_DD()
    
    
    def convert_to_DD(self) -> float:
        ''' из гр/мин/сек раскладываю в десятичный угол без округления, что б не запортачить дальнейшие вычисления '''
        
        return self.D + self.M / 60 + self.S / 3600
    
    
    def recalc_DMS(self):
        ''' Пересчитаю DMS. Понадобится тогда, когда DD изменится в рамках добавления поправки, например. '''
        
        self.D, self.M, self.S = self.convert_to_DMS(self.DD)
    
    
    def __add__(self, angle_DD: float):
        if not isinstance(angle_DD, float):
            raise ArithmeticError("Правый операнд должен быть типом float")
        
        return Angle(DD=self.DD + angle_DD)
    
    
    def __str__(self):
        return f'{self.D}°{self.M}\'{self.S}"'
    
    
    def __repr__(self):
        ''' Чтобы и при обычном печатании списка, где находятся эти углы печаталось красиво '''
        
        return f'{self.D}°{self.M}\'{self.S}"'
    
    
    @staticmethod
    def convert_to_DMS(DD: float):
        ''' 
        из десятичного угла получается гр/мин/сек 
        '''
        
        d = int(DD)
        m = int((DD - d) * 60)
        s = int(round((DD - d - m / 60) * 3600, 0))
        
        return (d, m, s)


class Point:
    def __init__(self, id: int, angle: Angle, distance: float):
        ''' Точка стояния. На ней измерен горизонтальный угол, дистанция, возможно дир. угол. И возможно координаты уже известны 
        Все точки нумеруются, начиная от нуля (вторая исходная точка, после неё должна идти сразу 1), последняя точка по счёту должна будет быть первой исходной
        От первой на вторую исходную точку известна сторона и дир.угол 
        Тут должна будет быть проверка на то, что на точке стояния угол не может быть больше 360 градусов, иначе генерить ошибку'''
        
        self.angle = angle
        self.distance = distance
        self.bearing_angle = 0  # Написать сеттеры внутри, будут назначаться только для первой и последней точки, а потом при вычислении в конце
        self.coords = ()


class DB:
    def __init__(self, path: str):
        '''
        Инициализирую "соединение" с уловной БД, передаю туда путь до файла с input данными
        ?поработать тут с объектом Path?
        '''
        
        self.path = path

    
    
    def get_all_data(self) -> dict:
        '''
        Прочитаю JSON, отдам все данные в переменную, это будет словарик, по идее?
        '''
        
        with open(self.path, "r", encoding="utf-8") as f:
            return json.loads(f.read())
    
    
        
        


if __name__ == '__main__':
    p = Polygon(6, True)
    # Проверяю раскидку невязки
    print(p.angles)
    print(p.sort_perim)
    print(p.theoretical_sum_angles.DD)
    print(p.practical_sum_angles.DD)
    print(p.difference)
    # a = Angle(0, 3, 0)
    # a1 = Angle(0, 3, 1)
    # a2 = Angle(0, -3, -1)
    # print(-a.DD)
    # print(a)
    # a += a1.DD if p.difference.DD > 0 else -a1.DD
    # print(a)
    p.calc_and_send_amendment(p.difference)
    # print(p.fixed_angles)
    ...