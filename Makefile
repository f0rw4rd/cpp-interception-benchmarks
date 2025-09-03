CC = gcc
CFLAGS = -Wall -O2 -fno-inline
LDFLAGS = -Lbuild -lfuncs -Wl,-rpath,build
BUILDDIR = build
RESULTSDIR = results

all: $(BUILDDIR)/libfuncs.so $(BUILDDIR)/benchmark $(BUILDDIR)/hook.so

$(BUILDDIR):
	mkdir -p $(BUILDDIR)

$(RESULTSDIR):
	mkdir -p $(RESULTSDIR)

$(BUILDDIR)/libfuncs.so: libfuncs.c | $(BUILDDIR)
	$(CC) -shared -fPIC $(CFLAGS) -o $@ $< -lm

$(BUILDDIR)/benchmark: benchmark.c $(BUILDDIR)/libfuncs.so | $(BUILDDIR)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS) -lm

$(BUILDDIR)/hook.so: hook.c | $(BUILDDIR)
	$(CC) -shared -O3 -fPIC -o $@ $< -ldl

run: all | $(RESULTSDIR)
	./run_all.sh

clean:
	rm -rf $(BUILDDIR)
	rm -f $(RESULTSDIR)/*.csv $(RESULTSDIR)/*.png

.PHONY: all run clean