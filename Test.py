from calc import *


# a = Angle(5, 1, 11, 29.138)                     # init Angle
# a1 = Angle(DD=900.198470)                      # init Angle
# print(f'DD - {a.convert_to_DD()}')              # get DD
# print(f'DMS - {Angle.convert_to_DMS(a.DD)}')    # get DMS
# db = DB("Data/Input/DataInput6.json")
# p = Polygon(6, True)


# four_sec = Angle(0, 0, 9)  # difference
# one_sec = Angle(0, 0, 1)

# # print(p.difference.convert_to_DD())
# print(four_sec.convert_to_DD())
# print(one_sec.convert_to_DD())
# # r = p.difference.convert_to_DD() / 1

# r = four_sec.convert_to_DD() / 2
# print(r, r <= one_sec.convert_to_DD())

# dif = p.difference.DD
# one_sec = Angle(0, 0, 1).DD
# delenie = dif / one_sec

# print(dif * 8 / one_sec)

# Проверяю метод __add__ сложение
# one = Angle(0, 0, 3600)
# print(one)
# ten = Angle(0, 0, 10)
# print(ten.DD)
# eleven = one + ten.DD
# print(eleven, eleven.DD, eleven.DD == Angle(0, 0, 11).DD)

# print(Angle(DD=ten.DD / 4), Angle(DD=ten.DD / 4).DD)
# print(ten.DD / 4)

# print(one)
# print(one.DD)

# bb = Angle(DD=0.0001277777777777778)
# print(bb, bb.DD)

# one + one.DD
# print(one)
# d = p.difference.DD # 2
# print(d)
# print(d / one.DD)
# d = d * 3      # 6
# print(d)
# print(d / one.DD)
# d = d + one.DD      # 4
# print(d)
# print(d / one.DD)
# d = d + one.DD      # 5 косячится число, превращается не пойми во что
# print(d)
# print(d / one.DD)
# d = d + one.DD      # 6 косячится число, превращается не пойми во что
# print(d)
# print(d / one.DD)

# print(f"dif: {dif}")
# print(f"one_sec: {one_sec}")

# while dif:
#     print(dif)
#     dif -= one_sec

# dif = dif - one_sec
# dif = dif - one_sec
# print(dif)
# print(one_sec)

# calc()
# print(initial_perim)
# print(sort_perim)

# Проверяю раскидку невязки
# print(p.angles)
# print(p.sort_perim)
# p.calc_and_send_amendment(p.difference)
# print(p.fixed_angles)
# print(Angle(DD=2340.0))

# Переписываю принцип хранения углов на словарь через генератор словарей
# print(p.angles)
# print(p.angles1)

# # sum_angles = sum([a.convert_to_DD() for a in self.angles])
# print(sum([a.convert_to_DD() for a in p.angles1.values()]))

# проверяю сортировку словарей
# sort_perim = dict(sorted(p.angles.items(), key=lambda x: x[1].DD, reverse=True))
# print(sort_perim)
# sort_perim = dict(sorted(sort_perim.items()))
# print(sort_perim)


# a = 60
# b = 75
# с = b%a
# print(с)
# print(b % a)


l = [1, 2, 3, 4, 5]

for i in range(len(l)):
    print(l[i-1], l[i])