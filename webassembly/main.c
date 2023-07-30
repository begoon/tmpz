unsigned char mem[0x10000];

const char *const upper(char *const str, const int sz)
{
    for (int i = 0; i < sz; i++)
        if (str[i] >= 'a' && str[i] <= 'z')
            str[i] -= 0x20;
    return str;
}
