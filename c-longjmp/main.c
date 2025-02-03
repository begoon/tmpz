#include <stdio.h>
#include <setjmp.h>

jmp_buf buffer;

void second()
{
    printf("> second(), now jumping back\n");
    longjmp(buffer, 1);
    printf("! second: never be printed\n");
}

void first()
{
    printf("> first(), calling second()\n");
    second();
    printf("! first: never be printed!\n");
}

int main()
{
    if (setjmp(buffer) == 0)
    {
        printf("calling first()\n");
        first();
    }
    else
    {
        printf("back in main() after longjmp\n");
    }
    printf("program continues normally\n");
    return 0;
}
