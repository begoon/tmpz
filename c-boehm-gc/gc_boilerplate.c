#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <gc.h> // Boehm-Demers-Weiser GC

// allocate a byte buffer that MAY contain pointers (GC will scan it)
void *runtime_alloc(size_t nbytes)
{
    void *p = GC_MALLOC(nbytes);
    if (!p)
    {
        fprintf(stderr, "GC_MALLOC failed\n");
        abort();
    }
    return p;
}

// allocate a byte buffer that contains NO pointers (faster scan)
void *runtime_alloc_atomic(size_t nbytes)
{
    void *p = GC_MALLOC_ATOMIC(nbytes);
    if (!p)
    {
        fprintf(stderr, "GC_MALLOC_ATOMIC failed\n");
        abort();
    }
    return p;
}

// duplicate a C string into GC-managed memory (no pointers inside → atomic)
char *runtime_strdup(const char *s)
{
    size_t n = strlen(s) + 1;
    char *p = (char *)runtime_alloc_atomic(n);
    memcpy(p, s, n);
    return p;
}

// Optional: trigger a collection at points your compiler chooses.
// Use GC_collect_a_little() for cheap incremental work, or GC_gcollect() for full.
void runtime_maybe_collect(int aggressive)
{
    if (aggressive)
    {
        GC_gcollect(); // full, stop-the-world collection
    }
    else
    {
        GC_collect_a_little(); // a bit of work; returns steps done
    }
}

int main(void)
{
    // Always initialize first (safe to call more than once).
    GC_INIT();

    // (Optional) Make GC a bit more responsive in interactive programs.
    // GC_enable_incremental();

    // test: allocate an immutable string
    const char *const hello = runtime_strdup("hello, world");
    printf("%s\n", hello);

    // allocate an object with interior pointers (use non-atomic)
    typedef struct Node
    {
        struct Node *next;
        char *label; // points to a GC string
    } Node;

    Node *a = (Node *)runtime_alloc(sizeof(Node));
    a->next = NULL;
    a->label = runtime_strdup("A");

    // build another node
    Node *b = (Node *)runtime_alloc(sizeof(Node));
    b->next = a;
    b->label = runtime_strdup("B");

    printf("b->label=%s, b->next->label=%s\n", b->label, b->next->label);

    // at spots your compiler chooses, we ask GC to do a little work:
    runtime_maybe_collect(0); // incremental nibble
    // ...or force a full collection:
    runtime_maybe_collect(1); // full

    return 0; // no frees required; GC will reclaim unreachable memory.
}
