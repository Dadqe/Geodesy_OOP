class Angle:
    def __init__(self, D: int=0, M: int=0, S: int=0, DD: float|None=None):
        '''
        Происходит инициализация угла и горизонтальное проложение до следующего угла
        Передаётся градус, минута, секунда и дистанция до следующего пункта
        
        Возможно надо накинуть проверку передаваемых аргументов, что б они не были сверхнормы, что б не допускать ошибочнопереданных чисел
        '''
        if DD:
            self.DD = DD    # Вычисления будут идти без округлений. Из этих вычислений будут получаться ДМС
            self.convert_to_DMS()
            # self.D, self.M, self.S = self.convert_to_DMS(self.DD)
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
        self._M = M
    
    @property
    def S(self):
        return self._S
    
    @S.setter
    def S(self, S):
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
        
        return Angle(DD=round(self.DD, 12) + round(angle_DD, 12))
    
    
    def __str__(self):
        return f'{self.D}°{self.M}\'{self.S}"'
    
    
    def __repr__(self):
        ''' Чтобы и при обычном печатании списка, где находятся эти углы печаталось красиво '''
        
        return f'{self.D}°{self.M}\'{self.S}"'
    
    
    def convert_to_DMS(self):
        ''' 
        из десятичного угла получается гр/мин/сек 
        '''
        
        self.D = int(self.DD)
        self.M = int((self.DD - self.D) * 60)
        self.S = int(round((self.DD - self.D - self.M / 60) * 3600, 0))


# b = Angle(DD=100)
b = Angle(2939, 59, 55)
print(b.DD)
b += Angle(0, 0, 5).DD
print(b)
# b_new = Angle(DD=round(b.DD, 9) + round(Angle(0, 0, 10).DD, 9))
alo = b.DD + Angle(0, 0, 10).DD
# print(alo)
# print(Angle(DD=alo + 0.0000000000004))
# print(Angle(DD=round(alo, 9)))
# print(b_new)
# print(b.DD)
# a = Angle(DD=2940)
# print(a.DD)
# a += -(Angle(0, 0, 10).DD)
# print(a.DD)
# print(a.DD == b.DD)
# 0.0000000000005
# 9.9999999999995