#DEBUG=-DPRINTF_DEBUG_ENABLE
DEBUG+=-DMALLOC_DEBUG_ENABLE
#OPT=-O2
LDSO_SONAME=ldso
CFLAGS=-g3 -Wall -Werror $(DEBUG) $(OPT) -Wp,-M,-MF,.deps/$*.d
LDFLAGS=$(OPT)

#we need libgcc for 64bit arithmetic functions
LIBGCC=$(shell gcc --print-libgcc-file-name)
PWD=$(shell pwd)
ARCH=$(shell uname -p)
ifeq ($(ARCH),i386)
LDSO_FILE=/lib/ld-linux.so.2
LIBDL_FILE=/lib/libdl.so.2
LDSO_DEBUG_FILE=/usr/lib/debug/ld-linux.so.2
else ifeq ($(ARCH),x86_64)
LDSO_FILE=/lib64/ld-linux-x86-64.so.2
LIBDL_FILE=/lib64/libdl.so.2
LDSO_DEBUG_FILE=/usr/lib/debug/lib64/ld-linux-x86-64.so.2.debug
endif

all: ldso libvdl.so elfedit

test: FORCE
	$(MAKE) -C test
	$(MAKE) -C test run
FORCE:

LDSO_ARCH_SRC=\
$(ARCH)/machine.c $(ARCH)/stage0.S $(ARCH)/resolv.S
LDSO_SOURCE=\
stage1.c stage2.c avprintf-cb.c \
dprintf.c vdl-utils.c vdl-log.c \
vdl.c system.c alloc.c glibc.c \
gdb.c vdl-dl.c interp.c vdl-file-reloc.c \
vdl-file-list.c vdl-gc.c vdl-file-symbol.c \
futex.c vdl-tls.c $(LDSO_ARCH_SRC)
SOURCE=$(LDSO_SOURCE) libvdl.c elfedit.c readversiondef.c

LDSO_OBJECTS=$(addsuffix .o,$(basename $(LDSO_SOURCE)))



ldso: $(LDSO_OBJECTS) ldso.version
# build rules.
%.o:%.c
	$(CC) $(CFLAGS) -DLDSO_SONAME=\"$(LDSO_SONAME)\" -fno-stack-protector  -I$(PWD) -I$(PWD)/$(ARCH) -fpic -fvisibility=hidden -o $@ -c $<
%.o:%.S
	$(AS) $(ASFLAGS) -o $@ $<
ldso:
	$(CC) $(LDFLAGS) -shared -nostartfiles -nostdlib -Wl,--entry=stage0,--version-script=ldso.version,--soname=$(LDSO_SONAME) -o $@ $(LDSO_OBJECTS) $(LIBGCC)

# we have two generated files and need to build them.
ldso.version: readversiondef vdl-dl.version
	./readversiondef $(LDSO_FILE) | cat vdl-dl.version - > $@
config.h:
	./extract-system-config.py --debug=$(LDSO_DEBUG_FILE) >$@
# build the program used to generate ldso.version
readversiondef.o: readversiondef.c
	$(CC) $(CFLAGS) -c -o $@ $^
readversiondef: readversiondef.o
	$(CC) $(LDFLAGS) -o $@ $^

libvdl.version: readversiondef
	./readversiondef $(LIBDL_FILE) > $@
libvdl.o: libvdl.c
	$(CC) $(CFLAGS) -fvisibility=hidden -fpic -o $@ -c $< 
libvdl.so: libvdl.o ldso libvdl.version
	$(CC) $(LDFLAGS) ldso -nostdlib -shared -Wl,--version-script=libvdl.version -o $@ $<

elfedit.o: elfedit.c
	$(CC) $(CFLAGS) -o $@ -c $<
elfedit: elfedit.o
	$(CC) $(LDFLAGS) -o $@ $^

clean: 
	-rm -f elfedit readversiondef core hello hello-ldso 2> /dev/null
	-rm -f ldso libvdl.so *.o  $(ARCH)/*.o 2>/dev/null
	-rm -f *~ $(ARCH)/*~ 2>/dev/null
	-rm -f \#* $(ARCH)/\#* 2>/dev/null
	-rm -f ldso.version 2>/dev/null
	$(MAKE) -C test clean

-include $(SRC:%.o=.deps/%.d)