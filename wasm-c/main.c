#include <stdint.h>

// Provided by the linker, marks where we can start allocating.
extern unsigned char __heap_base;

// Bump pointer for very simple allocation from JS-land.
static uint32_t bump_ptr = 0;

// Export an allocator so JS can reserve space inside wasm memory.
uint32_t alloc(uint32_t n)
{
    if (bump_ptr == 0)
    {
        bump_ptr = (uint32_t)(uintptr_t)&__heap_base;
    }
    // 8-byte align
    const uint32_t ptr = bump_ptr;
    bump_ptr = (ptr + n + 7u) & ~7u;
    return ptr;
}

int native_function(int x, int *y, char *s)
{
    int sz = 0;
    while (s[sz] != 0)
    {
        sz += 1;
    }

    int sum = x + *y;
    *y = sum + sz;

    return sz;
}

uint32_t native_string(uint64_t val)
{
    static char hex[] = "0123456789ABCDEF";

    const uint32_t ptr = alloc(18); // "0x" + 16 chars + null terminator
    char *p = (char *)(uintptr_t)ptr;
    p[0] = '0';
    p[1] = 'x';
    for (int i = 0; i < 16; i++)
    {
        p[i + 2] = hex[(val >> (60 - i * 4)) & 0xf];
    }
    p[18] = 0;
    return ptr;
}
