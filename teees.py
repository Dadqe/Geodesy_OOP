a = [0, 1, 2, 3, 4, 5, 6]
b = ["a", "b", "c", "d", "e", "f"]
c = ["aa", "ab", "ac", "ad", "ae", "af"]

out = {a[i]: [b[i], c[i]] for i in range(len(a)-1)}
print(out)