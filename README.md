# jetpack

Jetpack is a package
[templating](https://en.wikipedia.org/wiki/Template_processor)
system based on the [mustache](http://mustache.github.io/) template syntax.

A jetpack template (pack) is just a directory containing subdirectories and
template files. A pack might be a
[python package](https://docs.python.org/2/tutorial/modules.html#packages),
[R package](https://cran.r-project.org/manuals.html#R-exts),
[Ruby gem](http://guides.rubygems.org/make-your-own-gem/),
anything...

Packs are stored in a [hanger](https://github.com/bmweiner/hanger) and
rendered by the jetpack utility.

## the Hanger

A simple hanger might look like this:

    hanger/
      pack1/
        profile.md
        pack.json
      pack2/
        bio.txt
      pack.cfg
      pack.json

Each pack has it's own directory in the hanger and contains all the
subdirectories and template files for that pack. Additionally `pack.cfg` and
`pack.json` files may exist at the hanger and/or pack level.

### Template Files

Templates use the [mustache](http://mustache.github.io/) template syntax
(implemented with [pystache](https://github.com/defunkt/pystache)).

Partials are relative to the hanger directory.

hanger/pack1/profile.md

    # {{team}}
    {{first}} {{last}}
    {{role}}
    ## Bio
    {{> pack2/bio.txt}}
    Created: {{today}}

hanger/pack2/bio.txt

    Belichick has extensive authority over the Patriots'...

### Context Files

Context is stored in **pack.json** files.

hanger/pack.json

    {
      "team": "New England Patriots"
    }

hanger/pack1/pack.json

    {
      "first": "Bill",
      "last": "Belichik",
      "role": "coach"
    }

#### Built-in Context

The default context includes the following tags, which can be overwritten in a
context file, if desired.

**datetime**

 * today: %c
 * year: %Y
 * month: %m
 * day: %d
 * hour: %H
 * minute: %M
 * second: %S

### Configuration Files

Configuration is stored in **pack.cfg** files. The following options are
available:

A pack object can inherit the templates, contexts, and configurations of other
packs. Base classes are separated by a comma.

    [class]
    base: python,generic

#### Inheritance

When base classes are specified, templates, contexts, and configurations are
inherited in the following order:

 * pack
 * pack bases (recursive)
 * hanger

Circular imports are not permitted.

Set the format of built-in context tags by using the datetime
[directives](https://docs.python.org/2/library/time.html#time.strftime).

    [datetime]
    today: %c
    year: %Y
    month: %m
    day: %d
    hour: %H
    minute: %M
    second: %S

## Installation

    $ git clone https://github.com/bmweiner/jetpack.git
    $ python setup.py install

or

    $ pip install jetpack

## Usage

jetpack provides a terminal command `jetpack`:

    $ jetpack python -s /path/to/hanger
    name: my_package
    description: The best package!

try `jetpack --help` for additional details on usage.

and a python module for interaction:

    import jetpack
    jetpack.launch(hanger='/path/to/hanger', pack='python', name='my_package',
                   description='The best package!')

## Example

Fork my [hanger](https://github.com/bmweiner/hanger) to get started. This
example demonstrates using...

 * partials to create .gitignore and LICENSE
 * subclasses to render python-flask pack from python pack
 * built-in datetime context
