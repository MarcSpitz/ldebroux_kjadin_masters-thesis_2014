# CC=hovercraft
# OUTPUT=presentation

# CFLAGS=
# LDFLAGS=
# SOURCES=slides.rst
# OBJECTS=$(SOURCES:.rst=.generated)
# EXECUTABLE=slides

# all: $(SOURCES) $(OBJECTS)
# 	echo $(OBJECTS)

# $(EXECUTABLE): $(OBJECTS)

# .rst.generated:
# 	$(CC) $(CFLAGS) $< $@

# I am a comment, and I want to say that the variable CC will be
# the compiler to use.
CC=hovercraft
# Hey!, I am comment number 2. I want to say that CFLAGS will be the
# options I'll pass to the compiler.
CFLAGS=-t ../templates/force

all: slides

slides: slides.generated
	sed -i -e 's/&lt;/</g' slides.generated/index.html
	sed -i -e 's/&gt;/>/g' slides.generated/index.html
	cp *.json slides.generated/

slides.generated: slides.rst
	$(CC) $(CFLAGS) slides.rst slides.generated

clean:
	rm -rf *.generated
