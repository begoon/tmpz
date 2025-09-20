#include <stdio.h>

int main()
{
    auto n = printf("abc\n");
    _Generic(n, int: printf("int\n"), default: printf("other\n"));
    return 0;
}