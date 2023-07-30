unsigned char mem[0x10000];

int accumulate(unsigned char *addr, int sz)
{
    int sum = 0;
    for (int i = 0; i < sizeof(mem); i++)
        sum += mem[i];
    return sum;
}

char *upper(char *str, int sz)
{
    for (int i = 0; i < sz; i++)
        if (str[i] >= 'a' && str[i] <= 'z')
            str[i] -= 0x20;
    return str;
}
