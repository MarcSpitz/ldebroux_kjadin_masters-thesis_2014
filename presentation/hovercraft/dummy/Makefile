# CC=hovercraft
# OUTPUT=presentation

# CFLAGS=
# LDFLAGS=
# SOURCES=dummy.rst
# OBJECTS=$(SOURCES:.rst=.presentation)
# EXECUTABLE=dummy

# all: $(SOURCES) $(OBJECTS)
# 	echo $(OBJECTS)

# $(EXECUTABLE): $(OBJECTS)

# .rst.presentation:
# 	$(CC) $(CFLAGS) $< $@

# I am a comment, and I want to say that the variable CC will be
# the compiler to use.
CC=hovercraft
# Hey!, I am comment number 2. I want to say that CFLAGS will be the
# options I'll pass to the compiler.
CFLAGS=-t ../templates/force

all: dummy

dummy: dummy.presentation
	sed -i -e 's/&lt;/</g' dummy.presentation/index.html
	sed -i -e 's/&gt;/>/g' dummy.presentation/index.html
	cp *.json dummy.presentation/

dummy.presentation: dummy.rst
	$(CC) $(CFLAGS) dummy.rst dummy.presentation

clean:
	rm -rf *.presentation