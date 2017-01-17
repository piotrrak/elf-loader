// custom flags

// dl(m)open() flag. Specifies that the loaded file should be placed in load
// order as though it were added via LD_PRELOAD, in all contexts.
#define RTLD_PRELOAD 0x00020
// dl(m)open() flag. Specifies that the loaded file should be placed in load
// order as though it were added via LD_PRELOAD, in this context only.
#define RTLD_INTERPOSE 0x00040
