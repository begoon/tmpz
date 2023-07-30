print('I am on!')

n = 256

M = 1 * 1024 * 1024
while True:
    mem = 'x' * (n * M)
    sz = len(mem)
    print(f'{n}M')
    input()
    del mem
    n *= 2
