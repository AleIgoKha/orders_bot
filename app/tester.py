dct = {'a': 123}

list = [i for i in range(5)]

for i, j, in zip(list, dct):
    print(i, j)