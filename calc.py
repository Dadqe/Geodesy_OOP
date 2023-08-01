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
        # db = {'Answer': 'I have not get any data'}
        if from_local:
            db = DB(f"Data/Input/DataInput{data}.json")
        else:
            db = data
        
        self.all_data = db.get_all_data()   # type: ignore
        self.measured_angles = self.all_data.get('aPoints') 
        self.bearing_angle = self.all_data.get('bearingAngle')
        self.initial_coords = self.all_data.get('coords')
        self.help_side = self.get_help_side()   # ?Может это и не надо в атрибут прям вычислять, а лучше при вычислении теоретической суммы горизонтальных углов вычислить разок и всё.
        
        self.angles = [Angle(d.get('Deg'), d.get('Min'), d.get('Sec'), d.get('HorDist')) for d in self.measured_angles]   # type: ignore # Будет храниться список углов, экземпляры Angle
        self.theoretical_sum_angles = self.calc_sum_of_theoretical_angles()  # теоретическая сумма углов, нужно будет рассчитывать, когда заполнится массив углов
        self.practical_sum_angles = self.calc_sum_of_practice_angles()  # практическая сумма углов, просто посчитать сумму углов в массиве
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
        
        return res
        
    
    def calc_sum_of_practice_angles(self):
        '''
        Расситываю практическую сумму гор. углов. Считаю в DD
        '''
        
        sum_angles = sum([a.convert_to_DD() for a in self.angles])
        
        return Angle1(DD=sum_angles)


class Angle:
    def __init__(self, D: int, M: int, S: int, Distance: float=0):
        '''
        Происходит инициализация угла и горизонтальное проложение до следующего угла
        Передаётся градус, минута, секунда и дистанция до следующего пункта
        
        Возможно надо накинуть проверку передаваемых аргументов, что б они не были сверхнормы, что б не допускать ошибочнопереданных чисел
        '''
        
        self.D = D
        self.M = M
        self.S = S
        self.Distance = Distance
        self.DD = self.convert_to_DD()
        self.D_fixed = 0
        self.M_fixed = 0
        self.S_fixed = 0
        # фиксанутые, значит изменённые, значения уравненных углов... их надо будет в одну строку написать, использовать convert_to_DMS передав туда получаемый уравненный угол в DD
    
    
    def convert_to_DD(self):
        ''' из гр/мин/сек раскладываю в десятичный угол без округления, что б не запортачить дальнейшие вычисления '''
        
        return self.D + self.M / 60 + self.S / 3600
    
    
    def __str__(self):
        return f'{self.D}°{self.M}\'{self.S}" {self.Distance}'
    
    def __repr__(self):
        ''' Чтобы и при обычном печатании списка, где находятся эти углы печаталось красиво '''
        
        return f'{self.D}°{self.M}\'{self.S}" {self.Distance}'
    
    
    @staticmethod
    def convert_to_DMS(DD: float):
        ''' 
        из десятичного угла получается гр/мин/сек 
        '''
        
        d = int(DD)
        m = int((DD - d) * 60)
        s = int(round((DD - d - m / 60) * 3600, 0))
        
        return (d, m, s)


class Angle1:
    def __init__(self, D: int=0, M: int=0, S: int=0, Distance: float=0, DD: float|None=None):
        '''
        Происходит инициализация угла и горизонтальное проложение до следующего угла
        Передаётся градус, минута, секунда и дистанция до следующего пункта
        
        Возможно надо накинуть проверку передаваемых аргументов, что б они не были сверхнормы, что б не допускать ошибочнопереданных чисел
        '''
        if DD:
            self.DD = DD
            self.D, self.M, self.S = self.convert_to_DMS(self.DD)
        else:
            self.D = D
            self.M = M
            self.S = S
            self.DD = self.convert_to_DD()
        self.Distance = Distance
        self.D_fixed = 0
        self.M_fixed = 0
        self.S_fixed = 0
        # фиксанутые, значит изменённые, значения уравненных углов... их надо будет в одну строку написать, использовать convert_to_DMS передав туда получаемый уравненный угол в DD
    
    
    def convert_to_DD(self):
        ''' из гр/мин/сек раскладываю в десятичный угол без округления, что б не запортачить дальнейшие вычисления '''
        
        return self.D + self.M / 60 + self.S / 3600
    
    
    def __str__(self):
        return f'{self.D}°{self.M}\'{self.S}" {self.Distance}'
    
    def __repr__(self):
        ''' Чтобы и при обычном печатании списка, где находятся эти углы печаталось красиво '''
        
        return f'{self.D}°{self.M}\'{self.S}" {self.Distance}'
    
    
    @staticmethod
    def convert_to_DMS(DD: float):
        ''' 
        из десятичного угла получается гр/мин/сек 
        '''
        
        d = int(DD)
        m = int((DD - d) * 60)
        s = int(round((DD - d - m / 60) * 3600, 0))
        
        return (d, m, s)


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
    # a = Angle(5, 1, 11, 29.138)                     # init Angle
    # a1 = Angle1(DD=900.198470)                      # init Angle1
    # print(f'DD - {a.convert_to_DD()}')              # get DD
    # print(f'DMS - {Angle.convert_to_DMS(a.DD)}')    # get DMS
    # db = DB("Data/Input/DataInput6.json")
    p = Polygon(6, True)
    # print(p.theoretical_sum)
    print(p.practical_sum_angles)
    
    
    ...